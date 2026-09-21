from app.analytics.insight_service import InsightService


def test_insight_generation():
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

    trend_data = {
        "status_trends": [
            {
                "name": "Pending",
                "count": 6,
            },
            {
                "name": "Completed",
                "count": 4,
            },
        ],
    }

    result = InsightService.generate(
        kpi_data=kpi_data,
        trend_data=trend_data,
    )

    assert len(result) == 5

    titles = [
        item["title"]
        for item in result
    ]

    assert "Completion rate below target" in titles
    assert "Large pending backlog" in titles
    assert "High-priority backlog" in titles
    assert "Highest workload layer" in titles
    assert "Largest task status group" in titles


def test_insight_generation_with_healthy_data():
    kpi_data = {
        "completion_rate": 90.0,
        "pending_rate": 10.0,
        "high_priority_pending_tasks": 0,
        "layer_workload_distribution": [],
    }

    trend_data = {
        "status_trends": [],
    }

    result = InsightService.generate(
        kpi_data=kpi_data,
        trend_data=trend_data,
    )

    assert result == []


def test_highest_workload_insight_contains_evidence():
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

    trend_data = {
        "status_trends": [],
    }

    result = InsightService.generate(
        kpi_data=kpi_data,
        trend_data=trend_data,
    )

    assert len(result) == 1
    assert result[0]["title"] == "Highest workload layer"
    assert result[0]["severity"] == "medium"
    assert result[0]["evidence"]["layer"] == "AI"
    assert result[0]["evidence"]["estimated_hours"] == 75.0