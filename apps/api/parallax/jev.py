"""AI reader backed by Jev (TypeSafe's System One decision model).

Jev returns typed, calibrated decisions instead of text, which fits the part
of scoping a human estimator does by judgement, one clause at a time:
*what kind of work is this?*, *has the client committed to it?* and *is it
defined well enough to size?*. Hours, simulation and learning stay in code
(Jev's own docs advise against using it for arithmetic).

Design constraints:
  * Questions are written in English; clauses stay in their original language
    (independent tests found translated questions, not foreign-language
    state, are what degrades Jev).
  * Every answer is cached per (question version, clause text), so
    re-estimates, clarifications and repeated briefs never pay twice and stay
    consistent. A new question only costs the new question.
  * JevStation bills 1 credit for up to 5 questions and 3 credits for 6-10,
    so questions are packed 5 per call across clauses.
  * Several API keys form a pool: an empty or failing key is skipped and the
    call is retried on the next one. An hourly call cap protects the balance.

Providers: JEVSTATION_API_KEY, JEVSTATION_API_KEY_2 .. _N (jevstation.com, an
independent reseller), TYPESAFE_API_KEY (official API), AI_GATEWAY_API_KEY
(Vercel AI Gateway, TypeSafe-compatible route). Keys are read from the
environment; `load_dotenv()` fills it from a git-ignored `.env`.
"""
from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional, Sequence

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[3]
QUESTION_VERSION = "v1"  # namespace of the legacy kind+tentative cache
# Fixed before the held-out evaluation was run (see scripts/evaluate_readers.py).
KIND_CONFIDENCE_MIN = 0.6
TENTATIVE_MIN = 0.7
QUESTIONS_PER_CALL = 5  # JevStation: 1-5 questions = 1 credit, 6-10 = 3 credits
QUESTIONS_PER_CALL_DIRECT = 20  # TypeSafe/Vercel bill input tokens only: bigger packs share the fixed overhead
USD_PER_MILLION_INPUT_TOKENS = 0.042  # TypeSafe list price (docs.typesafe.ai/models)
CLAUSES_PER_CALL = 2  # legacy constant (2 clauses x 2 questions); kept for scripts that report it
SHIPPED_CACHE = ROOT_DIR / "datasets" / "jev_cache" / f"clauses_{QUESTION_VERSION}.json"
SHIPPED_ANSWERS = ROOT_DIR / "datasets" / "jev_cache" / "answers_v2.json"


def load_dotenv(path: Optional[Path] = None) -> int:
    """Fill os.environ from a KEY=VALUE file without overriding existing variables."""
    if os.environ.get("PARALLAX_NO_DOTENV") == "1":
        return 0
    path = path or ROOT_DIR / ".env"
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) and value and key not in os.environ:
            os.environ[key] = value
            n += 1
    return n


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


@dataclass(frozen=True)
class Question:
    qid: str
    version: str
    type: str  # "choice" | "noul"
    instructions: str  # "{ref}" is replaced by the state key holding the text
    criteria: Optional[dict] = None

    @property
    def tag(self) -> str:
        return f"{self.qid}@{self.version}"

    def spec(self, ref: str) -> dict:
        spec = {"type": self.type, "instructions": self.instructions.format(ref=ref)}
        if self.criteria:
            spec["criteria"] = self.criteria
        return spec


KIND_Q = Question("kind", "v1", "choice", KIND_INSTRUCTIONS, KINDS)
TENTATIVE_Q = Question("tentative", "v1", "noul", TENTATIVE_INSTRUCTIONS)
# The senior estimator's "this will take longer than it looks". Chosen on SiP training tasks and
# validated on later, unseen tasks (scripts/sip_jev_study.py); the exact same wording is asked of brief clauses.
OVERRUN_Q = Question(
    "overrun", "v1", "noul",
    "Would an experienced developer expect the work in `{ref}` to take noticeably longer than it first appears?")
CLAUSE_QUESTIONS: tuple[Question, ...] = (KIND_Q, TENTATIVE_Q, OVERRUN_Q)


