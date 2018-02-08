import pymel.core as pm

from maya_libs.selection.decorators import (
    need_maya_selection, filter_node_type_in_selection,
    selection_contains_at_least)


CORRECTIVE_BLENDSHAPE_NAME = 'corrective_blendshape'
CORRECTIVE_BLENDSHAPE_ATTR = 'is_corrective_blendshape'

WORKING_MESH_ATTR = 'is_working_copy_mesh'
DISPLAY_MESH_ATTR = 'is_display_copy_mesh'

WORKING_MESH_SHADER = 'TMP_WORKING_COPY_BLINN'
WORKING_MESH_SG = 'TMP_WORKING_COPY_BLINNSG'
DISPLAY_MESH_SHADER = 'TMP_DISPLAY_COPY_LAMBERT'
DISPLAY_MESH_SG = 'TMP_DISPLAY_COPY_LAMBERTSG'


@filter_node_type_in_selection(type='transform', objectsOnly=True)
@selection_contains_at_least(1, 'transform')
@need_maya_selection
def create_working_copy_on_selection():
    for transform in pm.ls(selection=True):
        if mesh_have_working_copy(transform):
            continue
        create_working_copy(transform)


def create_working_copy(mesh):
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
    original_mesh = pm.PyNode(mesh)
    working_copy = original_mesh.duplicate()[0]
    display_copy = original_mesh.duplicate()[0]

    # clean intermediate duplicated shapes
    for shape in working_copy.getShapes() + display_copy.getShapes():
        if shape.intermediateObject.get() is True:
            pm.delete(shape)

    original_mesh.lodVisibility.set(False)
    working_copy.rename(working_copy.name() + '_f' + str(pm.env.time))
    for shape in display_copy.getShapes():
        shape.overrideEnabled.set(True)
        shape.overrideDisplayType.set(2)

    # create and link attibutes to connect working meshes to original mesh.
    pm.addAttr(
        working_copy,
        attributeType='message',
        longName=WORKING_MESH_ATTR,
        niceName=WORKING_MESH_ATTR.replace('_', ' '))

    pm.addAttr(
        display_copy,
        attributeType='message',
        longName=DISPLAY_MESH_ATTR,
        niceName=DISPLAY_MESH_ATTR.replace('_', ' '))

    original_mesh.message >> working_copy.is_working_copy_mesh
    original_mesh.message >> display_copy.is_display_copy_mesh

    # create shaders
    if not pm.objExists(WORKING_MESH_SHADER):
        pm.shadingNode('blinn', asShader=True, name=WORKING_MESH_SHADER)
    working_copy_shader = pm.PyNode(WORKING_MESH_SHADER)
    working_copy_shader.color.set(1, .25, .33)

    if not pm.objExists(DISPLAY_MESH_SHADER):
        pm.shadingNode('lambert', asShader=True, name=DISPLAY_MESH_SHADER)
    display_copy_shader = pm.PyNode(DISPLAY_MESH_SHADER)
    display_copy_shader.color.set(0, .25, 1)
    display_copy_shader.transparency.set(1, 1, 1)

    pm.select(working_copy)
    pm.hyperShade(working_copy, assign=working_copy_shader)
    pm.select(display_copy)
    pm.hyperShade(display_copy, assign=display_copy_shader)

    pm.select(working_copy)


@filter_node_type_in_selection(type='transform', objectsOnly=True)
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
    original_mesh = pm.PyNode(mesh)
    working_meshes = [
        node for node in original_mesh.message.listConnections()
        if node.hasAttr(WORKING_MESH_ATTR) or node.hasAttr(DISPLAY_MESH_ATTR)]

    original_mesh.lodVisibility.set(True)
    pm.delete(working_meshes)

    # clean shaders
    if not pm.objExists(WORKING_MESH_SG):
        working_copy_shader_group = pm.PyNode(WORKING_MESH_SG)
        if not working_copy_shader_group.dagSetMembers.listConnections():
            pm.delete([WORKING_MESH_SG, WORKING_MESH_SHADER])

    if not pm.objExists(DISPLAY_MESH_SG):
        display_copy_shader_group = pm.PyNode(DISPLAY_MESH_SG)
        if not display_copy_shader_group.dagSetMembers.listConnections():
            pm.delete([DISPLAY_MESH_SG, DISPLAY_MESH_SHADER])


