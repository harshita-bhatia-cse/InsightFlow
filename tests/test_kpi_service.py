import pandas as pd

from app.analytics.kpi_service import KPIService


def create_test_dataframe():
    return pd.DataFrame(
        [
            {
                "Task_ID": 1,
                "Layer": "Analytics",
                "Component": "KPI",
                "Status": "Completed",
                "Priority": "High",
                "Estimated_Hours": 10,
            },
            {
                "Task_ID": 2,
                "Layer": "Analytics",
                "Component": "Trend",
                "Status": "Pending",
                "Priority": "Critical",
                "Estimated_Hours": 20,
            },
            {
                "Task_ID": 3,
                "Layer": "AI",
                "Component": "Insight",
                "Status": "In Progress",
                "Priority": "Low",
                "Estimated_Hours": 5,
            },
        ]
    )


def test_kpi_calculation():
    dataframe = create_test_dataframe()

    result = KPIService.calculate(
        dataframe=dataframe,
        dataset_id=1,
    )

    assert result["dataset_id"] == 1
    assert result["total_tasks"] == 3
    assert result["completed_tasks"] == 1
    assert result["pending_tasks"] == 2
    assert result["completion_rate"] == 33.33
    assert result["pending_rate"] == 66.67
    assert result["high_priority_pending_tasks"] == 1
    assert result["total_estimated_hours"] == 35.0


def test_kpi_calculation_handles_missing_optional_columns():
    dataframe = pd.DataFrame(
        [
            {
                "Task_ID": 1,
                "Status": "Completed",
            },
            {
                "Task_ID": 2,
                "Status": "Pending",
            },
        ]
    )

    result = KPIService.calculate(
        dataframe=dataframe,
        dataset_id=2,
    )

    assert result["dataset_id"] == 2
    assert result["total_tasks"] == 2
    assert result["completed_tasks"] == 1
    assert result["pending_tasks"] == 1
    assert result["total_estimated_hours"] == 0.0
    assert result["layer_workload_distribution"] == []
    assert result["component_distribution"] == []