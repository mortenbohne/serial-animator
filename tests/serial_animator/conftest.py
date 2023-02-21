from pathlib import Path

import pytest


@pytest.fixture()
def get_test_data_dir():
    return Path(__file__).parents[1] / "data"


@pytest.fixture()
def get_test_data_preview(get_test_data_dir):
    return get_test_data_dir / "preview.jpg"
