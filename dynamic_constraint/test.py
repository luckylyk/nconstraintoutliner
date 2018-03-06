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

    cmds.select([sphere_1 + ".vtx[53:70]", sphere_2 + ".vtx[0]"])
    dc = DynamicConstraint.create(DynamicConstraint.COMPONENT_TO_COMPONENT)
    dc.set_color(255, 0, 0)

    cmds.select([sphere_1, sphere_2 + ".vtx[35:50]"])
    dc = DynamicConstraint.create(DynamicConstraint.POINT_TO_SURFACE)
    dc.set_color(0, 125, 125)

    sphere_1 = cmds.polySphere()[0]
    cmds.setAttr(sphere_1 + '.t', 4, 0, 1)

    sphere_2 = cmds.polySphere()[0]
    cmds.setAttr(sphere_2 + '.t', 4, 0, -1)

    cmds.select([sphere_1, sphere_2])
    mel.eval('createNCloth 0')

    cmds.select([sphere_1])
    dc = DynamicConstraint.create(DynamicConstraint.TRANSFORM)
    dc.set_color(0, 125, 125)

    cmds.select([sphere_1, sphere_2 + ".vtx[381]"])
    dc = DynamicConstraint.create(DynamicConstraint.POINT_TO_SURFACE)
    dc.set_color(0, 125, 125)


def create_test_scene_for_corrective_blendshape():
    cube = cmds.polyCube(
        subdivisionsDepth=5, subdivisionsHeight=10, subdivisionsWidth=5,
        name='my_test_cube', height=5, width=2.5, depth=2.5)

    cmds.delete(cube[1])
    cube = cube[0]
    cmds.setAttr(cube + '.ty', 2.5)

    cmds.select(clear=True)
    joints = [
        cmds.joint(position=(0, 0, 0)),
        cmds.joint(position=(0, 1.25, 0)),
        cmds.joint(position=(0, 2.5, 0)),
        cmds.joint(position=(0, 3.75, 0)),
        cmds.joint(position=(0, 5, 0))]

    cmds.select([cube] + joints)
    cmds.skinCluster()
    cmds.select(joints[1:])
    cmds.rotate(0, 0, 18, relative=True, objectSpace=True)