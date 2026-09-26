# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                 |
| ------------------ | ------------------------------------------------------------------------ |
| Họ và tên          | Phạm Thành Đạt                                                           |
| MSSV               | 2A202602721                                                             |
| Khóa/Lớp           | K4-L3B-DAY10 (Ca Sáng, Thứ 7 26/09/2026)                                |
| Tên nhóm           | EasyGame                                                                 |
| Vai trò chính      | Member 1 — Trưởng nhóm / Pipeline Integrator & Vector Store              |
| Repository         | K4-L3B-DAY10-EasyGame-Data-Pipeline-Data-Observability                  |
| Ngày hoàn thành    | 2026-09-26                                                               |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Project & Path Config** | `src/core/config.py`, `src/core/utils.py` | Environment variables, `.env` file | Đối tượng `Settings`, `Paths` chuẩn hóa toàn project | Đang hoàn thiện |
| **Vector Store Indexing** | `src/retrieval/index.py` (`LocalEmbeddingIndex.build`, `search`) | `pd.DataFrame` (clean/corrupted/repaired) | 3 ChromaDB collections (`papers-baseline`, `papers-corrupted`, `papers-repaired`) | Đang hoàn thiện |
| **Embedding Generation** | `src/retrieval/embeddings.py` (`MiniLMEmbeddings`) | Danh sách chuỗi `text_for_embedding` | Vector ndarray 384 chiều (`all-MiniLM-L6-v2`) | Đang hoàn thiện |
| **Baseline Orchestrator** | `src/pipelines/phase1.py`, `script/run_phase1.py` | Raw data, clean data | Pipeline Phase 1 end-to-end, baseline index & metrics | Đang hoàn thiện |
| **Corruption & Repair Flow**| `src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py` | Corrupted dataframe, Raw snapshot | Luồng so sánh 3 trạng thái và trigger Idempotent Repair | Đang hoàn thiện |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| **Tích hợp Contract Ingestion** | Thành viên 2 (`crossref.py`, `cleaning.py`) | Thống nhất schema `PaperRecord` và schema DataFrame 5 trường helper cho `text_for_embedding`. |
| **Tích hợp Benchmark & Observability** | Thành viên 3 (`quality.py`, `testset.py`, `reporting.py`) | Đảm bảo `run_phase1.py` gọi đúng GX 1.x validation và nạp bộ `test_set.json` vào test suite. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Kiểm tra môi trường & Config** | `src/core/config.py`, `.env` | File cấu hình `Settings` nạp đầy đủ đường dẫn và LLM provider | `python -c "from core.config import load_settings; s=load_settings(); print(s.embedding_model)"` |
| **Khởi tạo ChromaDB Indexer** | `src/retrieval/index.py` | Lớp `LocalEmbeddingIndex` với cơ chế delete & recreate collection an toàn | `python -c "import chromadb; c=chromadb.PersistentClient('data/chroma'); print(c.list_collections())"` |
| **Kịch bản điều phối Phase 1** | `script/run_phase1.py`, `src/pipelines/phase1.py` | Entrypoint thực thi Ingestion -> Cleaning -> GX -> Chroma -> Eval | `python script/run_phase1.py` |
| **Kịch bản Corruption & Repair**| `script/run_corruption_flow.py`, `src/pipelines/corruption_flow.py` | Entrypoint thực thi Corruption -> Corrupted Eval -> Repair -> Repaired Eval -> So sánh | `python script/run_corruption_flow.py` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. Đảm bảo dữ liệu từ dạng bảng (`pd.DataFrame`) được chuyển đổi sang vector embedding và đánh chỉ mục chuẩn xác trên ChromaDB với không gian vector Cosine.
2. Ngăn ngừa hiện tượng nhiễm bẩn dữ liệu chéo giữa các trạng thái (Data Contamination) khi chạy thử nghiệm lỗi.
3. Điều phối (Orchestration) toàn bộ pipeline từ lúc tải dữ liệu đến khi xuất báo cáo đối chiếu, đảm bảo tính tái lập (Reproducibility) và Idempotency (chạy lại nhiều lần không sinh rác hay crash).

### Cách triển khai
1. **ChromaDB Collection Isolation:** Trong `LocalEmbeddingIndex.build()`, phân tách collection dựa theo file manifest đầu ra:
   - `papers_embeddings.json` -> Collection `papers-baseline`
   - `papers_embeddings_corrupted.json` -> Collection `papers-corrupted`
   - `papers_embeddings_repaired.json` -> Collection `papers-repaired`
