from __future__ import annotations

from typing import Any


class RecommendationService:
    """Generate transparent, rule-based recommendations from KPI results."""

    COMPLETION_RATE_TARGET = 70.0
    PENDING_RATE_THRESHOLD = 50.0

    @staticmethod
    def generate(
        kpi_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []

        RecommendationService._add_workload_recommendation(
            recommendations,
            kpi_data,
        )

        RecommendationService._add_high_priority_recommendation(
            recommendations,
            kpi_data,
        )

        RecommendationService._add_completion_recommendation(
            recommendations,
            kpi_data,
        )

        RecommendationService._add_backlog_recommendation(
            recommendations,
            kpi_data,
        )

        return recommendations

    @staticmethod
    def _add_workload_recommendation(
        recommendations: list[dict[str, Any]],
        kpi_data: dict[str, Any],
    ) -> None:
        workload = kpi_data.get(
            "layer_workload_distribution",
            [],
        )

        if not workload:
            return

        highest_workload_layer = max(
            workload,
            key=lambda item: float(
                item.get("estimated_hours", 0)
            ),
        )

        layer_name = highest_workload_layer.get(
            "name",
            "Unknown",
        )

        estimated_hours = float(
            highest_workload_layer.get(
                "estimated_hours",
                0,
            )
        )

        recommendations.append(
            {
                "priority": "medium",
                "recommendation": (
                    f"Review capacity in {layer_name}."
                ),
                "rationale": (
                    f"{layer_name} carries "
                    f"{estimated_hours:.1f} estimated hours, "
                    "the highest workload."
                ),
                "evidence": {
                    "layer": layer_name,
                    "estimated_hours": estimated_hours,
                },
            }
        )

    @staticmethod
    def _add_high_priority_recommendation(
        recommendations: list[dict[str, Any]],
        kpi_data: dict[str, Any],
    ) -> None:
        high_priority_pending = int(
            kpi_data.get(
                "high_priority_pending_tasks",
                0,
            )
        )

        if high_priority_pending <= 0:
            return

        recommendations.append(
            {
                "priority": "high",
                "recommendation": (
                    "Prioritize high-risk pending tasks "
                    "in the next planning cycle."
                ),
                "rationale": (
                    f"{high_priority_pending} high-priority "
                    "tasks are still open."
                ),
                "evidence": {
                    "high_priority_pending_tasks": (
                        high_priority_pending
                    ),
                },
            }
        )

    @staticmethod
    def _add_completion_recommendation(
        recommendations: list[dict[str, Any]],
        kpi_data: dict[str, Any],
    ) -> None:
        completion_rate = float(
            kpi_data.get(
                "completion_rate",
                0,
            )
        )

        if completion_rate >= (
            RecommendationService.COMPLETION_RATE_TARGET
        ):
            return

        recommendations.append(
            {
                "priority": "high",
                "recommendation": (
                    "Create a recovery plan for "
                    "incomplete tasks."
                ),
                "rationale": (
                    f"Current completion rate is "
                    f"{completion_rate:.1f}% versus the "
                    f"{RecommendationService.COMPLETION_RATE_TARGET:.0f}% target."
                ),
                "evidence": {
                    "completion_rate": completion_rate,
                    "target": (
                        RecommendationService.COMPLETION_RATE_TARGET
                    ),
                },
            }
        )

    @staticmethod
    def _add_backlog_recommendation(
        recommendations: list[dict[str, Any]],
        kpi_data: dict[str, Any],
    ) -> None:
        pending_rate = float(
            kpi_data.get(
                "pending_rate",
                0,
            )
        )

        if pending_rate <= (
            RecommendationService.PENDING_RATE_THRESHOLD
        ):
            return

        recommendations.append(
            {
                "priority": "medium",
                "recommendation": (
                    "Break down the pending backlog "
                    "into smaller delivery milestones."
                ),
                "rationale": (
                    f"{pending_rate:.1f}% of tasks are still "
                    "pending, which is above the "
                    f"{RecommendationService.PENDING_RATE_THRESHOLD:.0f}% threshold."
                ),
                "evidence": {
                    "pending_rate": pending_rate,
                    "threshold": (
                        RecommendationService.PENDING_RATE_THRESHOLD
                    ),
                },
            }
        )