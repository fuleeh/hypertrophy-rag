"""Tests for protocols and config module."""

from __future__ import annotations

from hypertrophy_rag.config import load_config
from hypertrophy_rag.index.vectordb import VectorDB
from hypertrophy_rag.retrieval.base import LLMProvider, Retriever
from hypertrophy_rag.retrieval.hybrid import HybridRetriever

# --- Retriever protocol ---


def test_vectordb_satisfies_retriever_protocol():
    assert isinstance(VectorDB.__new__(VectorDB), Retriever)


def test_hybrid_retriever_satisfies_retriever_protocol():
    assert isinstance(HybridRetriever.__new__(HybridRetriever), Retriever)


class FakeRetriever:
    def search(self, query, top_k=10, year_filter=None, source_filter=None):
        return []


def test_custom_class_satisfies_retriever_protocol():
    assert isinstance(FakeRetriever(), Retriever)


class NotARetriever:
    pass


def test_non_retriever_fails_protocol():
    assert not isinstance(NotARetriever(), Retriever)


# --- LLMProvider protocol ---


class FakeLLM:
    def generate(self, messages, model="", max_tokens=2048, temperature=0.3, **kwargs):
        return "response"


def test_custom_llm_satisfies_protocol():
    assert isinstance(FakeLLM(), LLMProvider)


# --- config module ---


def test_load_config_returns_dict():
    config = load_config()
    assert isinstance(config, dict)


def test_load_config_caches():
    from hypertrophy_rag import config

    config._config_cache = None
    first = config.load_config()
    second = config.load_config()
    assert first is second


def test_load_config_has_expected_keys():
    config = load_config()
    assert "llm" in config
    assert "chroma" in config
    assert "embedding" in config
