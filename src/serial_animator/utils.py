import os
import sys
import functools
from pathlib import Path
import pymel.core as pm
import maya.OpenMaya as om


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


class ContextDecorator(object):
    """
    Boilerplate setup for making context-decorators
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __enter__(self):
        # Note: Returning self means that in "with ... as x", x will be self
        return self

    def __exit__(self, typ, val, traceback):
        pass

    def __call__(self, f):
        @functools.wraps(f)
        def wrapper(*args, **kw):
            """
            wrapper function
            """
            with self:
                return f(*args, **kw)

        return wrapper


def get_user_preference_dir() -> str:
    return pm.internalVar(userPrefDir=True)


def setup_scene_opened_callback(function, parent=None) -> int:
    """
    Sets up a callback when new scene is opened and returns scriptJob-id
    """
    if parent:
        return pm.scriptJob(parent=parent, event=["SceneOpened", function])
    else:
        return pm.scriptJob(event=["SceneOpened", function])


class Undo(ContextDecorator):
    """
    Undo function for maya that both works as decorator and
    context-manager

    with Undo(undoable=True, name="undoableStuff":
        my_function
    """

    def __init__(self, name="PythonAction", undoable=True, **kwargs):
        super(Undo, self).__init__(**kwargs)
        self.orig_state = pm.undoInfo(query=True, state=True)
        self.state = undoable
        self.name = name

    def __enter__(self):
        if self.state:
            pm.undoInfo(
                openChunk=True,
                chunkName=self.name,
                undoName=self.name,
                redoName=self.name,
            )
        else:
            pm.undoInfo(stateWithoutFlush=False)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.state:
            pm.undoInfo(closeChunk=True)
        else:
            pm.undoInfo(state=self.orig_state)


def is_interactive() -> bool:
    """Checking if maya is running with a GUI"""
    # would be lovely if om.MGlobal.mayaState() would show this as
    # expected...but running mayapy.exe returns the same as normal
    # gui mode (2023.2)
    try:
        if pm.about(batch=True):
            return False
    except AttributeError:
        return False
    return True


def reload_serial_animator():
    """
    Workaround to reload entire serial-animator library.
    Removes serial_animator modules from 'sys.modules' and imports it again
    """
    import sys
    import serial_animator

    src_folder = Path(serial_animator.__file__).parents[1]
    if src_folder not in sys.path:
        sys.path.append(str(src_folder.resolve()))
    for m in [p for p in sys.modules if p.startswith("serial_animator")]:
        sys.modules.pop(m)
    import serial_animator
