import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Literal, Dict, Iterable
from collections import OrderedDict

import serial_animator.find_nodes as find_nodes

import pymel.core as pm
from serial_animator.file_io import (
    write_json_data,
    archive_files,
    read_data_from_archive,
)
from serial_animator.utils import Undo
import serial_animator.find_nodes


from serial_animator import log
from serial_animator.exceptions import SerialAnimatorError

_logger = log.log(__name__)
_logger.setLevel("DEBUG")


class SerialAnimatorKeyError(SerialAnimatorError):
    pass


class SerialAnimatorLoadDataError(SerialAnimatorError):
    pass


class SerialAnimatorAttributeMismatchError(SerialAnimatorLoadDataError):
    pass


InfinityType = Literal[
    "constant", "linear", "constant", "cycle", "cycleRelative", "oscillate"
]
InOutTangentType = Literal[
    "spline",
    "linear",
    "fast",
    "slow",
    "flat",
    "step",
    "stepnext",
    "fixed",
    "clamped",
    "plateau",
    "auto",
    "autoease",
    "automix",
    "autocustom",
]
TangentDataType = Tuple[
    float, float, float, float, InOutTangentType, InOutTangentType, bool, bool
]
KeyDataType = OrderedDict[float, Tuple[float, TangentDataType]]


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


@Undo(name="Serial-Animator: Load Animation")
def load_animation(
        path: Path, nodes=None, start: Optional[float] = None, end: Optional[float] = None
):
    data = read_animation_data(path)
    node_dict = find_nodes.search_nodes(list(data.keys()), nodes)
    for node_name, node_data in data.items():
        node = node_dict.get(node_name)
        if node:
            set_node_data(node, data[node_name], start, end)


def read_animation_data(path: Path) -> dict:
    return read_data_from_archive(path, json_name="anim_data.json")


def get_nodes_with_animation() -> [pm.PyNode]:
    """
    Gets animated nodes either from selection or if nothing is selected,
    from all scene nodes
    """
    nodes = pm.selected() or pm.ls()
    # don't find animation curves as we will get those from nodes connected to them
    nodes = [node for node in nodes if not isinstance(node, pm.nodetypes.AnimCurve)]
    return [node for node in nodes if has_animation(node)]


def get_selection() -> List[pm.PyNode]:
    return pm.selected()


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


def set_infinity(
        attribute: pm.general.Attribute,
        pre_infinity: InfinityType,
        post_infinity: InfinityType,
):
    """
    Sets the pre- and post-infinity for attribute.
    States are:
    "constant", "linear", "constant", "cycle", "cycleRelative", "oscillate".

    Note:
        Setting infinity on an attribute with no keys has no effect,
        but doesn't raise
    :param attribute: attribute with keys
    :param pre_infinity: string representing infinity-type
    :param post_infinity: string representing infinity-type
    """
    pm.setInfinity(attribute, preInfinite=pre_infinity, postInfinite=post_infinity)


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


def get_weighted_tangent_value_to_apply(
        attribute: pm.general.Attribute, input_value: bool
):
    if input_value is True:
        return input_value
    existing_value = pm.keyTangent(attribute, weightedTangents=True, query=True)
    if existing_value is True:
        return existing_value
    return input_value


def set_weighted_tangents(attribute: pm.general.Attribute, weighted: bool) -> bool:
    """
    Sets weighted tangents for keys on an attribute
    """
    pm.keyTangent(attribute, weightedTangents=weighted)


def has_animation(node):
    """Tests if node has keyframes"""
    return pm.keyframe(node, q=True, keyframeCount=True) > 0


def set_node_data(
        node, data, start: Optional[float] = None, end: Optional[float] = None
):
    for attribute_name, attribute_data in data.items():
        input_type = attribute_data.get("attributeType")
        if not hasattr(node, attribute_name):
            _logger.debug(f"{node}.{attribute_name} doesn't exist. Adding attribute")
            node.addAttr(attribute_name, attributeType=input_type, keyable=True)
        attribute = node.attr(attribute_name)
        attribute_type = attribute.type()
        if input_type != attribute_type:
            raise SerialAnimatorAttributeMismatchError(
                f"Error loading animation. {node}.{attribute_name} of type {attribute_type} "
                f"doesn't match input type {input_type}"
            )
        key_data = attribute_data.get("keys")
        remove_existing_keys(attribute, key_data, start=start, end=end)
        weighted_tangents = get_weighted_tangent_value_to_apply(
            attribute=attribute, input_value=attribute_data.get("weightedTangents")
        )
        w = pm.keyTangent(attribute, query=True, weightedTangents=True)
        _logger.debug(f"current state of weighted tangents: {w}")
        set_infinity(
            attribute=attribute,
            pre_infinity=attribute_data.get("preInfinity"),
            post_infinity=attribute_data.get("preInfinity"),
        )

        set_key_data(
            attribute=attribute,
            data=key_data,
            start=start,
            end=end,
            weighted_tangents=weighted_tangents,
        )


