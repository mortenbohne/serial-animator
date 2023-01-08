import os
import tempfile

from PySide2 import QtGui, QtCore
import serial_animator.animation_io as animation_io
import serial_animator.file_io as file_io
from serial_animator.ui.utils import get_maya_main_window
from serial_animator.ui.file_view import (
    FileLibraryView,
    FileWidgetHolderBase,
    FilePreviewWidgetBase,
)
from serial_animator.ui.view_grabber import AnimationViewGrabber

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class AnimationWidget(FilePreviewWidgetBase):
    """Previews animation and loads it from a file on disk"""

    def __init__(self, path):
        super(AnimationWidget, self).__init__(path)
        self.setMouseTracking(True)
        self.meta_data = animation_io.extract_meta_data(self.path)
        _logger.debug(f"{self.meta_data=}")
        self.frame_rate = self.get_framerate()
        self.start_frame = self.get_start_frame()
        self.frame = self.start_frame
        self.end_frame = self.get_end_frame()
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self.change_image)
        self._hover = False
        self.start_img = None

    def get_start_frame(self):
        return int(self.meta_data.get("frame_range")[0])

    def get_end_frame(self):
        return int(self.meta_data.get("frame_range")[1])

    def get_framerate(self):
        return self.meta_data.get("time_unit")

    def change_image(self):
        # set preview-image if we are not hovering
        if self._hover is False:
            self.set_start_image()
            return
        # reset animation if we are at the last frame, else move to next frame
        if self.frame >= self.end_frame:
            self.frame = self.start_frame
        else:
            self.frame += 1
        # establish the file name of image file we are looking for in
        # tar-archive
        image_name = f"preview.{self.frame:04d}.jpg"
        self.set_temp_image(image_name)


    def start_anim(self):
        """
        Starts animation-timer with correct frame-rate
        :return:
        """
        if self._anim_timer.isActive():
            return
        self._anim_timer.setInterval(1000 / self.frame_rate)
        self._anim_timer.start()

    def enterEvent(self, event):
        """
        Opens archive, sets hover and starts animation of image-sequence
        :param event:
        :return:
        """
        self._hover = True
        self.start_anim()

    def leaveEvent(self, event):
        """
        Stops animation of image-sequence, and sets start-image if it exists
        :param event:
        """
        self._hover = False
        self._anim_timer.stop()
        self.set_start_image()

    def set_temp_image(self, preview_image_name):
        with tempfile.TemporaryDirectory(prefix="serial_animator_") as tmp_dir:
            file_io.extract_file_from_archive(self.path, tmp_dir, preview_image_name)
            img_path = self.get_preview_image_path(tmp_dir, preview_image_name)
            self.set_image(img_path)

    def mouseDoubleClickEvent(self, event):
        self.load_animation()

    def load_animation(self):
        nodes = animation_io.get_nodes()
        animation_io.load_animation(self.path, nodes)


class AnimationWidgetHolder(FileWidgetHolderBase):
    """Displays Animations-files in a folder"""

    FileType = "anim"
    DataWidgetClass = AnimationWidget

    def __init__(self, path):
        super(AnimationWidgetHolder, self).__init__(path)


class SerialAnimatorView(FileLibraryView):
    """UI for saving and previewing animations in library"""
    FileType = "anim"
    ImageGrabber = AnimationViewGrabber
    DataHolderWidget = AnimationWidgetHolder

    def __init__(self, parent=None):
        super(SerialAnimatorView, self).__init__(parent)
        self.save_grp.setTitle("Save Animation")
        self.save_line_edit.setPlaceholderText("Animation Name")
        self.load_grp.setTitle("Load Animation")
        self.setWindowTitle("Animation Library")

    def grab_preview(self, out_dir):
        img_path = os.path.join(out_dir, "preview")
        start, end = animation_io.get_frame_range()
        grabber_window = self.ImageGrabber(img_path, start_frame=start, end_frame=end)
        return grabber_window

    def save_data(self, img_path):
        out_path = self.get_out_path()
        _logger.debug(f"{out_path=}")
        preview_dir = os.path.dirname(img_path)
        animation_io.save_animation_from_selection(out_path, preview_dir)


__VIEW = None


def main(parent=get_maya_main_window()):
    global __VIEW
    __VIEW = SerialAnimatorView(parent=parent)
    __VIEW.show()


if __name__ == "__main__":
    main()
