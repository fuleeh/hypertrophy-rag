"""FastAPI backend for the Hypertrophy RAG web UI."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path so we can import the RAG modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

load_dotenv(PROJECT_ROOT / ".env")

from hypertrophy_rag.logging import get_logger  # noqa: E402

logger = get_logger("api")

app = FastAPI(title="Hypertrophy RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration:.1f}ms)",
        extra={"extra_data": {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration, 2),
        }},
    )
    return response


_vectordb_instance = None
_config_cache = None


def _load_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    import yaml
    config_path = PROJECT_ROOT / "config.yaml"
    _config_cache = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}
    return _config_cache


def _get_vectordb():
    global _vectordb_instance
    if _vectordb_instance is not None:
        return _vectordb_instance
    from hypertrophy_rag.index.vectordb import VectorDB

    config = _load_config()
    chroma_config = config.get("chroma", {})
    _vectordb_instance = VectorDB(
        collection_name=chroma_config.get("collection_name", "hypertrophy_papers"),
        persist_directory=str(PROJECT_ROOT / chroma_config.get("persist_directory", "data/chroma")),
    )
    return _vectordb_instance


class IngestRequest(BaseModel):
    source: str = "all"
    topic: str | None = None
    max_papers: int = 2000


@app.get("/api/query")
def query(
    question: str = Query(..., description="Research question"),
    top_k: int = Query(8, ge=1, le=20),
    year: int | None = Query(None),
    source: str | None = Query(None),
    engine: str = Query("custom", description="RAG engine: 'custom' or 'langchain'"),
    history: str | None = Query(None, description="JSON array of previous messages"),
):
    """Query the RAG system and return a structured research answer."""
    db = _get_vectordb()
    stats = db.get_stats()
    if stats["total_chunks"] == 0:
        raise HTTPException(status_code=400, detail="No papers indexed yet. Run ingest first.")

    parsed_history = []
    if history:
        try:
            parsed_history = json.loads(history)
        except json.JSONDecodeError:
            pass

    t0 = time.perf_counter()
    try:
        if engine == "langchain":
            from hypertrophy_rag.retrieval.langchain_rag import build_langchain_rag
            result = build_langchain_rag(
                question=question,
                persist_directory=str(PROJECT_ROOT / "data" / "chroma"),
                collection_name="hypertrophy_papers",
                top_k=top_k,
            )
        elif engine == "agent":
            from hypertrophy_rag.agent.agent import run_agent
            result = run_agent(question=question)
        else:
            from hypertrophy_rag.retrieval.rag import query_rag
            result = query_rag(
                question=question,
                vectordb=db,
                top_k=top_k,
                year_filter=year,
                source_filter=source,
                history=parsed_history,
            )
    except Exception as e:
        logger.error(
            "RAG query failed",
            extra={"extra_data": {"question": question, "error": str(e), "engine": engine}},
        )
        raise HTTPException(status_code=500, detail="RAG query failed. Check server logs for details.")

    rag_duration = (time.perf_counter() - t0) * 1000
    logger.info(
        "RAG query completed",
        extra={"extra_data": {
            "question": question[:100],
            "top_k": top_k,
            "engine": engine,
            "history_turns": len(parsed_history),
            "studies_returned": len(result.studies),
            "confidence": result.confidence,
            "rag_duration_ms": round(rag_duration, 2),
        }},
    )

    return {
        "question": result.question,
        "answer": result.answer,
        "confidence": result.confidence,
        "conflicting_findings": result.conflicting_findings,
        "studies": [
            {
                "pmid": s.pmid,
                "s2_id": s.s2_id,
                "title": s.title,
                "authors": s.authors,
                "year": s.year,
                "journal": s.journal,
                "doi": s.doi,
                "citation_count": s.citation_count,
                "open_access_pdf": s.open_access_pdf,
                "sample_size": s.sample_size,
                "duration": s.duration,
                "key_findings": s.key_findings,
                "relevance_note": s.relevance_note,
            }
            for s in result.studies
        ],
    }


@app.get("/api/stats")
def stats():
    """Get index statistics."""
    from hypertrophy_rag.ingestion.parser import load_papers

    db = _get_vectordb()
    index_stats = db.get_stats()
    papers = load_papers(str(PROJECT_ROOT / "data" / "papers"))

    pubmed_count = sum(1 for p in papers.values() if p.source == "pubmed")
    s2_count = sum(1 for p in papers.values() if p.source == "semantic_scholar")

    years = [p.year for p in papers.values() if p.year > 0]

    topics = {}
    for p in papers.values():
        if p.mesh_terms:
            for term in p.mesh_terms[:3]:
                topics[term] = topics.get(term, 0) + 1
    top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        "total_papers": len(papers),
        "total_chunks": index_stats["total_chunks"],
        "pubmed_count": pubmed_count,
        "s2_count": s2_count,
        "year_min": min(years) if years else 0,
        "year_max": max(years) if years else 0,
        "with_doi": sum(1 for p in papers.values() if p.doi),
        "with_citations": sum(1 for p in papers.values() if p.citation_count),
        "top_mesh_terms": top_topics,
    }


@app.get("/api/papers")
def list_papers(
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List indexed papers with optional search."""
    from hypertrophy_rag.ingestion.parser import load_papers

    papers = load_papers(str(PROJECT_ROOT / "data" / "papers"))
    paper_list = list(papers.values())

    if search:
        search_lower = search.lower()
        paper_list = [
            p for p in paper_list
            if search_lower in p.title.lower()
            or search_lower in p.abstract.lower()
            or search_lower in p.authors.lower()
            or search_lower in p.journal.lower()
        ]

    # Sort by year descending, then citation count
    paper_list.sort(key=lambda p: (p.year, p.citation_count or 0), reverse=True)

    page = paper_list[offset : offset + limit]

    return [
        {
            "id": p.id,
            "source": p.source,
            "title": p.title,
            "authors": p.authors,
            "abstract": p.abstract[:500] + "..." if len(p.abstract) > 500 else p.abstract,
            "year": p.year,
            "journal": p.journal,
            "doi": p.doi,
            "pmid": p.pmid,
            "citation_count": p.citation_count,
            "open_access_pdf": p.open_access_pdf,
            "mesh_terms": p.mesh_terms[:10],
        }
        for p in page
    ]


