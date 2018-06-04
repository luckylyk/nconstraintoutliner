"""
This module is the cache manager file system librairies.
It provide utils and constants of the file system cache management

The module respect a nomenclature:
    version: a folder containing all file of a cache:
        - the maya .mcx: the cache datas
        - the maya .xml: the setting used
        - the infos.json: json contain interesting information (range, nodes)
    workspace: a folder containing lot of versions

example of an infos.json structure
DEFAULT_INFOS = {
    'name': 'cache manager cache',
    'comment': 'comme ci comme ca',
    'nodes': {
        'nodename_1': {
            'range': (100, 150)}},
        'nodename_2': {
            'namespace': 'scene_saved_00'}}}
"""


import os
import json

INFOS_FILENAME = 'infos.json'
VERSION_FOLDERNAME = 'version_{}'
WORKSPACE_FOLDERNAME = 'caches'


class CacheVersion(object):
    def __init__(self, path):
        self.path = path
        if not os.path.exists(os.path.join(self.path, INFOS_FILENAME)):
            raise ValueError('Invalid version path')

        self.xml_files = self._get_xml_files()
        self.mcx_files = self._get_mcx_files()
        self.infos = self._load_infos()

    def _load_infos(self):
        with open(os.path.join(self.path, INFOS_FILENAME), 'r') as info_file:
            return json.load(info_file)

    def save_infos(self):
        with open(os.path.join(self.path, INFOS_FILENAME), 'w') as info_file:
            return json.dump(self.infos, info_file, indent=2)

    def _get_mcx_files(self):
        return [
            os.path.join(self.path, f) for f in os.listdir(self.path)
            if f.endswith('.mcx')]

    def _get_xml_files(self):
        return [
            os.path.join(self.path, f) for f in os.listdir(self.path)
            if f.endswith('.xml')]

    def set_range(self, nodes=None, start_frame=None, end_frame=None):
        assert start_frame or end_frame
        if nodes:
            for node in nodes:
                self.infos['nodes'][node]['range'] = start_frame, end_frame
        self.save_infos()

    def set_comment(self, comment):
        self.infos['comment'] = comment
        self.save_infos()

    def set_name(self, name):
        self.infos['name'] = name
        self.save_infos()


def list_available_cacheversion_paths(workspace):
    versions = [
        os.path.join(workspace, folder)
        for folder in os.listdir(os.path.join(workspace))
        if os.path.exists(os.path.join(workspace, folder, INFOS_FILENAME))]
    return sorted(versions, key=lambda x: os.stat(x).st_ctime)


def list_available_cacheversions(workspace):
    return [
        CacheVersion(p) for p in list_available_cacheversion_paths(workspace)]


def get_new_cacheversion_path(workspace):
    increment = 0
    cacheversion_path = os.path.join(
        workspace, VERSION_FOLDERNAME.format(str(increment).zfill(3)))

    while os.path.exists(cacheversion_path):
        increment += 1
        cacheversion_path = os.path.join(
            workspace, VERSION_FOLDERNAME.format(str(increment).zfill(3)))

    return cacheversion_path


def create_workspace_folder(path):
    path = os.path.join(path, WORKSPACE_FOLDERNAME)
    os.mkdir(path)
    return path


def create_cacheversion(
        workspace=None, name=None, comment=None, nodes=None,
        start_frame=0, end_frame=0):

    directory = get_new_cacheversion_path(workspace)
    os.makedirs(directory)

    nodes_infos = {}
    for node in nodes:
        namespace, nodename = split_namespace_nodename(node)
        if nodename in nodes_infos:
            raise KeyError("{} is not unique")
        nodes_infos[nodename] = {
            'range': (start_frame, end_frame),
            'namespace': namespace}

    infos = dict(
        name=name, comment=comment, nodes=nodes_infos,
        start_frame=0, end_frame=0)

    infos_filepath = os.path.join(directory, INFOS_FILENAME)
    with open(infos_filepath, 'w') as infos_file:
        json.dump(infos_file, infos, indent=2, sort_keys=True)

    return CacheVersion(directory)


def list_nodes_in_cacheversions(versions):
    return list(set([version.infos['nodes'].keys() for version in versions]))


def version_contains_node(version, node, same_namespace=False):
    namespace, nodename = split_namespace_nodename(node)
    if not same_namespace:
        return nodename in version.infos['nodes']

    if nodename not in version.infos['nodes']:
        return False
    return version.infos['nodes'][nodename]['namespace'] == namespace


def split_namespace_nodename(node):
    names = node.split(":")
    if len(names) > 1:
        return names[0], names[1]
    else:
        return None, names[0]
        
if __name__ == "__main__":
    workspace = 'c:/test/cache/'
    cacheversion = create_cacheversion(
        workspace=workspace,
        name="Cache",
        comment="salut",
        nodes=['truc'],
        start_frame=1.0,
        end_frame=150.0)

    cacheversion.set_range(start_frame=1.0, end_frame=100.0)