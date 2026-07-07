"""Weekly index update script. Run via cron or manually.

Usage:
    python scripts/update_index.py [--source pubmed|semantic-scholar|all]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Update hypertrophy research index")
    parser.add_argument(
        "--source",
        choices=["pubmed", "semantic-scholar", "all"],
        default="all",
        help="Source to update",
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=500,
        help="Max papers per topic for new ingestion",
    )
    args = parser.parse_args()

    import yaml

    config_path = Path(__file__).parent.parent / "config.yaml"
    config = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}

    from hypertrophy_rag.index.vectordb import VectorDB

    chroma_config = config.get("chroma", {})
    db = VectorDB(
        collection_name=chroma_config.get("collection_name", "hypertrophy_papers"),
        persist_directory=chroma_config.get("persist_directory", "data/chroma"),
    )

    console.print("[bold]=== Weekly Index Update ===[/bold]\n")

    if args.source in ("pubmed", "all"):
        console.print("[bold blue]Updating PubMed...[/bold blue]")
        from hypertrophy_rag.ingestion.pubmed import ingest_pubmed
        pubmed_papers = ingest_pubmed(config, max_per_topic=args.max_papers)
    else:
        pubmed_papers = []

    if args.source in ("semantic-scholar", "all"):
        console.print("\n[bold blue]Updating Semantic Scholar...[/bold blue]")
        from hypertrophy_rag.ingestion.semantic_scholar import ingest_semantic_scholar
        s2_papers = ingest_semantic_scholar(config)
    else:
        s2_papers = []

    # Chunk and index new papers
    all_papers = pubmed_papers + s2_papers
    if all_papers:
        from hypertrophy_rag.ingestion.chunker import chunk_papers

        min_words = config.get("pubmed", {}).get("min_abstract_words", 100)
        chunks = chunk_papers(all_papers, min_abstract_words=min_words)
        indexed = db.index_chunks(chunks)
        console.print(f"\n[green]Indexed {indexed} chunks[/green]")

    stats = db.get_stats()
    console.print(f"\n[dim]Index stats: {stats}[/dim]")
    console.print("[green bold]Update complete![/green bold]")


if __name__ == "__main__":
    main()
