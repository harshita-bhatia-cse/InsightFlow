from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database.connection import SessionLocal
from app.database.models import User
from app.permissions.schemas import (
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberRoleUpdate,
)
from app.permissions.services import ProjectPermissionService


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_project_owner(
    project_id: int,
    current_user: User,
    db: Session,
) -> ProjectPermissionService:
    service = ProjectPermissionService(db)

    if not service.user_owns_project(
        project_id=project_id,
        user_id=current_user.id,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Project not found or not owned "
                "by the current user."
            ),
        )

    return service


@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_project_member(
    project_id: int,
    payload: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = require_project_owner(
        project_id=project_id,
        current_user=current_user,
        db=db,
    )

    if not service.user_exists(payload.user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if service.get_member(
        project_id=project_id,
        user_id=payload.user_id,
    ) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project.",
        )

    member = service.add_member(
        project_id=project_id,
        user_id=payload.user_id,
        role=payload.role,
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project member could not be created.",
        )

    return member


@router.get(
    "/projects/{project_id}/members",
    response_model=list[ProjectMemberResponse],
)
def list_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = require_project_owner(
        project_id=project_id,
        current_user=current_user,
        db=db,
    )

    return service.list_members(project_id=project_id)


@router.patch(
    "/projects/{project_id}/members/{user_id}",
    response_model=ProjectMemberResponse,
)
def update_project_member_role(
    project_id: int,
    user_id: int,
    payload: ProjectMemberRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = require_project_owner(
        project_id=project_id,
        current_user=current_user,
        db=db,
    )

    member = service.update_member_role(
        project_id=project_id,
        user_id=user_id,
        role=payload.role,
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project member not found.",
        )

    return member


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = require_project_owner(
        project_id=project_id,
        current_user=current_user,
        db=db,
    )

    removed = service.remove_member(
        project_id=project_id,
        user_id=user_id,
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project member not found.",
        )

    return None