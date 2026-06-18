from __future__ import annotations

from datetime import date, datetime, time, timedelta


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


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def calculate_spaced_repetition(
    knowledge_point: dict,
    review_state: dict | None = None,
    now: datetime | None = None,
    base_interval_days: int = 1,
) -> dict:
    review_state = review_state or {}
    now = now or datetime.now()

    review_count = max(
        _safe_int(review_state.get("review_count")),
        _safe_int(review_state.get("repetitions")),
    )
    interval_days = _safe_int(review_state.get("interval_days"), base_interval_days)
    last_review_time = _as_datetime(review_state.get("last_review_time") or review_state.get("last_review_date"))
    next_review_time = _as_datetime(review_state.get("next_review_time") or review_state.get("next_review_date"))

    if review_count <= 0:
        return {
            "next_review_time": None,
            "review_due": False,
            "repetition_priority": 1.0,
            "spaced_repetition_factor": 1.0,
            "review_count": 0,
        }

    if interval_days <= 0:
        interval_days = base_interval_days * (2 ** max(0, review_count - 1))

    if next_review_time is None and last_review_time is not None:
        next_review_time = last_review_time + timedelta(days=interval_days)

    if next_review_time is None:
        next_review_time = now + timedelta(days=interval_days)

    review_due = next_review_time <= now
    overdue_days = max(0.0, (now - next_review_time).total_seconds() / 86400) if review_due else 0.0
    normalized_overdue = min(2.0, overdue_days / max(1.0, float(interval_days)))
    last_quality = _safe_int(review_state.get("last_quality"), 4)
    quality_penalty = max(0.0, (3 - last_quality) * 0.15) if last_quality < 3 else 0.0

    repetition_priority = 1.0 + normalized_overdue + quality_penalty
    spaced_repetition_factor = 1.0 + (0.6 if review_due else 0.0) + normalized_overdue * 0.5 + quality_penalty

    return {
        "next_review_time": next_review_time.isoformat(),
        "review_due": review_due,
        "repetition_priority": round(repetition_priority, 4),
        "spaced_repetition_factor": round(spaced_repetition_factor, 4),
        "review_count": review_count,
    }
