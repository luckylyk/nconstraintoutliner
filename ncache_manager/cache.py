
from maya import cmds, mel


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


def list_connected_cachenodes(nodes=None):
    nodes = nodes or cmds.ls(type=('nCloth', 'hairSystem'))
    return cmds.listConnections(nodes, type='cacheFile')


def reconnect_all_cachenodes(connections):
    for attribute, connected in connections.iteritems():
        cmds.connectAttr(attribute, connected)


def record_ncache(
        nodes=None, start_frame=0, end_frame=100, output_folder=None):
    '''
    this method is a wrap around the mel command doCreateNclothCache
    it force an cache with one cache per geometry (containing all frame).
    '''
    nodes = nodes or cmds.ls(type=('nCloth', 'hairSystem'))
    output_folder = output_folder or ''

    cmds.select(nodes)
    command = (
        'doCreateNclothCache 5 {{ "0", "{start_frame}", "{end_frame}",'
        '"OneFile", "1", "{output_folder}", "1", "", "0", "replace", "1", "1", '
        '"1", "0", "1","mcx"}}').format(
            start_frame=start_frame,
            end_frame=end_frame,
            output_folder=output_folder)

    cache_nodes = mel.eval(command)
    return cache_nodes