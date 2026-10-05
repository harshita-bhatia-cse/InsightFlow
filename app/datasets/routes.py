from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database.connection import SessionLocal
from app.database.models import User
from app.datasets.schemas import (
    DatasetProjectAssignment,
    DatasetResponse,
)
from app.datasets.services import DatasetService


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.patch(
    "/{dataset_id}/project",
    response_model=DatasetResponse,
)
def assign_dataset_to_project(
    dataset_id: int,
    payload: DatasetProjectAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DatasetService(db)

    dataset = service.assign_dataset_to_project(
        dataset_id=dataset_id,
        project_id=payload.project_id,
        owner_id=current_user.id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Dataset not found, project not found, "
                "or project is not owned by the current user."
            ),
        )

    return dataset


@router.get(
    "",
    response_model=list[DatasetResponse],
)
def list_owned_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DatasetService(db)

    return service.list_datasets_for_user(
        user_id=current_user.id,
    )

@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
)
def get_owned_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DatasetService(db)

    dataset = service.get_dataset_for_user(
        dataset_id=dataset_id,
        user_id=current_user.id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return dataset