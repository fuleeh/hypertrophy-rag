"""Unified parser for combining papers from PubMed and Semantic Scholar."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from hypertrophy_rag.models import Paper

console = Console()


def load_papers(cache_dir: str = "data/papers") -> dict[str, Paper]:
    """Load all cached papers from both sources, deduplicated by DOI."""
    cache_path = Path(cache_dir)
    papers: dict[str, Paper] = {}

    # Load PubMed papers
    pubmed_file = cache_path / "pubmed.json"
    if pubmed_file.exists():
        raw = json.loads(pubmed_file.read_text())
        for p in raw:
            paper = Paper(**p)
            papers[paper.id] = paper
        console.print(f"[dim]Loaded {len([p for p in papers.values() if p.source == 'pubmed'])} PubMed papers[/dim]")

    # Load Semantic Scholar papers
    s2_file = cache_path / "semantic_scholar.json"
    if s2_file.exists():
        raw = json.loads(s2_file.read_text())
        s2_count = 0
        for p in raw:
            paper = Paper(**p)
            # Deduplicate by DOI if available
            if paper.doi:
                existing_by_doi = next(
                    (pid for pid, pp in papers.items() if pp.doi == paper.doi),
                    None,
                )
                if existing_by_doi:
                    # Merge: keep the one with more data
                    existing = papers[existing_by_doi]
                    has_more_citations = (
                        paper.citation_count
                        and (not existing.citation_count
                             or paper.citation_count > existing.citation_count)
                    )
                    if has_more_citations:
                        # S2 has citation count, prefer it for metadata
                        existing.citation_count = paper.citation_count
                        existing.open_access_pdf = paper.open_access_pdf
                        existing.id = paper.id
                        papers[paper.id] = existing
                        del papers[existing_by_doi]
                    continue
            papers[paper.id] = paper
            s2_count += 1
        console.print(f"[dim]Loaded {s2_count} Semantic Scholar papers[/dim]")

    console.print(f"[bold]Total unique papers: {len(papers)}[/bold]")
    return papers


def merge_papers(
    pubmed_papers: list[Paper],
    s2_papers: list[Paper],
) -> dict[str, Paper]:
    """Merge papers from both sources, deduplicate by DOI."""
    merged: dict[str, Paper] = {}

    for paper in pubmed_papers:
        merged[paper.id] = paper

    for paper in s2_papers:
        if paper.doi:
            existing_by_doi = next(
                (pid for pid, pp in merged.items() if pp.doi == paper.doi),
                None,
            )
            if existing_by_doi:
                existing = merged[existing_by_doi]
                # Merge metadata: prefer S2 for citation count, PubMed for MeSH
                if paper.citation_count and not existing.citation_count:
                    existing.citation_count = paper.citation_count
                if paper.open_access_pdf and not existing.open_access_pdf:
                    existing.open_access_pdf = paper.open_access_pdf
                if paper.mesh_terms and not existing.mesh_terms:
                    existing.mesh_terms = paper.mesh_terms
                continue
        merged[paper.id] = paper

    return merged
