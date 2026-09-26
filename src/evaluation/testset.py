from pathlib import Path
from typing import Any
 
import pandas as pd
 
from core.utils import first_sentence, normalize_whitespace, write_json
 
# 4 dang cau hoi bat buoc, phan bo deu tren 10 cau hoi cua bo test set.
QUESTION_TYPES: tuple[str, ...] = ("summary", "authors", "date", "categories")
TEST_SET_SIZE = 10
MIN_REQUIRED_ROWS = 1
 
 
def _select_sample_rows(df: pd.DataFrame, count: int) -> pd.DataFrame:
    """Chon `count` bai bao dai dien, trai deu qua toan bo dataframe."""
    sorted_df = df.sort_values("paper_id").reset_index(drop=True)
    total_rows = len(sorted_df)
    # Trai deu chi so tren toan bo dataframe (khong random) de dam bao
    # tinh tai lap (reproducible) giua cac lan chay.
    positions = [(i * total_rows) // count for i in range(count)]
    return sorted_df.iloc[positions].reset_index(drop=True)
 
 
def _build_question(question_type: str, row: pd.Series) -> tuple[str, str]:
    """Tra ve (question, ground_truth) cho mot `question_type` + mot hang du lieu."""
    title = normalize_whitespace(str(row["title"]))
 
    if question_type == "summary":
        question = f"What is the summary of the paper '{title}'?"
        ground_truth = first_sentence(str(row["summary"]))
    elif question_type == "authors":
        question = f"Who authored the paper '{title}'?"
        ground_truth = normalize_whitespace(str(row["authors_joined"]))
    elif question_type == "date":
        question = f"When was the paper '{title}' published?"
        ground_truth = normalize_whitespace(str(row["published"]))
    elif question_type == "categories":
        question = f"What categories does the paper '{title}' belong to?"
        ground_truth = normalize_whitespace(str(row["categories_joined"]))
    else:  # pragma: no cover - defensive guard
        raise ValueError(f"Unsupported question_type: {question_type}")
 
    return question, ground_truth
 
 
def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tao bo Benchmark Test Set (Ground Truth) tu cleaned dataframe.
 
    Sinh `TEST_SET_SIZE` (10) cau hoi, phan bo deu qua 4 dang bai toan:
    summary / authors / date / categories. Ket qua duoc ghi ra `output_path`
    (JSON) va cung duoc tra ve duoi dang list[dict].
    """
    if len(df) < MIN_REQUIRED_ROWS:
        raise ValueError(
            f"Not enough documents to build a test set: need at least {MIN_REQUIRED_ROWS}, got {len(df)}."
        )
 
    required_columns = {"paper_id", "title", "summary", "authors_joined", "published", "categories_joined"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Cleaned dataframe is missing required columns: {sorted(missing_columns)}")
 
    sample_rows = _select_sample_rows(df, TEST_SET_SIZE)
 
    test_set: list[dict[str, Any]] = []
    for i in range(TEST_SET_SIZE):
        row = sample_rows.iloc[i % len(sample_rows)]
        question_type = QUESTION_TYPES[i % len(QUESTION_TYPES)]
        question, ground_truth = _build_question(question_type, row)
 
        test_set.append(
            {
                "id": f"eval_{i + 1:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [str(row["paper_id"])],
            }
        )
 
    write_json(Path(output_path), test_set)
    return test_set
 

# from __future__ import annotations

# from typing import Any

# import pandas as pd
# from observability.quality import run_data_quality_checks

# def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
#    """TODO(student): tao bo evaluation set tu cleaned dataframe.

#    Pseudo-code:
#    1. Kiem tra so luong document toi thieu.
#    2. Chon mot so paper dai dien.
#    3. Tao nhieu loai cau hoi:
#       - summary
#       - authors
#       - date
#       - categories
#    4. Moi row can co:
#       - id
#       - question_type
#       - question
#       - ground_truth
#       - ground_truth_doc_ids
#    5. Ghi file JSON vao output_path.
#    """

#    quality = run_data_quality_checks(df, settings=None, report_name="test_set_quality_report")

#    return {
#       "id": "eval_001",
#       "question_type": "summary",
#       "question": "What is the summary of the paper '<Title>'?",
#       "ground_truth": "<Nội dung câu đầu tóm tắt chuẩn>",
#       "ground_truth_doc_ids": ["<DOI bài báo>"]
#    }
#    #  raise NotImplementedError("Student task: implement test set builder.")