@dataclass
class ClauseReading:
    kind: str
    kind_confidence: float
    kind_probabilities: dict[str, float]
    tentative: float
    model: str
    provider: str
    extra: dict[str, float] = field(default_factory=dict)  # further noul answers by question id

    @property
    def component(self) -> Optional[str]:
        return KIND_TO_COMPONENT.get(self.kind)


def _norm(answer_key: str) -> str:
    return re.sub(r"_+", "_", answer_key.strip().lower())


def _legacy_key(text: str) -> str:
    return hashlib.sha256(f"{QUESTION_VERSION}|{text.strip()}".encode()).hexdigest()[:24]


def _cache_key(text: str, question: Question) -> str:
    return hashlib.sha256(f"{question.tag}|{text.strip()}".encode()).hexdigest()[:24]


# --------------------------------------------------------------------------- #
# Key pool
# --------------------------------------------------------------------------- #
# Pinned: every threshold and factor was measured on jev-1.13.0, and the "jev"/"jev-latest" alias
# moves to newer versions. JEV_MODEL overrides it (re-run the evaluations if you do).
JEV_MODEL = os.environ.get("JEV_MODEL", "jev-1.13.0")
PROVIDERS = (
    ("JEVSTATION_API_KEY", "jevstation", "https://jevstation.com/api/v1/systemone", JEV_MODEL),
    ("TYPESAFE_API_KEY", "typesafe", "https://api.typesafe.ai/v1/systemone", JEV_MODEL),
    ("AI_GATEWAY_API_KEY", "vercel", "https://ai-gateway.vercel.sh/typesafe/v1/systemone", f"typesafe-ai/{JEV_MODEL}"),
)


@dataclass
class JevKey:
    name: str
    provider: str
    url: str
    model: str
    secret: str = field(repr=False)
    credits: Optional[int] = None
    disabled_until: float = 0.0
    calls: int = 0
    charged: int = 0
    input_tokens: int = 0
    last_error: Optional[str] = None

    @property
    def per_credit(self) -> bool:
        return self.provider == "jevstation"

    def public(self) -> dict:
        return {"name": self.name, "provider": self.provider, "credits": self.credits, "calls": self.calls,
                "charged": self.charged, "input_tokens": self.input_tokens,
                "usd_spent": None if self.per_credit else round(self.input_tokens * USD_PER_MILLION_INPUT_TOKENS / 1e6, 5),
                "cooling_down": time.time() < self.disabled_until, "last_error": self.last_error}


def discover_keys() -> list[JevKey]:
    if os.environ.get("JEV_DISABLED") == "1":
        return []
    keys: list[JevKey] = []
    seen: set[str] = set()
    for prefix, provider, url, model in PROVIDERS:
        names = [k for k in os.environ if k == prefix or re.fullmatch(rf"{prefix}_\d+", k)]
        names.sort(key=lambda k: int(k.rsplit("_", 1)[1]) if k != prefix else 1)
        secrets = [(n, os.environ[n].strip()) for n in names]
        for i, s in enumerate(os.environ.get(f"{prefix}S", "").split(","), start=1):
            secrets.append((f"{prefix}S[{i}]", s.strip()))
        for name, secret in secrets:
            if secret and secret not in seen:
                seen.add(secret)
                keys.append(JevKey(name, provider, url, model, secret))
    return keys


class JevError(Exception):
    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status


