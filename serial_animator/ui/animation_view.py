from PySide2 import QtGui, QtCore
import serial_animator.animation_io as animation_io
from serial_animator.ui.utils import get_maya_main_window
from serial_animator.ui.file_view import (
    FileLibraryView,
    FileWidgetHolderBase,
    FilePreviewWidgetBase,
)
from serial_animator.ui.view_grabber import GeometryViewGrabber

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class AnimationWidget(FilePreviewWidgetBase):
    """Previews animation and loads it from a file on disk"""

    def __init__(self, path):
        super(AnimationWidget, self).__init__(path)
        self.setMouseTracking(True)

        self.frame_rate = self.get_framerate()
        self.start_frame = self.get_start_frame()
        self.frame = self.start_frame
        self.end_frame = self.get_end_frame()
        self._anim_timer = QtCore.QTimer()
        self._anim_timer.timeout.connect(self.change_image)
        self._hover = False
        self.start_img = None

    def get_start_frame(self):
        return 0

    def get_end_frame(self):
        return 60

    def get_framerate(self):
        return 30

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
        image_name = "{0}_{1:04d}.png".format('img', self.frame)

        # establish path to image extracted from archive to tmp-dir
        # img_path = os.path.join(self.image_seq_dir, image_name)
        _logger.debug(image_name)

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

    ImageGrabber = GeometryViewGrabber
    DataHolderWidget = AnimationWidgetHolder

    def __init__(self, parent=None):
        super(SerialAnimatorView, self).__init__(parent)
        self.save_grp.setTitle("Save Animation")
        self.save_line_edit.setPlaceholderText("Animation Name")
        self.load_grp.setTitle("Load Animation")
        self.setWindowTitle("Animation Library")


__VIEW = None


def main(parent=get_maya_main_window()):
    global __VIEW
    __VIEW = SerialAnimatorView(parent=parent)
    __VIEW.show()


if __name__ == "__main__":
    main()
