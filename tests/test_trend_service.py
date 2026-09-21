import pandas as pd

from app.analytics.trend_service import TrendService


def create_test_dataframe():
    return pd.DataFrame(
        [
            {
                "Task_ID": 1,
                "Status": "Completed",
                "Priority": "High",
                "Layer": "Analytics",
                "Created_Date": "2026-01-01",
            },
            {
                "Task_ID": 2,
                "Status": "Pending",
                "Priority": "Critical",
                "Layer": "AI",
                "Created_Date": "2026-01-01",
            },
            {
                "Task_ID": 3,
                "Status": "Completed",
                "Priority": "Low",
                "Layer": "Analytics",
                "Created_Date": "2026-01-02",
            },
        ]
    )


def test_trend_calculation():
    dataframe = create_test_dataframe()

    result = TrendService.calculate(
        dataframe=dataframe,
        dataset_id=1,
    )

    assert result["dataset_id"] == 1
    assert result["time_column"] == "Created_Date"

    assert result["status_trends"] == [
        {
            "name": "Completed",
            "count": 2,
        },
        {
            "name": "Pending",
            "count": 1,
        },
    ]

    assert result["priority_trends"] == [
        {
            "name": "High",
            "count": 1,
        },
        {
            "name": "Critical",
            "count": 1,
        },
        {
            "name": "Low",
            "count": 1,
        },
    ]

    assert result["layer_trends"] == [
        {
            "name": "Analytics",
            "count": 2,
        },
        {
            "name": "AI",
            "count": 1,
        },
    ]

    assert "daily" in result["time_trends"]
    assert "weekly" in result["time_trends"]
    assert "monthly" in result["time_trends"]


def test_trend_calculation_without_date_column():
    dataframe = pd.DataFrame(
        [
            {
                "Task_ID": 1,
                "Status": "Completed",
                "Priority": "High",
                "Layer": "Analytics",
            },
            {
                "Task_ID": 2,
                "Status": "Pending",
                "Priority": "Low",
                "Layer": "AI",
            },
        ]
    )

    result = TrendService.calculate(
        dataframe=dataframe,
        dataset_id=2,
    )

    assert result["dataset_id"] == 2
    assert result["time_column"] is None
    assert result["time_trends"] == {}


def test_trend_calculation_handles_missing_category_columns():
    dataframe = pd.DataFrame(
        [
            {
                "Task_ID": 1,
                "Created_Date": "2026-01-01",
            }
        ]
    )

    result = TrendService.calculate(
        dataframe=dataframe,
        dataset_id=3,
    )

    assert result["status_trends"] == []
    assert result["priority_trends"] == []
    assert result["layer_trends"] == []