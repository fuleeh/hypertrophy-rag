"""Core protocols and abstractions for the Hypertrophy RAG system.

These protocols define the contracts that all implementations must satisfy,
enabling dependency inversion and open/closed principle compliance.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Retriever(Protocol):
    """Protocol for retrieving relevant documents given a query."""

    def search(
        self,
        query: str,
        top_k: int = 10,
        year_filter: int | None = None,
        source_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for relevant documents.

        Returns a list of dicts with at least 'text' and 'metadata' keys.
        """
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for generating text from messages."""

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> str:
        """Generate a response from a list of messages.

        Returns the generated text content.
        """
        ...


@runtime_checkable
class Embedder(Protocol):
    """Protocol for converting text to embeddings."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        ...
