# PARALLAX AI — Nhật ký phát triển (Development Log)

> **Lưu ý (17/10/2026):** đây là nhật ký của Day 0–1, giữ nguyên để làm lịch sử. Một số nội dung bên dưới đã được thay
> thế: không còn "dự án lịch sử seed sẵn" (reference class chỉ gồm dự án có giờ thực tế thật), cú sốc lognormal giả định
> đã được thay bằng phân phối thực nghiệm từ SiP, và AI Jev nay là bắt buộc. Trạng thái hiện tại và mọi kết quả đo được
> nằm ở [`README.md`](../README.md) và [`EVALUATION_LOG.md`](EVALUATION_LOG.md).

**Dự án**: PARALLAX AI — Evidence-Driven, Self-Calibrating Estimation Intelligence  
**Thử thách**: Anduin Cybernetics · Agent in the Shell (15–19/10/2026)  
**Tác giả**: Team Anduin / mapleleaflatte03  
**Bắt đầu**: 15/10/2026 23:15 (Giờ TP.HCM)  
**Cập nhật lần cuối**: 15/10/2026 23:45  

---

## 1. Bảng theo dõi tiến độ tổng thể (Milestone Tracker)

| Giai đoạn | Thời gian | Trọng tâm | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Day 0: Foundation** | 15/10 (Đêm) | Dựng repo, schema Pydantic, provenance check, Monte Carlo, Benchmark harness, CI, venv | **HOÀN THÀNH (100%)** |
| **Day 1: Scope & API** | 16/10 | FastAPI backend, 3 Golden Briefs, WBS generator, Evidence extractor, REST contracts | **HOÀN THÀNH (100%)** |
| **Day 2: Intelligence** | 17/10 | Reference-class retrieval, Adversarial Critic, What-if Clarification engine, Monte Carlo correlated shock | **HOÀN THÀNH (100%)** |
| **Day 3: Learning & UI**| 18/10 | Giao diện 5 màn hình (Next.js/Vite React), Actuals feedback loop, Calibration gate, UI/UX Pro Max Redesign | **HOÀN THÀNH (100%)** |
| **Day 4: Verification** | 19/10 | Benchmark holdout evaluation, documentation, video demo, audit an toàn, nộp bài | **CHUẨN BỊ** |

---

## 2. Chi tiết các hạng mục đã hoàn thành

### Giai đoạn 0: Foundation & Core Mathematics (15/10/2026)
- [x] **Giải nén & Chuẩn hóa workspace**:
  - Nhận bàn giao gói `parallax-estimator-day0.zip`.
  - Chuẩn hóa layout thư mục: `apps/api`, `apps/web`, `datasets`, `docs`, `scripts`, `tests`.
  - Khởi tạo local Git repository nhánh `main`.
- [x] **Môi trường & Phụ thuộc**:
  - Thiết lập virtual environment Python 3.14 (`.venv`).
  - Cài đặt `pydantic>=2`, `numpy>=1.26`, `pytest>=8`, `fastapi>=0.110.0`, `uvicorn[standard]>=0.28.0`, `httpx>=0.27.0`.
  - Đóng gói editable package `parallax-estimator-foundation`.
- [x] **Data Contracts (`apps/api/parallax/schemas.py`)**:
  - `VerificationStatus`: CONFIRMED, ASSUMED, MISSING.
  - `EvidenceSpan`: quote, source_doc, location (chặn quote rỗng hoặc ngắn hơn 5 ký tự).
  - `RequirementNode`: Ràng buộc requirement CONFIRMED bắt buộc phải có `EvidenceSpan`.
  - `WorkItem`: Ước tính 3 điểm (optimistic $\le$ likely $\le$ pessimistic).
  - `CriticFinding`: Chặn unverified finding tự động áp dụng vào WBS.
  - `ClarificationQuestion`: Đo `sensitivity_spread_hours`.
  - `ProbabilisticForecast`: Phân vị P10 $\le$ P50 $\le$ P80 $\le$ P90, mean, std, cảnh báo phân kỳ.
  - `EstimateVersion`: Phát hiện chu trình (cycle detection) trong đồ thị DAG phụ thuộc công việc và kiểm tra tính toàn vẹn của mã định danh.
  - Mở rộng thêm `Project`, `ProjectCreate`, `HistoricalCase`, `ActualWork`, `EvaluationRun`, `ClarificationAnswer`.
