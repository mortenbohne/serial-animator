import pytest
import pymel.core as pm

import serial_animator.find_nodes as find_nodes
import logging

import serial_animator.log

_logger = serial_animator.log.log(__name__)


def test_search_nodes(namespaced_cube, cube, caplog):
    node_paths = ["|FOO:BAR:namespacedCube"]
    assert len(find_nodes.search_nodes(node_paths, [namespaced_cube]).keys()) == 1
    node_paths = ["|BAR:namespacedCube"]
    assert len(find_nodes.search_nodes(node_paths, [namespaced_cube]).keys()) == 1
    node_paths = ["|namespacedCube"]
    assert len(find_nodes.search_nodes(node_paths, [namespaced_cube]).keys()) == 1
    node_dict = find_nodes.search_nodes(node_paths, [namespaced_cube])
    assert isinstance(node_dict, dict)
    cube.rename("namespacedCube")
    with caplog.at_level(logging.WARNING):
        find_nodes.search_nodes(node_paths, [namespaced_cube, cube])
        assert "Multiple nodes match" in caplog.text
    with caplog.at_level(logging.DEBUG):
        find_nodes.search_nodes(["|nonExistentNode"], [cube])
        assert "Didn't find target for" in caplog.text


def test_strip_namespaces_gen(namespaced_cube, cube, caplog):
    res = list(find_nodes.strip_namespaces_gen(namespaced_cube.fullPath()))
    assert len(res) == 3
    assert res[0][0] == "FOO"
    assert res[-1][0] == ""
    assert next(find_nodes.strip_namespaces_gen(cube.fullPath())) == ("", cube.longName())
    with caplog.at_level(logging.WARNING):
        assert next(find_nodes.strip_namespaces_gen("invalidNodePath")) is None
        assert "not a valid node-path" in caplog.text


def test_strip_all_namespaces(cube, namespaced_cube, caplog):
    assert find_nodes.strip_all_namespaces(cube.fullPath()) == "|pCube1"
    assert (
            find_nodes.strip_all_namespaces(namespaced_cube.fullPath()) == "|namespacedCube"
    )
    with caplog.at_level(logging.WARNING):
        assert find_nodes.strip_all_namespaces("not_a_node_path") == None
        assert "not a valid node-path" in caplog.text


def test_get_node_path_dict(two_cubes, time_node):
    assert isinstance(find_nodes.get_node_path_dict(two_cubes), dict)
    assert find_nodes.get_node_path_dict([time_node]) == dict()


@pytest.fixture()
def time_node():
    yield pm.ls(type=pm.nodetypes.Time)[0]


@pytest.fixture()
def namespaced_cube():
    pm.namespace(add="FOO:BAR")
    pm.namespace(set="FOO:BAR")
    cube = pm.polyCube(constructionHistory=False, name="namespacedCube")[0]
    pm.namespace(set=":")
    yield cube
    pm.newFile(force=True)


def test_node_dict_to_path_dict(cube, time_node):
    node_dict = dict()
    node_dict[cube] = 1
    path_dict = find_nodes.node_dict_to_path_dict(node_dict)
    assert len(node_dict.keys()) == len(path_dict)
    for node in node_dict.keys():
        v = node_dict[node]
        assert v == path_dict[node.fullPath()]
    non_dag_node_dict = dict()
    non_dag_node_dict[time_node] = 1
    non_dag_path_dict = find_nodes.node_dict_to_path_dict(non_dag_node_dict)
    for node in non_dag_node_dict.keys():
        v = non_dag_node_dict[node]
        assert v == non_dag_path_dict[node.longName()]