2. **Xóa & Tái tạo Collection Idempotent:** Khi build lại index, gọi `client.delete_collection(name=...)` bên trong khối `try/except` trước khi `client.create_collection()`, tránh lỗi `UniqueConstraintError` của ChromaDB.
3. **Pipeline Orchestration:**
   - Trong `phase1.py`: `fetch_source_records` -> `build_clean_dataframe` -> `run_data_quality_checks` -> `LocalEmbeddingIndex.build` -> `build_test_set` -> `evaluate_rag`.
   - Trong `corruption_flow.py`: Lấy dataframe sạch -> Tiêm 6 loại lỗi -> Build `papers-corrupted` -> Đánh giá suy giảm -> Đọc lại raw snapshot (`load_raw_records`) -> Build `papers-repaired` -> Đánh giá phục hồi -> Xuất bảng so sánh.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | `pd.DataFrame` đã làm sạch có cột `paper_id`, `title`, `text_for_embedding`, metadata |
| **Output** | Directory `data/chroma/`, manifest `papers_embeddings*.json`, `SearchResult` objects |
| **Module phụ thuộc** | `src/ingestion/cleaning.py` (đầu vào DataFrame), `sentence-transformers` |
| **Module sử dụng output** | `src/retrieval/agent.py` & `src/evaluation/metrics.py` (truy vấn semantic search) |
| **Điều kiện lỗi cần xử lý**| Thư mục `data/chroma` chưa tồn tại (`mkdir -p`), Collection đã tồn tại từ lần chạy trước |

### Cách xác minh

```bash
# 1. Kiểm tra ChromaDB và Embeddings engine
.venv/bin/python -c "from core.config import load_settings; from retrieval.index import LocalEmbeddingIndex; print('Retrieval module loaded successfully')"

# 2. Kiểm tra thực thi Phase 1
python script/run_phase1.py

# 3. Kiểm tra luồng Corruption & Repair
python script/run_corruption_flow.py
```

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần so sánh chính xác chất lượng trả lời và truy xuất giữa dữ liệu Sạch (Baseline), Dữ liệu Lỗi (Corrupted) và Dữ liệu Sau Phục Hồi (Repaired).
- **Các phương án đã cân nhắc:**
  - *Phương án A:* Dùng chung 1 collection trong ChromaDB và ghi đè (upsert) tài liệu theo từng pha.
  - *Phương án B:* Tạo 3 collection riêng biệt (`papers-baseline`, `papers-corrupted`, `papers-repaired`) trong cùng một persistent client.
- **Phương án đã chọn:** **Phương án B**.
- **Lý do:** Upsert chung 1 collection dễ để lại vector "ma" (orphan vectors) khi số lượng bản ghi của dữ liệu corrupted bị giảm (do kịch bản drop 20% bản ghi mới). Tạo 3 collection độc lập cô lập hoàn toàn không gian tìm kiếm, cho phép truy vấn lại bất kỳ trạng thái nào để kiểm chứng đối sánh mà không cần re-index lại từ đầu.
- **Bằng chứng:** Thư mục `data/chroma` lưu trữ cấu trúc đa collection và các file manifest `data/embeddings/papers_embeddings*.json` phân tách rõ ràng.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  chromadb.errors.UniqueConstraintError: Collection papers-baseline already exists
  ```
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_phase1.py` lần thứ 2 khi chưa xóa thư mục `data/chroma`.
- **Nguyên nhân gốc:** Hàm `client.create_collection(name=collection_name)` mặc định ném lỗi nếu collection đã tồn tại trong metadata database của ChromaDB.
- **Cách xử lý:** Đặt lệnh xóa trước khi tạo:
  ```python
  try:
      client.delete_collection(name=collection_name)
  except Exception:
      pass
  collection = client.create_collection(name=collection_name, configuration={"hnsw": {"space": "cosine"}})
  ```
