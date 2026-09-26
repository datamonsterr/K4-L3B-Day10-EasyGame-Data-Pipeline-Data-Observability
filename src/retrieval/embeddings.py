from __future__ import annotations

import os
from functools import lru_cache

from google import genai
from langchain_core.embeddings import Embeddings


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY")
    return genai.Client(api_key=api_key)


class GeminiEmbeddings(Embeddings):
    """Embeddings backed by Google Gemini Embedding 2 (models/gemini-embedding-2).

    The google-genai SDK's embed_content treats a list of strings as a single
    multi-turn content rather than a batch, so we call once per text and collect.
    """

    def __init__(self, model_name: str = "models/gemini-embedding-2"):
        self.model_name = model_name
        self._client = _get_client()

    def _embed_one(self, text: str) -> list[float]:
        result = self._client.models.embed_content(
            model=self.model_name,
            contents=text,
        )
        return result.embeddings[0].values

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)
