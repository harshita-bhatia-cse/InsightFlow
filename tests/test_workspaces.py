import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_authenticated_user_can_manage_workspace():
    unique_id = uuid.uuid4().hex

    register_response = client.post(
        "/auth/register",
        json={
            "email": f"workspace_{unique_id}@example.com",
            "username": f"workspace_{unique_id[:12]}",
            "password": "workspacepass123",
            "role": "admin",
        },
    )

    assert register_response.status_code == 200

    access_token = register_response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    create_response = client.post(
        "/api/workspaces",
        headers=headers,
        json={
            "name": "Test Workspace",
            "description": "Workspace created by an automated test",
        },
    )

    assert create_response.status_code == 201

    workspace = create_response.json()

    assert workspace["name"] == "Test Workspace"
    assert workspace["description"] == (
        "Workspace created by an automated test"
    )
    assert workspace["owner_id"] > 0
    assert workspace["id"] > 0
    assert workspace["created_at"] is not None

    workspace_id = workspace["id"]

    list_response = client.get(
        "/api/workspaces",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert any(
        item["id"] == workspace_id
        for item in list_response.json()
    )

    get_response = client.get(
        f"/api/workspaces/{workspace_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == workspace_id

    delete_response = client.delete(
        f"/api/workspaces/{workspace_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    missing_response = client.get(
        f"/api/workspaces/{workspace_id}",
        headers=headers,
    )

    assert missing_response.status_code == 404