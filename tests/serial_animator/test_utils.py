import pytest

try:
    import pymel.core as pm
except ImportError:
    pm = pytest.importorskip("pymel.core")
import serial_animator.utils as utils
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def test_get_user_preference_dir():
    assert isinstance(utils.get_user_preference_dir(), str)


def test_undo(cube):
    orig_val = cube.tx.get()
    cube.tx.set(10)
    first_move = cube.tx.get()
    with utils.Undo(name="move stuff"):
        cube.tx.set(20)
        cube.tx.set(30)
    pm.undo()
    assert cube.tx.get() == first_move
    with utils.Undo(undoable=False, name="not undoable"):
        cube.tx.set(20)
        cube.tx.set(30)
    pm.undo()
    assert cube.tx.get() == orig_val
    with pytest.raises(pm.general.MayaNodeError):
        cube = test_undo_decorator()
        pm.undo()
        _ = cube.tx.get()


@utils.Undo()
def test_undo_decorator():
    cube, _ = pm.polyCube()
    cube.tx.set(10)
    cube.tx.set(20)
    return cube


def test_context_decorator():
    # just run it and see it doesn't break to increase coverage
    with utils.ContextDecorator():
        pass


@pytest.mark.skipif(
    utils.is_interactive() is False, reason="ScriptJobs only works in interactive mode"
)
def test_setup_scene_opened_callback(caplog):
    pm.newFile(force=True)
    callback_id = utils.setup_scene_opened_callback(log_warning_test, parent=None)
    assert isinstance(callback_id, int)
    with caplog.at_level(logging.WARNING):
        pm.newFile(force=True)
        assert "test" in caplog.text


def log_warning_test():
    _logger.warning("test")


def test_is_interactive():
    assert utils.is_interactive() is False
