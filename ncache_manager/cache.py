
from maya import cmds, mel


def list_connected_cachefiles(nodes=None):
    '''
    :nodes: one or list of dyna,ic nodes as string ('hairSystem' and 'nCloth')
    '''
    nodes = nodes or cmds.ls(type=('nCloth', 'hairSystem'))
    cachenodes = cmds.listConnections(nodes, type='cacheFile')
    if cachenodes:
        return list(set(cachenodes))


def list_connected_cacheblends(nodes=None):
    '''
    :nodes: one or list of dyna,ic nodes as string ('hairSystem' and 'nCloth')
    '''
    nodes = nodes or cmds.ls(type=('nCloth', 'hairSystem'))
    blendnodes = cmds.listConnections(nodes, type='cacheBlend')
    if blendnodes:
        return list(set(blendnodes))


def get_connected_cachenode(node):
    assert cmds.nodeType(node) in ('nCloth', 'hairSystem')
    cachenodes = (
        (list_connected_cachefiles('nClothShape2') or []) +
        (list_connected_cacheblends('nClothShape2') or []))

    if not cachenodes:
        return
    elif len(cachenodes) > 1:
        raise ValueError(
            "More than 1 cache node is connected to {}".format(node))
    return cachenodes[0]


def disconnect_cachenodes(nodes=None):
    '''
    This method disconnect all cache node and return all connected nodes
    as dict.
    :nodes: one or list of dynamic nodes as string ('hairSystem' and 'nCloth')
    '''
    cachenodes = (
        (list_connected_cachefiles(nodes) or []) +
        (list_connected_cacheblends(nodes) or []))
    attributes = "inRange", "outCacheData"

    # retrieve connections and check the cachenodes setup
    try:
        connections = {}
        for cachenode in cachenodes:
            for attribute in attributes:
                inplug, outplug = cmds.listConnections(
                    cachenode + "." + attribute, plugs=True, connections=True)
                connections[inplug.split(".")[0]] = outplug.split(".")[0]
                cmds.disconnectAttr(inplug, outplug)
    except ValueError:
        raise ValueError(
            'A cacheBlend or a cacheFile node have multiple connections.\n'
            'This is not supported by the cache manager.\n'
            'Please remove them before to continue.')

    return connections


def reconnect_cachenodes(connections, nodetypes=None):
    for cachenode, node in connections.iteritems():
        cachefile = get_connected_cachenode(node)
        if not cachefile:
            attach_cachenode(cachenode, node)
            continue

        assert cmds.nodeType(cachefile) == 'cacheFile'
        if cmds.nodeType(cachenode) == 'cacheBlend':
            attach_cachefile_to_cacheblend(cachefile, cachenode)
            disconnect_cachenodes(node)
            attach_cachenode(cachenode, node)

        elif cmds.nodeType(cachenode) == 'cacheFile':
            cacheblend = cmds.createNode('cacheBlend')
            attach_cachefile_to_cacheblend(cachefile, cacheblend)
            disconnect_cachenodes(node)
            attach_cachenode(cacheblend, node)


def find_free_cachedata_channel_index(cacheblend):
    i = 0
    while cmds.listConnections(cacheblend + '.cacheData[{}].start'.format(i)):
        i += 1
    return i


def connect_attributes(outnode, innode, connections):
    """
    Connect a series of attribute from two nodes
    """
    for out_attribute, in_attribute in connections.iteritems():
        cmds.connectAttr(
            '{}.{}'.format(outnode, out_attribute),
            '{}.{}'.format(innode, in_attribute))


def attach_cachefile_to_cacheblend(cachefile, cacheblend):
    i = find_free_cachedata_channel_index(cacheblend)
    connections = {
        'end': 'cacheData[{}].end'.format(i),
        'inRange': 'cacheData[{}].range'.format(i),
        'start': 'cacheData[{}].start'.format(i),
        'outCacheData[0]': 'inCache[0].vectorArray[{}]'.format(i)}
    connect_attributes(cachefile, cacheblend, connections)


def attach_cachenode(cachenode, node):
    connections = {
        'outCacheData[0]': 'positions',
        'inRange': 'playFromCache'}
    connect_attributes(cachenode, node, connections)


def record_ncache(
        nodes=None, start_frame=0, end_frame=100, output=None, behavior=0):
    '''
    this method is a wrap around the mel command doCreateNclothCache
    it force an cache with one cache per geometry (containing all frame).
    :behavior: as int
        0: replace all old connected cachenodes and blendnodes
        1: replace all old connected cachenodes but add new cache in blendnodes
        2: blend all existing cachenodes with new cache
    '''
    nodes = nodes or cmds.ls(type=('nCloth', 'hairSystem'))
    output = output or ''

    if behavior is 0:
        cmds.delete(list_connected_cachefiles(nodes))
        cmds.delete(list_connected_cacheblends(nodes))
    elif behavior is 1:
        cmds.delete(list_connected_cachefiles(nodes))
        connections = disconnect_cachenodes(nodes)
    elif behavior is 2:
        connections = disconnect_cachenodes(nodes)

    cmds.select(nodes)
    command = (
        'doCreateNclothCache 5 {{ "0", "{start_frame}", "{end_frame}",'
        '"OneFile", "1", "{output}", "1", "", "0", "replace", "1", "1", '
        '"1", "0", "1","mcx"}}').format(
            start_frame=start_frame,
            end_frame=end_frame,
            output=output)
    print command
    cache_nodes = mel.eval(command)

    if behavior:
        reconnect_cachenodes(connections)

    return cache_nodes