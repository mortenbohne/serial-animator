import pytest
import pymel.core as pm

import serial_animator.find_nodes
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
def pose_file(tmp_path, test_data_preview, get_test_data):
    out_path = tmp_path / "tmp_pose_file.pose"
    pose_io.save_data(out_path, get_test_data, test_data_preview)
    yield out_path


def test_node_dict_to_path_dict(test_cube):
    node_dict = dict()
    node_dict[test_cube] = 1
    path_dict = serial_animator.find_nodes.node_dict_to_path_dict(node_dict)
    assert len(node_dict.keys()) == len(path_dict)
    for node in node_dict.keys():
        v = node_dict[node]
        assert v == path_dict[node.fullPath()]
