from __future__ import annotations

from typing import Any

import pandas as pd


COMPLETED_STATUSES = {
    "completed",
    "complete",
    "done",
    "closed",
}

HIGH_PRIORITY_VALUES = {
    "high",
    "critical",
    "urgent",
}


class KPIService:
    @staticmethod
    def calculate(
        dataframe: pd.DataFrame,
        dataset_id: int,
    ) -> dict[str, Any]:
        total_tasks = len(dataframe)

        status_values = KPIService._normalise_column(
            dataframe,
            "Status",
        )

        priority_values = KPIService._normalise_column(
            dataframe,
            "Priority",
        )

        completed_tasks = 0
        pending_tasks = 0
        high_priority_pending_tasks = 0

        if status_values is not None:
            completed_mask = status_values.isin(
                COMPLETED_STATUSES
            )

            completed_tasks = int(
                completed_mask.sum()
            )

            pending_mask = ~completed_mask

            pending_tasks = int(
                pending_mask.sum()
            )

            if priority_values is not None:
                high_priority_pending_tasks = int(
                    (
                        priority_values.isin(
                            HIGH_PRIORITY_VALUES
                        )
                        & pending_mask
                    ).sum()
                )

        estimated_hours = KPIService._estimated_hours(
            dataframe
        )

        return {
            "dataset_id": dataset_id,
            "total_tasks": int(total_tasks),
            "completed_tasks": completed_tasks,
            "completion_rate": KPIService._percentage(
                completed_tasks,
                total_tasks,
            ),
            "pending_tasks": pending_tasks,
            "pending_rate": KPIService._percentage(
                pending_tasks,
                total_tasks,
            ),
            "high_priority_pending_tasks": (
                high_priority_pending_tasks
            ),
            "total_estimated_hours": float(
                estimated_hours.sum()
            ),
            "layer_workload_distribution": (
                KPIService._workload_distribution(
                    dataframe,
                    "Layer",
                    estimated_hours,
                )
            ),
            "component_distribution": (
                KPIService._count_distribution(
                    dataframe,
                    "Component",
                )
            ),
        }

    @staticmethod
    def _normalise_column(
        dataframe: pd.DataFrame,
        column_name: str,
    ) -> pd.Series | None:
        if column_name not in dataframe.columns:
            return None

        return (
            dataframe[column_name]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

    @staticmethod
    def _estimated_hours(
        dataframe: pd.DataFrame,
    ) -> pd.Series:
        if "Estimated_Hours" not in dataframe.columns:
            return pd.Series(
                0.0,
                index=dataframe.index,
                dtype=float,
            )

        return pd.to_numeric(
            dataframe["Estimated_Hours"],
            errors="coerce",
        ).fillna(0.0)

    @staticmethod
    def _percentage(
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator == 0:
            return 0.0

        return round(
            (numerator / denominator) * 100,
            2,
        )

    @staticmethod
    def _count_distribution(
        dataframe: pd.DataFrame,
        column_name: str,
    ) -> list[dict[str, Any]]:
        if column_name not in dataframe.columns:
            return []

        counts = (
            dataframe[column_name]
            .fillna("Unknown")
            .astype(str)
            .value_counts()
        )

        return [
            {
                "name": str(name),
                "count": int(count),
            }
            for name, count in counts.items()
        ]

    @staticmethod
    def _workload_distribution(
        dataframe: pd.DataFrame,
        column_name: str,
        estimated_hours: pd.Series,
    ) -> list[dict[str, Any]]:
        if column_name not in dataframe.columns:
            return []

        workload_dataframe = pd.DataFrame(
            {
                "name": (
                    dataframe[column_name]
                    .fillna("Unknown")
                    .astype(str)
                ),
                "estimated_hours": estimated_hours,
            }
        )

        grouped = (
            workload_dataframe
            .groupby("name", as_index=False)
            .agg(
                task_count=("name", "size"),
                estimated_hours=(
                    "estimated_hours",
                    "sum",
                ),
            )
            .sort_values(
                "estimated_hours",
                ascending=False,
            )
        )

        return [
            {
                "name": row.name,
                "task_count": int(row.task_count),
                "estimated_hours": float(
                    row.estimated_hours
                ),
            }
            for row in grouped.itertuples(index=False)
        ]