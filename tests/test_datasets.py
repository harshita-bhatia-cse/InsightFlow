import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def register_user_and_get_headers(
    prefix: str,
) -> tuple[dict[str, str], int]:
    unique_id = uuid.uuid4().hex

    response = client.post(
        "/auth/register",
        json={
            "email": f"{prefix}_{unique_id}@example.com",
            "username": f"{prefix}_{unique_id[:12]}",
            "password": "datasetpass123",
            "role": "admin",
        },
    )

    assert response.status_code == 200

    access_token = response.json()["access_token"]

    return (
        {
            "Authorization": f"Bearer {access_token}",
        },
        response.json()["user"]["id"],
    )


def create_workspace_and_project(headers: dict[str, str]) -> int:
    workspace_response = client.post(
        "/api/workspaces",
        headers=headers,
        json={
            "name": "Dataset Test Workspace",
            "description": "Workspace for dataset ownership tests",
        },
    )

    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    project_response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Dataset Test Project",
            "description": "Project for dataset ownership tests",
            "workspace_id": workspace_id,
        },
    )

    assert project_response.status_code == 201
    return project_response.json()["id"]


def upload_test_dataset(
    headers: dict[str, str],
    project_id: int,
) -> int:
    csv_content = (
        "Task_ID,Layer,Component,Status,Priority,Estimated_Hours\n"
        "TEST-001,Backend,Authentication,Completed,High,8\n"
        "TEST-002,Analytics,KPI Engine,Pending,Medium,10\n"
    )

    response = client.post(
        "/upload",
        headers=headers,
        data={
            "project_id": str(project_id),
        },
        files={
            "file": (
                "dataset_ownership_test.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    return response.json()["analytics_result"]["dataset_id"]


def test_user_can_assign_and_retrieve_owned_dataset():
    headers, _ = register_user_and_get_headers(
        "dataset_owner"
    )
    project_id = create_workspace_and_project(headers)
    dataset_id = upload_test_dataset(
        headers=headers,
        project_id=project_id,
    )

    assign_response = client.patch(
        f"/api/datasets/{dataset_id}/project",
        headers=headers,
        json={
            "project_id": project_id,
        },
    )

    assert assign_response.status_code == 200

    assigned_dataset = assign_response.json()

    assert assigned_dataset["id"] == dataset_id
    assert assigned_dataset["project_id"] == project_id

    list_response = client.get(
        "/api/datasets",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert any(
        dataset["id"] == dataset_id
        for dataset in list_response.json()
    )

    get_response = client.get(
        f"/api/datasets/{dataset_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == dataset_id
    assert get_response.json()["project_id"] == project_id


def test_user_cannot_assign_dataset_to_another_users_project():
    owner_headers, _ = register_user_and_get_headers(
        "project_owner"
    )
    attacker_headers, _ = register_user_and_get_headers(
        "dataset_attacker"
    )

    project_id = create_workspace_and_project(owner_headers)
    dataset_id = upload_test_dataset(
        headers=owner_headers,
        project_id=project_id,
    )

    assign_response = client.patch(
        f"/api/datasets/{dataset_id}/project",
        headers=attacker_headers,
        json={
            "project_id": project_id,
        },
    )

    assert assign_response.status_code == 404
    assert assign_response.json()["detail"] == (
        "Dataset not found, project not found, "
        "or project is not owned by the current user."
    )


def test_user_cannot_retrieve_another_users_dataset():
    owner_headers, _ = register_user_and_get_headers(
        "dataset_owner"
    )
    other_user_headers, _ = register_user_and_get_headers(
        "dataset_viewer"
    )

    project_id = create_workspace_and_project(owner_headers)
    dataset_id = upload_test_dataset(
        headers=owner_headers,
        project_id=project_id,
    )

    assign_response = client.patch(
        f"/api/datasets/{dataset_id}/project",
        headers=owner_headers,
        json={
            "project_id": project_id,
        },
    )

    assert assign_response.status_code == 200

    get_response = client.get(
        f"/api/datasets/{dataset_id}",
        headers=other_user_headers,
    )

    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Dataset not found."


def test_project_member_can_view_project_dataset():
    owner_headers, _ = register_user_and_get_headers(
        "dataset_project_owner"
    )
    member_headers, member_id = register_user_and_get_headers(
        "dataset_project_member"
    )

    project_id = create_workspace_and_project(owner_headers)

    dataset_id = upload_test_dataset(
        headers=owner_headers,
        project_id=project_id,
    )

    add_member_response = client.post(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
        json={
            "user_id": member_id,
            "role": "viewer",
        },
    )

    assert add_member_response.status_code == 201

    list_response = client.get(
        "/api/datasets",
        headers=member_headers,
    )

    assert list_response.status_code == 200
    assert any(
        dataset["id"] == dataset_id
        for dataset in list_response.json()
    )

    get_response = client.get(
        f"/api/datasets/{dataset_id}",
        headers=member_headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == dataset_id


def test_viewer_cannot_upload_to_project():
    owner_headers, _ = register_user_and_get_headers(
        "upload_permission_owner"
    )
    viewer_headers, viewer_id = register_user_and_get_headers(
        "upload_permission_viewer"
    )

    project_id = create_workspace_and_project(owner_headers)

    add_member_response = client.post(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
        json={
            "user_id": viewer_id,
            "role": "viewer",
        },
    )

    assert add_member_response.status_code == 201

    csv_content = (
        "Task_ID,Layer,Component,Status,Priority,Estimated_Hours\n"
        "VIEWER-001,Backend,Authentication,Pending,High,8\n"
    )

    upload_response = client.post(
        "/upload",
        headers=viewer_headers,
        data={
            "project_id": str(project_id),
        },
        files={
            "file": (
                "viewer_upload_test.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 404
    assert upload_response.json()["detail"] == (
        "Project not found or the current user "
        "cannot upload to this project."
    )


def test_editor_can_upload_to_project():
    owner_headers, _ = register_user_and_get_headers(
        "editor_upload_owner"
    )
    editor_headers, editor_id = register_user_and_get_headers(
        "editor_upload_member"
    )

    project_id = create_workspace_and_project(owner_headers)

    add_member_response = client.post(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
        json={
            "user_id": editor_id,
            "role": "editor",
        },
    )

    assert add_member_response.status_code == 201

    dataset_id = upload_test_dataset(
        headers=editor_headers,
        project_id=project_id,
    )

    dataset_response = client.get(
        f"/api/datasets/{dataset_id}",
        headers=editor_headers,
    )

    assert dataset_response.status_code == 200
    assert dataset_response.json()["project_id"] == project_id


def test_project_member_can_view_analytics_but_unrelated_user_cannot():
    owner_headers, _ = register_user_and_get_headers(
        "analytics_access_owner"
    )
    member_headers, member_id = register_user_and_get_headers(
        "analytics_access_member"
    )
    unrelated_headers, _ = register_user_and_get_headers(
        "analytics_access_unrelated"
    )

    project_id = create_workspace_and_project(owner_headers)
    dataset_id = upload_test_dataset(
        headers=owner_headers,
        project_id=project_id,
    )

    add_member_response = client.post(
        f"/api/permissions/projects/{project_id}/members",
        headers=owner_headers,
        json={
            "user_id": member_id,
            "role": "analyst",
        },
    )

    assert add_member_response.status_code == 201

    member_response = client.get(
        f"/analytics/statistics/{dataset_id}",
        headers=member_headers,
    )

    assert member_response.status_code == 200
    assert member_response.json()["dataset_id"] == dataset_id

    unrelated_response = client.get(
        f"/analytics/statistics/{dataset_id}",
        headers=unrelated_headers,
    )

    assert unrelated_response.status_code == 404
    assert unrelated_response.json()["detail"] == (
        "Dataset not found."
    )


def test_legacy_dataset_routes_require_project_access():
    owner_headers, _ = register_user_and_get_headers(
        "legacy_route_owner"
    )
    unrelated_headers, _ = register_user_and_get_headers(
        "legacy_route_unrelated"
    )

    project_id = create_workspace_and_project(owner_headers)
    dataset_id = upload_test_dataset(
        headers=owner_headers,
        project_id=project_id,
    )

    owner_list_response = client.get(
        "/datasets",
        headers=owner_headers,
    )

    assert owner_list_response.status_code == 200
    assert any(
        dataset["id"] == dataset_id
        for dataset in owner_list_response.json()
    )

    unrelated_list_response = client.get(
        "/datasets",
        headers=unrelated_headers,
    )

    assert unrelated_list_response.status_code == 200
    assert not any(
        dataset["id"] == dataset_id
        for dataset in unrelated_list_response.json()
    )

    owner_preview_response = client.get(
        f"/datasets/{dataset_id}/preview",
        headers=owner_headers,
    )

    assert owner_preview_response.status_code == 200
    assert owner_preview_response.json()["dataset_id"] == dataset_id

    unrelated_preview_response = client.get(
        f"/datasets/{dataset_id}/preview",
        headers=unrelated_headers,
    )

    assert unrelated_preview_response.status_code == 404
    assert unrelated_preview_response.json()["detail"] == (
        "Dataset not found."
    )