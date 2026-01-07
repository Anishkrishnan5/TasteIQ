import json
import time
from database.db import init_db, get_connection
from services.spoonacular_client import fetch_menu_items

QUERY = "chicken"
PAGE_SIZE = 10
MAX_PAGES = 200
SLEEP_SECONDS = 1.5

def ingest():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    offset = 0
    page = 0

    while page < MAX_PAGES:
        print(f"Fetching page {page}...")
        data = fetch_menu_items(QUERY, offset, PAGE_SIZE)

        items = data.get("menuItems", [])

        if not items:
            print(f"No items found for page {page}, stopping ingestion.")
            break
        for item in items:
            cursor.execute("""
                INSERT INTO raw_menu_items (spoonacular_id, payload)
                VALUES (?, ?)
            """, (item.get("id"), json.dumps(item)))
        conn.commit()
        offset += PAGE_SIZE
        page += 1

        print(f"Stored {len(items)} items. Sleeping...")
        time.sleep(SLEEP_SECONDS)

    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest()