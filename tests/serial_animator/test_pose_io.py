import pytest
import pymel.core as pm
import serial_animator.pose_io as pose_io

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


# def test_read_pose_data_to_nodes(pose_file, test_cube):
#     pose_io.read_pose_data_to_nodes(pose_file, [test_cube])
#     data = get_test_data()
#     assert test_cube.tx.get() == data.get(test_cube.fullPath()).get("tx")


def test_read_pose_data(pose_file, get_test_data):
    assert pose_io.read_pose_data(pose_file) == get_test_data


def test_get_pose_filetype():
    assert pose_io.get_pose_filetype() == "pose"


@pytest.fixture()
def test_cube():
    yield pm.polyCube(constructionHistory=False)[0]
    pm.newFile(force=True)


@pytest.fixture()
def pose_file(tmp_path, get_test_data_preview, get_test_data):
    out_path = tmp_path / "tmp_pose_file.pose"
    pose_io.save_data(out_path, get_test_data, get_test_data_preview)
    yield out_path


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
