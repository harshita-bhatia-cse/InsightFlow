from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to InsightFlow AI"
    }


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy"
    }


def test_unknown_endpoint_returns_not_found():
    response = client.get("/does-not-exist")

    assert response.status_code == 404


def test_dataset_versions_endpoint_returns_not_found_for_unknown_file():
    response = client.get(
        "/dataset-versions/unknown-file.csv"
    )

    assert response.status_code == 200
    assert response.json() == []