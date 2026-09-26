from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import html
import logging
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(text: str) -> str:
    """Loại bỏ thẻ XML/HTML (như <jats:p>) và chuẩn hóa khoảng trắng."""
    no_html = re.sub(r"<[^>]+>", " ", text)
    unescaped = html.unescape(no_html)
    return normalize_whitespace(unescaped)


def _extract_date(item: dict[str, Any]) -> str:
    """Trích xuất ngày tháng ISO YYYY-MM-DD từ item Crossref."""
    for date_field in ["published", "published-print", "published-online", "issued", "created"]:
        val = item.get(date_field)
        if isinstance(val, dict):
            date_parts = val.get("date-parts")
            if date_parts and isinstance(date_parts, list) and len(date_parts) > 0:
                parts = date_parts[0]
                if len(parts) >= 3:
                    return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                if len(parts) == 2:
                    return f"{int(parts[0]):04d}-{int(parts[1]):02d}-01"
                if len(parts) == 1:
                    return f"{int(parts[0]):04d}-01-01"
            dt_str = val.get("date-time")
            if dt_str and isinstance(dt_str, str):
                return dt_str[:10]
        elif isinstance(val, str) and val.strip():
            return val.strip()[:10]
    return datetime.now(UTC).date().isoformat()


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thành danh sách PaperRecord đã được chuẩn hóa.

    Chuẩn hóa các trường:
    - paper_id: DOI
    - title: tên bài báo
    - summary: tóm tắt loại bỏ thẻ HTML/XML rác như <jats:p>
    - authors: danh sách tác giả
    - categories: danh sách thể loại / chủ đề
    - primary_category: thể loại chính
    - published / updated: ngày công bố
    - abs_url / pdf_url: liên kết tài liệu
    - comment: ghi chú record
    """
    message = payload.get("message", {})
    if isinstance(message, dict):
        items = message.get("items", [])
    elif isinstance(payload.get("items"), list):
        items = payload["items"]
    else:
        items = []

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        doi = str(item.get("DOI", "")).strip()
        if not doi:
            continue

        title_val = item.get("title", "")
        if isinstance(title_val, list):
            raw_title = title_val[0] if title_val else ""
        else:
            raw_title = str(title_val)
        title = _clean_text(raw_title)
        if not title:
            continue

        abstract_val = item.get("abstract", "") or ""
        summary = _clean_text(str(abstract_val))

        authors: list[str] = []
        for author in item.get("author", []):
            if isinstance(author, dict):
                given = str(author.get("given", "")).strip()
                family = str(author.get("family", "")).strip()
                name = f"{given} {family}".strip() if (given or family) else str(author.get("name", "")).strip()
                if name:
                    authors.append(name)
            elif isinstance(author, str) and author.strip():
                authors.append(author.strip())

        raw_cats = item.get("subject", []) or item.get("categories", [])
        if isinstance(raw_cats, str):
            raw_cats = [raw_cats]
        categories = [normalize_whitespace(str(cat)) for cat in raw_cats if str(cat).strip()]
        primary_category = categories[0] if categories else "General"

        pub_date = _extract_date(item)
        updated_date = pub_date

        url = str(item.get("URL") or f"https://doi.org/{doi}").strip()

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=pub_date,
                updated=updated_date,
                abs_url=url,
                pdf_url=url,
                comment=f"Crossref record {doi}",
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Gọi Crossref REST API, lưu raw response, parse thành records và lưu records.

    Hỗ trợ cơ chế retry cho các mã lỗi 429/503/500 và fallback sang snapshot local
    `data/raw/crossref_response.json` khi mất mạng hoặc dính rate limit.
    """
    payload: dict[str, Any] | None = None
    api_url = "https://api.crossref.org/works"

    if settings.refresh_source or not settings.paths.raw_api_response.exists():
        params = {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
        }
        headers = {
            "User-Agent": "DataObservabilityLab/1.0 (mailto:lab@example.com)",
        }

        max_retries = 3
        backoff_seconds = 2.0
        for attempt in range(1, max_retries + 1):
            try:
                logger.info("Calling Crossref API (attempt %s/%s)...", attempt, max_retries)
                response = requests.get(api_url, params=params, headers=headers, timeout=20)
                if response.status_code == 200:
                    payload = response.json()
                    write_json(settings.paths.raw_api_response, payload)
                    logger.info("Successfully fetched and saved raw response from Crossref API.")
                    break
                if response.status_code in {429, 500, 502, 503, 504}:
                    logger.warning("Received status %s from Crossref API. Retrying in %ss...", response.status_code, backoff_seconds)
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                response.raise_for_status()
            except requests.RequestException as exc:
                logger.warning("Request error on attempt %s: %s", attempt, exc)
                if attempt < max_retries:
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                else:
                    logger.error("Failed to fetch from Crossref API after %s attempts.", max_retries)

    if payload is None:
        if settings.paths.raw_api_response.exists():
            logger.info("Using local raw response snapshot from %s", settings.paths.raw_api_response)
            payload = read_json(settings.paths.raw_api_response)
        else:
            raise RuntimeError(
                f"Failed to fetch data from Crossref API and no local snapshot found at {settings.paths.raw_api_response}"
            )

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    logger.info("Saved %s standardized records to %s", len(records), settings.paths.raw_records_json)
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Đọc JSON snapshot và map thành danh sách `PaperRecord`."""
    data = read_json(path)
    if isinstance(data, list):
        return [PaperRecord(**item) for item in data]
    if isinstance(data, dict):
        return parse_crossref_payload(data)
    raise ValueError(f"Unsupported payload format in {path}")

