import pymel.core as pm
import maya.api.OpenMaya as om2
from maya import cmds

from maya_libs.selection.decorators import (
    need_maya_selection, filter_selection, selection_contains_at_least,
    select_shape_transforms, filter_transforms_by_children_types)


CORRECTIVE_BLENDSHAPE_NAME = 'corrective_blendshape'
CORRECTIVE_BLENDSHAPE_ATTR = 'is_corrective_blendshape'

WORKING_MESH_ATTR = 'is_working_copy_mesh'
DISPLAY_MESH_ATTR = 'is_display_copy_mesh'

WORKING_MESH_SHADER = 'TMP_WORKING_COPY_BLINN'
WORKING_MESH_SG = 'TMP_WORKING_COPY_BLINNSG'
DISPLAY_MESH_SHADER = 'TMP_DISPLAY_COPY_LAMBERT'
DISPLAY_MESH_SG = 'TMP_DISPLAY_COPY_LAMBERTSG'


@filter_selection(type=('mesh', 'transform'), objectsOnly=True)
@select_shape_transforms
@filter_transforms_by_children_types('mesh')
@selection_contains_at_least(1, 'transform')
@need_maya_selection
def create_working_copy_on_selection():
    for transform in cmds.ls(selection=True):
        if mesh_have_working_copy(transform):
            continue
        create_working_copy(transform)


def create_working_copy(original_mesh):
    """
    this method create two meshes linked to the
    given mesh's message attribute.

    the original mesh is hidden during the procedure (lodVisibility)
    the working copy, is a mesh for create the deformation.
    the display copy, is a copy (hidden by default), to compare the working
        copy to the original mesh.

    a red shader is assigned to the working copy
    a blue shader is assigned to the display copy
    """
    working_copy = cmds.duplicate(original_mesh)[0]
    display_copy = cmds.duplicate(original_mesh)[0]
    print working_copy, display_copy

    # clean intermediate duplicated shapes
    for shape in cmds.listRelatives(working_copy, shapes=True) + cmds.listRelatives(display_copy, shapes=True):
        if cmds.getAttr(shape + '.intermediateObject') is True:
            cmds.delete(shape)

    cmds.setAttr(original_mesh + '.lodVisibility', False)
    for shape in cmds.listRelatives(display_copy, shapes=True):
        cmds.setAttr(shape + '.overrideEnabled', True)
        cmds.setAttr(shape + '.overrideDisplayType', 2)
    working_copy = cmds.rename(
        working_copy, working_copy + '_f' + str(cmds.currentTime(q=1)))

    # create and link attibutes to connect working meshes to original mesh.
    cmds.addAttr(
        working_copy,
        attributeType='message',
        longName=WORKING_MESH_ATTR,
        niceName=WORKING_MESH_ATTR.replace('_', ' '))

    cmds.addAttr(
        display_copy,
        attributeType='message',
        longName=DISPLAY_MESH_ATTR,
        niceName=DISPLAY_MESH_ATTR.replace('_', ' '))

    cmds.connectAttr(original_mesh + '.message', working_copy + '.' + WORKING_MESH_ATTR)
    cmds.connectAttr(original_mesh + '.message', display_copy + '.' + DISPLAY_MESH_ATTR)

    # create shaders
    if not cmds.objExists(WORKING_MESH_SHADER):
        cmds.shadingNode('blinn', asShader=True, name=WORKING_MESH_SHADER)
    cmds.setAttr(WORKING_MESH_SHADER + '.color', 1, .25, .33)
    cmds.setAttr(WORKING_MESH_SHADER + '.transparency', 0, 0, 0)

    if not cmds.objExists(DISPLAY_MESH_SHADER):
        cmds.shadingNode('lambert', asShader=True, name=DISPLAY_MESH_SHADER)
    cmds.setAttr(DISPLAY_MESH_SHADER + '.color', 0, .25, 1)
    cmds.setAttr(DISPLAY_MESH_SHADER + '.transparency', 1, 1, 1)

    cmds.select(working_copy)
    cmds.hyperShade(working_copy, assign=WORKING_MESH_SHADER)
    cmds.select(display_copy)
    cmds.hyperShade(display_copy, assign=DISPLAY_MESH_SHADER)

    cmds.select(working_copy)


@filter_selection(type=('mesh', 'transform'), objectsOnly=True)
@select_shape_transforms
@filter_transforms_by_children_types('mesh')
@selection_contains_at_least(1, 'transform')
@need_maya_selection
def delete_selected_working_copys():
    for mesh_transform in pm.ls(selection=True):
        if not mesh_transform.hasAttr(WORKING_MESH_ATTR):
            continue
        mesh = mesh_transform.attr(WORKING_MESH_ATTR).listConnections()[0]
        delete_working_copy_on_mesh(mesh)


