from datetime import datetime, timedelta

from ..core.logger import get_logger
from .review_scheduler import compute_review_schedule, get_review_minutes

logger = get_logger(__name__)


def generate_plan(knowledge_points, total_days, daily_minutes, start_date=None):
    """
    Generate a study plan that interleaves new learning with SM-2 spaced reviews.

    Phase 1: schedule new KPs as learning items.
    Phase 2: for each KP, compute review days and insert review items.
    Review items take priority (cheaper), remaining time fills with learning.
    """
    if start_date is None:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    if not knowledge_points:
        return []

    # Group by chapter, sort by chapter order then KP importance
    chapter_groups = {}
    for kp in knowledge_points:
        ch_id = kp.get("chapter_id", 0)
        if ch_id not in chapter_groups:
            chapter_groups[ch_id] = []
        chapter_groups[ch_id].append(kp)

    flat_kps = []
    for ch_id in sorted(chapter_groups.keys()):
        sorted_kps = sorted(chapter_groups[ch_id], key=lambda x: x.get("order_index", 0))
        sorted_kps.sort(key=lambda x: -x.get("importance", 3))
        flat_kps.extend(sorted_kps)

    # Phase 1: all-new-learning allocation (use ~70% of daily time for learning)
    learning_budget_ratio = 0.7
    learning_minutes = max(5, round(daily_minutes * learning_budget_ratio))

    daily_plan = []
    current_day = {"day": 1, "items": [], "total_minutes": 0}
    learning_queue = list(flat_kps)

    while learning_queue and current_day["day"] <= total_days:
        kp = learning_queue.pop(0)
        est_minutes = kp.get("estimated_minutes", 10)

        if current_day["total_minutes"] + est_minutes > learning_minutes and current_day["items"]:
            # Cap learning items to ~70% of daily budget, then add reviews in Phase 2
            daily_plan.append(current_day)
            current_day = {"day": len(daily_plan) + 1, "items": [], "total_minutes": 0}

        if est_minutes > learning_minutes:
            est_minutes = learning_minutes

        current_day["items"].append({
            "knowledge_point_id": kp.get("id", 0),
            "knowledge_point_title": kp.get("title", ""),
            "chapter_id": kp.get("chapter_id", 0),
            "chapter_title": kp.get("chapter_title", ""),
            "order_index": len(current_day["items"]),
            "estimated_minutes": est_minutes,
            "item_type": "learning",
        })
        current_day["total_minutes"] += est_minutes

        if current_day["day"] >= total_days:
            while learning_queue:
                extra_kp = learning_queue.pop(0)
                extra_minutes = min(extra_kp.get("estimated_minutes", 10), learning_minutes)
                current_day["items"].append({
                    "knowledge_point_id": extra_kp.get("id", 0),
                    "knowledge_point_title": extra_kp.get("title", ""),
                    "chapter_id": extra_kp.get("chapter_id", 0),
                    "chapter_title": extra_kp.get("chapter_title", ""),
                    "order_index": len(current_day["items"]),
                    "estimated_minutes": extra_minutes,
                    "item_type": "learning",
                })
                current_day["total_minutes"] += extra_minutes

    if current_day["items"]:
        daily_plan.append(current_day)

    # Phase 2: pre-schedule reviews for each KP
    # Build a map: day_number -> KP ids learned that day
    kp_learning_day = {}  # kp_id -> day_number it was learned
    for day in daily_plan:
        for item in day["items"]:
            if item["item_type"] == "learning":
                kp_id = item["knowledge_point_id"]
                if kp_id not in kp_learning_day:
                    kp_learning_day[kp_id] = day["day"]

    # For each learned KP, compute review days and insert
    for kp in flat_kps:
        kp_id = kp.get("id", 0)
        if kp_id not in kp_learning_day:
            continue
        learn_day = kp_learning_day[kp_id]
        review_days = compute_review_schedule(learn_day, total_days=total_days)

        for review_day_num in review_days:
            # Find or create the target day
            target_day = None
            for d in daily_plan:
                if d["day"] == review_day_num:
                    target_day = d
                    break
            if target_day is None:
                continue

            # Check if daily budget allows this review
            review_mins = get_review_minutes(kp.get("estimated_minutes", 10))
            if target_day["total_minutes"] + review_mins > daily_minutes:
                # Try squeezing: replace a learning item's extra time first
                continue

            # Add review item
            target_day["items"].append({
                "knowledge_point_id": kp_id,
                "knowledge_point_title": kp.get("title", ""),
                "chapter_id": kp.get("chapter_id", 0),
                "chapter_title": kp.get("chapter_title", ""),
                "order_index": len(target_day["items"]),
                "estimated_minutes": review_mins,
                "item_type": "review",
            })
            target_day["total_minutes"] += review_mins

    # Re-index order_integers and set target_date
    for day in daily_plan:
        for idx, item in enumerate(day["items"]):
            item["order_index"] = idx

        day_index = day["day"] - 1
        day["target_date"] = (start_date + timedelta(days=day_index)).isoformat()

    return daily_plan
