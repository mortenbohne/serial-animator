import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Literal

import pymel.core as pm
from serial_animator.file_io import (
    write_json_data,
    archive_files,
    read_data_from_archive,
)
import serial_animator.find_nodes

from serial_animator import log
from serial_animator.exceptions import SerialAnimatorError

_logger = log.log(__name__)


class SerialAnimatorKeyError(SerialAnimatorError):
    pass


InfinityType = Literal[
    "constant", "linear", "constant", "cycle", "cycleRelative", "oscillate"
]


class SerialAnimatorNoKeyError(SerialAnimatorKeyError):
    def __init__(
            self,
            message: Optional[str] = None,
            attribute: Optional[pm.general.Attribute] = None,
    ):
        if not message:
            if attribute:
                message = f"Attribute: {attribute} has no keys!"
            else:
                message = "Attribute has no keys!"
        super().__init__(message)


def load_animation(path: Path, nodes=None):
    _logger.debug(f"Applying animation from {path} to {nodes}")


def get_nodes() -> [pm.PyNode]:
    """
    Gets animated nodes either from selection or if nothing is selected,
    from all scene nodes
    """
    nodes = pm.selected() or pm.ls()
    # don't find animation curves as we will get those from nodes connected to them
    nodes = [node for node in nodes if not isinstance(node, pm.nodetypes.AnimCurveTL)]
    return [node for node in nodes if has_animation(node)]


def get_infinity(attribute: pm.general.Attribute) -> Tuple[InfinityType, InfinityType]:
    """
    Gets the pre- and post-infinity for attribute.
    States are:
    "constant", "linear", "constant", "cycle", "cycleRelative", "oscillate",
    :param attribute: attribute with keys
    :raises: SerialAnimatorNoKeyError
    :return: pre-infinity, post-infinity
    """
    res = pm.setInfinity(attribute, preInfinite=True, postInfinite=True, query=True)
    if res:
        return tuple(res)
    else:
        raise SerialAnimatorNoKeyError(attribute=attribute)


def get_weighted_tangents(attribute: pm.general.Attribute) -> bool:
    """
    Checks if keys on an attribute have weighted tangents
    :param attribute: attribute with keys
    :raises: SerialAnimatorNoKeyError
    :return: True if keys have weighted tangents, false if not.
    """
    weighted_tangents = pm.keyTangent(attribute, weightedTangents=True, query=True)
    if weighted_tangents:
        return weighted_tangents[0]
    else:
        raise SerialAnimatorNoKeyError(attribute=attribute)


def has_animation(node):
    """Tests if node has keyframes"""
    return pm.keyframe(node, q=True, keyframeCount=True) > 0


def get_node_data(node, start: Optional[float] = None, end: Optional[float] = None):
    data = dict()
    for attribute, _ in node.inputs(
            plugs=True, connections=True, type=pm.nodetypes.AnimCurveTL
    ):
        # todo: if node have keys out of range, should keyframes be inserted at start, end?
        # nodes might have keyframes out of range of start, end
        attribute_data = get_attribute_data(attribute=attribute, start=start, end=end)
        if attribute_data["keys"]:
            data[attribute.shortName()] = attribute_data
    return data


def get_attribute_data(
        attribute: pm.general.Attribute,
        start: Optional[float] = None,
        end: Optional[float] = None,
):
    data = dict()
    pre_infinity, post_infinity = get_infinity(attribute)
    data["preInfinity"] = pre_infinity
    data["postInfinity"] = post_infinity
    data["weightedTangents"] = get_weighted_tangents(attribute)
    data["keys"] = get_key_data(attribute, start, end)

    return data


def get_key_data(
        attribute: pm.general.Attribute,
        start: Optional[float] = None,
        end: Optional[float] = None,
) -> dict:
    """
    Gets the animation-data for an attribute
    :param attribute:
    :param start:
    :param end:
    :return:
    """
    data = dict()
    time_values = pm.keyframe(
        attribute,
        query=True,
        time=(start, end),
        absolute=True,
        timeChange=True,
        valueChange=True,
    )
    tangent_values = pm.keyTangent(
        attribute,
        query=True,
        time=(start, end),
        inAngle=True,
        outAngle=True,
        inWeight=True,
        outWeight=True,
        inTangentType=True,
        outTangentType=True,
        lock=True,
        weightLock=True,
    )
    for i, time_value in enumerate(time_values):
        time, value = time_value
        start_index = i * 8
        tangent = tangent_values[start_index: start_index + 7]
        data[float(time)] = [value, tangent]
    return data


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
        node_names.append(serial_animator.find_nodes.get_node_path(node))
    data["nodes"] = node_names
    data["frame_range"] = frame_range
    data["time_unit"] = get_time_unit()
    return data


def get_anim_data(nodes=None, frame_range=None) -> dict:
    # todo: support animation layers
    nodes = nodes or get_nodes()
    start, end = frame_range or get_frame_range()
    data = dict()
    for node in nodes:
        data[node] = get_node_data(node, start=start, end=end)
    return data


def extract_meta_data(archive) -> dict:
    return read_data_from_archive(archive, json_name="meta_data.json")
