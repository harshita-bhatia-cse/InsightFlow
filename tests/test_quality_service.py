from app.analytics.quality_service import QualityService


def test_quality_calculation():
    pipeline_run = {
        "original_rows": 10,
        "ready_rows": 8,
        "quarantined_rows": 2,
        "validation_report": {
            "missing_values": {
                "Task_ID": 1,
                "Status": 1,
            },
            "exact_duplicate_rows": 1,
            "duplicate_task_id_rows": 1,
            "missing_columns": [],
            "required_field_errors": {},
            "unexpected_columns": [],
        },
    }

    result = QualityService.calculate(
        pipeline_run=pipeline_run,
        dataset_rows=8,
    )

    assert result["quality_score"] == 80.0
    assert result["grade"] == "B"

    assert result["metrics"]["completeness_score"] == 80.0
    assert result["metrics"]["uniqueness_score"] == 80.0
    assert result["metrics"]["validity_score"] == 80.0
    assert result["metrics"]["readiness_score"] == 80.0
    assert result["metrics"]["quarantine_rate"] == 20.0

    assert result["summary"]["original_rows"] == 10
    assert result["summary"]["ready_rows"] == 8
    assert result["summary"]["quarantined_rows"] == 2
    assert result["summary"]["dataset_rows"] == 8
    assert result["summary"]["missing_value_count"] == 2
    assert result["summary"]["duplicate_row_count"] == 1
    assert result["summary"]["duplicate_task_id_count"] == 1

    issue_types = [
        issue["type"]
        for issue in result["issues"]
    ]

    assert "duplicate_task_ids" in issue_types
    assert "quarantined_rows" in issue_types


def test_quality_calculation_with_perfect_data():
    pipeline_run = {
        "original_rows": 10,
        "ready_rows": 10,
        "quarantined_rows": 0,
        "validation_report": {
            "missing_values": {
                "Task_ID": 0,
                "Status": 0,
            },
            "exact_duplicate_rows": 0,
            "duplicate_task_id_rows": 0,
            "missing_columns": [],
            "required_field_errors": {},
            "unexpected_columns": [],
        },
    }

    result = QualityService.calculate(
        pipeline_run=pipeline_run,
        dataset_rows=10,
    )

    assert result["quality_score"] == 100.0
    assert result["grade"] == "A"
    assert result["metrics"]["completeness_score"] == 100.0
    assert result["metrics"]["uniqueness_score"] == 100.0
    assert result["metrics"]["validity_score"] == 100.0
    assert result["metrics"]["readiness_score"] == 100.0
    assert result["metrics"]["quarantine_rate"] == 0.0
    assert result["issues"] == []


def test_quality_calculation_handles_empty_data():
    pipeline_run = {
        "original_rows": 0,
        "ready_rows": 0,
        "quarantined_rows": 0,
        "validation_report": {},
    }

    result = QualityService.calculate(
        pipeline_run=pipeline_run,
        dataset_rows=0,
    )

    assert result["quality_score"] == 0.0
    assert result["grade"] == "F"
    assert result["metrics"]["completeness_score"] == 0.0
    assert result["metrics"]["uniqueness_score"] == 0.0
    assert result["metrics"]["readiness_score"] == 0.0
    assert result["metrics"]["quarantine_rate"] == 0.0
    assert result["issues"] == []