"""Reviewable draft deliverables from an estimate version: a proposal and CSV work list."""
from __future__ import annotations

import csv
import io
import math
from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))  # fixed offset: slim images ship without tzdata

from .schemas import EstimateVersion, Project, WorkItem

ROLE_VI = {"Backend": "Máy chủ", "Frontend": "Giao diện", "QA": "Kiểm thử", "DevOps": "Triển khai"}
ROLE_EN = {"Backend": "Server", "Frontend": "Interface", "QA": "Testing", "DevOps": "Deployment"}
HIDDEN_NOTES = {"scope_breadth", "quality_gate"}
HOURS_PER_PERSON_WEEK = 32


def _lang(lang: str) -> str:
    return "en" if lang == "en" else "vi"


def pert_mean(w: WorkItem) -> float:
    return (w.optimistic_hours + 4 * w.most_likely_hours + w.pessimistic_hours) / 6


def hours_at(version: EstimateVersion, confidence: float) -> float:
    """Hours not exceeded in `confidence`% of simulated outcomes (linear between stored percentiles)."""
    fc = version.forecast
    points = {p: h for p, h in fc.percentile_curve}
    low_pct, high_pct = fc.range_percentiles
    points.update({low_pct: fc.p10_hours, 50: fc.p50_hours, 80: fc.p80_hours, high_pct: fc.p90_hours})
    pts = sorted(points.items())
    if confidence <= pts[0][0]:
        return pts[0][1]
    for (pa, ha), (pb, hb) in zip(pts, pts[1:]):
        if confidence <= pb:
            return ha + (confidence - pa) / (pb - pa) * (hb - ha)
    return pts[-1][1]


def _fmt_hours(h: float, lang: str = "vi") -> str:
    n = f"{round(h):,}"
    if _lang(lang) == "en":
        return f"{n} hours"
    return n.replace(",", ".") + " giờ"


def _fmt_money(amount: float, currency: str, lang: str = "vi") -> str:
    if currency.upper() == "VND":
        if amount >= 1_000_000_000 and _lang(lang) == "en":
            return f"{amount / 1_000_000_000:,.2f} billion VND"
        shown = f"{amount / 1_000_000:,.1f}"
        if _lang(lang) == "en":
            return f"{shown} million VND"
        return shown.replace(",", "X").replace(".", ",").replace("X", ".") + " triệu đồng"
    return f"${amount:,.0f}"


def _fmt_rate(rate: float, currency: str, lang: str) -> str:
    shown = f"{rate:,.0f}"
    if _lang(lang) == "en":
        return f"{shown} {currency}/hour"
    return shown.replace(",", ".") + f" {currency}/giờ"


