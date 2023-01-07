from PySide2 import QtWidgets, QtGui
import logging
from serial_animator.ui.flowlayout import FlowLayout

_logger = logging.getLogger(__name__)

try:
    from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

    _logger.debug("Using Maya Mixins as base widgets")


    class WidgetBase(QtWidgets.QWidget, MayaQWidgetBaseMixin):
        pass


    class DialogBase(QtWidgets.QDialog, MayaQWidgetBaseMixin):
        pass

except ImportError:
    _logger.debug("Using QtWidget/QDialog as base widgets")

    WidgetBase = QtWidgets.QWidget
    DialogBase = QtWidgets.QDialog


class MayaWidget(WidgetBase):
    """Base Class for Maya widgets"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)


class ScrollContainer(QtWidgets.QWidget):
    """
    A container-widget that adds a scroll-area
    """

    def __init__(self):
        super(ScrollContainer, self).__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(QtGui.Qt.NoFocus)
        # self.scroll_area.setHorizontalScrollBarPolicy(
        #     QtGui.Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.scroll_area)


class ScrollFlowWidget(ScrollContainer):
    def __init__(self):
        super(ScrollFlowWidget, self).__init__()
        widget = QtWidgets.QWidget()
        self.scroll_area.setWidget(widget)
        self.flow_layout = FlowLayout()
        # self.flow_layout = QtWidgets.QVBoxLayout()
        widget.setLayout(self.flow_layout)
