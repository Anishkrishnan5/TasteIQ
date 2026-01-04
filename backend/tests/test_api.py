from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_bad_request():
    response = client.get("/test-error?q=-1")
    assert response.status_code == 400
    assert "error" in response.json()
