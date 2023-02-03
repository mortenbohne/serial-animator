class SerialAnimatorError(RuntimeError):
    def __init__(self, message=""):
        super(SerialAnimatorError, self).__init__(message)


class SerialAnimatorSceneNotSavedError(SerialAnimatorError):
    """Error when getting scene name but the scene isn't saved"""

    def __init__(self, message="Scene isn't saved"):
        super(SerialAnimatorSceneNotSavedError, self).__init__(message)
