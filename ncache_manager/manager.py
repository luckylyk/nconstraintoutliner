

import os
from maya import cmds
from .version import create_cacheversion
from .cache import import_ncache


class CacheManager(object):
    def __init__(self):
        self.workspace = os.path.expanduser("~")


def connect_cacheversion(version, nodes=None):
    nodes = nodes or cmds.ls(type=('nCloth', 'hairSystem'))
    for node in nodes:
        for mcx_file in version.mcx_files:
            if node.replace(":", "_") in mcx_file:
                cmds.cacheFile(
                    attachFile=True,
                    fileName=os.path.basename(mcx_file),
                    directory=os.path.dirname(mcx_file))


