import json
from io import BytesIO
from pathlib import Path
import uuid
import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile

from fastapi.responses import FileResponse

from sqlalchemy import text

from app.database.connection import engine

from app.database.connection import Base, engine
#from app.database.models import PipelineRun

from app.database.models import (
    PipelineRun,
    Dataset,
    DatasetVersion,
    QualityMonitoringSnapshot,
    User,
)

from app.database.connection import SessionLocal

from app.profiling.profiler import DataProfiler
from app.database.profile_repository import DatasetProfileRepository
from app.analytics.engine import AnalyticsEngine
from app.orchestration.processor import AnalyticsWorkflowOrchestrator
from app.auth import authenticate_user, create_access_token, require_roles, register_user
from app.schemas import (
    AuthTokenResponse,
    InsightsResponse,
    KPIResponse,
    LoginRequest,
    ProfileResponse,
    QualityResponse,
    RecommendationsResponse,
    RegisterRequest,
    StatisticsResponse,
    TrendResponse,
    UserResponse,
)

app = FastAPI(
    title="InsightFlow AI",
    description="Layer 2 analytics automation with monitoring and orchestration",
    version="0.2.0",
)
Base.metadata.create_all(bind=engine)
# This is our first Data Contract:
# fields the business considers mandatory for a usable task record.
REQUIRED_COLUMNS = ["Task_ID", "Status"]

# Expected structure for the project-task CSV used in this learning project.
EXPECTED_COLUMNS = [
    "Task_ID",
    "Layer",
    "Component",
    "Status",
    "Priority",
    "Estimated_Hours"
]

# Prevent very large files from consuming too much server memory.
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
PROCESSED_DIR = Path("data/processed")
QUARANTINE_DIR = Path("data/quarantine")

@app.get("/")
def home():
    return {"message": "Welcome to InsightFlow AI"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/auth/register", response_model=AuthTokenResponse)
def register_user_route(payload: RegisterRequest):
    user = register_user(
        email=payload.email,
        username=payload.username,
        password=payload.password,
        role=payload.role,
    )
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
        },
    }


@app.post("/auth/login", response_model=AuthTokenResponse)
def login_user_route(payload: LoginRequest):
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
        },
    }


@app.get("/auth/me", response_model=UserResponse)
def get_current_user_route(current_user: User = Depends(require_roles("admin", "analyst", "viewer", "uploader"))):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role,
    }


@app.get("/admin/users", response_model=list[UserResponse])
def list_users_route(current_user: User = Depends(require_roles("admin"))):
    database_session = SessionLocal()
    try:
        users = database_session.query(User).order_by(User.id.asc()).all()
        return [
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
            }
            for user in users
        ]
    finally:
        database_session.close()


