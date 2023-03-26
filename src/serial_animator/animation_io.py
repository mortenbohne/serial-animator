import os
import shutil
from pathlib import Path
from typing import List

import pymel.core as pm
from serial_animator.file_io import (
    write_json_data,
    archive_files,
    read_data_from_archive,
)
import serial_animator.find_nodes

from serial_animator import log

_logger = log.log(__name__)


def load_animation(path: Path, nodes=None):
    _logger.debug(f"Applying animation from {path} to {nodes}")


def get_nodes() -> [pm.PyNode]:
    """
    Gets selected nodes. If no nodes are selected, get all scene nodes
    """
    nodes = pm.selected() or pm.ls()
    # don't find animation curves as we will get those from nodes connected to them
    nodes = [node for node in nodes if not isinstance(node, pm.nodetypes.AnimCurveTL)]
    return [node for node in nodes if has_animation(node)]


def has_animation(node):
    """Tests if node has keyframes"""
    return pm.keyframe(node, q=True, keyframeCount=True) > 0


def save_animation_from_selection(path: Path, preview_dir_path: Path) -> Path:
    """
    Saves data for selected nodes to path and archives preview-image
    with it
    """
    nodes = get_nodes()
    frame_range = get_frame_range()
    anim_data = get_anim_data(nodes=nodes, frame_range=frame_range)
    meta_data = get_meta_data(nodes=nodes, frame_range=frame_range)

    meta_path = preview_dir_path / "meta_data.json"
    anim_data_path = preview_dir_path / "anim_data.json"
    image_paths = list(preview_dir_path.iterdir())
    _logger.debug(f"first image: {image_paths}")
    preview_image = preview_dir_path / "preview.jpg"
    shutil.copy(
        os.path.join(preview_dir_path, get_preview_image(image_paths)), preview_image
    )
    path_data = serial_animator.find_nodes.node_dict_to_path_dict(anim_data)
    write_json_data(path_data, anim_data_path)
    write_json_data(meta_data, meta_path)
    files = [preview_image, meta_path, anim_data_path, *image_paths]
    _logger.debug(f"files: {files}")
    archive = archive_files(
        files=[preview_image, meta_path, anim_data_path, *image_paths], out_path=path
    )

    return archive


def get_preview_image(images: List[Path]) -> Path:
    """Get the image in an image_sequence closest to current time"""
    current_time = int(pm.currentTime())

    def get_difference(img: Path) -> int:
        return abs(int(img.name.split(".")[1]) - current_time)

    return sorted(images, key=get_difference)[0]


def get_frame_range() -> [int, int]:
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


def get_time_unit() -> float:
    return pm.mel.eval("currentTimeUnitToFPS")


def get_meta_data(nodes=None, frame_range=None) -> dict:
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


def get_anim_data(nodes=None, frame_range=None) -> dict:
    nodes = nodes or get_nodes()
    frame_range = frame_range or get_frame_range()
    data = dict()
    for node in nodes:
        data[node] = dict()
    return data


def extract_meta_data(archive) -> dict:
    return read_data_from_archive(archive, json_name="meta_data.json")
