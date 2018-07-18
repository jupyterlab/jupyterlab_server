"""Test the kernels service API."""
import json
import os
import shutil

from jupyterlab_launcher.tests.utils import LabTestBase, APITester


class WorkspacesAPI(APITester):
    """Wrapper for workspaces REST API requests"""

    url = 'lab/api/workspaces'

    def delete(self, section_name):
        return self._req('DELETE', section_name)

    def get(self, section_name=''):
        return self._req('GET', section_name)

    def put(self, section_name, body):
        return self._req('PUT', section_name, json.dumps(body))


class WorkspacesAPITest(LabTestBase):
    """Test the workspaces web service API"""

    def setUp(self):
        data = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'workspaces')
        for item in os.listdir(data):
            src = os.path.join(data, item)
            dst = os.path.join(self.lab_config.workspaces_dir, item)
            if not os.path.exists(dst):
                shutil.copy(src, self.lab_config.workspaces_dir)
        self.workspaces_api = WorkspacesAPI(self.request)

    def test_delete(self):
        orig = 'foo'
        copy = 'baz'
        data = self.workspaces_api.get(orig).json()
        data['metadata']['id'] = copy

        assert self.workspaces_api.put(copy, data).status_code == 204
        assert self.workspaces_api.delete(copy).status_code == 204

    def test_get(self):
        id = 'foo'

        assert self.workspaces_api.get(id).json()['metadata']['id'] == id

    def test_listing(self):
        listing = set(['foo', 'bar'])

        assert set(self.workspaces_api.get().json()['workspaces']) == listing

    def test_put(self):
        id = 'foo'
        data = self.workspaces_api.get(id).json()

        assert self.workspaces_api.put(id, data).status_code == 204
