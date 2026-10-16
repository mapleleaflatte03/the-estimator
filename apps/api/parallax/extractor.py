"""Evidence-backed requirement & WBS extractor for PARALLAX.

Every requirement comes from a clause of the actual brief: the brief is
segmented into numbered/bulleted items and sentences, each clause is kept as
an exact verbatim quote, classified against a component taxonomy (Vietnamese
and English, with or without diacritics) and decomposed into work items.
Nothing is emitted unless it is traceable to a clause, except standard
engineering work (setup, QA, deployment), which is marked ASSUMED.

Hour figures in the component catalogue are the engine's *prior* estimates
(assumptions). The empirical layer (systemic spread from real SiP data and the
bias multiplier learned from recorded actuals) is applied in the forecast.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional, Sequence

from .estimation.engine import synthesize_forecast
from .jev import KIND_CONFIDENCE_MIN, TENTATIVE_MIN, ClauseReading
from .provenance import validate_evidence_against_sources
from .schemas import (
    ClarificationQuestion,
    CriticFinding,
    EstimateVersion,
    EvidenceSpan,
    RequirementNode,
    VerificationStatus,
    WorkItem,
)

MODEL_TAG = "PARALLAX-v2-clause"
MAX_BREADTH_FACTOR = 2.5


def fold(text: str) -> str:
    """Lowercase and strip Vietnamese diacritics so 'Đăng nhập' == 'dang nhap'."""
    text = text.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


# --------------------------------------------------------------------------- #
# Component taxonomy
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Template:
    code: str
    role: str
    name: str
    o: float
    m: float
    p: float


@dataclass(frozen=True)
class Component:
    key: str
    label: str
    pattern: str
    templates: tuple[Template, ...]
    shared: bool = False  # one implementation serves every clause that mentions it
    scales_with_breadth: bool = False


T = Template
COMPONENTS: tuple[Component, ...] = (
    Component("auth", "Authentication", r"\bsso\b|single sign|oauth|saml|\bldap\b|okta|keycloak|dang nhap|xac thuc|\blogin\b|log in|sign[- ]?in|authenticat|mat khau|password|\b2fa\b|\bmfa\b|\botp\b",
              (T("BE", "Backend", "Authentication service & session/token management", 10, 18, 34),
               T("FE", "Frontend", "Login, logout & session-expiry flows", 6, 12, 22)), shared=True),
    Component("rbac", "Roles & permissions", r"phan quyen|vai tro|\broles?\b|permission|rbac|quyen truy cap|access control|\badmin\b",
              (T("BE", "Backend", "Role/permission model & policy enforcement", 8, 14, 26),
               T("FE", "Frontend", "Role-aware UI & role administration", 6, 10, 18)), shared=True),
    Component("audit", "Audit trail", r"audit|nhat ky|lich su thay doi|truy vet|activity log|change log|ghi nhan moi thay doi",
              (T("BE", "Backend", "Audit trail capture, storage & query", 6, 10, 20),), shared=True),
    Component("integration", "External integration", r"tich hop|integrat|\bapis?\b|webhook|dong bo (voi|tu|sang|du lieu (voi|tu|sang))|sync (with|to|from)|ket noi (voi|toi|den)|connector|\berp\b|\bsap\b|\bcrm\b|third[- ]party|ben thu ba|shopee|lazada|tiktok|shopify|woocommerce|salesforce|hubspot|zendesk|misa|odoo|haravan|quickbooks|xero",
              (T("RETRY", "Backend", "Retry, idempotency & reconciliation for external calls", 6, 12, 24),)),
    Component("reporting", "Reporting & dashboards", r"bao cao|report|dashboard|bang dieu khien|thong ke|\bkpis?\b|bieu do|chart|analytics|gantt|doi soat",
              (T("BE", "Backend", "Reporting queries & aggregation", 8, 16, 30),
               T("FE", "Frontend", "Dashboard, charts & report views", 10, 18, 34)), scales_with_breadth=True),
    Component("export", "File export", r"\bxuat\b(?! hien| phat| xu| khau| sac)|export|tai xuong|download",
              (T("BE", "Backend", "Export generation (PDF/Excel/CSV)", 6, 12, 24),)),
    Component("import", "Data import", r"(?<!dang )\bnhap\b(?! lieu| vien| hoc| mon)|import|\bupload\b|tai len|\bcsv\b",
              (T("BE", "Backend", "Import pipeline: parsing, validation & error report", 10, 18, 36),
               T("FE", "Frontend", "Upload & import review screen", 4, 8, 16))),
    Component("migration", "Data migration", r"migrat|chuyen doi du lieu|di chuyen du lieu|du lieu cu|du lieu lich su|legacy data|historical data",
              (T("BE", "Backend", "Legacy data mapping & migration scripts", 14, 26, 52),)),
    Component("notification", "Notifications", r"thong bao|notif|gui email|email thong bao|send email|\bsms\b|push|nhac nho|reminder|canh bao|\balerts?\b|zalo oa",
              (T("BE", "Backend", "Notification service: templates, queue & delivery tracking", 8, 16, 30),), shared=True),
    Component("scheduling", "Scheduling & dispatch", r"\blich\b(?! su)|lich trinh|calendar|schedul|dieu phoi|phan cong|dispatch|dat lich|booking|\bca lam|\bshifts?\b|roster",
              (T("BE", "Backend", "Scheduling engine: availability, assignment rules & conflicts", 16, 30, 60),
               T("FE", "Frontend", "Calendar / dispatch board", 14, 26, 50)), scales_with_breadth=True),
    Component("mobile", "Mobile client", r"mobile|di dong|(?<!so )dien thoai|android|\bios\b|smartphone|react native|flutter|\bpwa\b|may tinh bang|tablet",
              (T("FE", "Frontend", "Mobile client (cross-platform / PWA)", 24, 45, 90),), shared=True),
    Component("offline", "Offline mode", r"offline|ngoai tuyen|mat ket noi|khong co mang|mat mang|no connectivity",
              (T("BE", "Backend", "Sync API with conflict resolution for offline edits", 12, 22, 44),
               T("FE", "Frontend", "Local storage & background sync queue", 12, 22, 44)), shared=True),
    Component("realtime", "Real-time updates", r"real[- ]?time|thoi gian thuc|tuc thoi|websocket|live update",
              (T("BE", "Backend", "Real-time event channel (WebSocket/SSE)", 8, 16, 32),
               T("FE", "Frontend", "Live UI updates", 4, 8, 16)), shared=True),
    Component("performance", "Performance / load", r"\d[\d.,]*\s*(req|requests?|yeu cau|rps|tps)\b|chiu tai|tai cao|high load|concurren|dong thoi|flash sale|latency|do tre|throughput|nghen",
              (T("LOAD", "DevOps", "Load testing & performance tuning", 12, 24, 48),
               T("CACHE", "Backend", "Caching / queueing for peak load", 10, 20, 40)), shared=True),
    Component("ai", "AI / LLM", r"tri tue nhan tao|chatbot|\bbot\b|\bllms?\b|\bgpt|openai|machine learning|hoc may|\bnlp\b|phan loai tu dong|\bocr\b|tro ly ao|tra loi tu dong",
              (T("BE", "Backend", "AI pipeline: prompts, guardrails, fallbacks & cost controls", 20, 36, 72),
               T("EVAL", "QA", "AI evaluation set & answer-quality metrics", 8, 16, 32)), shared=True),
    Component("rag", "Retrieval / knowledge base", r"\brag\b|retrieval|embedding|vector|knowledge base|tri thuc|semantic search|tuong dong ngu nghia",
              (T("BE", "Backend", "Document ingestion, chunking & vector index", 12, 24, 48),), shared=True),
    Component("search", "Search & filtering", r"tim kiem|search|bo loc|\bfilters?\b|loc theo|full[- ]text",
              (T("BE", "Backend", "Search & filtering API with indexes", 6, 12, 24),
               T("FE", "Frontend", "Search & filter UI", 4, 8, 16)), shared=True),
    Component("payment", "Payments", r"thanh toan|payment|hoa don|invoice|billing|vi dien tu|stripe|vnpay|momo|paypal|zalopay|subscription",
              (T("BE", "Backend", "Payment gateway integration, webhooks & reconciliation", 16, 28, 56),), shared=True),
    Component("workflow", "Workflow & approvals", r"phe duyet|approval|approve|quy trinh|workflow|trang thai|\bstatus\b|\bduyet\b",
              (T("BE", "Backend", "Workflow / status lifecycle & approval rules", 10, 20, 40),
               T("FE", "Frontend", "Status tracking & approval UI", 6, 12, 22)), scales_with_breadth=True),
    Component("files", "Files & media", r"dinh kem|attachment|hinh anh|anh chup|chup anh|\bphotos?\b|\bimages?\b|chu ky|signature|\btep\b",
              (T("BE", "Backend", "File storage & attachment handling", 6, 12, 24),
               T("FE", "Frontend", "Attachment / photo capture UI", 4, 8, 16)), shared=True),
    Component("maps", "Maps & location", r"ban do|\bmaps?\b|\bgps\b|vi tri|location|dinh vi|tuyen duong|\broutes?\b",
              (T("BE", "Backend", "Geolocation & map provider integration", 10, 20, 40),
               T("FE", "Frontend", "Map view", 6, 12, 24)), shared=True),
    Component("widget", "Embeddable widget", r"widget|nhung (vao )?(website|web|trang)|\bembed",
              (T("FE", "Frontend", "Embeddable web widget (isolated styles, auth handshake)", 10, 20, 40),), shared=True),
    Component("i18n", "Internationalization", r"da ngon ngu|multi[- ]?lang|\bi18n\b|localization|tieng anh va tieng viet",
              (T("FE", "Frontend", "Internationalization & translations", 6, 12, 24),), shared=True),
    Component("security", "Security & compliance", r"bao mat|security|ma hoa|encrypt|gdpr|\bpci\b|hipaa|tuan thu|compliance|pen ?test|owasp",
              (T("SEC", "QA", "Security hardening & review", 8, 16, 32),), shared=True),
    Component("crud", "Data management", r"quan ly|manage|\btao\b|create|cap nhat|update|\bxoa\b|delete|chinh sua|\bedit|theo doi|\btrack|danh sach|\blists?\b|ho so|profile|nhap lieu|\bforms?\b|bieu mau|cho phep|\ballow",
              (T("BE", "Backend", "Domain model & CRUD API", 10, 18, 34),
               T("FE", "Frontend", "Management screens & forms", 10, 18, 34)), scales_with_breadth=True),
)
GENERIC = Component("generic", "Unclassified feature", "",
                    (T("BE", "Backend", "Feature backend (generic sizing)", 12, 24, 56),
                     T("FE", "Frontend", "Feature UI (generic sizing)", 10, 20, 48)))
_COMPILED = [(c, re.compile(c.pattern)) for c in COMPONENTS]
COMPONENT_BY_KEY = {c.key: c for c in COMPONENTS}
# "AI" only counts in capitals: folded Vietnamese "ai" means "who" ("lịch sử ai đã sửa").
_AI_ACRONYM = re.compile(r"(?<![\w])AI(?![\w])")


def _match_components(text: str) -> list[Component]:
    folded = fold(text)
    matched = [c for c, rx in _COMPILED if rx.search(folded)]
    if _AI_ACRONYM.search(text) and COMPONENT_BY_KEY["ai"] not in matched:
        matched.append(COMPONENT_BY_KEY["ai"])
    return matched


def clause_texts(brief_text: str, source_docs: Optional[dict[str, str]] = None) -> list[str]:
    """Clause texts the extractor will read (used to fetch AI readings up front)."""
    clauses = segment("brief.txt", brief_text)
    for name, text in (source_docs or {}).items():
        if name != "brief.txt" and text and text.strip() != brief_text.strip():
            clauses.extend(segment(name, text))
    return [c.text for c in clauses if not c.is_title]

KNOWN_SYSTEMS = {
    r"\berp\b": "ERP", r"\bsap\b": "SAP", r"\bcrm\b": "CRM", r"shopee": "Shopee", r"lazada": "Lazada",
    r"\btiki\b": "Tiki", r"tiktok": "TikTok Shop", r"shopify": "Shopify", r"woocommerce": "WooCommerce",
    r"amazon": "Amazon", r"salesforce": "Salesforce", r"hubspot": "HubSpot", r"zendesk": "Zendesk",
    r"notion": "Notion", r"google sheets?": "Google Sheets", r"google calendar": "Google Calendar",
    r"\bmisa\b": "MISA", r"odoo": "Odoo", r"haravan": "Haravan", r"\bsapo\b": "Sapo", r"\bghn\b": "GHN",
    r"\bghtk\b": "GHTK", r"viettel post": "Viettel Post", r"quickbooks": "QuickBooks", r"\bxero\b": "Xero",
    r"\bslack\b": "Slack", r"microsoft teams|\bms teams\b": "Microsoft Teams", r"\bzalo\b": "Zalo",
    r"sharepoint": "SharePoint", r"\bjira\b": "Jira",
}
_CHANNELS = ((r"email", "Email"), (r"\bsms\b", "SMS"), (r"\bzalo\b", "Zalo"), (r"\bpush\b", "Push"),
             (r"\bslack\b", "Slack"), (r"telegram", "Telegram"))
_REQUIREMENT_MARKERS = re.compile(
    r"\bcan\b|\bphai\b|yeu cau|cho phep|ho tro|mong muon|\bmuon\b|bat buoc|xay dung|phat trien|tich hop|"
    r"\bmust\b|\bshould\b|\bneeds?\b|requir|\ballow|\bsupports?\b|\bwants?\b|\bbuild\b|\bdevelop"
)
_HEDGES = re.compile(
    r"can xem xet|xem xet kha nang|co the can|co the se|co the bo sung|neu can|neu co the|tuy chon|"
    r"giai doan sau|giai doan 2|sau nay|chua ro|chua xac dinh|chua chot|chua co tai lieu|chua co api|"
    r"du kien|kha nang cao|\boptional\b|nice to have|phase 2|later phase|\bmaybe\b|\bmight\b|possibly|"
    r"\btbd\b|to be (?:decided|confirmed|defined)|if possible|\bconsider"
)
_UNDOCUMENTED = re.compile(r"chua co tai lieu|chua co api|khong co api|no api|undocumented|no documentation")
_HAS_DOCS = re.compile(r"tai lieu api|api doc|swagger|openapi|sandbox|rest api cong khai|public api")
_PLATFORM = re.compile(r"\bios\b|android|\bpwa\b|react native|flutter|web app|trinh duyet|browser")
_TITLE = re.compile(r"^\s*(du an|ten du an|project|title|tieu de|de bai)\s*[:\-]", re.I)
_BULLET = re.compile(r"^\s*(?:\d{1,2}[.)]|[-*•–]|[a-zA-Z][.)])\s+")
_ACTION_SPLIT = re.compile(r",|;|\bva\b|\band\b|/")


@dataclass
class Clause:
    doc: str
    text: str
    index: int
    is_item: bool
    is_title: bool = False

    @property
    def heading(self) -> Optional[str]:
        head, sep, _ = self.text.partition(":")
        if sep and 2 <= len(head) <= 60:
            return head.strip()
        return None

    @property
    def body(self) -> str:
        head = self.heading
        return self.text.split(":", 1)[1].strip() if head else self.text


def _split_sentences(line: str) -> list[str]:
    parts, start = [], 0
    for m in re.finditer(r"[.!?;]\s+", line):
        nxt = line[m.end(): m.end() + 1]
        if nxt and (nxt.isupper() or nxt.isdigit() or nxt in "\"“("):
            parts.append(line[start: m.end()].strip())
            start = m.end()
    parts.append(line[start:].strip())
    return [p for p in parts if len(p) >= 5]


def segment(doc: str, text: str) -> list[Clause]:
    clauses: list[Clause] = []
    lines = [ln for ln in text.splitlines() if ln.strip()]
    has_bullets = sum(bool(_BULLET.match(ln)) for ln in lines) >= 2
    for i, line in enumerate(lines):
        bullet = _BULLET.match(line)
        body = line[bullet.end():].strip() if bullet else line.strip()
        if len(body) < 5:
            continue
        is_title = i == 0 and (bool(_TITLE.match(fold(body))) or (has_bullets and not bullet and len(body) < 160))
        if bullet or is_title:
            clauses.append(Clause(doc, body, len(clauses), is_item=bool(bullet), is_title=is_title))
        else:
            for sentence in _split_sentences(body):
                clauses.append(Clause(doc, sentence, len(clauses), is_item=False))
    return clauses


def _systems(folded: str) -> list[str]:
    found = []
    for pattern, name in KNOWN_SYSTEMS.items():
        if re.search(pattern, folded) and name not in found:
            found.append(name)
    return found


def _breadth(clause: Clause) -> int:
    segments = [s for s in _ACTION_SPLIT.split(fold(clause.body)) if len(s.strip()) >= 3]
    return max(1, len(segments))


def _short_title(clause: Clause) -> str:
    if clause.heading:
        return clause.heading
    text = clause.text.rstrip(".")
    if len(text) <= 70:
        return text
    cut = text[:70].rsplit(" ", 1)[0]
    return cut + "…"


# --------------------------------------------------------------------------- #
# Localized text
# --------------------------------------------------------------------------- #
_TEXT = {
    "vi": {
        "foundation": "Chuẩn bị, kiểm thử & bàn giao",
        "foundation_desc": "Những việc luôn cần làm dù mô tả không nhắc tới.",
        "detected": "Gồm",
        "excluded": "Đã bỏ khỏi dự án.",
        "q_scope": "Có làm phần “{title}” trong đợt này không?",
        "q_scope_why": "Mô tả ghi “{hedge}” nên chưa chắc có làm. Hiện dự toán đang tính cả phần này.",
        "q_scope_why_ai": "{hedge} (cách diễn đạt cho thấy chưa chốt). Hiện dự toán đang tính cả phần này.",
        "q_ai_kind": "Phần “{title}” có cần thêm {kind} không?",
        "q_ai_kind_why": "AI nhận định câu này có liên quan tới {kind} (chắc chắn {p}%), nhưng dự toán hiện chưa tính phần đó.",
        "c_hedge_ai": "Phần “{title}” có vẻ chưa chốt: {hedge}. Hãy trả lời câu hỏi để chốt.",
        "q_platform": "Có cần làm riêng ứng dụng cho cả iPhone và Android không?",
        "q_platform_why": "Mô tả có nhắc điện thoại nhưng chưa nói loại máy. Hiện đang tính một ứng dụng dùng chung.",
        "q_dataq": "Dữ liệu cũ có cần làm sạch, sửa lỗi trước khi đưa vào không?",
        "q_dataq_why": "Mô tả chưa nói dữ liệu cũ có gọn gàng không. Hiện đang giả định dữ liệu sạch.",
        "q_api": "Có cần tìm hiểu thêm cách kết nối với {system} vì chưa có tài liệu không?",
        "q_api_why": "Kết nối với hệ thống chưa có tài liệu thường tốn thêm thời gian.",
        "c_hedge": "Phần “{title}” chưa chắc chắn (“{hedge}”). Hãy trả lời câu hỏi để chốt.",
        "ai_hedge": "AI đánh giá {p}% khả năng khách chưa chốt",
        "c_generic": "Chưa rõ “{title}” là loại việc gì nên ước tính có thể lệch nhiều. Nên nhờ người có kinh nghiệm xem lại.",
        "c_perf": "Có yêu cầu chịu tải cao, đã cộng thêm thời gian kiểm tra tốc độ.",
        "c_integrations": "Cần kết nối với {n} hệ thống bên ngoài ({names}). Đây thường là phần dễ phát sinh.",
        "c_qa": "Thời gian kiểm thử chiếm {share:.0f}% tổng.",
        "c_nfr": "Mô tả chưa nói về tốc độ, bảo mật hay nơi đặt máy chủ. Nên bổ sung.",
        "c_breadth": "“{title}” gồm {n} việc nhỏ nên được tính nhiều giờ hơn.",
    },
    "en": {
        "foundation": "Engineering foundation & delivery",
        "foundation_desc": "Standard engineering work not stated in the brief: environments/CI-CD, core architecture, testing, deployment.",
        "detected": "Detected components",
        "excluded": "Excluded from scope by clarification answer.",
        "q_scope": "Is “{title}” in scope for this delivery?",
        "q_scope_why": "The brief uses tentative wording (“{hedge}”). The estimate currently includes it; answering “No” removes {n} work item(s).",
        "q_scope_why_ai": "{hedge}. The estimate currently includes it; answering “No” removes {n} work item(s).",
        "q_ai_kind": "Does “{title}” also need {kind}?",
        "q_ai_kind_why": "AI reads this clause as involving {kind} ({p}% confident), which the estimate does not include yet.",
        "c_hedge_ai": "“{title}” looks uncommitted: {hedge}. Answer the question to settle it.",
        "q_platform": "Are separate native apps required for both iOS and Android (instead of one cross-platform/PWA build)?",
        "q_platform_why": "The brief mentions mobile use but no platform. The estimate assumes a single cross-platform/PWA codebase.",
        "q_dataq": "Does imported/migrated data need cleansing, normalisation and de-duplication first?",
        "q_dataq_why": "The brief does not describe source data quality, format or volume. The estimate assumes clean, well-formed data.",
        "q_api": "Does {system} lack a documented API / sandbox, requiring discovery or reverse-engineering?",
        "q_api_why": "The brief requires integrating {system} but does not mention API documentation; undocumented interfaces are a common overrun source.",
        "c_hedge": "Tentative wording (“{hedge}”) for “{title}”; included as an assumption and turned into a clarification question.",
        "ai_hedge": "AI rates it {p}% likely the client has not committed",
        "c_generic": "Could not classify “{title}”; sized with a generic, wide-range template. Needs expert review.",
        "c_perf": "The brief states load/performance requirements; load testing and a cache/queue layer were added to the WBS.",
        "c_integrations": "The brief requires {n} external integrations ({names}); each gets its own adapter plus retry/reconciliation.",
        "c_qa": "QA is {share:.0f}% of development hours (minimum threshold 15%).",
        "c_nfr": "The brief states no non-functional requirements (performance, security, hosting). Default assumptions may be wrong.",
        "c_breadth": "“{title}” lists {n} actions/objects; template hours scaled by {factor:.2f} for breadth.",
    },
}


VI_NAMES = {
    "Authentication service & session/token management": "Đăng nhập & quản lý phiên (máy chủ)",
    "Login, logout & session-expiry flows": "Màn hình đăng nhập, đăng xuất",
    "Role/permission model & policy enforcement": "Phân quyền người dùng (máy chủ)",
    "Role-aware UI & role administration": "Giao diện quản lý quyền",
    "Audit trail capture, storage & query": "Lưu lịch sử thay đổi",
    "Retry, idempotency & reconciliation for external calls": "Xử lý lỗi kết nối & đối soát dữ liệu",
    "Reporting queries & aggregation": "Tổng hợp số liệu báo cáo",
    "Dashboard, charts & report views": "Màn hình báo cáo & biểu đồ",
    "Export generation (PDF/Excel/CSV)": "Xuất file (PDF, Excel, CSV)",
    "Import pipeline: parsing, validation & error report": "Đọc & kiểm tra file nhập vào",
    "Upload & import review screen": "Màn hình tải file lên",
    "Legacy data mapping & migration scripts": "Chuyển dữ liệu cũ sang hệ thống mới",
    "Notification service: templates, queue & delivery tracking": "Hệ thống gửi thông báo",
    "Scheduling engine: availability, assignment rules & conflicts": "Xử lý lịch & phân công",
    "Calendar / dispatch board": "Màn hình lịch & điều phối",
    "Mobile client (cross-platform / PWA)": "Ứng dụng điện thoại",
    "Sync API with conflict resolution for offline edits": "Đồng bộ dữ liệu khi có mạng lại",
    "Local storage & background sync queue": "Lưu tạm trên máy khi mất mạng",
    "Real-time event channel (WebSocket/SSE)": "Cập nhật tức thời (máy chủ)",
    "Live UI updates": "Hiển thị cập nhật tức thời",
    "Load testing & performance tuning": "Kiểm tra chịu tải & tối ưu tốc độ",
    "Caching / queueing for peak load": "Tăng tốc khi đông người dùng",
    "AI pipeline: prompts, guardrails, fallbacks & cost controls": "Xử lý AI (câu lệnh, giới hạn, dự phòng)",
    "AI evaluation set & answer-quality metrics": "Kiểm tra chất lượng câu trả lời AI",
    "Document ingestion, chunking & vector index": "Nạp tài liệu & tìm kiếm theo ý nghĩa",
    "Search & filtering API with indexes": "Tìm kiếm & lọc (máy chủ)",
    "Search & filter UI": "Ô tìm kiếm & bộ lọc",
    "Payment gateway integration, webhooks & reconciliation": "Kết nối cổng thanh toán",
    "Workflow / status lifecycle & approval rules": "Quy trình & trạng thái xử lý",
    "Status tracking & approval UI": "Màn hình theo dõi trạng thái & duyệt",
    "File storage & attachment handling": "Lưu trữ file đính kèm",
    "Attachment / photo capture UI": "Chụp ảnh & đính kèm file",
    "Geolocation & map provider integration": "Kết nối bản đồ & vị trí",
    "Map view": "Màn hình bản đồ",
    "Embeddable web widget (isolated styles, auth handshake)": "Khung chat nhúng vào website",
    "Internationalization & translations": "Hỗ trợ nhiều ngôn ngữ",
    "Security hardening & review": "Rà soát bảo mật",
    "Domain model & CRUD API": "Lưu trữ & xử lý dữ liệu",
    "Management screens & forms": "Màn hình quản lý & nhập liệu",
    "Feature backend (generic sizing)": "Phần máy chủ (ước tính chung)",
    "Feature UI (generic sizing)": "Phần giao diện (ước tính chung)",
    "Bidirectional sync: change detection & conflict resolution": "Đồng bộ hai chiều & xử lý xung đột",
    "Webhook endpoint, signature checks & event queue": "Nhận sự kiện tự động từ hệ thống khác",
    "Second native platform build & store release": "Làm thêm ứng dụng cho loại máy thứ hai",
    "Data cleansing, normalisation & de-duplication rules": "Làm sạch & chuẩn hóa dữ liệu",
    "Repository, environments & CI/CD pipeline": "Chuẩn bị môi trường làm việc",
    "Core architecture, shared data model & API conventions": "Thiết kế khung hệ thống",
    "Integration & regression test suite": "Kiểm thử toàn bộ",
    "End-to-end flows & UAT support": "Chạy thử cùng khách hàng",
    "Production deployment, monitoring & handover": "Đưa lên chạy thật & bàn giao",
}
VI_COMPONENTS = {
    "auth": "đăng nhập", "rbac": "phân quyền", "audit": "lịch sử thay đổi", "integration": "kết nối hệ thống khác",
    "reporting": "báo cáo", "export": "xuất file", "import": "nhập file", "migration": "chuyển dữ liệu cũ",
    "notification": "thông báo", "scheduling": "lịch & phân công", "mobile": "điện thoại", "offline": "dùng khi mất mạng",
    "realtime": "cập nhật tức thời", "performance": "chịu tải", "ai": "AI", "rag": "tìm kiếm tài liệu",
    "search": "tìm kiếm", "payment": "thanh toán", "workflow": "quy trình & trạng thái", "files": "ảnh & file",
    "maps": "bản đồ", "widget": "khung nhúng website", "i18n": "nhiều ngôn ngữ", "security": "bảo mật",
    "crud": "quản lý dữ liệu", "generic": "chưa phân loại",
}


def _vi_name(name: str) -> str:
    if name in VI_NAMES:
        return VI_NAMES[name]
    for prefix, vi in (("Integration adapter: ", "Kết nối với "), ("API discovery spike: ", "Tìm hiểu cách kết nối "),
                       ("Additional notification channel: ", "Thêm kênh thông báo ")):
        if name.startswith(prefix):
            rest = name[len(prefix):].replace("external system", "hệ thống bên ngoài")
            return vi + rest
    return name


def _lang(text: str) -> str:
    return "vi" if re.search(r"[ăâđêôơưàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]", text.lower()) else "en"


def _pert_mean(item: WorkItem) -> float:
    return (item.optimistic_hours + 4 * item.most_likely_hours + item.pessimistic_hours) / 6


@dataclass
class _Draft:
    req: RequirementNode
    items: list[WorkItem] = field(default_factory=list)
    hedge: Optional[str] = None
    clause: Optional[Clause] = None


def _build_items(req_id: str, title: str, components: list[Component], systems: list[str], folded: str,
                 factor: float, breadth: int, shared_items: dict[str, list[WorkItem]],
                 register: bool) -> list[WorkItem]:
    items: list[WorkItem] = []
    for comp in components:
        if comp.shared and comp.key in shared_items:
            if register:
                for item in shared_items[comp.key]:
                    if req_id not in item.req_ids:
                        item.req_ids.append(req_id)
            continue
        scale = factor if comp.scales_with_breadth else 1.0
        created: list[WorkItem] = []
        if comp.key == "integration":
            webhook_only = not systems and "webhook" in folded
            for n, sysname in enumerate(systems or ["external system"], start=1):
                created.append(WorkItem(
                    item_id=f"{req_id}-INT{n}", req_ids=[req_id], role="Backend",
                    name="Webhook endpoint, signature checks & event queue" if webhook_only
                    else f"Integration adapter: {sysname}",
                    optimistic_hours=12, most_likely_hours=24, pessimistic_hours=48,
                    basis="Engine prior per external system",
                ))
            if re.search(r"hai chieu|two[- ]way|bidirectional|2 chieu", folded):
                created.append(WorkItem(
                    item_id=f"{req_id}-INT-BIDI", req_ids=[req_id], role="Backend",
                    name="Bidirectional sync: change detection & conflict resolution",
                    optimistic_hours=12, most_likely_hours=22, pessimistic_hours=44,
                    basis="Engine prior; triggered by two-way sync wording",
                ))
        for tpl in comp.templates:
            prefix = comp.key.upper() if comp.shared else f"{req_id}-{comp.key.upper()}"
            created.append(WorkItem(
                item_id=f"{prefix}-{tpl.code}", req_ids=[req_id], role=tpl.role,
                name=tpl.name,
                optimistic_hours=round(tpl.o * scale, 1),
                most_likely_hours=round(tpl.m * scale, 1),
                pessimistic_hours=round(tpl.p * scale, 1),
                basis=("Engine prior" if scale == 1 else f"Engine prior x{scale:.2f} (breadth {breadth})")
                + ("; generic template — needs review" if comp is GENERIC else ""),
            ))
        if comp.key == "notification":
            channels = [name for rx, name in _CHANNELS if re.search(rx, folded)]
            for ch in channels[1:]:
                created.append(WorkItem(
                    item_id=f"NOTIFICATION-{ch.upper()}", req_ids=[req_id], role="Backend",
                    name=f"Additional notification channel: {ch}",
                    optimistic_hours=4, most_likely_hours=8, pessimistic_hours=16,
                    basis="Engine prior per channel beyond the first",
                ))
        if comp.shared and register:
            shared_items[comp.key] = created
        items.extend(created)
    return items


def _scope_question(L: dict, qid: str, req_id: str, title: str, hedge: str, items: list[WorkItem],
                    evidence: list[EvidenceSpan], answers: dict[str, bool], ai: bool = False) -> ClarificationQuestion:
    return ClarificationQuestion(
        question_id=qid, assumption_id=f"ASSUMP-{req_id}-SCOPE",
        question_text=L["q_scope"].format(title=title),
        context_reason=L["q_scope_why_ai" if ai else "q_scope_why"].format(hedge=hedge, n=len(items)),
        hours_if_false=0.0, hours_if_true=round(sum(_pert_mean(i) for i in items), 1),
        affected_item_ids=[i.item_id for i in items], evidence=evidence,
        current_assumption=True, answer=answers.get(qid),
    )


def _scale_to(item: WorkItem, hours: float) -> None:
    """Rescale a three-point estimate so its PERT mean equals `hours` (shape preserved)."""
    factor = hours / _pert_mean(item)
    item.optimistic_hours = round(item.optimistic_hours * factor, 1) or 0.1
    item.most_likely_hours = round(item.most_likely_hours * factor, 1) or 0.1
    item.pessimistic_hours = max(item.most_likely_hours, round(item.pessimistic_hours * factor, 1))
    item.optimistic_hours = min(item.optimistic_hours, item.most_likely_hours)


def _apply_overrides(items: list[WorkItem], overrides: dict) -> None:
    for item in items:
        edit = overrides.get(item.item_id)
        if not edit:
            continue
        if edit.get("name"):
            item.name = str(edit["name"])[:200]
        if edit.get("hours"):
            _scale_to(item, float(edit["hours"]))
        item.basis = "Edited by user"


def _apply_manual_edits(feature_items: list[WorkItem], edits: dict, req_ids: set[str]) -> list[WorkItem]:
    removed = set(edits.get("removed") or [])
    kept = [i for i in feature_items if i.item_id not in removed]
    kept_ids = {i.item_id for i in kept}
    for item in kept:
        item.dependencies = [d for d in item.dependencies if d in kept_ids or d == "CORE-ARCH"] or ["CORE-ARCH"]
    _apply_overrides(kept, edits.get("overrides") or {})
    for n, add in enumerate(edits.get("added") or [], start=1):
        hours = float(add["hours"])
        m = round(hours / 1.0417, 1)
        req = add.get("req_id") if add.get("req_id") in req_ids else "REQ-00"
        kept.append(WorkItem(
            item_id=str(add.get("item_id") or f"USER-{n:02d}"), req_ids=[req], name=str(add["name"])[:200],
            role=add.get("role") if add.get("role") in ("Backend", "Frontend", "QA", "DevOps") else "Backend",
            dependencies=["CORE-ARCH"], optimistic_hours=round(m * 0.75, 1), most_likely_hours=m,
            pessimistic_hours=round(m * 1.5, 1), basis="Added by user",
        ))
    return kept


def extract_scope_and_wbs(
    project_id: str,
    brief_text: str,
    source_docs: Optional[dict[str, str]] = None,
    clarification_answers: Optional[dict[str, bool]] = None,
    version_id: str = "v1",
    parent_version_id: Optional[str] = None,
    calibration_multiplier: float = 1.0,
    historical_cases: Optional[list[float]] = None,
    systemic_ratio_pool: Optional[Sequence[float]] = None,
    readings: Optional[dict[str, ClauseReading]] = None,
    manual_edits: Optional[dict] = None,
) -> EstimateVersion:
    """Analyse the brief (and extra documents) into a validated EstimateVersion."""
    sources = {k: v for k, v in (source_docs or {}).items() if v and v.strip()}
    sources["brief.txt"] = brief_text
    answers = clarification_answers or {}
    lang = _lang(brief_text)
    L = _TEXT[lang]

    clauses: list[Clause] = segment("brief.txt", brief_text)
    for name, text in sources.items():
        if name != "brief.txt" and text.strip() != brief_text.strip():
            clauses.extend(segment(name, text))

    drafts: list[_Draft] = []
    shared_items: dict[str, list[WorkItem]] = {}
    clarifications: list[ClarificationQuestion] = []
    critics: list[CriticFinding] = []
    all_systems: list[str] = []
    perf_clause: Optional[Clause] = None
    has_nfr = False
    seq = 0

    for clause in clauses:
        folded = fold(clause.text)
        matched = _match_components(clause.text)
        reading = readings.get(clause.text.strip()) if readings else None
        ai_component = None  # AI kind used directly (rules found nothing)
        ai_suggest = None  # AI kind the rules missed, offered as a question instead of silently added
        if reading and reading.component and reading.kind_confidence >= KIND_CONFIDENCE_MIN:
            candidate = COMPONENT_BY_KEY[reading.component]
            if not matched:
                ai_component = candidate
                matched = [candidate]
            elif candidate not in matched:
                ai_suggest = candidate
        if clause.is_title:
            continue
        if not matched and not clause.is_item and not _REQUIREMENT_MARKERS.search(folded):
            continue  # descriptive context, not a requirement
        seq += 1
        req_id = f"REQ-{seq:02d}"
        title = _short_title(clause)
        hedge_match = _HEDGES.search(folded)
        hedge = None
        if hedge_match:
            # map folded offsets back to the original text (fold keeps length for Vietnamese)
            hedge = clause.text[hedge_match.start(): hedge_match.end()] if len(fold(clause.text)) == len(clause.text) else hedge_match.group(0)
        ai_tentative = None
        if hedge is None and reading and reading.tentative >= TENTATIVE_MIN:
            ai_tentative = reading.tentative
            hedge = L["ai_hedge"].format(p=round(reading.tentative * 100))
        components = matched or [GENERIC]
        if any(c.key in ("performance", "security") for c in components):
            has_nfr = True
        evidence = [EvidenceSpan(source_doc=clause.doc, quote=clause.text, location=f"clause {clause.index + 1}")]
        scope_q = f"CLAR-{req_id}"
        excluded = hedge is not None and answers.get(scope_q) is False
        req = RequirementNode(
            req_id=req_id,
            title=title,
            description=f"{L['detected']}: {', '.join(VI_COMPONENTS.get(c.key, c.label) if lang == 'vi' else c.label for c in components)}."
            + (f" {L['excluded']}" if excluded else ""),
            status=VerificationStatus.ASSUMED if hedge and answers.get(scope_q) is None else VerificationStatus.CONFIRMED,
            evidence=evidence,
            components=[c.key for c in components],
            ai_reading=(
                {
                    "kind": reading.kind,
                    "confidence": reading.kind_confidence,
                    "tentative": reading.tentative,
                    "model": reading.model,
                    "added_component": ai_component.key if ai_component else None,
                    "suggested_component": ai_suggest.key if ai_suggest else None,
                    "flagged_tentative": ai_tentative is not None,
                }
                if reading else None
            ),
            in_scope=not excluded,
        )
        draft = _Draft(req=req, hedge=hedge, clause=clause)
        drafts.append(draft)

        breadth = _breadth(clause)
        factor = min(MAX_BREADTH_FACTOR, 1 + 0.25 * (breadth - 1))
        systems = _systems(folded) if any(c.key == "integration" for c in components) else []
        # Excluded requirements are still sized (to report what was removed) but
        # never register shared items, so other requirements keep theirs.
        draft.items = _build_items(req_id, title, components, systems, folded, factor, breadth,
                                   shared_items, register=not excluded)
        if systems and _UNDOCUMENTED.search(folded):
            # The brief itself says documentation is missing: include discovery, no question needed.
            draft.items.append(WorkItem(
                item_id=f"{req_id}-DISCOVERY", req_ids=[req_id], role="Backend",
                name=f"API discovery spike: {', '.join(systems)}",
                optimistic_hours=8, most_likely_hours=16, pessimistic_hours=40,
                basis="Brief states API documentation is missing",
            ))
        if excluded:
            clarifications.append(_scope_question(L, scope_q, req_id, title, hedge, draft.items, evidence, answers,
                                                 ai=ai_tentative is not None))
            draft.items = []
            continue
        all_systems.extend(s for s in systems if s not in all_systems)

        if factor > 1 and any(c.scales_with_breadth for c in components):
            critics.append(CriticFinding(
                finding_id=f"CRITIC-{req_id}-BREADTH", category="scope_breadth",
                claim=L["c_breadth"].format(title=title, n=breadth, factor=factor),
                verified_by_evidence=True, supporting_evidence=evidence, action_taken="applied_to_wbs",
            ))
        if any(c.key == "performance" for c in components) and perf_clause is None:
            perf_clause = clause
        if components == [GENERIC]:
            critics.append(CriticFinding(
                finding_id=f"CRITIC-{req_id}-GENERIC", category="estimation_risk",
                claim=L["c_generic"].format(title=title), verified_by_evidence=True,
                supporting_evidence=evidence, action_taken="flagged_for_human_review",
            ))

        if ai_suggest is not None:
            qid = f"CLAR-{req_id}-AI"
            accepted = answers.get(qid) is True
            suggested_items = _build_items(req_id, title, [ai_suggest], systems, folded, factor, breadth,
                                           shared_items, register=accepted)
            if suggested_items:
                kind_label = VI_COMPONENTS.get(ai_suggest.key, ai_suggest.label) if lang == "vi" else ai_suggest.label
                clarifications.append(ClarificationQuestion(
                    question_id=qid, assumption_id=f"ASSUMP-{req_id}-AI", evidence=evidence,
                    question_text=L["q_ai_kind"].format(title=title, kind=kind_label),
                    context_reason=L["q_ai_kind_why"].format(kind=kind_label, p=round(reading.kind_confidence * 100)),
                    hours_if_false=0.0, hours_if_true=round(sum(_pert_mean(i) for i in suggested_items), 1),
                    affected_item_ids=[i.item_id for i in suggested_items],
                    current_assumption=False, answer=answers.get(qid),
                ))
                if accepted:
                    draft.items.extend(suggested_items)

        # --- clarification questions grounded in this clause ---------------
        if hedge:
            clarifications.append(_scope_question(L, scope_q, req_id, title, hedge, draft.items, evidence, answers,
                                                 ai=ai_tentative is not None))
            critics.append(CriticFinding(
                finding_id=f"CRITIC-{req_id}-HEDGE", category="scope_ambiguity",
                claim=L["c_hedge_ai" if ai_tentative is not None else "c_hedge"].format(hedge=hedge, title=title),
                verified_by_evidence=True,
                supporting_evidence=evidence, action_taken="generated_clarification_question",
            ))

        extra_questions = []
        if any(c.key == "mobile" for c in components) and not _PLATFORM.search(folded):
            extra_questions.append(("PLATFORM", L["q_platform"], L["q_platform_why"],
                                    T("NATIVE2", "Frontend", "Second native platform build & store release", 20, 40, 80)))
        if any(c.key in ("import", "migration") for c in components):
            extra_questions.append(("DATAQ", L["q_dataq"], L["q_dataq_why"],
                                    T("CLEAN", "Backend", "Data cleansing, normalisation & de-duplication rules", 8, 16, 36)))
        if systems and not _HAS_DOCS.search(folded) and not _UNDOCUMENTED.search(folded):
            name = ", ".join(systems)
            extra_questions.append(("API", L["q_api"].format(system=name), L["q_api_why"].format(system=name),
                                    T("DISCOVERY", "Backend", f"API discovery spike: {name}", 8, 16, 40)))
        for code, question, why, tpl in extra_questions:
            qid = f"CLAR-{req_id}-{code}"
            item = WorkItem(
                item_id=f"{req_id}-{tpl.code}", req_ids=[req_id], role=tpl.role, name=tpl.name,
                optimistic_hours=tpl.o, most_likely_hours=tpl.m, pessimistic_hours=tpl.p,
                assumption_id=f"ASSUMP-{req_id}-{code}", basis="Added only if clarification answer is Yes",
            )
            clarifications.append(ClarificationQuestion(
                question_id=qid, assumption_id=f"ASSUMP-{req_id}-{code}", question_text=question,
                context_reason=why, hours_if_false=0.0, hours_if_true=round(_pert_mean(item), 1),
                affected_item_ids=[item.item_id], evidence=evidence,
                current_assumption=False, answer=answers.get(qid),
            ))
            if answers.get(qid) is True:
                draft.items.append(item)

    # ------------------------------------------------------------------ #
    # Foundation, QA and delivery work (ASSUMED: standard practice)
    # ------------------------------------------------------------------ #
    feature_items = [i for d in drafts for i in d.items]
    n_features = sum(1 for d in drafts if d.req.in_scope)
    foundation = RequirementNode(
        req_id="REQ-00", title=L["foundation"], description=L["foundation_desc"],
        status=VerificationStatus.ASSUMED, evidence=[], components=["foundation"],
    )
    setup = WorkItem(item_id="SETUP-ENV", req_ids=["REQ-00"], role="DevOps",
                     name="Repository, environments & CI/CD pipeline",
                     optimistic_hours=8, most_likely_hours=14, pessimistic_hours=26, basis="Engine prior")
    arch_m = 8 + 2 * n_features
    core = WorkItem(item_id="CORE-ARCH", req_ids=["REQ-00"], role="Backend", dependencies=["SETUP-ENV"],
                    name="Core architecture, shared data model & API conventions",
                    optimistic_hours=round(arch_m * 0.6, 1), most_likely_hours=arch_m,
                    pessimistic_hours=round(arch_m * 2, 1), basis=f"8h + 2h x {n_features} feature requirement(s)")

    # Dependencies: backend items -> core; frontend items -> first backend item of the same requirement.
    for d in drafts:
        first_be = next((i.item_id for i in d.items if i.role == "Backend"), None)
        for item in d.items:
            if item.dependencies:
                continue
            if item.role == "Frontend" and first_be and item.item_id != first_be:
                item.dependencies = [first_be]
            else:
                item.dependencies = ["CORE-ARCH"]

    # Deduplicate (shared items are referenced from several drafts).
    seen: dict[str, WorkItem] = {}
    for item in feature_items + [i for d in drafts for i in d.items]:
        seen.setdefault(item.item_id, item)
    feature_items = list(seen.values())
    edits = manual_edits or {}
    if edits:
        feature_items = _apply_manual_edits(feature_items, edits, {"REQ-00", *(d.req.req_id for d in drafts)})

    dev_mean = sum(_pert_mean(i) for i in feature_items) + _pert_mean(core)
    depended = {dep for i in feature_items for dep in i.dependencies}
    leaves = [i.item_id for i in feature_items if i.item_id not in depended] or ["CORE-ARCH"]
    qa_m = round(max(8.0, 0.12 * dev_mean), 1)
    e2e_m = round(max(6.0, 0.06 * dev_mean), 1)
    qa = WorkItem(item_id="QA-INTEG", req_ids=["REQ-00"], role="QA", dependencies=leaves,
                  name="Integration & regression test suite",
                  optimistic_hours=round(qa_m * 0.6, 1), most_likely_hours=qa_m, pessimistic_hours=round(qa_m * 1.9, 1),
                  basis=f"12% of development PERT mean ({dev_mean:.0f}h)")
    e2e = WorkItem(item_id="QA-E2E", req_ids=["REQ-00"], role="QA", dependencies=["QA-INTEG"],
                   name="End-to-end flows & UAT support",
                   optimistic_hours=round(e2e_m * 0.6, 1), most_likely_hours=e2e_m, pessimistic_hours=round(e2e_m * 1.9, 1),
                   basis=f"6% of development PERT mean ({dev_mean:.0f}h)")
    deploy = WorkItem(item_id="DEPLOY", req_ids=["REQ-00"], role="DevOps", dependencies=["QA-E2E"],
                      name="Production deployment, monitoring & handover",
                      optimistic_hours=6, most_likely_hours=12, pessimistic_hours=24, basis="Engine prior")
    wbs = [setup, core, *feature_items, qa, e2e, deploy]
    if edits:
        _apply_overrides([setup, core, qa, e2e, deploy], edits.get("overrides") or {})
    if lang == "vi":
        for item in wbs:
            item.name = _vi_name(item.name)

    # ------------------------------------------------------------------ #
    # Critic findings derived from the analysis
    # ------------------------------------------------------------------ #
    if perf_clause is not None:
        critics.append(CriticFinding(
            finding_id="CRITIC-PERF", category="nfr_risk", claim=L["c_perf"], verified_by_evidence=True,
            supporting_evidence=[EvidenceSpan(source_doc=perf_clause.doc, quote=perf_clause.text)],
            action_taken="applied_to_wbs",
        ))
    if all_systems:
        critics.append(CriticFinding(
            finding_id="CRITIC-INTEGRATIONS", category="integration_risk",
            claim=L["c_integrations"].format(n=len(all_systems), names=", ".join(all_systems)),
            verified_by_evidence=False, action_taken="flagged_for_human_review",
        ))
    total_mean = sum(_pert_mean(i) for i in wbs)
    qa_share = sum(_pert_mean(i) for i in wbs if i.role == "QA") / total_mean * 100
    critics.append(CriticFinding(
        finding_id="CRITIC-QA-SHARE", category="quality_gate", claim=L["c_qa"].format(share=qa_share),
        verified_by_evidence=False,
        action_taken="safeguard_verified" if qa_share >= 15 else "flagged_for_human_review",
    ))
    if not has_nfr:
        critics.append(CriticFinding(
            finding_id="CRITIC-NFR-MISSING", category="missing_requirement", claim=L["c_nfr"],
            verified_by_evidence=False, action_taken="flagged_for_human_review",
        ))

    clarifications.sort(key=lambda q: (q.answer is not None, -q.sensitivity_spread_hours))

    forecast = synthesize_forecast(
        wbs=wbs,
        comparable_actual_hours=historical_cases,
        calibration_multiplier=calibration_multiplier,
        seed=42,
        systemic_ratio_pool=systemic_ratio_pool,
    )

    version = EstimateVersion(
        version_id=version_id,
        project_id=project_id,
        parent_version_id=parent_version_id,
        model_tag=MODEL_TAG,
        requirements=[foundation, *[d.req for d in drafts]],
        wbs=wbs,
        critic_findings=critics,
        clarifications=clarifications,
        forecast=forecast,
        clarification_answers=dict(answers),
        reader="rules+jev" if readings else "rules",
        manual_edits=dict(edits),
        reader_model=next(iter(readings.values())).model if readings else None,
    )
    validate_evidence_against_sources(version, sources)
    return version
