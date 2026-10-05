import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def register_user(
    prefix: str,
) -> tuple[dict[str, str], int]:
    unique_id = uuid.uuid4().hex

    response = client.post(
        "/auth/register",
        json={
            "email": f"{prefix}_{unique_id}@example.com",
            "username": f"{prefix}_{unique_id[:12]}",
            "password": "permissionpass123",
            "role": "admin",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    access_token = response_data["access_token"]
    user_id = response_data["user"]["id"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    return headers, user_id


def create_project(
    owner_headers: dict[str, str],
) -> int:
    workspace_response = client.post(
        "/api/workspaces",
        headers=owner_headers,
        json={
            "name": "Permission Test Workspace",
            "description": "Workspace for permission tests",
        },
    )

    assert workspace_response.status_code == 201

    workspace_id = workspace_response.json()["id"]

    project_response = client.post(
        "/api/projects",
        headers=owner_headers,
        json={
            "name": "Permission Test Project",
            "description": "Project for permission tests",
            "workspace_id": workspace_id,
        },
    )

    assert project_response.status_code == 201

    return project_response.json()["id"]


def test_owner_can_manage_project_members():
    owner_headers, owner_id = register_user("permission_owner")
    member_headers, member_id = register_user("permission_member")

    project_id = create_project(owner_headers)

    add_response = client.post(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
        json={
            "user_id": member_id,
            "role": "viewer",
        },
    )

    assert add_response.status_code == 201

    member = add_response.json()

    assert member["project_id"] == project_id
    assert member["user_id"] == member_id
    assert member["role"] == "viewer"
    assert member["created_at"] is not None

    list_response = client.get(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
    )

    assert list_response.status_code == 200

    members = list_response.json()

    assert any(
        item["user_id"] == member_id
        for item in members
    )

    update_response = client.patch(
        f"/api/permissions/projects/{project_id}/members/{member_id}",
        headers=owner_headers,
        json={
            "role": "analyst",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["role"] == "analyst"

    delete_response = client.delete(
        f"/api/permissions/projects/{project_id}/members/{member_id}",
        headers=owner_headers,
    )

    assert delete_response.status_code == 204

    list_after_delete_response = client.get(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
    )

    assert list_after_delete_response.status_code == 200
    assert not any(
        item["user_id"] == member_id
        for item in list_after_delete_response.json()
    )

    # Keep the variable meaningful while confirming the owner account exists.
    assert owner_id > 0
    assert member_headers["Authorization"].startswith("Bearer ")


def test_duplicate_project_member_is_rejected():
    owner_headers, _ = register_user("duplicate_owner")
    member_headers, member_id = register_user("duplicate_member")

    project_id = create_project(owner_headers)

    first_response = client.post(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
        json={
            "user_id": member_id,
            "role": "viewer",
        },
    )

    assert first_response.status_code == 201

    duplicate_response = client.post(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
        json={
            "user_id": member_id,
            "role": "editor",
        },
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == (
        "User is already a member of this project."
    )

    assert member_headers["Authorization"].startswith("Bearer ")


def test_invalid_project_member_role_is_rejected():
    owner_headers, _ = register_user("invalid_role_owner")
    member_headers, member_id = register_user("invalid_role_member")

    project_id = create_project(owner_headers)

    response = client.post(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
        json={
            "user_id": member_id,
            "role": "administrator",
        },
    )

    assert response.status_code == 422
    assert member_headers["Authorization"].startswith("Bearer ")


def test_non_owner_cannot_manage_project_members():
    owner_headers, _ = register_user("real_project_owner")
    other_user_headers, other_user_id = register_user(
        "other_project_user"
    )

    project_id = create_project(owner_headers)

    add_response = client.post(
        f"/api/permissions/projects/{project_id}/members",
        headers=other_user_headers,
        json={
            "user_id": other_user_id,
            "role": "viewer",
        },
    )

    assert add_response.status_code == 404
    assert add_response.json()["detail"] == (
        "Project not found or not owned by the current user."
    )

    list_response = client.get(
        f"/api/permissions/projects/{project_id}/members",
        headers=other_user_headers,
    )

    assert list_response.status_code == 404
    assert list_response.json()["detail"] == (
        "Project not found or not owned by the current user."
    )