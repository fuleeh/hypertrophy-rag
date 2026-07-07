"""Tests for guardrails — hallucination detection and stat verification."""

from __future__ import annotations

from hypertrophy_rag.models import ResearchAnswer, StudySummary
from hypertrophy_rag.retrieval.guardrails import (
    _check_confidence_vs_evidence,
    _check_for_vague_claims,
    _extract_statistics,
    _verify_statistics_against_context,
    validate_output,
)

# --- _extract_statistics ---


def test_extract_statistics_percentages():
    stats = _extract_statistics("Participants gained 2.5% more muscle")
    assert len(stats) == 1
    assert "2.5%" in stats[0]


def test_extract_statistics_kg():
    stats = _extract_statistics("Increased by 3.2 kg over 8 weeks")
    assert len(stats) >= 1


def test_extract_statistics_p_value():
    stats = _extract_statistics("The difference was significant (p < 0.05)")
    assert any("p" in s for s in stats)


def test_extract_statistics_none_found():
    stats = _extract_statistics("No numbers here at all")
    assert stats == []


# --- _verify_statistics_against_context ---


def test_verify_stats_present_in_context():
    warnings = _verify_statistics_against_context(
        answer_text="The study found a 15% increase in muscle mass",
        context="Participants showed a 15% increase in muscle mass after 12 weeks",
    )
    assert warnings == []


def test_verify_stats_missing_from_context():
    warnings = _verify_statistics_against_context(
        answer_text="The study found a 47% increase in muscle mass",
        context="Participants showed a 15% increase in muscle mass after 12 weeks",
    )
    assert len(warnings) == 1
    assert "47%" in warnings[0]


def test_verify_stats_no_numbers():
    warnings = _verify_statistics_against_context(
        answer_text="The studies suggest benefits",
        context="Evidence supports training volume",
    )
    assert warnings == []


# --- _check_confidence_vs_evidence ---


def test_high_confidence_few_studies():
    warnings = _check_confidence_vs_evidence("high", study_count=1, total_sample_size=200)
    assert any("1 study" in w for w in warnings)


def test_high_confidence_small_samples():
    warnings = _check_confidence_vs_evidence("high", study_count=5, total_sample_size=30)
    assert any("30 total participants" in w for w in warnings)


def test_high_confidence_ok():
    warnings = _check_confidence_vs_evidence("high", study_count=5, total_sample_size=200)
    assert warnings == []


def test_medium_confidence_single_study():
    warnings = _check_confidence_vs_evidence("medium", study_count=1, total_sample_size=100)
    assert any("only 1 study" in w for w in warnings)


def test_low_confidence_no_warnings():
    warnings = _check_confidence_vs_evidence("low", study_count=1, total_sample_size=10)
    assert warnings == []


# --- _check_for_vague_claims ---


def test_vague_most_studies():
    warnings = _check_for_vague_claims("Most studies show that volume matters")
    assert any("most/many studies" in w for w in warnings)


def test_vague_experts_agree():
    warnings = _check_for_vague_claims("Experts agree that protein is important")
    assert any("experts" in w for w in warnings)


def test_vague_proven():
    warnings = _check_for_vague_claims("This has been proven to work")
    assert any("proven/established" in w for w in warnings)


def test_no_vague_claims():
    warnings = _check_for_vague_claims(
        "A 2020 RCT with n=50 found a significant increase (p<0.05)"
    )
    assert warnings == []


# --- validate_output ---


def test_validate_output_clean():
    answer = ResearchAnswer(
        question="test",
        answer="The 2020 study (PMID: 12345) found a 15% increase",
        studies=[StudySummary(pmid="12345", title="Test")],
        confidence="medium",
    )
    result = validate_output(answer, context="15% increase in muscle mass")
    assert "Warnings" not in (result.conflicting_findings or "")


def test_validate_output_hallucination_pattern():
    answer = ResearchAnswer(
        question="test",
        answer="According to a recent study, this works well",
        studies=[StudySummary(pmid="12345", title="Test")],
        confidence="medium",
    )
    result = validate_output(answer)
    assert "hallucination" in (result.conflicting_findings or "").lower()


def test_validate_output_vague_claim():
    answer = ResearchAnswer(
        question="test",
        answer="Most studies show that training volume matters for growth",
        studies=[StudySummary(pmid="12345", title="Test")],
        confidence="medium",
    )
    result = validate_output(answer)
    assert "vague" in (result.conflicting_findings or "").lower()


def test_validate_output_stat_not_in_context():
    answer = ResearchAnswer(
        question="test",
        answer="The study found a 99% increase in muscle",
        studies=[StudySummary(pmid="12345", title="Test")],
        confidence="medium",
    )
    result = validate_output(answer, context="The study found a 15% increase")
    assert "99%" in (result.conflicting_findings or "")


def test_validate_output_high_confidence_low_evidence():
    answer = ResearchAnswer(
        question="test",
        answer="Definitively, this works",
        studies=[StudySummary(pmid="12345", title="Test")],
        confidence="high",
    )
    result = validate_output(answer)
    assert "high confidence" in (result.conflicting_findings or "").lower()
