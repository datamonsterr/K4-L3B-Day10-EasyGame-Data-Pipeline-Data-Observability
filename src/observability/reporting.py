from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Generate a markdown report for the Phase 1 baseline pipeline run.

    Writes a human-readable .md file at `report_path` covering:
    - Run timestamp
    - Source summary (paper count, run date)
    - Data quality gate (Great Expectations results)
    - Freshness SLA
    - Retrieval and evaluation metrics
    - Ragas section (if present in metrics)
    """
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    # ------------------------------------------------------------------ #
    # Source summary
    # ------------------------------------------------------------------ #
    paper_count = source_summary.get("paper_count", "N/A")
    run_date = source_summary.get("run_date", "N/A")

    # ------------------------------------------------------------------ #
    # Data quality
    # ------------------------------------------------------------------ #
    gx_success = quality.get("gx_success", quality.get("success", "N/A"))
    overall_success = quality.get("success", "N/A")
    row_count = quality.get("row_count", paper_count)
    expectations = quality.get("expectations", [])

    # ------------------------------------------------------------------ #
    # Freshness SLA
    # ------------------------------------------------------------------ #
    is_fresh = freshness.get("is_fresh", "N/A")
    stale_ratio = freshness.get("stale_ratio", "N/A")
    stale_rows = freshness.get("stale_rows", "N/A")
    total_rows_fresh = freshness.get("total_rows", "N/A")
    threshold_days = freshness.get("freshness_threshold_days", "N/A")
    latest_published = freshness.get("latest_published", "N/A")
    oldest_published = freshness.get("oldest_published", "N/A")

    # ------------------------------------------------------------------ #
    # Retrieval / evaluation metrics
    # ------------------------------------------------------------------ #
    retrieval_hit_rate = metrics.get("retrieval_hit_rate", "N/A")
    mean_token_f1 = metrics.get("mean_token_f1", "N/A")
    judge_accuracy = metrics.get("judge_accuracy", "N/A")
    mean_judge_score = metrics.get("mean_judge_score", "N/A")
    samples = metrics.get("samples", "N/A")
    ragas = metrics.get("ragas", {})

    def pct(val) -> str:
        if isinstance(val, float):
            return f"{val:.1%}"
        return str(val)

    def fmt(val, decimals: int = 4) -> str:
        if isinstance(val, float):
            return f"{val:.{decimals}f}"
        return str(val)

    def bool_badge(val) -> str:
        if val is True:
            return "✅ PASS"
        if val is False:
            return "❌ FAIL"
        return str(val)

    lines: list[str] = [
        "# Phase 1 Baseline Pipeline Report",
        "",
        f"> **Generated:** {now}",
        "",
        "---",
        "",
        "## 1. Source Summary",
        "",
        f"| Field        | Value |",
        f"|--------------|-------|",
        f"| Paper count  | {paper_count} |",
        f"| Run date     | {run_date} |",
        "",
        "---",
        "",
        "## 2. Data Quality Gate (Great Expectations)",
        "",
        f"| Check               | Result |",
        f"|---------------------|--------|",
        f"| GX suite success    | {bool_badge(gx_success)} |",
        f"| Overall gate passed | {bool_badge(overall_success)} |",
        f"| Row count validated | {row_count} |",
        "",
    ]

    if expectations:
        lines += [
            "### Expectation Results",
            "",
            "| Expectation | Success | Details |",
            "|-------------|---------|---------|",
        ]
        for exp in expectations:
            exp_type = exp.get("expectation_type", "unknown")
            exp_success = bool_badge(exp.get("success", False))
            result_info = exp.get("result", {})
            detail = ""
            if "observed_value" in result_info:
                detail = f"observed: {result_info['observed_value']}"
            elif "element_count" in result_info:
                detail = f"elements: {result_info['element_count']}"
            lines.append(f"| `{exp_type}` | {exp_success} | {detail} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## 3. Freshness SLA",
        "",
        f"| Field                   | Value |",
        f"|-------------------------|-------|",
        f"| Is fresh                | {bool_badge(is_fresh)} |",
        f"| Stale ratio             | {pct(stale_ratio)} |",
        f"| Stale rows              | {stale_rows} / {total_rows_fresh} |",
        f"| Freshness threshold     | {threshold_days} days |",
        f"| Latest published        | {latest_published} |",
        f"| Oldest published        | {oldest_published} |",
        "",
        "---",
        "",
        "## 4. Retrieval & Evaluation Metrics",
        "",
        f"| Metric               | Value |",
        f"|----------------------|-------|",
        f"| Samples evaluated    | {samples} |",
        f"| Retrieval hit rate   | {pct(retrieval_hit_rate)} |",
        f"| Mean token F1        | {fmt(mean_token_f1)} |",
        f"| Judge accuracy       | {pct(judge_accuracy)} |",
        f"| Mean judge score     | {fmt(mean_judge_score, 2)} / 5 |",
        "",
    ]

    # ------------------------------------------------------------------ #
    # Ragas section
    # ------------------------------------------------------------------ #
    if ragas and not ragas.get("skipped") and not ragas.get("error"):
        lines += [
            "---",
            "",
            "## 5. Ragas Metrics",
            "",
            "| Metric | Score |",
            "|--------|-------|",
        ]
        for k, v in ragas.items():
            lines.append(f"| {k} | {fmt(v) if isinstance(v, float) else v} |")
        lines.append("")
    elif ragas.get("skipped"):
        lines += [
            "---",
            "",
            "## 5. Ragas Metrics",
            "",
            f"> ℹ️ {ragas['skipped']}",
            "",
        ]

    lines += [
        "---",
        "",
        "*End of report.*",
    ]

    Path(report_path).write_text("\n".join(lines), encoding="utf-8")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    raise NotImplementedError("Student task: implement corruption comparison report.")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    raise NotImplementedError("Student task: implement corruption comparison report.")
