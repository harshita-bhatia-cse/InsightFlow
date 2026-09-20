from __future__ import annotations

from typing import Any


class InsightService:
    COMPLETION_RATE_TARGET = 70.0
    PENDING_RATE_THRESHOLD = 50.0

    @staticmethod
    def generate(
        kpi_data: dict[str, Any],
        trend_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []

        InsightService._add_completion_insight(
            insights,
            kpi_data,
        )

        InsightService._add_pending_backlog_insight(
            insights,
            kpi_data,
        )

        InsightService._add_high_priority_insight(
            insights,
            kpi_data,
        )

        InsightService._add_workload_insight(
            insights,
            kpi_data,
        )

        InsightService._add_status_insight(
            insights,
            trend_data,
        )

        return insights

    @staticmethod
    def _add_completion_insight(
        insights: list[dict[str, Any]],
        kpi_data: dict[str, Any],
    ) -> None:
        completion_rate = float(
            kpi_data.get("completion_rate", 0)
        )

        if completion_rate < InsightService.COMPLETION_RATE_TARGET:
            insights.append(
                {
                    "severity": "high",
                    "title": "Completion rate below target",
                    "message": (
                        f"Completion is {completion_rate:.1f}%, "
                        f"below the {InsightService.COMPLETION_RATE_TARGET:.0f}% target."
                    ),
                    "evidence": {
                        "completion_rate": completion_rate,
                        "target": (
                            InsightService.COMPLETION_RATE_TARGET
                        ),
                    },
                }
            )

    @staticmethod
    def _add_pending_backlog_insight(
        insights: list[dict[str, Any]],
        kpi_data: dict[str, Any],
    ) -> None:
        pending_rate = float(
            kpi_data.get("pending_rate", 0)
        )

        if pending_rate > InsightService.PENDING_RATE_THRESHOLD:
            insights.append(
                {
                    "severity": "medium",
                    "title": "Large pending backlog",
                    "message": (
                        f"{pending_rate:.1f}% of tasks are still pending."
                    ),
                    "evidence": {
                        "pending_rate": pending_rate,
                        "threshold": (
                            InsightService.PENDING_RATE_THRESHOLD
                        ),
                    },
                }
            )

    @staticmethod
    def _add_high_priority_insight(
        insights: list[dict[str, Any]],
        kpi_data: dict[str, Any],
    ) -> None:
        high_priority_pending = int(
            kpi_data.get(
                "high_priority_pending_tasks",
                0,
            )
        )

        if high_priority_pending > 0:
            insights.append(
                {
                    "severity": "high",
                    "title": "High-priority backlog",
                    "message": (
                        f"{high_priority_pending} high-priority "
                        "tasks are not completed."
                    ),
                    "evidence": {
                        "high_priority_pending_tasks": (
                            high_priority_pending
                        ),
                    },
                }
            )

    @staticmethod
    def _add_workload_insight(
        insights: list[dict[str, Any]],
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
            key=lambda item: item.get(
                "estimated_hours",
                0,
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

        insights.append(
            {
                "severity": "medium",
                "title": "Highest workload layer",
                "message": (
                    f"{layer_name} has the highest workload "
                    f"at {estimated_hours:.1f} estimated hours."
                ),
                "evidence": {
                    "layer": layer_name,
                    "estimated_hours": estimated_hours,
                },
            }
        )

    @staticmethod
    def _add_status_insight(
        insights: list[dict[str, Any]],
        trend_data: dict[str, Any],
    ) -> None:
        status_trends = trend_data.get(
            "status_trends",
            [],
        )

        if not status_trends:
            return

        largest_status_group = max(
            status_trends,
            key=lambda item: item.get("count", 0),
        )

        status_name = largest_status_group.get(
            "name",
            "Unknown",
        )

        task_count = int(
            largest_status_group.get("count", 0)
        )

        insights.append(
            {
                "severity": "low",
                "title": "Largest task status group",
                "message": (
                    f"{status_name} is the largest task group "
                    f"with {task_count} tasks."
                ),
                "evidence": {
                    "status": status_name,
                    "task_count": task_count,
                },
            }
        )