"""Fetch detailed nutrition data for catalog records that have not been enriched."""

import json
import os
import time

import requests

from database.db import connection
from services.spoonacular_client import BASE_URL, REQUEST_TIMEOUT_SECONDS

HYDRATION_LIMIT = 200
SLEEP_SECONDS = 0.3


def hydrate_menu_items(api_key: str, limit: int = HYDRATION_LIMIT) -> None:
    """Hydrate up to ``limit`` records, preserving progress after each response."""
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT spoonacular_id
            FROM raw_menu_items
            WHERE spoonacular_id NOT IN (
                SELECT spoonacular_id FROM menu_item_details
            )
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        source_ids = [row["spoonacular_id"] for row in rows]
        print(f"Hydrating {len(source_ids)} menu items")
        with requests.Session() as session:
            for source_id in source_ids:
                response = session.get(
                    f"{BASE_URL}/food/menuItems/{source_id}",
                    params={"apiKey": api_key},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                if not response.ok:
                    print(f"Failed {source_id}: HTTP {response.status_code}")
                    continue
                conn.execute(
                    """
                    INSERT OR REPLACE INTO menu_item_details (spoonacular_id, payload)
                    VALUES (?, ?)
                    """,
                    (source_id, json.dumps(response.json())),
                )
                conn.commit()
                time.sleep(SLEEP_SECONDS)


def main() -> None:
    api_key = os.getenv("SPOONACULAR_API_KEY")
    if not api_key:
        raise RuntimeError("SPOONACULAR_API_KEY is required to hydrate menu data.")
    hydrate_menu_items(api_key)
    print("Hydration complete.")


if __name__ == "__main__":
    main()
