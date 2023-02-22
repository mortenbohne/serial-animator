import logging

import pytest
import pymel.core as pm
import serial_animator.find_nodes as find_nodes


def test_search_nodes(namespaced_cube):
    node_paths = ["|FOO:BAR:namespacedCube"]
    assert len(find_nodes.search_nodes(node_paths, [namespaced_cube]).keys()) == 1
    node_paths = ["|BAR:namespacedCube"]
    assert len(find_nodes.search_nodes(node_paths, [namespaced_cube]).keys()) == 1
    node_paths = ["|namespacedCube"]
    assert len(find_nodes.search_nodes(node_paths, [namespaced_cube]).keys()) == 1
    node_dict = find_nodes.search_nodes(node_paths, [namespaced_cube])
    assert isinstance(node_dict, dict)


def test_strip_namespace_gen(namespaced_cube):
    res = list(find_nodes.strip_namespaces_gen(namespaced_cube.fullPath()))
    assert len(res) == 3
    assert res[0][0] == "FOO"
    assert res[-1][0] == ""


def test_strip_all_namespaces(cube, namespaced_cube, caplog):
    assert find_nodes.strip_all_namespaces(cube.fullPath()) == "|pCube1"
    assert (
            find_nodes.strip_all_namespaces(namespaced_cube.fullPath()) == "|namespacedCube"
    )
    with caplog.at_level(logging.WARNING):
        assert find_nodes.strip_all_namespaces("not_a_node_path") == None
        assert "not a valid node-path" in caplog.text


def test_get_node_path_dict(two_cubes):
    assert isinstance(find_nodes.get_node_path_dict(two_cubes), dict)


@pytest.fixture()
def two_cubes():
    cube1 = pm.polyCube(constructionHistory=False)[0]
    cube2 = pm.polyCube(constructionHistory=False)[0]
    yield [cube1, cube2]
    pm.newFile(force=True)


@pytest.fixture()
def cube():
    cube = pm.polyCube(constructionHistory=False)[0]
    yield cube
    pm.newFile(force=True)


@pytest.fixture()
def namespaced_cube():
    pm.namespace(add="FOO:BAR")
    pm.namespace(set="FOO:BAR")
    cube = pm.polyCube(constructionHistory=False, name="namespacedCube")[0]
    pm.namespace(set=":")
    yield cube
    pm.newFile(force=True)
