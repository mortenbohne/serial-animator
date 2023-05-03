from pathlib import Path
import tempfile
import pymel.core as pm
from serial_animator.exceptions import SerialAnimatorError
from serial_animator.file_io import (
    archive_files,
    read_data_from_archive,
    write_json_data,
)
import serial_animator.find_nodes as find_nodes

from serial_animator import log

_logger = log.log(__name__)

# _logger.setLevel("DEBUG")


class SerialAnimatorPoseLibraryError(SerialAnimatorError):
    """Overall error for tool"""


class SerialAnimatorSavePoseError(SerialAnimatorPoseLibraryError):
    """Error when saving pose"""


def get_nodes() -> list:
    """
    Gets selected nodes. If no nodes are selected, get all scene nodes
    """
    return pm.selected() or pm.ls()


def get_data_from_nodes(nodes=None) -> dict:
    """
    Gets keyable data from nodes and returns them as a node-dict with
    a dict of attribute-names and values
    """
    nodes = nodes or get_nodes()
    data = dict()
    for node in nodes:
        data[node] = get_keyable_data(node)
    return data


def get_path_data_from_nodes(nodes=None) -> dict:
    """
    Gets keyable data from nodes and returns them as a node-path-dict
    with a dict of attribute-names and values
    """
    data = get_data_from_nodes(nodes)
    return find_nodes.node_dict_to_path_dict(data)


def save_pose_from_selection(path: Path, img_path: Path) -> Path:
    """
    Saves data for selected nodes to path and archives preview-image
    with it
    """
    data = get_path_data_from_nodes()
    return save_data(path, data, img_path)


def save_data(path, data: dict, img_path) -> Path:
    with tempfile.TemporaryDirectory(prefix="serial_animator_") as tmp_dir:
        pose_path = Path(tmp_dir) / "pose.json"
        write_json_data(data, pose_path)
        archive = archive_files(files=[pose_path, img_path], out_path=path)
    return archive


def get_keyable_data(node) -> dict:
    data = dict()
    for a in [a for a in node.listAttr() if a.isKeyable()]:
        data[a.attrName()] = a.get()
    return data


def interpolate(target: dict, origin: dict, weight: float):
    for node, node_data in target.items():
        for attribute_name, value in node_data.items():
            if not node.hasAttr(attribute_name):
                _logger.debug(
                    f"{node} doesn't have the attribute {attribute_name}. Skipping!"
                )
                continue
            target_attribute = node.attr(attribute_name)
            if target_attribute.isLocked():
                _logger.debug(f"{target_attribute} is locked")
                continue
            if target_attribute.isFromReferencedFile():
                _logger.debug(
                    f"{target_attribute} has incoming connections from reference"
                )
                continue
            try:
                o_value = origin[node][attribute_name]
                delta = (value - o_value) * weight
                target_attribute = node.attr(attribute_name)

                target_attribute.set(o_value + delta)
            except KeyError:
                # attribute not in target dict, so apply 100% of target value
                node.attr(attribute_name).set(value)


def read_pose_data(path) -> dict:
    data = read_data_from_archive(path, json_name="pose.json")
    _logger.debug(data)
    return data


def read_pose_data_to_nodes(path, nodes=None) -> dict:
    data = read_pose_data(path)
    node_dict = find_nodes.search_nodes(list(data.keys()), nodes)
    pose = dict()
    for node_name, node_data in data.items():
        node = node_dict.get(node_name)
        if node:
            pose[node] = data[node_name]
    return pose


def start_undo():
    _logger.debug("Start undo")
    pm.undoInfo(
        openChunk=True,
        chunkName="SerialAnimator Apply Pose",
        undoName="SerialAnimator Apply Pose",
        redoName="SerialAnimator Apply Pose",
    )


def end_undo():
    _logger.debug("End undo")
    pm.undoInfo(closeChunk=True)


def refresh_viewport():
    pm.refresh()


def get_pose_filetype() -> str:
    return "pose"
