from .dynamic_constraint import DynamicConstraint
from maya import cmds, mel


def create_dynamic_constraint_maya_scene():
    sphere_1 = cmds.polySphere()[0]
    cmds.setAttr(sphere_1 + '.t', -3, 0, 1)

    sphere_2 = cmds.polySphere()[0]
    cmds.setAttr(sphere_2 + '.t', -3, 0, -1)

    cmds.select([sphere_1, sphere_2])
    mel.eval('createNCloth 0')

    cmds.select([sphere_1 + ".vtx[381]", sphere_2 + ".vtx[381]"])
    dc = DynamicConstraint.create(DynamicConstraint.TRANSFORM)
    dc.set_color(215, 25, 125)
