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


def test_multibook_plan_enforces_daily_capacity():
    now = datetime(2026, 6, 18, 9, 0, 0)
    knowledge_points = [
        {
            "id": 1,
            "title": "Heavy-1",
            "chapter_id": 11,
            "chapter_title": "C1",
            "chapter_number": 1,
            "book_id": 101,
            "book_title": "Book1",
            "importance": 5,
            "difficulty": 0.7,
            "estimated_minutes": 40,
            "order_index": 0,
            "learning_metrics": {"completion_rate": 0.0, "skip_rate": 0.0, "error_rate": 0.0},
            "review_state": {"review_count": 0, "mastery": 0.5, "last_review_time": None},
            "last_review_time": None,
            "review_count": 0,
            "mastery": 0.5,
        },
        {
            "id": 2,
            "title": "Heavy-2",
            "chapter_id": 12,
            "chapter_title": "C2",
            "chapter_number": 1,
            "book_id": 202,
            "book_title": "Book2",
            "importance": 5,
            "difficulty": 0.7,
            "estimated_minutes": 35,
            "order_index": 0,
            "learning_metrics": {"completion_rate": 0.0, "skip_rate": 0.0, "error_rate": 0.0},
            "review_state": {"review_count": 0, "mastery": 0.5, "last_review_time": None},
            "last_review_time": None,
            "review_count": 0,
            "mastery": 0.5,
        },
        {
            "id": 3,
            "title": "Review-Due",
            "chapter_id": 13,
            "chapter_title": "C3",
            "chapter_number": 1,
            "book_id": 101,
            "book_title": "Book1",
            "importance": 4,
            "difficulty": 0.5,
            "estimated_minutes": 20,
            "order_index": 1,
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
        total_days=3,
        daily_minutes=45,
        start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
    )

    assert len(plan) >= 2
    assert all(day["total_minutes"] <= 45 for day in plan)


def test_short_daily_minutes_spreads_work_across_more_days():
    now = datetime(2026, 6, 18, 9, 0, 0)
    knowledge_points = []
    for idx in range(1, 5):
        knowledge_points.append(
            {
                "id": idx,
                "title": f"KP-{idx}",
                "chapter_id": 10 + idx,
                "chapter_title": f"C{idx}",
                "chapter_number": idx,
                "book_id": 100 + idx,
                "book_title": f"Book{idx}",
                "importance": 4,
                "difficulty": 0.5,
                "estimated_minutes": 12,
                "order_index": 0,
                "learning_metrics": {"completion_rate": 0.0, "skip_rate": 0.0, "error_rate": 0.0},
                "review_state": {"review_count": 0, "mastery": 0.5, "last_review_time": None},
                "last_review_time": None,
                "review_count": 0,
                "mastery": 0.5,
            }
        )

    plan = generate_interleaved_plan(
        knowledge_points,
        total_days=2,
        daily_minutes=5,
        start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
    )

    assert len(plan) >= len(knowledge_points)
    assert all(day["total_minutes"] <= 5 for day in plan)


def test_review_is_protected_before_learning_when_capacity_is_tight():
    now = datetime(2026, 6, 18, 9, 0, 0)
    knowledge_points = [
        {
            "id": 1,
            "title": "Review-First",
            "chapter_id": 11,
            "chapter_title": "C1",
            "chapter_number": 1,
            "book_id": 101,
            "book_title": "Book1",
            "importance": 5,
            "difficulty": 0.5,
            "estimated_minutes": 20,
            "order_index": 0,
            "learning_metrics": {"completion_rate": 1.0, "skip_rate": 0.0, "error_rate": 0.2},
            "review_state": {
                "review_count": 2,
                "mastery": 0.4,
                "last_review_time": (now - timedelta(days=4)).isoformat(),
            },
            "last_review_time": (now - timedelta(days=4)).isoformat(),
            "review_count": 2,
            "mastery": 0.4,
        },
        {
            "id": 2,
            "title": "Learning-Delayed",
            "chapter_id": 12,
            "chapter_title": "C2",
            "chapter_number": 1,
            "book_id": 202,
            "book_title": "Book2",
            "importance": 5,
            "difficulty": 0.7,
            "estimated_minutes": 20,
            "order_index": 0,
            "learning_metrics": {"completion_rate": 0.0, "skip_rate": 0.0, "error_rate": 0.0},
            "review_state": {"review_count": 0, "mastery": 0.95, "last_review_time": None},
            "last_review_time": None,
            "review_count": 0,
            "mastery": 0.95,
        },
    ]

    plan = generate_interleaved_plan(
        knowledge_points,
        total_days=2,
        daily_minutes=10,
        start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
    )

    assert plan[0]["review_items"]
    assert plan[0]["review_items"][0]["knowledge_point_id"] == 1
    assert plan[0]["total_minutes"] <= 10


def test_forced_review_stays_ahead_of_learning_after_one_day_delay():
    now = datetime(2026, 6, 18, 9, 0, 0)
    knowledge_points = [
        {
            "id": 1,
            "title": "Review-A",
            "chapter_id": 11,
            "chapter_title": "C1",
            "chapter_number": 1,
            "book_id": 101,
            "book_title": "Book1",
            "importance": 4,
            "difficulty": 0.5,
            "estimated_minutes": 20,
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
        {
            "id": 2,
            "title": "Review-B",
            "chapter_id": 12,
            "chapter_title": "C2",
            "chapter_number": 1,
            "book_id": 102,
            "book_title": "Book2",
            "importance": 4,
            "difficulty": 0.5,
            "estimated_minutes": 20,
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
        {
            "id": 3,
            "title": "Learning-After-Delay",
            "chapter_id": 13,
            "chapter_title": "C3",
            "chapter_number": 1,
            "book_id": 103,
            "book_title": "Book3",
            "importance": 5,
            "difficulty": 0.7,
            "estimated_minutes": 20,
            "order_index": 0,
            "learning_metrics": {"completion_rate": 0.0, "skip_rate": 0.0, "error_rate": 0.0},
            "review_state": {"review_count": 0, "mastery": 0.95, "last_review_time": None},
            "last_review_time": None,
            "review_count": 0,
            "mastery": 0.95,
        },
    ]

    plan = generate_interleaved_plan(
        knowledge_points,
        total_days=2,
        daily_minutes=8,
        start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
    )

    assert plan[0]["review_items"]
    assert plan[1]["review_items"]
    assert all(item["knowledge_point_id"] != 3 for item in plan[1]["items"])


def test_long_learning_task_prefers_same_day_sessions_without_tiny_fragments():
    now = datetime(2026, 6, 18, 9, 0, 0)
    knowledge_points = [
        {
            "id": 1,
            "title": "Long-Learning",
            "chapter_id": 11,
            "chapter_title": "C1",
            "chapter_number": 1,
            "book_id": 101,
            "book_title": "Book1",
            "importance": 5,
            "difficulty": 0.7,
            "estimated_minutes": 70,
            "order_index": 0,
            "learning_metrics": {"completion_rate": 0.0, "skip_rate": 0.0, "error_rate": 0.0},
            "review_state": {"review_count": 0, "mastery": 0.95, "last_review_time": None},
            "last_review_time": None,
            "review_count": 0,
            "mastery": 0.95,
        },
    ]

    plan = generate_interleaved_plan(
        knowledge_points,
        total_days=3,
        daily_minutes=90,
        start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
    )

    assert len(plan) == 1
    assert len(plan[0]["study_items"]) == 2
    assert [item["estimated_minutes"] for item in plan[0]["study_items"]] == [35, 35]


def test_oversized_task_is_split_across_days_with_bounded_session_lengths():
    now = datetime(2026, 6, 18, 9, 0, 0)
    knowledge_points = [
        {
            "id": 1,
            "title": "Oversized-Learning",
            "chapter_id": 11,
            "chapter_title": "C1",
            "chapter_number": 1,
            "book_id": 101,
            "book_title": "Book1",
            "importance": 5,
            "difficulty": 0.7,
            "estimated_minutes": 100,
            "order_index": 0,
            "learning_metrics": {"completion_rate": 0.0, "skip_rate": 0.0, "error_rate": 0.0},
            "review_state": {"review_count": 0, "mastery": 0.95, "last_review_time": None},
            "last_review_time": None,
            "review_count": 0,
            "mastery": 0.95,
        },
    ]

    plan = generate_interleaved_plan(
        knowledge_points,
        total_days=3,
        daily_minutes=40,
        start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
    )

    assert len(plan) == 3
    assert [day["total_minutes"] for day in plan] == [34, 33, 33]
    assert all(10 <= item["estimated_minutes"] <= 40 for day in plan for item in day["study_items"])
