"""Tools for the hypertrophy RAG agent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hypertrophy_rag.index.vectordb import VectorDB  # noqa: E402
from hypertrophy_rag.logging import get_logger  # noqa: E402

logger = get_logger("agent.tools")


def get_vectordb() -> VectorDB:
    """Get the vector database instance."""
    import yaml
    config_path = PROJECT_ROOT / "config.yaml"
    config = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}
    chroma_config = config.get("chroma", {})
    return VectorDB(
        collection_name=chroma_config.get("collection_name", "hypertrophy_papers"),
        persist_directory=str(PROJECT_ROOT / chroma_config.get("persist_directory", "data/chroma")),
    )


def search_studies(query: str, top_k: int = 5) -> str:
    """Search the hypertrophy research index for relevant studies."""
    db = get_vectordb()
    results = db.search(query, top_k=top_k)

    if not results:
        return "No studies found matching your query."

    studies = []
    for r in results:
        meta = r["metadata"]
        studies.append({
            "title": meta.get("paper_title", "Unknown"),
            "authors": meta.get("paper_authors", "Unknown"),
            "year": meta.get("paper_year", "Unknown"),
            "journal": meta.get("paper_journal", "Unknown"),
            "pmid": meta.get("paper_pmid"),
            "doi": meta.get("paper_doi"),
            "citation_count": meta.get("paper_citation_count"),
            "sample_size": meta.get("sample_size"),
            "duration": meta.get("duration"),
            "key_findings": meta.get("key_findings", ""),
            "relevance_score": round(r.get("distance", 0), 3),
        })

    return json.dumps(studies, indent=2)


def get_paper_details(paper_id: str) -> str:
    """Get detailed information about a specific paper by PMID or DOI."""
    from hypertrophy_rag.ingestion.parser import load_papers

    papers = load_papers(str(PROJECT_ROOT / "data" / "papers"))

    # Search by PMID
    for paper in papers.values():
        if paper.pmid == paper_id or paper.id == paper_id:
            return json.dumps(paper.to_dict(), indent=2)

    # Search by DOI
    for paper in papers.values():
        if paper.doi and paper.doi.lower() == paper_id.lower():
            return json.dumps(paper.to_dict(), indent=2)

    return f"Paper '{paper_id}' not found in the index."


def calculate_volume(
    sets: int = 0,
    reps: int = 0,
    weight_kg: float = 0.0,
    weight_lbs: float = 0.0,
    rpe: float = 0.0,
) -> str:
    """Calculate training volume and provide programming insights.

    Args:
        sets: Number of sets
        reps: Reps per set
        weight_kg: Weight in kilograms
        weight_lbs: Weight in pounds
        rpe: Rate of Perceived Exertion (1-10)

    Returns:
        Training volume analysis and recommendations
    """
    # Convert lbs to kg if needed
    if weight_lbs > 0 and weight_kg == 0:
        weight_kg = weight_lbs * 0.453592

    total_sets = sets
    total_reps = sets * reps if sets and reps else 0
    total_volume = total_reps * weight_kg if total_reps and weight_kg else 0

    # Estimate 1RM using Epley formula
    estimated_1rm = 0
    if weight_kg and reps and reps <= 10:
        estimated_1rm = weight_kg * (1 + reps / 30)

    result = {
        "total_sets": total_sets,
        "total_reps": total_reps,
        "total_volume_kg": round(total_volume, 1),
        "estimated_1rm_kg": round(estimated_1rm, 1) if estimated_1rm else None,
    }

    # Programming recommendations based on research
    recommendations = []
    if total_sets > 0:
        if total_sets < 10:
            recommendations.append("Below minimum effective volume (10 sets/week). Consider adding more sets.")
        elif total_sets <= 20:
            recommendations.append("Within the hypertrophy range (10-20 sets/week). Good volume.")
        else:
            recommendations.append("Above 20 sets/week. May need deload weeks. Monitor for overreaching.")

    if rpe > 0:
        if rpe >= 9:
            recommendations.append("Very high intensity. Ensure adequate recovery between sessions.")
        elif rpe >= 7:
            recommendations.append("Moderate-high intensity. Good for hypertrophy training.")
        elif rpe < 5:
            recommendations.append("Low intensity. Consider increasing load for better hypertrophy stimulus.")

    if reps:
        if reps <= 5:
            recommendations.append("Low rep range. Primarily strength-focused. Consider adding moderate-rep work.")
        elif reps <= 12:
            recommendations.append("Moderate rep range. Well-suited for hypertrophy.")
        elif reps <= 30:
            recommendations.append("High rep range. Can be effective for hypertrophy when taken close to failure.")

    result["recommendations"] = recommendations

    return json.dumps(result, indent=2)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_studies",
            "description": (
                "Search the hypertrophy research index "
                "for relevant studies. Returns study titles, "
                "authors, findings, and metadata."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for hypertrophy research"},
                    "top_k": {"type": "integer", "description": "Number of results to return", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_paper_details",
            "description": "Get detailed information about a specific paper by PMID or DOI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paper_id": {"type": "string", "description": "PMID or DOI of the paper"},
                },
                "required": ["paper_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_volume",
            "description": "Calculate training volume and provide programming insights based on research.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sets": {"type": "integer", "description": "Number of sets"},
                    "reps": {"type": "integer", "description": "Reps per set"},
                    "weight_kg": {"type": "number", "description": "Weight in kilograms"},
                    "weight_lbs": {"type": "number", "description": "Weight in pounds"},
                    "rpe": {"type": "number", "description": "Rate of Perceived Exertion (1-10)"},
                },
            },
        },
    },
]

TOOL_MAP = {
    "search_studies": search_studies,
    "get_paper_details": get_paper_details,
    "calculate_volume": calculate_volume,
}
