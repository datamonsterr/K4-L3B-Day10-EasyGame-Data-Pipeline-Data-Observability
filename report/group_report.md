# Group Report — Day 10: Data Pipeline & Data Observability

> Dùng mẫu này cho báo cáo chung của nhóm 3–5 thành viên. Thay toàn bộ nội dung trong dấu `[ ]` bằng thông tin và kết quả thực tế. Xóa các dòng hướng dẫn không còn cần thiết trước khi nộp.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                                                                 |
| ------------------ | ------------------------------------------------------------------------ |
| Khóa/Lớp           | K4-L3B-DAY10 (Ca Sáng, Thứ 7 26/09/2026)                                |
| Tên nhóm           | EasyGame                                                                 |
| Repository         | K4-L3B-DAY10-EasyGame-Data-Pipeline-Data-Observability                  |
| Ngày hoàn thành    | 2026-09-26                                                               |

### Thành viên và phân công (Nhóm 3 người)

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Phạm Thành Đạt | 2A202602721 | Trưởng nhóm / Pipeline Integrator & Vector Store | `core/`, `retrieval/index.py`, `phase1.py`, `corruption_flow.py`, `script/` |
| 2 | Nguyễn Tiến Đạt | 2A202602970 | Data Engineering & Corruption | `crossref.py`, `cleaning.py`, `corruption.py`, raw data & repair loader |
| 3 | Ngô Hoàng Thụy Khuê | 2A202603017 | Observability, Evaluation & Reporting | `quality.py` GX 1.x, `testset.py`, `reporting.py`, Freshness SLA |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

