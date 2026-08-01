from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

def test_bad_request():
    response = client.get("/test-error?q=-1")
    assert response.status_code == 400
    assert "error" in response.json()


def test_recommendations():
    response = client.post("/api/recommendations", json={"query": "chicken"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "chicken"
    assert 0 < len(body["results"]) <= 6
    assert all("name" in item for item in body["results"])


def test_recommendations_validate_input():
    response = client.post("/api/recommendations", json={"query": ""})
    assert response.status_code == 422