def _csv_text(value: str) -> str:
    """Keep brief text and user edits from becoming formulas in spreadsheets."""
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def proposal_markdown(project: Project, v: EstimateVersion, confidence: float = 80, rate: float = 500_000,
                      currency: str = "VND", people: int = 3, lang: str = "vi") -> str:
    lang = _lang(lang)
    en = lang == "en"
    fc = v.forecast
    planned = hours_at(v, confidence)
    people = max(1, people)
    team_weeks = max(1, math.ceil(planned / (people * HOURS_PER_PERSON_WEEK)))
    chain_weeks = math.ceil((fc.critical_path_hours or 0) * fc.calibration_multiplier / HOURS_PER_PERSON_WEEK)
    weeks = max(team_weeks, chain_weeks)
    by_req: dict[str, list[WorkItem]] = {}
    for w in v.wbs:
        by_req.setdefault(w.req_ids[0], []).append(w)
    shared_by: dict[str, list[WorkItem]] = {}
    for w in v.wbs:
        for rid in w.req_ids[1:]:
            shared_by.setdefault(rid, []).append(w)
    roles = ROLE_EN if en else ROLE_VI

    def hh(h: float) -> str:
        return _fmt_hours(h, lang)

    if en:
        chain = (
            f" (cannot be under about {chain_weeks} weeks, because some work must happen in sequence)"
            if chain_weeks > team_weeks else ""
        )
        lines = [
            f"# Estimate: {project.title}",
            "",
            f"Prepared: {datetime.now(VN_TZ):%d %b %Y} · Estimate version: {v.version_id}",
            "",
            "## Summary",
            "",
            f"- **Most likely effort:** {hh(fc.p50_hours)} (modelled 80% interval: {hh(fc.p10_hours)} to {hh(fc.p90_hours)})",
            f"- **Suggested plan:** {hh(planned)} — enough in about {round(confidence)}% of simulated outcomes",
            f"- **Illustrative cost:** {_fmt_money(planned * rate, currency, lang)} (rate {_fmt_rate(rate, currency, lang)})",
            f"- **Time:** about {weeks} weeks with {people} people{chain}",
            "- **Review status:** Draft. A delivery lead must check scope, base hours and constraints before a client commitment; end-to-end brief-to-actual accuracy has not been validated for this team.",
            "",
            "## Scope of work",
            "",
        ]
    else:
        chain = (
            f" (không thể dưới khoảng {chain_weeks} tuần vì một số việc phải làm nối tiếp nhau)"
            if chain_weeks > team_weeks else ""
        )
        lines = [
            f"# Dự toán: {project.title}",
            "",
            f"Ngày lập: {datetime.now(VN_TZ):%d/%m/%Y} · Phiên bản dự toán: {v.version_id}",
            "",
            "## Tóm tắt",
            "",
            f"- **Khối lượng ước tính:** {hh(fc.p50_hours)} (thường dao động {hh(fc.p10_hours)} – {hh(fc.p90_hours)})",
            f"- **Đề xuất dự trù:** {hh(planned)} — đủ trong khoảng {round(confidence)}% kịch bản mô phỏng",
            f"- **Chi phí tham khảo:** {_fmt_money(planned * rate, currency, lang)} (đơn giá {_fmt_rate(rate, currency, lang)})",
            f"- **Thời gian:** khoảng {weeks} tuần với {people} người{chain}",
            "- **Trạng thái:** Dự toán nháp. Người phụ trách giao hàng cần kiểm tra phạm vi, giờ gốc và các ràng buộc trước khi cam kết với khách; độ chính xác từ brief đến giờ thực tế của nhóm này chưa được kiểm định.",
            "",
            "## Phạm vi công việc",
            "",
        ]
    pending = []
    excluded = []
    ordered = [r for r in v.requirements if r.req_id != "REQ-00"] + [r for r in v.requirements if r.req_id == "REQ-00"]
    for req in ordered:
        items = by_req.get(req.req_id, [])
        quote = req.evidence[0].quote if req.evidence else req.title
        if req.in_scope is False:
            scope_q = next((q for q in v.clarifications if q.question_id == f"CLAR-{req.req_id}"), None)
            if scope_q and scope_q.answer is None:
                pending.append((quote, scope_q.hours_if_true))
            else:
                excluded.append(quote)
            continue
        heading = req.title if req.req_id == "REQ-00" else quote
        shared = shared_by.get(req.req_id, [])
        if not items and shared:
            tag = ""
            if req.status.value == "assumed" and req.req_id != "REQ-00":
                tag = " *(not committed)*" if en else " *(chưa chốt)*"
            lines.append(f"### {heading}{tag}")
            lines.append("")
            intro = (
                "In scope. The hours are already counted above, and are not added again:"
                if en else
                "Nằm trong phạm vi. Số giờ đã được tính ở trên, không cộng thêm:"
            )
            lines.append(intro)
            lines.append("")
            for w in shared:
                owner = next((r for r in v.requirements if r.req_id == w.req_ids[0]), None)
                owner_quote = (owner.evidence[0].quote if owner and owner.evidence else owner.title) if owner else w.req_ids[0]
                where = f", under “{owner_quote}”" if en else f", trong mục “{owner_quote}”"
                lines.append(f"- {w.name} ({hh(pert_mean(w))}){where}")
            lines.append("")
            continue
        if not items:
            continue
        total = sum(pert_mean(w) for w in items)
        if req.status.value == "assumed" and req.req_id != "REQ-00":
            tag = " *(not committed)*" if en else " *(chưa chốt)*"
        else:
            tag = ""
        lines.append(f"### {heading} — {hh(total)}{tag}")
        lines.append("")
        for w in items:
            lines.append(f"- {w.name} ({roles.get(w.role, w.role)}): {hh(pert_mean(w))}")
        lines.append("")
    if pending:
        heading = "## Pending scope (excluded until confirmed)" if en else "## Phạm vi chưa chốt (chưa tính giờ)"
        lines += [heading, ""] + [f"- {quote} (+{hh(extra)} if confirmed)" if en else f"- {quote} (+{hh(extra)} nếu xác nhận làm)" for quote, extra in pending] + [""]
    if excluded:
        heading = "## Out of scope (confirmed not in this delivery)" if en else "## Ngoài phạm vi (đã chốt không làm)"
        lines += [heading, ""] + [f"- {q}" for q in excluded] + [""]

    answered = [q for q in v.clarifications if q.answer is not None]
    if answered:
        lines += ["## Recorded scope decisions" if en else "## Quyết định phạm vi đã ghi nhận", ""]
        for q in answered:
            decision = "Yes" if q.answer else "No"
            if not en:
                decision = "Có" if q.answer else "Không"
            lines.append(f"- **{'Question' if en else 'Câu hỏi'}:** {' '.join(q.question_text.split())}")
            lines.append(f"  - **{'Answer' if en else 'Trả lời'}:** {decision}")
            note = v.clarification_notes.get(q.question_id, "").strip()
            if note:
                lines.append(f"  - **{'Confirmation source' if en else 'Nguồn xác nhận'}:** {' '.join(note.split())}")
            if q.evidence:
                lines.append(f"  - **{'Brief clause' if en else 'Câu trong mô tả'}:** {' '.join(q.evidence[0].quote.split())}")
        lines.append("")

    open_q = [q for q in v.clarifications if q.answer is None]
    if open_q:
        lines += ["## Questions for the client" if en else "## Câu hỏi cần khách hàng xác nhận", ""]
        for q in open_q:
            if en:
                assumed = "includes" if q.current_assumption else "does not include"
                lines.append(f"- {q.question_text} — this estimate {assumed} it (about {hh(q.sensitivity_spread_hours)})")
            else:
                assumed = "đang tính" if q.current_assumption else "chưa tính"
                lines.append(f"- {q.question_text} — dự toán {assumed} phần này (khoảng {hh(q.sensitivity_spread_hours)})")
        lines.append("")
    notes = [f.claim for f in v.critic_findings if f.category not in HIDDEN_NOTES]
    if notes:
        lines += ["## Notes" if en else "## Lưu ý", ""] + [f"- {n}" for n in notes] + [""]
    if en:
        adjust = (
            f", and has been adjusted ×{fc.calibration_multiplier:.2f} from your earlier projects' actual hours."
            if fc.calibration_multiplier != 1 else "."
        )
        reader = (
            " The brief was also read by AI (Jev) to recognise the kind of work and clauses the client has not committed to."
            if v.reader == "rules+jev" else ""
        )
        how = (
            "Each requirement is taken from the exact wording of the brief and split into work with a low, typical, and high hour figure. "
            "The system runs 10,000 outcomes. The spread between an estimate and the actual hours comes from real data on more than 10,000 "
            "software tasks (the SiP dataset)"
            + adjust + reader
        )
        lines += ["## How this number was calculated", "", how, ""]
    else:
        lines += [
            "## Cách tính",
            "",
            "Mỗi yêu cầu được tách từ đúng câu chữ trong mô tả và chia thành công việc có số giờ ít nhất / thường gặp / nhiều nhất. "
            "Hệ thống chạy 10.000 kịch bản; mức chênh lệch giữa dự toán và thực tế được lấy từ dữ liệu thật của hơn 10.000 công việc "
            "phần mềm (bộ dữ liệu SiP)"
            + (f", và đã điều chỉnh ×{fc.calibration_multiplier:.2f} theo giờ thực tế của các dự án trước." if fc.calibration_multiplier != 1 else ".")
            + (" Phần đọc mô tả có dùng AI (Jev) để nhận ra loại việc và các yêu cầu chưa chốt." if v.reader == "rules+jev" else ""),
            "",
        ]
    return "\n".join(lines)


