"""Context building and response parsing utilities.

Extracted from rag.py / langchain_rag.py / agent.py to eliminate
triplicated logic (Single Responsibility + Open/Closed).
"""

from __future__ import annotations

from typing import Any

from hypertrophy_rag.models import StudySummary


def build_context(results: list[dict[str, Any]]) -> str:
    """Build an LLM-ready context string from retrieval results.

    Each result must have 'text' and 'metadata' keys.
    Deduplicates by paper ID.
    """
    context_parts = []
    papers_seen: set[str] = set()

    for r in results:
        meta = r["metadata"]
        paper_id = meta.get("paper_id", meta.get("paper_pmid", "unknown"))
        if paper_id in papers_seen:
            continue
        papers_seen.add(paper_id)

        context_parts.append(
            f"Study: {meta.get('paper_title', 'Unknown')}\n"
            f"Authors: {meta.get('paper_authors', 'Unknown')}\n"
            f"Year: {meta.get('paper_year', 'Unknown')}\n"
            f"Journal: {meta.get('paper_journal', 'Unknown')}\n"
            f"PMID: {meta.get('paper_pmid', 'N/A')}\n"
            f"DOI: {meta.get('paper_doi', 'N/A')}\n"
            f"Citation count: {meta.get('paper_citation_count', 'N/A')}\n"
            f"Sample size: {meta.get('sample_size', 'Unknown')}\n"
            f"Duration: {meta.get('duration', 'Unknown')}\n"
            f"Abstract: {r['text']}\n"
            f"Key findings: {meta.get('key_findings', 'None extracted')}\n"
        )

    return "\n---\n".join(context_parts)


def results_to_studies(results: list[dict[str, Any]]) -> list[StudySummary]:
    """Convert retrieval results to deduplicated StudySummary objects.

    Each result must have 'text' and 'metadata' keys.
    """
    studies: list[StudySummary] = []
    seen_titles: set[str] = set()

    for r in results:
        meta = r["metadata"]
        title = meta.get("paper_title", "")
        if title in seen_titles:
            continue
        seen_titles.add(title)

        findings_raw = meta.get("key_findings", "")
        findings = (
            [f.strip() for f in findings_raw.split("|") if f.strip()]
            if findings_raw
            else []
        )

        studies.append(
            StudySummary(
                pmid=meta.get("paper_pmid"),
                s2_id=(
                    meta.get("paper_id")
                    if meta.get("paper_id", "").startswith("S2:")
                    else None
                ),
                title=title,
                authors=meta.get("paper_authors", ""),
                year=meta.get("paper_year", 0),
                journal=meta.get("paper_journal", ""),
                doi=meta.get("paper_doi"),
                citation_count=meta.get("paper_citation_count"),
                open_access_pdf=meta.get("paper_open_access_pdf"),
                sample_size=meta.get("sample_size"),
                duration=meta.get("duration"),
                key_findings=findings,
            )
        )

    return studies


def metadata_to_studies(metadatas: list[dict[str, Any]]) -> list[StudySummary]:
    """Convert raw metadata dicts (from agent tool results) to StudySummary objects."""
    studies: list[StudySummary] = []
    seen_titles: set[str] = set()

    for meta in metadatas:
        title = meta.get("title", "")
        if title in seen_titles:
            continue
        seen_titles.add(title)

        findings_raw = meta.get("key_findings", "")
        findings = (
            [f.strip() for f in findings_raw.split("|") if f.strip()]
            if findings_raw
            else []
        )

        studies.append(
            StudySummary(
                pmid=meta.get("pmid"),
                s2_id=(
                    meta.get("id")
                    if meta.get("id", "").startswith("S2:")
                    else None
                ),
                title=title,
                authors=meta.get("authors", ""),
                year=meta.get("year", 0),
                journal=meta.get("journal", ""),
                doi=meta.get("doi"),
                citation_count=meta.get("citation_count"),
                sample_size=meta.get("sample_size"),
                duration=meta.get("duration"),
                key_findings=findings,
            )
        )

    return studies
