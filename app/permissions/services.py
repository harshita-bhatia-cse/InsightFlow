from sqlalchemy.orm import Session

from app.database.models import Project, ProjectMember, User, Workspace


ALLOWED_PROJECT_ROLES = {
    "viewer",
    "analyst",
    "editor",
    "owner",
}


class ProjectPermissionService:
    def __init__(self, db: Session):
        self.db = db

    def user_owns_project(
        self,
        project_id: int,
        user_id: int,
    ) -> bool:
        return (
            self.db.query(Project)
            .join(
                Workspace,
                Project.workspace_id == Workspace.id,
            )
            .filter(
                Project.id == project_id,
                Workspace.owner_id == user_id,
            )
            .first()
            is not None
        )

    def user_exists(self, user_id: int) -> bool:
        return self.db.query(User).filter(
            User.id == user_id
        ).first() is not None

    def get_member(
        self,
        project_id: int,
        user_id: int,
    ) -> ProjectMember | None:
        return (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
            .first()
        )
    def get_user_project_role(
        self,
        project_id: int,
        user_id: int,
    ) -> str | None:
        if self.user_owns_project(
            project_id=project_id,
            user_id=user_id,
        ):
            return "owner"

        member = self.get_member(
            project_id=project_id,
            user_id=user_id,
        )

        if member is None:
            return None

        return member.role

    def user_has_project_access(
        self,
        project_id: int,
        user_id: int,
        allowed_roles: set[str],
    ) -> bool:
        role = self.get_user_project_role(
            project_id=project_id,
            user_id=user_id,
        )

        return role in allowed_roles

    def user_can_view_project(
        self,
        project_id: int,
        user_id: int,
    ) -> bool:
        return self.user_has_project_access(
            project_id=project_id,
            user_id=user_id,
            allowed_roles={
                "viewer",
                "analyst",
                "editor",
                "owner",
            },
        )

    def user_can_edit_project(
        self,
        project_id: int,
        user_id: int,
    ) -> bool:
        return self.user_has_project_access(
            project_id=project_id,
            user_id=user_id,
            allowed_roles={
                "editor",
                "owner",
            },
        )

    def user_can_manage_project(
        self,
        project_id: int,
        user_id: int,
    ) -> bool:
        return self.user_has_project_access(
            project_id=project_id,
            user_id=user_id,
            allowed_roles={
                "owner",
            },
        )
    def list_members(
        self,
        project_id: int,
    ) -> list[ProjectMember]:
        return (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
            )
            .order_by(ProjectMember.created_at.asc())
            .all()
        )

    def add_member(
        self,
        project_id: int,
        user_id: int,
        role: str,
    ) -> ProjectMember | None:
        if role not in ALLOWED_PROJECT_ROLES:
            return None

        if not self.user_exists(user_id):
            return None

        existing_member = self.get_member(
            project_id=project_id,
            user_id=user_id,
        )

        if existing_member is not None:
            return None

        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
        )

        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        return member

    def update_member_role(
        self,
        project_id: int,
        user_id: int,
        role: str,
    ) -> ProjectMember | None:
        if role not in ALLOWED_PROJECT_ROLES:
            return None

        member = self.get_member(
            project_id=project_id,
            user_id=user_id,
        )

        if member is None:
            return None

        member.role = role

        self.db.commit()
        self.db.refresh(member)

        return member

    def remove_member(
        self,
        project_id: int,
        user_id: int,
    ) -> bool:
        member = self.get_member(
            project_id=project_id,
            user_id=user_id,
        )

        if member is None:
            return False

        self.db.delete(member)
        self.db.commit()

        return True