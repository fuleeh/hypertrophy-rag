"""Shared utilities for the Hypertrophy RAG system."""

from __future__ import annotations


def assess_confidence(answer_text: str) -> str:
    """Assess confidence from the answer text using keyword heuristics."""
    low_indicators = [
        "limited evidence", "few studies", "unclear",
        "insufficient", "mixed evidence",
    ]
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
