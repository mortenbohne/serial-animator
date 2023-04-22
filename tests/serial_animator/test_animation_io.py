from pathlib import Path
import pytest
import pymel.core as pm
import serial_animator.animation_io as animation_io
import logging

from serial_animator import log

logger = log.log(__name__)


def test_get_node_data(keyed_cube):
    all_data = animation_io.get_node_data(keyed_cube)
    assert all_data[keyed_cube.tx.shortName()] == animation_io.get_attribute_data(
        keyed_cube.translateX
    )
    assert len(all_data.keys()) == 2
    assert len(animation_io.get_node_data(keyed_cube, start=2, end=20).keys()) == 1
    assert len(animation_io.get_node_data(keyed_cube, start=100, end=200).keys()) == 0


def test_get_attribute_data(keyed_cube):
    data = animation_io.get_attribute_data(keyed_cube.tx)
    assert data["preInfinity"] == "constant"
    assert data["postInfinity"] == "constant"
    assert data["weightedTangents"] is True
    assert len(data["keys"].keys()) == 2
    pm.setInfinity(keyed_cube.tx, preInfinite="oscillate")
    animation_io.set_weighted_tangents(keyed_cube.tx, False)
    new_data = animation_io.get_attribute_data(keyed_cube.tx)
    assert new_data["preInfinity"] == "oscillate"
    assert new_data["weightedTangents"] is False


def test_get_key_data(keyed_cube):
    data = animation_io.get_key_data(keyed_cube.tx)
    key_0_value, key_0_tangent = data[float(0)]
    key_10_value, key_10_tangent = data[float(10)]
    assert key_0_value == 0.0
    assert key_10_value == 10.0
    for i in range(4):
        pytest.approx(key_0_tangent[i], float(i))
    assert key_0_tangent[4:] == ("fixed", "fixed", False, False)
    assert key_10_tangent[4:] == ("flat", "auto", True, False)
    with pytest.raises(KeyError):
        _ = data[float(3)]
    range_data = animation_io.get_key_data(keyed_cube.tx, start=0, end=20)
    assert data == range_data
    out_of_range_data = animation_io.get_key_data(keyed_cube.tx, start=20, end=30)
    assert len(out_of_range_data) == 0


def test_get_infinity(keyed_cube):
    with pytest.raises(animation_io.SerialAnimatorNoKeyError):
        animation_io.get_infinity(keyed_cube.ty)


def test_set_infinity(keyed_cube):
    animation_io.set_infinity(
        keyed_cube.tx, pre_infinity="oscillate", post_infinity="oscillate"
    )
    assert animation_io.get_infinity(keyed_cube.tx) == ("oscillate", "oscillate")


def test_get_weighted_tangents(keyed_cube):
    with pytest.raises(animation_io.SerialAnimatorNoKeyError):
        animation_io.get_weighted_tangents(keyed_cube.ty)


def test_SerialAnimatorNoKeyError():
    with pytest.raises(animation_io.SerialAnimatorKeyError):
        raise animation_io.SerialAnimatorNoKeyError()


def test_load_animation(caplog, keyed_cube, preview_sequence, tmp_path):
    data_path = tmp_path / "keyed_cube.anim"
    pm.select(keyed_cube)
    animation_io.save_animation_from_selection(data_path, preview_sequence)
    pm.newFile(force=True)
    cube = pm.polyCube(constructionHistory=False)[0]

    animation_io.load_animation(path=data_path, nodes=[cube])
    # assert animation_io.has_animation(cube)


def test_set_node_data(caplog, keyed_cube):
    data = animation_io.get_node_data(keyed_cube)
    pm.newFile(force=True)
    new_cube = pm.polyCube(constructionHistory=False)[0]
    with caplog.at_level(logging.DEBUG):
        animation_io.set_node_data(new_cube, data)
        assert "Adding attribute" in caplog.text
    # pm.delete(new_cube)
    # new_cube = pm.polyCube()[0]
    # new_cube.addAttr("my_custom_attribute", attributeType="bool", keyable=True)
    # with pytest.raises(animation_io.SerialAnimatorAttributeMismatchError):
    #     animation_io.set_node_data(new_cube, data)
    # applied_data = animation_io.get_node_data(new_cube)
    # assert applied_data == data


def test_get_nodes(keyed_cube, cube):
    pm.select(cube)
    assert len(animation_io.get_nodes()) == 0
    pm.select(None)
    assert len(animation_io.get_nodes()) == 1


def test_save_animation_from_selection(tmp_path, preview_sequence, keyed_cube):
    out_path = tmp_path / "output.anim"
    pm.select(keyed_cube)
    result = animation_io.save_animation_from_selection(out_path, preview_sequence)
    assert result.is_file()


@pytest.fixture()
def keyed_cube():
    cube = pm.polyCube(constructionHistory=False)[0]
    cube.addAttr("my_custom_attribute", attributeType="long", keyable=True)
    pm.setKeyframe(cube, value=0, time=0, attribute="translateX")
    pm.setKeyframe(cube, value=1, time=0, attribute="my_custom_attribute")
    pm.keyTangent(cube.tx, weightedTangents=True)
    pm.keyTangent(
        cube.tx,
        time=0,
        inAngle=0.0,
        outAngle=1.0,
        inWeight=2.0,
        outWeight=3.0,
        inTangentType="fixed",
        outTangentType="fixed",
        lock=False,
        weightLock=False,
    )
    pm.setKeyframe(cube, value=10, time=10, attribute="translateX")
    pm.keyTangent(cube.tx, time=10, inTangentType="flat", outTangentType="auto")
    yield cube
