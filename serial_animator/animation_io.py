import os
import shutil
import tempfile

import pymel.core as pm
from serial_animator.file_io import (
    write_json_data,
    archive_files,
    write_pynode_data_to_json,
)
import serial_animator.scene_paths as scene_paths

import logging

_logger = logging.getLogger(__name__)


def load_animation(path, nodes=None):
    _logger.debug(f"Applying animation from {path} to {nodes}")


def get_nodes():
    """Gets selected nodes. If no nodes are selected, get all scene nodes"""
    nodes = pm.selected() or pm.ls()
    return [node for node in nodes if pm.keyframe(node, q=True, keyframeCount=True) > 0]


def save_animation_from_selection(path, preview_dir_path):
    """
    Saves data for selected nodes to path and archives preview-image
    with it
    """
    nodes = get_nodes()
    frame_range = get_frame_range()
    anim_data = get_anim_data(nodes=nodes, frame_range=frame_range)
    meta_data = get_meta_data(nodes=nodes, frame_range=frame_range)
    tmp_dir = tempfile.mkdtemp()
    meta_path = os.path.join(tmp_dir, "anim_data.json")
    inner_path = os.path.join(tmp_dir, "data")
    os.makedirs(inner_path)
    anim_data_path = os.path.join(inner_path, "anim_data.json")
    images = os.listdir(preview_dir_path)
    data_tar_path = os.path.join(inner_path, "data.tar")
    _logger.debug(images[0])
    preview_image = os.path.join(tmp_dir, "preview.jpg")
    _logger.debug(preview_image)
    shutil.copy(
        os.path.join(preview_dir_path, get_preview_image(images)), preview_image
    )
    try:
        write_pynode_data_to_json(anim_data, anim_data_path)
        inner_archive = archive_files(
            files=[anim_data_path, *images], out_path=data_tar_path
        )
        write_json_data(meta_data, meta_path)
        archive = archive_files(
            files=[preview_image, meta_path, inner_archive], out_path=path
        )
    finally:
        shutil.rmtree(tmp_dir)
    return archive


def get_preview_image(images):
    """Get the image in an image_sequence closest to current time"""
    current_time = int(pm.currentTime())

    def get_difference(img):
        return abs(int(img.split(".")[1]) - current_time)

    return sorted(images, key=get_difference)[0]


def get_frame_range():
    """
    Gets the selected frame_range from time-slider. If nothing is
    selected, get playback range
    """
    time_slider = pm.language.MelGlobals.get("gPlayBackSlider")
    if pm.windows.timeControl(time_slider, q=True, rangeVisible=True):
        start, end = pm.windows.timeControl(time_slider, q=True, rangeArray=True)
    else:
        start = pm.animation.playbackOptions(q=True, min=True)
        end = pm.animation.playbackOptions(q=True, max=True)
    return int(start), int(end)


def get_time_unit():
    return pm.general.currentUnit(q=True, time=True)


def get_meta_data(nodes=None, frame_range=None):
    nodes = nodes or get_nodes()
    frame_range = frame_range or get_frame_range()
    data = dict()
    node_names = list()
    for node in nodes:
        try:
            node_names.append(node.fullPath())
        except AttributeError:
            node_names.append(node.name())
    data["nodes"] = node_names
    data["frame_range"] = frame_range
    data["time_unit"] = get_time_unit()
    return data


def get_anim_data(nodes=None, frame_range=None):
    nodes = nodes or get_nodes()
    frame_range = frame_range or get_frame_range()
    data = dict()
    for node in nodes:
        data[node] = dict()
    return data