def delete_working_copy_on_mesh(mesh):
    '''
    This method let the user cancel his work and delete current working copy
    '''
    working_meshes = [
        node for node in cmds.listConnections(mesh + '.message')
        if cmds.attributeQuery(WORKING_MESH_ATTR, node=node, exists=True) or
        cmds.attributeQuery(DISPLAY_MESH_ATTR, node=node, exists=True)]

    cmds.setAttr(mesh + '.lodVisibility', True)
    cmds.delete(working_meshes)

    # clean shaders
    if not cmds.objExists(WORKING_MESH_SG):
        if not cmds.listConnections(WORKING_MESH_SG + '.dagSetMembers'):
            cmds.delete([WORKING_MESH_SG, WORKING_MESH_SHADER])

    if not cmds.objExists(DISPLAY_MESH_SG):
        if not cmds.listConnections(DISPLAY_MESH_SG + '.dagSetMembers'):
            cmds.delete([DISPLAY_MESH_SG, DISPLAY_MESH_SHADER])


def get_working_copys_transparency():
    """
    this method's querying the working shaders transparency
    """
    if not cmds.objExists(WORKING_MESH_SHADER):
        return 0.0
    if not cmds.objExists(DISPLAY_MESH_SHADER):
        return 0.0
    return cmds.getAttr(WORKING_MESH_SHADER + '.transparency')[0][0]


def set_working_copys_transparency(value):
    """
    this method's tweaking the working shaders to let user
    compare working mesh and original mesh
    """
    if not cmds.objExists(WORKING_MESH_SHADER):
        return cmds.warning('working mesh shader not found')
    if not cmds.objExists(DISPLAY_MESH_SHADER):
        return cmds.warning('working mesh shader not found')

    cmds.setAtttr(WORKING_MESH_SHADER + ".transparency", value, value, value)
    cmds.setAtttr(DISPLAY_MESH_SHADER + ".transparency", 1-value, 1-value, 1-value)


def get_corrective_blendshapes(mesh):
    """
    this method return a list off all corrective blendshapes
    present in the history
    """
    return [
        node for node in cmds.listHistory(mesh + '.inMesh')
        if cmds.nodeType(node) == 'blendShape' and
        cmds.attributeQuery(CORRECTIVE_BLENDSHAPE_ATTR, node=node, exists=True)]


@filter_selection(type=('mesh', 'transform'), objectsOnly=True)
@select_shape_transforms
@filter_transforms_by_children_types('mesh')
@selection_contains_at_least(1, 'transform')
@need_maya_selection
def create_blendshape_corrective_for_selected_working_copys(values=None):
    for transform in cmds.ls(selection=True):
        if not cmds.attributeQuery(WORKING_MESH_ATTR, node=transform, exists=True):
            continue
        base = cmds.listConnections(transform + '.' + WORKING_MESH_ATTR)[0]
        create_blendshape_corrective_on_mesh(
            base=base, target=transform, values=values)


def create_blendshape_corrective_on_mesh(base, target, values=None):
    """
    this method's creating a new corrective blendshape on a mesh and add the
    first target
    """
    name = base + '_' + CORRECTIVE_BLENDSHAPE_NAME

    corrective_blendshape = cmds.blendShape(
        target, base, name=name, before=True, weight=(0, 1))[0]

    cmds.addAttr(
        corrective_blendshape, attributeType='bool',
        longName=CORRECTIVE_BLENDSHAPE_ATTR,
        niceName=CORRECTIVE_BLENDSHAPE_ATTR.replace('_', ' '))

    if values is not None:
        set_animation_template_on_blendshape_target_weight(
            blendshape=corrective_blendshape, target_index=0, values=values)


def mesh_have_working_copy(mesh):
    '''
    This method query if a working copy is currently in use
    it should never append
    '''
    if cmds.listConnections(mesh + '.message') is None:
        return False
    return bool([
        node for node in cmds.listConnections(mesh + '.message')
        if cmds.attributeQuery(WORKING_MESH_ATTR, node=node, exists=True) or
        cmds.attributeQuery(DISPLAY_MESH_ATTR, node=node, exists=True)])


def add_target_on_corrective_blendshape(blendshape, target, base, values=None):
    '''
    this is a simple method to add target on a blendshape
    '''

    index = int(
        cmds.getAttr(
            blendshape + '.inputTarget[0].inputTargetGroup',
            multiIndices=True)[-1] + 1)

    set_target_relative(blendshape, target, base)

    cmds.blendShape(
        blendshape, edit=True, before=True,
        target=(base, index, target, 0.0))

    set_animation_template_on_blendshape_target_weight(
        blendshape=blendshape, target_index=index, values=values)


@filter_selection(type=('mesh', 'transform'), objectsOnly=True)
@select_shape_transforms
@selection_contains_at_least(1, 'transform')
@need_maya_selection
def apply_selected_working_copys(values=None):
    for transform in cmds.ls(selection=True):
        if cmds.attributeQuery(WORKING_MESH_ATTR, node=transform, exists=True):
            apply_working_copy(transform, values=values)


