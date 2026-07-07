"""ChromaDB vector index with Groq embeddings."""

from __future__ import annotations

import chromadb
from rich.console import Console

from hypertrophy_rag.models import Chunk

console = Console()


class VectorDB:
    """ChromaDB wrapper for the hypertrophy paper index.

    Satisfies the Retriever protocol — can be passed to query_rag().
    """

    def __init__(
        self,
        collection_name: str = "hypertrophy_papers",
        persist_directory: str = "data/chroma",
    ):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def index_chunks(self, chunks: list[Chunk], batch_size: int = 100) -> int:
        """Index chunks into ChromaDB. Returns number of chunks indexed."""
        total = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            ids = [c.id for c in batch]
            documents = [c.text for c in batch]
            metadatas = [c.to_dict() for c in batch]

            # ChromaDB handles embedding internally with default model
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            total += len(batch)

        return total

    def search(
        self,
        query: str,
        top_k: int = 10,
        year_filter: int | None = None,
        source_filter: str | None = None,
    ) -> list[dict]:
        """Search the vector index. Returns list of results with metadata."""
        where_filter = {}
        if year_filter:
            where_filter["paper_year"] = {"$gte": year_filter}
        if source_filter:
            where_filter["source"] = source_filter

        query_params = {
            "query_texts": [query],
            "n_results": top_k,
        }
        if where_filter:
            query_params["where"] = where_filter

        results = self.collection.query(**query_params)

        formatted = []
        if results and results["ids"] and results["ids"][0]:
            for idx in range(len(results["ids"][0])):
                meta = results["metadatas"][0][idx] if results["metadatas"] else {}
                distance = results["distances"][0][idx] if results["distances"] else None
                formatted.append({
                    "id": results["ids"][0][idx],
                    "text": results["documents"][0][idx] if results["documents"] else "",
                    "metadata": meta,
                    "distance": distance,
                })

        return formatted

    def get_stats(self) -> dict:
        """Get index statistics."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection.name,
        }

    def delete_all(self) -> None:
        """Delete all data from the collection."""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"},
        )
