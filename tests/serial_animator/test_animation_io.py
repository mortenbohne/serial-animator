from pathlib import Path
import pytest
import pymel.core as pm
import serial_animator.animation_io as animation_io
import logging

from serial_animator import log

logger = log.log(__name__)


def test_get_node_data(keyed_cube):
    all_data = animation_io.get_node_data(keyed_cube)
    assert all_data[keyed_cube.tx] == animation_io.get_attribute_data(
        keyed_cube.translateX
    )
    assert len(all_data.keys()) == 1
    assert len(animation_io.get_node_data(keyed_cube, start=2, end=20).keys()) == 1
    assert len(animation_io.get_node_data(keyed_cube, start=100, end=200).keys()) == 0


def test_get_attribute_data(keyed_cube):
    data = animation_io.get_attribute_data(keyed_cube.tx)
    assert data["preInfinity"] == "constant"
    assert data["postInfinity"] == "constant"
    assert data["weightedTangents"] is False
    assert len(data["keys"].keys()) == 2
    pm.setInfinity(keyed_cube.tx, preInfinite="oscillate")
    pm.keyTangent(keyed_cube.tx, weightedTangents=True)
    new_data = animation_io.get_attribute_data(keyed_cube.tx)
    assert new_data["preInfinity"] == "oscillate"
    assert new_data["weightedTangents"] is True


def test_get_key_data(keyed_cube):
    data = animation_io.get_key_data(keyed_cube.tx)
    key_0_value, key_0_tangent = data[float(0)]
    key_10_value, key_10_tangent = data[float(10)]
    assert key_0_value == 0.0
    assert key_10_value == 10.0
    assert key_0_tangent == [0.0, 0.0, 1.0, 1.0, "auto", "auto", True]
    with pytest.raises(KeyError):
        _ = data[float(3)]
    range_data = animation_io.get_key_data(keyed_cube.tx, start=0, end=20)
    assert data == range_data
    out_of_range_data = animation_io.get_key_data(keyed_cube.tx, start=20, end=30)
    assert len(out_of_range_data) == 0


def test_get_infinity(keyed_cube):
    with pytest.raises(animation_io.SerialAnimatorNoKeyError):
        animation_io.get_infinity(keyed_cube.ty)


def test_get_weighted_tangents(keyed_cube):
    with pytest.raises(animation_io.SerialAnimatorNoKeyError):
        animation_io.get_weighted_tangents(keyed_cube.ty)


def test_SerialAnimatorNoKeyError():
    with pytest.raises(animation_io.SerialAnimatorKeyError):
        raise animation_io.SerialAnimatorNoKeyError()


def test_load_animation(caplog):
    with caplog.at_level(logging.DEBUG):
        animation_io.load_animation(path=Path())
        assert "Applying" in caplog.text


def test_get_nodes(new_scene, keyed_cube, cube):
    pm.select(cube)
    assert len(animation_io.get_nodes()) == 0
    pm.select(None)
    assert len(animation_io.get_nodes()) == 1


def test_save_animation_from_selection(tmp_path, preview_sequence):
    out_path = tmp_path / "output.anim"
    result = animation_io.save_animation_from_selection(out_path, preview_sequence)
    assert result.is_file()


@pytest.fixture()
def new_scene():
    pm.newFile(force=True)


@pytest.fixture()
def keyed_cube():
    cube = pm.polyCube(constructionHistory=False)[0]
    pm.setKeyframe(cube, value=0, time=0, attribute="translateX")
    pm.setKeyframe(cube, value=10, time=10, attribute="translateX")
    yield cube
    pm.newFile(force=True)
