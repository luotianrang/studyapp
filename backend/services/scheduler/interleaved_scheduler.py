from collections import defaultdict
from datetime import datetime, timedelta


def _spaced_repetition_adjust(tasks: list[dict]) -> list[dict]:
    adjusted = []
    for task in tasks:
        item = dict(task)
        if item.get("review_due"):
            item["score"] = round(item["score"] * 1.15, 4)
        adjusted.append(item)
    return adjusted


def _attention_adjust(tasks: list[dict]) -> list[dict]:
    adjusted = []
    for task in tasks:
        item = dict(task)
        minutes = max(1, int(item.get("estimated_minutes", 10)))
        if minutes > 30:
            item["score"] = round(item["score"] * 0.9, 4)
        elif minutes > 15:
            item["score"] = round(item["score"] * 0.95, 4)
        adjusted.append(item)
    return adjusted


def _adaptive_adjust(tasks: list[dict], daily_minutes: int) -> list[dict]:
    adjusted = []
    for task in tasks:
        item = dict(task)
        difficulty = float(item.get("difficulty", 0.5))
        minutes = max(1, int(item.get("estimated_minutes", 10)))
        if daily_minutes <= 30 and minutes <= 15:
            item["score"] = round(item["score"] * 1.05, 4)
        elif daily_minutes >= 60 and difficulty >= 3:
            item["score"] = round(item["score"] * 1.05, 4)
        adjusted.append(item)
    return adjusted


def _normalize_difficulty(task: dict) -> float:
    difficulty = task.get("difficulty")
    if difficulty is None:
        difficulty = 0.5
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
    urgency_score = min(5.0, 1.0 + sequence_hint / horizon)
    return urgency_score


def build_interleaved_tasks(knowledge_points: list[dict], total_days: int) -> list[dict]:
    tasks = []
    for kp in knowledge_points:
        task = dict(kp)
        task["book_id"] = kp.get("book_id", 0)
        task["difficulty"] = _normalize_difficulty(kp)
        task["importance"] = _normalize_importance(kp)
        task["urgency"] = _normalize_urgency(kp, total_days)
        task["score"] = round(
            task["importance"] * 0.4 + task["difficulty"] * 0.4 + task["urgency"] * 0.2,
            4,
        )
        tasks.append(task)

    tasks.sort(
        key=lambda item: (
            -item["score"],
            -item.get("importance", 0),
            -item.get("difficulty", 0),
            item.get("book_id", 0),
            item.get("chapter_number", 0),
            item.get("order_index", 0),
        )
    )
    return tasks


def build_scheduler_pipeline(knowledge_points: list[dict], total_days: int, daily_minutes: int) -> list[dict]:
    tasks = build_interleaved_tasks(knowledge_points, total_days)
    tasks = _spaced_repetition_adjust(tasks)
    tasks = _attention_adjust(tasks)
    tasks = _adaptive_adjust(tasks, daily_minutes)
    tasks.sort(
        key=lambda item: (
            -item["score"],
            -item.get("importance", 0),
            -item.get("difficulty", 0),
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
        day_total_minutes = 0
        book_task_counts = defaultdict(int)
        last_book_id = None

        while remaining_tasks:
            selected_index = None

            for idx, task in enumerate(remaining_tasks):
                book_id = task.get("book_id", 0)
                estimated_minutes = max(1, int(task.get("estimated_minutes", 10)))

                if book_task_counts[book_id] >= 2:
                    continue
                if last_book_id is not None and book_id == last_book_id:
                    continue
                if day_items and day_total_minutes + estimated_minutes > daily_minutes:
                    continue

                selected_index = idx
                break

            if selected_index is None:
                if not day_items:
                    for idx, task in enumerate(remaining_tasks):
                        book_id = task.get("book_id", 0)
                        if book_task_counts[book_id] >= 2:
                            continue
                        if last_book_id is not None and book_id == last_book_id:
                            continue
                        selected_index = idx
                        break

                if selected_index is None:
                    break

            selected_task = remaining_tasks.pop(selected_index)
            selected_book_id = selected_task.get("book_id", 0)
            item_minutes = max(1, int(selected_task.get("estimated_minutes", 10)))

            if day_items and day_total_minutes + item_minutes > daily_minutes:
                remaining_tasks.insert(selected_index if selected_index <= len(remaining_tasks) else len(remaining_tasks), selected_task)
                break

            day_items.append(
                {
                    "knowledge_point_id": selected_task.get("id", 0),
                    "knowledge_point_title": selected_task.get("title", ""),
                    "chapter_id": selected_task.get("chapter_id", 0),
                    "chapter_title": selected_task.get("chapter_title", ""),
                    "book_id": selected_book_id,
                    "book_title": selected_task.get("book_title", ""),
                    "score": selected_task.get("score", 0),
                    "order_index": len(day_items),
                    "estimated_minutes": item_minutes,
                    "item_type": "learning",
                }
            )
            day_total_minutes += item_minutes
            book_task_counts[selected_book_id] += 1
            last_book_id = selected_book_id

        if not day_items:
            continue

        daily_plan.append(
            {
                "day": day_number,
                "items": day_items,
                "total_minutes": day_total_minutes,
                "target_date": (start_date + timedelta(days=day_number - 1)).isoformat(),
            }
        )

    return daily_plan
