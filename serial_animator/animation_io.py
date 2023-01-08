import os
import shutil

import pymel.core as pm
from serial_animator.file_io import (
    write_json_data,
    archive_files,
    write_pynode_data_to_json,
    read_data_from_archive,
)

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


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

    meta_path = os.path.join(preview_dir_path, "meta_data.json")
    anim_data_path = os.path.join(preview_dir_path, "anim_data.json")
    images = [
        os.path.join(preview_dir_path, img) for img in os.listdir(preview_dir_path)
    ]
    _logger.debug(f"first image: {images}")
    preview_image = os.path.join(preview_dir_path, "preview.jpg")
    shutil.copy(
        os.path.join(preview_dir_path, get_preview_image(images)), preview_image
    )
    write_pynode_data_to_json(anim_data, anim_data_path)
    write_json_data(meta_data, meta_path)
    files = [preview_image, meta_path, anim_data_path, *images]
    _logger.debug(f"files: {files}")
    archive = archive_files(
        files=[preview_image, meta_path, anim_data_path, *images], out_path=path
    )

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
    return pm.mel.eval("currentTimeUnitToFPS")


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


def extract_meta_data(archive):
    return read_data_from_archive(archive, json_name="meta_data.json")