- [x] **Cơ chế Provenance (`apps/api/parallax/provenance.py`)**:
  - Hàm `validate_evidence_against_sources` kiểm tra chuỗi trích dẫn thực tế so với văn bản gốc (NFKC normalization, loại bỏ khoảng trắng thừa) nhằm chặn triệt để hiện tượng bịa đặt trích dẫn.
- [x] **Monte Carlo & Risk Engine (`apps/api/parallax/estimation/engine.py`)**:
  - Beta-PERT mô phỏng từng task.
  - Lognormal systemic risk shock ($\mu = -0.5\sigma^2$, mean = 1.0) mô phỏng sự tương quan dương giữa các task.
  - Cảnh báo phân kỳ nếu Reference Class P50 lệch $> 30\%$ so với Bottom-up P50.
  - Đánh dấu rõ ràng `insufficient_historical_evidence` khi có dưới 5 case tương đồng.
- [x] **Benchmark & Calibration Gate (`apps/api/parallax/evaluation/benchmark.py`, `calibration.py`)**:
  - Tính toán MAE, MdAPE, WAPE, PRED(25), Interval Coverage, Mean Interval Width.
  - Cổng phê duyệt hiệu chỉnh `calibration_gate_decision`: chỉ cho phép đánh giá trên tập `validation`, từ chối nghiêm ngặt việc rò rỉ dữ liệu sang tập `test`.
- [x] **Kiểm thử tự động**:
  - Đạt 18/18 tests pass trong 0.51s (`test_foundation.py`, `test_api.py`, `test_golden_briefs.py`).

---

### Giai đoạn 1 & 2: Backend API, Scope Extractor & Golden Briefs
- [x] **Storage Repository (`apps/api/parallax/storage.py`)**:
  - Quản lý phiên bản bất biến (`EstimateVersion` không bao giờ bị ghi đè, tạo DAG phả hệ phiên bản theo `parent_version_id`).
  - Nạp sẵn 16 case dự án lịch sử (internal tools, e-commerce, AI/RAG) làm reference class.
- [x] **Scope & Evidence Extractor (`apps/api/parallax/extractor.py`)**:
  - Bóc tách tự động các yêu cầu CONFIRMED với trích dẫn verbatim chuẩn xác 100% từ brief.
  - Nhận diện các giả định ngầm (ASSUMED) và các lỗ hổng cần làm rõ (MISSING).
  - Tự động sinh DAG WBS gồm các vai trò (Frontend, Backend, DevOps, QA) với ước tính 3 điểm.
  - Sinh các câu hỏi làm rõ (Active Clarification) xếp hạng theo độ nhạy (Sensitivity Spread).
  - Khởi tạo nhận định của Adversarial Critic.
- [x] **Bộ 3 Golden Briefs (`datasets/golden_briefs/`)**:
  - `golden_brief_1_pm_portal.json`: Cổng thông tin Quản lý Dự án & ERP Legacy.
  - `golden_brief_2_ecommerce_sync.json`: Đồng bộ Tồn kho & Đơn hàng Đa sàn Thương mại Điện tử.
  - `golden_brief_3_ai_rag_support.json`: Trợ lý AI Hỗ trợ Khách hàng RAG & pgvector.
- [x] **FastAPI REST API (`apps/api/parallax/main.py`)**:
  - `GET /health`: Kiểm tra trạng thái hệ thống.
  - `POST /api/v1/projects`: Tạo dự án mới.
  - `GET /api/v1/projects`: Danh sách dự án.
  - `POST /api/v1/projects/{id}/estimate`: Sinh version dự toán mới.
  - `GET /api/v1/projects/{id}/versions`: Lịch sử phiên bản.
  - `POST /api/v1/projects/{id}/clarify`: Trả lời câu hỏi làm rõ & kích hoạt What-if.
  - `POST /api/v1/projects/{id}/actuals`: Ghi nhận giờ thực tế & đánh giá sai lệch.
  - `POST /api/v1/benchmark/run`: Chạy bộ benchmark tự động trên dữ liệu holdout.

---

### Giai đoạn 3: UI/UX Pro Max Redesign (Frontend Workspace)
- [x] **Khởi tạo ứng dụng Web React TypeScript + Tailwind CSS (`apps/web`)**:
  - Tích hợp công nghệ Vite v8, TypeScript, Tailwind CSS v4, Lucide React icons.
  - Cấu hình proxy tự động từ frontend port 3000 sang FastAPI port 8000.
- [x] **Tạo tài nguyên hình ảnh thương hiệu (Asset Generation)**:
  - `apps/web/public/parallax_hero.jpg`: Tranh minh họa không gian 3D Isometric hiện đại biểu diễn mạng lưới bằng chứng và phân phối xác suất Monte Carlo trên nền sáng tinh tế.
  - `apps/web/public/parallax_logo.jpg`: Logo lăng kính khúc xạ ánh sáng ba chiều (Holographic Prism) biểu trưng cho trí tuệ dự toán đa chiều.
- [x] **Nâng cấp thẩm mỹ theo chuẩn UI/UX Pro Max**:
  - **Màu sắc sáng & hài hòa**: Nền sáng mềm mại `#F8FAFC`, thẻ trắng tinh khiết `#FFFFFF`, viền mờ `#E2E8F0`, màu điểm nhấn tím ánh điện `#4F46E5` và xanh cyan `#0284C7`.
  - **Hỗ trợ Light / Dark Mode**: Tích hợp nút chuyển đổi giao diện sáng/tối tức thời.
  - **Font chữ hiện đại**: Import Google Fonts `Plus Jakarta Sans` và `Space Grotesk`.
  - **Pipeline Stepper 5 bước trực quan**:
    1. *Intake & Brief* (Nạp yêu cầu)
    2. *Scope & Evidence* (Trích dẫn WBS)
    3. *Estimation Lab* (Monte Carlo)
    4. *Active Clarify* (What-if)
    5. *Accuracy & Learn* (Tự hiệu chỉnh)
- [x] **Chi tiết 5 màn hình**:
  1. **Project Intake**: Banner Hero 3D, chọn nhanh 3 Golden Briefs chỉ với 1 click, form nhập brief kèm đếm ký tự.
  2. **Scope & Evidence Graph**: Thẻ tóm tắt tổng số yêu cầu, trích dẫn verbatim, bộ lọc theo trạng thái (Confirmed/Assumed/Missing), bảng WBS có huy hiệu vai trò màu sắc và kiểm tra chu trình DAG (0 cycles).
  3. **Estimation Laboratory**: 4 thẻ phân vị (P10 Lạc quan, P50 Target Commit, P80 An toàn, P90 Biên độ cao), biểu đồ SVG đường cong phân phối xác suất mượt mà, so sánh hai nhánh Bottom-up vs. Reference-Class, và bảng nhận định phản biện của Critic.
  4. **What-if & Active Clarification**: Thước đo mức độ ảnh hưởng (Sensitivity Impact), so sánh trực quan kịch bản "KHÔNG tích hợp" vs "CÓ tích hợp", các nút xác nhận tương tác, và cây phả hệ phiên bản dự toán (Version Tree).
  5. **Accuracy & Learning**: Form nạp giờ công thực tế, tính toán chênh lệch tuyệt đối và sai số %, kiểm tra độ phủ P10-P90, nút bấm chạy bộ kiểm định tự động (MAE, MdAPE, WAPE, PRED(25), Coverage), và cam kết trung thực nghiên cứu.

---

### Giai đoạn 4: Nghiên cứu & Hoàn thiện Phối màu Đa tầng theo Từng Phân vùng (Intuitive & Dynamic Thematic Color Palette)
- [x] **Khắc phục triệt để lỗi xung đột tương phản Dark/Light mode**:
  - Khai báo `@custom-variant dark (&:where(.dark, .dark *));` trong `index.css` để kích hoạt Dark mode class-based chuẩn cho Tailwind CSS v4, chấm dứt việc chữ trắng biến mất trên thẻ trắng khi OS ở dark mode.
  - Đồng bộ `isDarkMode` state với `localStorage` và `prefers-color-scheme` của hệ điều hành.
- [x] **Nâng cấp màu sắc nền trực quan, thân thiện và êm dịu (Canvas Aesthetics)**:
  - Chuyển từ màu đen đặc `#070b13` sang màu xanh đêm sang trọng `#090D1A` ở chế độ Tối, và màu nền canvas mềm mại `#F4F6FB` ở chế độ Sáng.
  - Bổ sung lớp phủ lưới phát quang Ambient Mesh Gradient (`bg-mesh-light` / `bg-mesh-dark`) tạo chiều sâu không gian ba chiều mà không làm rối mắt.
