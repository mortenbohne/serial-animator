import os
from pathlib import Path
import sys
from typing import Generator, List
import subprocess
import tempfile
import logging
import uuid

from PySide2 import QtWidgets, QtCore, QtGui

from serial_animator.utils import get_user_preference_dir, setup_scene_opened_callback
import serial_animator.file_io
import serial_animator.scene_paths as scene_paths
from serial_animator.ui.widgets import MayaWidget, ScrollFlowWidget
from serial_animator.ui.view_grabber import TmpViewport

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class FilePreviewWidgetBase(QtWidgets.QLabel):
    """Widget displaying an image extracted from archive from path"""

    def __init__(self, path: Path):
        super(FilePreviewWidgetBase, self).__init__()
        self.path = path
        self.setText(str(self.path))
        self.set_start_image()
        self.setToolTip(str(self.path))
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def mouseDoubleClickEvent(self, event):
        super(FilePreviewWidgetBase, self).mouseDoubleClickEvent(event)
        self.load_data()

    def on_context_menu(self, pos):
        context = QtWidgets.QMenu()
        delete_action = QtWidgets.QAction("Delete", self)
        delete_action.triggered.connect(self.delete)
        open_location_action = QtWidgets.QAction("Open in Explorer", self)
        open_location_action.triggered.connect(self.show_in_os)
        context.addAction(open_location_action)
        context.addAction(delete_action)
        context.exec_(self.mapToGlobal(pos))

    def show_in_os(self):
        show_in_os(self.path)

    def delete(self):
        try:
            os.remove(self.path)
        except (IOError, WindowsError):
            if not os.access(self.path, os.W_OK):
                _logger.critical(f"Couldn't delete locked file: {self.path}")
                return
            else:
                raise

    def load_data(self):
        raise NotImplementedError

    def set_start_image(self):
        """
        Extracts the start-image from archive, and sets it as pix-map
        """
        with tempfile.TemporaryDirectory(prefix="serial_animator_") as tmp_dir:
            img_path = self.get_preview_image_path(self.path, Path(tmp_dir))
            self.set_image(str(img_path))

    def set_image(self, img_path: str):
        pix = QtGui.QPixmap()
        if os.path.isfile(img_path):
            pix.load(img_path)
            pix = pix.scaled(250, 250, QtCore.Qt.KeepAspectRatio)
        self.setPixmap(pix)

    @staticmethod
    def get_preview_image_path(path, directory) -> Path:
        return serial_animator.file_io.extract_file_from_archive(path, directory)


class FileWidgetHolderBase(QtWidgets.QWidget):
    """
    A Widget holding Data-widgets in a flow-layout based on files in
    a specified path
    """

    FileType: str
    DataWidgetClass = FilePreviewWidgetBase

    def __init__(self, path: Path):
        super(FileWidgetHolderBase, self).__init__()
        self.path = path
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        scroll = ScrollFlowWidget()
        self.layout.addWidget(scroll)
        self.data_widget_layout = scroll.flow_layout
        self.path_label = QtWidgets.QLabel(str(path))
        self.path_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.data_widgets = list()
        self.update_content()
        self.setToolTip(str(self.path))
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, pos):
        context = QtWidgets.QMenu()
        open_location_action = QtWidgets.QAction("Open in Explorer", self)
        open_location_action.triggered.connect(self.show_in_os)
        context.addAction(open_location_action)
        context.exec_(self.mapToGlobal(pos))

    def show_in_os(self):
        show_in_os(self.path)

    def get_files(self) -> Generator[Path, None, None]:
        for f in self.path.iterdir():
            if str(f).endswith(f".{self.FileType}"):
                yield f

    def update_content(self):
        self.clear_widgets()
        if self.path.is_dir():
            for f in self.get_files():
                w = self.create_data_widget(f)
                self.data_widgets.append(w)
                self.data_widget_layout.addWidget(w)
        if not self.data_widgets:
            self.data_widget_layout.addWidget(self.path_label)
            self.data_widgets.append(self.path_label)

    def create_data_widget(self, path: Path) -> FilePreviewWidgetBase:
        return self.DataWidgetClass(path)

    def clear_widgets(self):
        """
        Removes all data-widgets
        """
        for i in reversed(range(self.data_widget_layout.count())):
            item = self.data_widget_layout.itemAt(i).widget()
            self.data_widgets.pop(i)
            if item:
                item.setParent(None)

    def update_widget_from_path(self, path):
        # Couldn't get updating QPixmap to work, so for now clearing the content
        # for w in self.data_widgets:
        #     if w.path == path:
        #         _logger.debug(f"Updating widget based on {path}")
        #         return w.set_start_image()
        # _logger.debug("Updating all widgets")
        self.update_content()


