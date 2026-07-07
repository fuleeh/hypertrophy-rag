"""RAG retrieval pipeline — query, retrieve, generate."""

from __future__ import annotations

import time

from hypertrophy_rag.logging import get_logger
from hypertrophy_rag.models import ResearchAnswer
from hypertrophy_rag.retrieval.base import LLMProvider, Retriever
from hypertrophy_rag.retrieval.context import build_context, results_to_studies
from hypertrophy_rag.retrieval.guardrails import validate_output
from hypertrophy_rag.retrieval.prompts import RAG_SYSTEM_PROMPT
from hypertrophy_rag.utils import assess_confidence

logger = get_logger("rag")


def _build_messages(
    question: str,
    context: str,
    history: list[dict] | None = None,
) -> list[dict[str, str]]:
    """Build the message list for the LLM."""
    messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
    if history:
        for msg in history[-6:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": f"Question: {question}\n\nRetrieved studies:\n{context}"})
    return messages


def query_rag(
    question: str,
    retriever: Retriever,
    llm: LLMProvider,
    top_k: int = 8,
    year_filter: int | None = None,
    source_filter: str | None = None,
    model: str = "",
    history: list[dict] | None = None,
) -> ResearchAnswer:
    """Run a RAG query and return structured results.

    Uses dependency injection — caller provides the retriever and LLM.
    """
    # 1. Retrieve relevant chunks
    t0 = time.perf_counter()
    results = retriever.search(question, top_k=top_k, year_filter=year_filter, source_filter=source_filter)
    retrieval_ms = (time.perf_counter() - t0) * 1000

    if not results:
        return ResearchAnswer(
            question=question,
            answer="No relevant studies found in the index. Try ingesting more papers or broadening your query.",
            confidence="low",
        )

    # 2. Build context from retrieved chunks
    context = build_context(results)

    # 3. Call LLM
    messages = _build_messages(question, context, history)

    t1 = time.perf_counter()
    answer_text = llm.generate(messages, model=model)
    llm_ms = (time.perf_counter() - t1) * 1000

    # 4. Build structured output
    studies = results_to_studies(results)

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

    answer = ResearchAnswer(
        question=question,
        answer=answer_text,
        studies=studies,
        confidence=assess_confidence(answer_text),
    )

    # Apply guardrails validation
    answer = validate_output(answer)

    return answer
