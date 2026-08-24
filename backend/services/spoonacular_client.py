import json
import os

import requests

API_KEY = os.getenv("SPOONACULAR_API_KEY")
BASE_URL = "https://api.spoonacular.com"
REQUEST_TIMEOUT_SECONDS = 15


def fetch_menu_items(query: str, offset: int = 0, number: int = 10) -> dict:
    if not API_KEY:
        raise RuntimeError("SPOONACULAR_API_KEY is required to ingest menu data.")
    url = f"{BASE_URL}/food/menuItems/search"
    params = {"apiKey": API_KEY, "query": query, "offset": offset, "number": number}

    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    data = fetch_menu_items("chicken")
    print(json.dumps(data, indent=2))
