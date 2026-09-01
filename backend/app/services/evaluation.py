"""
Retrieval evaluation utilities for testing embedding quality.

Measures recall@k for synthetic evaluation queries.
"""

import logging
from typing import List, Dict, Optional
import json
from pathlib import Path

from app.services.ai_engine import AIEngine
from app.db.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RetrievalEvaluator:
    """Evaluates retrieval quality against evaluation queries."""

    def __init__(self, ai_engine: Optional[AIEngine] = None, vector_store: Optional[VectorStore] = None):
        """
        Initialize evaluator.

        Args:
            ai_engine: AIEngine instance
            vector_store: VectorStore instance
        """
        self.ai_engine = ai_engine or AIEngine()
        self.vector_store = vector_store or VectorStore()

    def evaluate_query(
        self,
        query: str,
        expected_standard_ids: List[str],
        top_k: int = 10
    ) -> Dict[str, any]:
        """
        Evaluate a single query.

        Args:
            query: Query text
            expected_standard_ids: List of standard IDs that should be retrieved
            top_k: Number of results to retrieve

        Returns:
            Dictionary with evaluation metrics
        """
        # Embed query
        try:
            query_vector = self.ai_engine.embed(query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return {
                "query": query,
                "error": str(e),
                "recall_at_10": 0.0,
                "recall_at_5": 0.0,
            }

        # Search
        try:
            results = self.vector_store.search(query_vector, top_k=top_k)
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return {
                "query": query,
                "error": str(e),
                "recall_at_10": 0.0,
                "recall_at_5": 0.0,
            }

        # Extract retrieved IDs
        retrieved_ids = [r.standard_id for r in results]

        # Calculate recall metrics
        expected_set = set(expected_standard_ids)
        retrieved_set_5 = set(retrieved_ids[:5])
        retrieved_set_10 = set(retrieved_ids[:10])

        recall_at_5 = len(expected_set & retrieved_set_5) / len(expected_set) if expected_set else 0.0
        recall_at_10 = len(expected_set & retrieved_set_10) / len(expected_set) if expected_set else 0.0

        # Calculate MRR (Mean Reciprocal Rank)
        mrr = 0.0
        for i, standard_id in enumerate(retrieved_ids):
            if standard_id in expected_set:
                mrr = 1.0 / (i + 1)
                break

        return {
            "query": query,
            "expected_ids": expected_standard_ids,
            "retrieved_ids": retrieved_ids[:10],
            "recall_at_5": recall_at_5,
            "recall_at_10": recall_at_10,
            "mrr": mrr,
            "top_result_id": retrieved_ids[0] if retrieved_ids else None,
        }

    def evaluate_queries(
        self,
        eval_queries: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """
        Evaluate multiple queries.

        Args:
            eval_queries: List of dicts with 'query' and 'expected_standard_ids'

        Returns:
            Aggregated evaluation metrics
        """
        results = []
        recall_at_5_values = []
        recall_at_10_values = []
        mrr_values = []

        logger.info(f"Evaluating {len(eval_queries)} queries...")

        for eval_query in eval_queries:
            result = self.evaluate_query(
                eval_query["query"],
                eval_query.get("expected_standard_ids", [])
            )
            results.append(result)

            if "error" not in result:
                recall_at_5_values.append(result["recall_at_5"])
                recall_at_10_values.append(result["recall_at_10"])
                mrr_values.append(result["mrr"])

        # Calculate aggregates
        summary = {
            "total_queries": len(eval_queries),
            "successful_queries": len(results) - sum(1 for r in results if "error" in r),
            "mean_recall_at_5": sum(recall_at_5_values) / len(recall_at_5_values) if recall_at_5_values else 0.0,
            "mean_recall_at_10": sum(recall_at_10_values) / len(recall_at_10_values) if recall_at_10_values else 0.0,
            "mean_mrr": sum(mrr_values) / len(mrr_values) if mrr_values else 0.0,
            "results": results,
        }

        return summary


def load_evaluation_queries(file_path: str) -> List[Dict[str, any]]:
    """
    Load evaluation queries from JSON file.

    Expected format:
    [
        {
            "query": "query text",
            "expected_standard_ids": ["TEST-001", "TEST-002"]
        },
        ...
    ]

    Args:
        file_path: Path to JSON file

    Returns:
        List of evaluation query dictionaries
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_evaluation_summary(summary: Dict[str, any]) -> None:
    """Print evaluation summary in human-readable format."""
    print("\n" + "="*60)
    print("RETRIEVAL EVALUATION SUMMARY")
    print("="*60)
    print(f"Total queries: {summary['total_queries']}")
    print(f"Successful queries: {summary['successful_queries']}")
    print(f"\nMean Recall@5: {summary['mean_recall_at_5']:.3f}")
    print(f"Mean Recall@10: {summary['mean_recall_at_10']:.3f}")
    print(f"Mean MRR: {summary['mean_mrr']:.3f}")
    print("="*60 + "\n")

    # Print per-query results
    print("PER-QUERY RESULTS:")
    for result in summary['results']:
        if "error" not in result:
            print(f"\nQuery: {result['query'][:60]}...")
            print(f"  Recall@5: {result['recall_at_5']:.3f}")
            print(f"  Recall@10: {result['recall_at_10']:.3f}")
            print(f"  MRR: {result['mrr']:.3f}")
            print(f"  Top result: {result.get('top_result_id', 'None')}")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python eval.py <eval_queries_file.json>")
        sys.exit(1)

    eval_file = sys.argv[1]

    if not Path(eval_file).exists():
        print(f"File not found: {eval_file}")
        sys.exit(1)

    # Load queries
    eval_queries = load_evaluation_queries(eval_file)

    # Run evaluation
    evaluator = RetrievalEvaluator()
    summary = evaluator.evaluate_queries(eval_queries)

    # Print summary
    print_evaluation_summary(summary)
