import logging
from . import log_functions


def test_log(caplog):

    with caplog.at_level(logging.DEBUG):
        log_functions.log_output()
        assert "logger info showing" in caplog.text
        assert "logger debug silenced" not in caplog.text
        assert "I'm info from log2" in caplog.text
        assert "I'm debug from logger" in caplog.text
        assert "logger2 silenced" not in caplog.text
        assert "logger info silenced" not in caplog.text
        assert "Info from 2 still here" in caplog.text
        assert "Debug from 1 still here" in caplog.text