def remove_existing_keys(
        attribute,
        key_data,
        start: Optional[float] = None,
        end: Optional[float] = None,
):
    # get range of keys to remove
    time_values = list(key_data)
    min_frame = float(time_values[0])
    max_frame = float(time_values[-1])
    if start:
        min_frame = max(start, min_frame)
    if end:
        max_frame = min(end, max_frame)
    # remove existing keys in area we are writing data to
    pm.cutKey(attribute, time=(min_frame, max_frame), clear=True)


def get_node_data(node, start: Optional[float] = None, end: Optional[float] = None):
    data = dict()
    for attribute, _ in node.inputs(
            plugs=True, connections=True, type=pm.nodetypes.AnimCurve
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
) -> dict:
    """
    Gets key-data for attribute
    :param attribute:
    :param start:
    :param end:
    :return:
    """
    data = dict()
    pre_infinity, post_infinity = get_infinity(attribute)
    data["attributeType"] = attribute.type()
    data["preInfinity"] = pre_infinity
    data["postInfinity"] = post_infinity
    data["weightedTangents"] = get_weighted_tangents(attribute)
    data["keys"] = get_key_data(attribute, start, end)

    return data


def get_key_data(
        attribute: pm.general.Attribute,
        start: Optional[float] = None,
        end: Optional[float] = None,
) -> KeyDataType:
    """
    Gets the animation-data for an attribute
    :param attribute:
    :param start:
    :param end:
    :return:
    OrderedDict with key-data:
    {
        frame(float): tuple(
            key-value(float),
            tangent-data tuple(
                inAngle (float),
                outAngle (float),
                inWeight (float),
                outWeight (float)
                inTangentType (str)
                outTangentType (str)
                lock (bool)
                weightLock (bool)
            )
        )
    }

    """
    data = OrderedDict()
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
        tangent = tuple(tangent_values[start_index: start_index + 8])
        data[float(time)] = (value, tangent)
    return data


def set_key_data(
        attribute: pm.general.Attribute,
        data: KeyDataType,
        start: Optional[float] = None,
        end: Optional[float] = None,
        weighted_tangents: Optional[bool] = True,
):
    """
    Removes existing keyframes in time-range and create new keys based on data
    :param attribute: attribute to set keys on
    :param data: data to create keyframes from
    :param start: ignore data before start
    :param end: ignore data after end
    :param weighted_tangents: If False, Maya will not be able to set lock-state of tangents
    """
    should_change_curve_weight = False
    # if we are trying to set weighted tangents, we need to ensure that
    # the curve has that set. In order to do that, the curve must have keys
    if weighted_tangents is True:
        if pm.keyTangent(attribute, weightedTangents=True, query=True) is not True:
            should_change_curve_weight = True
    for time, key_data in data.items():
        if start:
            if time < start:
                continue
        if end:
            if time > end:
                continue
        value, tangent_data = key_data
        pm.setKeyframe(attribute, time=time, value=value)
        if should_change_curve_weight:
            # this is not settable before curve has keys!
            set_weighted_tangents(attribute=attribute, weighted=weighted_tangents)
            should_change_curve_weight = False
        set_tangent(
            attribute,
            time=time,
            tangent_data=tangent_data,
            curve_weights=weighted_tangents,
        )


def set_tangent(
        attribute: pm.general.Attribute,
        time: float,
        tangent_data: TangentDataType,
        curve_weights: Optional[bool] = True,
):
    """Sets tangent-data for keyframe at time"""
    _logger.debug(curve_weights)
    _logger.debug(get_weighted_tangents(attribute))
    (
        in_angle,
        out_angle,
        in_weight,
        out_weight,
        in_tangent_type,
        out_tangent_type,
        lock,
        weight_lock,
    ) = tangent_data
    if curve_weights is True:
        pm.keyTangent(
            attribute,
            time=time,
            inAngle=in_angle,
            outAngle=out_angle,
            inWeight=in_weight,
            outWeight=out_weight,
            inTangentType=in_tangent_type,
            outTangentType=out_tangent_type,
            lock=lock,
            weightLock=weight_lock,
        )
    else:
        pm.keyTangent(
            attribute,
            time=time,
            inAngle=in_angle,
            outAngle=out_angle,
            inWeight=in_weight,
            outWeight=out_weight,
            inTangentType=in_tangent_type,
            outTangentType=out_tangent_type,
            lock=lock,
        )


def save_animation_from_selection(path: Path, preview_dir_path: Path) -> Path:
    """
    Saves data for selected nodes to path and archives preview-image
    with it
    """
    nodes = get_nodes_with_animation()
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
    """Gets current time unit in fps"""
    return pm.mel.eval("currentTimeUnitToFPS")


def get_meta_data(nodes: Iterable, frame_range=None) -> dict:
    frame_range = frame_range or get_frame_range()
    data = dict()
    node_names = list()
    for node in nodes:
        node_names.append(serial_animator.find_nodes.get_node_path(node))
    data["nodes"] = node_names
    data["frame_range"] = frame_range
    data["time_unit"] = get_time_unit()
    return data


def get_anim_data(nodes: Iterable, frame_range=None) -> dict:
    # todo: support animation layers
    start, end = frame_range or get_frame_range()
    data = dict()
    for node in nodes:
        data[node] = get_node_data(node, start=start, end=end)
    return data


def extract_meta_data(archive) -> dict:
    return read_data_from_archive(archive, json_name="meta_data.json")
