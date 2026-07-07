"""Tool-using agent for the Hypertrophy RAG system."""

from __future__ import annotations

import json
import time

from hypertrophy_rag.agent.tools import TOOL_MAP, TOOLS
from hypertrophy_rag.logging import get_logger
from hypertrophy_rag.models import ResearchAnswer
from hypertrophy_rag.retrieval.base import LLMProvider
from hypertrophy_rag.retrieval.context import metadata_to_studies
from hypertrophy_rag.retrieval.prompts import AGENT_SYSTEM_PROMPT
from hypertrophy_rag.utils import assess_confidence

logger = get_logger("agent")


def _execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool by name with arguments."""
    tool_fn = TOOL_MAP.get(tool_name)
    if not tool_fn:
        return f"Unknown tool: {tool_name}"

    try:
        return tool_fn(**arguments)
    except Exception as e:
        logger.error(f"Tool execution failed: {tool_name} - {e}")
        return f"Error executing {tool_name}: {str(e)}"


def _collect_studies_from_tools(messages: list[dict]) -> list[dict]:
    """Extract study metadata from tool call results in the message history."""
    studies: list[dict] = []
    for msg in messages:
        if msg.get("role") != "tool":
            continue
        content = msg.get("content", "")
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                studies.extend(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    return studies


def run_agent(
    question: str,
    llm: LLMProvider,
    model: str = "",
    max_iterations: int = 5,
) -> ResearchAnswer:
    """Run the tool-using agent to answer a hypertrophy research question.

    Uses dependency injection — caller provides the LLM provider.
    """
    t0 = time.perf_counter()

    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Agent iteration {iteration}", extra={"extra_data": {"iteration": iteration}})

        response = llm.generate_with_tools(
            messages=messages,
            tools=TOOLS,
            model=model,
        )

        choice = response.choices[0]

        # If no tool calls, we have the final answer
        if not choice.message.tool_calls:
            answer_text = choice.message.content or ""

            all_study_data = _collect_studies_from_tools(messages)
            studies = metadata_to_studies(all_study_data)

            total_ms = (time.perf_counter() - t0) * 1000
            logger.info(
                "Agent completed",
                extra={"extra_data": {
                    "question": question[:100],
                    "iterations": iteration,
                    "tools_called": sum(1 for m in messages if m.get("role") == "tool"),
                    "studies_found": len(studies),
                    "total_ms": round(total_ms, 2),
                }},
            )

            return ResearchAnswer(
                question=question,
                answer=answer_text,
                studies=studies,
                confidence=assess_confidence(answer_text),
            )

        # Process tool calls
        messages.append(choice.message)

        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            logger.info(f"Tool call: {tool_name}", extra={"extra_data": {"tool": tool_name, "args": arguments}})
            result = _execute_tool(tool_name, arguments)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    # Max iterations reached
    return ResearchAnswer(
        question=question,
        answer=(
            "I've gathered as much information as possible, but couldn't "
            "complete the analysis within the allowed iterations. "
            "Please try rephrasing your question."
        ),
        confidence="low",
    )
