from PySide2 import QtWidgets
import pymel.core as pm


def get_maya_main_window() -> QtWidgets.QMainWindow:
    return pm.uitypes.toPySideControl(pm.MelGlobals.get("gMainWindow"))
