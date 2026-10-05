from datetime import datetime

from pydantic import BaseModel, Field


class DatasetProjectAssignment(BaseModel):
    project_id: int = Field(
        ...,
        gt=0,
    )


class DatasetResponse(BaseModel):
    id: int
    filename: str
    table_name: str
    rows_count: int
    columns_count: int
    project_id: int | None = None
    created_at: datetime