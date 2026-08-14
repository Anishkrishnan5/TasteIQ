import json
import os
import sqlite3
import time

import requests

API_KEY = os.getenv("SPOONACULAR_API_KEY")
DB_PATH = "database/tasteiq.db"

if not API_KEY:
    raise Exception("Missing SPOONACULAR_API_KEY env var")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT spoonacular_id
    FROM raw_menu_items
    WHERE spoonacular_id NOT IN (
        SELECT spoonacular_id FROM menu_item_details
    )
    LIMIT 200;
""")

ids = [row[0] for row in cursor.fetchall()]
print(f"Hydrating {len(ids)} menu items")

for menu_id in ids:
    url = f"https://api.spoonacular.com/food/menuItems/{menu_id}"
    params = {"apiKey": API_KEY}

    r = requests.get(url, params=params)

    if r.status_code != 200:
        print(f"❌ Failed {menu_id}: {r.status_code}")
        continue

    cursor.execute(
        """
        INSERT OR REPLACE INTO menu_item_details
        (spoonacular_id, payload)
        VALUES (?, ?)
    """,
        (menu_id, json.dumps(r.json())),
    )

    conn.commit()
    time.sleep(0.3)

conn.close()
print("✅ Done")