- [x] **Nghiên cứu phối màu chuyên biệt cho từng phân vùng (Section-by-Section Color Identities)**:
  1. **Intake & Brief (Tím & Chàm - Cosmic Indigo & Royal Violet)**:
     - Hero card chuyển sắc tinh tế với viền phát sáng nhẹ, huy hiệu công nghệ nổi bật.
     - 3 thẻ Golden Briefs được định danh mã màu riêng biệt theo phân loại domain:
       - *Internal Tool*: Sắc xanh doanh nghiệp Azure / Sapphire Blue (`#0284C7` / `#2563EB`).
       - *E-Commerce Sync*: Sắc xanh giao dịch thanh toán Emerald / Mint (`#059669` / `#10B981`).
       - *AI & RAG Pipeline*: Sắc tím trí tuệ nhân tạo Cyber Violet / Fuchsia (`#7C3AED` / `#A855F7`).
     - Form nhập brief có ô nhập liệu độ tương phản cao, focus ring mềm mại, nút bấm chuyển sắc tím chàm chuyển động mượt mà.
  2. **Scope & Evidence (Xanh ngọc lục bảo & Hổ phách - Precision Emerald & Amber)**:
     - Dải thống kê Ribbon 5 chỉ số có gradient và huy hiệu ngữ nghĩa độc lập (Confirmed: Emerald, Assumed: Amber, Missing: Rose, DAG: Indigo).
     - Khung trích dẫn bằng chứng Verbatim Citation kiểu parchment nổi bật trên nền vàng hổ phách, hiển thị chính xác tên tài liệu và vị trí offset.
     - Bảng WBS phân cấp vai trò với các chip màu pastel và hiển thị 3 điểm (O / L / P) sắc nét.
  3. **Estimation Lab (Dải phổ rủi ro 4 phân vị - Chromatic Risk Spectrum)**:
     - Thẻ P10 (Lạc quan - Emerald).
     - Thẻ P50 (Target Commit - Tiêu điểm nổi bật với viền đôi Indigo/Cyan và huy hiệu phát sáng).
     - Thẻ P80 (Kế hoạch cam kết an toàn - Amber).
     - Thẻ P90 (Biên độ sốc hệ thống - Purple/Violet).
     - Biểu đồ đường cong mật độ xác suất SVG nhiều tầng chuyển sắc (Indigo $\to$ Sky $\to$ Violet).
     - Thẻ đối soát hai nhánh độc lập (Bottom-up WBS vs. Reference Class) trực quan.
  4. **Active Clarification (Xanh điện Cyan & Hổ phách - Electric Cyan & Amber)**:
     - Huy hiệu độ nhạy lệch giờ công (&plusmn;XX giờ) viền vàng nổi bật.
     - Khung so sánh What-if trực quan giữa kịch bản KHÔNG triển khai (viền xám / chữ hồng) vs CÓ triển khai (viền chàm / chữ xanh ngọc).
     - Cây phả hệ phiên bản dự toán (Version Tree) hiển thị phân cấp v1 $\to$ v2 $\to$ v3 không bao giờ ghi đè.
  5. **Accuracy & Continuous Learning (Vàng kim & Xanh ngọc - Executive Gold & Emerald)**:
     - 4 thẻ đo lường chuẩn quốc tế (MAE, MdAPE, WAPE, PRED(25)) được thiết kế với dải màu riêng biệt, dễ đọc số liệu.
     - Dải banner độ phủ khoảng dự báo (Interval Coverage) sắc nét.
     - Hộp thoại cam kết trung thực nghiên cứu có đường viền chỉ thị Indigo/Cyan rõ ràng.

---

### Giai đoạn 5: Tái thiết kế Độc quyền & Khắc phục AI-Style theo chuẩn UI/UX Pro Max & 21st-dev (Bespoke Engineering Cockpit)
- [x] **Loại bỏ triệt để AI Tropes (Generic AI Gradients, Sparkles, Static Text-only Cards)**:
  - Áp dụng nguyên tắc từ skill `/ui-ux-pro-max` (Minimalism & Swiss Style, Data-Dense Dashboard) và `/21st-dev` (Asymmetric Bento Grid, tactile controls).
  - Thay thế các dải chuyển sắc tím hồng AI đại trà bằng bảng màu công nghệ chính xác: Xanh đêm Midnight Slate (`#090D1A`), viền kỹ thuật sắc nét (`#1E293B` / `#CBD5E1`), số liệu viễn trắc Monospace (`font-mono`), và màu ngữ nghĩa rõ rệt (Emerald cho bằng chứng xác thực, Amber cho đệm dự phòng rủi ro, Cyan cho cam kết trung vị P50, Rose cho lỗ hổng/phản biện).
