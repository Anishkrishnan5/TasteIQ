from __future__ import annotations

import math
from typing import Any


def precision_at_k(result_ids: list[int], judgments: dict[int, int], k: int) -> float:
    relevant = sum(judgments.get(item_id, 0) > 0 for item_id in result_ids[:k])
    return relevant / k


def recall_at_k(result_ids: list[int], judgments: dict[int, int], k: int) -> float:
    relevant_ids = {item_id for item_id, grade in judgments.items() if grade > 0}
    if not relevant_ids:
        return 0.0
    retrieved = set(result_ids[:k]) & relevant_ids
    return len(retrieved) / len(relevant_ids)


def reciprocal_rank_at_k(result_ids: list[int], judgments: dict[int, int], k: int) -> float:
    for rank, item_id in enumerate(result_ids[:k], start=1):
        if judgments.get(item_id, 0) > 0:
            return 1 / rank
    return 0.0


def _discounted_gain(grades: list[int]) -> float:
    return sum((2**grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(grades, 1))


def ndcg_at_k(result_ids: list[int], judgments: dict[int, int], k: int) -> float:
    actual = [judgments.get(item_id, 0) for item_id in result_ids[:k]]
    ideal = sorted(judgments.values(), reverse=True)[:k]
    ideal_gain = _discounted_gain(ideal)
    return _discounted_gain(actual) / ideal_gain if ideal_gain else 0.0


def constraint_violations(results: list[dict[str, Any]], filters: dict[str, float]) -> int:
    violations = 0
    for result in results:
        calories = result.get("calories")
        protein = result.get("protein_g")
        if "max_calories" in filters and (calories is None or calories > filters["max_calories"]):
            violations += 1
            continue
        if "min_protein" in filters and (protein is None or protein < filters["min_protein"]):
            violations += 1
    return violations
