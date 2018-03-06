
from maya import cmds


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
