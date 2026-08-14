from pathlib import Path

from tools.data_report import DEFAULT_CATALOG, DEFAULT_DATABASE, build_report


def test_current_data_integrity_gates_pass():
    report = build_report(DEFAULT_CATALOG, DEFAULT_DATABASE)

    assert all(report["quality_gate"].values())
    assert report["catalog"]["valid_records"] == 920
    assert report["catalog"]["unique"]["spoonacular_id"] == 460
    assert report["catalog"]["duplicates"]["spoonacular_id"]["extra_rows"] == 460
    assert report["database"]["menu_item_details"] == 51
    assert report["runtime_enrichment"]["catalog_records_with_detail"] == 102
    assert report["runtime_enrichment"]["unique_source_ids_with_detail"] == 51


def test_data_paths_are_repository_files():
    assert Path(DEFAULT_CATALOG).is_file()
    assert Path(DEFAULT_DATABASE).is_file()
