from unittest.mock import patch

from app.analytics.engine import AnalyticsEngine


def test_insights_use_services_and_persist_results():
    kpi_result = {
        "dataset_id": 1,
        "completion_rate": 50.0,
        "pending_rate": 50.0,
        "high_priority_pending_tasks": 2,
        "layer_workload_distribution": [],
    }

    trend_result = {
        "dataset_id": 1,
        "status_trends": [],
        "priority_trends": [],
        "layer_trends": [],
        "time_column": None,
        "time_trends": {},
    }

    insight_items = [
        {
            "severity": "high",
            "title": "Test insight",
            "message": "Test message",
            "evidence": {},
        }
    ]

    with (
        patch.object(
            AnalyticsEngine,
            "kpis",
            return_value=kpi_result,
        ) as kpis_mock,
        patch.object(
            AnalyticsEngine,
            "trends",
            return_value=trend_result,
        ) as trends_mock,
        patch(
            "app.analytics.engine.InsightService.generate",
            return_value=insight_items,
        ) as insight_mock,
        patch.object(
            AnalyticsEngine,
            "_replace_insights",
        ) as replace_mock,
    ):
        result = AnalyticsEngine.insights(1)

    assert result == {
        "dataset_id": 1,
        "insights": insight_items,
    }

    kpis_mock.assert_called_once_with(1)
    trends_mock.assert_called_once_with(1)

    insight_mock.assert_called_once_with(
        kpi_data=kpi_result,
        trend_data=trend_result,
    )

    replace_mock.assert_called_once_with(
        1,
        insight_items,
    )


def test_recommendations_use_service_and_persist_results():
    kpi_result = {
        "dataset_id": 1,
        "completion_rate": 50.0,
        "pending_rate": 60.0,
        "high_priority_pending_tasks": 2,
        "layer_workload_distribution": [],
    }

    recommendation_items = [
        {
            "priority": "high",
            "recommendation": "Test recommendation",
            "rationale": "Test rationale",
            "evidence": {},
        }
    ]

    with (
        patch.object(
            AnalyticsEngine,
            "kpis",
            return_value=kpi_result,
        ) as kpis_mock,
        patch(
            "app.analytics.engine.RecommendationService.generate",
            return_value=recommendation_items,
        ) as recommendation_mock,
        patch.object(
            AnalyticsEngine,
            "_replace_recommendations",
        ) as replace_mock,
    ):
        result = AnalyticsEngine.recommendations(1)

    assert result == {
        "dataset_id": 1,
        "recommendations": recommendation_items,
    }

    kpis_mock.assert_called_once_with(1)

    recommendation_mock.assert_called_once_with(
        kpi_data=kpi_result,
    )

    replace_mock.assert_called_once_with(
        1,
        recommendation_items,
    )