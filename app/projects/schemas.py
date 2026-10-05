from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    workspace_id: int


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    workspace_id: int
    created_at: datetime