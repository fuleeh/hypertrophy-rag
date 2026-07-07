"""Hybrid retrieval combining BM25 + semantic search with Reciprocal Rank Fusion."""

from __future__ import annotations

import re
import time

import chromadb
from rank_bm25 import BM25Okapi

from hypertrophy_rag.logging import get_logger

logger = get_logger("hybrid")


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenization for BM25."""
    return re.findall(r"\w+", text.lower())


class HybridRetriever:
    """BM25 + semantic hybrid retriever with Reciprocal Rank Fusion."""

    def __init__(
        self,
        persist_directory: str = "data/chroma",
        collection_name: str = "hypertrophy_papers",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._bm25_index: BM25Okapi | None = None
        self._bm25_docs: list[dict] = []
        self._bm25_corpus: list[list[str]] = []
        self._chroma_client = None
        self._collection = None

    def _load_chroma(self):
        """Load ChromaDB collection."""
        if self._collection is None:
            self._chroma_client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = self._chroma_client.get_collection(self.collection_name)
        return self._collection

    def _build_bm25_index(self):
        """Build BM25 index from ChromaDB documents."""
        if self._bm25_index is not None:
            return

        collection = self._load_chroma()
        all_docs = collection.get(include=["documents", "metadatas"])

        self._bm25_docs = []
        self._bm25_corpus = []

        for doc_id, doc_text, metadata in zip(
            all_docs["ids"], all_docs["documents"], all_docs["metadatas"]
        ):
            self._bm25_docs.append({
                "id": doc_id,
                "text": doc_text,
                "metadata": metadata,
            })
            self._bm25_corpus.append(_tokenize(doc_text))

        if self._bm25_corpus:
            self._bm25_index = BM25Okapi(self._bm25_corpus)
        else:
            self._bm25_index = BM25Okapi([])

        logger.info(f"BM25 index built with {len(self._bm25_docs)} documents")

    def bm25_search(self, query: str, top_k: int = 10) -> list[dict]:
        """Search using BM25 keyword matching."""
        self._build_bm25_index()

        if not self._bm25_index or not self._bm25_docs:
            return []

        query_tokens = _tokenize(query)
        scores = self._bm25_index.get_scores(query_tokens)

        # Get top-k indices sorted by score
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in ranked_indices:
            if scores[idx] > 0:
                results.append({
                    "id": self._bm25_docs[idx]["id"],
                    "text": self._bm25_docs[idx]["text"],
                    "metadata": self._bm25_docs[idx]["metadata"],
                    "bm25_score": float(scores[idx]),
                })

        return results

    def semantic_search(self, query: str, top_k: int = 10) -> list[dict]:
        """Search using ChromaDB semantic similarity."""
        collection = self._load_chroma()

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for doc_id, doc_text, metadata, distance in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                search_results.append({
                    "id": doc_id,
                    "text": doc_text,
                    "metadata": metadata,
                    "semantic_score": 1 - distance,  # Convert distance to similarity
                })

        return search_results

    def hybrid_search(
        self,
        query: str,
        top_k: int = 8,
        bm25_weight: float = 0.3,
        semantic_weight: float = 0.7,
    ) -> list[dict]:
        """Hybrid search combining BM25 and semantic with Reciprocal Rank Fusion."""
        t0 = time.perf_counter()

        # Get results from both methods
        bm25_results = self.bm25_search(query, top_k=top_k * 2)
        semantic_results = self.semantic_search(query, top_k=top_k * 2)

        # Normalize scores to 0-1 range
        def normalize_scores(results: list[dict], score_key: str) -> list[dict]:
            if not results:
                return results
            scores = [r[score_key] for r in results]
            max_score = max(scores) if scores else 1
            min_score = min(scores) if scores else 0
            score_range = max_score - min_score if max_score != min_score else 1
            for r in results:
                r[f"norm_{score_key}"] = (r[score_key] - min_score) / score_range
            return results

        bm25_results = normalize_scores(bm25_results, "bm25_score")
        semantic_results = normalize_scores(semantic_results, "semantic_score")

        # Build combined scores using Reciprocal Rank Fusion
        combined_scores: dict[str, float] = {}
        doc_data: dict[str, dict] = {}

        # BM25 scores
        for rank, result in enumerate(bm25_results):
            doc_id = result["id"]
            rrf_score = bm25_weight * (1 / (60 + rank))  # k=60 for RRF
            combined_scores[doc_id] = combined_scores.get(doc_id, 0) + rrf_score
            doc_data[doc_id] = result

        # Semantic scores
        for rank, result in enumerate(semantic_results):
            doc_id = result["id"]
            rrf_score = semantic_weight * (1 / (60 + rank))
            combined_scores[doc_id] = combined_scores.get(doc_id, 0) + rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = result

        # Sort by combined score and return top-k
        ranked_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)[:top_k]

        results = []
        for doc_id in ranked_ids:
            result = doc_data[doc_id].copy()
            result["hybrid_score"] = combined_scores[doc_id]
            results.append(result)

        total_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "Hybrid search completed",
            extra={"extra_data": {
                "query": query[:100],
                "bm25_results": len(bm25_results),
                "semantic_results": len(semantic_results),
                "combined_results": len(results),
                "total_ms": round(total_ms, 2),
            }},
        )

        return results


def hybrid_query(
    question: str,
    top_k: int = 8,
    persist_directory: str = "data/chroma",
    collection_name: str = "hypertrophy_papers",
) -> list[dict]:
    """Run a hybrid search and return results."""
    retriever = HybridRetriever(persist_directory=persist_directory, collection_name=collection_name)
    return retriever.hybrid_search(question, top_k=top_k)