def set_working_copys_transparency(value):
    """
    this method's tweaking the working shaders to let user
    compare working mesh and original mesh
    """
    if not pm.objExists(WORKING_MESH_SHADER):
        pm.warning('working mesh shader not found')
    if not pm.objExists(DISPLAY_MESH_SHADER):
        pm.warning('working mesh shader not found')

    working_copy_shader = pm.PyNode(WORKING_MESH_SHADER)
    display_copy_shader = pm.PyNode(DISPLAY_MESH_SHADER)

    working_copy_shader.transparency.set(value, value, value)
    display_copy_shader.transparency.set(1 - value, 1 - value, 1 - value)


def get_corrective_blendshapes(mesh):
    """
    this method return a list off all corrective blendshapes
    present in the history
    """
    original_mesh = pm.PyNode(mesh)
    return [
        node for node in original_mesh.inMesh.listHistory()
        if isinstance(node, pm.nt.BlendShape) and
        node.hasAttr(CORRECTIVE_BLENDSHAPE_ATTR)]


@filter_node_type_in_selection(type='transform', objectsOnly=True)
@selection_contains_at_least(1, 'transform')
@need_maya_selection
def create_blendshape_corrective_for_selected_working_copys():
    for mesh_transform in pm.ls(selection=True):
        if not mesh_transform.hasAttr(WORKING_MESH_ATTR):
            continue
        mesh = mesh_transform.attr(WORKING_MESH_ATTR).listConnections()[0]
        create_blendshape_corrective_on_mesh(base=mesh, target=mesh_transform)


def create_blendshape_corrective_on_mesh(base, target):
    """
    this method's creating a new corrective blendshape on a mesh and add the
    first target
    """
    base = pm.PyNode(base)
    target = pm.PyNode(target)
    name = base.name() + '_' + CORRECTIVE_BLENDSHAPE_NAME

    corrective_blendshape = pm.blendShape(
        target, base, name=name, before=True, weight=(0, 1))[0]

    pm.addAttr(
        corrective_blendshape, attributeType='bool',
        longName=CORRECTIVE_BLENDSHAPE_ATTR,
        niceName=CORRECTIVE_BLENDSHAPE_ATTR.replace('_', ' '))

    return corrective_blendshape


def mesh_have_working_copy(mesh):
    '''
    This method query if a working copy is currently in use
    it should never append
    '''
    return bool([
        node for node in mesh.message.listConnections()
        if node.hasAttr(WORKING_MESH_ATTR) or node.hasAttr(DISPLAY_MESH_ATTR)])


def add_target_on_corrective_blendshape(blendshape, target, base):
    '''
    this is a simple method to add target on a blendshape
    '''
    corrective_blendshape = pm.PyNode(blendshape)
    base = pm.PyNode(base)
    target = pm.PyNode(target)

    index = int(
        corrective_blendshape.inputTarget[0].inputTargetGroup.get(
            multiIndices=True)[-1] + 1)

    value = blendshape.envelope.get()
    blendshape.envelope.set(0)
    pm.blendShape(
        blendshape, edit=True, before=True, target=(base, index, target, 1.0))
    pm.blendShape(blendshape, edit=True, weight=(index, 1.0))
    blendshape.envelope.set(value)


@filter_node_type_in_selection(type='transform', objectsOnly=True)
@selection_contains_at_least(1, 'transform')
@need_maya_selection
def apply_selected_working_copys():
    for transform in pm.ls(selection=True):
        if transform.hasAttr(WORKING_MESH_ATTR):
            apply_working_copy(transform)


def apply_working_copy(mesh, blendshape=None):
    '''
    this method is let apply a working mesh on his main shape
    it manage if a blendshape already exist or not.
    '''
    working_mesh = pm.PyNode(mesh)
    if not working_mesh.hasAttr(WORKING_MESH_ATTR):
        pm.warning('please, select working mesh')

    original_mesh = working_mesh.attr(
        WORKING_MESH_ATTR).listConnections()[0]

    if blendshape:
        add_target_on_corrective_blendshape(
            blendshape, working_mesh, original_mesh)

    if blendshape is None:
        blendshapes = get_corrective_blendshapes(original_mesh)
        if not blendshapes:
            create_blendshape_corrective_on_mesh(
                original_mesh, working_mesh)
        else:
            add_target_on_corrective_blendshape(
                blendshapes[0], working_mesh, original_mesh)

    delete_working_copy_on_mesh(original_mesh)