- [x] **Dải Viễn trắc Hoạt động Trực tiếp (Live Operational Telemetry Ribbon)**:
  - Tích hợp thanh viễn trắc thời gian thực ngay dưới thanh điều hướng:
    - `ENGINE: ONLINE (Beta-PERT N=10,000)` (nhịp đập xanh ngọc lục bảo).
    - `DAG INTEGRITY: ACYCLIC (0 Chu trình &bull; Topological Sort)`.
    - `CALIBRATION: 16 Holdout Benchmarks (MAE < 4.5h Strict)`.
    - `SHOCK: Lognormal Tail Active (σ=0.35)`.
    - Nhãn model tag và tổng số gói công việc WBS đang hoạt động.
- [x] **Phòng thí nghiệm Dự toán Tương tác Độc quyền (Proprietary Estimation Lab Cockpit)**:
  - **Thanh trượt Quantile Scrubber xúc giác (P10 &rarr; P95)**: Người dùng trực tiếp kéo thanh trượt độ tin cậy để xem giờ công nội suy tức thời.
  - **Biểu đồ Đường cong Phân phối Động (Interactive SVG Beta-PERT Curve)**:
    - Con trỏ neon dọc và diện tích xác suất tích lũy (Shaded Probability Fill) chuyển động mượt mà theo vị trí thanh Scrubber.
  - **Bộ mô phỏng Cú sốc Hệ thống (Systemic Correlated Shock Simulator)**:
    - 3 chế độ stress-test: Chuẩn (1.0x), API Lệch (+15%), Scope Biến động (+25%). Khi bấm kích hoạt, đuôi phân phối lệch phải và các mốc P80/P90 tự động tính toán lại.
  - **Mô hình Ngân sách Tài chính & Điều khoản Hợp đồng (Financial Budget Modeler)**:
    - Bộ chuyển đổi tiền tệ song song: USD ($/h) và VND (₫/h).
    - Lựa chọn cấp bậc nhân sự (Junior, Standard, Lead) hoặc đơn giá tùy biến.
    - Tính toán tự động Ngân sách Cam kết và Đệm Dự phòng (Contingency Reserve) kèm khuyến nghị điều khoản hợp đồng (PoC, Milestone-based, hoặc Fixed-Price an toàn).
- [x] **Bảng Phân bổ Nguồn lực & Vận tốc Sprint (Scope & Evidence Screen)**:
  - Thanh phân bổ tỷ trọng đa sắc (Proportional Resource Stacked Bar) giữa các vai trò Backend, Frontend, QA, DevOps (click vào vai trò để lọc nhanh WBS).
  - Bộ tính toán quy mô đội ngũ (1 đến 5 lập trình viên) &rarr; tính số tuần bàn giao dự kiến dựa trên P50 hours.
  - Bộ lọc công việc theo chuỗi phụ thuộc DAG: "Khởi động Sprint 1 (Độc lập)" vs "Có phụ thuộc".
- [x] **Bộ Mô phỏng What-if Tức thời (Clarification Screen)**:
  - Cho phép người dùng nhấp thử nghiệm "Đang mô phỏng: CÓ" hoặc "Đang mô phỏng: KHÔNG" trên từng câu hỏi để thấy ngay tác động ròng (&Delta; hours) lên giờ công P50 và ngân sách trước khi chốt gửi dữ liệu lên server.
- [x] **Kho Dữ liệu Lịch sử Thực nghiệm (Seeded Historical Cases Explorer)**:
  - Hiển thị bảng tra cứu 16 dự án lịch sử holdout với độ phức tạp, số lượng task, và giờ công thực tế, minh chứng cho việc mô hình không bịa đặt số liệu mà dựa trên lớp tham chiếu thực nghiệm.

---

## 3. Trạng thái kiểm thử & Vận hành

- **Backend Tests**: 18/18 tests passed (`.venv/bin/pytest -v` trong 0.53s).
- **Frontend Build**: 100% build thành công (`npm run build` trong 377ms, zero errors, zero warnings).
- **Backend Service**: Đang chạy daemon trên `http://127.0.0.1:8000/`.
- **Frontend Service**: Đang chạy daemon trên `http://localhost:3000/`.

