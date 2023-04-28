import functools
import pymel.core as pm


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
