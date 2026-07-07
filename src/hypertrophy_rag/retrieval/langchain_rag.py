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
from hypertrophy_rag.models import ResearchAnswer
from hypertrophy_rag.retrieval.context import metadata_to_studies
from hypertrophy_rag.retrieval.prompts import RAG_SYSTEM_PROMPT
from hypertrophy_rag.utils import assess_confidence

logger = get_logger("langchain_rag")


def _get_embeddings():
    """Get Groq embeddings via custom wrapper for ChromaDB compatibility."""

    class GroqEmbeddings:
        """Wrapper to use Groq's nomic-embed-text via ChromaDB interface."""

        def __init__(self, model: str = "nomic-embed-text-v1.5"):
            self.model = model
            self.api_key = os.environ.get("GROQ_API_KEY", "")
            self.api_url = "https://api.groq.com/openai/v1/embeddings"

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            resp = http_requests.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "input": texts},
            )
            resp.raise_for_status()
            return [item["embedding"] for item in resp.json()["data"]]

        def embed_query(self, text: str) -> list[float]:
            return self.embed_documents([text])[0]

    return GroqEmbeddings()


def build_langchain_rag(
    question: str,
    persist_directory: str = "data/chroma",
    collection_name: str = "hypertrophy_papers",
    model: str = "llama-3.3-70b-versatile",
    top_k: int = 8,
) -> ResearchAnswer:
    """Run a RAG query using LangChain components and return structured results."""
    t0 = time.perf_counter()

    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return ResearchAnswer(
            question=question,
            answer="Error: GROQ_API_KEY not set in environment.",
            confidence="low",
        )

    llm = ChatGroq(groq_api_key=groq_key, model=model, temperature=0.3, max_tokens=2048)

    embeddings = _get_embeddings()
    vectorstore = Chroma(
        client=chromadb.PersistentClient(path=persist_directory),
        collection_name=collection_name,
        embedding_function=embeddings,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    prompt = ChatPromptTemplate.from_template(RAG_SYSTEM_PROMPT)

    def _format_docs(docs):
        return "\n---\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | _format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    t1 = time.perf_counter()
    answer_text = chain.invoke(question)
    chain_ms = (time.perf_counter() - t1) * 1000

    context_docs = retriever.invoke(question)

    studies = metadata_to_studies([doc.metadata for doc in context_docs])

    total_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "LangChain RAG completed",
        extra={"extra_data": {
            "question": question[:100],
            "chain_ms": round(chain_ms, 2),
            "total_ms": round(total_ms, 2),
            "studies_retrieved": len(studies),
            "confidence": assess_confidence(answer_text),
        }},
    )

    return ResearchAnswer(
        question=question,
        answer=answer_text,
        studies=studies,
        confidence=assess_confidence(answer_text),
    )
