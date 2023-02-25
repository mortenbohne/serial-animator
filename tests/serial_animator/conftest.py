from pathlib import Path
import pytest
from pymel import core as pm


@pytest.fixture()
def get_test_data_dir():
    return Path(__file__).parents[1] / "data"


@pytest.fixture()
def data_preview(get_test_data_dir):
    return get_test_data_dir / "preview.jpg"


@pytest.fixture()
def cube_keyable_data(scope="function"):
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


@pytest.fixture()
def cube():
    cube = pm.polyCube(constructionHistory=False)[0]
    yield cube
    pm.newFile(force=True)


@pytest.fixture()
def two_cubes():
    cube1 = pm.polyCube(constructionHistory=False)[0]
    cube2 = pm.polyCube(constructionHistory=False)[0]
    yield [cube1, cube2]
    pm.newFile(force=True)
