#!/usr/bin/env python3
"""
ir-metrics.py - Information Retrieval Metrics for aOa Benchmarks

Calculates:
- Hit Rate@K: Did at least one predicted file get used?
- MRR (Mean Reciprocal Rank): How quickly does first relevant file appear?
- NDCG@K: How well-ordered is the full list?
- Precision@K / Recall@K: What % of predictions were correct?

Usage:
    python3 ir-metrics.py --fixtures fixtures/synthetic-sessions.jsonl --url http://localhost:8080
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

# Colors for terminal output
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"  # No Color


def fetch_predictions(url: str, tags: list[str], limit: int = 10) -> list[str]:
    """Fetch ranked predictions from aOa /rank endpoint."""
    try:
        tag_param = ",".join(tags) if tags else ""
        endpoint = f"{url}/rank?tag={tag_param}&limit={limit}"

        req = Request(endpoint, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("files", [])
    except URLError as e:
        print(f"{YELLOW}Warning: Could not fetch predictions: {e}{NC}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        return []


def hit_rate_at_k(predictions: list[str], ground_truth: list[str], k: int = 10) -> float:
    """
    Hit Rate@K: 1 if at least one of the top-K predictions is in ground truth, else 0.
    """
    top_k = set(predictions[:k])
    relevant = set(ground_truth)
    return 1.0 if top_k & relevant else 0.0


def reciprocal_rank(predictions: list[str], ground_truth: list[str]) -> float:
    """
    Reciprocal Rank: 1/rank of the first relevant item.
    Returns 0 if no relevant item found.
    """
    relevant = set(ground_truth)
    for i, pred in enumerate(predictions, start=1):
        if pred in relevant:
            return 1.0 / i
    return 0.0


def precision_at_k(predictions: list[str], ground_truth: list[str], k: int = 10) -> float:
    """
    Precision@K: What fraction of top-K predictions are relevant?
    """
    top_k = predictions[:k]
    if not top_k:
        return 0.0
    relevant = set(ground_truth)
    hits = sum(1 for p in top_k if p in relevant)
    return hits / len(top_k)


def recall_at_k(predictions: list[str], ground_truth: list[str], k: int = 10) -> float:
    """
    Recall@K: What fraction of relevant items are in top-K predictions?
    """
    if not ground_truth:
        return 0.0
    top_k = set(predictions[:k])
    relevant = set(ground_truth)
    hits = len(top_k & relevant)
    return hits / len(relevant)


def dcg_at_k(relevances: list[float], k: int) -> float:
    """
    Discounted Cumulative Gain at K.
    relevances[i] = relevance score of item at position i
    """
    dcg = 0.0
    for i, rel in enumerate(relevances[:k], start=1):
        dcg += rel / math.log2(i + 1)
    return dcg


def ndcg_at_k(predictions: list[str], ground_truth: list[str], k: int = 10) -> float:
    """
    Normalized DCG@K: DCG normalized by ideal DCG.
    Binary relevance: 1 if in ground truth, 0 otherwise.
    """
    relevant = set(ground_truth)

    # Actual relevances based on predictions
    relevances = [1.0 if p in relevant else 0.0 for p in predictions[:k]]

    # Ideal relevances (all relevant items first)
    ideal_relevances = [1.0] * min(len(relevant), k)

    actual_dcg = dcg_at_k(relevances, k)
    ideal_dcg = dcg_at_k(ideal_relevances, k)

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg


def evaluate_session(session: dict, url: str, k: int = 10) -> dict:
    """
    Evaluate a single session against aOa predictions.
    """
    # Extract tags from the session events
    all_tags = set()
    for event in session.get("events", []):
        all_tags.update(event.get("tags", []))

    # Get ground truth files
    ground_truth = session.get("ground_truth", [])

    # Fetch predictions from aOa
    predictions = fetch_predictions(url, list(all_tags), limit=k)

    return {
        "session": session.get("session", "unknown"),
        "hit_rate": hit_rate_at_k(predictions, ground_truth, k),
        "mrr": reciprocal_rank(predictions, ground_truth),
        "precision": precision_at_k(predictions, ground_truth, k),
        "recall": recall_at_k(predictions, ground_truth, k),
        "ndcg": ndcg_at_k(predictions, ground_truth, k),
        "predictions": predictions[:k],
        "ground_truth": ground_truth,
    }


def run_evaluation(fixtures_path: str, url: str, k: int = 10) -> dict:
    """
    Run evaluation on all sessions in the fixtures file.
    """
    sessions = []

    with open(fixtures_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                sessions.append(json.loads(line))

    if not sessions:
        print(f"{RED}No sessions found in fixtures file{NC}")
        return {}

    results = []
    for session in sessions:
        result = evaluate_session(session, url, k)
        results.append(result)

    # Aggregate metrics
    n = len(results)
    aggregate = {
        "hit_rate": sum(r["hit_rate"] for r in results) / n,
        "mrr": sum(r["mrr"] for r in results) / n,
        "precision": sum(r["precision"] for r in results) / n,
        "recall": sum(r["recall"] for r in results) / n,
        "ndcg": sum(r["ndcg"] for r in results) / n,
    }

    return {
        "k": k,
        "num_sessions": n,
        "aggregate": aggregate,
        "per_session": results,
    }


def print_results(results: dict, k: int):
    """Print formatted results to terminal."""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              IR Metrics Evaluation Results                   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    if not results:
        print(f"{RED}No results to display{NC}")
        return

    agg = results.get("aggregate", {})

    print(f"  {BOLD}Sessions evaluated:{NC} {results.get('num_sessions', 0)}")
    print(f"  {BOLD}K (top-K):{NC} {k}")
    print()

    print("  ┌─────────────────┬────────────┬────────────┐")
    print("  │ Metric          │ Value      │ Target     │")
    print("  ├─────────────────┼────────────┼────────────┤")

    metrics = [
        ("Hit Rate@K", agg.get("hit_rate", 0), 0.40),
        ("MRR", agg.get("mrr", 0), 0.25),
        ("Precision@K", agg.get("precision", 0), 0.30),
        ("Recall@K", agg.get("recall", 0), 0.50),
        ("NDCG@K", agg.get("ndcg", 0), 0.40),
    ]

    for name, value, target in metrics:
        color = GREEN if value >= target else RED
        status = "✓" if value >= target else "✗"
        print(f"  │ {name:<15} │ {color}{value:>10.3f}{NC} │ {target:>10.2f} │ {color}{status}{NC}")

    print("  └─────────────────┴────────────┴────────────┘")
    print()

    # Per-session breakdown
    print(f"  {BOLD}Per-Session Results:{NC}")
    print()

    for r in results.get("per_session", []):
        session_name = r.get("session", "unknown")
        hit = "✓" if r["hit_rate"] > 0 else "✗"
        color = GREEN if r["hit_rate"] > 0 else RED
        print(f"    {color}{hit}{NC} {session_name}: MRR={r['mrr']:.2f}, NDCG={r['ndcg']:.2f}")

    print()


def save_results(results: dict, output_dir: Path):
    """Save results to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    output_file = output_dir / f"{today}-ir-metrics.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="IR Metrics Evaluation for aOa")
    parser.add_argument("--fixtures", required=True, help="Path to fixtures JSONL file")
    parser.add_argument("--url", default="http://localhost:8080", help="aOa API URL")
    parser.add_argument("--k", type=int, default=10, help="Top-K for evaluation")
    parser.add_argument("--output", help="Output directory for results")

    args = parser.parse_args()

    # Check fixtures file exists
    if not Path(args.fixtures).exists():
        print(f"{RED}Fixtures file not found: {args.fixtures}{NC}")
        sys.exit(1)

    print()
    print(f"{CYAN}Running IR Metrics Evaluation{NC}")
    print(f"  Fixtures: {args.fixtures}")
    print(f"  API URL:  {args.url}")
    print(f"  K:        {args.k}")

    # Run evaluation
    results = run_evaluation(args.fixtures, args.url, args.k)

    # Print results
    print_results(results, args.k)

    # Save results if output directory specified
    if args.output:
        save_results(results, Path(args.output))
    else:
        # Default to results directory
        script_dir = Path(__file__).parent.parent
        save_results(results, script_dir / "results")

    # Exit with failure if targets not met
    agg = results.get("aggregate", {})
    if agg.get("hit_rate", 0) < 0.40 or agg.get("mrr", 0) < 0.25:
        print(f"{YELLOW}IR metrics below target. This is expected before implementation.{NC}")
        sys.exit(1)

    print(f"{GREEN}All IR metrics meet targets!{NC}")
    sys.exit(0)


if __name__ == "__main__":
    main()
