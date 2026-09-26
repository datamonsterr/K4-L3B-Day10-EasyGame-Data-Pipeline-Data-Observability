# from __future__ import annotations


# def main() -> None:
#     """TODO(student): xay dung corruption -> evaluate -> repair -> compare flow.

#     Pseudo-code:
#     1. Load baseline metrics va clean dataset.
#     2. Tao corrupted dataframe.
#     3. Save corrupted artifacts.
#     4. Rebuild index va evaluate.
#     5. Run quality checks/freshness tren corrupted data.
#     6. Repair lai tu raw records.
#     7. Evaluate repaired dataset.
#     8. Tao comparison report.
#     """
    
#     # raise NotImplementedError("Student task: implement corruption flow pipeline.")

from __future__ import annotations
from typing import Any
import pandas as pd

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.corruption import corrupt_clean_dataframe, repair_from_raw_snapshot
from observability.quality import run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex

COMPARISON_METRIC_KEYS: tuple[str, ...] = (
    "samples",
    "retrieval_hit_rate",
    "mean_token_f1",
    "judge_accuracy",
    "mean_judge_score",
)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return "n/a" if value is None else str(value)


def _print_comparison_table(baseline: dict, corrupted: dict, repaired: dict) -> None:
    columns = ["Metric", "Baseline", "Corrupted", "Repaired"]
    widths = [22, 14, 14, 14]
    header = "".join(col.ljust(w) for col, w in zip(columns, widths))
    print(header)
    print("-" * len(header))
    for key in COMPARISON_METRIC_KEYS:
        row = [key, _fmt(baseline.get(key)), _fmt(corrupted.get(key)), _fmt(repaired.get(key))]
        print("".join(str(cell).ljust(w) for cell, w in zip(row, widths)))
    print()
    print(
        f"Data Quality Gate -> Corrupted success={corrupted.get('quality_success')} "
        f"| Repaired success={repaired.get('quality_success')}"
    )


def run_corruption_flow_pipeline(settings: Settings) -> dict[str, Any]:
    """Phase 2: Do luong suy giam, phuc hoi du lieu & doi chieu 3 trang thai.

    1. Nap du lieu sach + baseline metrics tu Phase 1, tiem 6 kich ban
       Synthetic Data Corruption, index lai vao ChromaDB (`papers-corrupted`)
       va tai danh gia RAG de quan sat hien tuong Silent Failure.
    2. Kich hoat `repair_from_raw_snapshot()` de phuc hoi an toan (idempotent)
       du lieu tu snapshot raw ban dau, ghi de len du lieu hong, index lai vao
       ChromaDB (`papers-repaired`) va tai danh gia.
    3. Chay lai Data Quality Gate + Freshness SLA tren ca 2 trang thai va xuat
       bang / bao cao doi chieu 3 trang thai Baseline vs Corrupted vs Repaired
       ra `data/reports/corruption_report.md`.
    """
    run_date = now_utc()

    # --- 0. Nap baseline artifacts da sinh boi Phase 1 ----------------------
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_df = pd.read_json(settings.paths.clean_json)

    # --- 1. Corrupt -> index -> evaluate (quan sat Silent Failure) ---------
    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))

    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, embeddings_output_path=settings.paths.corrupted_embeddings_json
    )
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")

    # --- 2. Idempotent repair tu raw snapshot -> index -> evaluate ----------
    repaired_df = repair_from_raw_snapshot(settings, run_date=run_date)

    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, embeddings_output_path=settings.paths.repaired_embeddings_json
    )
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")

    # --- 3. Bao cao doi chieu 3 trang thai -----------------------------------
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_quality["freshness"],
        repaired_freshness=repaired_quality["freshness"],
    )

    result = {
        "baseline_metrics": baseline_metrics,
        "corrupted_metrics": corrupted_bundle.summary,
        "repaired_metrics": repaired_bundle.summary,
        "corrupted_quality": corrupted_quality,
        "repaired_quality": repaired_quality,
    }

    _print_comparison_table(
        baseline_metrics,
        {**corrupted_bundle.summary, "quality_success": corrupted_quality["success"]},
        {**repaired_bundle.summary, "quality_success": repaired_quality["success"]},
    )
    print(f"\nBao cao doi chieu 3 trang thai da duoc ghi vao: {settings.paths.comparison_report}")

    return result


def main() -> None:
    settings = load_settings()
    run_corruption_flow_pipeline(settings)


if __name__ == "__main__":
    main()