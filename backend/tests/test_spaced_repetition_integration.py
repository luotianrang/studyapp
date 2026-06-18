from datetime import datetime, timedelta

from backend.services.scheduler.interleaved_scheduler import generate_interleaved_plan
from backend.services.scheduler.spaced_repetition import calculate_spaced_repetition


def test_spaced_repetition_defaults_to_new_content_priority():
    result = calculate_spaced_repetition(
        {"id": 1, "title": "KP"},
        review_state={"review_count": 0, "mastery": 0.5},
        now=datetime(2026, 6, 18, 9, 0, 0),
    )

    assert result["review_score"] == 1.0
    assert result["last_review_time"] is None


def test_multibook_plan_contains_study_and_review_items():
    now = datetime(2026, 6, 18, 9, 0, 0)
    knowledge_points = [
        {
            "id": 1,
            "title": "Book1-New",
            "chapter_id": 11,
            "chapter_title": "C1",
            "chapter_number": 1,
            "book_id": 101,
            "book_title": "Book1",
            "importance": 4,
            "difficulty": 0.5,
            "estimated_minutes": 20,
            "order_index": 0,
            "learning_metrics": {"completion_rate": 0.0, "skip_rate": 0.0, "error_rate": 0.0},
            "review_state": {"review_count": 0, "mastery": 0.5, "last_review_time": None},
            "last_review_time": None,
            "review_count": 0,
            "mastery": 0.5,
        },
        {
            "id": 2,
            "title": "Book2-Review",
            "chapter_id": 22,
            "chapter_title": "C2",
            "chapter_number": 1,
            "book_id": 202,
            "book_title": "Book2",
            "importance": 5,
            "difficulty": 0.6,
            "estimated_minutes": 15,
            "order_index": 0,
            "learning_metrics": {"completion_rate": 1.0, "skip_rate": 0.0, "error_rate": 0.2},
            "review_state": {
                "review_count": 2,
                "mastery": 0.4,
                "last_review_time": (now - timedelta(days=3)).isoformat(),
            },
            "last_review_time": (now - timedelta(days=3)).isoformat(),
            "review_count": 2,
            "mastery": 0.4,
        },
    ]

    plan = generate_interleaved_plan(
        knowledge_points,
        total_days=2,
        daily_minutes=60,
        start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
    )

    assert plan
    assert any(day["study_items"] for day in plan)
    assert any(day["review_items"] for day in plan)
