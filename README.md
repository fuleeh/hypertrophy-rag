# HypertroHub

RAG agent for hypertrophy research. Searches PubMed and Semantic Scholar for peer-reviewed studies, indexes them in ChromaDB, and uses Llama 3.3 70B to generate evidence-based answers with citations.

**Ask any training question. Get answers backed by peer-reviewed studies.**

---

## Features

- **Dual data sources** — PubMed (MeSH-based) + Semantic Scholar (citation-sorted)
- **16,000+ papers indexed** across 16 hypertrophy topics
- **Three retrieval engines** — custom RAG, LangChain LCEL chain, tool-using agent
- **Hybrid search** — BM25 keyword + semantic similarity with Reciprocal Rank Fusion
- **Structured citations** — PMID, DOI, citation count, sample size, key findings
- **Output guardrails** — hallucination detection, confidence calibration
- **RAGAS evaluation** — faithfulness, relevancy, context precision/recall

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq Llama 3.3 70B |
| Embeddings | Groq nomic-embed-text-v1.5 |
| Vector DB | ChromaDB (local, persistent) |
| Backend | FastAPI + Python 3.12 |
| Frontend | Next.js 16 + React 19 + Tailwind v4 |
| Data Sources | PubMed E-utilities + Semantic Scholar API |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 22+
- A [Groq API key](https://console.groq.com/keys) (free tier)

### Setup

```bash
git clone https://github.com/<your-username>/hypertrophy-rag.git
cd hypertrophy-rag

# Backend
pip install -e ".[dev]"
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Frontend
cd web && npm install && cd ..
```

### Ingest Data

```bash
hypertrophy-rag ingest --all
```

This fetches papers from PubMed and Semantic Scholar, chunks them, and indexes into ChromaDB. Takes ~10 minutes on first run.

### Run

```bash
# Backend (port 8000)
uvicorn api.main:app --reload

# Frontend (port 3000)
cd web && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Docker

```bash
docker compose up --build
```

## CLI

```bash
hypertrophy-rag query "how many sets per muscle per week?"
hypertrophy-rag query "does creatine help" --json
hypertrophy-rag stats
hypertrophy-rag top-cited --topic "volume" --limit 10
hypertrophy-rag paper PMID:31234567 --full
hypertrophy-rag list-topics
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/query?question=...` | RAG query |
| POST | `/api/ingest` | Trigger paper ingestion |
| GET | `/api/stats` | Index statistics |
| GET | `/api/papers?search=...` | Search papers |
| GET | `/api/papers/{id}` | Get specific paper |
| GET | `/api/topics` | List ingestion topics |

Select retrieval engine via `?engine=custom|langchain|agent`.

## Project Structure

```
hypertrophy-rag/
├── src/hypertrophy_rag/       # Core Python package
│   ├── ingestion/             # PubMed + Semantic Scholar pipelines
│   ├── index/                 # ChromaDB vector store
│   ├── retrieval/             # RAG, LangChain, hybrid, guardrails
│   └── agent/                 # Tool-using agent
├── api/                       # FastAPI backend
├── web/                       # Next.js frontend
├── tests/                     # Unit tests
├── scripts/                   # Evaluation + cron scripts
├── config.yaml                # Search queries, model settings
└── data/                      # Cached papers + ChromaDB (gitignored)
```

## How It Works

1. **Ingest** — Fetch papers from PubMed (MeSH queries) and Semantic Scholar (keyword search)
2. **Chunk** — Split abstracts into retrievable units, extract key findings (p-values, effect sizes, sample sizes)
3. **Embed** — Convert chunks to 768-dimensional vectors via Groq nomic-embed-text
4. **Index** — Store in ChromaDB with cosine similarity search
5. **Query** — Embed user question, retrieve top-8 similar chunks
6. **Generate** — Feed retrieved context to Llama 3.3 70B with citation instructions
7. **Validate** — Check for hallucinations, confidence calibration, format validation

## Cost

$0. All APIs (PubMed, Semantic Scholar, Groq) have free tiers.

## License

MIT
