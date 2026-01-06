import os
import requests
import json

API_KEY = os.getenv("SPOONACULAR_API_KEY")

def fetch_menu_items():
    url = "https://api.spoonacular.com/food/menuItems/search"
    params = {
        "apiKey": API_KEY,
        "query": "burger",
        "number": 3
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    data = fetch_menu_items()
    print(json.dumps(data, indent=2))
    