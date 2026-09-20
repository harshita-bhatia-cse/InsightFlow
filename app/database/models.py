import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base

from sqlalchemy import JSON

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    quality_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    original_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    ready_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    quarantined_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    validation_report: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    table_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    rows_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    columns_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class DatasetProfile(Base):

    __tablename__ = "dataset_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    dataset_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    profile_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class DatasetAnalytics(Base):
    """Persisted Layer 2 output for one dataset and analysis type."""
    __tablename__ = "dataset_analytics"
    __table_args__ = (
        UniqueConstraint("dataset_id", "analysis_type", name="uq_dataset_analysis_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)
    result_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DatasetInsight(Base):
    __tablename__ = "dataset_insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DatasetRecommendation(Base):
    __tablename__ = "dataset_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
