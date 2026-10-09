"""Учебный пример логики отбора чанков без внешних зависимостей."""
import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Embedding dimensions differ")
    denominator = math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b))
    return sum(x*y for x, y in zip(a, b)) / denominator if denominator else 0.0


def top_k(scores: list[tuple[str, float]], k: int = 4):
    return sorted(scores, key=lambda item: item[1], reverse=True)[:k]
