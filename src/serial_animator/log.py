"""
Utilities for setting up logging in modules
"""
import logging


class LogLevelContextManager:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.previous_level = logger.level

    def __enter__(self):
        self.logger.setLevel(self.level)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.previous_level)


class ContextLogger(logging.Logger):
    def log_level_context(self, level):
        return LogLevelContextManager(self, level)


def log(name):
    """
    Simple stream-logger that can also be used as a context manager
    """
    logger = ContextLogger(name)
    # create console handler and set level to debug
    console_handler = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s-%(levelname)s:%(name)s.%(funcName)s: %(message)s", "%H:%M:%S"
    )
    # add formatter to ch
    console_handler.setFormatter(formatter)
    logger.propagate = 0
    # add ch to logger
    logger.handlers = [console_handler]

    return logger
