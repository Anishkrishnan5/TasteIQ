from pathlib import Path

import pytest

from rag.dense import DenseUnavailableError, load_dense_index


def test_dense_index_fails_closed_when_artifacts_are_missing(tmp_path: Path):
    with pytest.raises(DenseUnavailableError, match="missing"):
        load_dense_index(tmp_path / "missing.npz", tmp_path / "missing.json")
