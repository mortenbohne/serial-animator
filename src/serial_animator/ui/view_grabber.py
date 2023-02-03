import uuid
from PySide2 import QtWidgets, QtCore
import logging
import pymel.core as pm
from src.serial_animator.ui.utils import get_maya_main_window

_logger = logging.getLogger(__name__)
_logger.setLevel("DEBUG")


def get_current_camera() -> pm.nodetypes.Transform:
    current_viewport_name = pm.playblast(activeEditor=True).split("|")[-1]
    current_camera = pm.modelPanel(current_viewport_name, query=True, camera=True)
    cam = pm.PyNode(current_camera)
    return cam


def unlock_cam_attributes(camera):
    for a in ["translate", "rotate", "scale"]:
        for ax in ["X", "Y", "Z"]:
            attr = camera.attr("{}{}".format(a, ax))
            if attr.isLocked():
                attr.unlock()


class TmpViewport(QtWidgets.QWidget):
    snap_taken = QtCore.Signal(str)

    def __init__(self, out_path, parent=get_maya_main_window()):
        _logger.debug("opening tmp viewport")
        super(TmpViewport, self).__init__(parent=parent)
        self.out_path = out_path
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowModality(QtCore.Qt.WindowModal)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.setObjectName(
            "serial_animator_tmp_image_grabber_{}".format(uuid.uuid4().hex)
        )

        self.cam = pm.duplicate(get_current_camera())[0]
        self.cam.hiddenInOutliner.set(True)
        unlock_cam_attributes(self.cam)
        self.model_panel = pm.modelPanel(
            "embeddedModelPanel#", cam=self.cam.longName(), parent=layout.objectName()
        )
        pm.setFocus(self.model_panel)
        pm.modelEditor(self.model_panel, edit=True, activeView=True)
        self.set_viewport_options()
        self.capture_button = QtWidgets.QPushButton("Capture")
        layout.addWidget(self.capture_button)
        self.capture_button.clicked.connect(self.capture)
        self.setFixedSize(500, 540)
        pm.viewFit(self.cam.nodeName())
        self.setFocus()
        self.setWindowTitle("Take Snapshot")
        self.show()

    def set_viewport_options(self):
        pm.modelEditor(
            self.model_panel,
            edit=True,
            headsUpDisplay=False,
            grid=False,
            manipulators=False,
            selectionHiliteDisplay=False,
            displayTextures=True,
            displayAppearance="smoothShaded",
        )

    def capture(self):
        pm.setFocus(self.model_panel)
        pm.refresh(
            currentView=True,
            filename=self.out_path,
            force=True,
        )
        self.snap_taken.emit(self.out_path)
        self.close()

    def closeEvent(self, event):
        pm.isolateSelect(self.model_panel, state=0)
        pm.deleteUI(self.model_panel)
        if pm.objExists(self.cam):
            pm.delete(self.cam)
        super(TmpViewport, self).closeEvent(event)

    def keyPressEvent(self, event):

        if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            self.capture()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.close()
        super(TmpViewport, self).keyPressEvent(event)


class GeometryViewGrabber(TmpViewport):
    """Displays geometry"""

    def set_viewport_options(self):
        super(GeometryViewGrabber, self).set_viewport_options()
        pm.modelEditor(
            self.model_panel,
            edit=True,
            nurbsCurves=False,
            joints=False,
            cameras=False,
            follicles=False,
            greasePencils=True,
            handles=False,
            ikHandles=False,
            imagePlane=False,
            locators=False,
            motionTrails=False,
        )


class GeometryCurveViewGrabber(TmpViewport):
    """Displays geometry and nurbs curves"""

    def set_viewport_options(self):
        super(GeometryCurveViewGrabber, self).set_viewport_options()
        pm.modelEditor(
            self.model_panel,
            edit=True,
            nurbsCurves=True,
            joints=False,
            cameras=False,
            follicles=False,
            greasePencils=True,
            handles=False,
            ikHandles=False,
            imagePlane=False,
            locators=False,
            motionTrails=False,
        )


class AnimationViewGrabber(GeometryViewGrabber):
    def __init__(self, *args, start_frame=0, end_frame=10, step=1, **kwargs):
        """Captures a frame-range as a .jpg sequence"""
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.step = step
        super().__init__(*args, **kwargs)

    def capture(self):
        pm.setFocus(self.model_panel)
        frames = range(self.start_frame, self.end_frame, self.step)
        pm.playblast(
            filename=self.out_path,
            frame=frames,
            compression="jpg",
            clearCache=True,
            format="image",
            offScreen=True,
            rawFrameNumbers=True,
            showOrnaments=False,
            viewer=False,
        )
        self.snap_taken.emit(self.out_path)
        self.close()
