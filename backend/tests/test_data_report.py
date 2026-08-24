from pathlib import Path

from tools.data_report import DEFAULT_CATALOG, DEFAULT_DATABASE, build_report


def test_database_initialization_creates_both_maintenance_tables(tmp_path, monkeypatch):
    import database.db as db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "tasteiq.db")
    db.init_db()

    with db.connection() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {"raw_menu_items", "menu_item_details"} <= tables


def test_current_data_integrity_gates_pass():
    report = build_report(DEFAULT_CATALOG, DEFAULT_DATABASE)

    assert all(report["quality_gate"].values())
    assert report["catalog"]["valid_records"] == 448
    assert report["catalog"]["unique"]["spoonacular_id"] == 448
    assert report["catalog"]["duplicates"]["spoonacular_id"]["extra_rows"] == 0
    assert report["database"]["menu_item_details"] == 51
    assert report["runtime_enrichment"]["catalog_records_with_detail"] == 51
    assert report["runtime_enrichment"]["unique_source_ids_with_detail"] == 51


def test_data_paths_are_repository_files():
    assert Path(DEFAULT_CATALOG).is_file()
    assert Path(DEFAULT_DATABASE).is_file()
