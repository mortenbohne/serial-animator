from pathlib import Path
import pytest


@pytest.fixture()
def get_test_data_dir():
    return Path(__file__).parents[1] / "data"


@pytest.fixture()
def test_data_preview(get_test_data_dir):
    return get_test_data_dir / "preview.jpg"


@pytest.fixture()
def get_test_data():
    return {
        "|pCube1": {
            "v": True,
            "tx": -2.526906870875038,
            "ty": 2.0449175883476016,
            "tz": 0.0,
            "rx": 26.036432965708386,
            "ry": 7.951386703658792e-16,
            "rz": -27.076318145075327,
            "sx": 1.0,
            "sy": 1.0,
            "sz": 1.0,
        }
    }
