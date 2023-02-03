"""Widgets for saving, loading and editing animation files"""
import os
import tarfile
import tempfile

from PySide2 import QtCore
import src.serial_animator.animation_io as animation_io
from src.serial_animator.ui.utils import get_maya_main_window
from src.serial_animator.ui.file_view import (
    FileLibraryView,
    FileWidgetHolderBase,
    FilePreviewWidgetBase,
)
from src.serial_animator.ui.view_grabber import AnimationViewGrabber

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class AnimationWidget(FilePreviewWidgetBase):
    """Previews animation and loads it from a file on disk"""

    def __init__(self, path):
        super(AnimationWidget, self).__init__(path)
        self.meta_data = animation_io.extract_meta_data(self.path)
        self.frame_rate = self.get_framerate()
        self.start_frame = self.get_start_frame()
        self.frame = self.start_frame
        self.end_frame = self.get_end_frame()
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self.change_image)
        self._hover = False
        self.start_img = None

    def get_start_frame(self) -> int:
        return int(self.meta_data.get("frame_range")[0])

    def get_end_frame(self) -> int:
        return int(self.meta_data.get("frame_range")[1])

    def get_framerate(self) -> float:
        return float(self.meta_data.get("time_unit"))

    def change_image(self):
        """
        If mouse is not over widget, set start-image. If the mouse is
        over, loop animation by setting tmp image based on current frame
        """
        # set preview-image if we are not hovering
        if self._hover is False:
            self.set_start_image()
            return
        # reset animation if we are at the last frame, else move to next
        # frame
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
        """
        if self._anim_timer.isActive():
            return
        self._anim_timer.setInterval(1000 / self.frame_rate)
        self._anim_timer.start()

    def enterEvent(self, event):
        """
        Opens archive, sets hover and starts animation of image-sequence
        """
        self._hover = True
        self.start_anim()

    def leaveEvent(self, event):
        """
        Stops animation of image-sequence, and sets start-image
        """
        self._hover = False
        self._anim_timer.stop()
        self.set_start_image()

    def set_temp_image(self, preview_image_name):
        """
        Opens archive and tries to extract preview_image_name to a
        temporary location and sets it as widget image. Deletes tmp-file
        """
        try:
            with tarfile.open(self.path) as tf:
                img_file = tf.extractfile(preview_image_name)
                with tempfile.NamedTemporaryFile(
                        prefix="Serial_animator", suffix=".png", delete=False
                ) as img:
                    img.write(img_file.read())
                    tmp_file_name = img.name
                self.set_image(tmp_file_name)
            # couldn't get it to work with a temp-file that deletes
            # itself, so manually doing it here
            os.remove(tmp_file_name)
        except KeyError:
            pass

    def mouseDoubleClickEvent(self, event):
        self.load_animation()

    def load_animation(self):
        nodes = animation_io.get_nodes()
        animation_io.load_animation(self.path, nodes)


class AnimationWidgetHolder(FileWidgetHolderBase):
    """
    Displays Animations-files in a folder. This is the widget holding
    multiple widgets representing files
    """

    FileType = "anim"
    DataWidgetClass = AnimationWidget

    def __init__(self, path):
        super(AnimationWidgetHolder, self).__init__(path)


class SerialAnimatorView(FileLibraryView):
    """
    Main UI for saving loading and previewing animations in library
    """

    FileType = "anim"
    ImageGrabber = AnimationViewGrabber
    DataHolderWidget = AnimationWidgetHolder

    def __init__(self, parent=None):
        super(SerialAnimatorView, self).__init__(parent)
        self.save_grp.setTitle("Save Animation")
        self.save_line_edit.setPlaceholderText("Animation Name")
        self.load_grp.setTitle("Load Animation")
        self.setWindowTitle("Animation Library")

    def grab_preview(self, out_dir) -> AnimationViewGrabber:
        """Opens a preview viewport and grabs image-sequence from it"""
        img_path = os.path.join(out_dir, "preview")
        start, end = animation_io.get_frame_range()
        grabber_window = self.ImageGrabber(img_path, start_frame=start, end_frame=end)
        return grabber_window

    def save_data(self, img_path):
        out_path = self.get_out_path()
        preview_dir = os.path.dirname(img_path)
        animation_io.save_animation_from_selection(out_path, preview_dir)


__VIEW = None


def main(parent=get_maya_main_window()):
    global __VIEW
    __VIEW = SerialAnimatorView(parent=parent)
    __VIEW.show()


if __name__ == "__main__":
    main()
