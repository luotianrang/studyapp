from __future__ import annotations


def _safe_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_difficulty(value) -> float:
    difficulty = _safe_float(value, 0.5)
    if difficulty <= 1:
        return max(0.0, min(5.0, difficulty * 5))
    return max(0.0, min(5.0, difficulty))


def calculate_attention_score(knowledge_point: dict, learning_metrics: dict | None = None) -> dict:
    learning_metrics = learning_metrics or {}

    importance = max(0.0, min(5.0, _safe_float(knowledge_point.get("importance", 3), 3.0)))
    difficulty = _normalize_difficulty(knowledge_point.get("difficulty", 0.5))
    error_rate = max(0.0, min(1.0, _safe_float(learning_metrics.get("error_rate", 0.0), 0.0)))
    error_component = error_rate * 5

    attention_score = importance * 0.5 + difficulty * 0.3 + error_component * 0.2

    return {
        "attention_score": round(attention_score, 4),
        "importance_component": round(importance, 4),
        "difficulty_component": round(difficulty, 4),
        "error_component": round(error_component, 4),
    }
