import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_and_login_user():
    email = f"user_{uuid.uuid4().hex}@example.com"
    username = f"user_{uuid.uuid4().hex[:8]}"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "secret123",
            "role": "viewer",
        },
    )

    assert register_response.status_code == 200
    token = register_response.json()["access_token"]
    assert token

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == email


def test_admin_route_requires_admin_role():
    email = f"admin_{uuid.uuid4().hex}@example.com"
    username = f"admin_{uuid.uuid4().hex[:8]}"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "adminpass",
            "role": "admin",
        },
    )

    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    allowed_response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert allowed_response.status_code == 200
    assert isinstance(allowed_response.json(), list)

    viewer_email = f"viewer_{uuid.uuid4().hex}@example.com"
    viewer_username = f"viewer_{uuid.uuid4().hex[:8]}"
    viewer_response = client.post(
        "/auth/register",
        json={
            "email": viewer_email,
            "username": viewer_username,
            "password": "viewerpass",
            "role": "viewer",
        },
    )
    viewer_token = viewer_response.json()["access_token"]

    forbidden_response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert forbidden_response.status_code == 403
