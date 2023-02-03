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
