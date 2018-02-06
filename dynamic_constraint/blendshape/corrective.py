######### WIIIIIP ##########

import pymel.core as pm

CORRECTIVE_BLENDSHAPE_NAME = 'corrective_blendshape'
CORRECTIVE_BLENDSHAPE_ATTR = 'is_corrective_blendshape'

WORKING_MESH_ATTR = 'is_working_copy_mesh'
DISPLAY_MESH_ATTR = 'is_display_copy_mesh'

WORKING_MESH_SHADER = 'TMP_WORKING_COPY_BLINN'
WORKING_MESH_SG = 'TMP_WORKING_COPY_BLINNSG'
DISPLAY_MESH_SHADER = 'TMP_DISPLAY_COPY_LAMBERT'
DISPLAY_MESH_SG = 'TMP_DISPLAY_COPY_LAMBERTSG'


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
        if shape.intermerdiateObject.get() == True:
            pm.delete(shape)
    original_mesh.lodVisibility.set(False)

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
    if  not pm.objExists(WORKING_MESH_SG):
        working_copy_shader_group = pm.PyNode(WORKING_MESH_SG)
        if not working_copy_shader_group.dagSetMembers.listConnections():
            pm.delete([WORKING_MESH_SG, WORKING_MESH_SHADER])

    if  not pm.objExists(DISPLAY_MESH_SG):
        display_copy_shader_group = pm.PyNode(DISPLAY_MESH_SG)
        if not display_copy_shader_group.dagSetMembers.listConnections():
            pm.delete([DISPLAY_MESH_SG, DISPLAY_MESH_SHADER])


def set_working_copy_transparency(value):
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


def has_corrective_blendshape(mesh):
    """
    this method look in the mesh history if a corrective blendshape exists
    """
    original_mesh = pm.PyNode(mesh)
    for node in original_mesh.inMesh.listHistory():
        if isinstance(node, pm.nt.blendShape):
            if node.hasAttr('CORRECTIVE_BLENDSHAPE_ATTR'):
                return True
    return False


def create_blendshape_corrective_on_mesh(mesh, target):
    """
    this method's creating a new corrective blendshape on a mesh and add the
    first target
    """
    mesh = pm.PyNode(mesh)
    target = pm.PyNode(target)

    corrective_blendshape = pm.blendShape(
        target, mesh, name=CORRECTIVE_BLENDSHAPE_NAME, 
        before=True, weight=(0, 1))[0]

    pm.addAttr(
        corrective_blendshape, attributeType='bool',
        longName=CORRECTIVE_BLENDSHAPE_ATTR,
        niceName=CORRECTIVE_BLENDSHAPE_ATTR.replace('_', ' '))

    return corrective_blendshape


def add_target_on_corrective_blendshape(blendshape, target):
    corrective_blendshape = pm.PyNode(blendshape)
    target = pm.PyNode(target)
    ### TODO ###


