# Phase 2: Data Corruption, Observability & Idempotent Repair Report

> **Generated:** 2026-09-26 05:19:36 UTC

---

## 1. Executive Summary

Báo cáo này đối chiếu toàn diện hệ thống RAG và Data Pipeline qua **3 trạng thái tiến hóa**:

1. **Baseline (Pha chuẩn):** Tập dữ liệu sạch nguyên bản từ Crossref API, vượt qua toàn bộ Data Quality Gate.
2. **Corrupted (Pha tiêm lỗi):** Giả lập sự cố sản xuất với 6 kịch bản làm bẩn dữ liệu. Dẫn đến hiện tượng **Silent Failure** — pipeline không sập nhưng chất lượng AI suy giảm rõ rệt và bị chặn bởi Data Observability Gate.
3. **Repaired (Pha phục hồi):** Tự động khôi phục an toàn (idempotent repair) từ snapshot thô ban đầu (`data/raw/crossref_records.json`), ghi đè dữ liệu lỗi và phục hồi 100% phong độ của hệ thống.

---

## 2. Bảng Đối Chiếu Hiệu Năng 3 Trạng Thái (Performance Comparison)

| Chỉ số (Metric) | Baseline (Chuẩn) | Corrupted (Bị lỗi) | Repaired (Phục hồi) | Trạng thái phục hồi |
| :--- | :---: | :---: | :---: | :--- |
| **Samples Evaluated** | `10` | `10` | `10` | Đồng nhất cùng tập test |
| **Retrieval Hit Rate** | `100.0%` | `90.0%` | `100.0%` | Phục hồi hoàn toàn (100%) |
| **Mean Token F1** | `1.0000` | `0.8692` | `1.0000` | Phục hồi hoàn toàn (1.0000) |
| **Judge Accuracy** | `100.0%` | `90.0%` | `100.0%` | Phục hồi hoàn toàn (100%) |
| **Mean Judge Score** | `5.00 / 5` | `4.40 / 5` | `5.00 / 5` | Phục hồi tối đa (5.00/5) |

> **Nhận xét hiệu năng:** Trong pha Corrupted, `retrieval_hit_rate` giảm xuống `90.0%` và `mean_token_f1` giảm xuống `0.8692`. Sau khi thực hiện repair idempotent từ raw snapshot, cả hai chỉ số đều bật ngược trở lại `100.0%` và `1.0000`, minh chứng khả năng tự phục hồi toàn vẹn.

---

## 3. Chốt Kiểm Soát Chất Lượng & Độ Tươi (Data Observability Gate)

| Tiêu chí kiểm soát | Baseline | Corrupted | Repaired | Đánh giá tác động |
| :--- | :---: | :---: | :---: | :--- |
| **Great Expectations Suite** | ✅ PASS | ❌ FAIL | ✅ PASS | Bắt được vi phạm unique ID và độ dài summary |
| **Freshness SLA (`is_fresh`)** | ✅ PASS | ❌ FAIL | ✅ PASS | Bắt được tỷ lệ bài báo cũ vượt ngưỡng 25% |
| **Overall Quality Gate** | ✅ PASS | ❌ FAIL | ✅ PASS | **Chặn dữ liệu bẩn** trước khi nạp Vector DB |
| **Tổng số bản ghi (Rows)** | `24` | `22` | `24` | Giảm do drop 20% bản ghi mới + nhân bản |
| **Tỷ lệ bài báo cũ (Stale ratio)** | `4.2%` | `40.9%` | `4.2%` | Tăng vọt lên 40.9% do lùi ngày 8 dòng |
| **Số dòng cũ / Tổng dòng** | `1/24` | `9/22` | `1/24` | Phục hồi về mức chuẩn sau repair |

---

## 4. Chi Tiết Kết Quả Kiểm Thử Great Expectations

| Expectation Check | Corrupted Result | Repaired Result | Chi tiết sai lệch ở pha Corrupted |
| :--- | :---: | :---: | :--- |
| `expect_table_row_count_to_be_between` | ✅ PASS | ✅ PASS | Đạt yêu cầu kiểm định |
| `expect_column_values_to_not_be_null` | ✅ PASS | ✅ PASS | Đạt yêu cầu kiểm định |
| `expect_column_values_to_be_unique` | ❌ FAIL | ✅ PASS | Phát hiện 4 dòng lỗi (18.2%) |
| `expect_column_values_to_not_be_null` | ✅ PASS | ✅ PASS | Đạt yêu cầu kiểm định |
| `expect_column_values_to_not_be_null` | ✅ PASS | ✅ PASS | Đạt yêu cầu kiểm định |
| `expect_column_value_lengths_to_be_between` | ❌ FAIL | ✅ PASS | Phát hiện 4 dòng lỗi (18.2%) |

---

## 5. Phân Tích Hiện Tượng Silent Failure & Cơ Chế Phục Hồi Idempotent

### Hiện tượng Silent Failure
1. **Bản chất vấn đề:** Khi dữ liệu bị nhiễm bẩn (xóa summary, chèn ký tự nhiễu, nhân bản ID, lùi ngày xuất bản), ChromaDB và RAG Pipeline **vẫn khởi chạy bình thường mà không báo lỗi runtime (không throw exception)**.
2. **Hậu quả ngầm:** Tuy code không sập, hiệu năng AI sụt giảm âm thầm: Retrieval Hit Rate giảm từ **100% xuống 90%**, Mean Token F1 tụt từ **1.0000 xuống 0.8692**. Người dùng cuối sẽ nhận được câu trả lời sai lệch mà kỹ sư không hề hay biết nếu thiếu hệ thống giám sát.
3. **Vai trò của Observability:** Great Expectations kết hợp Freshness SLA đóng vai trò chốt kiểm dịch nghiêm ngặt. Khi phát hiện dữ liệu bẩn, cổng kiểm soát lập tức bật cờ `success = False`, ngăn chặn việc nạp dữ liệu độc hại vào Vector Database.

### Cơ chế Idempotent Repair
1. **Nguyên lý thiết kế:** Hàm `repair_from_raw_snapshot()` không chắp vá trên dữ liệu đã hỏng. Thay vào đó, nó đọc lại snapshot thô nguyên bản (`data/raw/crossref_records.json` hoặc fallback `data/raw/crossref_response.json`).
2. **Tính tất định (Deterministic):** Bất kể dữ liệu trên đĩa bị làm bẩn bao nhiêu lần, việc tái thực thi quy trình làm sạch từ nguồn raw bất biến luôn sinh ra đúng 24 bản ghi chuẩn.
3. **Kết quả xác minh:** Hệ thống sau khi repair đã vượt qua 100% các chốt kiểm định chất lượng, tái lập lại chỉ số Hit Rate = 100% và Token F1 = 1.0000, đưa hệ thống trở lại trạng thái sản xuất an toàn.

---

*End of report.*