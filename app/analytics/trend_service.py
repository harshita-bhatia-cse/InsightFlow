from __future__ import annotations

from typing import Any

import pandas as pd


class TrendService:
    CATEGORICAL_COLUMNS = [
        "Status",
        "Priority",
        "Layer",
    ]

    TIME_COLUMN_KEYWORDS = [
        "date",
        "time",
        "created",
        "updated",
    ]

    @staticmethod
    def calculate(
        dataframe: pd.DataFrame,
        dataset_id: int,
    ) -> dict[str, Any]:
        result = {
            "dataset_id": dataset_id,
            "status_trends": (
                TrendService._count_distribution(
                    dataframe,
                    "Status",
                )
            ),
            "priority_trends": (
                TrendService._count_distribution(
                    dataframe,
                    "Priority",
                )
            ),
            "layer_trends": (
                TrendService._count_distribution(
                    dataframe,
                    "Layer",
                )
            ),
            "time_column": None,
            "time_trends": {},
        }

        time_column = TrendService._find_time_column(
            dataframe
        )

        if time_column is not None:
            time_trends = TrendService._time_trends(
                dataframe,
                time_column,
            )

            if time_trends:
                result["time_column"] = time_column
                result["time_trends"] = time_trends

        return result

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
            .str.strip()
            .replace("", "Unknown")
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
    def _find_time_column(
        dataframe: pd.DataFrame,
    ) -> str | None:
        for column in dataframe.columns:
            normalized_name = str(column).lower()

            if any(
                keyword in normalized_name
                for keyword in TrendService.TIME_COLUMN_KEYWORDS
            ):
                return str(column)

        return None

    @staticmethod
    def _time_trends(
        dataframe: pd.DataFrame,
        time_column: str,
    ) -> dict[str, list[dict[str, Any]]]:
        parsed_dates = pd.to_datetime(
            dataframe[time_column],
            errors="coerce",
        ).dropna()

        if parsed_dates.empty:
            return {}

        if getattr(parsed_dates.dt, "tz", None) is not None:
            parsed_dates = parsed_dates.dt.tz_localize(None)

        return {
            "daily": TrendService._period_counts(
                parsed_dates,
                "D",
            ),
            "weekly": TrendService._period_counts(
                parsed_dates,
                "W",
            ),
            "monthly": TrendService._period_counts(
                parsed_dates,
                "M",
            ),
        }

    @staticmethod
    def _period_counts(
        dates: pd.Series,
        frequency: str,
    ) -> list[dict[str, Any]]:
        counts = (
            dates.dt.to_period(frequency)
            .value_counts()
            .sort_index()
        )

        return [
            {
                "period": str(period),
                "count": int(count),
            }
            for period, count in counts.items()
        ]

    