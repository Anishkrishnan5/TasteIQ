from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.2.0"}
    assert response.headers["x-request-id"]
    assert response.headers["server-timing"].startswith("total;dur=")


def test_recommendations():
    response = client.post("/api/recommendations", json={"query": "chicken"})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["query"] == "chicken"
    assert 0 < len(body["results"]) <= 6
    assert all("name" in item for item in body["results"])
    assert body["meta"]["result_count"] == len(body["results"])
    assert body["meta"]["request_id"] == response.headers["x-request-id"]
    assert body["meta"]["retriever_version"] == "token-overlap-v2"
    assert len(body["meta"]["catalog_sha256"]) == 64


def test_recommendations_validate_input():
    for query in ("", "   "):
        response = client.post("/api/recommendations", json={"query": query})
        assert response.status_code == 422
        body = response.json()
        assert body["schema_version"] == "1.0"
        assert body["error"]["code"] == "validation_error"
        assert body["request_id"] == response.headers["x-request-id"]


def test_recommendations_reject_unknown_fields():
    response = client.post("/api/recommendations", json={"query": "chicken", "diet": "vegetarian"})
    assert response.status_code == 422


def test_recommendations_preserve_safe_request_id():
    response = client.post(
        "/api/recommendations",
        json={"query": "chicken"},
        headers={"X-Request-ID": "portfolio-demo-123"},
    )
    assert response.headers["x-request-id"] == "portfolio-demo-123"
    assert response.json()["meta"]["request_id"] == "portfolio-demo-123"


def test_development_error_route_was_removed():
    assert client.get("/test-error?q=-1").status_code == 404


def test_openapi_documents_versioned_success_and_error_models():
    operation = client.get("/openapi.json").json()["paths"]["/api/recommendations"]["post"]

    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/RecommendationResponse"
    )
    assert operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ErrorResponse"
    )


def test_recommendations_include_macro_fields():
    response = client.post("/api/recommendations", json={"query": "pizza", "limit": 10})
    results = response.json()["results"]
    assert any(item["calories"] is not None for item in results)
    enriched = next(item for item in results if item["calories"] is not None)
    assert all(key in enriched for key in ("protein_g", "carbs_g", "fat_g", "ingredients"))
    assert len({item["spoonacular_id"] for item in results}) == len(results)


def test_unknown_query_returns_no_unrelated_results():
    response = client.post("/api/recommendations", json={"query": "zzzxxyy"})
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_nutrition_filters_exclude_unknown_and_violating_values():
    response = client.post(
        "/api/recommendations",
        json={"query": "chicken", "limit": 20, "max_calories": 500, "min_protein": 20},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"]
    assert all(
        item["calories"] is not None
        and item["calories"] <= 500
        and item["protein_g"] is not None
        and item["protein_g"] >= 20
        for item in body["results"]
    )
    assert body["meta"]["filters"]["unknown_nutrition_policy"] == "exclude"
