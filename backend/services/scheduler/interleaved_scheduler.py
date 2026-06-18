from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from ..review_scheduler import get_review_minutes
from .adaptive_scheduler import calculate_adaptive_priority
from .attention_model import calculate_attention_score
from .spaced_repetition import calculate_spaced_repetition


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

    if item_type == "review":
        variant["estimated_minutes"] = get_review_minutes(variant.get("estimated_minutes", 10))
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
    tasks = build_interleaved_tasks(knowledge_points, total_days)
    tasks.sort(
        key=lambda item: (
            0 if item.get("item_type") == "review" else 1,
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


def generate_interleaved_plan(knowledge_points: list[dict], total_days: int, daily_minutes: int, start_date=None):
    if start_date is None:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    if not knowledge_points or total_days <= 0 or daily_minutes <= 0:
        return []

    task_pool = build_scheduler_pipeline(knowledge_points, total_days, daily_minutes)
    daily_plan = []
    remaining_tasks = list(task_pool)

    for day_number in range(1, total_days + 1):
        if not remaining_tasks:
            break

        day_items = []
        study_items = []
        review_items = []
        day_total_minutes = 0
        book_task_counts = defaultdict(int)
        last_book_id = None

        while remaining_tasks:
            selected_index = None

            for idx, task in enumerate(remaining_tasks):
                book_id = task.get("book_id", 0)
                estimated_minutes = max(1, int(task.get("estimated_minutes", 10)))
                is_review = task.get("item_type") == "review"

                if not is_review and book_task_counts[book_id] >= 2:
                    continue
                if not is_review and last_book_id is not None and book_id == last_book_id:
                    continue
                if day_items and day_total_minutes + estimated_minutes > daily_minutes:
                    continue

                selected_index = idx
                break

            if selected_index is None:
                if not day_items:
                    for idx, task in enumerate(remaining_tasks):
                        book_id = task.get("book_id", 0)
                        is_review = task.get("item_type") == "review"
                        if not is_review and book_task_counts[book_id] >= 2:
                            continue
                        selected_index = idx
                        break

                if selected_index is None:
                    break

            selected_task = remaining_tasks.pop(selected_index)
            selected_book_id = selected_task.get("book_id", 0)
            item_minutes = max(1, int(selected_task.get("estimated_minutes", 10)))

            if day_items and day_total_minutes + item_minutes > daily_minutes:
                remaining_tasks.insert(
                    selected_index if selected_index <= len(remaining_tasks) else len(remaining_tasks),
                    selected_task,
                )
                break

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
