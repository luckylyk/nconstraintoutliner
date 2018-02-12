
import os
from functools import partial

from PySide2 import QtWidgets, QtGui, QtCore

from maya_libs.qt.main_window import get_maya_windows
from .finaling import (
    create_working_copy_on_selection, delete_selected_working_copys,
    set_working_copys_transparency, apply_selected_working_copys,
    create_blendshape_corrective_for_selected_working_copys,
    get_working_copys_transparency)


WINDOWTITLE = "Corrective Blendshape"
ICONPATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'icons')

KEY_TEMPLATES = [
    [None, None, None, None, 0.0, 1.0, 0.0, None, None, None, None],
    [None, None, None, 0.0, 1.0, None, 1.0, 0.0, None, None, None],
    [None, None, None, None, None, 1.0, None, None, None, None, None],
    [None, None, None, None, None, 0.0, None, None, None, None, None],
    [None, None, None, None, 0.0, 1.0, None, None, None, None, None],
    [None, None, None, None, 1.0, 0.0, None, None, None, None, None],
    [0.0, None, 0.15, 0.8, None, 1.0, None, 0.8, 0.15, None, 0.0],
    [None, None, None, None, None, None, None, None, None, None, None]]

class CorrectiveBlendshapeWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CorrectiveBlendshapeWindow, self).__init__(
            parent, QtCore.Qt.Tool)

        # self.setFixedSize(QtCore.QSize(222, 234))
        self.setWindowTitle(WINDOWTITLE)

        self._create_working_copy_button = QtWidgets.QPushButton()
        self._create_working_copy_button.setText('Create Sculpt')
        self._create_working_copy_button.released.connect(
            self._call_create_working_copy)

        self._delete_working_copy_on_mesh_button = QtWidgets.QPushButton()
        self._delete_working_copy_on_mesh_button.setText('Cancel Sculpt')
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
        self._display_slider.setValue(
            int(get_working_copys_transparency() * 100))
        self._display_slider.valueChanged.connect(self._call_slider_changed)

        self._animation_template_editor = AnimationTemplateEditor(self)

        font = QtGui.QFont()
        font.setBold(True)
        font.setPixelSize(16)
        self._apply_button = QtWidgets.QPushButton('Apply')
        self._apply_button.released.connect(self._call_apply)
        self._apply_button.setFont(font)
        self._apply_on_new_blendshape_button = QtWidgets.QPushButton()
        self._apply_on_new_blendshape_button.setText('Apply on new blendshape')
        self._apply_on_new_blendshape_button.released.connect(
            self._call_apply_on_new_blendshape)

        self._animation_template_buttons = self._create_animation_template_buttons()
        self._animation_template_layout = self._create_animation_template_layout()

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setSpacing(4)
        self._layout.addLayout(self._create_delete_layout)
        self._layout.addWidget(self._display_slider)
        self._layout.addWidget(self._animation_template_editor)
        self._layout.addLayout(self._animation_template_layout)
        self._layout.addSpacing(4)
        self._layout.addWidget(self._apply_button)
        self._layout.addWidget(self._apply_on_new_blendshape_button)

    def _create_animation_template_buttons(self):
        buttons = []
        for index in range(1, 9):
            button = QtWidgets.QPushButton()
            button.setIcon(
                QtGui.QIcon(
                    os.path.join(ICONPATH, 'template_0{}.png'.format(index))))
            button.setIconSize(QtCore.QSize(35, 24))
            button.setFixedSize(QtCore.QSize(47, 35))
            button.clicked.connect(
                partial(self._call_set_template_values, index -1))
            buttons.append(button)
        return buttons

    def _create_animation_template_layout(self):
        layout = QtWidgets.QGridLayout()
        row, col = 0, 0
        for button in self._animation_template_buttons:
            layout.addWidget(button, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
        return layout

    #@undochunk
    def _call_create_working_copy(self):
        create_working_copy_on_selection()
        set_working_copys_transparency(self._display_slider.value() / 100.0)

    #@undochunk
    def _call_delete_working_copy(self):
        delete_selected_working_copys()

    def _call_slider_changed(self, value):
        set_working_copys_transparency(value / 100.0)

    #@undochunk
    def _call_apply(self):
        apply_selected_working_copys(
            values=self._animation_template_editor.values())

    #@undochunk
    def _call_apply_on_new_blendshape(self):
        create_blendshape_corrective_for_selected_working_copys(
            values=self._animation_template_editor.values())

    def _call_set_template_values(self, value):
        self._animation_template_editor.set_values(KEY_TEMPLATES[value])


class AnimationTemplateEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AnimationTemplateEditor, self).__init__(parent)
        self.configure()

        self._values = KEY_TEMPLATES[0]

        self._edit_mode = False
        self._edited_index = None
        self._edited_value = None

        self._working_rect = QtCore.QRect(0, 15, 200, 85)
        self._working_area = QtCore.QRect(-15, 0, 215, 100)

        self._mouse_clicked = False
        self._mouse_in_working_rect = False
        self._mouse_in_working_area = False
        self._mouse_index_hovered = None

    def configure(self):
        self.setMouseTracking(True)
        self.setFixedSize(QtCore.QSize(200, 100))

    def values(self):
        if not self._edit_mode:
            return self._values

        values = self._values[:]
        values[self._edited_index] = None
        if self._mouse_index_hovered is not None:
            values[self._mouse_index_hovered] = self._edited_value
        return values

    def set_values(self, values):
        assert len(values) == 11
        assert [v <= 1 or v >= 0 for v in values]
        self._values = values
        self.repaint()

    def mousePressEvent(self, event):
        self._mouse_clicked = True
        self.set_edit_mode(event.pos())
        self.repaint()

    def mouseReleaseEvent(self, event):
        if self._edit_mode:
            self._values = self.values()
        self._mouse_clicked = False
        self._edit_mode = False
        self._edited_index = None
        self.repaint()

    def leaveEvent(self, event):
        if not self._mouse_clicked:
            self._mouse_in_working_rect = False
            self._mouse_in_working_area = False
            self.repaint()

    def mouseMoveEvent(self, event):
        self._mouse_in_working_rect = self._working_rect.contains(event.pos())
        self._mouse_in_working_area = self._working_area.contains(event.pos())
        if not self._working_area.contains(event.pos()):
            self._mouse_index_hovered = None
        else:
            self._mouse_index_hovered = int(round(event.pos().x() / 20.0))

        if self._edit_mode:
            self._edited_value = self._get_edited_value(event.pos())
        self.repaint()

    def set_edit_mode(self, point):
        """
        this method check if the paint context must be passed in edit mode
        """
        if not self.rect().contains(point):
            return

        value = self._values[self._mouse_index_hovered]
        if value is None:
            self._edit_mode = True
            self._edited_index = self._mouse_index_hovered
            return

        left = self._mouse_index_hovered * 20
        height = 70 * (1 - value) + 15
        near_rect = QtCore.QRect(left - 5, height - 5, left + 5, height + 5)
        if near_rect.contains(point):
            self._edit_mode = True
            self._edited_index = self._mouse_index_hovered

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        rect = self.rect()

        self._draw_grid(painter, rect)
        self._draw_lines(painter)
        self._draw_points(painter)

        if self._mouse_index_hovered is not None:
            self._draw_interactive_point(painter)

    def _draw_interactive_point(self, painter):
        value = self.values()[self._mouse_index_hovered]
        if value is None:
            return

        if self._edit_mode:
            pen = QtGui.QPen(QtGui.QColor('white'))
            brush = QtGui.QBrush(QtGui.QColor('white'))
            painter.setPen(pen)
            painter.setBrush(brush)
            point = QtCore.QPoint(
                self._mouse_index_hovered * 20,
                70 * (1 - value) + 15)
            painter.drawEllipse(point, 3, 3)
        else:
            point = QtCore.QPoint(
                self._mouse_index_hovered * 20,
                70 * (1 - value) + 15)
            painter.drawEllipse(point, 3, 3)

    def _draw_grid(self, painter, rect):
        pen = QtGui.QPen(QtGui.QColor('#111111'))
        pen.setStyle(QtCore.Qt.SolidLine)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor('#282828'))
        painter.drawRect(rect)
        pen = QtGui.QPen(QtGui.QColor('#323232'))
        painter.setPen(pen)

        for i in range(10):
            left = i * 20
            painter.drawLine(
                QtCore.QPoint(left, 2),
                QtCore.QPoint(left, rect.height() -2))

        pen = QtGui.QPen(QtGui.QColor('#434343'))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(
            QtCore.QPoint(100, 3),
            QtCore.QPoint(100, rect.height() -3))

        pen = QtGui.QPen(QtGui.QColor('#323232'))
        painter.setPen(pen)
        painter.drawLine(
            QtCore.QPoint(3, rect.height() -15),
            QtCore.QPoint(rect.width() - 3, rect.height() - 15))
        painter.drawLine(
            QtCore.QPoint(3, 15),
            QtCore.QPoint(rect.width() - 3, 15))

    def _draw_lines(self, painter):
        points = self._get_points()
        lines = []
        values = self.values()
        if not any([1 for f in values if f is not None]):
            return lines

        if values[0] is None:
            point = QtCore.QPoint(0, points[0].y())
            points.insert(0, point)

        if values[-1] is None:
            point = QtCore.QPoint(200, points[-1].y())
            points.append(point)

        for index, point in enumerate(points[:-1]):
            line = QtCore.QLine(point, points[index + 1])
            lines.append(line)

        pen = QtGui.QPen(QtGui.QColor('orange'))
        painter.setPen(pen)
        for line in lines:
            painter.drawLine(line)

    def _draw_points(self, painter):
        pen = QtGui.QPen(QtGui.QColor('red'))
        brush = QtGui.QBrush(QtGui.QColor('red'))
        painter.setPen(pen)
        painter.setBrush(brush)
        for point in self._get_points():
            painter.drawEllipse(point, 2, 2)

    def _get_points(self):
        points = []
        for index, value in enumerate(self.values()):
            if value is None:
                continue
            left = index * 20
            height = 70 * (1 - value) + 15
            points.append(QtCore.QPoint(left, height))
        return points

    def _get_edited_value(self, point):
        if not self._working_area.contains(point):
            return None

        if point.y() < 15:
            return 1.0
        elif point.y() > 75:
            return 0.0
        else:
            return 1 - ((point.y() - 15) / 60.0)


_corrective_blendshape_window = None


def launch():
    if _corrective_blendshape_window is None:
        global _corrective_blendshape_window
        _corrective_blendshape_window = CorrectiveBlendshapeWindow(
            get_maya_windows())
    _corrective_blendshape_window.show()
