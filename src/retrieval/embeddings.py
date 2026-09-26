from __future__ import annotations

import os
from functools import lru_cache

import google.generativeai as genai
from langchain_core.embeddings import Embeddings


@lru_cache(maxsize=4)
def _get_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY")
    return genai.Client(api_key=api_key)


class GeminiEmbeddings(Embeddings):
    """Embeddings backed by Google's text-embedding-004 (Gemini Embedding 2) model."""

    def __init__(self, model_name: str = "models/text-embedding-004"):
        self.model_name = model_name
        self._client = _get_client()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        result = self._client.models.embed_content(
            model=self.model_name,
            contents=texts,
        )
        return [e.values for e in result.embeddings]

    def embed_query(self, text: str) -> list[float]:
        result = self._client.models.embed_content(
            model=self.model_name,
            contents=[text],
        )
        return result.embeddings[0].values
