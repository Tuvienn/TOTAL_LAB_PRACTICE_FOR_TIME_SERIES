from pathlib import Path

import pytest

from practice_2 import find_practice_root


ROOT = Path(__file__).parents[1]


def test_find_practice_root_from_notebook_directory():
    assert find_practice_root(ROOT / "notebooks") == ROOT


def test_find_practice_root_rejects_unrelated_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_practice_root(tmp_path)
