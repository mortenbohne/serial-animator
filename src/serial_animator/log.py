"""
Utilities for setting up logging in modules
"""
import logging

NOTSET = logging.NOTSET
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


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

    # add ch to logger
    logger.handlers = [console_handler]

    return logger
