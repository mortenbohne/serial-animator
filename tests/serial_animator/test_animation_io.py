from pathlib import Path
import pytest
import pymel.core as pm
import serial_animator.animation_io as animation_io
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def test_load_animation(caplog):
    with caplog.at_level(logging.DEBUG):
        animation_io.load_animation(path=Path())
        assert "Applying" in caplog.text


def test_get_nodes(new_scene, keyed_cube, cube):
    pm.select(cube)
    assert len(animation_io.get_nodes()) == 0
    pm.select(None)
    assert len(animation_io.get_nodes()) == 1


def test_save_animation_from_selection():
    pass


@pytest.fixture()
def new_scene():
    pm.newFile(force=True)


@pytest.fixture()
def keyed_cube():
    cube = pm.polyCube(constructionHistory=False)[0]
    pm.setKeyframe(cube, value=10, time=0, attribute="translateX")
    yield cube
    pm.newFile(force=True)
