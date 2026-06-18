from __future__ import annotations

from math import ceil

from ..review_scheduler import compute_review_schedule, get_review_minutes

DEFAULT_BASE_MINUTES = 15
MIN_DAILY_CAPACITY = 1
MIN_LEARNING_MINUTES = 1
ESSENTIAL_MIN_LEARNING_MINUTES = 5


def _clamp_int(value: object, fallback: int, minimum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(minimum, parsed)


def _difficulty_multiplier(difficulty: object) -> float:
    try:
        value = float(difficulty)
    except (TypeError, ValueError):
        value = 0.5

    if value <= 0.35:
        return 0.9
    if value <= 0.7:
        return 1.15
    return 1.4


def _importance_score(task: dict) -> int:
    return _clamp_int(task.get("importance"), 3, 1)


def _mastery_score(task: dict) -> float:
    try:
        return max(0.0, min(1.0, float(task.get("mastery", 0.5) or 0.5)))
    except (TypeError, ValueError):
        return 0.5


def _is_core_review(task: dict) -> bool:
    return int(task.get("review_count", 0) or 0) > 0 or _mastery_score(task) < 0.5 or _importance_score(task) >= 4


def _base_learning_minutes(task: dict) -> int:
    estimated = task.get("estimated_minutes")
    try:
        estimated = int(estimated)
    except (TypeError, ValueError):
        estimated = None

    if estimated is not None and estimated > 0:
        return estimated

    learning_minutes = round(DEFAULT_BASE_MINUTES * _difficulty_multiplier(task.get("difficulty")))
    return max(ESSENTIAL_MIN_LEARNING_MINUTES, learning_minutes)


def _estimated_review_count(task: dict, total_days: int) -> int:
    importance = _importance_score(task)
    review_count = int(task.get("review_count", 0) or 0)
    mastery = _mastery_score(task)

    if review_count > 0:
        return 1

    max_reviews_per_kp = 3 if importance >= 4 or mastery < 0.5 else 2
    review_days = compute_review_schedule(learning_day=1, total_days=max(1, total_days), max_reviews_per_kp=max_reviews_per_kp)
    if not review_days and mastery < 0.6:
        return 1
    return len(review_days)


def _scheduled_review_count(task: dict) -> int:
    review_count = int(task.get("review_count", 0) or 0)
    last_review_time = task.get("last_review_time")
    mastery = _mastery_score(task)
    return 1 if (review_count > 0 or last_review_time is not None or mastery < 0.6) else 0


def _core_review_count(task: dict, estimated_review_count: int) -> int:
    if estimated_review_count <= 0:
        return 0
    return 1 if _is_core_review(task) else 0


def _planning_priority(task: dict) -> float:
    importance = float(_importance_score(task))
    mastery_gap = 1.0 - _mastery_score(task)
    review_pressure = 1.0 if int(task.get("review_count", 0) or 0) > 0 else 0.0
    return round(importance * 2.0 + mastery_gap * 3.0 + review_pressure * 2.0, 4)


def _task_workload(task: dict) -> int:
    return int(task["planned_learning_minutes"]) + int(task["planned_review_count"]) * int(task["planned_review_minutes"])


def _task_estimated_workload(task: dict) -> int:
    return int(task["planned_learning_minutes"]) + int(task["estimated_review_count"]) * int(task["planned_review_minutes"])


def _compress_to_horizon(tasks: list[dict], horizon_capacity: int) -> None:
    if horizon_capacity <= 0:
        return

    priority_order = sorted(tasks, key=lambda item: (item["planning_priority"], item.get("order_index", 0), item.get("id", 0)))

    while sum(_task_workload(task) for task in tasks) > horizon_capacity:
        changed = False

        for task in priority_order:
            if task["planned_review_count"] > task["core_review_count"]:
                task["planned_review_count"] -= 1
                changed = True
                break

        if changed:
            continue

        for task in priority_order:
            minimum = ESSENTIAL_MIN_LEARNING_MINUTES if task["core_review_count"] > 0 or _importance_score(task) >= 4 else MIN_LEARNING_MINUTES
            if task["planned_learning_minutes"] > minimum:
                task["planned_learning_minutes"] -= 1
                changed = True
                break

        if not changed:
            break


def build_planning_context(knowledge_points: list[dict], total_days: int, daily_minutes: int) -> dict:
    daily_capacity = max(MIN_DAILY_CAPACITY, _clamp_int(daily_minutes, DEFAULT_BASE_MINUTES, MIN_DAILY_CAPACITY))
    requested_days = max(0, _clamp_int(total_days, 0, 0))
    planning_days = max(1, requested_days) if knowledge_points else 0

    planned_tasks = []
    for kp in knowledge_points:
        planned_tasks.append(dict(kp))

    if planned_tasks:
        seed_learning_minutes = sum(_base_learning_minutes(task) for task in planned_tasks)
        planning_days = max(1, requested_days or ceil(seed_learning_minutes / daily_capacity))

    for _ in range(3 if planned_tasks else 0):
        total_workload_minutes = 0
        for task in planned_tasks:
            learning_minutes = _base_learning_minutes(task)
            review_minutes = get_review_minutes(learning_minutes)
            estimated_review_count = _estimated_review_count(task, planning_days)
            total_workload_minutes += learning_minutes + estimated_review_count * review_minutes

        next_days = max(1, ceil(total_workload_minutes / daily_capacity)) if total_workload_minutes else 0
        if next_days == planning_days:
            break
        planning_days = next_days

    final_days = planning_days

    enriched_tasks = []
    for kp in planned_tasks:
        learning_minutes = _base_learning_minutes(kp)
        review_minutes = get_review_minutes(learning_minutes)
        estimated_review_count = _estimated_review_count(kp, final_days)
        scheduled_review_count = _scheduled_review_count(kp)
        core_review_count = _core_review_count(kp, scheduled_review_count)

        planned_task = dict(kp)
        planned_task["base_learning_minutes"] = learning_minutes
        planned_task["planned_learning_minutes"] = learning_minutes
        planned_task["planned_review_minutes"] = review_minutes
        planned_task["estimated_review_count"] = estimated_review_count
        planned_task["planned_review_count"] = scheduled_review_count
        planned_task["core_review_count"] = core_review_count
        planned_task["planning_priority"] = _planning_priority(kp)
        enriched_tasks.append(planned_task)

    planned_tasks = enriched_tasks
    total_workload_minutes = sum(_task_estimated_workload(task) for task in planned_tasks)
    recommended_days = max(1, ceil(total_workload_minutes / daily_capacity)) if planned_tasks else 0

    horizon_capacity = daily_capacity * final_days
    scheduled_workload_minutes = sum(_task_workload(task) for task in planned_tasks)
    if scheduled_workload_minutes > horizon_capacity:
        _compress_to_horizon(planned_tasks, horizon_capacity)

    compressed_workload_minutes = sum(_task_workload(task) for task in planned_tasks)

    for task in planned_tasks:
        task["estimated_minutes"] = task["planned_learning_minutes"]
        task["planned_total_minutes"] = _task_workload(task)
        task["planning_pressure"] = round(total_workload_minutes / horizon_capacity, 4) if horizon_capacity else 0.0

    explanation = (
        f"Based on {daily_capacity} minutes per day and an estimated workload of "
        f"{total_workload_minutes} minutes, the system recommends about {recommended_days} days."
        if planned_tasks
        else f"Based on {daily_capacity} minutes per day, no study days are required."
    )

    return {
        "planned_tasks": planned_tasks,
        "daily_capacity": daily_capacity,
        "final_days": final_days,
        "recommended_days": recommended_days,
        "total_workload_minutes": total_workload_minutes,
        "compressed_workload_minutes": compressed_workload_minutes,
        "horizon_capacity": horizon_capacity,
        "requested_days": requested_days,
        "explanation": explanation,
    }
