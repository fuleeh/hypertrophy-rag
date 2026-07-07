"""Core data models for the hypertrophy RAG system."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Paper:
    """A research paper from any source."""

    id: str  # "PMID:12345678" or "S2:ABC123"
    source: str  # "pubmed" or "semantic_scholar"
    title: str
    authors: str
    abstract: str
    year: int
    journal: str
    doi: str | None = None
    pmid: str | None = None
    citation_count: int | None = None
    open_access_pdf: str | None = None
    mesh_terms: list[str] = field(default_factory=list)
    query_topic: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "pmid": self.pmid,
            "citation_count": self.citation_count,
            "open_access_pdf": self.open_access_pdf,
            "mesh_terms": self.mesh_terms,
            "query_topic": self.query_topic,
        }


@dataclass
class Chunk:
    """A chunk of text from a paper, ready for embedding."""

    id: str  # f"{paper_id}_{chunk_idx}"
    text: str
    paper: Paper
    key_findings: list[str] = field(default_factory=list)
    sample_size: str | None = None
    duration: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "paper_id": self.paper.id,
            "paper_title": self.paper.title,
            "paper_authors": self.paper.authors,
            "paper_year": self.paper.year,
            "paper_journal": self.paper.journal,
            "paper_doi": self.paper.doi,
            "paper_pmid": self.paper.pmid,
            "paper_citation_count": self.paper.citation_count,
            "paper_open_access_pdf": self.paper.open_access_pdf,
            "key_findings": "|".join(self.key_findings),
            "sample_size": self.sample_size or "",
            "duration": self.duration or "",
            "query_topic": self.paper.query_topic,
            "source": self.paper.source,
        }


@dataclass
class StudySummary:
    """A study summary for the final output."""

    pmid: str | None = None
    s2_id: str | None = None
    title: str = ""
    authors: str = ""
    year: int = 0
    journal: str = ""
    doi: str | None = None
    citation_count: int | None = None
    open_access_pdf: str | None = None
    sample_size: str | None = None
    duration: str | None = None
    key_findings: list[str] = field(default_factory=list)
    relevance_note: str = ""


@dataclass
class ResearchAnswer:
    """Final structured answer from the RAG pipeline."""

    question: str = ""
    answer: str = ""
    studies: list[StudySummary] = field(default_factory=list)
    conflicting_findings: str | None = None
    confidence: str = "medium"
