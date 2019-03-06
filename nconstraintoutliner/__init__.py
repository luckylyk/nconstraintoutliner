
from PySide2 import QtWidgets
import shiboken2
import maya.OpenMayaUI as omui
from nconstraintoutliner.outliner import NConstraintOutliner


_nconstraint_outliner = None


def launch():
    if _nconstraint_outliner is None:
        global _nconstraint_outliner
        main_window = omui.MQtUtil.mainWindow()
        parent = shiboken2.wrapInstance(long(main_window), QtWidgets.QWidget)
        _nconstraint_outliner = NConstraintOutliner(parent)
    _nconstraint_outliner.show()

