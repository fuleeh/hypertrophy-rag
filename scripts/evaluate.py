"""RAGAS evaluation script for the Hypertrophy RAG system."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from datasets import Dataset

from hypertrophy_rag.index.vectordb import VectorDB
from hypertrophy_rag.retrieval.rag import query_rag


TEST_QUESTIONS = [
    {
        "question": "How many sets per muscle per week are optimal for hypertrophy?",
        "ground_truth": "Research suggests 10-20 sets per muscle group per week for most lifters, with diminishing returns beyond 20 sets.",
    },
    {
        "question": "What rep range is best for muscle growth?",
        "ground_truth": "Hypertrophy can be achieved across a wide rep range (5-30 reps), as long as sets are taken close to failure. The 6-12 rep range is commonly used but not strictly necessary.",
    },
    {
        "question": "How much protein do I need for muscle growth?",
        "ground_truth": "1.6-2.2 g/kg body weight per day is recommended for maximizing muscle protein synthesis and hypertrophy.",
    },
    {
        "question": "Does creatine supplementation help with muscle growth?",
        "ground_truth": "Creatine monohydrate is one of the most well-researched supplements. It can increase lean body mass, strength, and training capacity when combined with resistance training.",
    },
    {
        "question": "What is the optimal training frequency for hypertrophy?",
        "ground_truth": "Training each muscle group 2-3 times per week is generally superior to once per week for hypertrophy, as it allows for more frequent stimulation of muscle protein synthesis.",
    },
    {
        "question": "How important is progressive overload for muscle growth?",
        "ground_truth": "Progressive overload is fundamental. Without gradually increasing mechanical tension over time, hypertrophy adaptations will plateau.",
    },
    {
        "question": "Does sleep quality affect muscle recovery and growth?",
        "ground_truth": "Adequate sleep (7-9 hours) is crucial for recovery, hormone regulation (growth hormone, testosterone), and muscle protein synthesis. Poor sleep impairs hypertrophy.",
    },
    {
        "question": "Are eccentric training phases beneficial for hypertrophy?",
        "ground_truth": "Eccentric training can produce greater muscle damage and may lead to enhanced hypertrophy when controlled. Slow eccentrics (3-5 seconds) are effective.",
    },
    {
        "question": "How do rest periods between sets affect hypertrophy?",
        "ground_truth": "Rest periods of 1-2 minutes are commonly used for hypertrophy, but longer rests (2-3 minutes) may allow for greater volume load and potentially better hypertrophy outcomes.",
    },
    {
        "question": "What role does metabolic stress play in muscle hypertrophy?",
        "ground_truth": "Metabolic stress (the pump) is one of the three mechanisms of hypertrophy alongside mechanical tension and muscle damage. Techniques like blood flow restriction can enhance metabolic stress.",
    },
]


def run_evaluation():
    """Run RAGAS evaluation on test questions."""
    config_path = PROJECT_ROOT / "config.yaml"
    import yaml
    config = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}
    chroma_config = config.get("chroma", {})

    db = VectorDB(
        collection_name=chroma_config.get("collection_name", "hypertrophy_papers"),
        persist_directory=str(PROJECT_ROOT / chroma_config.get("persist_directory", "data/chroma")),
    )

    stats = db.get_stats()
    print(f"Index stats: {stats['total_chunks']} chunks, {stats.get('total_papers', 'N/A')} papers")

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    for i, item in enumerate(TEST_QUESTIONS):
        print(f"\n[{i+1}/{len(TEST_QUESTIONS)}] {item['question'][:80]}...")
        result = query_rag(
            question=item["question"],
            vectordb=db,
            top_k=5,
        )

        questions.append(item["question"])
        answers.append(result.answer)
        contexts.append([s.title + ". " + " ".join(s.key_findings) for s in result.studies[:3]])
        ground_truths.append(item["ground_truth"])

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    print("\nRunning RAGAS evaluation...")
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    print("\n" + "=" * 60)
    print("RAGAS Evaluation Results")
    print("=" * 60)
    print(f"Faithfulness:      {result['faithfulness']:.3f}")
    print(f"Answer Relevancy:  {result['answer_relevancy']:.3f}")
    print(f"Context Precision: {result['context_precision']:.3f}")
    print(f"Context Recall:    {result['context_recall']:.3f}")
    print("=" * 60)

    output_path = PROJECT_ROOT / "data" / "eval_results.json"
    with open(output_path, "w") as f:
        json.dump({
            "faithfulness": result["faithfulness"],
            "answer_relevancy": result["answer_relevancy"],
            "context_precision": result["context_precision"],
            "context_recall": result["context_recall"],
            "questions": questions,
            "answers": answers,
        }, f, indent=2)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    run_evaluation()