def wbs_csv(v: EstimateVersion, lang: str = "vi") -> str:
    lang = _lang(lang)
    en = lang == "en"
    roles = ROLE_EN if en else ROLE_VI
    quotes = {r.req_id: (r.evidence[0].quote if r.evidence else r.title) for r in v.requirements}
    in_scope = {r.req_id: r.in_scope is not False for r in v.requirements}
    buf = io.StringIO()
    buf.write("\ufeff")  # BOM so Excel opens the text correctly
    writer = csv.writer(buf)
    if en:
        writer.writerow(["Requirement (quoted from the brief)", "Work item", "Role", "Typical hours", "Low", "High", "On the critical path"])
        yes = "Yes"
    else:
        writer.writerow(["Yêu cầu (trích mô tả)", "Công việc", "Vai trò", "Giờ thường gặp", "Ít nhất", "Nhiều nhất", "Trên đường găng"])
        yes = "Có"
    critical = set(v.forecast.critical_path_ids or [])
    for w in v.wbs:
        if not in_scope.get(w.req_ids[0], True):
            continue
        covered = []
        for rid in w.req_ids:
            quote = quotes.get(rid, "")
            if quote and quote not in covered:
                covered.append(quote)
        writer.writerow([
            _csv_text(" | ".join(covered)), _csv_text(w.name), _csv_text(roles.get(w.role, w.role)), round(pert_mean(w), 1),
            w.optimistic_hours, w.pessimistic_hours, yes if w.item_id in critical else "",
        ])
    return buf.getvalue()
