"""
SM-2 Spaced Repetition Algorithm Engine
Based on: https://en.wikipedia.org/wiki/SuperMemo#SM-2_algorithm

Key formulas:
- EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
- EF' min = 1.3
- First review: 1 day, second: 6 days, then: interval * EF
"""
import math
from datetime import date, timedelta
from typing import Optional

from ..core.logger import get_logger

logger = get_logger(__name__)


def sm2_calculate(quality: int, repetitions: int, ease_factor: float, interval_days: int):
    """
    Calculate new SM-2 parameters after a review.

    Args:
        quality: 0-5 recall quality (0=complete blackout, 5=perfect)
        repetitions: current consecutive successful recall count
        ease_factor: current ease factor (default 2.5)
        interval_days: current interval in days

    Returns:
        tuple: (new_ease_factor, new_interval_days, new_repetitions)
    """
    quality = max(0, min(5, quality))

    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)

    if quality >= 3:
        new_repetitions = repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = round(interval_days * ease_factor)
    else:
        new_repetitions = 0
        new_interval = 1

    new_interval = max(1, new_interval)
    return new_ef, new_interval, new_repetitions


def compute_review_schedule(
    learning_day: int,
    quality_assumed: int = 4,
    total_days: int = 30,
    max_reviews_per_kp: int = 4,
) -> list[int]:
    """
    Predict which days (1-indexed) a KP's reviews fall on, assuming
    a given quality rating. Used when pre-generating a plan.
    """
    ef = 2.5
    interval = 0
    reps = 0
    review_days = []

    for _ in range(max_reviews_per_kp):
        ef, interval, reps = sm2_calculate(quality_assumed, reps, ef, interval)
        review_day = learning_day + interval
        if review_day > total_days:
            break
        if review_day not in review_days:
            review_days.append(review_day)

    return review_days


def get_review_minutes(item_estimated_minutes: int) -> int:
    """Reviews take less time than initial learning."""
    return max(3, round(item_estimated_minutes * 0.4))
