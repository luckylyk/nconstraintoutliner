
import os
import json


INFOS_FILENAME = 'infos.json'

class CacheVersion(object):
    def __init__(self, folder):
        self.folder = folder
        if not os.path.exists(os.path.join(self.folder, INFOS_FILENAME)):
            raise ValueError('Invalid version path')

        self.xml_files = self._get_xml_files()
        self.mcx_files = self._get_mcx_files()
        self.infos = self._load_infos()

    def _load_infos(self):
        with open(os.path.join(self.folder, INFOS_FILENAME), 'r') as info_file:
            return json.load(info_file)

    def _get_mcx_files(self):
        return [
            os.path.join(self.folder, f) for f in os.listdir(self.folder)
            if f.endswith('.mcx')]

    def _get_xml_files(self):
        return [
            os.path.join(self.folder, f) for f in os.listdir(self.folder)
            if f.endswith('.xml')]
