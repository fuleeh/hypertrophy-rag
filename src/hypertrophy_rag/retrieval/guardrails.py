"""Output validation guardrails for the Hypertrophy RAG system.

Verifies that the LLM's answer is actually supported by the retrieved context.
"""

from __future__ import annotations

import re

from hypertrophy_rag.logging import get_logger
from hypertrophy_rag.models import ResearchAnswer

logger = get_logger("guardrails")

# Patterns that suggest the LLM is fabricating external references
HALLUCINATION_PATTERNS = [
    r"study (?:by |conducted )?(?:found|showed|demonstrated) that",
    r"according to (?:a |the )?(?:recent |latest )?study",
    r"researchers (?:at|from|discovered|found)",
    r"it (?:has |was )?been (?:shown|demonstrated|proven|established)",
    r"the evidence (?:clearly |strongly )?(?:shows|suggests|indicates)",
]

# Off-topic / medical advice patterns
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

# Patterns to extract statistics from answer text
STAT_PATTERN = re.compile(
    r"(?:\d+(?:\.\d+)?)\s*(?:%|kg|lbs?|reps?|sets?|weeks?|months?|days?|years?)",
    re.IGNORECASE,
)

P_VALUE_PATTERN = re.compile(
    r"p\s*[<>=]+\s*0?\.\d+",
    re.IGNORECASE,
)


def _extract_statistics(text: str) -> list[str]:
    """Extract statistical claims from text."""
    stats = STAT_PATTERN.findall(text)
    stats.extend(P_VALUE_PATTERN.findall(text))
    return stats


def _verify_statistics_against_context(
    answer_text: str,
    context: str,
) -> list[str]:
    """Check if statistics in the answer can be found in the context."""
    warnings = []
    answer_stats = _extract_statistics(answer_text)

    for stat in answer_stats:
        # Check if the stat (or close variant) appears in context
        stat_clean = stat.strip().lower()
        if stat_clean not in context.lower():
            # Try without trailing space/period
            stat_base = stat_clean.rstrip(".")
            if stat_base not in context.lower():
                warnings.append(f"Statistic '{stat}' in answer not found in retrieved context")

    return warnings


def _check_confidence_vs_evidence(
    confidence: str,
    study_count: int,
    total_sample_size: int,
) -> list[str]:
    """Warn if confidence doesn't match the evidence strength."""
    warnings = []

    if confidence == "high":
        if study_count < 3:
            studies_word = "study" if study_count == 1 else "studies"
            warnings.append(
                f"High confidence claimed with only {study_count} {studies_word} — "
                "consider lowering to medium"
            )
        if total_sample_size < 50:
            warnings.append(
                f"High confidence claimed with only {total_sample_size} total participants — "
                "small sample sizes reduce certainty"
            )

    if confidence == "medium" and study_count < 2:
        warnings.append(
            f"Medium confidence with only {study_count} study — "
            "single studies should be treated as preliminary"
        )

    return warnings


def _check_for_vague_claims(answer_text: str) -> list[str]:
    """Flag vague or unsupported claims."""
    warnings = []
    vague_patterns = [
        (r"(?:most|many|several|numerous) studies (?:show|suggest|indicate|found)",
         "Vague reference to 'most/many studies' without specific citations"),
        (r"(?:experts|researchers) (?:agree|believe|think|suggest)",
         "Vague appeal to 'experts' without specific citations"),
        (r"(?:proven|established|settled|definitive)",
         "Strong claim of 'proven/established' — science is rarely this certain"),
    ]

    for pattern, msg in vague_patterns:
        if re.search(pattern, answer_text, re.IGNORECASE):
            warnings.append(msg)

    return warnings


def validate_output(
    answer: ResearchAnswer,
    context: str = "",
) -> ResearchAnswer:
    """Validate the answer against the retrieved context.

    Args:
        answer: The RAG answer to validate.
        context: The context string that was sent to the LLM.
    """
    warnings = []

    # 1. Check for hallucinated external references
    if answer.studies:
        for pattern in HALLUCINATION_PATTERNS:
            matches = re.findall(pattern, answer.answer, re.IGNORECASE)
            if matches:
                warnings.append(f"Potential hallucination: '{matches[0]}'")

    # 2. Verify statistics against context
    if context:
        warnings.extend(_verify_statistics_against_context(answer.answer, context))

    # 3. Check confidence vs evidence
    total_sample = 0
    for s in answer.studies:
        if s.sample_size and s.sample_size.isdigit():
            total_sample += int(s.sample_size)
    warnings.extend(_check_confidence_vs_evidence(
        answer.confidence, len(answer.studies), total_sample,
    ))

    # 4. Flag vague claims
    warnings.extend(_check_for_vague_claims(answer.answer))

    # 5. Off-topic detection
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, answer.answer, re.IGNORECASE):
            warnings.append("Answer may contain medical advice — consider adding disclaimer")

    # 6. Validate DOI/PMID format
    for study in answer.studies:
        if study.doi and not re.match(DOI_PATTERN, study.doi):
            warnings.append(f"Invalid DOI format: {study.doi}")
        if study.pmid and not re.match(PMID_PATTERN, study.pmid):
            warnings.append(f"Invalid PMID format: {study.pmid}")

    if warnings:
        logger.warning(
            f"Guardrails flagged {len(warnings)} issues",
            extra={"extra_data": {"warnings": warnings, "question": answer.question[:100]}},
        )
        warning_text = "\n\n⚠️ Confidence warnings: " + "; ".join(warnings)
        answer.conflicting_findings = (answer.conflicting_findings or "") + warning_text

    return answer
