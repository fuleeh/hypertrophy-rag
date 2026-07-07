"""CLI entry point for the hypertrophy RAG agent."""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

app = typer.Typer(
    name="hypertrophy-rag",
    help="Hypertrophy Research RAG Agent — PubMed + Semantic Scholar + Groq LLM",
)
console = Console()

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


def _load_config() -> dict:
    """Load config.yaml."""
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text())
    return {}


def _get_vectordb():
    """Initialize the vector DB."""
    from hypertrophy_rag.index.vectordb import VectorDB

    config = _load_config()
    chroma_config = config.get("chroma", {})
    return VectorDB(
        collection_name=chroma_config.get("collection_name", "hypertrophy_papers"),
        persist_directory=chroma_config.get("persist_directory", "data/chroma"),
    )


@app.command()
def ingest(
    source: str = typer.Option("all", help="Source to ingest: pubmed, semantic-scholar, or all"),
    topic: str | None = typer.Option(None, help="Specific topic/query name to ingest"),
    max_papers: int = typer.Option(2000, help="Max papers per topic"),
    reindex: bool = typer.Option(False, help="Clear index and re-index everything"),
):
    """Ingest papers from PubMed and/or Semantic Scholar."""
    config = _load_config()
    db = _get_vectordb()

    if reindex:
        console.print("[yellow]Clearing existing index...[/yellow]")
        db.delete_all()

    all_papers = []

    # PubMed
    if source in ("pubmed", "all"):
        console.print("\n[bold blue]=== PubMed Ingestion ===[/bold blue]")
        from hypertrophy_rag.ingestion.pubmed import ingest_pubmed

        if topic:
            queries = [q for q in config.get("search_queries", []) if q["name"] == topic]
            if not queries:
                console.print(f"[red]Topic '{topic}' not found in config[/red]")
                return
            sub_config = {**config, "search_queries": queries}
        else:
            sub_config = config

        pubmed_papers = ingest_pubmed(sub_config, max_per_topic=max_papers)
        all_papers.extend(pubmed_papers)

    # Semantic Scholar
    if source in ("semantic-scholar", "all"):
        console.print("\n[bold blue]=== Semantic Scholar Ingestion ===[/bold blue]")
        from hypertrophy_rag.ingestion.semantic_scholar import ingest_semantic_scholar

        if topic:
            sub_config = {**config, "semantic_scholar_queries": [topic]}
        else:
            sub_config = config

        s2_papers = ingest_semantic_scholar(sub_config)
        all_papers.extend(s2_papers)

    # Chunk and index
    if all_papers:
        console.print(f"\n[bold]Chunking {len(all_papers)} papers...[/bold]")
        from hypertrophy_rag.ingestion.chunker import chunk_papers

        min_words = config.get("pubmed", {}).get("min_abstract_words", 100)
        chunks = chunk_papers(all_papers, min_abstract_words=min_words)
        console.print(f"[bold]Created {len(chunks)} chunks[/bold]")

        console.print("\n[bold]Indexing into ChromaDB...[/bold]")
        indexed = db.index_chunks(chunks)
        console.print(f"\n[green bold]Done! Indexed {indexed} chunks.[/green bold]")
    else:
        console.print("[yellow]No papers ingested.[/yellow]")

    stats = db.get_stats()
    console.print(f"\n[dim]Index stats: {stats}[/dim]")


