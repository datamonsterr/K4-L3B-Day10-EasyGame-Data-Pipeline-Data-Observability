# Phase 1 Baseline Pipeline Report

> **Generated:** 2026-09-26 04:35:58 UTC

---

## 1. Source Summary

| Field        | Value |
|--------------|-------|
| Paper count  | 24 |
| Run date     | 2026-09-26 |

---

## 2. Data Quality Gate (Great Expectations)

| Check               | Result |
|---------------------|--------|
| GX suite success    | ✅ PASS |
| Overall gate passed | ✅ PASS |
| Row count validated | 24 |

### Expectation Results

| Expectation | Success | Details |
|-------------|---------|---------|
| `expect_table_row_count_to_be_between` | ✅ PASS | observed: 24 |
| `expect_column_values_to_not_be_null` | ✅ PASS | elements: 24 |
| `expect_column_values_to_be_unique` | ✅ PASS | elements: 24 |
| `expect_column_values_to_not_be_null` | ✅ PASS | elements: 24 |
| `expect_column_values_to_not_be_null` | ✅ PASS | elements: 24 |
| `expect_column_value_lengths_to_be_between` | ✅ PASS | elements: 24 |

---

## 3. Freshness SLA

| Field                   | Value |
|-------------------------|-------|
| Is fresh                | ✅ PASS |
| Stale ratio             | 4.2% |
| Stale rows              | 1 / 24 |
| Freshness threshold     | 180 days |
| Latest published        | 2026-07-22 |
| Oldest published        | 2026-03-28 |

---

## 4. Retrieval & Evaluation Metrics

| Metric               | Value |
|----------------------|-------|
| Samples evaluated    | 10 |
| Retrieval hit rate   | 100.0% |
| Mean token F1        | 1.0000 |
| Judge accuracy       | 100.0% |
| Mean judge score     | 5 / 5 |

---

## 5. Ragas Metrics

> ℹ️ Set RUN_RAGAS=1 to enable the slower Ragas pass.

---

*End of report.*