[Viết phần tóm tắt tại đây.]

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API / Local fallback | Fetch retry, parse JSON thành `PaperRecord` | `data/raw/crossref_records.json` | Nguyễn Tiến Đạt (Member 2) |
| Cleaning          | `list[PaperRecord]` | Bóc tách XML, tính `age_days`, tạo `text_for_embedding` | `data/clean/papers_clean.csv`, `.json` | Nguyễn Tiến Đạt (Member 2) |
| Embedding/index   | Clean DataFrame | Nạp vector MiniLM, quản lý 3 collection ChromaDB | `data/chroma/`, `papers_embeddings*.json` | Phạm Thành Đạt (Member 1) |
| Evaluation        | Clean DataFrame & ChromaDB | Tạo 10 câu test set, tính Hit Rate & Token F1 | `data/eval/test_set.json`, `baseline_metrics.json` | Ngô Hoàng Thụy Khuê (Member 3) |
| Observability     | Clean/Corrupted DataFrame | Chốt kiểm dịch GX 1.x (4 expectations) & Freshness SLA | `data/quality/*_quality_report.json` | Ngô Hoàng Thụy Khuê (Member 3) |
| Corruption/repair | Clean DataFrame & Raw records | Tiêm 6 kịch bản lỗi & Phục hồi từ raw snapshot | `corruption_log.json`, `papers-repaired` | Nguyễn Tiến Đạt & Phạm Thành Đạt |
| Orchestration     | Toàn bộ modules | Kết nối luồng Phase 1 & Corruption Flow end-to-end | `data/reports/phase1_report.md`, `corruption_report.md` | Phạm Thành Đạt (Member 1) |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `gemini`         |
| `LLM_MODEL`                | `gemini-3.5-flash`         |
| Embedding model              | `models/gemini-embedding-2` (Gemini Embedding 2, thay thế `sentence-transformers` sau hotfix)         |
| Số lượng Crossref records | 24 (`max_results = 24`)         |
| Retrieval`top_k`           | 4         |
| Freshness threshold          | 180 ngày (ngưỡng stale ratio 25%)         |
| Random seed, nếu có        | Không sử dụng random seed cố định — dữ liệu Crossref được snapshot sẵn trong `data/raw/`, không fetch ngẫu nhiên khi chạy lại         |
 

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 10:45                  | `data/reports/phase1_report.md`, `data/results/baseline_metrics` |
| Corruption flow   | Thành công | 12:44                  | `data/reports/corruption_report.md`, `data/results/corruption_log.json` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | `data/raw/crossref_response.json` `data/raw/crossref_records.json`|
| Query/filter                | Query `"agentic retrieval augmented generation large language model"`, filter `from-pub-date:<180 ngày trước>,has-abstract:true`                  |
| Thời điểm lấy dữ liệu | 9:45 (chạy `run_phase1.py`, dùng snapshot offline có sẵn trong  `data/raw/`)                          |
| Số record nhận được    | 24                   |
| Cơ chế retry/backoff      | Nếu `data/raw/crossref_records.json` đã tồn tại, pipeline load lại từ file thay vì gọi API; nếu chưa có, `fetch_source_records()` gọi Crossref REST API theo query/filter cấu hình sẵn (fallback offline giúp tránh phụ thuộc mạng khi chấm bài)                       |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id`    | string (DOI)   | Có         | Khóa chính, định danh duy nhất bài báo | Bỏ record nếu rỗng hoặc trùng `paper_id` đã thấy (dedupe) |
| `title`       | string         | Có         | Tiêu đề bài báo | Bỏ record nếu title rỗng sau khi chuẩn hóa whitespace |
| `summary`     | string         | Có         | Tóm tắt nội dung | Loại bỏ thẻ HTML/XML (`<jats:p>`...) bằng regex, chuẩn hóa whitespace; bỏ record nếu summary rỗng sau xử lý |
| `authors`     | list[string]   | Không      | Danh sách tác giả | Chuẩn hóa whitespace từng tên, lọc phần tử rỗng; join thành `authors_joined` |
| `categories`  | list[string]   | Không      | Lĩnh vực/chủ đề | Lọc phần tử rỗng; nếu rỗng thì `primary_category` = "General" |
| `published`/`updated` | date (YYYY-MM-DD) | Có (published) | Ngày công bố/cập nhật, dùng tính `age_days` và Freshness SLA | Nếu parse lỗi, `published` fallback về `run_date`; `updated` fallback về `published` |
| `age_days`    | int            | Có         | Tuổi dữ liệu = run_date − published, đầu vào cho Freshness Check | Tính lại mỗi lần chạy dựa trên `run_date` hiện tại |
| `text_for_embedding` | string   | Có         | Chuỗi 5 phần (Title/Authors/Published/Categories/Summary) dùng để tạo vector embedding | Ghép từ các trường đã chuẩn hóa ở trên, không cho phép rỗng |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại bỏ record không có `paper_id` hoặc trùng `paper_id` | Uniqueness/Completeness  |              0 (không có record nào bị loại ở baseline) | `expect_column_values_to_be_unique` trên `paper_id`, PASS trong `baseline_quality_report.json` |
| Loại bỏ record không có `title` hoặc `summary` (sau khi strip HTML/XML) | Completeness/Validity |              0 (không có record nào bị loại ở baseline) | `expect_column_values_to_not_be_null` trên `title`, `text_for_embedding` |
| Ràng buộc độ dài `summary` trong khoảng [30, 20000] ký tự | Validity |              0 ở baseline; 4 record (18.2%) vi phạm ở pha corrupted do bị xóa trắng | `expect_column_value_lengths_to_be_between`, `data/quality/corrupted_quality_report.json` |
| Chuẩn hóa ngày `published`/`updated` về `YYYY-MM-DD`, fallback `run_date` nếu parse lỗi | Validity | 0 (tất cả record parse thành công) | Kiểm tra thủ công trường `published` trong `papers_clean.csv` |
 
Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:
 
`paper_id` được dùng trực tiếp từ DOI của Crossref (ví dụ `10.1145/3637528.3671801`), đảm bảo tính duy nhất toàn cục và được dùng làm ID document khi index vào ChromaDB. `age_days` được tính bằng `(run_date − published).days` tại thời điểm chạy pipeline, dùng làm input cho Freshness SLA (ngưỡng 180 ngày). `text_for_embedding` được ghép theo khuôn 5 phần cố định — `Title: ...`, `Authors: ...`, `Published: ...`, `Categories: ...`, `Summary: ...` — nhằm cung cấp ngữ cảnh đầy đủ (metadata + nội dung) cho mô hình embedding, giúp truy vấn theo tác giả/ngày/thể loại vẫn có tín hiệu tốt thay vì chỉ nhúng phần tóm tắt.
 
## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 10                 |
| Các`question_type`                    | `summary`, `authors`, `date`, `categories`                  |
| Ground-truth document ID                 | `ground_truth_doc_ids` gán thủ công theo `paper_id` (DOI) của bài báo được hỏi, dùng để đối chiếu với top-k kết quả retrieval     |
| Embedding model                          | `models/gemini-embedding-2`                  |
| Vector store/collection                  | ChromaDB persistent client — 3 collection riêng: `papers-baseline`, `papers-corrupted`, `papers-repaired`, cosine similarity (`hnsw.space = cosine`)                 |
| Retrieval`top_k`                       | 4                   |
| LLM provider/model                       | `gemini` / `gemini-2.5-flash`                   |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` (10 câu, không đổi qua 3 lần chạy baseline/corrupted/repaired) |
 
Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:
 
