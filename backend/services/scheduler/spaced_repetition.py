from __future__ import annotations

from datetime import date, datetime, time

from .learning_state_machine import REVIEW_INTERVALS_DAYS


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
    next_review_time = _as_datetime(review_state.get("next_review_time") or review_state.get("next_review_date"))

    if last_review_time is None:
        next_interval_days = REVIEW_INTERVALS_DAYS[min(review_count, len(REVIEW_INTERVALS_DAYS) - 1)] if REVIEW_INTERVALS_DAYS else 1
        return {
            "last_review_time": None,
            "days_since_last_review": None,
            "review_count": review_count,
            "mastery": mastery,
            "review_score": 1.0,
            "next_review_time": None,
            "next_interval_days": next_interval_days,
        }

    days_since_last_review = max(0, (now - last_review_time).days)
    target_interval = REVIEW_INTERVALS_DAYS[min(review_count, len(REVIEW_INTERVALS_DAYS) - 1)] if REVIEW_INTERVALS_DAYS else 1
    overdue_days = max(0, days_since_last_review - target_interval)
    due_ratio = days_since_last_review / max(1, target_interval)
    review_score = max(0.1, 0.4 + due_ratio + overdue_days * 0.15)

    return {
        "last_review_time": last_review_time.isoformat(),
        "days_since_last_review": days_since_last_review,
        "review_count": review_count,
        "mastery": mastery,
        "review_score": round(review_score, 4),
        "next_review_time": next_review_time.isoformat() if next_review_time is not None else None,
        "next_interval_days": target_interval,
    }
