from __future__ import annotations


def _safe_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_adaptive_priority(
    knowledge_point: dict,
    attention_score: float,
    spaced_repetition_factor: float,
    repetition_priority: float,
    learning_metrics: dict | None = None,
) -> dict:
    learning_metrics = learning_metrics or {}

    completion_rate = max(0.0, min(1.0, _safe_float(learning_metrics.get("completion_rate", 0.0), 0.0)))
    skip_rate = max(0.0, min(1.0, _safe_float(learning_metrics.get("skip_rate", 0.0), 0.0)))
    error_rate = max(0.0, min(1.0, _safe_float(learning_metrics.get("error_rate", 0.0), 0.0)))

    performance_factor = 1.0
    performance_factor *= 0.8 + completion_rate * 0.4
    performance_factor *= 1.0 - skip_rate * 0.35
    performance_factor *= 1.0 + error_rate * 0.45

    if knowledge_point.get("review_due"):
        performance_factor *= 1.05

    priority_score = attention_score * max(1.0, spaced_repetition_factor) * max(0.5, performance_factor)
    priority_score += max(0.0, repetition_priority - 1.0) * 0.35

    return {
        "performance_factor": round(performance_factor, 4),
        "priority_score": round(priority_score, 4),
    }
