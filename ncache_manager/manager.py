

from maya import cmds


def connect_version(version, nodes=None):
    nodes = nodes or cmds.ls(type=('nCloth', 'hairSystem'))
    for node in nodes:
        for mcx_file in version.mcx_files:
            if node.replace(":", "_") in mcx_file:
                cmds.cacheFile(
                    attachFile=True,
                    fileName=os.path.basename(mcx_file),
                    directory=os.path.dirname(mcx_file))