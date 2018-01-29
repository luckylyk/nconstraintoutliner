

from maya import cmds


class MayaSelectionManager(object):
    """
    This context manager save the current selection and retrieve selection
    on exit.

    @nodes list of string representing nodes. Entering in the context manager,
    it select the nodes if the argument is specified
    """

    def __init__(self, nodes=None):
        self.nodes = nodes

    def __enter__(self):
        self.old_selection = cmds.ls(selection=True)
        if self.nodes:
            cmds.select(self.nodes)

    def __exit__(self, type, value, traceback):
        cmds.select(self.old_selection)  # retrieve original selection
