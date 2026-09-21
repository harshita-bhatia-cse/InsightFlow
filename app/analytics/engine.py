from __future__ import annotations
from app.analytics.kpi_service import KPIService
from app.analytics.trend_service import TrendService
from app.analytics.insight_service import InsightService
from app.analytics.quality_service import QualityService
from app.analytics.recommendation_service import (
    RecommendationService
)
from app.analytics.analytics_repository import (
    AnalyticsRepository
)
import math
import re
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy import text

from app.database.connection import SessionLocal, engine
from app.database.models import (
    Dataset,
    PipelineRun,
)
SAFE_TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
COMPLETED_VALUES = {"completed", "complete", "done", "closed"}


class AnalyticsEngine:
    @staticmethod
    def load_dataset(dataset_id: int) -> tuple[dict[str, Any], pd.DataFrame]:
        session = SessionLocal()
        try:
            dataset = session.get(Dataset, dataset_id)
            if dataset is None:
                raise HTTPException(status_code=404, detail="Dataset not found.")
            metadata = {"id": dataset.id, "filename": dataset.filename, "table_name": dataset.table_name}
        finally:
            session.close()
        if not SAFE_TABLE_NAME.fullmatch(metadata["table_name"]):
            raise HTTPException(status_code=400, detail="Dataset has an invalid table name.")
        dataframe = pd.read_sql_query(text(f'SELECT * FROM "{metadata["table_name"]}"'), engine)
        return metadata, dataframe

    @staticmethod
    def profile(dataset_id: int) -> dict[str, Any]:
        dataset, dataframe = AnalyticsEngine.load_dataset(dataset_id)
        numeric = dataframe.select_dtypes(include="number").columns.tolist()
        datetime_columns = dataframe.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
        columns = []
        for column in dataframe.columns:
            series = dataframe[column]
            kind = "numeric" if column in numeric else "datetime" if column in datetime_columns else "categorical"
            columns.append({"name": str(column), "kind": kind, "data_type": str(series.dtype),
                            "missing_count": int(series.isna().sum()), "missing_rate": _rate(series.isna().sum(), len(dataframe)),
                            "unique_count": int(series.nunique(dropna=True))})
        result = {"dataset_id": dataset["id"], "filename": dataset["filename"], "table_name": dataset["table_name"],
                  "summary": {"rows": int(len(dataframe)), "columns": int(len(dataframe.columns))},
                  "missing_value_analysis": {str(c): int(dataframe[c].isna().sum()) for c in dataframe.columns},
                  "numeric_columns": [str(c) for c in numeric],
                  "categorical_columns": [str(c) for c in dataframe.select_dtypes(exclude=["number", "datetime", "datetimetz"]).columns],
                  "datetime_columns": [str(c) for c in datetime_columns], "columns": columns}
        AnalyticsEngine._save_analysis(dataset_id, "profile", result)
        return result


    @staticmethod
    def quality(dataset_id: int) -> dict[str, Any]:
        """
        Calculate and persist the data-quality score for a dataset.
        """
        dataset, dataframe = AnalyticsEngine.load_dataset(
            dataset_id
        )

        session = SessionLocal()

        try:
            pipeline_run = (
                session.query(PipelineRun)
                .filter(
                    PipelineRun.filename == dataset["filename"]
                )
                .order_by(
                    PipelineRun.created_at.desc()
                )
                .first()
            )

            if pipeline_run is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Pipeline metadata was not found "
                        "for this dataset."
                    )
                )

            pipeline_run_data = {
                "original_rows": (
                    pipeline_run.original_rows
                ),
                "ready_rows": pipeline_run.ready_rows,
                "quarantined_rows": (
                    pipeline_run.quarantined_rows
                ),
                "validation_report": (
                    pipeline_run.validation_report
                ),
            }

        finally:
            session.close()

        quality_result = QualityService.calculate(
            pipeline_run=pipeline_run_data,
            dataset_rows=len(dataframe),
        )

        quality_result.update(
            {
                "dataset_id": dataset["id"],
                "filename": dataset["filename"],
                "table_name": dataset["table_name"],
            }
        )

        AnalyticsEngine._save_analysis(
            dataset_id=dataset_id,
            analysis_type="quality",
            result=quality_result,
        )

        return quality_result

    @staticmethod
    def statistics(dataset_id: int) -> dict[str, Any]:
        _, dataframe = AnalyticsEngine.load_dataset(dataset_id)
        numeric = dataframe.select_dtypes(include="number")
        stats, outliers = {}, {}
        for column in numeric.columns:
            series = numeric[column].dropna()
            if series.empty:
                continue
            q1, q3 = series.quantile([0.25, 0.75]); iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outlier_count = int(((series < lower) | (series > upper)).sum())
            stats[str(column)] = {"mean": float(series.mean()), "median": float(series.median()), "std": float(series.std(ddof=0)), "min": float(series.min()), "max": float(series.max()), "count": int(series.count())}
            outliers[str(column)] = {"count": outlier_count, "rate": _rate(outlier_count, len(series)), "lower_bound": float(lower), "upper_bound": float(upper)}
        result = {"dataset_id": dataset_id, "numeric_statistics": stats,
                  "correlation_matrix": numeric.corr(numeric_only=True).round(4).fillna(0).to_dict(),
                  "outlier_summary": outliers}
        AnalyticsEngine._save_analysis(dataset_id, "statistics", result)
        return result

    @staticmethod
    def kpis(dataset_id: int) -> dict[str, Any]:
        """
        Load a stored dataset, calculate its KPIs,
        persist the result, and return it to the API.
        """
        _, dataframe = AnalyticsEngine.load_dataset(
            dataset_id
        )

        kpi_result = KPIService.calculate(
            dataframe=dataframe,
            dataset_id=dataset_id,
        )

        AnalyticsEngine._save_analysis(
            dataset_id=dataset_id,
            analysis_type="kpis",
            result=kpi_result,
        )

        return kpi_result

    @staticmethod
    def trends(dataset_id: int) -> dict[str, Any]:
        """
        Load a stored dataset, calculate trends,
        persist the result, and return it to the API.
        """
        _, dataframe = AnalyticsEngine.load_dataset(
            dataset_id
        )

        trend_result = TrendService.calculate(
            dataframe=dataframe,
            dataset_id=dataset_id,
        )

        AnalyticsEngine._save_analysis(
            dataset_id=dataset_id,
            analysis_type="trends",
            result=trend_result,
        )

        return trend_result

    @staticmethod
    def insights(dataset_id: int) -> dict[str, Any]:
        kpi_data = AnalyticsEngine.kpis(dataset_id)
        trend_data = AnalyticsEngine.trends(dataset_id)
        items = InsightService.generate(
            kpi_data=kpi_data,
            trend_data=trend_data,
        )
        AnalyticsEngine._replace_insights(dataset_id, items)
        return {"dataset_id": dataset_id, "insights": items}

    @staticmethod
    def recommendations(dataset_id: int) -> dict[str, Any]:
        """
        Generate and persist recommendations for a dataset.
        """
        kpi_data = AnalyticsEngine.kpis(
            dataset_id
        )

        items = RecommendationService.generate(
            kpi_data=kpi_data,
        )

        AnalyticsEngine._replace_recommendations(
            dataset_id,
            items,
        )

        return {
            "dataset_id": dataset_id,
            "recommendations": items,
        }

    @staticmethod
    def _save_analysis(
        dataset_id: int,
        analysis_type: str,
        result: dict[str, Any],
    ) -> None:
        AnalyticsRepository.save_analysis(
            dataset_id=dataset_id,
            analysis_type=analysis_type,
            result=_json_safe(result),
        )

    @staticmethod
    def _replace_insights(
        dataset_id: int,
        items: list[dict[str, Any]],
    ) -> None:
        AnalyticsRepository.replace_insights(
            dataset_id=dataset_id,
            insights=items,
        )

    @staticmethod
    def _replace_recommendations(
        dataset_id: int,
        items: list[dict[str, Any]],
    ) -> None:
        AnalyticsRepository.replace_recommendations(
            dataset_id=dataset_id,
            recommendations=items,
        )


