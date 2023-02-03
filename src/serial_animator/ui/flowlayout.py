"""
Backported from PySide6 examples at
https://doc.qt.io/qtforpython/examples/example_widgets_layouts_flowlayout.html

..note:: removed layout_spacing as it seemed to crash when running from Maya

"""
import sys
from PySide2 import QtWidgets, QtCore
import logging

_logger = logging.getLogger(__name__)


# _logger.setLevel("DEBUG")


class TestWindow(QtWidgets.QWidget):
    def __init__(self):
        super(TestWindow, self).__init__()

        flow_layout = FlowLayout(self)
        flow_layout.addWidget(QtWidgets.QPushButton("Short"))
        flow_layout.addWidget(QtWidgets.QPushButton("Longer"))
        flow_layout.addWidget(QtWidgets.QPushButton("Different text"))
        flow_layout.addWidget(QtWidgets.QPushButton("More text"))
        flow_layout.addWidget(QtWidgets.QPushButton("Even longer button text"))
        self.setWindowTitle("Flow Layout")


class FlowLayout(QtWidgets.QLayout):
    """Lays widgets out in a grid and rearranges when resized"""

    def __init__(self, parent=None):
        super(FlowLayout, self).__init__(parent)

        if parent is None:
            self.setContentsMargins(0, 0, 0, 0)

        self._item_list = list()

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(
            2 * self.contentsMargins().top(), 2 * self.contentsMargins().top()
        )
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()
        for item in self._item_list:
            # style = item.widget().style()
            layout_spacing_x = 1
            # layout_spacing_x = style.layoutSpacing(
            #     QtWidgets.QSizePolicy.PushButton,
            #     QtWidgets.QSizePolicy.PushButton,
            #     QtCore.Qt.Horizontal,
            # )
            layout_spacing_y = 1
            # layout_spacing_y = style.layoutSpacing(
            #     QtWidgets.QSizePolicy.PushButton,
            #     QtWidgets.QSizePolicy.PushButton,
            #     QtCore.Qt.Vertical,
            # )

            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_win = TestWindow()
    main_win.show()
