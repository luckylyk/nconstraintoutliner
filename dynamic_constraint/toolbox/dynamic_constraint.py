
"""
This module containing tools to create Dynamic Constraint : nConstraint
It's useful to remember the constaint's creation preset (saving in a custom
attribute). It respect production nomenclature and can be used as model for
gui.
"""

from itertools import cycle
from maya import cmds, mel
from maya_libs.selection.decorators import keep_maya_selection, need_maya_selection
from maya_libs.selection.context_managers import MayaSelectionManager

TYPE_ATTR_NAME = 'constraintType'
TYPE_ATTR_LONGNAME = 'Dynamic Constraint Type'

DYNAMIC_CONTRAINT_TYPES = [
    {'name': 'transform', 'type': 'transform', 'short': 'TRS'},
    {'name': 'point to surface', 'type': 'pointToPoint',  'short': 'PTP'},
    {'name': 'slide on surface', 'type': 'pointToSurface', 'short': 'PTS'},
    {'name': 'exclude collide', 'type': 'collisionExclusion', 'short': 'EXC'},
    {'name': 'weld', 'type': 'weld', 'short': 'WEL'},
    {'name': 'undefined', 'type': 'undefined', 'short': 'UND'}]


class DynamicConstraint(object):
    """
    This class is a model of nConstraint with a custom attribute who save the
    creation preset and a name auto-generated in the outliner.

    this object can be instancied around an existing node:
    dynamic_constraint = DynamicConstraint(nodename='existing_nConstraintShape')
    or instancied creating a new constraint node in maya:
    dynamic_constraint = DynamicConstraint.create(DynamicConstraint.TRANSFORM)
    """
    TRANSFORM = 0
    POINT_TO_SURFACE = 1
    SLIDE_ON_SURFACE = 2
    EXCLUDE_COLLIDE = 3
    WELD = 4
    UNDEFINED = 5

    def __init__(self, nodename=None):
        self._node = nodename
        self._components_iterator = cycle(self.components)

    @staticmethod
    def create(constraint_type=None):
        '''
        Alternative constructor, creating the node in maya and name it correctly
        '''
        onstraint_type = constraint_type or DynamicConstraint.UNDEFINED
        constraint_node = create_dynamic_constraint_node(constraint_type)
        dynamic_constraint = DynamicConstraint(constraint_node)
        dynamic_constraint.rename_node_from_components()
        return dynamic_constraint

    @property
    def color(self):
        return get_dynamic_constraint_color(self._node)

    @property
    def components(self):
        ''' return objects members parent's '''
        return get_dynamic_constraint_components(self._node)

    @property
    def enable(self):
        return cmds.getAttr(self._node + '.enable')

    @property
    def is_named_correctly(self):
        transform = cmds.listRelatives(self._node, parent=True)[0]
        return transform == self.nice_name

    @property
    def is_well_named(self):
        return self.parent == self.nice_name

    @property
    def nice_name(self):
        return get_dynamic_constraint_nice_name(self._node)

    @property
    def node(self):
        return self._node

    @property
    def parent(self):
        return cmds.listRelatives(self._node, parent=True)[0]

    @property
    def type(self):
        return get_constraint_type(self._node)

    @property
    def type_name(self):
        return DYNAMIC_CONTRAINT_TYPES[self.type]['name']

    @keep_maya_selection
    def add_selection_to_members(self):
        cmds.select([self._node] + cmds.ls(sl=True))
        mel.eval('dynamicConstraintMembership "add";')
        self._components_iterator = cycle(self.components)

    def paint_constraint_strength_map_on_components(self):
        component = self._components_iterator.next()
        cmds.select([self._node, component])
        cmd = (
            'setNComponentMapType("strength",1);'
            'artAttrNComponentToolScript 4 strength;')
        mel.eval(cmd)

    @keep_maya_selection
    def remove_selection_to_members(self):
        cmds.select([self._node] + cmds.ls(sl=True))
        mel.eval('dynamicConstraintMembership "remove";')
        self._components_iterator = cycle(self.components)

    def rename_node_from_components(self):
        parent = self.parent
        nice_name = self.nice_name
        shape_name = nice_name + 'Shape'
        cmds.rename(self._node, shape_name)
        cmds.rename(parent, nice_name)
        self._node = nice_name

    def set_type(self, constraint_type):
        attribute = self._node + '.' + TYPE_ATTR_NAME
        cmds.setAttr(attribute, constraint_type)

    def switch(self):
        return cmds.setAttr(self._node + '.enable', not self.enable)


