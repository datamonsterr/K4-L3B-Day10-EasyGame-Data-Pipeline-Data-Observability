from __future__ import annotations
import great_expectations as gx
from typing import Any

import pandas as pd

from core.config import Settings


# def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
#     """TODO(student): tao bo data quality checks.

#     Pseudo-code:
#     1. Check row count.
#     2. Check `paper_id` not null va unique.
#     3. Check `title` not null.
#     4. Check do dai `summary`.
#     5. Check freshness bang `age_days`.
#     6. Ghi ket qua vao `data/quality/`.
#     """
#     context = gx.get_context(mode="ephemeral")
#     data_source = context.data_sources.add_pandas(name="papers_source")
#     data_asset = data_source.add_dataframe_asset(name="papers_asset")
#     batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
#     batch = batch_def.get_batch(batch_parameters={"dataframe": df})


#     # raise NotImplementedError("Student task: implement quality checks.")


# def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
#     """TODO(student): tong hop freshness report.

#     Pseudo-code:
#     1. Tim latest va oldest published date.
#     2. Dem so dong stale.
#     3. Tao payload:
#        - latest_published
#        - oldest_published
#        - stale_rows
#        - total_rows
#        - is_fresh
#     4. Ghi JSON report.
#     """
    # raise NotImplementedError("Student task: implement freshness reporting.")


from pathlib import Path
from typing import Any
 
import great_expectations as gx
import pandas as pd
 
from core.config import Settings
from core.utils import write_json
 
# --- 4 hang rao Expectations bat buoc (theo de bai) -----------------------
REQUIRED_NOT_NULL_COLUMNS: tuple[str, ...] = ("paper_id", "title", "text_for_embedding")
UNIQUE_ID_COLUMN = "paper_id"
SUMMARY_COLUMN = "summary"
 
MIN_ROW_COUNT = 5
MAX_ROW_COUNT = 5000
MIN_SUMMARY_LENGTH = 30
MAX_SUMMARY_LENGTH = 20_000
 
# --- Freshness SLA ----------------------------------------------------------
STALE_RATIO_THRESHOLD = 0.25  # > 25% bai bao cu -> is_fresh = False
 
 
def _get_validation_batch(df: pd.DataFrame):
    """Tao Ephemeral Context + Batch theo chuan Great Expectations 1.x."""
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    return batch_def.get_batch(batch_parameters={"dataframe": df})
 
 
def _build_expectation_suite() -> gx.ExpectationSuite:
    """Dinh nghia 4 Expectations thiet yeu cho chot kiem soat du lieu."""
    suite = gx.ExpectationSuite(name="papers_quality_suite")
 
    # 1. So luong ban ghi nam trong nguong [5, 5000]
    suite.add_expectation(
        gx.expectations.ExpectTableRowCountToBeBetween(
            min_value=MIN_ROW_COUNT, max_value=MAX_ROW_COUNT
        )
    )
 
    # 2. Cac cot quan trong khong duoc rong (null)
    for column in REQUIRED_NOT_NULL_COLUMNS:
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column=column))
 
    # 3. paper_id la duy nhat, khong trung lap
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column=UNIQUE_ID_COLUMN))
 
    # 4. summary co do dai toi thieu 30 ky tu
    suite.add_expectation(
        gx.expectations.ExpectColumnValueLengthsToBeBetween(
            column=SUMMARY_COLUMN, min_value=MIN_SUMMARY_LENGTH, max_value=MAX_SUMMARY_LENGTH
        )
    )
 
    return suite
 
 
def _serialize_expectation_result(result: Any) -> dict[str, Any]:
    kwargs = dict(result.expectation_config.kwargs)
    kwargs.pop("batch_id", None)
    return {
        "expectation_type": result.expectation_config.type,
        "success": bool(result.success),
        "kwargs": kwargs,
        "result": dict(result.result),
    }
 
 
