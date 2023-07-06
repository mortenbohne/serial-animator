"""
Utilities for setting up logging in modules
"""
import logging


class LogLevelContextManager:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.previous_level = logger.getEffectiveLevel()

    def __enter__(self):
        self.logger.setLevel(self.level)

    def __call__(self, func):
        """Allow class to be used as decorator"""

        def decorator(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return decorator

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.previous_level)


class LogAllLevelsContextManager:
    def __init__(self, min_level=logging.CRITICAL):
        self.min_level = min_level

    def __enter__(self):
        logging.disable(self.min_level)

    def __call__(self, func):
        """Allow class to be used as decorator"""

        def decorator(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return decorator

    def __exit__(self, exit_type, exit_value, exit_traceback):
        logging.disable(logging.NOTSET)


def log(name):
    """
    Simple stream-logger that can also be used as a context manager
    """
    logger = logging.getLogger(name)

    # Hacks since current versions of pytest doesn't allow subclassing
    # of logging.getLogger
    setattr(logger, "all_log_levels", LogAllLevelsContextManager)

    def at_level(level):
        return LogLevelContextManager(logger, level)

    setattr(logger, "at_level", at_level)
    # end of pytest-hacks
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s-%(levelname)s:%(name)s.%(funcName)s: %(message)s", "%H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    # keeping logger.propagate = 1 until pytests work with non-propagating logs
    # logger.propagate = 0
    logger.handlers = [console_handler]

    return logger
