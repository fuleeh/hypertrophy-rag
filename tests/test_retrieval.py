"""Tests for retrieval utilities: context building, prompts."""

from __future__ import annotations

from hypertrophy_rag.retrieval.context import build_context, metadata_to_studies, results_to_studies
from hypertrophy_rag.retrieval.prompts import AGENT_SYSTEM_PROMPT, RAG_SYSTEM_PROMPT

# --- build_context ---


def test_build_context_empty():
    assert build_context([]) == ""


def test_build_context_deduplicates_by_paper_id():
    results = [
        {"text": "abstract one", "metadata": {"paper_id": "PMID:123", "paper_title": "Study A"}},
        {"text": "abstract one dup", "metadata": {"paper_id": "PMID:123", "paper_title": "Study A"}},
        {"text": "abstract two", "metadata": {"paper_id": "PMID:456", "paper_title": "Study B"}},
    ]
    ctx = build_context(results)
    assert "Study A" in ctx
    assert "Study B" in ctx
    assert ctx.count("Study A") == 1


def test_build_context_includes_metadata():
    results = [
        {
            "text": "The abstract text",
            "metadata": {
                "paper_title": "My Study",
                "paper_authors": "Smith et al",
                "paper_year": 2024,
                "paper_journal": "J Strength",
                "paper_pmid": "999",
                "paper_doi": "10.1234/test",
                "paper_citation_count": 42,
                "sample_size": "n=30",
                "duration": "12 weeks",
                "key_findings": "gain|loss",
            },
        }
    ]
    ctx = build_context(results)
    assert "My Study" in ctx
    assert "Smith et al" in ctx
    assert "2024" in ctx
    assert "999" in ctx
    assert "n=30" in ctx


# --- results_to_studies ---


def test_results_to_studies_empty():
    assert results_to_studies([]) == []


def test_results_to_studies_deduplicates_by_title():
    results = [
        {"text": "abs", "metadata": {"paper_title": "Same", "paper_year": 2024}},
        {"text": "abs", "metadata": {"paper_title": "Same", "paper_year": 2024}},
    ]
    studies = results_to_studies(results)
    assert len(studies) == 1


def test_results_to_studies_maps_s2_id():
    results = [
        {"text": "abs", "metadata": {"paper_title": "T", "paper_id": "S2:abc123"}},
    ]
    studies = results_to_studies(results)
    assert studies[0].s2_id == "S2:abc123"


def test_results_to_studies_splits_findings():
    results = [
        {"text": "abs", "metadata": {"paper_title": "T", "key_findings": "finding1|finding2|finding3"}},
    ]
    studies = results_to_studies(results)
    assert studies[0].key_findings == ["finding1", "finding2", "finding3"]


# --- metadata_to_studies ---


def test_metadata_to_studies_empty():
    assert metadata_to_studies([]) == []


def test_metadata_to_studies_deduplicates():
    metas = [
        {"title": "X", "year": 2024},
        {"title": "X", "year": 2024},
    ]
    studies = metadata_to_studies(metas)
    assert len(studies) == 1


def test_metadata_to_studies_maps_pmid():
    metas = [{"title": "T", "pmid": "12345"}]
    studies = metadata_to_studies(metas)
    assert studies[0].pmid == "12345"


# --- prompts ---


def test_prompts_are_nonempty_strings():
    assert isinstance(RAG_SYSTEM_PROMPT, str) and len(RAG_SYSTEM_PROMPT) > 50
    assert isinstance(AGENT_SYSTEM_PROMPT, str) and len(AGENT_SYSTEM_PROMPT) > 50
