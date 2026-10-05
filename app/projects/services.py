from sqlalchemy.orm import Session

from app.database.models import Project, Workspace


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_project(
        self,
        name: str,
        description: str | None,
        workspace_id: int,
        owner_id: int,
    ) -> Project | None:
        workspace = (
            self.db.query(Workspace)
            .filter(
                Workspace.id == workspace_id,
                Workspace.owner_id == owner_id,
            )
            .first()
        )

        if workspace is None:
            return None

        project = Project(
            name=name.strip(),
            description=description.strip() if description else None,
            workspace_id=workspace_id,
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        return project

    def get_project_for_owner(
        self,
        project_id: int,
        owner_id: int,
    ) -> Project | None:
        return (
            self.db.query(Project)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .filter(
                Project.id == project_id,
                Workspace.owner_id == owner_id,
            )
            .first()
        )

    def list_projects_for_owner(
        self,
        owner_id: int,
    ) -> list[Project]:
        return (
            self.db.query(Project)
            .join(Workspace, Project.workspace_id == Workspace.id)
            .filter(Workspace.owner_id == owner_id)
            .order_by(Project.created_at.desc())
            .all()
        )

    def delete_project(
        self,
        project_id: int,
        owner_id: int,
    ) -> bool:
        project = self.get_project_for_owner(
            project_id=project_id,
            owner_id=owner_id,
        )

        if project is None:
            return False

        self.db.delete(project)
        self.db.commit()

        return True