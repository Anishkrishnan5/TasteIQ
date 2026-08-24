from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import app
from personalization.database import Base, get_session
from personalization.service import PreferenceSnapshot, rerank_for_profile


def test_reranking_filters_dislikes_and_explains_preference_boosts():
    items = [
        {
            "spoonacular_id": 1,
            "name": "Italian chicken bowl",
            "ingredients": ["roasted mushroom"],
            "protein_g": 30,
            "score": 4.0,
        },
        {
            "spoonacular_id": 2,
            "name": "Italian grilled chicken",
            "ingredients": ["chicken"],
            "protein_g": 30,
            "score": 3.5,
        },
        {"spoonacular_id": 3, "name": "Chicken salad", "score": 3.8},
    ]
    preferences = PreferenceSnapshot(
        dietary_preferences=frozenset({"high_protein"}),
        disliked_ingredients=frozenset({"mushroom"}),
        favorite_cuisines=frozenset({"italian"}),
        saved_source_ids=frozenset({2}),
    )

    results = rerank_for_profile(items, preferences)

    assert [item["spoonacular_id"] for item in results] == [2, 3]
    assert results[0]["personalization"] == {
        "boost": 2.75,
        "reasons": [
            "favorite cuisine: italian",
            "diet preference: high_protein",
            "previously saved",
        ],
    }


def test_profile_saved_items_and_personalized_search_history():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    def test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    client = TestClient(app)
    try:
        created = client.post(
            "/api/profiles",
            json={
                "display_name": "Demo User",
                "dietary_preferences": ["HIGH_PROTEIN"],
                "disliked_ingredients": ["mushroom"],
                "favorite_cuisines": ["Italian"],
            },
        )
        assert created.status_code == 201
        profile = created.json()
        assert profile["dietary_preferences"] == ["high_protein"]

        response = client.post(
            "/api/recommendations",
            json={"query": "chicken", "profile_id": profile["id"]},
        )
        assert response.status_code == 200
        assert response.json()["meta"]["personalized"] is True

        result = response.json()["results"][0]
        saved = client.post(
            f"/api/profiles/{profile['id']}/saved",
            json={"spoonacular_id": result["spoonacular_id"], "item_name": result["name"]},
        )
        assert saved.status_code == 201
        assert len(client.get(f"/api/profiles/{profile['id']}/saved").json()) == 1
        assert client.get(f"/api/profiles/{profile['id']}/history").json()[0]["query"] == "chicken"
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
