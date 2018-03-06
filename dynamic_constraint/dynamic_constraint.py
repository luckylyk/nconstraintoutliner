
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
from maya_libs.selection.context_managers import MayaSelectionManager
from maya_libs.selection.decorators import (
    preserve_selection, selection_required)

TYPE_ATTR_NAME = 'constraintType'
TYPE_ATTR_LONGNAME = 'Dynamic Constraint Type'

PRESETS_FOLDER = 'presets'
DYNAMIC_CONTRAINT_TYPES = [
    {
        'name': 'undefined',
        'type': 'undefined',
        'short': 'UND',
        'preset_file': None
    },
    {
        'name': 'transform',
        'type': 'transform',
        'short': 'TRS',
        'preset_file': 'transform.json'
    },
    {
        'name': 'component to component',
        'type': 'pointToPoint',
        'short': 'CTC',
        'preset_file': 'component_to_component.json'
    },
    {
        'name': 'point to surface',
        'type': 'pointToSurface',
        'short': 'PTS',
        'preset_file': 'point_to_surface.json'
    },

    {
        'name': 'slide on surface',
        'type': 'slideOnSurface',
        'short': 'SOS',
        'preset_file': 'slide_on_surface.json'
    },

    {
        'name': 'weld',
        'type': 'weldBorders',
        'short': 'WLD',
        'preset_file': 'weld_adjacent_border.json'
    },

    {
        'name': 'exclude collide',
        'type': 'collisionExclusion',
        'short': 'EXC',
        'preset_file': 'exclude_collider_pairs.json'
    },

    {
        'name': 'disable collision',
        'type': 'disableCollision',
        'short': 'DIS',
        'preset_file': 'disable_collision.json'
    },
]


class DynamicConstraint(object):
    """
    This class is a model of nConstraint with a custom attribute who save the
    creation preset and a name auto-generated in the outliner.

    this object can be instancied around an existing node:
    dynamic_constraint = DynamicConstraint(nodename='existing_nConstraintShape')
    or instancied creating a new constraint node in maya:
    dynamic_constraint = DynamicConstraint.create(DynamicConstraint.TRANSFORM)
    """
    UNDEFINED = 0
    TRANSFORM = 1
    COMPONENT_TO_COMPONENT = 2
    POINT_TO_SURFACE = 3
    SLIDE_ON_SURFACE = 4
    WELD = 5
    EXCLUDE_COLLIDE = 6
    DISABLE_COLLIDE = 7

    def __init__(self, nodename=None):
        self._node = nodename
        self._components = None
        self._components_iterator = None
        self._members = None
        self._type = None
        self._nice_name = None

    @staticmethod
    @selection_required
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
    def components_iterator(self):
        if self._components_iterator is None:
            self._components_iterator = cycle(self.components)
        return self._components_iterator

    @property
    def components(self):
        ''' return objects members parent's '''
        if self._components is None:
            self._components = get_dynamic_constraint_components(self._node)
            self._components_iterator = None
        return self._components

    @property
    def enable(self):
        return cmds.getAttr(self._node + '.enable')

    @property
    def is_well_named(self):
        return self.parent == self.nice_name

    @property
    def nice_name(self):
        if self._nice_name is None:
            self._nice_name = get_dynamic_constraint_nice_name(self._node)
        return self._nice_name

    @property
    def node(self):
        return self._node

    @property
    def parent(self):
        return cmds.listRelatives(self._node, parent=True)[0]

    @property
    def type(self):
        if self._type is None:
            self._type = get_constraint_type(self._node)
        return self._type

    @property
    def type_name(self):
        return DYNAMIC_CONTRAINT_TYPES[self.type]['name']

    @preserve_selection
    @selection_required
    def add_selection_to_members(self):
        cmds.select([self._node] + cmds.ls(sl=True))
        mel.eval('dynamicConstraintMembership "add";')
        self._components = None
        self._components_iterator = None

    def paint_constraint_strength_map_on_components(self):
        component = self.components_iterator.next()
        cmds.select([self._node, component])
        cmd = (
            'setNComponentMapType("strength", 1);'
            'artAttrNComponentToolScript 4 strength;')
        mel.eval(cmd)

    def select_members(self):
        cmds.select(self._node)
        mel.eval('dynamicConstraintMembership "select";')

    @preserve_selection
    @selection_required
    def remove_selection_to_members(self):
        cmds.select([self._node] + cmds.ls(sl=True))
        mel.eval('dynamicConstraintMembership "remove";')
        self._components = None
        self._components_iterator = None

    def rename_node_from_components(self):
        parent = self.parent
        nice_name = self.nice_name
        new_node_name = cmds.rename(self._node, nice_name + 'Shape')
        cmds.rename(parent, nice_name)
        self._node = new_node_name
        self._nice_name = None

    def select(self, add=True):
        cmds.select(self._node)

    def set_color(self, r, g, b):
        set_dynamic_constraint_color(self._node, r, g ,b)

    def set_color_from_dialogbox(self):
        cmds.colorEditor(rgb=[c / 255.0 for c in self.color])
        if not cmds.colorEditor(query=True, result=True):
            return
        r, g, b = [
            int(c * 255) for c in cmds.colorEditor(query=True, rgb=True)]
        self.set_color(r, g, b)

    def set_type(self, constraint_type):
        attribute = self._node + '.' + TYPE_ATTR_NAME
        old_type = self.type
        cmds.setAttr(attribute, constraint_type)
        self._type = constraint_type
        # if the constraint if undefined, it's not changing the preset
        # to avoid a change from a tweaked constraint done with the maya tools
        if old_type == DynamicConstraint.UNDEFINED:
            return
        apply_presets_on_dynamic_constraint(self._node, constraint_type)

    def switch(self):
        cmds.setAttr(self._node + '.enable', not self.enable)
        return self.enable


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


