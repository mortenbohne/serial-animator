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
    logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        ' %(asctime)s - %(levelname)s - %(name)s - %(funcName)s: %(message)s')
    logger.propagate = False
    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.handlers = [ch]

    return logger
