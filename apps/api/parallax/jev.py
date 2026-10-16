"""Optional AI reader backed by Jev (TypeSafe's System One decision model).

Jev returns typed, calibrated decisions instead of text, which fits the part
of scoping that is a judgement per clause: *what kind of work is this?* and
*has the client actually committed to it?*. Hours, simulation and learning
stay in code (Jev's own docs advise against using it for arithmetic).

Design constraints:
  * Questions are written in English; clauses stay in their original language
    (independent tests found translated questions, not foreign-language
    state, are what degrades Jev).
  * Every reading is cached by clause text, so re-estimates, clarifications
    and repeated briefs never pay twice and stay consistent.
  * A credit floor and an hourly call cap protect the prepaid balance; on any
    error the caller falls back to the rule-based reader.

Providers (first key found wins): JEVSTATION_API_KEY (jevstation.com, an
independent reseller), TYPESAFE_API_KEY (official API), AI_GATEWAY_API_KEY
(Vercel AI Gateway, TypeSafe-compatible route; needs paid credits for Jev).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence

logger = logging.getLogger(__name__)

QUESTION_VERSION = "v1"
# Fixed before the held-out evaluation was run (see scripts/evaluate_readers.py).
KIND_CONFIDENCE_MIN = 0.6
TENTATIVE_MIN = 0.7
CLAUSES_PER_CALL = 2  # 2 clauses x 2 questions = 4 questions -> 1 JevStation credit
SHIPPED_CACHE = Path(__file__).resolve().parents[3] / "datasets" / "jev_cache" / f"clauses_{QUESTION_VERSION}.json"

# Kinds of work the reader can assign; descriptions are what Jev sees.
KINDS: dict[str, str] = {
    "auth": "User sign-up, login, passwords, OTP, single sign-on",
    "permissions_audit": "Roles, permissions, access rights, audit log or change history, security",
    "reporting": "Reports, dashboards, statistics, KPIs, charts",
    "file_export": "Exporting data to files such as Excel, PDF or CSV",
    "data_import": "Importing or migrating existing data from files or old systems",
    "notification": "Sending notifications or messages: email, SMS, push, Zalo, chat",
    "scheduling": "Calendars, bookings, appointments, shifts, dispatching or assigning people",
    "mobile_app": "A mobile phone or tablet app",
    "offline_sync": "Working without internet and syncing later",
    "external_integration": "Connecting to an external system or third-party API (ERP, accounting, marketplace, shipping)",
    "payment": "Online payments, payment gateways, invoices, billing",
    "ai_assistant": "AI features: chatbot, summarisation, document or image understanding, semantic search",
    "search": "Searching and filtering records",
    "workflow_approval": "Approval steps, workflow states, tracking the status or progress of something",
    "performance": "High load, many concurrent users, speed or throughput targets",
    "maps_location": "Maps, GPS, live location, routes",
    "data_management": "Creating, editing and managing business records or domain features (forms, lists, profiles)",
    "other": "None of the above",
}
# Reader kind -> extractor component key.
KIND_TO_COMPONENT: dict[str, Optional[str]] = {
    "auth": "auth", "permissions_audit": "rbac", "reporting": "reporting", "file_export": "export",
    "data_import": "import", "notification": "notification", "scheduling": "scheduling", "mobile_app": "mobile",
    "offline_sync": "offline", "external_integration": "integration", "payment": "payment", "ai_assistant": "ai",
    "search": "search", "workflow_approval": "workflow", "performance": "performance", "maps_location": "maps",
    "data_management": "crud", "other": None,
}
TENTATIVE_INSTRUCTIONS = (
    "Is the requirement in `{ref}` stated tentatively, meaning the client has not committed to it "
    "(for example: maybe, might, may need, to be considered, if budget allows, optional, undecided, later phase)? "
    "Answer no for a firm requirement, even if it uses 'can' or 'có thể' to describe what a user is able to do."
)
KIND_INSTRUCTIONS = (
    "`{ref}` is one requirement from a client's software brief (it may be written in Vietnamese). "
    "Which kind of software work does it mainly ask for?"
)


@dataclass
class ClauseReading:
    kind: str
    kind_confidence: float
    kind_probabilities: dict[str, float]
    tentative: float
    model: str
    provider: str

    @property
    def component(self) -> Optional[str]:
        return KIND_TO_COMPONENT.get(self.kind)


def _cache_key(text: str) -> str:
    return hashlib.sha256(f"{QUESTION_VERSION}|{text.strip()}".encode()).hexdigest()[:24]


class JevReader:
    def __init__(
        self,
        cache_path: Optional[Path] = None,
        min_credits: int = int(os.environ.get("JEV_MIN_CREDITS", "4")),
        max_calls_per_hour: int = int(os.environ.get("JEV_MAX_CALLS_PER_HOUR", "30")),
        timeout: float = 30.0,
    ):
        self.provider, self.url, self.key = self._configure()
        self.cache_path = cache_path
        self.min_credits = min_credits
        self.max_calls_per_hour = max_calls_per_hour
        self.timeout = timeout
        self.lock = threading.Lock()
        self.cache: dict[str, dict] = {}
        self.credits_remaining: Optional[int] = None
        self.disabled_until = 0.0
        self.last_error: Optional[str] = None
        self.call_times: list[float] = []
        self.calls_made = 0
        disabled = os.environ.get("JEV_DISABLED") == "1"
        for path in () if disabled else (SHIPPED_CACHE, cache_path):
            if path and path.exists():
                try:
                    self.cache.update(json.loads(path.read_text(encoding="utf-8")))
                except (OSError, ValueError) as exc:
                    logger.warning("Ignoring unreadable Jev cache %s: %s", path, exc)

    @staticmethod
    def _configure() -> tuple[Optional[str], Optional[str], Optional[str]]:
        if os.environ.get("JEV_DISABLED") == "1":
            return None, None, None
        if key := os.environ.get("JEVSTATION_API_KEY"):
            return "jevstation", "https://jevstation.com/api/v1/systemone", key
        if key := os.environ.get("TYPESAFE_API_KEY"):
            return "typesafe", "https://api.typesafe.ai/v1/systemone", key
        if key := os.environ.get("AI_GATEWAY_API_KEY"):
            return "vercel", "https://ai-gateway.vercel.sh/typesafe/v1/systemone", key
        return None, None, None

    # ------------------------------------------------------------------ status
    @property
    def configured(self) -> bool:
        return self.url is not None

    def status(self) -> dict:
        return {
            "configured": self.configured,
            "provider": self.provider,
            "available": self._can_call(),
            "credits_remaining": self.credits_remaining,
            "cached_clauses": len(self.cache),
            "calls_this_process": self.calls_made,
            "last_error": self.last_error,
        }

    def _can_call(self) -> bool:
        if not self.configured or time.time() < self.disabled_until:
            return False
        if self.credits_remaining is not None and self.credits_remaining <= self.min_credits:
            return False
        recent = [t for t in self.call_times if t > time.time() - 3600]
        return len(recent) < self.max_calls_per_hour

    # ------------------------------------------------------------------ reading
    def cached(self, text: str) -> Optional[ClauseReading]:
        raw = self.cache.get(_cache_key(text))
        return ClauseReading(**raw) if raw else None

    def read(self, clauses: Sequence[str]) -> dict[str, ClauseReading]:
        """Return readings for as many clauses as possible (cached or fresh)."""
        out: dict[str, ClauseReading] = {}
        missing: list[str] = []
        for text in dict.fromkeys(c.strip() for c in clauses if c.strip()):
            hit = self.cached(text)
            if hit:
                out[text] = hit
            else:
                missing.append(text)
        batches = [missing[i: i + CLAUSES_PER_CALL] for i in range(0, len(missing), CLAUSES_PER_CALL)]
        if not batches:
            return out
        # Probe with one call while the balance is unknown, so parallel calls can never overspend.
        if self.credits_remaining is None and self._reserve_call():
            out.update(self._call(batches.pop(0)))
        if self.credits_remaining is not None:
            # Each call carries <= 5 questions, i.e. one credit.
            affordable = max(0, self.credits_remaining - self.min_credits)
            batches = batches[:affordable]
        batches = [b for b in batches if self._reserve_call()]
        if batches:
            with ThreadPoolExecutor(max_workers=4) as pool:
                for result in pool.map(self._call, batches):
                    out.update(result)
        self._persist()
        return out

    def _reserve_call(self) -> bool:
        with self.lock:
            if not self._can_call():
                return False
            self.call_times.append(time.time())
            self.calls_made += 1
            return True

    def _call(self, batch: list[str]) -> dict[str, ClauseReading]:
        state = {f"c{i}": text for i, text in enumerate(batch)}
        questions = {}
        for i in range(len(batch)):
            ref = f"c{i}"
            questions[f"{ref}_kind"] = {
                "type": "choice",
                "instructions": KIND_INSTRUCTIONS.format(ref=ref),
                "criteria": KINDS,
            }
            questions[f"{ref}_tentative"] = {"type": "noul", "instructions": TENTATIVE_INSTRUCTIONS.format(ref=ref)}
        body: dict = {"state": state, "questions": questions}
        body["model"] = "jev" if self.provider == "jevstation" else (
            "typesafe-ai/jev-1.13.0" if self.provider == "vercel" else "jev-1.13.0"
        )
        request = urllib.request.Request(
            self.url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                # Cloudflare in front of some providers rejects the default urllib signature (error 1010).
                "User-Agent": "parallax-estimator/0.2 (+https://github.com/mapleleaflatte03/the-estimator)",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:300].decode("utf-8", "replace")
            self._fail(f"HTTP {exc.code}: {detail}", backoff=600 if exc.code in (401, 402, 403) else 60)
            return {}
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            self._fail(str(exc), backoff=60)
            return {}

        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        if isinstance(payload, dict) and payload.get("code") not in (None, 0):
            self._fail(str(payload.get("message")), backoff=300)
            return {}
        credits = (data.get("credits") or {}).get("remaining")
        answers = data.get("answers") or {}
        model = data.get("model") or body["model"]
        results: dict[str, ClauseReading] = {}
        for i, text in enumerate(batch):
            kind_answer = answers.get(f"c{i}_kind") or {}
            tent_answer = answers.get(f"c{i}_tentative") or {}
            if "choice" not in kind_answer or "noul" not in tent_answer:
                continue
            probs = kind_answer.get("probabilities") or {}
            top = dict(sorted(probs.items(), key=lambda kv: -kv[1])[:3])
            reading = ClauseReading(
                kind=kind_answer["choice"],
                kind_confidence=round(float(kind_answer.get("confidence", 0.0)), 4),
                kind_probabilities={k: round(float(v), 4) for k, v in top.items()},
                tentative=round(float(tent_answer["noul"]), 4),
                model=model,
                provider=self.provider or "",
            )
            results[text] = reading
        with self.lock:
            if credits is not None:
                self.credits_remaining = int(credits)
            for text, reading in results.items():
                self.cache[_cache_key(text)] = asdict(reading)
            self.last_error = None
        return results

    def _fail(self, message: str, backoff: float) -> None:
        logger.warning("Jev call failed (%s); falling back to rules", message)
        with self.lock:
            self.last_error = message[:300]
            self.disabled_until = time.time() + backoff

    def _persist(self) -> None:
        if not self.cache_path:
            return
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.cache_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(self.cache_path)
        except OSError as exc:
            logger.warning("Could not persist Jev cache: %s", exc)