@selection_required
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
    constraint_type_name = DYNAMIC_CONTRAINT_TYPES[constraint_type]['type']
    constraint_node = mel.eval(
        'createNConstraint {} 0;'.format(constraint_type_name))
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

    color_index = cmds.getAttr(parent + '.overrideColor')
    if color_index > 0:
        return [
            int(c * 255) for c in
            cmds.colorIndex(color_index, query=True)]
    else:
        return 25, 25, 125


@preserve_selection
def get_dynamic_constraint_components(constraint_shape):
    '''
    return the nconstraint components list as list of strings.
    '''
    cmds.select(constraint_shape)
    try:  # this maya command can crash if it can't find any component
        mel.eval('dynamicConstraintMembership "select";')
    except:
        return []
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
        name = type_name + '_' + '_to_'.join(components)
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
            TYPE_ATTR_NAME, node=constraint_shape, exists=True):
        add_and_set_constraint_type_attribute(
            constraint_shape, DynamicConstraint.UNDEFINED)

    attribute = constraint_shape + '.' + TYPE_ATTR_NAME
    return cmds.getAttr(attribute)


def set_dynamic_constraint_color(constraint_shape, r=0, g=0, b=0):
    '''
    this method is setting the overide color on the constraint parent
    '''
    r, g, b = [c / 255.0 for c in (r, g, b)]
    parent = cmds.listRelatives(constraint_shape, parent=True)[0]

    cmds.setAttr(parent + '.overrideEnabled', True)
    cmds.setAttr(parent + '.overrideRGBColors', True)
    cmds.setAttr(parent + '.overrideColorRGB', r, g, b)


def list_dynamic_constraints(types=None, components=None):
    '''
    this method list the dynamic constraint in the current maya scene.
    if types or components is specified, it will filter dynamic constraints
    :types: if the dynmic contraint 
    '''
    nodes = cmds.ls(type='dynamicConstraint')
    dynamic_constraints = [DynamicConstraint(node) for node in nodes]

    if types is not None:
        dynamic_constraints = [
            dc for dc in dynamic_constraints if dc.type in types]

    if components is not None:
        dynamic_constraints = [
            dc for dc in dynamic_constraints
            if any([c in components for c in dc.components])]

    return dynamic_constraints


