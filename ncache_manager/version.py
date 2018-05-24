
import os
import json

from maya import cmds

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


def list_available_version_paths(path):
    versions = [
        os.path.join(path, folder)
        for folder in os.listdir(os.path.join(path, folder))
        if os.path.exists(os.path.join(path, folder, INFOS_FILENAME))]
    return sorted(versions, key=lambda x: os.stat(x).st_ctime)


def list_available_versions(path):
    return [CacheVersion(p) for p in list_available_version_paths(path)]


def get_new_version_path(path):
    increment = 0
    version_path = os.path.join(
        path, VERSION_FOLDERNAME + str(increment).zfill(3))

    while os.path.exists(version_path):
        increment += 1
        version_path = os.path.join(
            path, VERSION_FOLDERNAME + str(increment).zfill(3))

    return version_path


def create_version(
        path=None, name=None, comment=None, nodes=None,
        start_frame=0, end_frame=0):

    os.makedirs(path)
    infos = dict(
        name=None, comment=None, nodes=None, start_frame=0, end_frame=0)

    with open(path, 'w') as version_file:
        json.dump(version_file, infos, indent=2, sort_keys=True)


def connect_version(version, nodes=None):
    nodes = nodes or cmds.ls(type=('nCloth', 'hairSystem'))
    for node in nodes:
        for mcx_file in version.mcx_files:
            if node.replace(":", "_") in mcx_file:
                cmds.cacheFile(
                    attachFile=True,
                    fileName=os.path.basename(mcx_file),
                    directory=os.path.dirname(mcx_file))


def list_nodes_in_versions(versions):
    return list(set([version.infos['nodes'] for version in versions]))
