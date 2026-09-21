from __future__ import annotations

from typing import Any

from app.database.connection import SessionLocal
from app.database.models import (
    DatasetAnalytics,
    DatasetInsight,
    DatasetRecommendation,
)


class AnalyticsRepository:
    """Persist calculated analytics and decision-support results."""

    @staticmethod
    def save_analysis(
        dataset_id: int,
        analysis_type: str,
        result: dict[str, Any],
    ) -> None:
        """
        Create or update one analysis result for a dataset.

        Each dataset can have one current result for an analysis type,
        such as profile, quality, statistics, kpis, or trends.
        """
        session = SessionLocal()

        try:
            analysis = (
                session.query(DatasetAnalytics)
                .filter_by(
                    dataset_id=dataset_id,
                    analysis_type=analysis_type,
                )
                .one_or_none()
            )

            if analysis is None:
                analysis = DatasetAnalytics(
                    dataset_id=dataset_id,
                    analysis_type=analysis_type,
                    result_data=result,
                )
                session.add(analysis)
            else:
                analysis.result_data = result

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def replace_insights(
        dataset_id: int,
        insights: list[dict[str, Any]],
    ) -> None:
        """
        Replace all stored insights for a dataset.

        The API may return extra fields such as evidence, but the current
        database model stores only severity, title, and message.
        """
        session = SessionLocal()

        try:
            (
                session.query(DatasetInsight)
                .filter_by(dataset_id=dataset_id)
                .delete()
            )

            rows = [
                DatasetInsight(
                    dataset_id=dataset_id,
                    severity=insight["severity"],
                    title=insight["title"],
                    message=insight["message"],
                )
                for insight in insights
            ]

            session.add_all(rows)
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def replace_recommendations(
        dataset_id: int,
        recommendations: list[dict[str, Any]],
    ) -> None:
        """
        Replace all stored recommendations for a dataset.

        The API may return extra fields such as evidence, but the current
        database model stores only priority, recommendation, and rationale.
        """
        session = SessionLocal()

        try:
            (
                session.query(DatasetRecommendation)
                .filter_by(dataset_id=dataset_id)
                .delete()
            )

            rows = [
                DatasetRecommendation(
                    dataset_id=dataset_id,
                    priority=recommendation["priority"],
                    recommendation=recommendation[
                        "recommendation"
                    ],
                    rationale=recommendation["rationale"],
                )
                for recommendation in recommendations
            ]

            session.add_all(rows)
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()