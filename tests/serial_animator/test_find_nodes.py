import pytest
import pymel.core as pm
import serial_animator.find_nodes as find_nodes
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def test_search_nodes(namespaced_cube, cube, caplog):
    node_paths = ["|FOO:BAR:namespacedCube"]
    assert len(find_nodes.search_nodes(node_paths, [namespaced_cube]).keys()) == 1
    node_paths = ["|BAR:namespacedCube"]
    assert len(find_nodes.search_nodes(node_paths, [namespaced_cube]).keys()) == 1
    node_paths = ["|namespacedCube"]
    assert len(find_nodes.search_nodes(node_paths, [namespaced_cube]).keys()) == 1
    node_dict = find_nodes.search_nodes(node_paths, [namespaced_cube])
    assert isinstance(node_dict, dict)
    _logger.info(namespaced_cube)
    cube.rename("namespacedCube")
    with caplog.at_level(logging.WARNING):
        find_nodes.search_nodes(node_paths, [namespaced_cube, cube])
        assert "Multiple nodes match" in caplog.text
    with caplog.at_level(logging.DEBUG):
        find_nodes.search_nodes(["|nonExistentNode"], [cube])
        assert "Didn't find target for" in caplog.text

    _logger.info(cube)


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
