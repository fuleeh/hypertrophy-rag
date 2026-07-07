"""PubMed E-utilities ingestion pipeline."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from rich.console import Console

from hypertrophy_rag.models import Paper

console = Console()

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _build_query(query_config: dict) -> str:
    """Build a PubMed search query from config entry."""
    parts = []
    if "mesh" in query_config:
        parts.append(f"({query_config['mesh']})")
    if "text" in query_config:
        parts.append(f"({query_config['text']})")
    if "years" in query_config:
        start, end = query_config["years"].split(":")
        parts.append(f"({start}:{end}[pdat])")
    parts.append("humans[mh]")
    return " AND ".join(parts)


def search_papers(
    query_config: dict,
    max_results: int = 2000,
    delay: float = 0.35,
) -> list[str]:
    """Search PubMed and return list of PMIDs."""
    query = _build_query(query_config)
    console.print(f"  [dim]Query:[/dim] {query[:100]}...")

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": min(max_results, 10000),
        "retmode": "json",
        "sort": "relevance",
    }

    resp = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    pmids = data.get("esearchresult", {}).get("idlist", [])
    total = data.get("esearchresult", {}).get("count", "0")
    console.print(f"  [green]Found {total} results, retrieved {len(pmids)} PMIDs[/green]")
    time.sleep(delay)
    return pmids


def fetch_papers(
    pmids: list[str],
    batch_size: int = 100,
    delay: float = 0.35,
) -> list[Paper]:
    """Fetch paper details from PubMed for a list of PMIDs."""
    papers: list[Paper] = []
    total_batches = (len(pmids) - 1) // batch_size + 1

    for i in range(0, len(pmids), batch_size):
        batch = pmids[i : i + batch_size]
        batch_num = i // batch_size + 1
        console.print(f"  Fetching batch {batch_num}/{total_batches} ({len(batch)} papers)...")

        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
            "rettype": "abstract",
        }

        try:
            resp = requests.get(f"{BASE_URL}/efetch.fcgi", params=params, timeout=60)
            resp.raise_for_status()
            papers.extend(_parse_xml(resp.text))
        except requests.exceptions.HTTPError as e:
            console.print(f"  [yellow]Batch {batch_num} failed: {e}. Skipping...[/yellow]")
        except requests.exceptions.RequestException as e:
            console.print(f"  [yellow]Batch {batch_num} network error: {e}. Skipping...[/yellow]")
        time.sleep(delay)

    return papers


def _parse_xml(xml_text: str) -> list[Paper]:
    """Parse PubMed EFetch XML response into Paper objects."""
    papers = []
    root = ET.fromstring(xml_text)

    for article in root.findall(".//PubmedArticle"):
        try:
            paper = _parse_article(article)
            if paper:
                papers.append(paper)
        except Exception as e:
            console.print(f"  [yellow]Warning: Failed to parse article: {e}[/yellow]")
            continue

    return papers


def _parse_article(article: ET.Element) -> Paper | None:
    """Parse a single PubmedArticle element."""
    medline = article.find("MedlineCitation")
    if medline is None:
        return None

    pmid_el = medline.find("PMID")
    if pmid_el is None or pmid_el.text is None:
        return None
    pmid = pmid_el.text.strip()

    article_el = medline.find("Article")
    if article_el is None:
        return None

    # Title
    title_el = article_el.find("ArticleTitle")
    title = _text_content(title_el) if title_el is not None else ""

    # Abstract
    abstract_parts = []
    abstract_el = article_el.find("Abstract")
    if abstract_el is not None:
        for text_el in abstract_el.findall("AbstractText"):
            label = text_el.get("Label", "")
            text = _text_content(text_el)
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
    abstract = " ".join(abstract_parts).strip()

    if not abstract:
        return None

    # Authors
    authors_list = []
    author_list_el = article_el.find("AuthorList")
    if author_list_el is not None:
        for author_el in author_list_el.findall("Author"):
            last = author_el.find("LastName")
            fore = author_el.find("ForeName")
            name_parts = []
            if fore is not None and fore.text:
                name_parts.append(fore.text)
            if last is not None and last.text:
                name_parts.append(last.text)
            if name_parts:
                authors_list.append(" ".join(name_parts))
    authors = ", ".join(authors_list[:5])
    if len(authors_list) > 5:
        authors += f" et al. ({len(authors_list)} authors)"

    # Journal
    journal_el = article_el.find("Journal/Title")
    journal = _text_content(journal_el) if journal_el is not None else ""

    # Year
    year = 0
    year_el = article_el.find("Journal/JournalIssue/PubDate/Year")
    if year_el is not None and year_el.text:
        try:
            year = int(year_el.text)
        except ValueError:
            pass

    if year == 0:
        medline_date = article_el.find("Journal/JournalIssue/PubDate/MedlineDate")
        if medline_date is not None and medline_date.text:
            match = re.search(r"(\d{4})", medline_date.text)
            if match:
                year = int(match.group(1))

    # DOI
    doi = None
    for eid in article_el.findall("ELocationID"):
        if eid.get("EIdType") == "doi":
            doi = eid.text
            break

    # MeSH terms
    mesh_terms = []
    mesh_list = medline.find("MeshHeadingList")
    if mesh_list is not None:
        for mh in mesh_list.findall("MeshHeading"):
            descriptor = mh.find("DescriptorName")
            if descriptor is not None and descriptor.text:
                mesh_terms.append(descriptor.text)

    return Paper(
        id=f"PMID:{pmid}",
        source="pubmed",
        title=title,
        authors=authors,
        abstract=abstract,
        year=year,
        journal=journal,
        doi=doi,
        pmid=pmid,
        mesh_terms=mesh_terms,
    )


def _text_content(element: ET.Element | None) -> str:
    """Extract all text content from an element, including tail text."""
    if element is None:
        return ""
    parts = []
    if element.text:
        parts.append(element.text)
    for child in element:
        parts.append(_text_content(child))
        if child.tail:
            parts.append(child.tail)
    return " ".join(parts).strip()


def ingest_pubmed(
    config: dict,
    cache_dir: str = "data/papers",
    max_per_topic: int = 2000,
) -> list[Paper]:
    """Run the full PubMed ingestion pipeline."""
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_file = cache_path / "pubmed.json"

    # Load existing cache
    existing_papers: dict[str, Paper] = {}
    if cache_file.exists():
        raw = json.loads(cache_file.read_text())
        for p in raw:
            paper = Paper(**p)
            existing_papers[paper.id] = paper
        console.print(f"[dim]Loaded {len(existing_papers)} cached papers[/dim]")

    all_pmids: list[str] = []
    queries = config.get("search_queries", [])
    delay = config.get("pubmed", {}).get("rate_limit_delay", 0.35)
    batch_size = config.get("pubmed", {}).get("fetch_batch_size", 200)

    for query_config in queries:
        console.print(f"\n[bold cyan]Searching: {query_config['name']}[/bold cyan]")
        pmids = search_papers(query_config, max_per_topic, delay)
        all_pmids.extend(pmids)

    # Deduplicate
    unique_pmids = list(dict.fromkeys(all_pmids))
    console.print(f"\n[bold]Total unique PMIDs: {len(unique_pmids)}[/bold]")

    # Filter out already cached
    new_pmids = [p for p in unique_pmids if f"PMID:{p}" not in existing_papers]
    console.print(f"[dim]New PMIDs to fetch: {len(new_pmids)}[/dim]")

    if new_pmids:
        new_papers = fetch_papers(new_pmids, batch_size, delay)
        for paper in new_papers:
            existing_papers[paper.id] = paper

    # Save cache
    all_papers = list(existing_papers.values())
    cache_file.write_text(json.dumps([p.to_dict() for p in all_papers], indent=2))
    console.print(f"\n[green]Saved {len(all_papers)} papers to {cache_file}[/green]")

    return all_papers
