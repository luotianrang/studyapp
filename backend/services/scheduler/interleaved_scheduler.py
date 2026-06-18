from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from math import ceil

from ..review_scheduler import get_review_minutes
from .adaptive_scheduler import calculate_adaptive_priority
from .attention_model import calculate_attention_score
from .learning_state_machine import (
    LEARNING_STATES,
    build_learning_state_machine,
    get_review_intervals_for_task,
)
from .planning_layer import build_planning_context
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


def _as_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


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
    return task.get("learning_state") in {LEARNING_STATES["UNLEARNED"], LEARNING_STATES["LEARNING"]}


def _should_create_review_item(task: dict) -> bool:
    return task.get("learning_state") in {LEARNING_STATES["LEARNED"], LEARNING_STATES["REVIEW_QUEUE"]}


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
        variant["estimated_minutes"] = _coerce_minutes(
            variant.get("planned_review_minutes"),
            get_review_minutes(variant.get("estimated_minutes", 10)),
        )
        next_review_time = _as_datetime(variant.get("next_review_time"))
        if next_review_time is not None:
            review_anchor_day = max(1, min(total_days, (next_review_time.date() - now.date()).days + 1))
        else:
            review_anchor_day = max(1, int(variant.get("review_anchor_day", 1) or 1))
        variant["review_anchor_day"] = review_anchor_day
    else:
        variant["learning_state"] = LEARNING_STATES["LEARNING"]
    return variant