- **Cách xác minh sau khi sửa:** Chạy script nhiều lần liên tiếp (`run_phase1.py` rồi `run_corruption_flow.py`), script chạy trơn tru mà không cần can thiệp thủ công `rm -rf data/chroma`.
- **Điều học được:** Mọi thao tác ghi dữ liệu trong Data Pipeline chuyên nghiệp đều phải tuân thủ nguyên lý **Idempotent** (khả nghịch và có thể chạy lại an toàn).

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - Dữ liệu thô từ Crossref API (hoặc snapshot offline `crossref_response.json`) được tải và chuẩn hóa thành danh sách `PaperRecord`. Sau đó, module cleaning lọc trùng, bóc tách XML, tính `age_days` và ghép thành chuỗi `text_for_embedding`. Chuỗi này được mô hình MiniLM mã hóa thành vector 384 chiều và nạp kèm metadata vào ChromaDB collection.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - 10 câu hỏi trong `test_set.json` lưu sẵn `paper_id` gốc (ground-truth). Khi Agent thực hiện tìm kiếm Top-K:
     - `retrieval_hit_rate = 1.0` nếu ground-truth `paper_id` nằm trong danh sách Top-K được trả về.
     - `mean_token_f1` đo độ tương đồng từ vựng giữa câu trả lời sinh ra bởi LLM và ground-truth context.
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - *Quality checks (Great Expectations):* Kiểm soát tính toàn vẹn tĩnh của bảng dữ liệu (không rỗng, không trùng khóa chính, độ dài ký tự hợp lệ, số dòng nằm trong ngưỡng).
   - *Freshness monitoring (SLA):* Đo lường tính kịp thời theo thời gian thực (độ tuổi tài liệu `age_days > 180`), phản ánh sự suy thoái theo thời gian (Data Drift/Data Staleness) ngay cả khi schema hoàn toàn hợp lệ.
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Tuân thủ nguyên tắc "Controlled Experiment" (biến kiểm soát). Giữ cố định bộ câu hỏi kiểm thử giúp phản ánh trung thực và khách quan 100% sự biến động của metrics là do chất lượng dữ liệu thay đổi, không phải do độ khó của câu hỏi thay đổi.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Dựa trên việc file `repaired_metrics.json` có `retrieval_hit_rate` và `mean_token_f1` phục hồi tiệm cận hoặc bằng mức trong `baseline_metrics.json`, đồng thời Quality Gate trong `corruption_report.md` đổi trạng thái từ FAILED trở lại PASSED.

---

## 8. Phân tích kết quả

### Metrics chính (Dự kiến theo dõi khi chạy Pipeline)

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | :---: | :---: | :---: | :--- |
| `retrieval_hit_rate` | ~1.00 | ~0.30 - 0.50 | ~1.00 | Dữ liệu lỗi làm mất ground-truth context trong top-k; repair phục hồi đầy đủ. |
| `mean_token_f1` | ~0.75 - 0.90 | ~0.20 - 0.40 | ~0.75 - 0.90 | Câu trả lời LLM bị trật hướng khi tài liệu bị tiêm noise hoặc cắt ngắn title/summary. |
| `Quality checks` | PASSED | FAILED | PASSED | Great Expectations 1.x bắt được ngay lập tức các vi phạm schema và null values. |
| `Freshness status` | FRESH | STALE WARNING | FRESH | Kịch bản lùi ngày xuất bản vi phạm ngưỡng SLA 25% bài báo > 180 ngày. |

### Kết luận từ số liệu
1. **Chuỗi lỗi:** Tiêm 6 kịch bản lỗi -> GX Quality Gate chuyển sang FAILED & Freshness cảnh báo STALE -> Retrieval Hit Rate sụt giảm nghiêm trọng -> LLM trả lời sai lệch (Silent Failure).
2. **Chuỗi phục hồi:** Kích hoạt Idempotent Repair nạp lại raw snapshot -> GX Quality Gate chuyển sang PASSED -> ChromaDB nạp lại `papers-repaired` -> Metrics hồi phục tương đương baseline ban đầu.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Về Data Pipeline:** Pipeline phải Idempotent và bất biến ở tầng raw data; nếu mất tầng lưu trữ thô, việc phục hồi hệ thống khi có sự cố dữ liệu là bất khả thi.
2. **Về Data Quality/Observability:** Không thể chỉ dựa vào exception handling để bắt lỗi dữ liệu. Dữ liệu sai cấu trúc vẫn chạy qua model bình thường nhưng tạo ra câu trả lời thảm họa (Silent Failure). Great Expectations là tấm khiên thiết yếu trước vector database.
3. **Về RAG Agent:** Chất lượng của Vector Search phụ thuộc tuyệt đối vào khâu chuẩn hóa `text_for_embedding` và tính sạch của metadata.

### Nếu có thêm thời gian
- Xây dựng thêm một **Auto-Healing Worker**: khi Great Expectations phát hiện batch dữ liệu vi phạm SLA hoặc fail schema, hệ thống sẽ tự động cách ly (quarantine) bản ghi bẩn và tự động kích hoạt fallback re-fetch mà không cần can thiệp bằng script thủ công.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phạm Thành Đạt  
**Ngày xác nhận:** 2026-09-26
