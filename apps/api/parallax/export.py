"""Client-ready deliverables from an estimate version: a plain-language proposal and a CSV work list."""
from __future__ import annotations

import csv
import io
import math
from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))  # fixed offset: slim images ship without tzdata

from .schemas import EstimateVersion, Project, WorkItem

ROLE_VI = {"Backend": "Máy chủ", "Frontend": "Giao diện", "QA": "Kiểm thử", "DevOps": "Triển khai"}
HIDDEN_NOTES = {"scope_breadth", "quality_gate"}
HOURS_PER_PERSON_WEEK = 32


def pert_mean(w: WorkItem) -> float:
    return (w.optimistic_hours + 4 * w.most_likely_hours + w.pessimistic_hours) / 6


def hours_at(version: EstimateVersion, confidence: float) -> float:
    """Hours not exceeded in `confidence`% of simulated outcomes (linear between stored percentiles)."""
    fc = version.forecast
    points = {p: h for p, h in fc.percentile_curve}
    points.update({10: fc.p10_hours, 50: fc.p50_hours, 80: fc.p80_hours, 90: fc.p90_hours})
    pts = sorted(points.items())
    if confidence <= pts[0][0]:
        return pts[0][1]
    for (pa, ha), (pb, hb) in zip(pts, pts[1:]):
        if confidence <= pb:
            return ha + (confidence - pa) / (pb - pa) * (hb - ha)
    return pts[-1][1]


def _fmt_hours(h: float) -> str:
    return f"{round(h):,}".replace(",", ".") + " giờ"


def _fmt_money(amount: float, currency: str) -> str:
    if currency.upper() == "VND":
        return f"{amount / 1_000_000:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " triệu đồng"
    return f"${amount:,.0f}"


def proposal_markdown(project: Project, v: EstimateVersion, confidence: float = 80, rate: float = 500_000,
                      currency: str = "VND", people: int = 3) -> str:
    fc = v.forecast
    planned = hours_at(v, confidence)
    people = max(1, people)
    weeks = max(1, math.ceil(planned / (people * HOURS_PER_PERSON_WEEK)))
    chain_weeks = math.ceil((fc.critical_path_hours or 0) * fc.calibration_multiplier / HOURS_PER_PERSON_WEEK)
    by_req: dict[str, list[WorkItem]] = {}
    for w in v.wbs:
        by_req.setdefault(w.req_ids[0], []).append(w)

    lines = [
        f"# Dự toán: {project.title}",
        "",
        f"Ngày lập: {datetime.now(VN_TZ):%d/%m/%Y} · Phiên bản dự toán: {v.version_id}",
        "",
        "## Tóm tắt",
        "",
        f"- **Khối lượng ước tính:** {_fmt_hours(fc.p50_hours)} (thường dao động {_fmt_hours(fc.p10_hours)} – {_fmt_hours(fc.p90_hours)})",
        f"- **Đề xuất dự trù:** {_fmt_hours(planned)} — đủ trong khoảng {round(confidence)}% kịch bản mô phỏng",
        f"- **Chi phí dự kiến:** {_fmt_money(planned * rate, currency)} (đơn giá {f'{rate:,.0f}'.replace(',', '.')} {currency}/giờ)",
        f"- **Thời gian:** khoảng {weeks} tuần với {people} người"
        + (f" (không thể dưới khoảng {chain_weeks} tuần vì một số việc phải làm nối tiếp nhau)" if chain_weeks > weeks else ""),
        "",
        "## Phạm vi công việc",
        "",
    ]
    excluded = []
    ordered = [r for r in v.requirements if r.req_id != "REQ-00"] + [r for r in v.requirements if r.req_id == "REQ-00"]
    for req in ordered:
        items = by_req.get(req.req_id, [])
        quote = req.evidence[0].quote if req.evidence else req.title
        if req.in_scope is False:
            excluded.append(quote)
            continue
        if not items:
            continue
        total = sum(pert_mean(w) for w in items)
        heading = req.title if req.req_id == "REQ-00" else quote
        tag = " *(chưa chốt)*" if req.status.value == "assumed" and req.req_id != "REQ-00" else ""
        lines.append(f"### {heading} — {_fmt_hours(total)}{tag}")
        lines.append("")
        for w in items:
            lines.append(f"- {w.name} ({ROLE_VI.get(w.role, w.role)}): {_fmt_hours(pert_mean(w))}")
        lines.append("")
    if excluded:
        lines += ["## Ngoài phạm vi (đã chốt không làm)", ""] + [f"- {q}" for q in excluded] + [""]

    open_q = [q for q in v.clarifications if q.answer is None]
    if open_q:
        lines += ["## Câu hỏi cần khách hàng xác nhận", ""]
        for q in open_q:
            assumed = "đang tính" if q.current_assumption else "chưa tính"
            lines.append(f"- {q.question_text} — dự toán {assumed} phần này (khoảng {_fmt_hours(q.sensitivity_spread_hours)})")
        lines.append("")
    notes = [f.claim for f in v.critic_findings if f.category not in HIDDEN_NOTES]
    if notes:
        lines += ["## Lưu ý", ""] + [f"- {n}" for n in notes] + [""]
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


def wbs_csv(v: EstimateVersion) -> str:
    quotes = {r.req_id: (r.evidence[0].quote if r.evidence else r.title) for r in v.requirements}
    in_scope = {r.req_id: r.in_scope is not False for r in v.requirements}
    buf = io.StringIO()
    buf.write("\ufeff")  # BOM so Excel opens Vietnamese text correctly
    writer = csv.writer(buf)
    writer.writerow(["Yêu cầu (trích mô tả)", "Công việc", "Vai trò", "Giờ thường gặp", "Ít nhất", "Nhiều nhất", "Trên đường găng"])
    critical = set(v.forecast.critical_path_ids or [])
    for w in v.wbs:
        if not in_scope.get(w.req_ids[0], True):
            continue
        writer.writerow([
            quotes.get(w.req_ids[0], ""), w.name, ROLE_VI.get(w.role, w.role), round(pert_mean(w), 1),
            w.optimistic_hours, w.pessimistic_hours, "Có" if w.item_id in critical else "",
        ])
    return buf.getvalue()
