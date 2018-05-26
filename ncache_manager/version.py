"""
This module is the cache manager file system librairies.
It provide utils and constants of the file system cache management

The module respect a nomenclature:
    version: a folder containing all file of a cache:
        - the maya .mcx: the cache datas
        - the maya .xml: the setting used
        - the infos.json: json contain interesting information (range, nodes)
    workspace: a folder containing lot of versions
"""


import os
import json

INFOS_FILENAME = 'infos.json'
VERSION_FOLDERNAME = 'version_{}'


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

    def _get_mcx_files(self):
        return [
            os.path.join(self.path, f) for f in os.listdir(self.path)
            if f.endswith('.mcx')]

    def _get_xml_files(self):
        return [
            os.path.join(self.path, f) for f in os.listdir(self.path)
            if f.endswith('.xml')]


def list_available_version_paths(workspace):
    versions = [
        os.path.join(workspace, folder)
        for folder in os.listdir(os.path.join(workspace))
        if os.path.exists(os.path.join(workspace, folder, INFOS_FILENAME))]
    return sorted(versions, key=lambda x: os.stat(x).st_ctime)


def list_available_versions(workspace):
    return [CacheVersion(p) for p in list_available_version_paths(workspace)]


def get_new_version_path(workspace):
    increment = 0
    version_path = os.path.join(
        workspace, VERSION_FOLDERNAME + str(increment).zfill(3))

    while os.path.exists(version_path):
        increment += 1
        version_path = os.path.join(
            workspace, VERSION_FOLDERNAME + str(increment).zfill(3))

    return version_path


def create_version(
        workspace=None, name=None, comment=None, nodes=None,
        start_frame=0, end_frame=0):

    directory = get_new_version_path(workspace)
    os.makedirs(directory)
    infos = dict(
        name=None, comment=None, nodes=None, start_frame=0, end_frame=0)
    infos_filepath = os.path.join(directory, INFOS_FILENAME)
    with open(infos_filepath, 'w') as infos_file:
        json.dump(infos_file, infos, indent=2, sort_keys=True)


def list_nodes_in_versions(versions):
    return list(set([version.infos['nodes'] for version in versions]))
