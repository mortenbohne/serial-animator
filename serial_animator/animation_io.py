import os
import pymel.core as pm
import serial_animator.scene_paths as scene_paths

import logging

_logger = logging.getLogger(__name__)


def load_animation(path, nodes=None):
    _logger.debug(f"Applying animation from {path} to {nodes}")


def get_nodes():
    """Gets selected nodes. If no nodes are selected, get all scene nodes"""
    return pm.selected() or pm.ls()


def get_scene_anim_path():
    """Gets the path to the currently open scene if any"""
    return scene_paths.get_current_scene_lib_path()


def get_shared_anim_path():
    """Gets the path to commonly shared poses"""
    return scene_paths.get_shared_lib_path()


def get_user_anim_path():
    """Gets the path to user's library-folder"""
    return scene_paths.get_user_lib_path()
