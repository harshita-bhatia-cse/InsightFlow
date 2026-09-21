from app.analytics.recommendation_service import (
    RecommendationService,
)


def test_recommendation_generation():
    kpi_data = {
        "completion_rate": 50.0,
        "pending_rate": 60.0,
        "high_priority_pending_tasks": 3,
        "layer_workload_distribution": [
            {
                "name": "Analytics",
                "task_count": 4,
                "estimated_hours": 40.0,
            },
            {
                "name": "AI",
                "task_count": 2,
                "estimated_hours": 20.0,
            },
        ],
    }

    result = RecommendationService.generate(
        kpi_data=kpi_data,
    )

    assert len(result) == 4

    priorities = [
        item["priority"]
        for item in result
    ]

    assert priorities == [
        "medium",
        "high",
        "high",
        "medium",
    ]

    recommendation_text = [
        item["recommendation"]
        for item in result
    ]

    assert (
        "Review capacity in Analytics."
        in recommendation_text
    )

    assert (
        "Prioritize high-risk pending tasks "
        "in the next planning cycle."
        in recommendation_text
    )

    assert (
        "Create a recovery plan for incomplete tasks."
        in recommendation_text
    )

    assert (
        "Break down the pending backlog into smaller "
        "delivery milestones."
        in recommendation_text
    )


def test_recommendation_generation_with_healthy_data():
    kpi_data = {
        "completion_rate": 90.0,
        "pending_rate": 10.0,
        "high_priority_pending_tasks": 0,
        "layer_workload_distribution": [],
    }

    result = RecommendationService.generate(
        kpi_data=kpi_data,
    )

    assert result == []


def test_workload_recommendation_contains_evidence():
    kpi_data = {
        "completion_rate": 90.0,
        "pending_rate": 10.0,
        "high_priority_pending_tasks": 0,
        "layer_workload_distribution": [
            {
                "name": "AI",
                "task_count": 5,
                "estimated_hours": 75.0,
            },
        ],
    }

    result = RecommendationService.generate(
        kpi_data=kpi_data,
    )

    assert len(result) == 1
    assert result[0]["priority"] == "medium"
    assert result[0]["evidence"]["layer"] == "AI"
    assert result[0]["evidence"]["estimated_hours"] == 75.0