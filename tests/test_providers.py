"""Tests for LLM providers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from hypertrophy_rag.retrieval.providers import GroqLLM


def test_groq_llm_init_default():
    llm = GroqLLM()
    assert llm.model == "llama-3.3-70b-versatile"


def test_groq_llm_init_custom_model():
    llm = GroqLLM(model="llama-3.1-8b")
    assert llm.model == "llama-3.1-8b"


def test_groq_llm_init_explicit_key():
    llm = GroqLLM(api_key="test-key-123")
    assert llm.api_key == "test-key-123"


@patch("hypertrophy_rag.retrieval.providers.Groq")
def test_groq_llm_generate(mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test answer"))]
    mock_client.chat.completions.create.return_value = mock_response

    llm = GroqLLM(api_key="test-key")
    result = llm.generate(
        messages=[{"role": "user", "content": "Hello"}],
        model="test-model",
    )

    assert result == "Test answer"
    mock_client.chat.completions.create.assert_called_once()


@patch("hypertrophy_rag.retrieval.providers.Groq")
def test_groq_llm_generate_with_tools(mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "search"
    mock_tool_call.function.arguments = '{"query": "test"}'
    mock_tool_call.id = "call_123"

    mock_message = MagicMock()
    mock_message.tool_calls = [mock_tool_call]
    mock_message.content = None

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response

    llm = GroqLLM(api_key="test-key")
    result = llm.generate_with_tools(
        messages=[{"role": "user", "content": "Hello"}],
        tools=[{"type": "function", "function": {"name": "search"}}],
    )

    assert result.choices[0].message.tool_calls[0].function.name == "search"


@patch("hypertrophy_rag.retrieval.providers.Groq")
def test_groq_llm_client_cached(mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    llm = GroqLLM(api_key="test-key")
    client1 = llm._get_client()
    client2 = llm._get_client()

    assert client1 is client2
    assert mock_groq_cls.call_count == 1