def list_dynamic_constraints_components():
    '''
    this is returning all components nodes linked to a dynamic constraint
    '''
    dynamic_constraints = list_dynamic_constraints()
    return list(set([c for dc in dynamic_constraints for c in dc.components]))


def get_dynamic_constraint_members(constraint):
    members = []
    components = cmds.listConnections(constraint, type="nComponent")
    if not components:
        return cmds.warning('{} have no component'.format(constraint))

    for component in components:
        mesh = get_component_mesh(component)
        if not mesh:
            continue

        elements = cmds.getAttr(component + '.elements')
        if elements == 0:
            set_connected = get_set_from_component(component)
            if not set_connected:
                continue
            set_members = cmds.sets(set_connected, query=True)
            if not set_members:
                continue

            buffer = set_members[0].split('.')
            if len(buffer) <= 1:
                continue

            set_object = buffer[0]
            for index in range(len(set_members)):
                set_members[index] = set_members[index].replace(
                    set_object, mesh)
            members += set_members
            continue

        component_type = cmds.getAttr(component + ".componentType")
        if not elements:
            indices = cmds.getAttr(component + ".componentIndices")[0]
        total_elements = [0]
        if component_type == 0:
            continue

        elif component_type == 6:
            members.append(mesh)
            continue

        elif component_type == 2:
            if cmds.nodeType(mesh) == "nParticle":
                attr = mesh + ".pt"
                if elements == 2:
                    total_elements[0] = cmds.getAttr(mesh +".count")
            else:
                attr = mesh + ".vtx"
                if elements == 2:
                    total_elements = cmds.polyEvaluate(mesh, v=True)

        elif component_type == 3:
            mesh + ".e"
            if elements == 2:
                total_elements = cmds.polyEvaluate(mesh, e=True)

        elif component_type == 4:
            mesh + ".f"
            if elements == 2:
                total_elements = cmds.polyEvaluate(mesh, f=True)

        else:
            cmds.warning("unsupported component type")

        if elements == 2:
            if total_elements[0]:
                members.append(attr + "[0:" + (total_elements[0] - 1) + "]")
        else:
            members += get_selection_array(attr, indices)
    return members


def get_set_from_component(component):
    con = cmds.listConnections(component + ".componentGroupId")
    if con:
        con = cmds.listConnections(con[0] + ".message", type="objectSet")
    return con or ""


def get_selection_array(attribute, indices):
    selection_array = []
    for indice in indices:
        selection_array.append("{}[{}]".format(attribute, indice))
    return selection_array


def get_component_mesh(component):
    cons = cmds.listConnections(component, type="nBase", sh=1)
    if not cons:
        return cmds.warning("{} have no cons".format(component))

    if cmds.nodeType(cons[0]) == "nParticle":
        return cons[0]

    mesh = find_type_in_history(
        cons[0], nodetype="mesh", future=True, past=False)
    shape_visible = all([
        cmds.getAttr(mesh + ".visibility"),
        cmds.getAttr(mesh + ".intermediateObject")])

    if mesh == "" or not shape_visible:
        mesh = find_type_in_history(
            cons[0], nodetype="mesh", future=False, past=True)

    if mesh == "":
        return cmds.warning("No visible mesh found")

    return mesh

def find_type_in_history(node, nodetype, past=True, future=True):
    if not past and not future:
        return ""

    elif not past or not future:
        history = cmds.listHistory(node, f=future, bf=True, af=True)
        objects = cmds.ls(history, type=nodetype)
        if objects:
            return objects[0]

    elif past and future:
        past = cmds.listHistory(node, f=0, bf=True, af=True)
        future = cmds.listHistory(node, f=1, bf=True, af=True)
        past_objects = cmds.ls(past, type=nodetype)
        future_objects = cmds.ls(future, type=nodetype)
        if past_objects:
            if not future_objects:
                return past_objects[0]

            min=max([len(future_objects), len(past_objects)])
            for index in range(min):
                if past[index] == past_objects[0]:
                    return past_objects[0]
                if future[index] == future_objects[0]:
                    return future_objects[0]

        elif future_objects:
            return future_objects[0]

    return ""
