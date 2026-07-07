"""Tool-using agent for the Hypertrophy RAG system."""

from __future__ import annotations

import json
import os
import time

from groq import Groq

from hypertrophy_rag.agent.tools import TOOLS, TOOL_MAP, search_studies, get_paper_details, calculate_volume
from hypertrophy_rag.logging import get_logger
from hypertrophy_rag.models import ResearchAnswer, StudySummary

logger = get_logger("agent")

AGENT_SYSTEM_PROMPT = """You are HypertroHub, an expert hypertrophy research assistant. You have access to tools that let you search a research database, look up specific papers, and calculate training volume.

When answering questions:
1. Use the search_studies tool to find relevant research
2. Use get_paper_details to get more info on specific papers
3. Use calculate_volume to help with programming questions
4. Synthesize findings from multiple studies
5. Always cite your sources (PMID or title)
6. Be specific with statistics (percentages, p-values, sample sizes)
7. If studies conflict, present both sides
8. For medical questions, recommend consulting a professional

You can call multiple tools in sequence to gather comprehensive information before providing your answer."""


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


def run_agent(
    question: str,
    model: str = "llama-3.3-70b-versatile",
    max_iterations: int = 5,
) -> ResearchAnswer:
    """Run the tool-using agent to answer a hypertrophy research question.

    The agent can call tools multiple times to gather information before
    providing a final answer.
    """
    t0 = time.perf_counter()

    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return ResearchAnswer(
            question=question,
            answer="Error: GROQ_API_KEY not set in environment.",
            confidence="low",
        )

    client = Groq(api_key=groq_key)

    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    all_studies = []
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Agent iteration {iteration}", extra={"extra_data": {"iteration": iteration}})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=4096,
            temperature=0.3,
        )

        choice = response.choices[0]

        # If no tool calls, we have the final answer
        if not choice.message.tool_calls:
            answer_text = choice.message.content

            # Extract study summaries from tool results
            studies = []
            seen_titles = set()
            for study_data in all_studies:
                title = study_data.get("title", "")
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                findings_raw = study_data.get("key_findings", "")
                findings = [f.strip() for f in findings_raw.split("|") if f.strip()] if findings_raw else []

                studies.append(
                    StudySummary(
                        pmid=study_data.get("pmid"),
                        s2_id=study_data.get("id") if study_data.get("id", "").startswith("S2:") else None,
                        title=title,
                        authors=study_data.get("authors", ""),
                        year=study_data.get("year", 0),
                        journal=study_data.get("journal", ""),
                        doi=study_data.get("doi"),
                        citation_count=study_data.get("citation_count"),
                        sample_size=study_data.get("sample_size"),
                        duration=study_data.get("duration"),
                        key_findings=findings,
                    )
                )

            total_ms = (time.perf_counter() - t0) * 1000
            logger.info(
                f"Agent completed",
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
                confidence=_assess_confidence(answer_text),
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

            # Collect study data from search results
            if tool_name == "search_studies":
                try:
                    studies = json.loads(result)
                    if isinstance(studies, list):
                        all_studies.extend(studies)
                except json.JSONDecodeError:
                    pass

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    # Max iterations reached
    return ResearchAnswer(
        question=question,
        answer="I've gathered as much information as possible, but couldn't complete the analysis within the allowed iterations. Please try rephrasing your question.",
        confidence="low",
    )


def _assess_confidence(answer_text: str) -> str:
    """Simple heuristic to assess confidence from the answer text."""
    low_indicators = ["limited evidence", "few studies", "unclear", "insufficient", "mixed evidence"]
    high_indicators = ["strong evidence", "consistent findings", "meta-analysis", "systematic review", "multiple studies"]
    text_lower = answer_text.lower()
    low_count = sum(1 for ind in low_indicators if ind in text_lower)
    high_count = sum(1 for ind in high_indicators if ind in text_lower)
    if low_count > high_count:
        return "low"
    elif high_count > low_count:
        return "high"
    return "medium"
