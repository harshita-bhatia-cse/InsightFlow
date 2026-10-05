import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def register_user_and_get_headers(prefix: str) -> dict[str, str]:
    unique_id = uuid.uuid4().hex

    response = client.post(
        "/auth/register",
        json={
            "email": f"{prefix}_{unique_id}@example.com",
            "username": f"{prefix}_{unique_id[:12]}",
            "password": "projectpass123",
            "role": "admin",
        },
    )

    assert response.status_code == 200

    access_token = response.json()["access_token"]
    return {
        "Authorization": f"Bearer {access_token}",
    }


def test_authenticated_user_can_manage_project():
    headers = register_user_and_get_headers("project_owner")

    workspace_response = client.post(
        "/api/workspaces",
        headers=headers,
        json={
            "name": "Project Test Workspace",
            "description": "Workspace for project tests",
        },
    )

    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    create_response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Test Project",
            "description": "Project created by an automated test",
            "workspace_id": workspace_id,
        },
    )

    assert create_response.status_code == 201

    project = create_response.json()
    project_id = project["id"]

    assert project["name"] == "Test Project"
    assert project["description"] == (
        "Project created by an automated test"
    )
    assert project["workspace_id"] == workspace_id
    assert project["id"] > 0
    assert project["created_at"] is not None

    list_response = client.get(
        "/api/projects",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert any(
        item["id"] == project_id
        for item in list_response.json()
    )

    get_response = client.get(
        f"/api/projects/{project_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == project_id

    delete_response = client.delete(
        f"/api/projects/{project_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    missing_response = client.get(
        f"/api/projects/{project_id}",
        headers=headers,
    )

    assert missing_response.status_code == 404


def test_user_cannot_create_project_in_another_users_workspace():
    owner_headers = register_user_and_get_headers("workspace_owner")
    other_user_headers = register_user_and_get_headers("other_user")

    workspace_response = client.post(
        "/api/workspaces",
        headers=owner_headers,
        json={
            "name": "Private Workspace",
            "description": "Owned by another user",
        },
    )

    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    project_response = client.post(
        "/api/projects",
        headers=other_user_headers,
        json={
            "name": "Unauthorized Project",
            "description": "This project must not be created",
            "workspace_id": workspace_id,
        },
    )

    assert project_response.status_code == 404
    assert project_response.json()["detail"] == (
        "Workspace not found or not owned by the current user."
    )