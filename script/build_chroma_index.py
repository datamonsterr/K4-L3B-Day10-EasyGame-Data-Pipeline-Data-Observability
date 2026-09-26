"""Build the ChromaDB baseline index (papers-baseline) from clean data.

Usage (run from main repo root):
    PYTHONPATH=.worktrees/feat-chroma-index/src \
        python .worktrees/feat-chroma-index/script/build_chroma_index.py [--root /path/to/repo]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ChromaDB baseline index.")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root directory (defaults to the main repo resolved from cwd or script location).",
    )
    args = parser.parse_args()

    # Resolve project root: prefer --root, then fall back to cwd so the script
    # works when run from the main repo root as documented.
    project_dir: Path | None = args.root
    if project_dir is None:
        cwd = Path.cwd()
        # If cwd looks like the main repo (has data/clean/), use it.
        if (cwd / "data" / "clean" / "papers_clean.json").exists():
            project_dir = cwd

    settings = load_settings(project_dir=project_dir)

    df = pd.read_json(settings.paths.clean_json)
    index = LocalEmbeddingIndex.build(df, settings)

    count = index.collection.count()
    print(f"ChromaDB index built: {count} docs in collection '{index.collection_name}'")


if __name__ == "__main__":
    main()
