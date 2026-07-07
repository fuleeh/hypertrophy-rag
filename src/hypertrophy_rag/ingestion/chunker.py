"""Abstract chunking and key finding extraction."""

from __future__ import annotations

import re

from hypertrophy_rag.models import Chunk, Paper

# Patterns for extracting quantitative findings
FINDING_PATTERNS = [
    # Percentage changes: "increased by 25%", "30% greater"
    re.compile(
        r"(?:increased|decreased|greater|lower|more|less|higher|reduced)"
        r"\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+(?:\.\d+)?)\s*%\s+"
        r"(?:greater|higher|lower|more|less|increase|decrease|improvement|reduction)",
        re.IGNORECASE,
    ),
    # P-values: "p < 0.05"
    re.compile(r"p\s*[<>=]+\s*0?\.\d+", re.IGNORECASE),
    # Effect sizes: "d = 0.85"
    re.compile(r"(?:effect\s+size|Cohen'?s?\s+d|Hedges'?s?\s*g)\s*[=:]\s*-?\d+\.\d+", re.IGNORECASE),
    # Mean differences: "increased from X to Y"
    re.compile(r"(?:increased|decreased|improved|changed)\s+from\s+\d+\.?\d*\s+to\s+\d+\.?\d*", re.IGNORECASE),
]

SAMPLE_SIZE_PATTERN = re.compile(r"n\s*=\s*(\d+)", re.IGNORECASE)
DURATION_PATTERN = re.compile(r"(\d+)[\s-]*(weeks?|months?|days?)", re.IGNORECASE)


def extract_key_findings(text: str) -> list[str]:
    """Extract quantitative findings from text."""
    findings = []
    for pattern in FINDING_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            # Get the full sentence containing the match
            sentence = _get_containing_sentence(text, match if isinstance(match, str) else match[0])
            if sentence and sentence not in findings:
                findings.append(sentence.strip())
    return findings[:10]  # Cap at 10 findings per chunk


def extract_sample_size(text: str) -> str | None:
    """Extract sample size from text."""
    match = SAMPLE_SIZE_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def extract_duration(text: str) -> str | None:
    """Extract study duration from text."""
    match = DURATION_PATTERN.search(text)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return None


def _get_containing_sentence(text: str, match_text: str) -> str | None:
    """Get the sentence containing a match."""
    idx = text.find(match_text)
    if idx == -1:
        return None

    # Find sentence boundaries
    sentence_end = max(
        text.rfind(".", 0, idx),
        text.rfind("!", 0, idx),
        text.rfind("?", 0, idx),
    )
    sentence_start = sentence_end + 1 if sentence_end >= 0 else 0

    # Find end of sentence
    next_period = len(text)
    for end_char in [".", "!", "?"]:
        pos = text.find(end_char, idx)
        if pos != -1 and pos < next_period:
            next_period = pos

    sentence = text[sentence_start : next_period + 1].strip()
    return sentence if len(sentence) > 20 else None


def chunk_paper(paper: Paper, min_abstract_words: int = 100) -> list[Chunk]:
    """Create chunks from a paper. Primary chunk = full abstract."""
    abstract = paper.abstract.strip()
    word_count = len(abstract.split())

    if word_count < min_abstract_words:
        return []

    chunks = []

    # Primary chunk: full abstract
    key_findings = extract_key_findings(abstract)
    sample_size = extract_sample_size(abstract)
    duration = extract_duration(abstract)

    chunks.append(
        Chunk(
            id=f"{paper.id}_0",
            text=abstract,
            paper=paper,
            key_findings=key_findings,
            sample_size=sample_size,
            duration=duration,
        )
    )

    # If abstract is very long (>500 words), also create subsection chunks
    if word_count > 500:
        sentences = re.split(r"(?<=[.!?])\s+", abstract)
        mid = len(sentences) // 2
        first_half = " ".join(sentences[:mid])
        second_half = " ".join(sentences[mid:])

        if len(first_half.split()) >= 100:
            chunks.append(
                Chunk(
                    id=f"{paper.id}_1",
                    text=first_half,
                    paper=paper,
                    key_findings=extract_key_findings(first_half),
                    sample_size=extract_sample_size(first_half),
                    duration=extract_duration(first_half),
                )
            )
        if len(second_half.split()) >= 100:
            chunks.append(
                Chunk(
                    id=f"{paper.id}_2",
                    text=second_half,
                    paper=paper,
                    key_findings=extract_key_findings(second_half),
                    sample_size=extract_sample_size(second_half),
                    duration=extract_duration(second_half),
                )
            )

    return chunks


def chunk_papers(papers: list[Paper], min_abstract_words: int = 100) -> list[Chunk]:
    """Chunk a list of papers."""
    all_chunks = []
    for paper in papers:
        chunks = chunk_paper(paper, min_abstract_words)
        all_chunks.extend(chunks)
    return all_chunks
