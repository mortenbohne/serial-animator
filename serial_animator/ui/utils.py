import shiboken2
from PySide2 import QtWidgets
import maya.OpenMayaUI


def get_maya_main_window():
    ptr = maya.OpenMayaUI.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)
