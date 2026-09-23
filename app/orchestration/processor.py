from __future__ import annotations

from app.analytics.engine import AnalyticsEngine
from app.core.logging import logger
from app.services.alert_service import AlertService
from app.services.export_service import ExportService


class AnalyticsWorkflowOrchestrator:
    @staticmethod
    def run_for_dataset(dataset_id: int) -> dict:
        logger.info("Starting analytics workflow for dataset %s", dataset_id)

        profile = AnalyticsEngine.profile(dataset_id)
        quality = AnalyticsEngine.quality(dataset_id)
        statistics = AnalyticsEngine.statistics(dataset_id)
        kpis = AnalyticsEngine.kpis(dataset_id)
        trends = AnalyticsEngine.trends(dataset_id)
        insights = AnalyticsEngine.insights(dataset_id)
        recommendations = AnalyticsEngine.recommendations(dataset_id)

        alert = AlertService.evaluate(dataset_id, quality)

        payload = {
            "dataset_id": dataset_id,
            "profile": profile,
            "quality": quality,
            "statistics": statistics,
            "kpis": kpis,
            "trends": trends,
            "insights": insights,
            "recommendations": recommendations,
            "alert": alert,
        }

        export_path = ExportService.export_summary(dataset_id, payload)
        logger.info("Analytics workflow finished for dataset %s; export saved to %s", dataset_id, export_path)

        return payload
