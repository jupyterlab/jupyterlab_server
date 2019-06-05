"""Test the kernels service API."""
import json
import os
import shutil

from jupyterlab_server.tests.utils import LabTestBase, APITester
from notebook.tests.launchnotebook import assert_http_error


class WorkspacesAPI(APITester):
    """Wrapper for workspaces REST API requests"""

    url = 'lab/api/workspaces'

    def delete(self, space_name):
        return self._req('DELETE', space_name)

    def get(self, space_name=''):
        return self._req('GET', space_name)

    def put(self, space_name, body):
        return self._req('PUT', space_name, json.dumps(body))


class WorkspacesAPITest(LabTestBase):
    """Test the workspaces web service API"""

    def setUp(self):
        data = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'workspaces')
        for item in os.listdir(data):
            src = os.path.join(data, item)
            dst = os.path.join(self.lab_config.workspaces_dir, item)
            if os.path.exists(dst):
                os.remove(dst)
            shutil.copy(src, self.lab_config.workspaces_dir)
        self.workspaces_api = WorkspacesAPI(self.request)

    def test_delete(self):
        orig = 'f/o/o/'
        copy = 'baz'
        data = self.workspaces_api.get(orig).json()
        data['metadata']['id'] = copy
        assert self.workspaces_api.put(copy, data).status_code == 204
        assert self.workspaces_api.delete(copy).status_code == 204

    def test_get(self):
        id = 'foo'
        assert self.workspaces_api.get(id).json()['metadata']['id'] == id

    def test_listing(self):
        # ID fields are from workspaces/*.jupyterlab-workspace
        listing = set(['foo', 'f/o/o/'])
        output = set(self.workspaces_api.get().json()['workspaces']['ids'])
        assert output == listing

    def test_put(self):
        id = 'foo'
        data = self.workspaces_api.get(id).json()
        assert self.workspaces_api.put(id, data).status_code == 204

    def test_bad_put(self):
        orig = 'foo'
        copy = 'bar'
        data = self.workspaces_api.get(orig).json()
        with assert_http_error(400):
            self.workspaces_api.put(copy, data)

    def test_blank_put(self):
        orig = 'foo'
        data = self.workspaces_api.get(orig).json()
        with assert_http_error(400):
            self.workspaces_api.put('', data)
