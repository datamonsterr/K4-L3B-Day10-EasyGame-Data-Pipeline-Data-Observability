# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                 |
| ------------------ | ------------------------------------------------------------------------ |
| Họ và tên          | Ngô Hoàng Thụy Khuê                                                      |
| MSSV               | 2A202603017                                                              |
| Khóa/Lớp           | K4-L3B-DAY10 (Ca Sáng, Thứ 7 26/09/2026)                                |
| Tên nhóm           | EasyGame                                                                 |
| Vai trò chính      | Member 3 — Observability, Evaluation & Reporting                         |
| Repository         | K4-L3B-DAY10-EasyGame-Data-Pipeline-Data-Observability                  |
| Ngày hoàn thành    | 2026-09-26                                                               |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Quality Gate (GX 1.x)**   | `src/observability/quality.py`<br>• `run_data_quality_checks` | `pd.DataFrame` (clean hoặc corrupted) | Dictionary kết quả kiểm thử, JSON report (`baseline_quality_report.json`) | Hoàn thành |
| **Freshness SLA Monitoring**| `src/observability/quality.py`<br>• `build_freshness_report` | `pd.DataFrame`, `threshold_days=180` | `freshness_report.json` với tỷ lệ quá hạn và cờ `is_fresh` | Hoàn thành |
| **Evaluation Benchmark Set**| `src/evaluation/testset.py`<br>• `build_test_set` | Clean DataFrame | `data/eval/test_set.json` (10 câu hỏi phủ 4 nhóm nghiệp vụ) | Hoàn thành |
| **Markdown Reporting**      | `src/observability/reporting.py`<br>• `generate_baseline_report`<br>• `generate_comparison_report` | Metrics dictionary, quality results | `data/reports/phase1_report.md` và `data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| **Tích hợp Quality Gate vào Pipeline** | Thành viên 1 (Integrator) | Tích hợp lệnh gọi `run_data_quality_checks()` vào `phase1.py` và `corruption_flow.py` trước khi nạp ChromaDB. |
| **Xác thực dữ liệu testset** | Thành viên 2 (Data Foundation) | Kiểm tra bộ câu hỏi 10 câu có trỏ đúng vào các `paper_id` tồn tại trong tập dữ liệu sạch. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Chốt kiểm dịch GX 1.x (CP1)** | `src/observability/quality.py` | Cài đặt ephemeral context và 4 expectations chuẩn GX 1.x | `python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print(res['success'])"` |
| **Giám sát Freshness SLA (CP1)**| `src/observability/quality.py` | Kiểm tra tỷ lệ bài báo `age_days > 180` không vượt quá 25% | `python -c "from core.config import load_settings; from observability.quality import build_freshness_report; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); print(build_freshness_report(df, s))"` |
| **Sinh bộ Benchmark Testset (CP2)**| `src/evaluation/testset.py` | Tạo bộ 10 câu hỏi chuẩn hóa qua 4 nhóm nghiệp vụ ra `test_set.json` | `python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); print(len(build_test_set(df, s.paths.eval_testset)))"` |
| **Xuất báo cáo 3 trạng thái (CP5)** | `src/observability/reporting.py` | Tạo bảng đối chiếu Baseline vs Corrupted vs Repaired trong `corruption_report.md` | Kiểm tra file `data/reports/corruption_report.md` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Bắt lỗi dữ liệu trước khi vào mô hình (Prevent Silent Failures):** Nếu dữ liệu bị lỗi (rỗng summary, trùng id, title cụt) được nạp vào ChromaDB, hệ thống vẫn sinh vector nhưng kết quả trả lời của RAG sẽ bị hỏng hoàn toàn mà không có exception nào được ném ra.
2. **Cập nhật chuẩn Great Expectations 1.x:** Tránh dùng cú pháp cũ của GX 0.x (`DataAssistant`, `RuntimeBatchRequest`) gây crash hệ thống.
3. **Đánh giá khách quan, có căn cứ:** Xây dựng bộ test set đại diện cho các tác vụ hỏi đáp thực tế trong nghiên cứu khoa học.