Test set (`test_set.json`) được sinh một lần từ dữ liệu clean baseline và được tái sử dụng nguyên vẹn cho cả 3 trạng thái để đảm bảo phép so sánh là "apples-to-apples" — mọi thay đổi về metric (retrieval hit rate, token F1, judge score) chỉ phản ánh sự thay đổi trong dữ liệu được index/truy vấn (do corruption hoặc repair), chứ không bị nhiễu bởi việc câu hỏi hay ground-truth thay đổi giữa các lần chạy. Nếu regenerate test set ở mỗi trạng thái, sự khác biệt về câu hỏi có thể che lấp hoặc phóng đại tác động thực sự của corruption/repair.
 
## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | [Ghi chú] |
| Cleaned dataset          | `data/clean/`                        | Có | [Ghi chú] |
| Embedding manifest/index | `data/embeddings/`                   | Có | [Ghi chú] |
| Evaluation set           | `data/eval/`                         | Có | [Ghi chú] |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | [Ghi chú] |
| Quality/freshness        | `data/quality/`                      | Có | [Ghi chú] |
| Baseline report          | `data/reports/phase1_report.md`      | Có | [Ghi chú] |

### Baseline metrics
 
| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     100.0% (1.0000) | Toàn bộ 10/10 câu hỏi đều retrieval đúng document trong top-`k=4`  |
| `mean_token_f1`      |     1.0000 | Câu trả lời sinh ra khớp gần như tuyệt đối với ground truth về mặt token, cho thấy context truy xuất đủ chính xác để LLM trả lời đúng                          |
| `judge_accuracy`     |     100.0% | LLM-judge (Gemini) đánh giá toàn bộ 10 câu trả lời là đúng                           |
| `mean_judge_score`   |     5 / 5 | Điểm chất lượng câu trả lời tối đa theo thang chấm của judge                           |
| Ragas, nếu có        | N/A (bỏ qua) | `RUN_RAGAS` không được set = 1, nhóm chưa bật pass Ragas do thời gian chạy chậm hơn (ghi rõ trong `phase1_report.md`: "Set RUN_RAGAS=1 to enable the slower Ragas pass") |
 
## 8. Data quality và freshness

### Quality checks
 
| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `expect_table_row_count_to_be_between` | Completeness       | [5, 5000] dòng         | PASS — observed 24 | `baseline_quality_report.json` |
| `expect_column_values_to_not_be_null` (`paper_id`, `title`, `text_for_embedding`) | Completeness       | 0% null         | PASS — unexpected_percent 0.0% | `baseline_quality_report.json` |
| `expect_column_values_to_be_unique` (`paper_id`) | Uniqueness       | 0% trùng lặp         | PASS — unexpected_percent 0.0% | `baseline_quality_report.json` |
| `expect_column_value_lengths_to_be_between` (`summary`) | Validity       | Độ dài [30, 20000] ký tự         | PASS — unexpected_percent 0.0% | `baseline_quality_report.json` |
| Freshness SLA (`is_fresh`) | Timeliness       | Stale ratio ≤ 25% (ngưỡng 180 ngày)         | PASS — stale ratio 4.2% (1/24 dòng) | `baseline_quality_report.json` |
 
### Freshness
 
| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Dataset clean baseline (`papers_clean.csv`), trường `published`/`age_days`            |
| Timestamp mới nhất       | 2026-07-22 (bài mới nhất)                         |
| Ngưỡng freshness         | 180 ngày (record cũ hơn 180 ngày được tính là "stale"); ngưỡng cảnh báo khi stale ratio > 25%                         |
| Trạng thái baseline      | Fresh (PASS)               |
| Lý do                     | Chỉ 1/24 bài (4.2%) có tuổi > 180 ngày, thấp hơn nhiều so với ngưỡng cảnh báo 25%, nên `is_fresh = true` |
 
## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| `drop_latest` (Drop latest records) | Bỏ 4 bản ghi mới nhất (16.7%) mô phỏng mất dữ liệu tươi | 4 | Giảm tổng số dòng, có thể ảnh hưởng retrieval nếu bài bị hỏi nằm trong nhóm bị drop | Tổng dòng giảm 24→22 (đã cộng bù bởi 2 dòng duplicate) | Repair từ raw snapshot khôi phục đủ 24 dòng |
| `blank_summary` (Blank summary) | Xóa trắng tóm tắt của 2 dòng | 2 | Vi phạm `expect_column_value_lengths_to_be_between` | Góp phần vào 4 dòng fail length check (18.2%), GX suite FAIL | Rebuild `text_for_embedding`/`summary` từ raw records |
| `inject_noise` (Inject noise) | Chèn chuỗi `[CORRUPTED_DATA_NOISE_#$!@%^&*]` vào summary của 2 dòng | 2 | Giảm chất lượng ngữ nghĩa của embedding, có thể ảnh hưởng judge score | Không trigger GX fail trực tiếp nhưng làm nhiễu context truy xuất | Repair phục hồi `summary` gốc, loại bỏ noise |
| `truncate_title` (Truncate title) | Cắt title xuống còn 6 ký tự (ví dụ "Advanc") của 2 dòng | 2 | Giảm khả năng match câu hỏi theo tên bài báo (retrieval theo title) | Không có expectation riêng cho title length, nhưng ảnh hưởng đến câu hỏi loại `authors`/`summary` khi hỏi theo tên đầy đủ | Repair phục hồi `title` đầy đủ từ raw snapshot |
| `stale_date` (Stale date) | Lùi ngày publish 365 ngày trên 8 dòng | 8 | Vi phạm Freshness SLA (stale ratio > 25%) | **Tác động lớn nhất**: stale ratio tăng từ 4.2% lên 40.9% (9/22 dòng), `is_fresh = false` | Repair khôi phục `published` gốc, stale ratio về 4.2% |
| `duplicate_rows` (Duplicate rows) | Nhân đôi 2 dòng gây trùng `paper_id` | 2 | Vi phạm `expect_column_values_to_be_unique` | 4 dòng (18.2%) vi phạm unique check, GX suite FAIL | Rebuild dataframe từ raw (dedupe theo `paper_id` trong bước cleaning) loại bỏ hoàn toàn duplicate |
 
Corruption log:
 
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log ghi đầy đủ 6 kịch bản (`scenarios_applied: 6`), mỗi kịch bản có `name`, `count`, `affected_paper_ids` và tham số riêng (`noise_pattern`, `days_shifted`, `details` cho truncate_title), cùng summary tổng (`original_rows: 24`, `corrupted_rows: 22`, `dropped_rows: 4`, `duplicated_rows: 2`) — đủ để truy vết chính xác từng bản ghi bị ảnh hưởng.
Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:
 
Cơ chế `repair_from_raw_snapshot()` **không** vá trực tiếp lên dữ liệu đã bị corrupt (ví dụ không tự điền lại summary rỗng bằng placeholder, không tự sửa ngày). Thay vào đó, hàm đọc lại snapshot thô bất biến `data/raw/crossref_records.json` (fallback `crossref_response.json`) và chạy lại toàn bộ bước `build_clean_dataframe()` từ đầu, sau đó rebuild collection ChromaDB `papers-repaired` từ dữ liệu sạch này. Vì raw snapshot không bao giờ bị corruption chạm vào, quy trình repair là **idempotent và tất định**: chạy lại bao nhiêu lần cũng luôn cho ra đúng 24 bản ghi chuẩn, khớp 100% với baseline — khác với cách "che lỗi" như làm tròn số liệu hay bỏ qua expectation fail.
 

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      100.0% |       90.0% |      100.0% |                      -10.0 điểm % |             100% | Drop 4 bản ghi mới + duplicate làm trượt tài liệu đúng khỏi top-`k=4` cho 1/10 câu |
| `mean_token_f1`        |      1.0000 |       0.8692 |      1.0000 |                      -0.1308 |             100% | Blank summary + inject noise làm câu trả lời sinh ra lệch khỏi ground truth |
| `judge_accuracy`       |      100.0% |       90.0% |      100.0% |                      -10.0 điểm % |             100% | Đồng biến với retrieval hit rate, phản ánh 1/10 câu bị đánh giá sai |
| `mean_judge_score`     |      5.00/5 |       4.40/5 |      5.00/5 |                      -0.60 |             100% | LLM-judge hạ điểm các câu trả lời liên quan tài liệu bị corrupt |
| Quality checks pass/fail |      PASS (6/6) |       FAIL (4/6, 2 fail: unique + length) |      PASS (6/6) |                      2 expectation fail (unique, length) |             100% | `duplicate_rows` → fail unique; `blank_summary` → fail length |
| Freshness status         |      Fresh (4.2%) |       Stale (40.9%) |      Fresh (4.2%) |                      +36.7 điểm % stale ratio |             100% | `stale_date` (lùi 365 ngày, 8 dòng) là nguyên nhân trực tiếp duy nhất |
 
Kết luận nhân quả được hỗ trợ bởi artifacts:
 
