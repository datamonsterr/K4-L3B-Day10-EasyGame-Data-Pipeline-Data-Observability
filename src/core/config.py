from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Paths:
    project_dir: Path
    workspace_dir: Path
    raw_api_response: Path
    raw_records_json: Path
    clean_csv: Path
    clean_json: Path
    chroma_dir: Path
    embeddings_json: Path
    corrupted_clean_csv: Path
    corrupted_clean_json: Path
    corrupted_embeddings_json: Path
    repaired_clean_csv: Path
    repaired_clean_json: Path
    repaired_embeddings_json: Path
    eval_testset: Path
    baseline_metrics: Path
    baseline_answers: Path
    demo_answers: Path
    quality_dir: Path
    gx_dir: Path
    baseline_quality_report: Path
    corrupted_quality_report: Path
    freshness_report: Path
    baseline_report: Path
    corruption_log: Path
    corrupted_metrics: Path
    corrupted_answers: Path
    repaired_metrics: Path
    repaired_answers: Path
    comparison_report: Path


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    model_name: str
    google_api_key: str | None
    openai_api_key: str | None
    anthropic_api_key: str | None
    openrouter_api_key: str | None
    openrouter_base_url: str
    ollama_base_url: str
    custom_llm_api_key: str | None
    custom_llm_base_url: str | None
    embedding_model: str
    baseline_collection_name: str
    corrupted_collection_name: str
    repaired_collection_name: str
    source_api: str
    source_query: str
    source_filter: str
    max_results: int
    top_k: int
    freshness_threshold_days: int
    refresh_source: bool
    refresh_test_set: bool
    paths: Paths


def load_settings(project_dir: Path | None = None) -> Settings:
    root = (project_dir or Path(__file__).resolve().parents[2]).resolve()
    workspace = root.parent
    freshness_threshold_days = 180
    source_from_date = (datetime.now(UTC).date() - timedelta(days=freshness_threshold_days)).isoformat()

    load_dotenv(workspace / ".env")
    load_dotenv(root / ".env", override=False)

    data_dir = root / "data"
    paths = Paths(
        project_dir=root,
        workspace_dir=workspace,
        raw_api_response=data_dir / "raw" / "crossref_response.json",
        raw_records_json=data_dir / "raw" / "crossref_records.json",
        clean_csv=data_dir / "clean" / "papers_clean.csv",
        clean_json=data_dir / "clean" / "papers_clean.json",
        chroma_dir=data_dir / "chroma",
        embeddings_json=data_dir / "embeddings" / "papers_embeddings.json",
        corrupted_clean_csv=data_dir / "clean" / "papers_clean_corrupted.csv",
        corrupted_clean_json=data_dir / "clean" / "papers_clean_corrupted.json",
        corrupted_embeddings_json=data_dir / "embeddings" / "papers_embeddings_corrupted.json",
        repaired_clean_csv=data_dir / "clean" / "papers_clean_repaired.csv",
        repaired_clean_json=data_dir / "clean" / "papers_clean_repaired.json",
        repaired_embeddings_json=data_dir / "embeddings" / "papers_embeddings_repaired.json",
        eval_testset=data_dir / "eval" / "test_set.json",
        baseline_metrics=data_dir / "results" / "baseline_metrics.json",
        baseline_answers=data_dir / "results" / "baseline_answers.json",
        demo_answers=data_dir / "results" / "agent_demo_answers.json",
        quality_dir=data_dir / "quality",
        gx_dir=data_dir / "quality" / "gx",
        baseline_quality_report=data_dir / "quality" / "baseline_quality_report.json",
        corrupted_quality_report=data_dir / "quality" / "corrupted_quality_report.json",
        freshness_report=data_dir / "quality" / "freshness_report.json",
        baseline_report=data_dir / "reports" / "phase1_report.md",
        corruption_log=data_dir / "results" / "corruption_log.json",
        corrupted_metrics=data_dir / "results" / "corrupted_metrics.json",
        corrupted_answers=data_dir / "results" / "corrupted_answers.json",
        repaired_metrics=data_dir / "results" / "repaired_metrics.json",
        repaired_answers=data_dir / "results" / "repaired_answers.json",
        comparison_report=data_dir / "reports" / "corruption_report.md",
    )

    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
        model_name=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        custom_llm_api_key=os.getenv("CUSTOM_LLM_API_KEY"),
        custom_llm_base_url=os.getenv("CUSTOM_LLM_BASE_URL"),
        embedding_model="models/text-embedding-004",
        baseline_collection_name="papers-baseline",
        corrupted_collection_name="papers-corrupted",
        repaired_collection_name="papers-repaired",
        source_api="Crossref REST API",
        source_query="agentic retrieval augmented generation large language model",
        source_filter=f"from-pub-date:{source_from_date},has-abstract:true",
        max_results=24,
        top_k=4,
        freshness_threshold_days=freshness_threshold_days,
        refresh_source=os.getenv("REFRESH_SOURCE", "").lower() in {"1", "true", "yes"},
        refresh_test_set=os.getenv("REFRESH_TEST_SET", "").lower() in {"1", "true", "yes"},
        paths=paths,
    )


def normalized_provider(settings: Settings) -> str:
    provider = settings.llm_provider.strip().lower().replace(" ", "").replace("-", "")
    if provider == "anthorpic":
        return "anthropic"
    if provider == "customllm":
        return "custom"
    return provider


def require_llm_credentials(settings: Settings) -> None:
    provider = normalized_provider(settings)
    if provider == "gemini":
        if settings.google_api_key:
            return
        raise RuntimeError("GOOGLE_API_KEY is required when LLM_PROVIDER=gemini.")
    if provider == "openai":
        if settings.openai_api_key:
            return
        raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
    if provider == "anthropic":
        if settings.anthropic_api_key:
            return
        raise RuntimeError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic.")
    if provider == "openrouter":
        if settings.openrouter_api_key:
            return
        raise RuntimeError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter.")
    if provider in {"mock", "ollama"}:
        return
    if provider == "custom":
        if settings.custom_llm_base_url:
            return
        raise RuntimeError("CUSTOM_LLM_BASE_URL is required when LLM_PROVIDER=custom.")
    raise RuntimeError(
        "Unsupported LLM_PROVIDER. Expected one of: openai, gemini, anthropic, openrouter, ollama, custom, mock."
    )
