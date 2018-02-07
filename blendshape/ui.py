
from PySide2 import QtWidgets, QtGui, QtCore
from .corrective import (
    create_working_copy_on_selection, delete_selected_working_copys,
    set_working_copys_transparency, apply_selected_working_copys,
    create_blendshape_corrective_for_selected_working_copys)

from maya_libs.qt.wrap_instance import get_main_maya_window_instance
undochunk = TODO


class CorrectiveBlendshapeWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CorrectiveBlendshapeWindow, self).__init__(
            parent, QtCore.Qt.Window)

        self._create_working_copy_button = QtWidgets.QPushButton(
            'Create Sculpt')
        self._create_working_copy_button.released.connect(
            self._call_create_working_copy)
        self._delete_working_copy_on_mesh_button = QtWidgets.QPushButton(
            'Cancel Sculpt')
        self._delete_working_copy_on_mesh_button.released.connect(
            self._call_delete_working_copy)

        self._create_delete_layout = QtWidgets.QHBoxLayout()
        self._create_delete_layout.setContentsMargins(0, 0, 0, 0)
        self._create_delete_layout.setSpacing(4)
        self._create_delete_layout.addWidget(self._create_working_copy_button)
        self._create_delete_layout.addWidget(
            self._delete_working_copy_on_mesh_button)

        self._display_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._display_slider.setRange(0, 100)
        self._display_slider.setValue(0)
        self._display_slider.valueChanged.connect(self._call_slider_changed)

        self._apply_button = QtWidgets.QPushButton('Apply')
        self._apply_button.released.connect(self._call_apply)
        self._apply_on_new_blendshape_button = QtWidgets.QPushButton(
            'Apply on new blendshape')
        self._apply_on_new_blendshape_button.released.connect(
            self._call_apply_on_new_blendshape)

        self._apply_layout = QtWidgets.QHBoxLayout()
        self._apply_layout.setContentsMargins(0, 0, 0, 0)
        self._apply_layout.setSpacing(4)
        self._apply_layout.addWidget(self._apply_button)
        self._apply_layout.addWidget(self._apply_on_new_blendshape_button)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.addLayout(self._create_delete_layout)
        self._layout.addWidget(self._display_slider)
        self._layout.addLayout(self._apply_layout)

        self._template_selecter = TemplateSelecterView()

    @undochunk
    def _call_create_working_copy(self):
        create_working_copy_on_selection()

    @undochunk
    def _call_delete_working_copy(self):
        delete_selected_working_copys()

    def _call_slider_changed(self, value):
        set_working_copys_transparency(value / 100.0)

    @undochunk
    def _call_apply(self):
        apply_selected_working_copys()

    @undochunk
    def _call_apply_on_new_blendshape(self):
        create_blendshape_corrective_for_selected_working_copys()


class TemplateSelecterView(QtWidgets.QWidget):
    pass


_corrective_blendshape_window = None


def launch():
    if _corrective_blendshape_window is None:
        global _corrective_blendshape_window
        _corrective_blendshape_window = CorrectiveBlendshapeWindow(
            get_main_maya_window_instance())
    _corrective_blendshape_window.show()