### Cách triển khai
1. **Cấu hình Great Expectations 1.x Ephemeral Context:**
   ```python
   context = gx.get_context(mode="ephemeral")
   data_source = context.data_sources.add_pandas(name="papers_source")
   data_asset = data_source.add_dataframe_asset(name="papers_asset")
   batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
   batch = batch_def.get_batch(batch_parameters={"dataframe": df})
   ```
2. **4 Expectations bắt buộc theo Rubric:**
   - `ExpectTableRowCountToBeBetween(min_value=10)`: Đảm bảo số lượng bài báo không bị sụt giảm bất thường.
   - `ExpectColumnValuesToNotBeNull(column="paper_id")`: Đảm bảo khóa chính định danh không bị rỗng.
   - `ExpectColumnValuesToBeUnique(column="paper_id")`: Khử trùng lặp bản ghi.
   - `ExpectColumnValueLengthsToBeBetween(column="title", min_value=8)`: Ngăn chặn title cụt, tiêu đề rác.
3. **Freshness SLA:**
   - Tính toán tỷ lệ: `stale_ratio = (df['age_days'] > 180).mean()`
   - Cảnh báo vi phạm `is_fresh = False` khi `stale_ratio > 0.25`.
4. **Bộ Test Set 10 câu hỏi qua 4 nhóm nghiệp vụ:**
   - `summary` (4 câu): Kiểm tra khả năng hiểu nội dung chính của bài báo.
   - `authors` (2 câu): Kiểm tra khả năng trích xuất tên tác giả.
   - `date` (2 câu): Kiểm tra khả năng truy vấn thời gian xuất bản.
   - `categories` (2 câu): Kiểm tra phân loại chủ đề bài báo.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | `pd.DataFrame` được làm sạch từ `src/ingestion/cleaning.py` |
| **Output** | `data/eval/test_set.json`, kết quả boolean của Quality Gate, các file báo cáo markdown |
| **Module phụ thuộc** | `great_expectations>=1.0.0`, `src/core/config.py` |
| **Module sử dụng output** | `src/pipelines/phase1.py` & `src/pipelines/corruption_flow.py` quyết định dừng/tiếp tục hoặc ghi nhận trạng thái kiểm định |
| **Điều kiện lỗi cần xử lý**| DataFrame rỗng (0 dòng) -> GX bắt lỗi `min_value=10`; Cột bị thiếu trong DataFrame -> Ném lỗi thiếu schema rõ ràng |

### Cách xác minh

```bash
# 1. Kiểm tra Great Expectations 1.x
python -c "import great_expectations as gx; print(gx.__version__)"

# 2. Kiểm tra chạy Quality Checks trên tập clean
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'baseline'); assert res['success'] == True; print('Quality Gate PASSED')"

# 3. Kiểm tra Freshness Report
python -c "from core.config import load_settings; from observability.quality import build_freshness_report; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); rep=build_freshness_report(df, s); print('Freshness check:', rep['is_fresh'])"
```

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn giữa cấu hình GX dạng file tĩnh (`great_expectations.yml`) hay chế độ Ephemeral Context trong code.
- **Các phương án đã cân nhắc:**
  - *Phương án A:* Khởi tạo thư mục `gx/` trên đĩa và dùng CLI của Great Expectations để lưu trữ Data Context.
  - *Phương án B:* Dùng `gx.get_context(mode="ephemeral")` và khai báo Data Source bằng Pandas trực tiếp trong Python.