@app.get("/api/papers/{paper_id:path}")
def get_paper(paper_id: str):
    """Get a specific paper by ID."""
    from hypertrophy_rag.ingestion.parser import load_papers

    papers = load_papers(str(PROJECT_ROOT / "data" / "papers"))
    paper = papers.get(paper_id)

    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found")

    return {
        "id": paper.id,
        "source": paper.source,
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract,
        "year": paper.year,
        "journal": paper.journal,
        "doi": paper.doi,
        "pmid": paper.pmid,
        "citation_count": paper.citation_count,
        "open_access_pdf": paper.open_access_pdf,
        "mesh_terms": paper.mesh_terms,
    }


@app.get("/api/topics")
def list_topics():
    """List available ingestion topics."""
    config = _load_config()

    topics = []
    for q in config.get("search_queries", []):
        topics.append({
            "name": q["name"],
            "type": "pubmed",
            "description": q.get("text", "")[:100],
        })
    for q in config.get("semantic_scholar_queries", []):
        topics.append({
            "name": q,
            "type": "semantic_scholar",
            "description": q,
        })

    return topics


@app.post("/api/ingest")
def ingest(req: IngestRequest):
    """Trigger paper ingestion. Runs synchronously (may take a while)."""
    from hypertrophy_rag.ingestion.chunker import chunk_papers
    from hypertrophy_rag.ingestion.pubmed import ingest_pubmed
    from hypertrophy_rag.ingestion.semantic_scholar import ingest_semantic_scholar
    from hypertrophy_rag.retrieval.hybrid import HybridRetriever

    config = _load_config()
    db = _get_vectordb()
    all_papers = []

    t0 = time.perf_counter()
    logger.info("Ingestion started", extra={"extra_data": {"source": req.source, "topic": req.topic}})

    if req.source in ("pubmed", "all"):
        pubmed_config = config.copy()
        if req.topic:
            queries = [q for q in config.get("search_queries", []) if q["name"] == req.topic]
            pubmed_config["search_queries"] = queries
        papers = ingest_pubmed(pubmed_config, str(PROJECT_ROOT / "data" / "papers"), req.max_papers)
        all_papers.extend(papers)

    if req.source in ("semantic-scholar", "all"):
        s2_config = config.copy()
        if req.topic:
            s2_config["semantic_scholar_queries"] = [req.topic]
        papers = ingest_semantic_scholar(s2_config, str(PROJECT_ROOT / "data" / "papers"))
        all_papers.extend(papers)

    if all_papers:
        chunks = chunk_papers(all_papers)
        indexed = db.index_chunks(chunks)
        try:
            hybrid = HybridRetriever()
            hybrid.invalidate_bm25()
        except Exception:
            pass
        duration = time.perf_counter() - t0
        logger.info(
            "Ingestion completed",
            extra={"extra_data": {
                "source": req.source,
                "topic": req.topic,
                "papers_fetched": len(all_papers),
                "chunks_indexed": indexed,
                "duration_s": round(duration, 2),
            }},
        )
        return {"status": "ok", "indexed": indexed}

    return {"status": "ok", "indexed": 0}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
