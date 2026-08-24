import json
import time

from database.db import connection, init_db
from services.spoonacular_client import fetch_menu_items

QUERY = "chicken"
PAGE_SIZE = 10
MAX_PAGES = 200
SLEEP_SECONDS = 1.5


def ingest() -> None:
    init_db()
    with connection() as conn:
        offset = 0
        for page in range(MAX_PAGES):
            print(f"Fetching page {page}...")
            items = fetch_menu_items(QUERY, offset, PAGE_SIZE).get("menuItems", [])
            if not items:
                print(f"No items found for page {page}, stopping ingestion.")
                break
            conn.executemany(
                "INSERT INTO raw_menu_items (spoonacular_id, payload) VALUES (?, ?)",
                [(item.get("id"), json.dumps(item)) for item in items],
            )
            conn.commit()
            offset += PAGE_SIZE
            print(f"Stored {len(items)} items. Sleeping...")
            time.sleep(SLEEP_SECONDS)

    print("Ingestion complete.")


if __name__ == "__main__":
    ingest()
