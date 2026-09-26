from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: str | Path | None = None) -> pd.DataFrame:
    """Giả lập 6 dạng sự cố dữ liệu thực tế và ghi lại nhật ký toàn bộ vào file log.

    6 kịch bản lỗi:
    1. Drop latest records: Bỏ rơi 20% các bài báo mới nhất.
    2. Blank summary: Xóa trắng phần tóm tắt ở một số dòng.
    3. Inject noise: Chèn các chuỗi ký tự rác vào tóm tắt.
    4. Truncate title: Cắt ngắn tiêu đề xuống dưới 8 ký tự.
    5. Stale date: Lùi ngày xuất bản về 365 ngày trước (vi phạm Freshness SLA > 25%).
    6. Duplicate rows: Nhân đôi các dòng để tạo trùng lặp paper_id.

    Các bước bổ sung:
    7. Rebuild lại trường `text_for_embedding` và `summary_chars` tương ứng.
    8. Ghi lại chi tiết toàn bộ các dòng bị biến đổi vào `output_log_path`.
    """
    if df.empty:
        return df.copy()

    # Tạo bản sao và sắp xếp theo ngày xuất bản giảm dần để xác định chuẩn bài mới nhất
    corrupted = df.copy()
    if "published" in corrupted.columns:
        corrupted = corrupted.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)

    corruption_records: list[dict[str, Any]] = []
    total_original = len(corrupted)

    # 1. Drop latest records: Bỏ rơi 20% các bài báo mới nhất (mất dữ liệu tươi)
    n_drop = max(1, int(total_original * 0.2))
    dropped_slice = corrupted.iloc[:n_drop]
    dropped_ids = dropped_slice["paper_id"].tolist()
    corrupted = corrupted.iloc[n_drop:].copy().reset_index(drop=True)

    corruption_records.append(
        {
            "scenario": "drop_latest",
            "name": "Drop latest records",
            "count": n_drop,
            "affected_paper_ids": dropped_ids,
            "description": f"Bỏ rơi {n_drop} bài báo mới nhất ({round(n_drop / total_original * 100, 1)}%) mô phỏng sự cố mất dữ liệu tươi",
        }
    )

    # 2. Blank summary: Xóa trắng phần tóm tắt ở 2 dòng đầu (lỗi cào dữ liệu rỗng)
    blank_indices = [0, 1] if len(corrupted) >= 2 else [0]
    blank_ids: list[str] = []
    for idx in blank_indices:
        blank_ids.append(str(corrupted.at[idx, "paper_id"]))
        corrupted.at[idx, "summary"] = ""
        corrupted.at[idx, "summary_chars"] = 0

    corruption_records.append(
        {
            "scenario": "blank_summary",
            "name": "Blank summary",
            "count": len(blank_ids),
            "affected_paper_ids": blank_ids,
            "description": f"Xóa trắng tóm tắt {len(blank_ids)} dòng mô phỏng lỗi cào dữ liệu rỗng (vi phạm ExpectColumnValueLengthsToBeBetween)",
        }
    )

    # 3. Inject noise: Chèn các chuỗi ký tự rác vào tóm tắt ở dòng 2 và 3
    noise_indices = [2, 3] if len(corrupted) >= 4 else []
    noise_ids: list[str] = []
    noise_pattern = "[CORRUPTED_DATA_NOISE_#$!@%^&*] "
    for idx in noise_indices:
        noise_ids.append(str(corrupted.at[idx, "paper_id"]))
        orig_summary = str(corrupted.at[idx, "summary"])
        corrupted.at[idx, "summary"] = f"{noise_pattern}{orig_summary} [ERROR: ENCODING_CORRUPTED_0xDEADBEEF]"
        corrupted.at[idx, "summary_chars"] = len(str(corrupted.at[idx, "summary"]))

    corruption_records.append(
        {
            "scenario": "inject_noise",
            "name": "Inject noise",
            "count": len(noise_ids),
            "affected_paper_ids": noise_ids,
            "noise_pattern": noise_pattern,
            "description": f"Chèn chuỗi ký tự rác vào tóm tắt của {len(noise_ids)} dòng mô phỏng nhiễu ký tự",
        }
    )

    # 4. Truncate title: Cắt ngắn tiêu đề xuống dưới 8 ký tự ở dòng 4 và 5
    truncate_indices = [4, 5] if len(corrupted) >= 6 else []
    truncated_details: list[dict[str, str]] = []
    for idx in truncate_indices:
        pid = str(corrupted.at[idx, "paper_id"])
        orig_title = str(corrupted.at[idx, "title"])
        trunc_title = orig_title[:6].strip() or "Paper"
        corrupted.at[idx, "title"] = trunc_title
        truncated_details.append(
            {
                "paper_id": pid,
                "original_title": orig_title,
                "truncated_title": trunc_title,
            }
        )

    corruption_records.append(
        {
            "scenario": "truncate_title",
            "name": "Truncate title",
            "count": len(truncated_details),
            "affected_paper_ids": [d["paper_id"] for d in truncated_details],
            "details": truncated_details,
            "description": f"Cắt ngắn tiêu đề {len(truncated_details)} bài báo xuống dưới 8 ký tự",
        }
    )

    # 5. Stale date: Lùi ngày xuất bản về 365 ngày trước (dòng 6 đến 13) để vi phạm Freshness SLA (> 25% bài cũ)
    stale_indices = [i for i in range(6, min(14, len(corrupted)))]
    stale_details: list[dict[str, str]] = []
    for idx in stale_indices:
        pid = str(corrupted.at[idx, "paper_id"])
        orig_pub = str(corrupted.at[idx, "published"])
        try:
            pub_date = datetime.strptime(orig_pub[:10], "%Y-%m-%d").date()
            new_pub_date = pub_date - timedelta(days=365)
            new_pub_str = new_pub_date.isoformat()
        except Exception:
            new_pub_str = "2024-01-01"

        corrupted.at[idx, "published"] = new_pub_str
        if "age_days" in corrupted.columns:
            corrupted.at[idx, "age_days"] = int(corrupted.at[idx, "age_days"]) + 365

        stale_details.append(
            {
                "paper_id": pid,
                "original_published": orig_pub,
                "corrupted_published": new_pub_str,
            }
        )

    corruption_records.append(
        {
            "scenario": "stale_date",
            "name": "Stale date",
            "count": len(stale_details),
            "affected_paper_ids": [d["paper_id"] for d in stale_details],
            "days_shifted": 365,
            "description": f"Lùi ngày xuất bản {len(stale_details)} dòng về 365 ngày trước để vi phạm Freshness SLA (> 25% bài cũ)",
        }
    )

    # 6. Duplicate rows: Nhân đôi 2 dòng đầu để tạo trùng lặp paper_id
    dup_indices = [0, 1] if len(corrupted) >= 2 else [0]
    duplicate_rows = corrupted.iloc[dup_indices].copy()
    duplicated_ids = [str(x) for x in duplicate_rows["paper_id"].tolist()]
    corrupted = pd.concat([corrupted, duplicate_rows], ignore_index=True)

    corruption_records.append(
        {
            "scenario": "duplicate_rows",
            "name": "Duplicate rows",
            "count": len(duplicated_ids),
            "affected_paper_ids": duplicated_ids,
            "description": f"Nhân đôi {len(duplicated_ids)} dòng tạo trùng lặp paper_id (vi phạm ExpectColumnValuesToBeUnique)",
        }
    )

    # 7. Rebuild `text_for_embedding` cho toàn bộ các dòng (bao gồm các dòng bị sửa và dòng duplicate)
    rebuilt_texts: list[str] = []
    for _, row in corrupted.iterrows():
        title = str(row.get("title", ""))
        authors = str(row.get("authors_joined", ""))
        published = str(row.get("published", ""))
        categories = str(row.get("categories_joined", ""))
        summary = str(row.get("summary", ""))
        rebuilt_texts.append(
            f"Title: {title}\n"
            f"Authors: {authors}\n"
            f"Published: {published}\n"
            f"Categories: {categories}\n"
            f"Summary: {summary}"
        )
    corrupted["text_for_embedding"] = rebuilt_texts

    # 8. Ghi log vào output_log_path nếu được chỉ định
    log_payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "total_original_rows": total_original,
        "total_corrupted_rows": len(corrupted),
        "corruption_scenarios": corruption_records,
        "summary": {
            "scenarios_applied": len(corruption_records),
            "original_rows": total_original,
            "corrupted_rows": len(corrupted),
            "dropped_rows": n_drop,
            "duplicated_rows": len(duplicated_ids),
        },
    }

    if output_log_path:
        write_json(Path(output_log_path), log_payload)

    return corrupted

