from __future__ import annotations

import logging
from datetime import UTC, datetime

from core.config import load_settings
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Baseline pipeline end-to-end (Phase 1).

    Steps:
    1. Load settings.
    2. Load or fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Run data quality checks.
    6. Build Chroma index.
    7. Build evaluation test set.
    8. Evaluate pipeline.
    9. Generate markdown report.
    10. Print summary to console.
    """
    # 1. Settings
    settings = load_settings()
    run_date = datetime.now(UTC)

    print("=" * 60)
    print("Phase 1 Baseline Pipeline")
    print(f"Run date: {run_date.date()}")
    print("=" * 60)

    # 2. Load or fetch raw records
    if settings.paths.raw_records_json.exists() and not settings.refresh_source:
        logger.info("Loading raw records from %s", settings.paths.raw_records_json)
        raw_records = load_raw_records(settings.paths.raw_records_json)
    else:
        logger.info("Fetching records from Crossref API...")
        raw_records = fetch_source_records(settings)

    print(f"[1/7] Raw records loaded: {len(raw_records)}")

    # 3. Clean data
    df = build_clean_dataframe(raw_records, run_date)
    print(f"[2/7] Cleaned dataframe: {len(df)} rows")

    # 4. Save clean CSV/JSON
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.clean_json.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False)
    df.to_json(settings.paths.clean_json, orient="records", indent=2, force_ascii=False)
    print(f"[3/7] Saved clean data → {settings.paths.clean_csv}")

    # 5. Run data quality checks (GX + freshness SLA)
    logger.info("Running data quality checks...")
    quality_result = run_data_quality_checks(df, settings, "baseline")
    freshness_info = quality_result.get("freshness", {})
    gx_ok = quality_result.get("gx_success", False)
    fresh_ok = quality_result.get("is_fresh", False)
    print(
        f"[4/7] Quality gate: GX={'PASS' if gx_ok else 'FAIL'}, "
        f"Fresh={'PASS' if fresh_ok else 'FAIL'}"
    )

    # 6. Build Chroma index
    logger.info("Building embedding index...")
    settings.paths.chroma_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.embeddings_json.parent.mkdir(parents=True, exist_ok=True)
    index = LocalEmbeddingIndex.build(df, settings)
    print(f"[5/7] Index built ({len(index.documents)} docs) → {settings.paths.chroma_dir}")

    # 7. Build evaluation test set
    settings.paths.eval_testset.parent.mkdir(parents=True, exist_ok=True)
    if settings.paths.eval_testset.exists() and not settings.refresh_test_set:
        logger.info("Test set already exists at %s, skipping rebuild.", settings.paths.eval_testset)
    else:
        build_test_set(df, settings.paths.eval_testset)
    print(f"[6/7] Test set ready → {settings.paths.eval_testset}")

    # 8. Evaluate pipeline
    settings.paths.baseline_metrics.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.baseline_answers.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Evaluating pipeline...")
    bundle = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    print(f"[7/7] Evaluation complete → {settings.paths.baseline_metrics}")

    # 9. Generate markdown report
    source_summary = {"paper_count": len(df), "run_date": str(run_date.date())}
    settings.paths.baseline_report.parent.mkdir(parents=True, exist_ok=True)
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality_result,
        freshness=freshness_info,
    )
    print(f"\nReport written → {settings.paths.baseline_report}")

    # 10. Print summary
    s = bundle.summary
    print("\n--- Phase 1 Summary ---")
    print(f"  Papers:              {len(df)}")
    print(f"  GX quality:          {'PASS' if gx_ok else 'FAIL'}")
    print(f"  Freshness SLA:       {'PASS' if fresh_ok else 'FAIL'}")
    print(f"  Retrieval hit rate:  {s.get('retrieval_hit_rate', 0):.1%}")
    print(f"  Mean token F1:       {s.get('mean_token_f1', 0):.4f}")
    print(f"  Judge accuracy:      {s.get('judge_accuracy', 0):.1%}")
    print(f"  Mean judge score:    {s.get('mean_judge_score', 0):.2f} / 5")
    print("-" * 40)

