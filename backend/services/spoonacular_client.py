import os
import requests
import json

API_KEY = os.getenv("SPOONACULAR_API_KEY")

def fetch_menu_items(query, offset=0, number=10):
    url = "https://api.spoonacular.com/food/menuItems/search"
    params = {
        "apiKey": API_KEY,
        "query": query,
        "offset": offset,
        "number": number
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    data = fetch_menu_items()
    print(json.dumps(data, indent=2))
    