def normalize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize simple formatting issues before validation.
    Example: turns '   High  ' into 'High' and empty text into missing data.
    """
    normalized_dataframe = dataframe.copy()

    normalized_dataframe.columns = [
        str(column).strip()
        for column in normalized_dataframe.columns
    ]

    for column in normalized_dataframe.columns:
        if pd.api.types.is_string_dtype(normalized_dataframe[column]):
            normalized_dataframe[column] = (
                normalized_dataframe[column]
                .str.strip()
                .replace("", pd.NA)
            )

    return normalized_dataframe


def validate_dataframe(dataframe: pd.DataFrame) -> dict:
    """
    Check schema, required values, exact duplicate rows,
    and duplicate Task_ID values.
    """
    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in dataframe.columns
    ]

    unexpected_columns = [
        column
        for column in dataframe.columns
        if column not in EXPECTED_COLUMNS
    ]

    missing_values = {
        column: int(dataframe[column].isnull().sum())
        for column in dataframe.columns
    }

    required_field_errors = {
        column: missing_values.get(column, "column is missing")
        for column in REQUIRED_COLUMNS
        if (
            column not in dataframe.columns
            or missing_values.get(column, 0) > 0
        )
    }

    exact_duplicate_rows = int(dataframe.duplicated().sum())

    duplicate_task_id_rows = 0

    if "Task_ID" in dataframe.columns:
        valid_task_ids = dataframe["Task_ID"].dropna()

        duplicate_task_id_rows = int(
            valid_task_ids.duplicated(keep=False).sum()
        )

    is_valid = (
        len(missing_columns) == 0
        and len(required_field_errors) == 0
        and duplicate_task_id_rows == 0
    )

    return {
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "missing_values": missing_values,
        "required_field_errors": required_field_errors,
        "exact_duplicate_rows": exact_duplicate_rows,
        "duplicate_task_id_rows": duplicate_task_id_rows,
        "is_valid": is_valid
    }


def clean_dataframe(dataframe: pd.DataFrame):
    """
    Clean safe fields and quarantine risky records.

    We never invent a Task_ID or Status. Records missing either field
    are separated for manual review rather than treated as valid data.
    """
    cleaned_dataframe = normalize_dataframe(dataframe)

    rows_before_cleaning = len(cleaned_dataframe)

    exact_duplicate_rows_removed = int(
        cleaned_dataframe.duplicated().sum()
    )

    cleaned_dataframe = cleaned_dataframe.drop_duplicates()

    missing_values_filled = {}

    # These fields are useful even if initially missing,
    # so we can safely use "Unknown".
    optional_text_columns = [
        "Layer",
        "Component",
        "Priority"
    ]

    for column in optional_text_columns:
        if column in cleaned_dataframe.columns:
            missing_count = int(
                cleaned_dataframe[column].isnull().sum()
            )

            if missing_count > 0:
                cleaned_dataframe[column] = (
                    cleaned_dataframe[column].fillna("Unknown")
                )

                missing_values_filled[column] = {
                    "count": missing_count,
                    "method": "filled with 'Unknown'"
                }

    # For this learning project, missing effort estimates use the median.
    # In a real company, this policy must be approved by the business team.
    if "Estimated_Hours" in cleaned_dataframe.columns:
        missing_count = int(
            cleaned_dataframe["Estimated_Hours"].isnull().sum()
        )

        if missing_count > 0:
            median_hours = cleaned_dataframe["Estimated_Hours"].median()

            if pd.isna(median_hours):
                median_hours = 0

            cleaned_dataframe["Estimated_Hours"] = (
                cleaned_dataframe["Estimated_Hours"]
                .fillna(median_hours)
            )

            missing_values_filled["Estimated_Hours"] = {
                "count": missing_count,
                "method": f"filled with median value {median_hours}"
            }

    # A missing Task_ID or Status makes a record unsafe for analytics.
    # Duplicate Task_ID records are also quarantined, rather than guessed.
    quarantine_mask = pd.Series(
        False,
        index=cleaned_dataframe.index
    )

    for column in REQUIRED_COLUMNS:
        if column in cleaned_dataframe.columns:
            quarantine_mask = (
                quarantine_mask
                | cleaned_dataframe[column].isnull()
            )
        else:
            quarantine_mask = pd.Series(
                True,
                index=cleaned_dataframe.index
            )

    if "Task_ID" in cleaned_dataframe.columns:
        duplicate_task_id_mask = (
            cleaned_dataframe["Task_ID"].notna()
            & cleaned_dataframe["Task_ID"].duplicated(keep=False)
        )

        quarantine_mask = (
            quarantine_mask | duplicate_task_id_mask
        )

    quarantined_dataframe = cleaned_dataframe[
        quarantine_mask
    ].copy()

    ready_dataframe = cleaned_dataframe[
        ~quarantine_mask
    ].copy()

    cleaning_report = {
        "rows_received": rows_before_cleaning,
        "exact_duplicate_rows_removed": (
            exact_duplicate_rows_removed
        ),
        "rows_ready_for_analytics": len(ready_dataframe),
        "rows_quarantined_for_review": len(
            quarantined_dataframe
        ),
        "missing_values_filled": missing_values_filled
    }

    return (
        ready_dataframe,
        quarantined_dataframe,
        cleaning_report
    )


def dataframe_preview(dataframe: pd.DataFrame) -> list:
    """Return JSON-safe preview records for the API response."""
    return json.loads(
        dataframe.head(5).to_json(orient="records")
    )


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please choose a CSV file."
        )

    if Path(file.filename).suffix.lower() != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file only."
        )

    file_contents = await file.read()

    if len(file_contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV file is empty."
        )

    if len(file_contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File is too large. Maximum allowed size is 5 MB."
        )

    try:
        dataframe = pd.read_csv(BytesIO(file_contents))
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=(
                "The file could not be read as a valid CSV. "
                f"Details: {str(error)}"
            )
        )

    dataframe = normalize_dataframe(dataframe)

    validation_before_cleaning = validate_dataframe(
        dataframe
    )

    (
        cleaned_dataframe,
        quarantined_dataframe,
        cleaning_report
    ) = clean_dataframe(dataframe)

    profile_report = (
        DataProfiler.profile_dataframe(
            cleaned_dataframe
        )
    )

    validation_after_cleaning = validate_dataframe(
        cleaned_dataframe
    )

    quality_status = (
        "ready_for_analytics"
        if validation_after_cleaning["is_valid"]
        and len(quarantined_dataframe) == 0
        else "needs_review"
    )    
    run_id = str(uuid.uuid4())

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    processed_file_path = (
        PROCESSED_DIR / f"{run_id}_ready.csv"
    )

    quarantine_file_path = (
        QUARANTINE_DIR / f"{run_id}_quarantine.csv"
    )

    cleaned_dataframe.to_csv(
        processed_file_path,
        index=False
    )

    quarantined_dataframe.to_csv(
        quarantine_file_path,
        index=False
    )
    base_table_name = (
    Path(file.filename)
    .stem
    .lower()
    .replace(" ", "_")
    )

    run_id_short = run_id.replace(
        "-",
        "",
    )[:12]

    table_name = (
        f"{base_table_name}_{run_id_short}"
    )

    dataset = Dataset(
    filename=file.filename,
    table_name=table_name,
    rows_count=len(cleaned_dataframe),
    columns_count=len(cleaned_dataframe.columns)
    )

    #database_session.add(dataset)


    cleaned_dataframe.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False
    )

    database_session = SessionLocal()

    DatasetProfileRepository.save_profile(
        dataset_name=table_name,
        profile_data=profile_report
    )

    try:
        latest_version = (
            database_session.query(
            DatasetVersion
        )
        .filter(
            DatasetVersion.filename == file.filename
        )
        .order_by(
            DatasetVersion.version_number.desc()
        )
        .first()
        )

        next_version_number = (
            latest_version.version_number + 1
            if latest_version is not None
            else 1
        )

    # Save pipeline run metadata
        pipeline_run = PipelineRun(
            id=run_id,
            filename=file.filename,
            quality_status=quality_status,
            original_rows=len(dataframe),
            ready_rows=len(cleaned_dataframe),
            quarantined_rows=len(quarantined_dataframe),
            validation_report=validation_after_cleaning
        )
        database_session.add(pipeline_run)
        dataset = Dataset(
            filename=file.filename,
            table_name=table_name,
            rows_count=len(cleaned_dataframe),
            columns_count=len(cleaned_dataframe.columns)
        )
        database_session.add(dataset)
        database_session.flush()

        dataset_version = DatasetVersion(
            filename=file.filename,
            version_number=next_version_number,
            run_id=run_id,
            dataset_id=dataset.id,
            table_name=table_name,
            rows_count=len(cleaned_dataframe),
            columns_count=len(cleaned_dataframe.columns),
            quality_status=quality_status,
        )

        database_session.add(
            dataset_version
        )


        database_session.commit()

    except Exception as error:
        database_session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )

    finally:
        database_session.close()

    try:
        analytics_result = AnalyticsWorkflowOrchestrator.run_for_dataset(dataset.id)
    except Exception as error:
        analytics_result = {
            "dataset_id": dataset.id,
            "error": str(error),
            "status": "analysis_failed",
        }

    return {
        "message": "CSV processed successfully",
        "run_id": run_id,
        "filename": file.filename,
        "table_name": table_name,
        "quality_status": quality_status,
        "profile_report": profile_report,
        "summary": {
            "original_rows": len(dataframe),
            "ready_rows": len(cleaned_dataframe),
            "quarantined_rows": len(quarantined_dataframe),
            "total_columns": len(dataframe.columns)
        },
        "downloads": {
            "ready_dataset": (
                f"/downloads/{run_id}/ready"
            ),
            "quarantined_dataset": (
                f"/downloads/{run_id}/quarantine"
            )
        },
        "validation_before_cleaning": (
            validation_before_cleaning
        ),
        "cleaning_report": cleaning_report,
        "validation_after_cleaning": (
            validation_after_cleaning
        ),
        "ready_data_preview": dataframe_preview(
            cleaned_dataframe
        ),
        "quarantined_data_preview": dataframe_preview(
            quarantined_dataframe
        ),
        "analytics_result": analytics_result,
    }


@app.get("/downloads/{run_id}/{dataset_type}")
def download_dataset(run_id: str, dataset_type: str):
    try:
        safe_run_id = str(uuid.UUID(run_id))
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    if dataset_type == "ready":
        file_path = (
            PROCESSED_DIR / f"{safe_run_id}_ready.csv"
        )
        download_name = "insightflow_ready_data.csv"

    elif dataset_type == "quarantine":
        file_path = (
            QUARANTINE_DIR
            / f"{safe_run_id}_quarantine.csv"
        )
        download_name = "insightflow_quarantined_data.csv"

    else:
        raise HTTPException(
            status_code=404,
            detail="Dataset type not found."
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found."
        )

    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type="text/csv"
    )

@app.get("/database-health")
def database_health():
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    return {
        "status": "connected",
        "database": database_name
    }
@app.get("/pipeline-runs")
def get_pipeline_runs():

    database_session = SessionLocal()

    try:
        runs = database_session.query(
            PipelineRun
        ).all()

        return runs

    finally:
        database_session.close()

@app.get("/datasets")
def get_datasets():

    database_session = SessionLocal()

    try:
        datasets = database_session.query(
            Dataset
        ).all()

        return datasets

    finally:
        database_session.close()


@app.get("/datasets/{dataset_id}/preview")
def preview_dataset(dataset_id: int):
    with engine.connect() as connection:
        dataset_result = connection.execute(
            text(
                """
                SELECT id, table_name, filename
                FROM datasets
                WHERE id = :dataset_id
                """
            ),
            {"dataset_id": dataset_id}
        ).mappings().first()

        if dataset_result is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found."
            )

        table_name = dataset_result["table_name"]

        # Safety check: only allow letters, numbers, and underscores.
        # This prevents unsafe SQL table names.
        if not table_name.replace("_", "").isalnum():
            raise HTTPException(
                status_code=400,
                detail="Invalid dataset table name."
            )

        preview_result = connection.execute(
            text(
                f"""
                SELECT *
                FROM "{table_name}"
                LIMIT 20
                """
            )
        ).mappings().all()

    return {
        "dataset_id": dataset_result["id"],
        "filename": dataset_result["filename"],
        "table_name": table_name,
        "rows": [
            dict(row)
            for row in preview_result
        ]
    }


@app.get("/profiles/{dataset_id}", response_model=ProfileResponse)
def get_dataset_profile(dataset_id: int):
    return AnalyticsEngine.profile(dataset_id)

@app.get(
    "/analytics/quality/{dataset_id}",
    response_model=QualityResponse,
)
def get_dataset_quality(dataset_id: int):
    return AnalyticsEngine.quality(dataset_id)


@app.get(
    "/analytics/statistics/{dataset_id}",
    response_model=StatisticsResponse,
)
def get_dataset_statistics(dataset_id: int):
    return AnalyticsEngine.statistics(dataset_id)


@app.get(
    "/analytics/kpis/{dataset_id}",
    response_model=KPIResponse,
)
def get_dataset_kpis(dataset_id: int):
    return AnalyticsEngine.kpis(dataset_id)


@app.get(
    "/analytics/trends/{dataset_id}",
    response_model=TrendResponse,
)
def get_dataset_trends(dataset_id: int):
    return AnalyticsEngine.trends(dataset_id)


@app.get(
    "/analytics/insights/{dataset_id}",
    response_model=InsightsResponse,
)
def get_dataset_insights(dataset_id: int):
    return AnalyticsEngine.insights(dataset_id)


@app.get(
    "/analytics/recommendations/{dataset_id}",
    response_model=RecommendationsResponse,
)
def get_dataset_recommendations(dataset_id: int):
    return AnalyticsEngine.recommendations(dataset_id)


@app.get("/dataset-versions/{filename}")
def get_dataset_versions(filename: str):
    database_session = SessionLocal()

    try:
        versions = (
            database_session.query(
                DatasetVersion
            )
            .filter(
                DatasetVersion.filename == filename
            )
            .order_by(
                DatasetVersion.version_number.desc()
            )
            .all()
        )

        return [
            {
                "id": version.id,
                "filename": version.filename,
                "version_number": version.version_number,
                "run_id": version.run_id,
                "dataset_id": version.dataset_id,
                "table_name": version.table_name,
                "rows_count": version.rows_count,
                "columns_count": version.columns_count,
                "quality_status": version.quality_status,
                "created_at": version.created_at,
            }
            for version in versions
        ]

    finally:
        database_session.close()


@app.get("/quality-monitoring/{filename}")
def get_quality_monitoring_history(filename: str):
    from app.analytics.quality_monitoring_service import QualityMonitoringService

    return {
        "filename": filename,
        "history": QualityMonitoringService.history(filename),
    }
