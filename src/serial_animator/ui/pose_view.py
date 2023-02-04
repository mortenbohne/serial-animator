from PySide2 import QtCore, QtGui

from serial_animator.utils import Undo
import serial_animator.pose_io as pose_io
from serial_animator.ui.utils import get_maya_main_window
from serial_animator.ui.file_view import (
    FileLibraryView,
    FilePreviewWidgetBase,
    FileWidgetHolderBase,
)
from serial_animator.ui.view_grabber import GeometryViewGrabber

import logging

_logger = logging.getLogger(__name__)


class PoseWidget(FilePreviewWidgetBase):
    def __init__(self, path):
        super(PoseWidget, self).__init__(path)
        self.mouse_start = QtCore.QPoint()
        self.start_pose = None
        self.target_pose = None
        self.nodes = None

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.buttons() == QtCore.Qt.MiddleButton:
            pose_io.start_undo()
            self.mouse_start = ev.globalPos()
            self.nodes = pose_io.get_nodes()
            self.start_pose = pose_io.get_data_from_nodes(self.nodes)
        super(PoseWidget, self).mousePressEvent(ev)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.buttons() == QtCore.Qt.MiddleButton:
            delta = ev.globalPos() - self.mouse_start
            weight = delta.x() * 0.01
            if 0 < weight < 1:
                self.apply_pose(weight=weight)
            ev.accept()
        super(PoseWidget, self).mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        pose_io.end_undo()
        super(PoseWidget, self).mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, event):
        self.apply_full_pose()

    @Undo()
    def apply_full_pose(self):
        self.start_pose = dict()
        self.apply_pose(1)

    def apply_pose(self, weight):
        if not self.nodes:
            self.nodes = pose_io.get_nodes()
        if not self.target_pose:
            self.target_pose = pose_io.read_pose_data_to_nodes(self.path, self.nodes)
        pose_io.interpolate(
            target=self.target_pose, origin=self.start_pose, weight=weight
        )
        pose_io.refresh_viewport()


class PoseWidgetHolder(FileWidgetHolderBase):
    FileType = pose_io.get_pose_filetype()
    DataWidgetClass = PoseWidget

    def __init__(self, path):
        super(PoseWidgetHolder, self).__init__(path)


class PoseLibraryView(FileLibraryView):
    """UI for editing poses"""

    FileType = pose_io.get_pose_filetype()
    ImageGrabber = GeometryViewGrabber
    DataHolderWidget = PoseWidgetHolder

    def __init__(self, parent=None):
        super(PoseLibraryView, self).__init__(parent)
        self.save_grp.setTitle("Save Pose")
        self.save_line_edit.setPlaceholderText("Pose Name")
        self.load_grp.setTitle("Load Pose")
        self.setWindowTitle("Pose Library")

    def save_clicked(self):
        if not self.save_line_edit.text():
            _logger.warning("Please name the pose before saving")
            return
        if not pose_io.get_nodes():
            _logger.warning("Please select controls to save pose from")
            return
        super(PoseLibraryView, self).save_clicked()

    def save_data(self, img_path):
        out_path = self.get_out_path()
        pose_io.save_pose_from_selection(out_path, img_path)
        self.tab_widget.currentWidget().update_widget_from_path(out_path)
        _logger.debug(img_path)


__VIEW = None


def main(parent=get_maya_main_window()):
    global __VIEW
    __VIEW = PoseLibraryView(parent=parent)
    __VIEW.show()


if __name__ == "__main__":
    main()
