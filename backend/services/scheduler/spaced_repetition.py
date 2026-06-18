from __future__ import annotations

from datetime import date, datetime, time


def _as_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def calculate_spaced_repetition(
    knowledge_point: dict,
    review_state: dict | None = None,
    now: datetime | None = None,
) -> dict:
    review_state = review_state or {}
    now = now or datetime.now()

    last_review_time = _as_datetime(review_state.get("last_review_time") or review_state.get("last_review_date"))
    review_count = max(
        _safe_int(review_state.get("review_count")),
        _safe_int(review_state.get("repetitions")),
    )
    mastery = _safe_float(review_state.get("mastery"), 0.5)
    mastery = max(0.0, min(1.0, mastery))

    if last_review_time is None:
        return {
            "last_review_time": None,
            "days_since_last_review": None,
            "review_count": review_count,
            "mastery": mastery,
            "review_score": 1.0,
        }

    days_since_last_review = max(0, (now - last_review_time).days)
    review_score = (1 / (days_since_last_review + 1)) * (1 + review_count * 0.1)

    return {
        "last_review_time": last_review_time.isoformat(),
        "days_since_last_review": days_since_last_review,
        "review_count": review_count,
        "mastery": mastery,
        "review_score": round(review_score, 4),
    }
