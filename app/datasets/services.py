from sqlalchemy.orm import Session

from app.database.models import Dataset, Project, Workspace
from app.permissions.services import ProjectPermissionService


class DatasetService:
    def __init__(self, db: Session):
        self.db = db

    def get_dataset_for_user(
        self,
        dataset_id: int,
        user_id: int,
    ) -> Dataset | None:
        dataset = (
            self.db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if dataset is None or dataset.project_id is None:
            return None

        permission_service = ProjectPermissionService(self.db)

        if not permission_service.user_can_view_project(
            project_id=dataset.project_id,
            user_id=user_id,
        ):
            return None

        return dataset

    def list_datasets_for_user(
        self,
        user_id: int,
    ) -> list[Dataset]:
        permission_service = ProjectPermissionService(self.db)

        datasets = (
            self.db.query(Dataset)
            .filter(Dataset.project_id.is_not(None))
            .order_by(Dataset.created_at.desc())
            .all()
        )

        return [
            dataset
            for dataset in datasets
            if permission_service.user_can_view_project(
                project_id=dataset.project_id,
                user_id=user_id,
            )
        ]

    def assign_dataset_to_project(
        self,
        dataset_id: int,
        project_id: int,
        owner_id: int,
    ) -> Dataset | None:
        project = (
            self.db.query(Project)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .filter(
                Project.id == project_id,
                Workspace.owner_id == owner_id,
            )
            .first()
        )

        if project is None:
            return None

        dataset = (
            self.db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if dataset is None:
            return None

        dataset.project_id = project_id

        self.db.commit()
        self.db.refresh(dataset)

        return dataset

    def get_dataset_for_owner(
        self,
        dataset_id: int,
        owner_id: int,
    ) -> Dataset | None:
        return (
            self.db.query(Dataset)
            .join(Project, Dataset.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .filter(
                Dataset.id == dataset_id,
                Workspace.owner_id == owner_id,
            )
            .first()
        )

    def list_datasets_for_owner(
        self,
        owner_id: int,
    ) -> list[Dataset]:
        return (
            self.db.query(Dataset)
            .join(Project, Dataset.project_id == Project.id)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .filter(Workspace.owner_id == owner_id)
            .order_by(Dataset.created_at.desc())
            .all()
        )