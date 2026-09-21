from unittest.mock import MagicMock, patch

from app.analytics.analytics_repository import (
    AnalyticsRepository,
)


def create_mock_session():
    session = MagicMock()
    query = session.query.return_value
    query.filter_by.return_value = query
    return session, query


def test_save_analysis_creates_new_analysis():
    session, query = create_mock_session()
    query.one_or_none.return_value = None

    result = {
        "dataset_id": 1,
        "total_tasks": 10,
    }

    with patch(
        "app.analytics.analytics_repository.SessionLocal",
        return_value=session,
    ):
        AnalyticsRepository.save_analysis(
            dataset_id=1,
            analysis_type="kpis",
            result=result,
        )

    session.add.assert_called_once()
    created_analysis = session.add.call_args.args[0]

    assert created_analysis.dataset_id == 1
    assert created_analysis.analysis_type == "kpis"
    assert created_analysis.result_data == result

    session.commit.assert_called_once()
    session.close.assert_called_once()


def test_save_analysis_updates_existing_analysis():
    session, query = create_mock_session()

    existing_analysis = MagicMock()
    query.one_or_none.return_value = existing_analysis

    result = {
        "dataset_id": 1,
        "total_tasks": 20,
    }

    with patch(
        "app.analytics.analytics_repository.SessionLocal",
        return_value=session,
    ):
        AnalyticsRepository.save_analysis(
            dataset_id=1,
            analysis_type="kpis",
            result=result,
        )

    assert existing_analysis.result_data == result
    session.add.assert_not_called()
    session.commit.assert_called_once()
    session.close.assert_called_once()


def test_replace_insights_replaces_database_rows():
    session, query = create_mock_session()

    insights = [
        {
            "severity": "high",
            "title": "Test insight",
            "message": "Test message",
            "evidence": {
                "completion_rate": 50.0,
            },
        }
    ]

    with patch(
        "app.analytics.analytics_repository.SessionLocal",
        return_value=session,
    ):
        AnalyticsRepository.replace_insights(
            dataset_id=1,
            insights=insights,
        )

    query.delete.assert_called_once()
    session.add_all.assert_called_once()

    rows = session.add_all.call_args.args[0]

    assert len(rows) == 1
    assert rows[0].dataset_id == 1
    assert rows[0].severity == "high"
    assert rows[0].title == "Test insight"
    assert rows[0].message == "Test message"

    session.commit.assert_called_once()
    session.close.assert_called_once()


def test_replace_recommendations_replaces_database_rows():
    session, query = create_mock_session()

    recommendations = [
        {
            "priority": "high",
            "recommendation": "Test recommendation",
            "rationale": "Test rationale",
            "evidence": {
                "pending_rate": 60.0,
            },
        }
    ]

    with patch(
        "app.analytics.analytics_repository.SessionLocal",
        return_value=session,
    ):
        AnalyticsRepository.replace_recommendations(
            dataset_id=1,
            recommendations=recommendations,
        )

    query.delete.assert_called_once()
    session.add_all.assert_called_once()

    rows = session.add_all.call_args.args[0]

    assert len(rows) == 1
    assert rows[0].dataset_id == 1
    assert rows[0].priority == "high"
    assert rows[0].recommendation == "Test recommendation"
    assert rows[0].rationale == "Test rationale"

    session.commit.assert_called_once()
    session.close.assert_called_once()

def test_save_analysis_rolls_back_when_commit_fails():
    session, query = create_mock_session()
    query.one_or_none.return_value = None

    commit_error = RuntimeError(
        "Database commit failed"
    )

    session.commit.side_effect = commit_error

    with patch(
        "app.analytics.analytics_repository.SessionLocal",
        return_value=session,
    ):
        try:
            AnalyticsRepository.save_analysis(
                dataset_id=1,
                analysis_type="kpis",
                result={
                    "dataset_id": 1,
                    "total_tasks": 10,
                },
            )
        except RuntimeError as error:
            assert str(error) == "Database commit failed"
        else:
            raise AssertionError(
                "Expected RuntimeError was not raised"
            )

    session.rollback.assert_called_once()
    session.close.assert_called_once()