"""Utilities to find nodes from path-name but in different namespaces"""
from typing import Generator, Optional, List
import pymel.core as pm

from serial_animator import log

_logger = log.log(__name__)

# _logger.setLevel("DEBUG")


def search_nodes(node_paths: List[str], target_nodes: List[pm.PyNode]) -> dict:
    """
    finds relevant nodes in target-dict based on full path defined in
    node_paths.
    Returns a dict with node_path: target_node
    """
    target_dict = get_node_path_dict(target_nodes)
    node_dict = dict()
    stripped_names = [strip_all_namespaces(name) for name in target_dict.keys()]
    node_list = list(target_dict.values())
    scene_namespaces = pm.namespaceInfo(listNamespace=True)
    for node_name in node_paths:
        for ns, search_name in strip_namespaces_gen(node_name):
            if ns in scene_namespaces:
                if search_name in target_dict.keys():
                    node_dict[node_name] = target_dict.get(search_name)
            else:
                c = stripped_names.count(search_name)
                if not c:
                    _logger.debug(f"No nodes match {search_name}")
                elif c == 1:
                    node_dict[node_name] = node_list[stripped_names.index(search_name)]
                    _logger.debug(f"found {node_name}")
                    break
                else:
                    _logger.warning(f"Multiple nodes match {search_name}")
        else:
            _logger.debug(f"Didn't find target for {node_name}")

    return node_dict


def strip_namespaces_gen(name: str) -> Generator[str, None, None]:
    """
    Generator to strip namespaces from node path name.
    Returns namespace-name and node-path
    """
    tokens = name.split("|")
    if len(tokens) == 1:
        _logger.warning(f"{name} is not a valid node-path")
        yield
    parts = tokens[1].split(":")
    for i, part in enumerate(parts[:-1]):
        search_string = ":".join(parts[: i + 1]) + ":"
        yield part, name.replace(search_string, part + ":")
    full_ns = ":".join(parts[:-1]) + ":"

    yield "", name.replace(full_ns, "")


def strip_all_namespaces(name: str) -> Optional[str]:
    """Strips all namespaces from node-path"""
    tokens = name.split("|")
    if len(tokens) == 1:
        _logger.warning(f"{name} is not a valid node-path")
        return
    namespaces = ":".join(tokens[1].split(":")[:-1]) + ":"
    return name.replace(namespaces, "")


def get_node_path_dict(nodes: List[pm.PyNode]) -> dict:
    path_dict = dict()
    for node in nodes:
        path_dict[get_node_path(node)] = node
    return path_dict


def node_dict_to_path_dict(node_dict: dict) -> dict:
    node_path_data = dict()
    for k, v in node_dict.items():
        node_path_data[get_node_path(k)] = v
    return node_path_data


def get_node_path(node):
    try:
        return node.fullPath()
    except AttributeError:
        return node.name()
