from typing import Any

from pydantic import BaseModel, Field


class DistributionItem(BaseModel):
    name: str
    count: int


class WorkloadItem(BaseModel):
    name: str
    task_count: int
    estimated_hours: float


class PeriodCount(BaseModel):
    period: str
    count: int


class ProfileColumn(BaseModel):
    name: str
    kind: str
    data_type: str
    missing_count: int
    missing_rate: float
    unique_count: int


class ProfileSummary(BaseModel):
    rows: int
    columns: int


class ProfileResponse(BaseModel):
    dataset_id: int
    filename: str
    table_name: str
    summary: ProfileSummary
    missing_value_analysis: dict[str, int]
    numeric_columns: list[str]
    categorical_columns: list[str]
    datetime_columns: list[str]
    columns: list[ProfileColumn]


class QualityMetrics(BaseModel):
    completeness_score: float
    uniqueness_score: float
    validity_score: float
    readiness_score: float
    quarantine_rate: float


class QualitySummary(BaseModel):
    original_rows: int
    ready_rows: int
    quarantined_rows: int
    dataset_rows: int
    missing_value_count: int
    duplicate_row_count: int
    duplicate_task_id_count: int


class QualityIssue(BaseModel):
    type: str
    severity: str
    count: int
    message: str
    details: Any | None = None


class QualityResponse(BaseModel):
    dataset_id: int
    filename: str
    table_name: str
    quality_score: float
    grade: str
    metrics: QualityMetrics
    summary: QualitySummary
    issues: list[QualityIssue]


class NumericStatistics(BaseModel):
    mean: float
    median: float
    std: float
    min: float
    max: float
    count: int


class OutlierSummary(BaseModel):
    count: int
    rate: float
    lower_bound: float
    upper_bound: float


class StatisticsResponse(BaseModel):
    dataset_id: int
    numeric_statistics: dict[str, NumericStatistics]
    correlation_matrix: dict[str, dict[str, float]]
    outlier_summary: dict[str, OutlierSummary]


class KPIResponse(BaseModel):
    dataset_id: int
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    pending_tasks: int
    pending_rate: float
    high_priority_pending_tasks: int
    total_estimated_hours: float
    layer_workload_distribution: list[WorkloadItem]
    component_distribution: list[DistributionItem]


class TrendResponse(BaseModel):
    dataset_id: int
    status_trends: list[DistributionItem]
    priority_trends: list[DistributionItem]
    layer_trends: list[DistributionItem]
    time_column: str | None
    time_trends: dict[str, list[PeriodCount]]


class Insight(BaseModel):
    severity: str
    title: str
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class InsightsResponse(BaseModel):
    dataset_id: int
    insights: list[Insight]


class Recommendation(BaseModel):
    priority: str
    recommendation: str
    rationale: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class RecommendationsResponse(BaseModel):
    dataset_id: int
    recommendations: list[Recommendation]


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    role: str = "viewer"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
