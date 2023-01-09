import pymel.core as pm


def get_maya_main_window():
    return pm.uitypes.toPySideControl(pm.MelGlobals.get("gMainWindow"))
