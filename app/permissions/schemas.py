from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ProjectMemberRole = Literal[
    "viewer",
    "analyst",
    "editor",
    "owner",
]


class ProjectMemberCreate(BaseModel):
    user_id: int = Field(
        ...,
        gt=0,
    )
    role: ProjectMemberRole = "viewer"


class ProjectMemberRoleUpdate(BaseModel):
    role: ProjectMemberRole


class ProjectMemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: ProjectMemberRole
    created_at: datetime