def add_and_set_constraint_type_attribute(contraint_shape, constraint_type):
    """
    this method add an enum attribut on the constraint shape. Containing the
    preset name used during the constraint creation
    """
    cmds.addAttr(
        contraint_shape, attributeType='enum',
        longName=TYPE_ATTR_NAME,
        niceName=TYPE_ATTR_LONGNAME,
        keyable=True,
        enumName=": ".join([t['name'] for t in DYNAMIC_CONTRAINT_TYPES]))

    attribute = contraint_shape + '.' + TYPE_ATTR_NAME
    cmds.setAttr(attribute, constraint_type)


def create_dynamic_constraint_node(constraint_type):
    """
    this method create an nConstraint and apply the custom enum attribute
    containing the different presets name and set the given one.
    @constraint_type must be an int. The constant are in the DynamicConstraint
    class :
        DynamicConstraint.TRANSFORM, DynamicConstraint.POINT_TO_SURFACE,
        DynamicConstraint.SLIDE_ON_SURFACE, DynamicConstraint.EXCLUDE_COLLIDE,
        DynamicConstraint.WELD, DynamicConstraint.UNDEFINED
    """
    constraint_name = DYNAMIC_CONTRAINT_TYPES[constraint_type]['name']
    constraint_node = mel.eval(
        'createNConstraint {} 0;'.format(constraint_name))
    if not constraint_node:
        return
    add_and_set_constraint_type_attribute(constraint_node[0], constraint_type)
    return constraint_node[0]


def get_dynamic_constraint_color(contraint_shape):
    '''
    smart function who return the nconstraint viewport color.
    It working as a normal transform override color except if color is
    undefined, it returns 25, 25, 125 
    '''
    parent = cmds.listRelatives(contraint_shape, parent=True)[0]

    if not cmds.getAttr(parent + '.overrideEnabled'):
        return 25, 25, 125

    if cmds.getAttr(parent + '.overrideRGBColors'):
        return [
            c * 255 for c in
            cmds.getAttr(parent + '.overrideColorRGB')[0]]

    else:
        color_index = cmds.getAttr(parent + '.overrideColor')
        if color_index > 0:
            return [
                c * 255 for c in
                cmds.colorIndex(color_index, query=True)]
        else:
            return 25, 25, 125


@keep_maya_selection
def get_dynamic_constraint_components(constraint_shape):
    '''
    return the nconstraint components list as list of strings.
    '''
    cmds.select(constraint_shape)
    mel.eval('dynamicConstraintMembership "select";')
    components = cmds.ls(selection=True, objectsOnly=True)
    components = [n for c in components for n in cmds.listRelatives(c, p=True)]
    return components


def get_dynamic_constraint_nice_name(constraint_shape):
    '''
    this is construct a name for a constraint transform based
    on is components names
    '''
    constraint_type = get_constraint_type(constraint_shape)
    type_name = DYNAMIC_CONTRAINT_TYPES[constraint_type]['short']
    components = get_dynamic_constraint_components(constraint_shape)
    if len(components) > 1:
        name = type_name + '_' + 'To'.join(components)
    elif len(components) == 1:
        name = components[0]
    else:
        name = type_name
    name += '_DNC'
    return name


def get_constraint_type(constraint_shape):
    '''
    return an index corresponding to DYNAMIC_CONTRAINT_TYPES index
    of the type selected in the enum attribut set on the node
    '''
    if not cmds.attributeQuery(
            TYPE_ATTR_NAME,
            node=constraint_shape, exists=True):
        add_and_set_constraint_type_attribute(
            constraint_shape, DynamicConstraint.UNDEFINED)

    attribute = constraint_shape + '.' + TYPE_ATTR_NAME
    return cmds.getAttr(attribute)


def list_dynamic_constraints():
    nodes = cmds.ls(type='dynamicConstraint')
    return [DynamicConstraint(node) for node in nodes]