def evaluate_freshness_sla(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    """Do luong ty le bai bao cu (`age_days > freshness_threshold_days`).
 
    Neu ty le bai bao cu vuot qua 25% (`STALE_RATIO_THRESHOLD`), he thong lap
    tuc gan co canh bao `is_fresh = False`.
    """
    threshold_days = settings.freshness_threshold_days
    total_rows = int(len(df))
 
    if total_rows == 0 or "age_days" not in df.columns:
        return {
            "total_rows": total_rows,
            "stale_rows": 0,
            "stale_ratio": 0.0,
            "freshness_threshold_days": threshold_days,
            "stale_ratio_threshold": STALE_RATIO_THRESHOLD,
            "is_fresh": True,
            "latest_published": None,
            "oldest_published": None,
        }
 
    age_days = pd.to_numeric(df["age_days"], errors="coerce")
    stale_mask = age_days > threshold_days
    stale_rows = int(stale_mask.fillna(False).sum())
    stale_ratio = stale_rows / total_rows
    is_fresh = stale_ratio <= STALE_RATIO_THRESHOLD
 
    latest_published: str | None = None
    oldest_published: str | None = None
    if "published" in df.columns:
        published_sorted = df["published"].dropna().sort_values()
        if not published_sorted.empty:
            oldest_published = str(published_sorted.iloc[0])
            latest_published = str(published_sorted.iloc[-1])
 
    return {
        "total_rows": total_rows,
        "stale_rows": stale_rows,
        "stale_ratio": round(stale_ratio, 4),
        "freshness_threshold_days": threshold_days,
        "stale_ratio_threshold": STALE_RATIO_THRESHOLD,
        "is_fresh": bool(is_fresh),
        "latest_published": latest_published,
        "oldest_published": oldest_published,
    }
 
 
def _resolve_quality_report_path(settings: Settings, stage: str) -> Path:
    stage_key = (stage or "").strip().lower()
    if stage_key == "baseline":
        return settings.paths.baseline_quality_report
    if stage_key == "corrupted":
        return settings.paths.corrupted_quality_report
    return settings.paths.quality_dir / f"{stage_key or 'report'}_quality_report.json"
 
 
def run_data_quality_checks(df: pd.DataFrame, settings: Settings, stage: str) -> dict[str, Any]:
    """Chot kiem soat chat luong du lieu (Observability Gate) truoc khi index.
 
    Su dung Ephemeral Context chuan Great Expectations 1.x de kiem dinh 4
    Expectations bat buoc, ket hop `evaluate_freshness_sla()` de giam sat do
    tuoi moi. Ket qua duoc ghi ra `data/quality/` va tra ve dict chua it nhat
    `{"success": bool}`.
    """
    batch = _get_validation_batch(df)
    suite = _build_expectation_suite()
    validation_result = batch.validate(suite)
 
    expectation_results = [_serialize_expectation_result(result) for result in validation_result.results]
    gx_success = bool(validation_result.success)
 
    freshness = evaluate_freshness_sla(df, settings)
 
    # Chot kiem soat chi cho phep du lieu di tiep khi ca GX suite lan
    # Freshness SLA deu dat, dung voi yeu cau "vuot qua chot kiem dinh
    # nghiem ngat truoc khi dua vao Vector Database".
    overall_success = gx_success and freshness["is_fresh"]
 
    report: dict[str, Any] = {
        "stage": stage,
        "row_count": int(len(df)),
        "gx_success": gx_success,
        "is_fresh": freshness["is_fresh"],
        "success": overall_success,
        "expectations": expectation_results,
        "freshness": freshness,
    }
 
    report_path = _resolve_quality_report_path(settings, stage)
    write_json(report_path, report)
 
    return report
 
 
def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Xuat rieng freshness report (dung lai `evaluate_freshness_sla`)."""
    freshness = evaluate_freshness_sla(df, settings)
    write_json(Path(report_path), freshness)
    return freshness
