from functools import wraps
from maya import cmds


def preserve_selection(func):
    '''
    this decorator save your maya selection before execute the
    decorated function. And reselect it when it's executed. 
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        selection = cmds.ls(sl=True)
        result = func(*args, **kwargs)
        cmds.select(selection)
        return result
    return wrapper


def selection_required(func):
    '''
    this decorator check check if node is selected and return a cmds.error
    if nothing is selected
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not cmds.ls(selection=True):
            return cmds.warning('Select at least one node')
        else:
            return func(*args, **kwargs)
    return wrapper


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
