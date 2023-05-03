import pathlib
import pytest
import getpass

try:
    import pymel.core as pm
except ImportError:
    pm = pytest.importorskip("pymel.core")

import serial_animator.scene_paths as scene_paths
from serial_animator.exceptions import SerialAnimatorSceneNotSavedError

import logging

_logger = logging.getLogger(__name__)
# _logger.setLevel(logging.DEBUG)


def test_get_scene_name(tmp_scene):
    assert scene_paths.get_scene_name() == tmp_scene
    pm.newFile(force=True)
    with pytest.raises(SerialAnimatorSceneNotSavedError):
        scene_paths.get_scene_name()


def test_get_current_scene_lib_path(tmp_path_factory, tmp_workspace):
    out_path = pathlib.Path(tmp_workspace / "SerialAnimator/Scenes")
    out_path.mkdir(parents=True)
    pm.saveAs(out_path / "tmp.mb")
    assert (
            "Scenes" and "SerialAnimator" in scene_paths.get_current_scene_lib_path().parts
    )
    pm.newFile(force=True)
    assert scene_paths.get_current_scene_lib_path() is None
    tmp_path_outside_workspace = tmp_path_factory.mktemp("tmp")
    pm.saveAs(tmp_path_outside_workspace / "tmp.mb")
    assert scene_paths.get_current_scene_lib_path() is None


def test_get_current_workspace(tmp_workspace):
    assert scene_paths.get_current_workspace() == tmp_workspace


def test_get_workspace_lib_path():
    assert scene_paths.get_workspace_lib_path().parts[-1] == "SerialAnimator"


def test_get_shared_lib_path():
    assert scene_paths.get_shared_lib_path().parts[-1] == "_Shared"


def test_get_user_lib_path():
    assert scene_paths.get_user_lib_path().parts[-2:] == ("Users", getpass.getuser())


@pytest.fixture()
def tmp_scene(tmp_path):
    tmp_file = tmp_path / "tmp_file.mb"
    pm.saveAs(tmp_file)
    yield tmp_file


@pytest.fixture()
def tmp_workspace(tmp_path):
    old_workspace = pm.workspace.getPath()
    pm.workspace.open(tmp_path)
    yield tmp_path
    pm.workspace.open(old_workspace)
