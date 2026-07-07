"""Shared configuration and factory functions.

Single source of truth for config loading and dependency creation.
Used by both API and CLI — no duplication.
"""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

_config_cache: dict | None = None
_vectordb_instance = None


def load_config() -> dict:
    """Load and cache config.yaml."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    _config_cache = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    return _config_cache


def get_vectordb():
    """Get or create the cached VectorDB instance."""
    global _vectordb_instance
    if _vectordb_instance is not None:
        return _vectordb_instance
    from hypertrophy_rag.index.vectordb import VectorDB

    config = load_config()
    chroma_config = config.get("chroma", {})
    _vectordb_instance = VectorDB(
        collection_name=chroma_config.get("collection_name", "hypertrophy_papers"),
        persist_directory=str(PROJECT_ROOT / chroma_config.get("persist_directory", "data/chroma")),
    )
    return _vectordb_instance


def get_llm():
    """Create an LLM provider from config."""
    from hypertrophy_rag.retrieval.providers import GroqLLM

    config = load_config()
    llm_config = config.get("llm", {})
    return GroqLLM(model=llm_config.get("model", "llama-3.3-70b-versatile"))


def get_cors_origins() -> list[str]:
    """Get CORS origins from config."""
    config = load_config()
    return config.get("api", {}).get("cors_origins", [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ])