@app.command()
def query(
    question: str = typer.Argument(..., help="Your research question"),
    top_k: int = typer.Option(8, help="Number of studies to retrieve"),
    year: int | None = typer.Option(None, help="Minimum publication year"),
    source: str | None = typer.Option(None, help="Filter by source: pubmed or semantic_scholar"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Ask a research question about hypertrophy."""
    from hypertrophy_rag.retrieval.rag import query_rag

    db = _get_vectordb()

    stats = db.get_stats()
    if stats["total_chunks"] == 0:
        console.print("[red]No papers indexed yet. Run 'hypertrophy-rag ingest' first.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Question:[/bold cyan] {question}")
    console.print(f"[dim]Searching {stats['total_chunks']} chunks...[/dim]\n")

    result = query_rag(
        question=question,
        vectordb=db,
        top_k=top_k,
        year_filter=year,
        source_filter=source,
    )

    if json_output:
        output = {
            "question": result.question,
            "answer": result.answer,
            "confidence": result.confidence,
            "studies": [
                {
                    "title": s.title,
                    "authors": s.authors,
                    "year": s.year,
                    "journal": s.journal,
                    "pmid": s.pmid,
                    "doi": s.doi,
                    "citation_count": s.citation_count,
                    "sample_size": s.sample_size,
                    "duration": s.duration,
                    "key_findings": s.key_findings,
                }
                for s in result.studies
            ],
        }
        console.print(json.dumps(output, indent=2))
    else:
        _print_answer(result)


@app.command()
def top_cited(
    topic: str = typer.Option("hypertrophy", help="Topic to search"),
    limit: int = typer.Option(10, help="Number of papers to show"),
):
    """Show most cited papers in the index."""
    from hypertrophy_rag.ingestion.parser import load_papers

    papers = load_papers()
    filtered = [p for p in papers.values() if p.citation_count and p.citation_count > 0]

    # Sort by citation count
    filtered.sort(key=lambda p: p.citation_count or 0, reverse=True)

    if topic:
        topic_lower = topic.lower()
        filtered = [
            p for p in filtered
            if topic_lower in p.title.lower()
            or topic_lower in p.abstract.lower()
            or topic_lower in " ".join(p.mesh_terms).lower()
        ]

    table = Table(title=f"Top Cited Papers: {topic}")
    table.add_column("Citations", justify="right", style="cyan")
    table.add_column("Year", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Authors", style="dim")
    table.add_column("PMID", style="green")

    for paper in filtered[:limit]:
        table.add_row(
            str(paper.citation_count),
            str(paper.year),
            paper.title[:80] + ("..." if len(paper.title) > 80 else ""),
            paper.authors[:40] + ("..." if len(paper.authors) > 40 else ""),
            paper.pmid or "",
        )

    console.print(table)


@app.command()
def stats():
    """Show index statistics."""
    from hypertrophy_rag.ingestion.parser import load_papers

    db = _get_vectordb()
    index_stats = db.get_stats()
    papers = load_papers()

    # Count by source
    pubmed_count = sum(1 for p in papers.values() if p.source == "pubmed")
    s2_count = sum(1 for p in papers.values() if p.source == "semantic_scholar")

    # Year distribution
    years = [p.year for p in papers.values() if p.year > 0]
    year_min = min(years) if years else 0
    year_max = max(years) if years else 0

    console.print("\n[bold]=== Index Statistics ===[/bold]")
    console.print(f"  Total papers: [cyan]{len(papers)}[/cyan]")
    console.print(f"    PubMed: [green]{pubmed_count}[/green]")
    console.print(f"    Semantic Scholar: [green]{s2_count}[/green]")
    console.print(f"  Total chunks: [cyan]{index_stats['total_chunks']}[/cyan]")
    console.print(f"  Year range: [cyan]{year_min} - {year_max}[/cyan]")

    # Papers with DOIs
    with_doi = sum(1 for p in papers.values() if p.doi)
    with_citations = sum(1 for p in papers.values() if p.citation_count)
    console.print(f"  Papers with DOI: [cyan]{with_doi}[/cyan]")
    console.print(f"  Papers with citation count: [cyan]{with_citations}[/cyan]")

    # Top topics
    topics = {}
    for p in papers.values():
        if p.mesh_terms:
            for term in p.mesh_terms[:3]:
                topics[term] = topics.get(term, 0) + 1
    if topics:
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]
        console.print("\n[bold]Top MeSH Terms:[/bold]")
        for term, count in top_topics:
            console.print(f"  {term}: {count}")


@app.command()
def list_topics():
    """List available ingestion topics from config."""
    config = _load_config()

    console.print("\n[bold]PubMed Topics (MeSH-based):[/bold]")
    for q in config.get("search_queries", []):
        console.print(f"  [cyan]{q['name']}[/cyan]")
        if "mesh" in q:
            console.print(f"    MeSH: {q['mesh'][:60]}...")
        console.print(f"    Text: {q.get('text', '')[:60]}...")

    console.print("\n[bold]Semantic Scholar Topics (keyword-based):[/bold]")
    for q in config.get("semantic_scholar_queries", []):
        console.print(f"  [cyan]{q}[/cyan]")


@app.command()
def paper(
    paper_id: str = typer.Argument(..., help="Paper ID (PMID:12345678 or S2:ABC123)"),
    full: bool = typer.Option(False, "--full", help="Show full abstract"),
):
    """Look up a specific paper by ID."""
    from hypertrophy_rag.ingestion.parser import load_papers

    papers = load_papers()
    paper = papers.get(paper_id)

    if not paper:
        console.print(f"[red]Paper '{paper_id}' not found in index.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]{paper.title}[/bold]")
    console.print(f"  Authors: {paper.authors}")
    console.print(f"  Year: {paper.year}")
    console.print(f"  Journal: {paper.journal}")
    console.print(f"  PMID: {paper.pmid or 'N/A'}")
    console.print(f"  DOI: {paper.doi or 'N/A'}")
    console.print(f"  Source: {paper.source}")
    if paper.citation_count:
        console.print(f"  Citations: {paper.citation_count}")
    if paper.open_access_pdf:
        console.print(f"  PDF: {paper.open_access_pdf}")
    if paper.mesh_terms:
        console.print(f"  MeSH: {', '.join(paper.mesh_terms[:10])}")

    if full:
        console.print(f"\n[bold]Abstract:[/bold]\n{paper.abstract}")
    else:
        abstract_preview = paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract
        console.print(f"\n[dim]{abstract_preview}[/dim]")


def _print_answer(result):
    """Pretty-print a ResearchAnswer."""
    console.print(f"\n{'='*60}")
    console.print(f"[bold cyan]Question:[/bold cyan] {result.question}")
    console.print(f"{'='*60}\n")

    console.print("[bold green]Answer:[/bold green]")
    console.print(result.answer)
    console.print()

    if result.studies:
        console.print(f"[bold]Studies ({len(result.studies)} found):[/bold]\n")
        for i, study in enumerate(result.studies, 1):
            citation_info = f" | {study.citation_count} citations" if study.citation_count else ""
            sample_info = f" | n={study.sample_size}" if study.sample_size else ""
            duration_info = f" | {study.duration}" if study.duration else ""

            console.print(
                f"  [cyan]{i}.[/cyan] [bold]{study.title}[/bold]"
            )
            console.print(
                f"     {study.authors[:50]}{'...' if len(study.authors) > 50 else ''} "
                f"({study.year}) — {study.journal}"
            )
            console.print(
                f"     [dim]{study.pmid or ''}{citation_info}{sample_info}{duration_info}[/dim]"
            )
            if study.doi:
                console.print(f"     [dim]DOI: {study.doi}[/dim]")
            if study.key_findings:
                for finding in study.key_findings[:3]:
                    console.print(f"     [green]>[/green] {finding}")
            console.print()

    if result.conflicting_findings:
        console.print(f"[bold yellow]Conflicting Findings:[/bold yellow]")
        console.print(f"  {result.conflicting_findings}\n")

    console.print(f"[dim]Confidence: {result.confidence}[/dim]")


if __name__ == "__main__":
    app()
