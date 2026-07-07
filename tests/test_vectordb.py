"""Tests for vector DB."""

import tempfile
from pathlib import Path

from hypertrophy_rag.index.vectordb import VectorDB
from hypertrophy_rag.models import Chunk, Paper


def _make_chunk(chunk_id: str = "test_0", text: str = "muscle hypertrophy training") -> Paper:
    paper = Paper(
        id="PMID:12345678",
        source="pubmed",
        title="Test Paper",
        authors="Author A",
        abstract=text,
        year=2023,
        journal="Test Journal",
    )
    return Chunk(id=chunk_id, text=text, paper=paper)


def test_vectordb_index_and_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = VectorDB(collection_name="test", persist_directory=tmpdir)
        chunks = [_make_chunk(f"test_{i}", f"muscle hypertrophy training volume set {i}") for i in range(5)]
        indexed = db.index_chunks(chunks)
        assert indexed == 5

        results = db.search("hypertrophy", top_k=3)
        assert len(results) > 0
        assert len(results) <= 3


def test_vectordb_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = VectorDB(collection_name="test_stats", persist_directory=tmpdir)
        stats = db.get_stats()
        assert stats["total_chunks"] == 0

        chunks = [_make_chunk("s1", "test document")]
        db.index_chunks(chunks)
        stats = db.get_stats()
        assert stats["total_chunks"] == 1


def test_vectordb_delete_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = VectorDB(collection_name="test_delete", persist_directory=tmpdir)
        db.index_chunks([_make_chunk("d1", "test")])
        assert db.get_stats()["total_chunks"] == 1

        db.delete_all()
        assert db.get_stats()["total_chunks"] == 0
