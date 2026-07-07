"""Output validation guardrails for the Hypertrophy RAG system."""

from __future__ import annotations

import re

from hypertrophy_rag.logging import get_logger
from hypertrophy_rag.models import ResearchAnswer

logger = get_logger("guardrails")

# Patterns that suggest hallucination
HALLUCINATION_PATTERNS = [
    r"study (?:by |conducted )?(?:found|showed|demonstrated) that",
    r"according to (?:a |the )?(?:recent |latest )?study",
    r"researchers (?:at|from|discovered|found)",
]

# Patterns for off-topic detection
OFF_TOPIC_PATTERNS = [
    r"(?i)medical advice",
    r"(?i)diagnos(?:e|is|ing)",
    r"(?i)treatment plan",
    r"(?i)medication",
    r"(?i)surgery",
    r"(?i)clinical patient",
]

# Valid DOI pattern
DOI_PATTERN = r"10\.\d{4,}/[^\s]+"

# Valid PMID pattern
PMID_PATTERN = r"\d{1,9}"


def validate_output(answer: ResearchAnswer) -> ResearchAnswer:
    """Validate and add warnings to the output."""
    warnings = []

    # Check for potential hallucinations - claims without study references
    if answer.studies:
        # Check if answer references studies not in the retrieved set
        for pattern in HALLUCINATION_PATTERNS:
            matches = re.findall(pattern, answer.answer, re.IGNORECASE)
            if matches:
                warnings.append(f"Potential reference to external study: '{matches[0]}'")

    # Check confidence vs specificity mismatch
    if answer.confidence == "high" and len(answer.studies) < 3:
        warnings.append("High confidence with fewer than 3 supporting studies")

    # Validate DOI/PMID format
    for study in answer.studies:
        if study.doi and not re.match(DOI_PATTERN, study.doi):
            warnings.append(f"Invalid DOI format: {study.doi}")
        if study.pmid and not re.match(PMID_PATTERN, study.pmid):
            warnings.append(f"Invalid PMID format: {study.pmid}")

    # Off-topic detection
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, answer.answer, re.IGNORECASE):
            warnings.append("Answer may contain medical advice - consider adding disclaimer")

    if warnings:
        logger.warning(f"Guardrails flagged {len(warnings)} issues", extra={"extra_data": {"warnings": warnings}})
        answer.conflicting_findings = (answer.conflicting_findings or "") + "\n\nWarnings: " + "; ".join(warnings)

    return answer