class JevReader:
    def __init__(
        self,
        cache_path: Optional[Path] = None,
        min_credits: int = int(os.environ.get("JEV_MIN_CREDITS", "0")),
        max_calls_per_hour: Optional[int] = int(os.environ.get("JEV_MAX_CALLS_PER_HOUR", "120")),
        timeout: float = 30.0,
        questions: Sequence[Question] = CLAUSE_QUESTIONS,
        keys: Optional[list[JevKey]] = None,
    ):
        self.keys = discover_keys() if keys is None else keys
        # The legacy kind+tentative file is read-only; fresh answers go to the per-question file.
        self.cache_path = SHIPPED_ANSWERS if cache_path == SHIPPED_CACHE else cache_path
        self.min_credits = min_credits
        self.max_calls_per_hour = max_calls_per_hour
        self.timeout = timeout
        self.questions = tuple(questions)
        self.lock = threading.Lock()
        self.cache: dict[str, dict] = {}
        self.last_error: Optional[str] = None
        self.halted: Optional[str] = None
        self.call_times: list[float] = []
        self.calls_made = 0
        self.credits_charged = 0
        self._rr = 0
        self._dirty = False  # only write the cache file when a fresh answer was added
        disabled = os.environ.get("JEV_DISABLED") == "1"
        for path in () if disabled else (SHIPPED_CACHE, SHIPPED_ANSWERS, cache_path):
            if path and path.exists():
                try:
                    self.cache.update(json.loads(path.read_text(encoding="utf-8")))
                except (OSError, ValueError) as exc:
                    logger.warning("Ignoring unreadable Jev cache %s: %s", path, exc)

    def with_key(self, secret: str, provider: str = "jevstation") -> "JevReader":
        """A reader that spends only the given (visitor's) key but shares this reader's answer cache."""
        spec = next((p for p in PROVIDERS if p[1] == provider), PROVIDERS[0])
        clone = copy.copy(self)
        clone.keys = [JevKey("visitor", spec[1], spec[2], spec[3], secret.strip())]
        clone.call_times, clone.calls_made, clone.credits_charged = [], 0, 0
        clone.halted, clone.last_error = None, None
        clone.max_calls_per_hour = None  # their own credits, their own limit
        return clone

    # ------------------------------------------------------------------ status
    @property
    def configured(self) -> bool:
        return bool(self.keys)

    @property
    def provider(self) -> Optional[str]:
        return self.keys[0].provider if self.keys else None

    @property
    def credits_remaining(self) -> Optional[int]:
        known = [k.credits for k in self.keys if k.credits is not None]
        if not known:
            return None
        return sum(known)

    def status(self) -> dict:
        return {
            "configured": self.configured,
            "provider": self.provider,
            "available": self._can_call(),
            "credits_remaining": self.credits_remaining,
            "keys_total": len(self.keys),
            "keys_usable": sum(self._usable(k) for k in self.keys),
            "keys": [k.public() for k in self.keys],
            "cached_answers": len(self.cache),
            "cached_clauses": len(self.cache),
            "calls_this_process": self.calls_made,
            "credits_charged_this_process": self.credits_charged,
            "usd_spent_this_process": round(sum(k.input_tokens for k in self.keys if not k.per_credit)
                                            * USD_PER_MILLION_INPUT_TOKENS / 1e6, 5),
            "questions": [q.tag for q in self.questions],
            "last_error": self.last_error,
            "halted": self.halted,
        }

    def _usable(self, key: JevKey) -> bool:
        return time.time() >= key.disabled_until and (key.credits is None or key.credits > self.min_credits)

    def _can_call(self) -> bool:
        if self.halted or not any(self._usable(k) for k in self.keys):
            return False
        if self.max_calls_per_hour is None:
            return True
        recent = [t for t in self.call_times if t > time.time() - 3600]
        return len(recent) < self.max_calls_per_hour

    # ------------------------------------------------------------------ cache
    def answer(self, text: str, question: Question) -> Optional[dict]:
        raw = self.cache.get(_cache_key(text, question))
        if raw is not None:
            return raw
        if question.version != "v1" or question.qid not in ("kind", "tentative"):
            return None
        # Readings from before per-question caching hold kind and tentative together.
        raw = self.cache.get(_legacy_key(text))
        if raw is None or "kind" not in raw:
            return None
        if question.qid == "kind":
            return {"answer": {"choice": raw["kind"], "confidence": raw["kind_confidence"],
                               "probabilities": raw.get("kind_probabilities") or {}},
                    "model": raw.get("model"), "provider": raw.get("provider")}
        if question.qid == "tentative":
            return {"answer": {"noul": raw["tentative"]}, "model": raw.get("model"), "provider": raw.get("provider")}
        return None

    def cached(self, text: str) -> Optional[ClauseReading]:
        return self._reading(text.strip())

    def _reading(self, text: str) -> Optional[ClauseReading]:
        answers = {q.qid: self.answer(text, q) for q in self.questions}
        if any(a is None for a in answers.values()):
            return None
        kind, tent = answers["kind"], answers["tentative"]
        k = kind["answer"]
        extra = {qid: float(a["answer"]["noul"]) for qid, a in answers.items()
                 if qid not in ("kind", "tentative") and "noul" in a["answer"]}
        return ClauseReading(
            kind=k["choice"], kind_confidence=round(float(k.get("confidence", 0.0)), 4),
            kind_probabilities=dict(k.get("probabilities") or {}), tentative=round(float(tent["answer"]["noul"]), 4),
            model=kind.get("model") or "", provider=kind.get("provider") or "", extra=extra,
        )

    # ------------------------------------------------------------------ reading
    def read(self, clauses: Sequence[str]) -> dict[str, ClauseReading]:
        """Return readings for as many clauses as possible (cached or fresh)."""
        texts = list(dict.fromkeys(c.strip() for c in clauses if c.strip()))
        self.ask(texts, self.questions)
        out = {}
        for text in texts:
            reading = self._reading(text)
            if reading:
                out[text] = reading
        return out

    def missing(self, texts: Sequence[str], questions: Sequence[Question]) -> list[tuple[str, Question]]:
        return [(t, q) for t in dict.fromkeys(x.strip() for x in texts if x.strip()) for q in questions
                if self.answer(t, q) is None]

    def ask(self, texts: Sequence[str], questions: Sequence[Question], max_calls: Optional[int] = None,
            workers: int = 8) -> dict[tuple[str, str], dict]:
        """Answer every (text, question) pair that is not cached yet, 5 questions per call.

        Returns the fresh answers keyed by (text, question id).
        """
        todo = self.missing(texts, questions)
        # Token-billed providers take big packs; per-credit JevStation is cheapest at 5 questions.
        direct = any(not k.per_credit and self._usable(k) for k in self.keys)
        size = QUESTIONS_PER_CALL_DIRECT if direct else QUESTIONS_PER_CALL
        packs = [todo[i: i + size] for i in range(0, len(todo), size)]
        if max_calls is not None:
            packs = packs[:max_calls]
        if not packs or not self.configured:
            return {}
        fresh: dict[tuple[str, str], dict] = {}
        # All packs go out in parallel: an empty key answers 402 without charging, and the
        # pack is retried on the next key, so unknown balances cannot cause overspending.
        with ThreadPoolExecutor(max_workers=max(1, min(workers, len(packs)))) as pool:
            for result in pool.map(self._send, packs):
                fresh.update(result)
        self._persist()
        return fresh

    def _reserve_call(self) -> bool:
        with self.lock:
            if not self._can_call():
                return False
            self.call_times.append(time.time())
            self.calls_made += 1
            return True

    def _pick_key(self, tried: set[str], n_questions: int = QUESTIONS_PER_CALL) -> Optional[JevKey]:
        with self.lock:
            usable = [k for k in self.keys if k.name not in tried and self._usable(k)
                      and (n_questions <= QUESTIONS_PER_CALL or not k.per_credit)]
            if not usable:
                return None
            # Prefer keys with the largest known balance; unknown balances count as fresh.
            usable.sort(key=lambda k: -(k.credits if k.credits is not None else 10**6))
            top = [k for k in usable if (k.credits or 10**6) == (usable[0].credits or 10**6)]
            self._rr += 1
            return top[self._rr % len(top)]

    def _send(self, pack: list[tuple[str, Question]]) -> dict[tuple[str, str], dict]:
        if not self._reserve_call():
            return {}
        texts = list(dict.fromkeys(t for t, _ in pack))
        refs = {t: f"c{i}" for i, t in enumerate(texts)}
        state = {ref: t for t, ref in refs.items()}
        questions = {f"{refs[t]}_{q.qid}": q.spec(refs[t]) for t, q in pack}
        tried: set[str] = set()
        while True:
            key = self._pick_key(tried, len(pack))
            if key is None:
                return {}
            tried.add(key.name)
            try:
                data = self._post(key, {"model": key.model, "state": state, "questions": questions})
            except JevError as exc:
                self._key_failed(key, exc)
                continue
            break
        model = data.get("model") or key.model
        out: dict[tuple[str, str], dict] = {}
        # The API normalises answer keys (e.g. collapses repeated underscores), so match loosely.
        answers = {_norm(k): v for k, v in (data.get("answers") or {}).items()}
        with self.lock:
            credits = data.get("credits") or {}
            if credits.get("remaining") is not None:
                key.credits = int(credits["remaining"])
            charged = int(credits.get("charged") or 0)
            key.charged += charged
            key.input_tokens += int((data.get("usage") or {}).get("input_tokens") or 0)
            key.calls += 1
            key.last_error = None
            self.credits_charged += charged
            self.last_error = None
            for t, q in pack:
                raw = answers.get(_norm(f"{refs[t]}_{q.qid}")) or {}
                if q.type == "choice" and "choice" in raw:
                    probs = raw.get("probabilities") or {}
                    top = dict(sorted(probs.items(), key=lambda kv: -kv[1])[:5])
                    ans = {"choice": raw["choice"], "confidence": round(float(raw.get("confidence", 0.0)), 4),
                           "probabilities": {k: round(float(v), 4) for k, v in top.items()}}
                elif q.type == "noul" and "noul" in raw:
                    ans = {"noul": round(float(raw["noul"]), 4)}
                else:
                    continue
                entry = {"answer": ans, "q": q.tag, "model": model, "provider": key.provider}
                self.cache[_cache_key(t, q)] = entry
                out[(t, q.qid)] = entry
                self._dirty = True
            if not out:
                # Paid for a call but could not use any answer: stop spending until a human looks.
                self.halted = f"{key.name}: response had no usable answers (keys {sorted(answers)[:5]})"
                self.last_error = self.halted
                logger.error("Jev reader halted: %s", self.halted)
        return out

    def _post(self, key: JevKey, body: dict) -> dict:
        request = urllib.request.Request(
            key.url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key.secret}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                # Cloudflare in front of some providers rejects the default urllib signature (error 1010).
                "User-Agent": "parallax-estimator/0.3 (+https://github.com/mapleleaflatte03/the-estimator)",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:300].decode("utf-8", "replace")
            raise JevError(f"HTTP {exc.code}: {detail}", exc.code) from None
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            raise JevError(str(exc)) from None
        if not isinstance(payload, dict):
            raise JevError("unexpected response")
        if payload.get("code") not in (None, 0):
            raise JevError(str(payload.get("message")), 402 if "credit" in str(payload.get("message")).lower() else None)
        return payload.get("data", payload)

    def _key_failed(self, key: JevKey, exc: JevError) -> None:
        logger.warning("Jev call failed on %s (%s)", key.name, exc)
        with self.lock:
            key.last_error = str(exc)[:200]
            self.last_error = f"{key.name}: {key.last_error}"
            if exc.status == 402:
                key.credits = 0
            elif exc.status in (401, 403):
                key.disabled_until = time.time() + 3600
            else:
                key.disabled_until = time.time() + 30

    def _persist(self) -> None:
        # Never rewrite the file without new answers: a disabled reader starts with an empty cache
        # and would otherwise overwrite the shipped answers.
        if not self.cache_path or not self._dirty:
            return
        try:
            with self.lock:
                own = {k: v for k, v in self.cache.items() if "answer" in v} \
                    if self.cache_path == SHIPPED_ANSWERS else dict(self.cache)
                payload = json.dumps(own, ensure_ascii=False, indent=0, sort_keys=True)
                self._dirty = False
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.cache_path.with_suffix(".tmp")
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(self.cache_path)
        except OSError as exc:
            logger.warning("Could not persist Jev cache: %s", exc)


__all__ = [
    "ClauseReading", "JevReader", "JevKey", "Question", "KIND_Q", "TENTATIVE_Q", "CLAUSE_QUESTIONS", "KINDS",
    "KIND_TO_COMPONENT", "KIND_CONFIDENCE_MIN", "TENTATIVE_MIN", "SHIPPED_CACHE", "SHIPPED_ANSWERS",
    "load_dotenv", "asdict",
]
