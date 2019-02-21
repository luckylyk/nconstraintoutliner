from PySide2 import QtWidgets, QtGui, QtCore
from qtutils import get_icon


class OnOffLabel(QtWidgets.QWidget):
    """
    / | \  on/off switch icon for delegate
    \___/
    """
    ICONSIZE = 22, 22

    def __init__(self, dynamic_node, parent=None):
        super(OnOffLabel, self).__init__(parent)

        self.icons = get_icon(dynamic_node.on), get_icon(dynamic_node.off)
        self.dynamic_node = dynamic_node
        self.setFixedSize(24, 24)
        self.repaint()

    def mousePressEvent(self, _):
        self.dynamic_node.switch()
        self.repaint()

    def paintEvent(self, _):
        painter = QtGui.QPainter()
        icon = self.icon[bool(self.dynamic_node.enable)]
        pixmap = icon.pixmap(32, 32).scaled(
            QtCore.QSize(*self.ICONSIZE),
            transformMode=QtCore.Qt.SmoothTransformation)
        painter.drawPixmap(self.rect(), pixmap))


def DynamicNodesTableModel(QtCore.QAbstractTableModel):
    HEADERS = "", "Node", "Cache"

    def __init__(self, parent=None):
        super(DynamicNodesTableModel, self).__init__(parent)
        self.nodes = []

    def columnCount(self, _):
        return len(self.HEADERS)

    def rowCount(self, _):
        return len(self.nodes)

    def set_nodes(self, nodes):
        self.layoutAboutToBeChanged()
        self.nodes = nodes
        self.layoutChanged()

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.Display:
            return

        if orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]

    def data(self, index, role):
        if not index.isValid():
            return
        row, column = index.row(), index.column()

        if role == QtCore.Qt.DisplayRole:
            if column == 1:
                return self.nodes[row].name