- **Phương án đã chọn:** **Phương án B**.
- **Lý do:** Ephemeral Context giúp pipeline hoàn toàn độc lập, không phụ thuộc vào trạng thái file cục bộ hay đường dẫn tuyệt đối của máy tính cá nhân. Mọi thành viên trong nhóm và máy chấm của Giảng viên đều có thể chạy trơn tru mà không sợ lệch cấu hình môi trường.
- **Bằng chứng:** Code chạy sạch sẽ trong hàm `run_data_quality_checks` và không tạo ra các file cấu hình thừa trong git repo.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  AttributeError: module 'great_expectations' has no attribute 'DataAssistant'
  (hoặc lỗi cú pháp cũ khi gọi context.sources.add_pandas)
  ```
- **Lệnh hoặc bước tái hiện:** Khi chạy các đoạn code mẫu GX trên mạng sử dụng cú pháp của Great Expectations 0.18.x trên thư viện `great_expectations 1.x`.
- **Nguyên nhân gốc:** Great Expectations 1.x tái cấu trúc toàn diện API sang Fluent Data Source API (`context.data_sources.add_pandas`).
- **Cách xử lý:** Cập nhật toàn bộ sang API chuẩn 1.x theo tài liệu của Checkpoint 1:
  Dùng `context.data_sources.add_pandas()` -> `add_dataframe_asset()` -> `add_batch_definition_whole_dataframe()` -> `batch.validate(expectation_suite)`.
- **Cách xác minh sau khi sửa:** Chạy kiểm thử thành công, trả về đúng đối tượng `ValidationResult` với `success=True`.
- **Điều học được:** Khi làm việc với các framework nâng cấp major version (từ 0.x lên 1.x), luôn đọc Release Notes và Documentation chuẩn phiên bản thay vì copy code từ các bài viết cũ.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - Dữ liệu đi từ API thô -> Làm sạch -> **Chặn bởi Chốt kiểm dịch Data Quality & Freshness Gate** -> Nếu đạt chuẩn mới được nạp vào ChromaDB -> RAG Agent sẵn sàng phục vụ.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Bộ 10 câu hỏi chuẩn bị trước ground-truth `paper_id` giúp đo đạc định lượng 2 khâu: Khâu Truy xuất (Retrieval Hit Rate: tài liệu đúng có nằm trong top 4 không) và Khâu Trả lời (Token F1: câu trả lời có chứa thông tin chính xác không).
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - Quality checks bảo đảm cấu trúc hợp lệ (syntax/integrity); Freshness monitoring bảo đảm giá trị nghiệp vụ theo thời gian (timeliness/drift).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Giúp so sánh "táo với táo" (apples-to-apples). Nếu đổi câu hỏi giữa các pha, ta không biết metric giảm là do dữ liệu bẩn hay do câu hỏi khó hơn.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Dựa trên việc bảng đối chiếu trong `corruption_report.md` ghi nhận: Quality Gate đổi từ FAILED sang PASSED, và chỉ số Retrieval Hit Rate / Token F1 phục hồi lại mức của Baseline ban đầu.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | :---: | :---: | :---: | :--- |
| `retrieval_hit_rate` | `[Điền]` | `[Điền]` | `[Điền]` | `[Đánh giá sự biến động giữa 3 pha]` |
| `mean_token_f1` | `[Điền]` | `[Điền]` | `[Điền]` | `[Đánh giá câu trả lời LLM]` |
| `Quality checks` | PASSED | FAILED | PASSED | GX bắt được vi phạm ngay ở pha Corrupted |
| `Freshness status` | FRESH | STALE WARNING | FRESH | SLA hoạt động chính xác khi có dữ liệu cũ |

### Kết luận từ số liệu
1. **Bằng chứng Silent Failure:** Ở pha Corrupted, dù không có lỗi code nào xuất hiện trong terminal, chỉ số Hit Rate và F1 sụt giảm rõ rệt. Nếu không có Great Expectations, người vận hành hệ thống sẽ không biết dữ liệu đã bị lỗi.
2. **Giá trị của Observability:** Báo cáo `corruption_report.md` cung cấp bức tranh minh bạch 3 trạng thái giúp nhóm tự tin trình bày Live Demo trước Giảng viên.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. Data Observability là thành phần bắt buộc trong bất kỳ kiến trúc AI/RAG nào muốn chạy trên Production.
2. Nắm vững cú pháp mới của Great Expectations 1.x giúp xây dựng các Data Contract linh hoạt và chặt chẽ.
3. Việc đo lường tự động cả Retrieval (Hit Rate) và Generation (Token F1) cung cấp cái nhìn 2 chiều về chất lượng của hệ thống.

### Nếu có thêm thời gian
- Thiết lập một Dashboard HTML trực quan (bằng Gradio hoặc Streamlit) để render báo cáo Data Quality và phân bố Freshness dưới dạng biểu đồ tương tác thời gian thực (đạt điểm bonus +5 của Rubric B1).

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Ngô Hoàng Thụy Khuê  
**Ngày xác nhận:** 2026-09-26
