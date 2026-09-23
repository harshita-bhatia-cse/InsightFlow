from __future__ import annotations

from typing import Any

from app.config.settings import settings
from app.core.logging import logger


class AlertService:
    @staticmethod
    def evaluate(dataset_id: int, quality_result: dict[str, Any]) -> dict[str, Any]:
        score = float(quality_result.get("quality_score", 0.0))

        if score < settings.quality_alert_threshold:
            logger.warning(
                "Quality alert triggered for dataset %s with score %.2f",
                dataset_id,
                score,
            )
            return {
                "status": "alert",
                "message": "Dataset quality dropped below the configured threshold.",
                "quality_score": score,
            }

        return {
            "status": "healthy",
            "message": "Quality is within the configured threshold.",
            "quality_score": score,
        }
