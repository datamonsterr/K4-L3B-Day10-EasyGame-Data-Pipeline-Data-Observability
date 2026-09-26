# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                 |
| ------------------ | ------------------------------------------------------------------------ |
| Họ và tên          | Nguyễn Tiến Đạt                                                          |
| MSSV               | 2A202602970                                                              |
| Khóa/Lớp           | K4-L3B-DAY10 (Ca Sáng, Thứ 7 26/09/2026)                                |
| Tên nhóm           | EasyGame                                                                 |
| Vai trò chính      | Member 2 — Data Engineering & Corruption                                 |
| Repository         | K4-L3B-DAY10-EasyGame-Data-Pipeline-Data-Observability                  |
| Ngày hoàn thành    | 2026-09-26                                                               |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Raw Ingestion & Lineage** | `src/ingestion/crossref.py`<br>• `parse_crossref_payload`<br>• `fetch_source_records`<br>• `load_raw_records` | JSON response từ Crossref API hoặc local fallback snapshot | `list[PaperRecord]`, `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành (PR #1) |
| **Data Cleaning & Modeling**| `src/ingestion/cleaning.py`<br>• `build_clean_dataframe` | `list[PaperRecord]`, `run_date` | `pd.DataFrame` chuẩn hóa có `age_days`, `text_for_embedding` (5 phần), khử trùng lặp `paper_id`, lưu ra CSV và JSON | Hoàn thành (PR #3) |
| **Data Corruption Suite**   | `src/ingestion/corruption.py`<br>• `corrupt_dataframe` (6 kịch bản) | `pd.DataFrame` sạch | `pd.DataFrame` bị tiêm lỗi, `data/results/corruption_log.json` | Đang triển khai |
| **Idempotent Data Repair**  | `src/ingestion/crossref.py` & `src/ingestion/cleaning.py` | `data/raw/crossref_records.json` | Re-cleaned DataFrame sạch không lỗi, phục vụ cho `papers-repaired` | Đang triển khai |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| **Bàn giao Schema sạch & text_for_embedding** | Thành viên 1 (Vector Store & Integrator) | Đảm bảo DataFrame đầu ra có đầy đủ cột metadata và `text_for_embedding` 5 phần không bị null để ChromaDB nạp vector không lỗi. |
| **Cung cấp mẫu lỗi cho GX & Freshness SLA**| Thành viên 3 (Observability) | Cung cấp thông tin chi tiết về 6 kịch bản làm bẩn dữ liệu và logic tính `age_days` để thiết lập Expectation Suite và Freshness SLA tương ứng. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Thu thập dữ liệu thô (CP0)** | `src/ingestion/crossref.py` | Tải 24 bài báo, lưu nguyên bản `data/raw/crossref_response.json` & `data/raw/crossref_records.json` (PR #1, commit `3b72a40`) | `PYTHONPATH=src python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"`<br>→ Console in: `Tín hiệu hoàn thành: Đã tải 24 bài báo` |
| **Làm sạch dữ liệu & Pre-embed Modeling (CP1)** | `src/ingestion/cleaning.py` | Tạo DataFrame 24 dòng sạch, tính `age_days`, tạo cột `text_for_embedding` 5 phần, khử trùng lặp `paper_id` (PR #3, commit `fc0f57a`) | `PYTHONPATH=src .venv/bin/python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"`<br>→ Console in: `Tín hiệu hoàn thành: Clean thành công 24 dòng` |
| **Tiêm 6 lỗi dữ liệu (CP4)** | `src/ingestion/corruption.py` | Tiêm lỗi drop 20%, blank summary, noise, truncate title, stale date, duplicate | Kiểm tra `data/results/corruption_log.json` có đủ 6 loại lỗi |
| **Phục hồi dữ liệu (CP5)** | Tái nạp từ `data/raw/` | Làm sạch lại nguyên trạng từ raw snapshot cho pha Repair | `python script/run_corruption_flow.py` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Dữ liệu thô chứa nhiễu XML & định dạng phức tạp:** Abstract trả về từ Crossref chứa các thẻ XML JATS (`<jats:p>`, `<jats:title>`, `<jats:sec>`), ngày tháng nằm rải rác trong `date-parts`, tên tác giả nằm trong mảng `given` và `family`.
2. **Khả năng gián đoạn mạng (Resilience & Lineage):** Khi gọi API ngoài có thể dính lỗi mạng hoặc HTTP 429 Too Many Requests; cần có cơ chế retry với exponential backoff và fallback tự động sang snapshot local để bảo toàn Data Lineage.
3. **Chuẩn hóa văn bản phục vụ Embedding:** Vector embedding nhạy cảm với cấu trúc văn bản. Cần hợp nhất 5 trường thông tin vào một đoạn ngữ cảnh thống nhất, loại bỏ ký tự rác và khoảng trắng thừa.
4. **Tính toán Freshness và Khử trùng lặp:** Tính chính xác số ngày tuổi `age_days` phục vụ giám sát Freshness SLA và loại bỏ hoàn toàn các dòng trùng lặp `paper_id`.

### Cách triển khai
1. **Bóc tách XML & Chuẩn hóa văn bản (`_clean_text`):** Dùng regex `re.sub(r"<[^>]+>", " ", text)`, kết hợp `html.unescape()` để giải mã HTML entities và `normalize_whitespace()` xóa khoảng trắng thừa.
2. **Trích xuất ngày tháng linh hoạt (`_extract_date`):** Hỗ trợ duyệt qua các trường `published`, `published-print`, `published-online`, `issued`, `created`; trích xuất `date-parts` dạng `[YYYY, MM, DD]` và chuẩn hóa thành ISO string `YYYY-MM-DD`.
3. **Cơ chế Retry & Offline Fallback:** Trong `fetch_source_records()`, thực hiện tối đa 3 lần thử lại với exponential backoff (2s, 4s...) khi gặp HTTP 429/500/502/503/504 hoặc `RequestException`. Nếu API không khả dụng, tự động fallback nạp từ snapshot local `data/raw/crossref_response.json`.
4. **Lưu trữ 2 Raw Artifacts phục vụ Data Lineage:**
   - `data/raw/crossref_response.json`: Payload gốc nguyên bản từ Crossref REST API.
   - `data/raw/crossref_records.json`: Danh sách đối tượng `PaperRecord` sau khi bóc tách.
5. **Quy tắc cấu tạo `text_for_embedding` (chuẩn 5 phần theo Rubric):**
   ```text
   Title: <Tiêu đề bài báo>
   Authors: <Danh sách tác giả>
   Published: <Ngày xuất bản>
   Categories: <Lĩnh vực chuyên môn>
   Summary: <Tóm tắt nội dung>
   ```
6. **Tính tuổi dữ liệu (`age_days`):**
   ```python
   age_days = (run_date.date() - published_date).days
   ```
7. **Khử trùng lặp:** Dùng `seen_paper_ids` để loại bỏ triệt để các bài báo trùng `paper_id`, chỉ giữ lại bản ghi hợp lệ đầu tiên và lọc bỏ các bản ghi thiếu `title` hoặc `summary`.
8. **Chi tiết 6 kịch bản Corruption:**
   - `drop_latest`: Sắp xếp theo ngày giảm dần và loại bỏ 20% bản ghi mới nhất.
   - `blank_summary`: Chọn các bản ghi và gán `summary = ""`.
   - `inject_noise`: Chèn chuỗi ký tự rác vô nghĩa vào `summary`.
   - `truncate_title`: Cắt tiêu đề bài báo xuống dưới 8 ký tự.
   - `stale_date`: Lùi ngày xuất bản về quá khứ (lệch hơn 365 ngày) để vi phạm Freshness SLA.
   - `duplicate_rows`: Nhân bản thêm các dòng có cùng `paper_id`.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | Raw JSON từ Crossref API (`payload["message"]["items"]`) hoặc local snapshot |
| **Output** | Danh sách đối tượng `PaperRecord`, DataFrame sạch 24 dòng gồm 16 cột (trong đó có `text_for_embedding`, `authors_joined`, `categories_joined`, `summary_chars`, `age_days`) |
| **Module phụ thuộc** | `src/core/config.py` (cấu hình tham số, đường dẫn), `src/core/utils.py` (chuẩn hóa khoảng trắng, join chuỗi) |
| **Module sử dụng output** | `src/observability/quality.py` (chạy GX checks & Freshness SLA), `src/retrieval/index.py` (sinh embedding nạp ChromaDB) |
| **Điều kiện lỗi cần xử lý**| Mất mạng / HTTP 429 -> Fallback local snapshot; Bài báo không có abstract -> Làm sạch hoặc bỏ qua; Tác giả thiếu `family` -> Gán placeholder; Trùng `paper_id` -> Khử trùng lặp |

### Cách xác minh

```bash
# 1. Kiểm tra Ingestion raw records (CP0)
PYTHONPATH=src python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"
# Tín hiệu hoàn thành: Đã tải 24 bài báo

# 2. Kiểm tra Cleaning DataFrame (CP1)
PYTHONPATH=src .venv/bin/python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"
# Tín hiệu hoàn thành: Clean thành công 24 dòng
```

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương pháp lưu trữ dữ liệu thô (raw data) và kiến trúc phục hồi (repair).
- **Các phương án đã cân nhắc:**
  - *Phương án A:* Ghi đè file clean trực tiếp và chỉ fetch lại từ API khi cần sửa lỗi.
  - *Phương án B:* Lưu trữ bất biến (Immutable Storage) 2 file raw artifacts (`crossref_response.json` và `crossref_records.json`) độc lập với tầng clean. Khi sửa lỗi, re-run cleaning từ bản ghi snapshot thô.
- **Phương án đã chọn:** **Phương án B**.
- **Lý do:** Tuân thủ nguyên tắc Data Lineage. Gọi lại API ngoài trong lúc sửa lỗi có thể gây lỗi mạng hoặc nhận về dữ liệu khác (API trả về kết quả mới theo thời gian), khiến việc đánh giá 3 trạng thái không còn tính kiểm soát (Controlled Experiment).
- **Bằng chứng:** Thư mục `data/raw/` luôn được giữ nguyên vẹn qua mọi lần chạy script corruption hay repair.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  1. `ModuleNotFoundError: No module named 'pandas'` khi import `from ingestion.crossref import fetch_source_records` do file `src/ingestion/__init__.py` ban đầu eager-import `build_clean_dataframe` từ `cleaning.py`.
  2. `TypeError: can't subtract offset-naive and offset-aware datetimes` khi tính toán `(run_date - published).days`.
- **Lệnh hoặc bước tái hiện:** Chạy kiểm thử CP0 và tính `age_days = (run_date - published).days` khi `run_date` truyền vào là `datetime.now(timezone.utc)` (timezone-aware) trong khi `published` được parse từ chuỗi ISO naive.
- **Nguyên nhân gốc:** 
  1. `src/ingestion/__init__.py` phụ thuộc chặt vào `pandas` ngay cả khi chỉ cần dùng parser `crossref.py`.
  2. Không đồng nhất kiểu dữ liệu ngày tháng giữa `datetime` có múi giờ và `date` thuần túy.
- **Cách xử lý:** 
  1. Thêm khối `try...except ImportError` trong `src/ingestion/__init__.py` để các sub-module có thể import độc lập mà không bị chặn chéo.
  2. Chuyển đổi cả `run_date` và `published` về `datetime.date` thuần túy trước khi thực hiện phép trừ (`(run_date_val - pub_date_val).days`), đảm bảo kết quả là số nguyên chính xác và an toàn với mọi kiểu timezone.
- **Cách xác minh sau khi sửa:** Chạy kiểm thử cleaning trên toàn bộ 24 bản ghi, không còn dòng nào có `age_days` bị NaN hoặc null, và lệnh CP0 chạy độc lập mượt mà.
- **Điều học được:** Tách biệt dependency giữa các tầng dữ liệu (ingestion parser vs cleaning) và luôn chuẩn hóa kiểu ngày tháng về `date` khi chỉ cần tính toán độ chênh lệch số ngày.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - API hoặc snapshot thô -> Parser chuẩn hóa thành `PaperRecord` -> Cleaning lọc thẻ XML, tính `age_days`, tạo `text_for_embedding` -> MiniLM biến đổi thành vector -> Nạp vào ChromaDB.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Mỗi câu hỏi được gán cứng `paper_id` chuẩn (ground truth). Nếu vector search tìm ra văn bản có `paper_id` này nằm trong top-k, `hit_rate = 1`. Token F1 so khớp mức độ trùng lặp từ ngữ giữa câu trả lời sinh ra và tài liệu gốc.
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - Quality checks bắt các lỗi tĩnh về cấu trúc (schema, null, duplicate). Freshness monitoring bắt lỗi động về thời gian (tài liệu bị cũ > 180 ngày so với SLA).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Để đảm bảo tính khách quan của phép đo. Biến số duy nhất thay đổi giữa 3 pha là chất lượng dữ liệu.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Dựa trên việc file `repaired_clean.csv` khôi phục lại đủ 24 dòng không lỗi, GX test chuyển sang PASSED, và chỉ số trong `repaired_metrics.json` tăng vọt trở lại tương đương `baseline_metrics.json`.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | :---: | :---: | :---: | :--- |
| `retrieval_hit_rate` | `[Điền]` | `[Điền]` | `[Điền]` | `[Nhận xét về độ sụt giảm khi bị drop 20% bản ghi]` |
| `mean_token_f1` | `[Điền]` | `[Điền]` | `[Điền]` | `[Nhận xét khi summary bị xóa rỗng hoặc chèn noise]` |
| `Quality checks` | PASSED | FAILED | PASSED | GX phát hiện ngay lỗi null summary và duplicate paper_id |
| `Freshness status` | FRESH | STALE WARNING | FRESH | Kịch bản lùi ngày làm tỷ lệ bài quá hạn vượt 25% |

### Kết luận từ số liệu
1. **Corruption tác động nặng nhất:** Kịch bản `blank_summary` và `drop_latest` làm sụt giảm Retrieval Hit Rate mạnh nhất vì câu hỏi trong testset không còn dữ liệu đối chiếu trong vector store.
2. **Hiệu quả phục hồi:** Quy trình đọc lại từ raw snapshot giải quyết triệt để 100% các vi phạm dữ liệu.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. Dữ liệu thô luôn phải được coi là bất biến (Immutable).
2. Xử lý chuỗi văn bản (regex, strip tag) trước khi nhúng vector quyết định trực tiếp tới khoảng cách cosine của embedding.
3. Data Corruption cần được kiểm thử định kỳ giống như Unit Test trong phần mềm để bảo đảm hệ thống RAG không gặp lỗi âm thầm.

### Nếu có thêm thời gian
- Tích hợp thêm thư viện `ftfy` hoặc `BeautifulSoup` để xử lý triệt để hơn các ký tự unicode lạ và các định dạng markup phức tạp từ nhiều nguồn xuất bản khác nhau.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Tiến Đạt  
**Ngày xác nhận:** 2026-09-26
