"""
Utilities for setting up logging in modules
"""
import logging


def log(name):
    """
    Simple stream-logger
    """
    logger = logging.getLogger(name)
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

