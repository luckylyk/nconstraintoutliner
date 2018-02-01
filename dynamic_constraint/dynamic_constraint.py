
"""
This module containing tools to create Dynamic Constraint : nConstraint
It's useful to remember the constaint's creation preset (saving in a custom
attribute). It respect production nomenclature and can be used as model for
gui.
"""

import logging
import json
import os
from itertools import cycle

from maya import cmds, mel
from maya_libs.selection.decorators import keep_maya_selection, need_maya_selection
from maya_libs.selection.context_managers import MayaSelectionManager

TYPE_ATTR_NAME = 'constraintType'
TYPE_ATTR_LONGNAME = 'Dynamic Constraint Type'

PRESETS_FOLDER = 'presets'
DYNAMIC_CONTRAINT_TYPES = [
    {
        'name': 'transform',
        'type': 'transform',
        'short': 'TRS',
        'preset_file': 'transform.json'
    },

    {
        'name': 'point to surface',
        'type': 'pointToPoint',
        'short': 'PTP',
        'preset_file': 'point_to_surface.json'
    },

    {
        'name': 'slide on surface',
        'type': 'pointToSurface',
        'short': 'PTS',
        'preset_file': 'slide_on_surface.json'
    },

    {
        'name': 'exclude collide',
        'type': 'collisionExclusion',
        'short': 'EXC',
        'preset_file': 'exclude_collider_pairs.json'
    },

    {
        'name': 'weld',
        'type': 'weld',
        'short': 'WEL',
        'preset_file': None
    },

    {
        'name': 'undefined',
        'type': 'undefined',
        'short': 'UND',
        'preset_file': None
    }]


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
    @need_maya_selection
    def create(constraint_type=None):
        '''
        Alternative constructor, creating the node in maya and name it correctly
        '''
        constraint_type = constraint_type or DynamicConstraint.UNDEFINED
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
        mel.evalDeferred(cmd)

    @keep_maya_selection
    def remove_selection_to_members(self):
        cmds.select([self._node] + cmds.ls(sl=True))
        mel.eval('dynamicConstraintMembership "remove";')
        self._components_iterator = cycle(self.components)

    def rename_node_from_components(self):
        parent = self.parent
        nice_name = self.nice_name
        new_node_name = cmds.rename(self._node, nice_name + 'Shape')
        cmds.rename(parent, nice_name)
        self._node = new_node_name

    def set_color(self, r, g, b):
        set_dynamic_constraint_color(self._node, r, g ,b)

    def set_type(self, constraint_type):
        attribute = self._node + '.' + TYPE_ATTR_NAME
        cmds.setAttr(attribute, constraint_type)
        apply_presets_on_dynamic_constraint(self._node, constraint_type)

    def switch(self):
        return cmds.setAttr(self._node + '.enable', not self.enable)


def apply_presets_on_dynamic_constraint(constraint_shape, constraint_type):
    """
    this method opening the json file linked to the constraint type
    it applying the presets
    """
    filename = DYNAMIC_CONTRAINT_TYPES[constraint_type]['preset_file']
    if filename is None:
        return logging.info(
            'No preset file available, applying presets skipped')

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), PRESETS_FOLDER, filename)

    with open(filepath, 'r') as preset_file:
        attributes = json.load(preset_file)

    for k, v in attributes.iteritems():
        if v is not None:
            cmds.setAttr(constraint_shape + '.' + k, v)


def add_and_set_constraint_type_attribute(constraint_shape, constraint_type):
    """
    this method add an enum attribute on the constraint shape. Containing the
    preset name used during the constraint creation
    """
    cmds.addAttr(
        constraint_shape, attributeType='enum',
        longName=TYPE_ATTR_NAME,
        niceName=TYPE_ATTR_LONGNAME,
        keyable=True,
        enumName=": ".join([t['name'] for t in DYNAMIC_CONTRAINT_TYPES]))

    attribute = constraint_shape + '.' + TYPE_ATTR_NAME
    cmds.setAttr(attribute, constraint_type)


@need_maya_selection
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


def get_dynamic_constraint_color(constraint_shape):
    '''
    smart function who return the nconstraint viewport color.
    It working as a normal transform override color except if color is
    undefined, it returns 25, 25, 125 
    '''
    parent = cmds.listRelatives(constraint_shape, parent=True)[0]

    if not cmds.getAttr(parent + '.overrideEnabled'):
        return 25, 25, 125

    if cmds.getAttr(parent + '.overrideRGBColors'):
        return [
            int(c * 255) for c in
            cmds.getAttr(parent + '.overrideColorRGB')[0]]

    else:
        color_index = cmds.getAttr(parent + '.overrideColor')
        if color_index > 0:
            return [
                int(c * 255) for c in
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


def set_dynamic_constraint_color(constraint_shape, r=0, g=0, b=0):
    '''
    this method is setting the overide color on the constraint parent
    '''
    r, g, b = [c / 255 for c in (r, g, b)]
    parent = cmds.listRelatives(constraint_shape, parent=True)[0]

    cmds.setAttr(parent + '.overrideEnabled', True)
    cmds.setAttr(parent + '.overrideRGBColors', True)
    cmds.setAttr(parent + '.overrideColorRGB', r, g, b)


def list_dynamic_constraints():
    nodes = cmds.ls(type='dynamicConstraint')
    return [DynamicConstraint(node) for node in nodes]
