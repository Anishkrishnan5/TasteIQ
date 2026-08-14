from utils.preprocess import clean_one_menu_item, preprocess_menu_items


def test_spoonacular_restaurant_chain_is_preserved():
    cleaned = clean_one_menu_item(
        {"spoonacular_id": 1, "title": "Chicken Bowl", "restaurantChain": "Example Cafe"}
    )

    assert cleaned is not None
    assert cleaned.restaurant == "example cafe"
    assert "restaurant: example cafe" in cleaned.embedding_text


def test_preprocessing_deduplicates_source_ids_and_entities():
    records = [
        {"spoonacular_id": 1, "title": "Chicken Bowl", "restaurantChain": "Example Cafe"},
        {"spoonacular_id": 1, "title": "Chicken Bowl", "restaurantChain": "Example Cafe"},
        {"spoonacular_id": 2, "title": "Chicken Bowl", "restaurantChain": "Example Cafe"},
        {"spoonacular_id": 3, "title": "Veggie Bowl", "restaurantChain": "Example Cafe"},
    ]

    cleaned, stats = preprocess_menu_items(records)

    assert [item.raw_source["spoonacular_id"] for item in cleaned] == [1, 3]
    assert stats == {
        "seen": 4,
        "kept": 2,
        "dropped_missing_name": 0,
        "dropped_duplicate": 2,
    }
