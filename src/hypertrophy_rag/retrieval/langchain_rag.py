"""LangChain-based RAG chain for hypertrophy research."""

from __future__ import annotations

import os
import time

import chromadb
import requests as http_requests
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

from hypertrophy_rag.logging import get_logger
from hypertrophy_rag.models import ResearchAnswer, StudySummary

logger = get_logger("langchain_rag")

SYSTEM_PROMPT = """You are a hypertrophy research assistant. \
Given the retrieved research studies below, provide a structured, \
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
- Use plain language — avoid jargon where possible

{context}"""


def _get_embeddings():
    """Get Groq embeddings via custom wrapper for ChromaDB compatibility."""

    class GroqEmbeddings:
        """Wrapper to use Groq's nomic-embed-text via ChromaDB interface."""

        def __init__(self, model: str = "nomic-embed-text-v1.5"):
            self.model = model
            self.api_key = os.environ.get("GROQ_API_KEY", "")
            self.api_url = "https://api.groq.com/openai/v1/embeddings"

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            results = []
            for text in texts:
                resp = http_requests.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"model": self.model, "input": text},
                )
                resp.raise_for_status()
                results.append(resp.json()["data"][0]["embedding"])
            return results

        def embed_query(self, text: str) -> list[float]:
            return self.embed_documents([text])[0]

    return GroqEmbeddings()


def _assess_confidence(answer_text: str) -> str:
    """Simple heuristic to assess confidence from the answer text."""
    low_indicators = ["limited evidence", "few studies", "unclear", "insufficient", "mixed evidence"]
    high_indicators = [
        "strong evidence", "consistent findings", "meta-analysis",
        "systematic review", "multiple studies",
    ]
    text_lower = answer_text.lower()
    low_count = sum(1 for ind in low_indicators if ind in text_lower)
    high_count = sum(1 for ind in high_indicators if ind in text_lower)
    if low_count > high_count:
        return "low"
    elif high_count > low_count:
        return "high"
    return "medium"


def build_langchain_rag(
    question: str,
    persist_directory: str = "data/chroma",
    collection_name: str = "hypertrophy_papers",
    model: str = "llama-3.3-70b-versatile",
    top_k: int = 8,
) -> ResearchAnswer:
    """Run a RAG query using LangChain components and return structured results."""
    t0 = time.perf_counter()

    # Set up Groq LLM
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return ResearchAnswer(
            question=question,
            answer="Error: GROQ_API_KEY not set in environment.",
            confidence="low",
        )

    llm = ChatGroq(groq_api_key=groq_key, model=model, temperature=0.3, max_tokens=2048)

    # Connect to existing ChromaDB
    embeddings = _get_embeddings()
    vectorstore = Chroma(
        client=chromadb.PersistentClient(path=persist_directory),
        collection_name=collection_name,
        embedding_function=embeddings,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    # Build prompt
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    def _format_docs(docs):
        return "\n---\n".join(doc.page_content for doc in docs)

    # Build chain using LCEL
    chain = (
        {"context": retriever | _format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Run chain
    t1 = time.perf_counter()
    answer_text = chain.invoke(question)
    chain_ms = (time.perf_counter() - t1) * 1000

    # Also get raw docs for study extraction
    context_docs = retriever.invoke(question)

    # Extract study summaries from retrieved documents
    studies = []
    seen_titles = set()
    for doc in context_docs:
        meta = doc.metadata
        title = meta.get("paper_title", "")
        if title in seen_titles:
            continue
        seen_titles.add(title)

        findings_raw = meta.get("key_findings", "")
        findings = [f.strip() for f in findings_raw.split("|") if f.strip()] if findings_raw else []

        studies.append(
            StudySummary(
                pmid=meta.get("paper_pmid"),
                s2_id=meta.get("paper_id") if meta.get("paper_id", "").startswith("S2:") else None,
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

    total_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "LangChain RAG completed",
        extra={"extra_data": {
            "question": question[:100],
            "chain_ms": round(chain_ms, 2),
            "total_ms": round(total_ms, 2),
            "studies_retrieved": len(studies),
            "confidence": _assess_confidence(answer_text),
        }},
    )

    return ResearchAnswer(
        question=question,
        answer=answer_text,
        studies=studies,
        confidence=_assess_confidence(answer_text),
    )
