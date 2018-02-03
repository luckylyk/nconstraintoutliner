import shiboken2
from PySide2 import QtWidgets
import maya.OpenMayaUI as omui


def get_maya_windows():
    """
    Get the main Maya window as a QtWidgets.QMainWindow instance
    @return: QtWidgets.QMainWindow instance of the top level Maya windows
    """
    main_window = omui.MQtUtil.mainWindow()
    if main_window is not None:
        return shiboken2.wrapInstance(long(main_window), QtWidgets.QWidget)