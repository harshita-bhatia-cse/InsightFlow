from sqlalchemy.orm import Session

from app.database.models import User, Workspace


class WorkspaceService:
    def __init__(self, db: Session):
        self.db = db

    def create_workspace(self, name: str, description: str | None, owner_id: int) -> Workspace:
        workspace = Workspace(
            name=name.strip(),
            description=description.strip() if description else None,
            owner_id=owner_id,
        )

        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)

        return workspace

    def get_workspace_by_id(self, workspace_id: int) -> Workspace | None:
        return (
            self.db.query(Workspace)
            .filter(Workspace.id == workspace_id)
            .first()
        )

    def list_workspaces_for_user(self, owner_id: int) -> list[Workspace]:
        return (
            self.db.query(Workspace)
            .filter(Workspace.owner_id == owner_id)
            .order_by(Workspace.created_at.desc())
            .all()
        )

    def delete_workspace(self, workspace_id: int, owner_id: int) -> bool:
        workspace = (
            self.db.query(Workspace)
            .filter(Workspace.id == workspace_id, Workspace.owner_id == owner_id)
            .first()
        )

        if workspace is None:
            return False

        self.db.delete(workspace)
        self.db.commit()
        return True


def create_workspace_service(db: Session) -> WorkspaceService:
    return WorkspaceService(db)