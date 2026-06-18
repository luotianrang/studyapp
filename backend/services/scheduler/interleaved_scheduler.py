from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from ..review_scheduler import get_review_minutes
from .adaptive_scheduler import calculate_adaptive_priority
from .attention_model import calculate_attention_score
from .spaced_repetition import calculate_spaced_repetition

DEFAULT_DAILY_CAPACITY_MINUTES = 90
DEFAULT_TASK_MINUTES = 15
MIN_SESSION_MINUTES = 5
PREFERRED_MAX_SESSION_MINUTES = 35
MAX_REVIEW_DELAY_DAYS = 1


def _coerce_minutes(value: object, fallback: int) -> int:
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        minutes = fallback
    return max(1, minutes)


def _resolve_daily_capacity(daily_minutes: int) -> int:
    return max(MIN_SESSION_MINUTES, _coerce_minutes(daily_minutes, DEFAULT_DAILY_CAPACITY_MINUTES))


def _resolve_task_minutes(task: dict) -> int:
    return _coerce_minutes(task.get("estimated_minutes"), DEFAULT_TASK_MINUTES)


def _task_session_key(task: dict) -> tuple[int, str]:
    return (int(task.get("id", 0) or 0), str(task.get("item_type", "learning")))


def _balanced_session_lengths(total_minutes: int, max_session_minutes: int) -> list[int]:
    session_count = max(1, (total_minutes + max_session_minutes - 1) // max_session_minutes)
    base = total_minutes // session_count
    remainder = total_minutes % session_count
    sessions = [base + (1 if idx < remainder else 0) for idx in range(session_count)]
    target_min_session = min(MIN_SESSION_MINUTES, max_session_minutes)

    # Avoid a tiny trailing fragment by rebalancing into earlier sessions.
    if len(sessions) > 1 and sessions[-1] < target_min_session:
        deficit = target_min_session - sessions[-1]
        for idx in range(len(sessions) - 1):
            available = sessions[idx] - target_min_session
            if available <= 0:
                continue
            shift = min(deficit, available)
            sessions[idx] -= shift
            sessions[-1] += shift
            deficit -= shift
            if deficit <= 0:
                break

    return sessions


def _split_task_into_sessions(task: dict, daily_capacity: int) -> list[dict]:
    total_minutes = _resolve_task_minutes(task)
    is_review = _is_review_task(task)
    max_session_minutes = min(
        daily_capacity,
        total_minutes if is_review else max(MIN_SESSION_MINUTES, PREFERRED_MAX_SESSION_MINUTES),
    )
    max_session_minutes = max(MIN_SESSION_MINUTES, max_session_minutes)

    if total_minutes <= max_session_minutes:
        single_session = dict(task)
        single_session["estimated_minutes"] = total_minutes
        single_session["session_index"] = 1
        single_session["session_count"] = 1
        single_session["session_task_key"] = _task_session_key(task)
        return [single_session]

    sessions = []
    session_lengths = _balanced_session_lengths(total_minutes, max_session_minutes)
    session_count = len(session_lengths)

    for session_index, session_minutes in enumerate(session_lengths, start=1):
        session = dict(task)
        session["estimated_minutes"] = session_minutes
        session["session_index"] = session_index
        session["session_count"] = session_count
        session["session_task_key"] = _task_session_key(task)
        session["must_span_days"] = total_minutes > daily_capacity
        sessions.append(session)

    return sessions


def _fits_within_day(task: dict, remaining_capacity: int) -> bool:
    return _resolve_task_minutes(task) <= remaining_capacity


def _is_review_task(task: dict) -> bool:
    return task.get("item_type") == "review"


def _review_anchor_day(task: dict) -> int:
    try:
        return max(1, int(task.get("review_anchor_day", 1)))
    except (TypeError, ValueError):
        return 1


def _is_forced_review(task: dict, day_number: int) -> bool:
    if not _is_review_task(task):
        return False
    return (day_number - _review_anchor_day(task)) >= MAX_REVIEW_DELAY_DAYS


def _normalize_difficulty(task: dict) -> float:
    difficulty = task.get("difficulty")
    if difficulty is None:
        return 0.5
    try:
        return float(difficulty)
    except (TypeError, ValueError):
        return 0.5


def _normalize_importance(task: dict) -> float:
    try:
        return float(task.get("importance", 3))
    except (TypeError, ValueError):
        return 3.0


def _normalize_urgency(task: dict, total_days: int) -> float:
    urgency = task.get("urgency")
    if urgency is not None:
        try:
            return float(urgency)
        except (TypeError, ValueError):
            pass

    chapter_number = task.get("chapter_number", 0)
    order_index = task.get("order_index", 0)
    try:
        chapter_number = float(chapter_number)
    except (TypeError, ValueError):
        chapter_number = 0.0
    try:
        order_index = float(order_index)
    except (TypeError, ValueError):
        order_index = 0.0

    sequence_hint = max(1.0, chapter_number * 10 + order_index + 1)
    horizon = max(1.0, float(total_days))
    return min(5.0, 1.0 + sequence_hint / horizon)


def _build_learning_score(task: dict, total_days: int) -> tuple[float, dict, dict]:
    normalized = dict(task)
    normalized["difficulty"] = _normalize_difficulty(task)
    normalized["importance"] = _normalize_importance(task)
    normalized["urgency"] = _normalize_urgency(task, total_days)

    learning_metrics = dict(task.get("learning_metrics") or {})
    attention = calculate_attention_score(normalized, learning_metrics=learning_metrics)
    adaptive = calculate_adaptive_priority(
        normalized,
        attention_score=attention["attention_score"],
        spaced_repetition_factor=1.0,
        repetition_priority=1.0,
        learning_metrics=learning_metrics,
    )
    interleaved_score = (
        normalized["importance"] * 0.4
        + normalized["difficulty"] * 0.4
        + normalized["urgency"] * 0.2
    )
    learning_score = interleaved_score + attention["attention_score"]
    return round(learning_score, 4), attention, adaptive


def _should_create_study_item(task: dict) -> bool:
    learning_metrics = dict(task.get("learning_metrics") or {})
    completion_rate = float(learning_metrics.get("completion_rate", 0.0) or 0.0)
    mastery = float(task.get("mastery", 0.5) or 0.5)
    review_count = int(task.get("review_count", 0) or 0)
    return completion_rate < 1.0 or (review_count == 0 and mastery < 0.95)


def _should_create_review_item(task: dict) -> bool:
    review_count = int(task.get("review_count", 0) or 0)
    last_review_time = task.get("last_review_time")
    mastery = float(task.get("mastery", 0.5) or 0.5)
    return review_count > 0 or last_review_time is not None or mastery < 0.6


def _build_task_variant(task: dict, item_type: str, total_days: int, now: datetime) -> dict:
    variant = dict(task)
    sr = calculate_spaced_repetition(variant, review_state=variant.get("review_state"), now=now)
    learning_score, attention, adaptive = _build_learning_score(variant, total_days)

    variant.update(sr)
    variant.update(attention)
    variant.update(adaptive)
    variant["difficulty"] = _normalize_difficulty(task)
    variant["importance"] = _normalize_importance(task)
    variant["urgency"] = _normalize_urgency(task, total_days)
    variant["learning_score"] = learning_score
    variant["item_type"] = item_type
    variant["final_score"] = round(learning_score * 0.6 + sr["review_score"] * 0.4, 4)
    variant["score"] = round(variant["final_score"] + adaptive["priority_score"] * 0.05, 4)
    variant["estimated_minutes"] = _resolve_task_minutes(task)

    if item_type == "review":
        variant["estimated_minutes"] = get_review_minutes(variant.get("estimated_minutes", 10))
        days_since_last_review = variant.get("days_since_last_review")
        try:
            review_anchor_day = max(1, int(days_since_last_review or 1))
        except (TypeError, ValueError):
            review_anchor_day = 1
        variant["review_anchor_day"] = review_anchor_day
    return variant


def build_interleaved_tasks(knowledge_points: list[dict], total_days: int) -> list[dict]:
    tasks = []
    now = datetime.now()

    for kp in knowledge_points:
        base_task = dict(kp)
        base_task["book_id"] = kp.get("book_id", 0)

        review_snapshot = calculate_spaced_repetition(base_task, review_state=base_task.get("review_state"), now=now)
        base_task.update(review_snapshot)

        if _should_create_study_item(base_task):
            tasks.append(_build_task_variant(base_task, "learning", total_days, now))
        if _should_create_review_item(base_task):
            tasks.append(_build_task_variant(base_task, "review", total_days, now))

    tasks.sort(
        key=lambda item: (
            -item["score"],
            0 if item.get("item_type") == "review" else 1,
            -item.get("review_score", 0),
            -item.get("learning_score", 0),
            item.get("book_id", 0),
            item.get("chapter_number", 0),
            item.get("order_index", 0),
        )
    )
    return tasks


def build_scheduler_pipeline(knowledge_points: list[dict], total_days: int, daily_minutes: int) -> list[dict]:
    daily_capacity = _resolve_daily_capacity(daily_minutes)
    tasks = build_interleaved_tasks(knowledge_points, total_days)
    expanded_tasks = []
    for task in tasks:
        expanded_tasks.extend(_split_task_into_sessions(task, daily_capacity))
    expanded_tasks.sort(
        key=lambda item: (
            0 if item.get("item_type") == "review" else 1,
            -item["score"],
            0 if item.get("item_type") == "review" else 1,
            -item.get("review_score", 0),
            -item.get("learning_score", 0),
            item.get("book_id", 0),
            item.get("chapter_number", 0),
            item.get("order_index", 0),
            item.get("session_index", 1),
        )
    )
    return expanded_tasks


def _select_review_task_for_day(
    remaining_tasks: list[dict],
    day_total_minutes: int,
    daily_capacity: int,
    day_number: int,
    forced_only: bool = False,
) -> int | None:
    remaining_capacity = daily_capacity - day_total_minutes
    if remaining_capacity <= 0:
        return None

    for idx, task in enumerate(remaining_tasks):
        if not _is_review_task(task):
            continue
        if forced_only and not _is_forced_review(task, day_number):
            continue
        if not forced_only and _is_forced_review(task, day_number):
            continue
        if _fits_within_day(task, remaining_capacity):
            return idx

    return None


def _select_learning_task_for_day(
    remaining_tasks: list[dict],
    day_items: list[dict],
    day_total_minutes: int,
    daily_capacity: int,
    book_task_counts: dict[int, int],
    last_book_id: int | None,
) -> int | None:
    remaining_capacity = daily_capacity - day_total_minutes
    if remaining_capacity <= 0:
        return None

    existing_task_keys = {
        (item.get("knowledge_point_id", 0), item.get("item_type", "learning"))
        for item in day_items
    }

    for idx, task in enumerate(remaining_tasks):
        if _is_review_task(task):
            continue
        if task.get("session_task_key") in existing_task_keys and _fits_within_day(task, remaining_capacity):
            return idx

    candidate_sets = (
        lambda task: (
            _fits_within_day(task, remaining_capacity)
            and (task.get("item_type") == "review" or book_task_counts[task.get("book_id", 0)] < 2)
            and (task.get("item_type") == "review" or last_book_id is None or task.get("book_id", 0) != last_book_id)
        ),
        lambda task: (
            _fits_within_day(task, remaining_capacity)
            and (task.get("item_type") == "review" or book_task_counts[task.get("book_id", 0)] < 2)
        ),
        lambda task: _fits_within_day(task, remaining_capacity),
    )

    for rule in candidate_sets:
        for idx, task in enumerate(remaining_tasks):
            if _is_review_task(task):
                continue
            if rule(task):
                return idx

    if not day_items:
        for idx, task in enumerate(remaining_tasks):
            if _is_review_task(task):
                continue
            if _fits_within_day(task, remaining_capacity):
                return idx

    return None


def generate_interleaved_plan(knowledge_points: list[dict], total_days: int, daily_minutes: int, start_date=None):
    if start_date is None:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    if not knowledge_points or total_days <= 0 or daily_minutes <= 0:
        return []

    daily_capacity = _resolve_daily_capacity(daily_minutes)
    task_pool = build_scheduler_pipeline(knowledge_points, total_days, daily_minutes)
    daily_plan = []
    remaining_tasks = list(task_pool)
    day_number = 1

    while remaining_tasks:
        if day_number > total_days and not daily_plan:
            break

        day_items = []
        study_items = []
        review_items = []
        day_total_minutes = 0
        book_task_counts = defaultdict(int)
        last_book_id = None

        while remaining_tasks:
            selected_index = _select_review_task_for_day(
                remaining_tasks=remaining_tasks,
                day_total_minutes=day_total_minutes,
                daily_capacity=daily_capacity,
                day_number=day_number,
                forced_only=True,
            )
            if selected_index is None:
                break

            selected_task = remaining_tasks.pop(selected_index)
            selected_book_id = selected_task.get("book_id", 0)
            item_minutes = _resolve_task_minutes(selected_task)

            item_payload = {
                "knowledge_point_id": selected_task.get("id", 0),
                "knowledge_point_title": selected_task.get("title", ""),
                "chapter_id": selected_task.get("chapter_id", 0),
                "chapter_title": selected_task.get("chapter_title", ""),
                "book_id": selected_book_id,
                "book_title": selected_task.get("book_title", ""),
                "score": selected_task.get("score", 0),
                "order_index": len(day_items),
                "estimated_minutes": item_minutes,
                "item_type": selected_task.get("item_type", "learning"),
            }
            day_items.append(item_payload)
            review_items.append(item_payload)
            day_total_minutes += item_minutes
            book_task_counts[selected_book_id] += 1
            last_book_id = selected_book_id

        while remaining_tasks:
            selected_index = _select_review_task_for_day(
                remaining_tasks=remaining_tasks,
                day_total_minutes=day_total_minutes,
                daily_capacity=daily_capacity,
                day_number=day_number,
                forced_only=False,
            )
            if selected_index is None:
                break

            selected_task = remaining_tasks.pop(selected_index)
            selected_book_id = selected_task.get("book_id", 0)
            item_minutes = _resolve_task_minutes(selected_task)

            item_payload = {
                "knowledge_point_id": selected_task.get("id", 0),
                "knowledge_point_title": selected_task.get("title", ""),
                "chapter_id": selected_task.get("chapter_id", 0),
                "chapter_title": selected_task.get("chapter_title", ""),
                "book_id": selected_book_id,
                "book_title": selected_task.get("book_title", ""),
                "score": selected_task.get("score", 0),
                "order_index": len(day_items),
                "estimated_minutes": item_minutes,
                "item_type": selected_task.get("item_type", "learning"),
            }
            day_items.append(item_payload)
            review_items.append(item_payload)
            day_total_minutes += item_minutes
            book_task_counts[selected_book_id] += 1
            last_book_id = selected_book_id

        while remaining_tasks:
            selected_index = _select_learning_task_for_day(
                remaining_tasks=remaining_tasks,
                day_items=day_items,
                day_total_minutes=day_total_minutes,
                daily_capacity=daily_capacity,
                book_task_counts=book_task_counts,
                last_book_id=last_book_id,
            )
            if selected_index is None:
                break

            selected_task = remaining_tasks.pop(selected_index)
            selected_book_id = selected_task.get("book_id", 0)
            item_minutes = _resolve_task_minutes(selected_task)

            item_payload = {
                "knowledge_point_id": selected_task.get("id", 0),
                "knowledge_point_title": selected_task.get("title", ""),
                "chapter_id": selected_task.get("chapter_id", 0),
                "chapter_title": selected_task.get("chapter_title", ""),
                "book_id": selected_book_id,
                "book_title": selected_task.get("book_title", ""),
                "score": selected_task.get("score", 0),
                "order_index": len(day_items),
                "estimated_minutes": item_minutes,
                "item_type": selected_task.get("item_type", "learning"),
            }
            day_items.append(item_payload)
            if item_payload["item_type"] == "review":
                review_items.append(item_payload)
            else:
                study_items.append(item_payload)

            day_total_minutes += item_minutes
            book_task_counts[selected_book_id] += 1
            last_book_id = selected_book_id

        day_items = merge_learning_and_review(study_items, review_items)
        for idx, item in enumerate(day_items):
            item["order_index"] = idx
        for idx, item in enumerate(study_items):
            item["order_index"] = idx
        for idx, item in enumerate(review_items):
            item["order_index"] = idx

        if not day_items:
            day_number += 1
            continue

        daily_plan.append(
            {
                "day": day_number,
                "items": day_items,
                "study_items": study_items,
                "review_items": review_items,
                "total_minutes": day_total_minutes,
                "target_date": (start_date + timedelta(days=day_number - 1)).isoformat(),
            }
        )
        day_number += 1

    return daily_plan


def merge_learning_and_review(study_items: list[dict], review_items: list[dict]) -> list[dict]:
    merged = []
    study_idx = 0
    review_idx = 0

    while study_idx < len(study_items) or review_idx < len(review_items):
        if review_idx < len(review_items):
            merged.append(review_items[review_idx])
            review_idx += 1
        if study_idx < len(study_items):
            merged.append(study_items[study_idx])
            study_idx += 1

    return merged
