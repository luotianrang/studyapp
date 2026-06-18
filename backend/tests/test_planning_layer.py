from backend.services.scheduler.planning_layer import build_planning_context


def test_planning_layer_estimates_days_from_workload():
    knowledge_points = [
        {
            "id": 1,
            "title": "KP-1",
            "importance": 5,
            "difficulty": 0.8,
            "estimated_minutes": 20,
            "order_index": 0,
            "review_count": 0,
            "mastery": 0.4,
        },
        {
            "id": 2,
            "title": "KP-2",
            "importance": 4,
            "difficulty": 0.7,
            "estimated_minutes": 20,
            "order_index": 1,
            "review_count": 1,
            "mastery": 0.5,
        },
    ]

    context = build_planning_context(knowledge_points, total_days=2, daily_minutes=120)

    assert context["recommended_days"] >= 1
    assert context["total_workload_minutes"] > 0
    assert context["daily_capacity"] == 120
    assert context["final_days"] == context["recommended_days"]
    assert "recommends about" in context["explanation"]


def test_planning_layer_compresses_workload_into_user_horizon():
    knowledge_points = []
    for idx in range(1, 9):
        knowledge_points.append(
            {
                "id": idx,
                "title": f"KP-{idx}",
                "importance": 2 if idx > 4 else 5,
                "difficulty": 0.9,
                "estimated_minutes": 20,
                "order_index": idx,
                "review_count": 0,
                "mastery": 0.7 if idx > 4 else 0.4,
            }
        )

    context = build_planning_context(knowledge_points, total_days=2, daily_minutes=30)

    assert context["recommended_days"] > 2
    assert context["compressed_workload_minutes"] <= context["horizon_capacity"]
    assert context["final_days"] == context["recommended_days"]
    assert any(task["planned_review_count"] == task["core_review_count"] for task in context["planned_tasks"])
