"""Groq LLM provider implementation."""

from __future__ import annotations

import os

from groq import Groq

from hypertrophy_rag.logging import get_logger

logger = get_logger("llm.groq")


class GroqLLM:
    """Concrete LLM provider wrapping the Groq SDK."""

    def __init__(self, api_key: str | None = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.model = model
        self._client: Groq | None = None

    def _get_client(self) -> Groq:
        if self._client is None:
            self._client = Groq(api_key=self.api_key)
        return self._client

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        **kwargs,
    ) -> str:
        """Generate a response from messages."""
        client = self._get_client()
        response = client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def generate_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict],
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.3,
        tool_choice: str = "auto",
    ):
        """Generate a response that may include tool calls."""
        client = self._get_client()
        return client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            max_tokens=max_tokens,
            temperature=temperature,
        )
