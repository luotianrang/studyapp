from __future__ import annotations

from datetime import date, datetime, time

LEARNING_STATES = {
    "UNLEARNED": "UNLEARNED",
    "LEARNING": "LEARNING",
    "LEARNED": "LEARNED",
    "REVIEW_QUEUE": "REVIEW_QUEUE",
    "MASTERED": "MASTERED",
}

REVIEW_INTERVALS_DAYS = [1, 3, 7, 14, 30]


def _as_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_review_count(task: dict) -> int:
    review_state = dict(task.get("review_state") or {})
    return max(
        _safe_int(task.get("review_count")),
        _safe_int(review_state.get("review_count")),
        _safe_int(review_state.get("repetitions")),
    )


def infer_learning_state(task: dict, now: datetime | None = None) -> str:
    now = now or datetime.now()
    learning_metrics = dict(task.get("learning_metrics") or {})
    review_state = dict(task.get("review_state") or {})
    completion_rate = _safe_float(learning_metrics.get("completion_rate"), 0.0)
    mastery = max(0.0, min(1.0, _safe_float(task.get("mastery", review_state.get("mastery", 0.5)), 0.5)))
    review_count = _normalize_review_count(task)
    last_review_time = _as_datetime(review_state.get("last_review_time") or task.get("last_review_time"))
    next_review_time = _as_datetime(review_state.get("next_review_time"))
    next_interval_days = REVIEW_INTERVALS_DAYS[min(review_count, len(REVIEW_INTERVALS_DAYS) - 1)] if REVIEW_INTERVALS_DAYS else 1
    completed_interval_days = REVIEW_INTERVALS_DAYS[max(0, min(max(review_count - 1, 0), len(REVIEW_INTERVALS_DAYS) - 1))] if REVIEW_INTERVALS_DAYS else 1

    has_learning_history = completion_rate > 0.0 or review_count > 0 or last_review_time is not None or next_review_time is not None
    if not has_learning_history:
        return LEARNING_STATES["UNLEARNED"]

    if review_count >= len(REVIEW_INTERVALS_DAYS) and mastery >= 0.85:
        return LEARNING_STATES["MASTERED"]

    if next_review_time is not None and next_review_time <= now:
        return LEARNING_STATES["REVIEW_QUEUE"]

    if last_review_time is not None:
        days_since_last_review = max(0, (now - last_review_time).days)
        if review_count > 0 and days_since_last_review >= completed_interval_days:
            return LEARNING_STATES["REVIEW_QUEUE"]
        return LEARNING_STATES["LEARNED"]

    if review_count > 0 or next_review_time is not None:
        return LEARNING_STATES["LEARNED"]

    return LEARNING_STATES["LEARNED"]


def build_learning_state_machine(knowledge_points: list[dict], now: datetime | None = None) -> dict:
    now = now or datetime.now()
    ordered_points = sorted(
        (dict(item) for item in knowledge_points),
        key=lambda item: (
            int(item.get("book_id", 0) or 0),
            int(item.get("chapter_number", 0) or 0),
            int(item.get("order_index", 0) or 0),
            int(item.get("id", 0) or 0),
        ),
    )

    unlearned_store = []
    learned_store = []
    mastered_store = []

    for item in ordered_points:
        state = infer_learning_state(item, now=now)
        enriched = dict(item)
        enriched["learning_state"] = state
        enriched["chapter_key"] = (
            int(item.get("book_id", 0) or 0),
            int(item.get("chapter_number", 0) or 0),
        )
        enriched["sequence_key"] = (
            int(item.get("book_id", 0) or 0),
            int(item.get("chapter_number", 0) or 0),
            int(item.get("order_index", 0) or 0),
            int(item.get("id", 0) or 0),
        )

        if state == LEARNING_STATES["UNLEARNED"]:
            unlearned_store.append(enriched)
        elif state == LEARNING_STATES["MASTERED"]:
            mastered_store.append(enriched)
        else:
            learned_store.append(enriched)

    return {
        "unlearned_store": unlearned_store,
        "learned_store": learned_store,
        "mastered_store": mastered_store,
        "ordered_points": ordered_points,
    }


def get_review_intervals_for_task(task: dict, total_days: int, learning_day: int = 1) -> list[int]:
    if total_days <= 0:
        return []

    review_count = _normalize_review_count(task)
    remaining_intervals = REVIEW_INTERVALS_DAYS[review_count:]
    review_days = []
    for interval in remaining_intervals:
        review_day = learning_day + interval
        if review_day > total_days:
            break
        review_days.append(review_day)
    return review_days