def apply_working_copy(working_mesh, blendshape=None, values=None):
    '''
    this method is let apply a working mesh on his main shape
    it manage if a blendshape already exist or not.
    '''
    if not cmds.attributeQuery(WORKING_MESH_ATTR, node=working_mesh, exists=True):
        pm.warning('please, select working mesh')

    original_mesh = cmds.listConnections(
        working_mesh + '.' + WORKING_MESH_ATTR)[0]

    if blendshape:
        add_target_on_corrective_blendshape(
            blendshape, working_mesh, original_mesh, values=values)

    if blendshape is None:
        blendshapes = get_corrective_blendshapes(original_mesh)
        if not blendshapes:
            create_blendshape_corrective_on_mesh(
                original_mesh, working_mesh, values=values)
        else:
            add_target_on_corrective_blendshape(
                blendshapes[0], working_mesh, original_mesh, values=values)

    delete_working_copy_on_mesh(original_mesh)

# def set_target_relative(blendshape, target, base):
#     """
#     the methode is setting the target relative to the base if a blendshape
#     exist to avoid double transformation when the target is applyied
#     Thanks Carlo Giesa, this one is yours :)
#     """
#     target = pm.PyNode(target)
#     base = pm.PyNode(base)
 
#     intermediate_mesh = pm.createNode("mesh")
#     in_connection = blendshape.attr('input[0].inputGeometry').listConnections(
#         source=True, destination=False, plugs=True)[0]
#     in_connection >> intermediate_mesh.inMesh
#     intermediate_mesh.outMesh.get(type=True)
#     in_connection // intermediate_mesh.inMesh

#     selection_list = om.MSelectionList()
#     selection_list.add(target.name())
#     selection_list.add(base.name())
#     selection_list.add(intermediate_mesh.name())

#     target_object = om.MObject()
#     base_object = om.MObject()
#     intermediate_object = om.MObject()

#     selection_list.getDependNode(0, target_object)
#     selection_list.getDependNode(1, base_object)
#     selection_list.getDependNode(2, intermediate_object)
#     selection_list.clear()

#     target_fn_esh = om.MFnMesh(target_object)
#     deform_fn_mesh = om.MFnMesh(base_object)
#     intermediate_fn_mesh = om.MFnMesh(intermediate_object)

#     target_points = om.MPointArray()
#     base_points = om.MPointArray()
#     intermediate_points = om.MPointArray()

#     target_fn_esh.getPoints(target_points)
#     deform_fn_mesh.getPoints(base_points)
#     intermediate_fn_mesh.getPoints(intermediate_points)

#     i = 0
#     while (i < target_points.length()):
#         intermediate_points.set(
#             intermediate_points[i] + (target_points[i] - base_points[i]), i)
#         i += 1

#     target_fn_esh.setPoints(intermediate_points)
#     target_fn_esh.updateSurface()
#     pm.delete(intermediate_mesh.listRelatives(parent=True))


def set_target_relative(blendshape, target, base):
    """
    the methode is setting the target relative to the base if a blendshape
    exist to avoid double transformation when the target is applyied
    Thanks Carlo Giesa, this one is yours :)
    """
    target = pm.PyNode(target)
    base = pm.PyNode(base)

    blendshape = pm.PyNode(blendshape)
    intermediate = pm.createNode('mesh')
    in_mesh = blendshape.input[0].inputGeometry.listConnections(plugs=True)[0]
    in_mesh >> intermediate.inMesh
    intermediate.outMesh.get(type=True)  # this force mesh evaluation
    in_mesh // intermediate.inMesh

    selection_list = om2.MSelectionList()
    selection_list.add(target.name())
    selection_list.add(base.name())
    selection_list.add(intermediate.name())

    target_fn_mesh = om2.MFnMesh(selection_list.getDagPath(0))
    target_points = target_fn_mesh.getPoints()
    base_points = om2.MFnMesh(selection_list.getDagPath(1)).getPoints()
    intermediate_points = om2.MFnMesh(selection_list.getDagPath(2)).getPoints()
    selection_list.clear()

    i = 0
    while (i < len(target_points)):
        intermediate_points[i] = (
            intermediate_points[i] + (target_points[i] - base_points[i]))
        i += 1

    target_fn_mesh.setPoints(intermediate_points)
    target_fn_mesh.updateSurface()
    #pm.delete(intermediate.getParent())


def set_animation_template_on_blendshape_target_weight(
        blendshape, target_index, values=None):
    """
    this method will apply an animation on the blendshape target index given.
    the value is an float array. It represent a value at frame.
    the array middle value is the value set at the current frame.
    """
    if values is None or not any([1 for v in values if v is not None]):
        return

    time = cmds.currentTime(query=True)
    frames = range(int(time - 5), int(time + 6))
    frames_values = {
        f: values[i] for i, f in enumerate(frames) if values[i] is not None}

    for frame, value in frames_values.iteritems():
        cmds.setKeyframe(
            blendshape.weight[target_index], time=frame, value=value,
            inTangentType='linear', outTangentType='linear')


