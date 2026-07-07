"""Semantic Scholar ingestion pipeline."""

from __future__ import annotations

import json
import time
from pathlib import Path

from rich.console import Console
from semanticscholar import SemanticScholar

from hypertrophy_rag.models import Paper

console = Console()


def search_papers(
    query: str,
    sch: SemanticScholar,
    max_results: int = 100,
    year_range: str = "2015-2026",
    delay: float = 1.1,
) -> list[Paper]:
    """Search Semantic Scholar and return Paper objects."""
    console.print(f"  [dim]Query:[/dim] {query}")

    try:
        response = sch.search_paper(
            query=query,
            bulk=True,
            sort="citationCount:desc",
            year=year_range,
            fields=[
                "title",
                "abstract",
                "authors",
                "year",
                "venue",
                "citationCount",
                "externalIds",
                "openAccessPdf",
                "publicationTypes",
                "s2FieldsOfStudy",
            ],
            limit=min(max_results, 100),
        )
    except Exception as e:
        console.print(f"  [red]Error searching Semantic Scholar: {e}[/red]")
        return []

    papers = []
    for item in response.items:
        paper = _parse_paper(item)
        if paper:
            papers.append(paper)

    console.print(f"  [green]Retrieved {len(papers)} papers[/green]")
    time.sleep(delay)
    return papers


def _parse_paper(item) -> Paper | None:
    """Parse a Semantic Scholar Paper object into our Paper model."""
    if not item.abstract:
        return None

    authors_list = []
    if item.authors:
        for author in item.authors[:5]:
            if author.name:
                authors_list.append(author.name)
    authors = ", ".join(authors_list)
    if item.authors and len(item.authors) > 5:
        authors += f" et al. ({len(item.authors)} authors)"

    doi = None
    pmid = None
    if item.externalIds:
        doi = getattr(item.externalIds, "DOI", None)
        pmid = getattr(item.externalIds, "PubMed", None)

    open_access_pdf = None
    if item.openAccessPdf:
        open_access_pdf = getattr(item.openAccessPdf, "url", None)

    journal = item.venue or ""

    return Paper(
        id=f"S2:{item.paperId}",
        source="semantic_scholar",
        title=item.title or "",
        authors=authors,
        abstract=item.abstract,
        year=item.year or 0,
        journal=journal,
        doi=doi,
        pmid=pmid,
        citation_count=item.citationCount,
        open_access_pdf=open_access_pdf,
    )


def ingest_semantic_scholar(
    config: dict,
    cache_dir: str = "data/papers",
) -> list[Paper]:
    """Run the full Semantic Scholar ingestion pipeline."""
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_file = cache_path / "semantic_scholar.json"

    # Load existing cache
    existing_papers: dict[str, Paper] = {}
    if cache_file.exists():
        raw = json.loads(cache_file.read_text())
        for p in raw:
            paper = Paper(**p)
            existing_papers[paper.id] = paper
        console.print(f"[dim]Loaded {len(existing_papers)} cached papers[/dim]")

    s2_config = config.get("semantic_scholar", {})
    delay = s2_config.get("rate_limit_delay", 1.1)
    max_per_query = s2_config.get("max_papers_per_query", 1000)

    # Initialize Semantic Scholar client
    api_key = config.get("semantic_scholar_api_key")
    sch = SemanticScholar(api_key=api_key) if api_key else SemanticScholar()

    queries = config.get("semantic_scholar_queries", [])

    for query in queries:
        console.print(f"\n[bold cyan]Searching Semantic Scholar: {query}[/bold cyan]")
        papers = search_papers(query, sch, max_per_query, delay=delay)
        for paper in papers:
            if paper.id not in existing_papers:
                existing_papers[paper.id] = paper

    # Save cache
    all_papers = list(existing_papers.values())
    cache_file.write_text(json.dumps([p.to_dict() for p in all_papers], indent=2))
    console.print(f"\n[green]Saved {len(all_papers)} papers to {cache_file}[/green]")

    return all_papers
