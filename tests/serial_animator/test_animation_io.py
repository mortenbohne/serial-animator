from pathlib import Path
import pytest
import pymel.core as pm
import serial_animator.animation_io as animation_io
import logging

from serial_animator import log

logger = log.log(__name__)


def test_get_attribute_data(keyed_cube):
    data = animation_io.get_attribute_data(keyed_cube.tx)
    assert data == {
        "preInfinity": "constant",
        "postInfinity": "constant",
        "weightedTangents": False,
    }
    pm.setInfinity(keyed_cube.tx, preInfinite="oscillate")
    pm.keyTangent(keyed_cube.tx, weightedTangents=True)
    new_data = animation_io.get_attribute_data(keyed_cube.tx)
    assert new_data["preInfinity"] == "oscillate"
    assert new_data["weightedTangents"] is True


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
    pm.setKeyframe(cube, value=10, time=0, attribute="translateX")
    yield cube
    pm.newFile(force=True)
