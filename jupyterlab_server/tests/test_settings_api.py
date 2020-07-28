"""Test the kernels service API."""
import json
import os
import shutil
from strict_rfc3339 import rfc3339_to_timestamp

from jupyterlab_server.tests.utils import LabTestBase, APITester
from ..servertest import assert_http_error

from .utils import maybe_patch_ioloop

maybe_patch_ioloop()

class SettingsAPI(APITester):
    """Wrapper for settings REST API requests"""

    url = 'lab/api/settings'

    def get(self, schema_name=''):
        return self._req('GET', schema_name)

    def put(self, schema_name, body):
        return self._req('PUT', schema_name, json.dumps(body))


class SettingsAPITest(LabTestBase):
    """Test the settings web service API"""

    def setUp(self):
        # Copy the schema files.
        src = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'schemas',
            '@jupyterlab')
        dst = os.path.join(self.lab_config.schemas_dir, '@jupyterlab')
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

        # Copy the overrides file.
        src = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'app-settings',
            'overrides.json')
        dst = os.path.join(self.lab_config.app_settings_dir, 'overrides.json')
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copyfile(src, dst)
        self.settings_api = SettingsAPI(self.request)

    def test_get(self):
        id = '@jupyterlab/apputils-extension:themes'
        data = self.settings_api.get(id).json()
        schema = data['schema']

        assert data['id'] == id
        # Check that overrides.json file is respected.
        assert schema['properties']['theme']['default'] == 'JupyterLab Dark'
        assert 'raw' in data

    def test_get_bad(self):
        with assert_http_error(404):
            self.settings_api.get('foo')

    def test_listing(self):
        ids = [
            '@jupyterlab/apputils-extension:themes',
            '@jupyterlab/codemirror-extension:commands',
            '@jupyterlab/shortcuts-extension:plugin',
            '@jupyterlab/translation-extension:plugin',
        ]
        versions = ['N/A', 'N/A', 'test-version']

        response = self.settings_api.get('').json()
        response_ids = [item['id'] for item in response['settings']]
        response_versions = [item['version'] for item in response['settings']]

        assert set(response_ids) == set(ids)
        assert set(response_versions) == set(versions)
        last_modifieds = [item['last_modified'] for item in response['settings']]
        createds = [item['created'] for item in response['settings']]
        assert {None} == set(last_modifieds + createds)

    def test_patch(self):
        id = '@jupyterlab/shortcuts-extension:plugin'

        assert self.settings_api.put(id, dict()).status_code == 204
        data = self.settings_api.get(id).json()
        first_created = rfc3339_to_timestamp(data['created']), data
        first_modified = rfc3339_to_timestamp(data['last_modified']), data

        assert self.settings_api.put(id, dict()).status_code == 204
        data = self.settings_api.get(id).json()
        second_created = rfc3339_to_timestamp(data['created']), data
        second_modified = rfc3339_to_timestamp(data['last_modified']), data

        assert first_created <= second_created
        assert first_modified < second_modified

        listing = self.settings_api.get('').json()['settings']
        list_data = [item for item in listing if item['id'] == id][0]
        assert list_data['created'] == data['created']
        assert list_data['last_modified'] == data['last_modified']


    def test_patch_wrong_id(self):
        with assert_http_error(404):
            self.settings_api.put('foo', dict())

    def test_patch_bad_data(self):
        id = '@jupyterlab/codemirror-extension:commands'

        with assert_http_error(400):
            self.settings_api.put(id, dict(keyMap=10))
