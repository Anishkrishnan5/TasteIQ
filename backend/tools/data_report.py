from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
DEFAULT_CATALOG = BACKEND_ROOT / "database" / "rag_items.jsonl"
DEFAULT_DATABASE = BACKEND_ROOT / "database" / "tasteiq.db"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "reports" / "data-quality.json"
REQUIRED_METADATA_FIELDS = (
    "name",
    "restaurant",
    "cuisine",
    "ingredients",
    "diet_tags",
    "derived_tags",
    "calories",
    "protein_g",
    "carbs_g",
    "fat_g",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _known(value: Any) -> bool:
    return value is not None and value != "" and value != []


def _percent(count: int, total: int) -> float:
    return round(count * 100 / total, 2) if total else 0.0


def inspect_catalog(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    malformed_lines: list[int] = []
    non_object_lines: list[int] = []

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                malformed_lines.append(line_number)
                continue
            if not isinstance(record, dict):
                non_object_lines.append(line_number)
                continue
            records.append(record)

    ids = [record.get("id") for record in records if _known(record.get("id"))]
    source_ids = [
        record.get("spoonacular_id") for record in records if _known(record.get("spoonacular_id"))
    ]
    normalized_names = [
        str(record.get("metadata", {}).get("name", "")).strip().casefold()
        for record in records
        if isinstance(record.get("metadata"), dict)
        and _known(record.get("metadata", {}).get("name"))
    ]
    metadata_objects = [
        record.get("metadata", {}) for record in records if isinstance(record.get("metadata"), dict)
    ]
    coverage = {
        field: {
            "known": (known := sum(_known(metadata.get(field)) for metadata in metadata_objects)),
            "percent": _percent(known, len(records)),
        }
        for field in REQUIRED_METADATA_FIELDS
    }
    id_counts = Counter(ids)
    source_id_counts = Counter(source_ids)
    name_counts = Counter(normalized_names)

    report = {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "sha256": _sha256(path),
        "total_lines": len(records) + len(malformed_lines) + len(non_object_lines),
        "valid_records": len(records),
        "malformed_json": {"count": len(malformed_lines), "line_numbers": malformed_lines[:20]},
        "non_object_json": {"count": len(non_object_lines), "line_numbers": non_object_lines[:20]},
        "missing_required_structure": {
            "id": len(records) - len(ids),
            "spoonacular_id": len(records) - len(source_ids),
            "metadata_object": len(records) - len(metadata_objects),
            "name": len(records) - len(normalized_names),
        },
        "duplicates": {
            "id": {
                "groups": sum(count > 1 for count in id_counts.values()),
                "extra_rows": len(ids) - len(id_counts),
            },
            "spoonacular_id": {
                "groups": sum(count > 1 for count in source_id_counts.values()),
                "extra_rows": len(source_ids) - len(source_id_counts),
            },
            "normalized_name": {
                "groups": sum(count > 1 for count in name_counts.values()),
                "extra_rows": len(normalized_names) - len(name_counts),
            },
        },
        "unique": {
            "id": len(id_counts),
            "spoonacular_id": len(source_id_counts),
            "normalized_name": len(name_counts),
        },
        "metadata_coverage": coverage,
    }
    return report, records


def inspect_database(path: Path) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    report: dict[str, Any] = {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "sha256": _sha256(path),
    }
    details: dict[int, dict[str, Any]] = {}
    connection = sqlite3.connect(path)
    try:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        report["tables"] = sorted(tables)
        report["raw_menu_items"] = (
            connection.execute("SELECT COUNT(*) FROM raw_menu_items").fetchone()[0]
            if "raw_menu_items" in tables
            else 0
        )
        invalid_payloads = 0
        if "menu_item_details" in tables:
            rows = connection.execute(
                "SELECT spoonacular_id, payload FROM menu_item_details"
            ).fetchall()
            for source_id, payload in rows:
                try:
                    parsed = json.loads(payload)
                except (TypeError, json.JSONDecodeError):
                    invalid_payloads += 1
                    continue
                if isinstance(source_id, int) and isinstance(parsed, dict):
                    details[source_id] = parsed
        report["menu_item_details"] = len(details)
        report["invalid_detail_payloads"] = invalid_payloads
    finally:
        connection.close()
    return report, details


def build_report(catalog_path: Path, database_path: Path) -> dict[str, Any]:
    catalog, records = inspect_catalog(catalog_path)
    database, details = inspect_database(database_path)
    catalog_source_ids = {record.get("spoonacular_id") for record in records}
    enriched_ids = catalog_source_ids & details.keys()
    enriched_records = [
        record for record in records if record.get("spoonacular_id") in enriched_ids
    ]
    valid_records = catalog["valid_records"]

    return {
        "report_version": 1,
        "source": {
            "provider": "Spoonacular historical snapshot",
            "catalog_role": "checked-in runtime retrieval catalog",
            "database_role": "checked-in optional runtime enrichment",
            "provenance_limitations": [
                "The original fetch timestamp and request parameters are not recorded "
                "per catalog row.",
                "The snapshot does not include a versioned source manifest.",
            ],
        },
        "catalog": catalog,
        "database": database,
        "runtime_enrichment": {
            "catalog_records_with_detail": len(enriched_records),
            "catalog_record_percent": _percent(len(enriched_records), valid_records),
            "unique_source_ids_with_detail": len(enriched_ids),
            "unique_source_id_percent": _percent(len(enriched_ids), len(catalog_source_ids)),
            "unique_catalog_source_ids": len(catalog_source_ids),
        },
        "quality_gate": {
            "malformed_json_is_zero": catalog["malformed_json"]["count"] == 0,
            "all_records_have_ids": catalog["missing_required_structure"]["id"] == 0,
            "all_records_have_names": catalog["missing_required_structure"]["name"] == 0,
            "duplicate_source_ids_is_zero": (
                catalog["duplicates"]["spoonacular_id"]["extra_rows"] == 0
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Report TasteIQ catalog and database quality.")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check", action="store_true", help="Fail when minimum integrity gates fail."
    )
    args = parser.parse_args()

    report = build_report(args.catalog.resolve(), args.database.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote data-quality report to {args.output}")
    print(json.dumps(report["quality_gate"], sort_keys=True))
    return int(args.check and not all(report["quality_gate"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
