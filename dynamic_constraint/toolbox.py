
import os
import sys
from PySide2 import QtWidgets, QtCore, QtGui
from .dynamic_constraint import DYNAMIC_CONTRAINT_TYPES, list_dynamic_constraints


class DynamicConstraintView(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(DynamicConstraintView, self).__init__(parent)
        self.initUI()

    def initUI(self):

        self._dynamic_constraint_table_view = DynamicConstraintTableView()
        self._dynamic_constraint_table_model = DynamicConstraintTableModel()
        self._dynamic_constraint_table_view.set_model(
            self._dynamic_constraint_table_model)
        self._dynamic_constraint_item_delegate = DynamicConstraintDelegate(
            self._dynamic_constraint_table_view)
        self._dynamic_constraint_table_view.set_item_delegate(
            self._dynamic_constraint_item_delegate)

        self._create_constraint_button = QtWidgets.QPushButton()
        self._create_constraint_button.setText('Create dynamic constraint')

        self._refresh = QtWidgets.QPushButton('Refresh')
        self._refresh.clicked.connect(self.update_dynamic_constraints)

        self._buttons_layout = QtWidgets.QHBoxLayout()
        self._buttons_layout.addWidget(self._create_constraint_button)
        self._buttons_layout.addWidget(self._refresh)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.addWidget(self._dynamic_constraint_table_view)
        self._layout.addLayout(self._buttons_layout)

        self.update_dynamic_constraints()

    def update_dynamic_constraints(self):
        self._dynamic_constraint_table_model.set_dynamic_constraints(
            list_dynamic_constraints())


class DynamicConstraintDelegate(QtWidgets.QAbstractItemDelegate):
    SELECT_MEMBERS_ICON = None
    ADD_MEMBERS_ICON = None
    REMOVE_MEMBERS_ICON = None
    PAINT_ICON = None
    RENAME_ICON = None

    def __init__(self, table):
        super(DynamicConstraintDelegate, self).__init__(table)
        self.model = table.model()
        self._generate_icons()

    def paint(self, painter, option, index):
        row, column = index.row(), index.column()
        style = QtWidgets.QApplication.style()
        dynamic_constraint = self.model.data(index, QtCore.Qt.UserRole)

        if column == 0:
            brush = QtGui.QBrush(QtGui.QColor(*dynamic_constraint.color))
            pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
            painter.setBrush(brush)
            painter.setPen(pen)
            rect = QtCore.QRect(
                option.rect.center().x() - 7, option.rect.center().y() - 7,
                14, 14)
            painter.drawRect(rect)
            return

        if column == 1:
            opt = QtWidgets.QStyleOptionButton()
            opt.rect = option.rect
            opt.text = dynamic_constraint.nice_name
            opt.textVisible = True
            state = QtWidgets.QStyle.State_Enabled
            if dynamic_constraint.enable:
                state |= QtWidgets.QStyle.State_On
            else:
                state = QtWidgets.QStyle.State_Off
            opt.state = state
            if not dynamic_constraint.is_well_named:
                opt.palette.setColor(
                    QtGui.QPalette.WindowText, QtGui.QColor('red'))
            style.drawControl(QtWidgets.QStyle.CE_CheckBox, opt, painter)
            return

        elif column == 2:
            point = QtCore.QPoint(
                option.rect.left() + 5,
                (option.rect.height() / 2 + option.rect.top() + 3))
            text = dynamic_constraint.type_name
            painter.setPen(QtGui.QPalette().color(QtGui.QPalette.WindowText))
            painter.drawText(point, text)
            return

        # draw buttons
        icon = QtGui.QIcon()
        if column == 3:
            icon = self.SELECT_MEMBERS_ICON
        elif column == 4:
            icon = self.ADD_MEMBERS_ICON
        elif column == 5:
            icon = self.REMOVE_MEMBERS_ICON
        elif column == 6:
            icon = self.PAINT_ICON
        elif column == 7:
            icon = self.RENAME_ICON

        opt = QtWidgets.QStyleOptionButton()
        opt.rect = option.rect
        style.drawControl(QtWidgets.QStyle.CE_PushButton, opt, painter)
        rect = QtCore.QRect(
            option.rect.center().x() - 8, option.rect.center().y() - 8, 16, 16)
        painter.drawPixmap(rect, icon.pixmap(16, 16))
        return

    def createEditor(self, parent, option, index):
        row, column = index.row(), index.column()
        dynamic_constraint = self.model.data(index, QtCore.Qt.UserRole)
        if column == 1:
            editor = QtWidgets.QCheckBox(parent)
            editor.stateChanged.connect(dynamic_constraint.switch)
            return editor

        if column == 2:
            editor = QtWidgets.QComboBox(parent)
            editor.addItems([d['name'] for d in DYNAMIC_CONTRAINT_TYPES])

            editor.setCurrentIndex(dynamic_constraint.type)
            editor.currentIndexChanged.connect(dynamic_constraint.set_type)
            return editor

        elif column == 3:
            editor = QtWidgets.QPushButton(
                self.SELECT_MEMBERS_ICON, '', parent)
            return editor

        elif column == 4:
            editor = QtWidgets.QPushButton(self.ADD_MEMBERS_ICON, '', parent)

            return editor

        elif column == 5:
            editor = QtWidgets.QPushButton(
                self.REMOVE_MEMBERS_ICON, '', parent)
            return editor

        elif column == 6:
            editor = QtWidgets.QPushButton(self.PAINT_ICON, '', parent)
            editor.clicked.connect(
                dynamic_constraint.paint_constraint_strength_map_on_components)
            return editor

        elif column == 7:
            editor = QtWidgets.QPushButton(self.RENAME_ICON, '', parent)
            return editor

    def setEditorData(self, editor, index):
        row, column = index.row(), index.column()
        dynamic_constraint = self.model.data(index, QtCore.Qt.UserRole)

        if column == 3:
            return dynamic_constraint.select_members()

        elif column == 4:
            return dynamic_constraint.add_selection_to_members()

        elif column == 5:
            return dynamic_constraint.remove_selection_to_members()

        elif column == 6:
            return dynamic_constraint.paint_constraint_strength_map_on_components()

        elif column == 7:
            return dynamic_constraint.rename_node_from_components()

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def sizeHint(self, option, index):
        col = index.column()
        if col == 1:
            return QtCore.QSize(300, 15)
        elif col == 2:
            return QtCore.QSize(120, 15)
        else:
            return QtCore.QSize(15, 15)

    def _generate_icons(self):
        # iconpath = os.path.join(
        #     os.path.dirname(os.path.realpath(__file__)), 'icons')
        # temporary hardoded path for testgithub
        iconpath = r"D:\EclipseWorkspaces\csse120\myPyRessource\GitHub\maya_libs\dynamic_constraint\icons"

        if not self.ADD_MEMBERS_ICON:
            self.ADD_MEMBERS_ICON = QtGui.QIcon(
                os.path.join(iconpath, 'add_members.png'))

        if not self.SELECT_MEMBERS_ICON:
            self.SELECT_MEMBERS_ICON = QtGui.QIcon(
                os.path.join(iconpath, 'select_members.png'))

        if not self.REMOVE_MEMBERS_ICON:
            self.REMOVE_MEMBERS_ICON = QtGui.QIcon(
                os.path.join(iconpath, 'remove_members.png'))

        if not self.PAINT_ICON:
            self.PAINT_ICON = QtGui.QIcon(
                os.path.join(iconpath, 'paint.png'))
            print(os.path.join(iconpath, 'paint.png'))

        if not self.RENAME_ICON:
            self.RENAME_ICON = QtGui.QIcon(
                os.path.join(iconpath, 'rename.png'))


class DynamicConstraintTableModel(QtCore.QAbstractTableModel):
    HEADERS = ['', 'name', 'type', '', '', '', '', '']

    def __init__(self, parent=None):
        super(DynamicConstraintTableModel, self).__init__(parent)
        self._dynamic_constraints = []

    def rowCount(self, index):
        return len(self._dynamic_constraints)

    def columnCount(self, index):
        return 8

    def data(self, index, role):
        if role == QtCore.Qt.UserRole:
            return self._dynamic_constraints[index.row()]

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled

    def set_dynamic_constraints(self, dynamic_constraints):
        self.layoutAboutToBeChanged.emit()
        self._dynamic_constraints = dynamic_constraints
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Vertical:
            return super(DynamicConstraintTableModel, self).headerData(
                section, orientation, role)

        if role == QtCore.Qt.DisplayRole:
            return self.HEADERS[section]


class DynamicConstraintTableView(QtWidgets.QTableView):

    def __init__(self, parent=None):
        super(DynamicConstraintTableView, self).__init__(parent)
        self.configure()

    def configure(self):
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
        self.viewport().installEventFilter(self)

    def set_model(self, model):
        self.setModel(model)

    def set_item_delegate(self, item_delegate):
        self.setItemDelegate(item_delegate)
