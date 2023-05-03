import pathlib
import getpass
from typing import Optional
import pymel.core as pm
from serial_animator.exceptions import SerialAnimatorSceneNotSavedError
from serial_animator import log

_logger = log.log(__name__)


def get_scene_name() -> pathlib.Path:
    scene_name = pm.sceneName()
    if not scene_name:
        raise SerialAnimatorSceneNotSavedError()
    return pathlib.Path(scene_name)


def get_current_scene_lib_path() -> Optional[pathlib.Path]:
    try:
        scene = get_scene_name()
    except SerialAnimatorSceneNotSavedError:
        return
    if scene:
        workspace_path = get_current_workspace()
        if str(scene).startswith(str(workspace_path)):
            workspace_part_number = len(workspace_path.parts)
            scene_parts = scene.parts[workspace_part_number + 1: -1]
            _logger.debug(scene_parts)
            p = pathlib.Path(*[*get_workspace_lib_path().parts, "Scenes", *scene_parts])
            _logger.debug(p)
            return p


def get_current_workspace() -> pathlib.Path:
    """
    Gets current working directory
    """
    return pathlib.Path(pm.workspace.getPath())


def get_workspace_lib_path() -> pathlib.Path:
    return get_current_workspace() / "SerialAnimator"


def get_shared_lib_path() -> pathlib.Path:
    return get_workspace_lib_path() / "_Shared"


def get_user_lib_path(user=None) -> pathlib.Path:
    user = user or getpass.getuser()
    return get_workspace_lib_path() / f"Users/{user}"