def build_interleaved_tasks(knowledge_points: list[dict], total_days: int) -> list[dict]:
    tasks = []
    now = datetime.now()
    state_machine = build_learning_state_machine(knowledge_points, now=now)

    for kp in state_machine["unlearned_store"]:
        base_task = dict(kp)
        base_task["book_id"] = kp.get("book_id", 0)
        base_task["learning_state"] = LEARNING_STATES["UNLEARNED"]

        review_snapshot = calculate_spaced_repetition(base_task, review_state=base_task.get("review_state"), now=now)
        base_task.update(review_snapshot)

        if _should_create_study_item(base_task):
            tasks.append(_build_task_variant(base_task, "learning", total_days, now))
            review_days = get_review_intervals_for_task(base_task, total_days, learning_day=1)
            for review_index, review_day in enumerate(review_days):
                review_task = _build_task_variant(base_task, "review", total_days, now)
                review_task["review_anchor_day"] = min(total_days, max(1, review_day))
                review_task["score"] = round(review_task["score"] - review_index * 0.01, 4)
                review_task["final_score"] = round(review_task["final_score"] - review_index * 0.01, 4)
                review_task["learning_state"] = LEARNING_STATES["REVIEW_QUEUE"]
                tasks.append(review_task)

    for kp in state_machine["learned_store"]:
        base_task = dict(kp)
        base_task["book_id"] = kp.get("book_id", 0)
        base_task["learning_state"] = kp.get("learning_state", LEARNING_STATES["LEARNED"])

        review_snapshot = calculate_spaced_repetition(base_task, review_state=base_task.get("review_state"), now=now)
        base_task.update(review_snapshot)

        if _should_create_review_item(base_task):
            review_days = get_review_intervals_for_task(base_task, total_days, learning_day=1)
            if not review_days and base_task.get("learning_state") == LEARNING_STATES["REVIEW_QUEUE"]:
                review_days = [1]
            elif base_task.get("learning_state") == LEARNING_STATES["REVIEW_QUEUE"]:
                review_days = [1]
            for review_index, review_day in enumerate(review_days):
                review_task = _build_task_variant(base_task, "review", total_days, now)
                review_task["review_anchor_day"] = min(total_days, max(1, review_day))
                review_task["score"] = round(review_task["score"] - review_index * 0.01, 4)
                review_task["final_score"] = round(review_task["final_score"] - review_index * 0.01, 4)
                tasks.append(review_task)

    tasks.sort(
        key=lambda item: (
            0 if item.get("item_type") == "review" else 1,
            item.get(
                "sequence_key",
                (
                    item.get("book_id", 0),
                    item.get("chapter_number", 0),
                    item.get("order_index", 0),
                    item.get("id", 0),
                ),
            ),
            item.get("review_anchor_day", 10**6),
            -item["score"],
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
    include_future: bool = False,
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
        if not include_future and _review_anchor_day(task) > day_number:
            continue
        if _fits_within_day(task, remaining_capacity):
            return idx

    return None


def _remaining_minutes(remaining_tasks: list[dict], *, review_only: bool | None = None) -> int:
    total = 0
    for task in remaining_tasks:
        is_review = _is_review_task(task)
        if review_only is True and not is_review:
            continue
        if review_only is False and is_review:
            continue
        total += _resolve_task_minutes(task)
    return total


def _min_remaining_task_minutes(remaining_tasks: list[dict], *, review_only: bool | None = None) -> int | None:
    candidates = []
    for task in remaining_tasks:
        is_review = _is_review_task(task)
        if review_only is True and not is_review:
            continue
        if review_only is False and is_review:
            continue
        candidates.append(_resolve_task_minutes(task))
    return min(candidates) if candidates else None


def _daily_target_minutes(remaining_tasks: list[dict], day_number: int, total_days: int, *, review_only: bool) -> int:
    remaining_days = max(1, total_days - day_number + 1)
    remaining_minutes = _remaining_minutes(remaining_tasks, review_only=review_only)
    if remaining_minutes <= 0:
        return 0
    return max(MIN_SESSION_MINUTES, ceil(remaining_minutes / remaining_days))


def _build_item_payload(selected_task: dict, order_index: int) -> dict:
    return {
        "knowledge_point_id": selected_task.get("id", 0),
        "knowledge_point_title": selected_task.get("title", ""),
        "chapter_id": selected_task.get("chapter_id", 0),
        "chapter_title": selected_task.get("chapter_title", ""),
        "book_id": selected_task.get("book_id", 0),
        "book_title": selected_task.get("book_title", ""),
        "score": selected_task.get("score", 0),
        "order_index": order_index,
        "estimated_minutes": _resolve_task_minutes(selected_task),
        "item_type": selected_task.get("item_type", "learning"),
    }


def _append_selected_task(
    remaining_tasks: list[dict],
    selected_index: int,
    day_items: list[dict],
    study_items: list[dict],
    review_items: list[dict],
    book_task_counts: dict[int, int],
) -> tuple[int, int | None]:
    selected_task = remaining_tasks.pop(selected_index)
    item_payload = _build_item_payload(selected_task, len(day_items))
    day_items.append(item_payload)
    if item_payload["item_type"] == "review":
        review_items.append(item_payload)
    else:
        study_items.append(item_payload)

    selected_book_id = item_payload.get("book_id", 0)
    book_task_counts[selected_book_id] += 1
    return item_payload["estimated_minutes"], selected_book_id


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
    earliest_learning_sequence = None
    earliest_chapter_key = None

    for task in remaining_tasks:
        if _is_review_task(task):
            continue
        sequence_key = task.get(
            "sequence_key",
            (
                task.get("book_id", 0),
                task.get("chapter_number", 0),
                task.get("order_index", 0),
                task.get("id", 0),
            ),
        )
        chapter_key = task.get(
            "chapter_key",
            (
                task.get("book_id", 0),
                task.get("chapter_number", 0),
            ),
        )
        if earliest_learning_sequence is None or sequence_key < earliest_learning_sequence:
            earliest_learning_sequence = sequence_key
            earliest_chapter_key = chapter_key

    if earliest_learning_sequence is None:
        return None

    for idx, task in enumerate(remaining_tasks):
        if _is_review_task(task):
            continue
        if task.get("sequence_key", earliest_learning_sequence) != earliest_learning_sequence:
            continue
        if task.get("session_task_key") in existing_task_keys and _fits_within_day(task, remaining_capacity):
            return idx

    candidate_sets = (
        lambda task: (
            task.get("sequence_key", earliest_learning_sequence) == earliest_learning_sequence
            and task.get("chapter_key", earliest_chapter_key) == earliest_chapter_key
            and _fits_within_day(task, remaining_capacity)
            and (task.get("item_type") == "review" or book_task_counts[task.get("book_id", 0)] < 2)
            and (task.get("item_type") == "review" or last_book_id is None or task.get("book_id", 0) != last_book_id)
        ),
        lambda task: (
            task.get("sequence_key", earliest_learning_sequence) == earliest_learning_sequence
            and task.get("chapter_key", earliest_chapter_key) == earliest_chapter_key
            and _fits_within_day(task, remaining_capacity)
            and (task.get("item_type") == "review" or book_task_counts[task.get("book_id", 0)] < 2)
        ),
        lambda task: task.get("sequence_key", earliest_learning_sequence) == earliest_learning_sequence and _fits_within_day(task, remaining_capacity),
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
            if task.get("sequence_key", earliest_learning_sequence) == earliest_learning_sequence and _fits_within_day(task, remaining_capacity):
                return idx

    return None


def generate_interleaved_plan(knowledge_points: list[dict], total_days: int, daily_minutes: int, start_date=None):
    if start_date is None:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    if not knowledge_points or total_days <= 0 or daily_minutes <= 0:
        return []

    requested_horizon = total_days
    planning_context = build_planning_context(knowledge_points, total_days, daily_minutes)
    total_days = max(requested_horizon, int(planning_context.get("final_days", requested_horizon) or requested_horizon))
    planning_context["final_days"] = total_days
    planning_context["recommended_days"] = max(
        int(planning_context.get("recommended_days", total_days) or total_days),
        total_days,
    )
    daily_capacity = _resolve_daily_capacity(planning_context["daily_capacity"])
    task_pool = build_scheduler_pipeline(planning_context["planned_tasks"], total_days, daily_capacity)
    daily_plan = []
    remaining_tasks = list(task_pool)
    day_number = 1

    while remaining_tasks and day_number <= total_days:

        day_items = []
        study_items = []
        review_items = []
        day_total_minutes = 0
        book_task_counts = defaultdict(int)
        last_book_id = None
        learning_target_minutes = _daily_target_minutes(remaining_tasks, day_number, total_days, review_only=False)
        review_target_minutes = _daily_target_minutes(remaining_tasks, day_number, total_days, review_only=True)
        learning_minutes_scheduled = 0
        review_minutes_scheduled = 0
        min_learning_minutes = _min_remaining_task_minutes(remaining_tasks, review_only=False)
        min_review_minutes = _min_remaining_task_minutes(remaining_tasks, review_only=True)
        can_mix_today = (
            min_learning_minutes is not None
            and min_review_minutes is not None
            and (min_learning_minutes + min_review_minutes) <= daily_capacity
        )

        while remaining_tasks and not can_mix_today:
            selected_index = _select_review_task_for_day(
                remaining_tasks=remaining_tasks,
                day_total_minutes=day_total_minutes,
                daily_capacity=daily_capacity,
                day_number=day_number,
                forced_only=True,
            )
            if selected_index is None:
                break

            item_minutes, last_book_id = _append_selected_task(
                remaining_tasks,
                selected_index,
                day_items,
                study_items,
                review_items,
                book_task_counts,
            )
            day_total_minutes += item_minutes
            review_minutes_scheduled += item_minutes

        while remaining_tasks and not can_mix_today:
            selected_index = _select_review_task_for_day(
                remaining_tasks=remaining_tasks,
                day_total_minutes=day_total_minutes,
                daily_capacity=daily_capacity,
                day_number=day_number,
                forced_only=False,
            )
            if selected_index is None:
                break

            item_minutes, last_book_id = _append_selected_task(
                remaining_tasks,
                selected_index,
                day_items,
                study_items,
                review_items,
                book_task_counts,
            )
            day_total_minutes += item_minutes
            review_minutes_scheduled += item_minutes

        while remaining_tasks and can_mix_today and not study_items:
            review_reservation = min_review_minutes if not review_items else 0
            remaining_capacity = daily_capacity - day_total_minutes
            if remaining_capacity <= review_reservation:
                break

            selected_index = _select_learning_task_for_day(
                remaining_tasks=remaining_tasks,
                day_items=day_items,
                day_total_minutes=day_total_minutes,
                daily_capacity=daily_capacity - review_reservation,
                book_task_counts=book_task_counts,
                last_book_id=last_book_id,
            )
            if selected_index is None:
                break

            item_minutes, last_book_id = _append_selected_task(
                remaining_tasks,
                selected_index,
                day_items,
                study_items,
                review_items,
                book_task_counts,
            )
            day_total_minutes += item_minutes
            learning_minutes_scheduled += item_minutes
            if learning_minutes_scheduled >= learning_target_minutes:
                break

        while remaining_tasks:
            if can_mix_today and not review_items and min_review_minutes is not None:
                remaining_capacity = daily_capacity - day_total_minutes
                if remaining_capacity <= min_review_minutes:
                    break

            selected_index = _select_learning_task_for_day(
                remaining_tasks=remaining_tasks,
                day_items=day_items,
                day_total_minutes=day_total_minutes,
                daily_capacity=daily_capacity - (min_review_minutes if can_mix_today and not review_items and min_review_minutes else 0),
                book_task_counts=book_task_counts,
                last_book_id=last_book_id,
            )
            if selected_index is None:
                break

            item_minutes, last_book_id = _append_selected_task(
                remaining_tasks,
                selected_index,
                day_items,
                study_items,
                review_items,
                book_task_counts,
            )
            day_total_minutes += item_minutes
            learning_minutes_scheduled += item_minutes

            if learning_minutes_scheduled >= learning_target_minutes:
                break

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

            item_minutes, last_book_id = _append_selected_task(
                remaining_tasks,
                selected_index,
                day_items,
                study_items,
                review_items,
                book_task_counts,
            )
            day_total_minutes += item_minutes
            review_minutes_scheduled += item_minutes

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

            item_minutes, last_book_id = _append_selected_task(
                remaining_tasks,
                selected_index,
                day_items,
                study_items,
                review_items,
                book_task_counts,
            )
            day_total_minutes += item_minutes
            review_minutes_scheduled += item_minutes

            if review_minutes_scheduled >= review_target_minutes and review_items:
                break

        while remaining_tasks:
            reserve_for_due_review = 0
            if min_review_minutes is not None:
                has_due_review = _select_review_task_for_day(
                    remaining_tasks=remaining_tasks,
                    day_total_minutes=day_total_minutes,
                    daily_capacity=daily_capacity,
                    day_number=day_number,
                    forced_only=False,
                ) is not None
                if has_due_review and not review_items:
                    reserve_for_due_review = min_review_minutes

            selected_index = _select_learning_task_for_day(
                remaining_tasks=remaining_tasks,
                day_items=day_items,
                day_total_minutes=day_total_minutes,
                daily_capacity=daily_capacity - reserve_for_due_review,
                book_task_counts=book_task_counts,
                last_book_id=last_book_id,
            )
            if selected_index is None:
                break

            item_minutes, last_book_id = _append_selected_task(
                remaining_tasks,
                selected_index,
                day_items,
                study_items,
                review_items,
                book_task_counts,
            )
            day_total_minutes += item_minutes
            learning_minutes_scheduled += item_minutes

        while remaining_tasks:
            selected_index = _select_review_task_for_day(
                remaining_tasks=remaining_tasks,
                day_total_minutes=day_total_minutes,
                daily_capacity=daily_capacity,
                day_number=day_number,
                forced_only=False,
                include_future=False,
            )
            if selected_index is None:
                break

            item_minutes, last_book_id = _append_selected_task(
                remaining_tasks,
                selected_index,
                day_items,
                study_items,
                review_items,
                book_task_counts,
            )
            day_total_minutes += item_minutes
            review_minutes_scheduled += item_minutes

            if review_minutes_scheduled >= review_target_minutes:
                break

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
                "recommended_days": planning_context["recommended_days"],
                "final_days": planning_context["final_days"],
                "total_workload_minutes": planning_context["total_workload_minutes"],
                "explanation": planning_context["explanation"],
            }
        )
        day_number += 1

    return daily_plan


def merge_learning_and_review(study_items: list[dict], review_items: list[dict]) -> list[dict]:
    if not study_items:
        return list(review_items)
    if not review_items:
        return list(study_items)

    front_study_count = max(1, (len(study_items) + 1) // 2)
    merged = list(study_items[:front_study_count])
    remaining_study = study_items[front_study_count:]
    review_idx = 0
    study_idx = 0

    while review_idx < len(review_items) or study_idx < len(remaining_study):
        if review_idx < len(review_items):
            merged.append(review_items[review_idx])
            review_idx += 1
        if study_idx < len(remaining_study):
            merged.append(remaining_study[study_idx])
            study_idx += 1

    return merged
