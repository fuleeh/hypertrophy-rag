"""Tests for chunker."""

from hypertrophy_rag.ingestion.chunker import (
    extract_duration,
    extract_key_findings,
    extract_sample_size,
    chunk_paper,
)
from hypertrophy_rag.models import Paper


def _make_paper(abstract: str) -> Paper:
    return Paper(
        id="PMID:12345678",
        source="pubmed",
        title="Test Paper",
        authors="Author A, Author B",
        abstract=abstract,
        year=2023,
        journal="Test Journal",
    )


def test_extract_sample_size():
    assert extract_sample_size("We enrolled n = 42 participants") == "42"
    assert extract_sample_size("n=8 trained men") == "8"
    assert extract_sample_size("no sample size here") is None


def test_extract_duration():
    assert extract_duration("over 12 weeks") == "12 weeks"
    assert extract_duration("for 6 months") == "6 months"
    result = extract_duration("during a 8-week program")
    assert result is not None
    assert "8" in result and "week" in result
    assert extract_duration("no duration here") is None


def test_extract_key_findings():
    text = "Muscle thickness increased by 25% in the training group (p < 0.05). Strength improved from 100 to 150 kg."
    findings = extract_key_findings(text)
    assert len(findings) > 0
    # Should find percentage or p-value
    assert any("25%" in f or "p <" in f or "p=" in f.lower() for f in findings)


def test_chunk_paper_basic():
    abstract = " ".join(["This is sentence number {} about muscle hypertrophy and resistance training."] * 150)
    paper = _make_paper(abstract)
    chunks = chunk_paper(paper, min_abstract_words=100)
    assert len(chunks) >= 1
    assert chunks[0].paper.id == "PMID:12345678"
    assert chunks[0].id == "PMID:12345678_0"


def test_chunk_paper_short_abstract():
    paper = _make_paper("Too short.")
    chunks = chunk_paper(paper, min_abstract_words=100)
    assert len(chunks) == 0


def test_chunk_paper_long_splits():
    # Create an abstract with >500 words
    abstract = " ".join(["Word"] * 600)
    paper = _make_paper(abstract)
    chunks = chunk_paper(paper, min_abstract_words=100)
    assert len(chunks) >= 2  # Primary + at least one split
