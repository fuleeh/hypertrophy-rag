"""RAG retrieval pipeline — query, retrieve, generate."""

from __future__ import annotations

import os
import time

from groq import Groq
from rich.console import Console

from hypertrophy_rag.index.vectordb import VectorDB
from hypertrophy_rag.logging import get_logger
from hypertrophy_rag.models import ResearchAnswer, StudySummary
from hypertrophy_rag.retrieval.guardrails import validate_output
from hypertrophy_rag.utils import assess_confidence

console = Console()
logger = get_logger("rag")

SYSTEM_PROMPT = """You are a hypertrophy research assistant. \
Given the retrieved research studies, provide a structured, \
evidence-based summary.

For each study:
- State the key finding with specific statistics (percentages, p-values, sample sizes)
- Note the sample size (n) and study duration
- Explain why this study is relevant to the question
- Cite by PMID or title

If studies conflict with each other, present both sides clearly.
Assess overall confidence based on: number of studies, total sample sizes, consistency of findings, and recency.

Rules:
- Only use information present in the provided context
- Do not fabricate statistics or study details
- If the provided studies don't adequately cover the question, say so
- Be specific and quantitative where possible
- Use plain language — avoid jargon where possible"""


def query_rag(
    question: str,
    vectordb: VectorDB,
    top_k: int = 8,
    year_filter: int | None = None,
    source_filter: str | None = None,
    model: str = "llama-3.3-70b-versatile",
    history: list[dict] | None = None,
) -> ResearchAnswer:
    """Run a RAG query and return structured results."""
    # 1. Retrieve relevant chunks
    t0 = time.perf_counter()
    results = vectordb.search(question, top_k=top_k, year_filter=year_filter, source_filter=source_filter)
    retrieval_ms = (time.perf_counter() - t0) * 1000

    if not results:
        return ResearchAnswer(
            question=question,
            answer="No relevant studies found in the index. Try ingesting more papers or broadening your query.",
            confidence="low",
        )

    # 2. Build context from retrieved chunks
    context_parts = []
    papers_seen = set()
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

    context = "\n---\n".join(context_parts)

    # 3. Call Groq LLM
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return ResearchAnswer(
            question=question,
            answer="Error: GROQ_API_KEY not set in environment.",
            confidence="low",
        )

    client = Groq(api_key=groq_key)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for msg in history[-6:]:  # Keep last 6 messages for context
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": f"Question: {question}\n\nRetrieved studies:\n{context}"})

    console.print(f"\n[dim]Calling LLM with {len(context_parts)} studies...[/dim]")

    t1 = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=2048,
        temperature=0.3,
    )
    llm_ms = (time.perf_counter() - t1) * 1000

    answer_text = response.choices[0].message.content

    logger.info(
        "RAG pipeline completed",
        extra={"extra_data": {
            "question": question[:100],
            "retrieval_ms": round(retrieval_ms, 2),
            "llm_ms": round(llm_ms, 2),
            "total_ms": round(retrieval_ms + llm_ms, 2),
            "studies_retrieved": len(results),
            "context_chars": len(context),
        }},
    )

    # 4. Build structured output
    studies = []
    for r in results:
        meta = r["metadata"]
        findings_raw = meta.get("key_findings", "")
        findings = [f.strip() for f in findings_raw.split("|") if f.strip()] if findings_raw else []

        studies.append(
            StudySummary(
                pmid=meta.get("paper_pmid"),
                s2_id=meta.get("paper_id") if meta.get("paper_id", "").startswith("S2:") else None,
                title=meta.get("paper_title", ""),
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

    # Deduplicate studies by title
    seen_titles = set()
    unique_studies = []
    for s in studies:
        if s.title not in seen_titles:
            seen_titles.add(s.title)
            unique_studies.append(s)

    answer = ResearchAnswer(
        question=question,
        answer=answer_text,
        studies=unique_studies,
        confidence=assess_confidence(answer_text),
    )

    # Apply guardrails validation
    answer = validate_output(answer)

    return answer
