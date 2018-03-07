
from maya import cmds


def disconnect_cachenodes(cachenodes=None):
    '''
    This method disconnect all cache node and return all connections
    disconnected as dict
    '''
    cachenodes = cachenodes or cmds.ls(type="cacheFile")
    attributes = "inRange", "outCacheData"
    attributes = {
        attribute: connected for (attribute, connected) in [
            cmds.listConnections(
                cachenode + "." + attribute, plugs=True, connections=True)
            for cachenode in cachenodes for attribute in attributes]}

    for attribute, connected in attributes.iteritems():
         cmds.disconnectAttr(attribute, connected)

    return attributes


def reconnect_all_cachenodes(connections):
    for attribute, connected in connections.iteritems():
        cmds.connectAttr(attribute, connected)
