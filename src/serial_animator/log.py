"""
Utilities for setting up logging in modules
"""
import os
import sys
import logging
import maya.OpenMaya as om

PROPAGATE = os.getenv("SERIAL_ANIMATOR_LOG_PROPAGATE", 0)


class SuppressScriptEditorOutput:
    """
    Suppresses output to the scriptEditor
    """

    def __init__(self):
        self.callback_id = om.MCommandMessage.addCommandOutputFilterCallback(
            self.suppress
        )

    @staticmethod
    def suppress(_, __, filter_output, ___):
        """
        This is the callback function that gets called when Maya wants to
        print something suppressing the print
        """
        om.MScriptUtil.setBool(filter_output, True)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        om.MMessage.removeCallback(self.callback_id)


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


# copied from: https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions
class SuppressStdOutStdErr:
    """
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    """

    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            os.close(fd)


class SilenceContextManager(SuppressScriptEditorOutput, LogAllLevelsContextManager):
    pass


class SingleLevelFilter(logging.Filter):
    def __init__(self, passlevel, reject):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return (record.levelno != self.passlevel)
        else:
            return (record.levelno == self.passlevel)


class CustomLogger(logging.Logger):
    info_handler: logging.StreamHandler

    @staticmethod
    def all_log_levels(min_level=logging.CRITICAL):
        return LogAllLevelsContextManager(min_level)

    @staticmethod
    def silence():
        return SilenceContextManager()

    @staticmethod
    def at_level(logger, level):
        return LogLevelContextManager(logger, level)

    @staticmethod
    def info_to_stdout(logger=None):
        h1 = logging.StreamHandler(sys.stdout)
        f1 = SingleLevelFilter(logging.INFO, False)
        h1.addFilter(f1)
        logger.addHandler(h1)


def log(name) -> CustomLogger:
    """
    Simple stream-logger that can also be used as a context manager.
    Be aware of the hacky adding of methods to existing logger,
    but overriding return type to get correct inspection in IDEs
    """
    logger = logging.getLogger(name)

    # Hacks since current versions of pytest doesn't allow subclassing
    # of logging.getLogger
    setattr(logger, "all_log_levels", CustomLogger.all_log_levels)
    setattr(logger, "silence", CustomLogger.silence)

    def _info_to_stdout():
        return CustomLogger.info_to_stdout(logger)

    setattr(logger, "info_to_stdout", _info_to_stdout)

    def at_level(level):
        return CustomLogger.at_level(logger, level)

    setattr(logger, "at_level", at_level)

    # end of pytest-hacks
    console_handler = logging.StreamHandler()
    logger.info_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s-%(levelname)s:%(name)s.%(funcName)s: %(message)s", "%H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    # pytests currently doesn't work with non-propagating logs, so keeping default value at 1; for places where this is
    # undesirable (maya would get double output in script-editor), this can be changed before creating new loggers
    logger.propagate = PROPAGATE
    logger.handlers = [console_handler]

    return logger  # noqa