class TabWidget(QtWidgets.QTabWidget):
    DataHolderWidget = FileWidgetHolderBase

    def __init__(
            self, parent, data_holder_class=None, locations_func=None, settings_path=None
    ):
        if data_holder_class:
            self.DataHolderWidget = data_holder_class
        if locations_func:
            self.get_asset_locations = locations_func
        super(TabWidget, self).__init__(parent)
        self.ui_settings_path = settings_path or self.get_ui_settings_path()
        self.ui_settings = QtCore.QSettings(
            self.ui_settings_path, QtCore.QSettings.IniFormat
        )
        self.file_watcher = QtCore.QFileSystemWatcher()
        self.file_watcher.directoryChanged.connect(self.dir_changed)
        self.setObjectName(f"SerialAnimator_TabWidget_{uuid.uuid4().hex}")
        self._callback_id = setup_scene_opened_callback(
            self.reload_tabs, parent=self.objectName()
        )
        self.add_tabs()

    @staticmethod
    def get_asset_locations():
        raise NotImplementedError

    def add_tabs(self):
        for _, p in enumerate(self.get_asset_locations()):
            name = p.name
            tab = self.add_tab(p)
            self.file_watcher.addPath(str(p))
            self.addTab(tab, name)
        self.set_current_tab_from_settings()

    def set_current_tab_from_settings(self):
        setting = self.ui_settings.value("tab_index") or 0
        tab_index = int(setting)  # noqa
        if tab_index < self.count():
            self.setCurrentIndex(tab_index)

    def save_current_tab_to_settings(self):
        self.ui_settings.setValue("tab_index", self.currentIndex())

    def add_tab(self, path) -> FileWidgetHolderBase:
        return self.DataHolderWidget(path=path)

    def dir_changed(self, path):
        tab_dict = dict()

        tabs = [self.widget(i) for i in range(self.count())]
        for tab in tabs:
            tab_dict[tab.path] = tab
        tab = tab_dict.get(path)
        if tab:
            tab.update_content()

    def reload_tabs(self):
        self.clear()
        self.add_tabs()

    @classmethod
    def get_ui_settings_path(cls) -> str:
        """Gets path for ui settings-file"""
        name = cls.__name__
        return os.path.join(get_user_preference_dir(), f"SerialAnimator_{name}.ini")

    def closeEvent(self, event) -> None:
        self.save_current_tab_to_settings()


class FileLibraryView(MayaWidget):
    """Base UI for saving, loading and editing data archived with a preview image"""

    FileType = "tar"
    ImageGrabber = TmpViewport
    DataHolderWidget = FileWidgetHolderBase

    def __init__(self, parent=None):
        super(FileLibraryView, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.top_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(self.top_layout)
        self.save_grp = QtWidgets.QGroupBox()
        self.save_grp.setTitle("Save")
        self.top_layout.addWidget(self.save_grp)
        self.save_layout = QtWidgets.QVBoxLayout()
        self.save_grp.setLayout(self.save_layout)
        self.save_line_edit = QtWidgets.QLineEdit()
        self.save_line_edit.setPlaceholderText("Asset Name")
        regex = QtCore.QRegExp("[\w\-]+")
        validator = QtGui.QRegExpValidator(regex, self)
        self.save_line_edit.setValidator(validator)
        self.save_layout.addWidget(self.save_line_edit)
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save_clicked)

        self.load_grp = QtWidgets.QGroupBox()
        self.main_layout.addWidget(self.load_grp)
        self.load_grp.setTitle("Load Asset")
        self.load_layout = QtWidgets.QVBoxLayout()
        self.load_grp.setLayout(self.load_layout)
        self.tab_widget = TabWidget(
            parent=self,
            data_holder_class=self.DataHolderWidget,
            locations_func=self.get_asset_locations,
            settings_path=self.get_ui_settings_path(),
        )
        self.load_layout.addWidget(self.tab_widget)

        self.setWindowTitle("FileLibraryBase")
        self.ui_settings = QtCore.QSettings(
            self.get_ui_settings_path(), QtCore.QSettings.IniFormat
        )
        self.apply_settings()

    def apply_settings(self):
        self.restoreGeometry(self.ui_settings.value("geometry"))

    @staticmethod
    def get_asset_locations() -> List[Path]:
        """Gets location of assets displayed in tabs"""
        locations = list()

        locations.append(scene_paths.get_shared_lib_path())
        locations.append(scene_paths.get_user_lib_path())
        scene_path = scene_paths.get_current_scene_lib_path()
        if scene_path:
            locations.append(scene_path)
        return locations

    def dockCloseEventTriggered(self):
        self._close()
        super(FileLibraryView, self).dockCloseEventTriggered()

    def closeEvent(self, event):
        self._close()
        super(FileLibraryView, self).closeEvent(event)

    def _close(self):
        """
        In current version of maya the closeEvent of dock widgets
        doesn't seem to get triggered, but the dockCloseEventTriggered
        works, extracting functionality and running it from both as it
        seems to change between every version
        :return:
        """
        self.ui_settings.setValue("geometry", self.saveGeometry())
        self.tab_widget.save_current_tab_to_settings()

    def save_clicked(self):
        """
        Opens capture-viewport and connects it's snap-taken signal to
        save_data
        """
        with tempfile.TemporaryDirectory(prefix="serial_animator_") as tmp_dir:
            grabber_window = self.grab_preview(Path(tmp_dir))
            grabber_window.snap_taken.connect(self.save_data)

    def grab_preview(self, out_dir) -> TmpViewport:
        img_path = Path(out_dir) / "preview.jpg"
        grabber_window = self.ImageGrabber(img_path)
        return grabber_window

    def save_data(self, img_path):
        raise NotImplementedError

    def get_out_path(self) -> Path:
        file_name = f"{self.save_line_edit.text()}.{self.FileType}"
        current_tab_path = self.tab_widget.currentWidget().path
        return Path(current_tab_path) / file_name

    @classmethod
    def get_ui_settings_path(cls) -> str:
        """Gets path for ui settings-file"""
        return os.path.join(
            get_user_preference_dir(), f"SerialAnimator_{cls.__name__}.ini"
        )


def show_in_os(path):
    if sys.platform == "win32":
        subprocess.Popen(f"explorer /select, {path}")
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        os.system(f"xdg-open '{path}'")
