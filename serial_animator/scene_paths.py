import os
import getpass

import pymel.core as pm
from serial_animator.exceptions import SerialAnimatorSceneNotSavedError


def get_scene_name():
    scene_name = pm.sceneName()
    if not scene_name:
        raise SerialAnimatorSceneNotSavedError()
    return os.path.normpath(scene_name)


def get_current_scene_lib_path():
    try:
        scene = os.path.normpath(os.path.normcase(get_scene_name()))
    except SerialAnimatorSceneNotSavedError:
        return
    if scene:
        workspace_path = get_current_workspace()
        if workspace_path in scene:
            c_tokens_len = len(workspace_path.split(os.path.sep))
            scene_name = scene.split(os.path.sep)[c_tokens_len]
            return os.path.normpath(
                os.path.join(get_workspace_lib_path(), "Scenes", scene_name)
            )


def get_current_workspace():
    """
    Gets current working directory
    """
    return os.path.normcase(pm.workspace.getPath())


def get_workspace_lib_path():
    return os.path.normpath(os.path.join(get_current_workspace(), "SerialAnimator"))


def get_shared_lib_path():
    return os.path.join(get_workspace_lib_path(), "_Shared")


def get_user_lib_path(user=None):
    user = user or getpass.getuser()
    return os.path.normpath(os.path.join(get_workspace_lib_path(), f"Users/{user}"))