def _normalised_column(dataframe: pd.DataFrame, name: str) -> pd.Series | None:
    return dataframe[name].fillna("").astype(str).str.strip().str.casefold() if name in dataframe else None

def _rate(numerator: float, denominator: int) -> float:
    return round((float(numerator) / denominator * 100) if denominator else 0.0, 2)

def _counts(dataframe: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    if column not in dataframe: return []
    return [{"name": str(name), "count": int(count)} for name, count in dataframe[column].fillna("Unknown").astype(str).value_counts().items()]

def _workload(dataframe: pd.DataFrame, column: str, hours: pd.Series) -> list[dict[str, Any]]:
    if column not in dataframe: return []
    frame = pd.DataFrame({"name": dataframe[column].fillna("Unknown").astype(str), "hours": hours.fillna(0)})
    grouped = frame.groupby("name", as_index=False).agg(task_count=("name", "size"), estimated_hours=("hours", "sum")).sort_values("estimated_hours", ascending=False)
    return [{"name": row.name, "task_count": int(row.task_count), "estimated_hours": float(row.estimated_hours)} for row in grouped.itertuples(index=False)]

def _period_counts(series: pd.Series, frequency: str) -> list[dict[str, Any]]:
    counts = series.dt.to_period(frequency).value_counts().sort_index()
    return [{"period": str(period), "count": int(count)} for period, count in counts.items()]

def _json_safe(value: Any) -> Any:
    if isinstance(value, dict): return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list): return [_json_safe(item) for item in value]
    if isinstance(value, np.integer): return int(value)
    if isinstance(value, np.floating): return None if math.isnan(float(value)) else float(value)
    if isinstance(value, (pd.Timestamp, datetime, date)): return value.isoformat()
    return value
