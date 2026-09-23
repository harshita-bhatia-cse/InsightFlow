from __future__ import annotations

from typing import Any
from app.database.models import Dataset
from app.database.connection import SessionLocal
from app.database.models import (
    Dataset,
    QualityMonitoringSnapshot,
)


class QualityMonitoringService:
    @staticmethod
    def save_snapshot(
        dataset_id: int,
        version_number: int,
        quality_result: dict[str, Any],
    ) -> None:
        session = SessionLocal()

        try:
            snapshot = QualityMonitoringSnapshot(
                dataset_id=dataset_id,
                version_number=version_number,
                quality_score=float(
                    quality_result.get(
                        "quality_score",
                        0.0,
                    )
                ),
                grade=str(
                    quality_result.get(
                        "grade",
                        "F",
                    )
                ),
                metrics=quality_result.get(
                    "metrics",
                    {},
                ),
                summary=quality_result.get(
                    "summary",
                    {},
                ),
                issues=quality_result.get(
                    "issues",
                    [],
                ),
            )

            session.add(snapshot)
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @staticmethod
    def history(
        filename: str,
    ) -> list[dict[str, Any]]:
        session = SessionLocal()

        try:
            snapshots = (
                session.query(
                    QualityMonitoringSnapshot
                )
                .join(
                    Dataset,
                    Dataset.id
                    == QualityMonitoringSnapshot.dataset_id,
                )
                .filter(
                    Dataset.filename == filename
                )
                .order_by(
                    QualityMonitoringSnapshot.version_number.asc()
                )
                .all()
            )

            return [
                {
                    "dataset_id": snapshot.dataset_id,
                    "version_number": snapshot.version_number,
                    "quality_score": snapshot.quality_score,
                    "grade": snapshot.grade,
                    "metrics": snapshot.metrics,
                    "summary": snapshot.summary,
                    "issues": snapshot.issues,
                    "created_at": snapshot.created_at,
                }
                for snapshot in snapshots
            ]

        finally:
            session.close()