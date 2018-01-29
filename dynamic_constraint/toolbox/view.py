
from PySide2 import QtWidgets, QtCore
from table import DynamicConstraintTableView, DynamicConstraintTableModel, DynamicConstraintDelegate
from dynamic_constraint import list_dynamic_constraints


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


view = DynamicConstraintView()
view.show()
