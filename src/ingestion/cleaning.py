from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord

CLEAN_COLUMNS: tuple[str, ...] = (
    "paper_id",
    "title",
    "summary",
    "summary_chars",
    "authors_joined",
    "categories_joined",
    "primary_category",
    "published",
    "updated",
    "abs_url",
    "pdf_url",
    "comment",
    "age_days",
    "text_for_embedding",
)


def build_text_for_embedding(
    title: str, authors_joined: str, categories_joined: str, published: str, summary: str
) -> str:
    """Ghep text_for_embedding theo cau truc 5 phan: Title/Authors/Categories/Published/Summary."""
    return "\n".join(
        [
            f"Title: {title}",
            f"Authors: {authors_joined or 'Unknown'}",
            f"Categories: {categories_joined or 'Uncategorized'}",
            f"Published: {published or 'Unknown'}",
            f"Summary: {summary}",
        ]
    )


def _parse_published_date(published: str, fallback: datetime) -> datetime.date:
    if published:
        try:
            return datetime.fromisoformat(published).date()
        except ValueError:
            pass
    return fallback.date()


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw PaperRecord list thanh dataframe san sang de embed.

    - Normalize title/summary/authors/categories (khoang trang thua).
    - Khu trung lap theo `paper_id`.
    - Tinh `age_days = (run_date - published).days`.
    - Sinh `authors_joined`, `categories_joined`, `summary_chars`,
      `text_for_embedding` (cau truc 5 phan).
    - Bo cac row thieu title/summary/paper_id.
    """
    if not records:
        return pd.DataFrame(columns=CLEAN_COLUMNS)

    rows: list[dict] = []
    seen_paper_ids: set[str] = set()

    for record in records:
        paper_id = normalize_whitespace(record.paper_id)
        title = normalize_whitespace(record.title)
        summary = normalize_whitespace(record.summary)

        if not paper_id or not title or not summary:
            continue
        if paper_id in seen_paper_ids:
            continue
        seen_paper_ids.add(paper_id)

        authors = [normalize_whitespace(a) for a in record.authors if normalize_whitespace(a)]
        categories = [normalize_whitespace(c) for c in record.categories if normalize_whitespace(c)]
        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)
        primary_category = normalize_whitespace(record.primary_category) or (
            categories[0] if categories else "Uncategorized"
        )

        published = normalize_whitespace(record.published)
        updated = normalize_whitespace(record.updated) or published

        published_date = _parse_published_date(published, run_date)
        if not published:
            published = published_date.isoformat()
        age_days = max(0, (run_date.date() - published_date).days)

        text_for_embedding = build_text_for_embedding(
            title=title,
            authors_joined=authors_joined,
            categories_joined=categories_joined,
            published=published,
            summary=summary,
        )

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "summary_chars": len(summary),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "abs_url": normalize_whitespace(record.abs_url),
                "pdf_url": normalize_whitespace(record.pdf_url),
                "comment": normalize_whitespace(record.comment),
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows, columns=list(CLEAN_COLUMNS))
    if df.empty:
        return df

    df = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df