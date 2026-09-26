# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `EasyGame`
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-DAY10-EasyGame-Data-Pipeline-Data-Observability`

---

## 👥 Danh Sách Thành Viên (Nhóm 3 Người)

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Phạm Thành Đạt | 2A202602721 | phamthanhdat17092004@gmail.com | **Member 1 (Trưởng nhóm / Pipeline Integrator & Vector Store):** Quản lý cấu hình (`core/config.py`, `core/utils.py`), ChromaDB vector collections (`retrieval/index.py`, `retrieval/embeddings.py`), điều phối luồng end-to-end (`pipelines/phase1.py`, `pipelines/corruption_flow.py`, `script/`), theo dõi Git commit nhánh `main`. | `report/2A202602721_PhamThanhDat.md` |
| 2 | Nguyễn Tiến Đạt | 2A202602970 | dn841746@gmail.com | **Member 2 (Data Engineering & Corruption):** Thu thập dữ liệu API & offline fallback (`ingestion/crossref.py`), làm sạch & chuẩn hóa embedding (`ingestion/cleaning.py`), giả lập 6 kịch bản lỗi dữ liệu (`ingestion/corruption.py`), phục hồi dữ liệu từ raw snapshot. | `report/2A202602970_NguyenTienDat.md` |
| 3 | Ngô Hoàng Thụy Khuê | 2A202603017 | khuengo.work@gmail.com | **Member 3 (Observability, Evaluation & Reporting):** Thiết lập Quality Gate Great Expectations 1.x & Freshness SLA (`observability/quality.py`), tạo bộ benchmark test set 10 câu hỏi (`evaluation/testset.py`), xuất báo cáo markdown đối chiếu 3 trạng thái (`observability/reporting.py`). | `report/2A202603017_NgoHoangThuyKhue.md` |

---

## 📝 Báo Cáo Cá Nhân & Phân Chia Trách Nhiệm

### 👤 Thành Viên 1 (Trưởng nhóm / Pipeline Integrator & Vector Store)
- **Họ và tên:** `Phạm Thành Đạt` | **MSSV:** `2A202602721`
- **Vai trò:** Trưởng nhóm, Điều phối Pipeline & Quản lý Vector Store.
- **Phạm vi file phụ trách:**
  - `src/core/config.py`, `src/core/utils.py`
  - `src/retrieval/index.py`, `src/retrieval/embeddings.py`, `src/retrieval/agent.py`
  - `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`
  - `script/run_phase1.py`, `script/run_corruption_flow.py`
- **Nhiệm vụ & Sản phẩm bàn giao:**
  - Thiết lập môi trường `.venv`, cấu hình `.env`, đường dẫn artifacts.
  - Quản lý 3 collection ChromaDB: `papers-baseline`, `papers-corrupted`, `papers-repaired`.
  - Kết nối luồng chạy hoàn chỉnh Phase 1 và Corruption/Repair Flow.
  - Điều phối Live Demo và bảo đảm 100% thành viên có commit trên nhánh `main`.
- **Đóng góp chính / Kiến thức thu nhận:**
  - Thiết kế kiến trúc Idempotent Data Pipeline, quản lý vòng đời của Vector Store tách biệt qua từng trạng thái dữ liệu.

### 👤 Thành Viên 2 (Data Engineering & Corruption)
- **Họ và tên:** `Nguyễn Tiến Đạt` | **MSSV:** `2A202602970`
- **Vai trò:** Kỹ sư Dữ liệu, Giả lập Lỗi & Phục hồi dữ liệu.
- **Phạm vi file phụ trách:**
  - `src/ingestion/crossref.py`
  - `src/ingestion/cleaning.py`
  - `src/ingestion/corruption.py`
  - `data/raw/`, `data/clean/`
- **Nhiệm vụ & Sản phẩm bàn giao:**
  - Xây dựng parser và cơ chế fallback offline nạp raw snapshot (`data/raw/crossref_records.json`).
  - Tiền xử lý, bóc tách XML, tính trường `age_days` và `text_for_embedding`.
  - Triển khai 6 kịch bản tiêm lỗi dữ liệu (drop 20%, blank summary, inject noise, truncate title, stale date, duplicate rows).
  - Tái nạp dữ liệu sạch khi kích hoạt quy trình Repair.
- **Đóng góp chính / Kiến thức thu nhận:**
  - Nắm vững Data Lineage, bảo toàn tính bất biến của raw artifacts và cơ chế tiêm lỗi mô phỏng suy thoái dữ liệu thực tế.

### 👤 Thành Viên 3 (Observability, Evaluation & Reporting)
- **Họ và tên:** `Ngô Hoàng Thụy Khuê` | **MSSV:** `2A202603017`
- **Vai trò:** Quản lý Chất lượng Dữ liệu, Đánh giá Hiệu năng & Báo cáo.
- **Phạm vi file phụ trách:**
  - `src/observability/quality.py`
  - `src/observability/reporting.py`
  - `src/evaluation/testset.py`, `src/evaluation/metrics.py`
  - `data/reports/`, `data/eval/`, `data/results/`
- **Nhiệm vụ & Sản phẩm bàn giao:**
  - Cấu hình Great Expectations 1.x (Ephemeral Context, 4 core expectations).
  - Thiết lập Freshness SLA (cảnh báo khi tỷ lệ bài báo `age_days > 180` vượt 25%).
  - Xây dựng bộ test set chuẩn 10 câu hỏi qua 4 nhóm nghiệp vụ (`summary`, `authors`, `date`, `categories`).
  - Lập trình bộ sinh báo cáo markdown (`phase1_report.md` và `corruption_report.md` với bảng đối chiếu 3 trạng thái).
- **Đóng góp chính / Kiến thức thu nhận:**
  - Thiết kế chốt chặn Data Observability, hiểu rõ hiện tượng Silent Failure trong RAG và đo lường định lượng mức độ suy giảm/phục hồi.
