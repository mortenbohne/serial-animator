import logging

import pytest
import pymel.core as pm

import serial_animator.file_io
import serial_animator.pose_io as pose_io
import serial_animator.find_nodes

from serial_animator import log

_logger = log.log(__name__)

def test_get_nodes(two_cubes):
    cube1, cube2 = two_cubes
    assert cube1 and cube2 in pose_io.get_nodes()
    pm.select(cube1)
    selected_nodes = pose_io.get_nodes()
    assert cube2 not in selected_nodes
    assert cube1 in selected_nodes


def test_get_data_from_nodes(two_cubes):
    cube1 = two_cubes[0]
    data = pose_io.get_data_from_nodes(two_cubes)
    assert data[cube1] == pose_io.get_keyable_data(cube1)
    assert len(data.keys()) == len(two_cubes)


def test_save_pose_from_selection(tmp_path, cube, data_preview):
    out_path = tmp_path / "test_save_pose_data_from_selection.pose"
    archive = pose_io.save_pose_from_selection(out_path, data_preview)
    assert archive.is_file()
    node_data = pose_io.get_data_from_nodes([cube])
    pose_path_data = serial_animator.find_nodes.node_dict_to_path_dict(node_data)
    assert (
            serial_animator.file_io.read_data_from_archive(archive, "pose.json")
            == pose_path_data
    )


def test_read_pose_data(pose_file, cube_keyable_data):
    assert pose_io.read_pose_data(pose_file) == cube_keyable_data


def test_get_pose_filetype():
    assert pose_io.get_pose_filetype() == "pose"


def test_read_pose_data_to_nodes(cube, pose_file, cube_keyable_data):
    pose_io.read_pose_data_to_nodes(pose_file, [cube])
    cube_data = cube_keyable_data.get(cube.fullPath())
    for k, v in cube_data.items():
        assert cube.attr(k).get() == v


def test_interpolate(pose_file, cube_keyable_data, caplog):
    pm.newFile(force=True)
    cube = pm.polyCube(constructionHistory=False)[0]
    start_pose = pose_io.get_data_from_nodes([cube])
    target_pose = pose_io.read_pose_data_to_nodes(pose_file, [cube])
    target_pose[cube]["non_existent_attribute"] = 1.0
    _logger.info(target_pose)
    cube.tx.lock()
    with caplog.at_level(logging.DEBUG):
        pose_io.interpolate(target=target_pose, origin=start_pose, weight=0.1)
        assert "doesn't have the attribute" in caplog.text
        assert "is locked" in caplog.text
    cube_data = cube_keyable_data.get(cube.fullPath())
    for k, v in cube_data.items():
        if not isinstance(v, float):
            continue
        # tx is locked in this test
        if k == "tx":
            continue
        o_value = start_pose[cube][k]
        delta = (v - o_value) * 0.1
        assert cube.attr(k).get() == pytest.approx(o_value + delta)
    pose_io.interpolate(target=target_pose, origin=start_pose, weight=0.2)


@pytest.fixture()
def posed_cube(cube, cube_keyable_data):
    cube_data = cube_keyable_data.get(cube.fullPath())
    for k, v in cube_data.items():
        cube.attr(k).set(v)
    yield cube


@pytest.fixture()
def pose_file(tmp_path, data_preview, posed_cube):
    out_path = tmp_path / "tmp_pose_file.pose"
    path_data = pose_io.get_path_data_from_nodes([posed_cube])
    pose_io.save_data(out_path, path_data, data_preview)
    yield out_path