1. **`duplicate_rows` + `blank_summary`** (nhân đôi 2 dòng, xóa trắng 2 summary) → `expect_column_values_to_be_unique` và `expect_column_value_lengths_to_be_between` chuyển từ PASS sang FAIL, 4/22 dòng (18.2%) vi phạm mỗi expectation (theo `corrupted_quality_report.json`) → Overall Quality Gate FAIL, kéo `mean_token_f1` giảm từ 1.0000 xuống 0.8692 vì nội dung truy xuất bị thiếu/nhiễu.
2. **`stale_date`** (lùi ngày 365 ngày trên 8 dòng) → Freshness SLA chuyển từ PASS (stale ratio 4.2%) sang FAIL (stale ratio 40.9%, vượt ngưỡng 25%) → góp phần vào `retrieval_hit_rate` giảm còn 90.0% do một số câu hỏi loại `date` bị ảnh hưởng bởi thông tin ngày sai lệch.
3. **Repair từ raw snapshot** (`repair_from_raw_snapshot()`) → tất cả 6 expectation của GX quay lại PASS và Freshness SLA quay lại PASS (stale ratio 4.2%) → toàn bộ 4 agent metric (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`) phục hồi 100% về đúng giá trị baseline, xác nhận repair khôi phục dữ liệu chứ không chỉ che lỗi cục bộ.
Riêng `truncate_title` và `inject_noise` không có expectation riêng để bắt trực tiếp (không fail GX), nên tác động của 2 kịch bản này chỉ thể hiện gián tiếp qua sự sụt giảm của `mean_token_f1`/`mean_judge_score` chứ không phản ánh trong bảng Quality checks — đây là giới hạn của bộ 6 expectation hiện tại.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:
 
- **Triệu chứng:** Khi chạy lại `script/run_phase1.py` lần thứ hai mà chưa xóa thư mục `data/chroma`, pipeline crash với lỗi `chromadb.errors.UniqueConstraintError: Collection papers-baseline already exists`.
- **Nguyên nhân:** Module index (`retrieval/index.py`) gọi `client.create_collection(name=collection_name)`, hàm này mặc định ném lỗi nếu collection đã tồn tại sẵn trong metadata database của ChromaDB — một giả định không tương thích với việc chạy lại pipeline nhiều lần (idempotency) mà các module khác (cleaning, corruption) đều tuân thủ.
- **Cách xử lý:** Bọc bước tạo collection bằng try/except, chủ động xóa collection cũ trước khi tạo mới:
```python
  try:
      client.delete_collection(name=collection_name)
  except Exception:
      pass
  collection = client.create_collection(name=collection_name, configuration={"hnsw": {"space": "cosine"}})
```
- **Cách xác minh:** Chạy liên tiếp `uv run python script/run_phase1.py` rồi `uv run python script/run_corruption_flow.py` nhiều lần mà không cần `rm -rf data/chroma` thủ công; cả hai script đều chạy trơn tru và tạo lại đúng 3 collection (`papers-baseline`, `papers-corrupted`, `papers-repaired`) với artifact cuối (`phase1_report.md`, `corruption_report.md`) không đổi.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Bộ test set chỉ 10 câu, 4 loại question_type | Metric (hit rate, F1) dễ bị dao động lớn khi chỉ 1 câu sai (mỗi câu chiếm 10% điểm số) | Mở rộng test set lên ≥30 câu, đa dạng thêm loại câu hỏi (so sánh nhiều bài, câu hỏi phủ định), đo lại độ ổn định qua nhiều lần chạy |
| Ragas chưa được bật (`RUN_RAGAS=0`) | Thiếu các chỉ số đánh giá RAG chuyên sâu hơn (faithfulness, context precision/recall) để đối chiếu với judge tự viết | Chạy lại với `RUN_RAGAS=1`, so sánh kết quả Ragas với `judge_accuracy`/`mean_judge_score` hiện tại trên cùng test set |
| `truncate_title` và `inject_noise` không có expectation GX riêng để bắt trực tiếp | Corruption vẫn "lọt" qua Quality Gate (không fail GX) dù ảnh hưởng ngầm đến `mean_token_f1`/`judge_score` | Thêm expectation kiểm tra độ dài tối thiểu `title` và regex phát hiện ký tự đặc biệt bất thường trong `summary` |
| Corruption/repair mới kiểm chứng trên một lần chạy với tham số cố định (365 ngày, 1 noise pattern...) | Chưa đo được độ ổn định của Quality Gate và khả năng phục hồi khi tham số corruption thay đổi ngẫu nhiên | Tham số hóa corruption (seed, tỷ lệ, mức độ) và chạy lặp lại nhiều lần để đo phương sai của các chỉ số phục hồi |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
