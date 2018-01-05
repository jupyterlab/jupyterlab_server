"""Test the kernels service API."""
import json

from jupyterlab_launcher.tests.utils import LabTestBase, APITester


class WorkspacesAPI(APITester):
    """Wrapper for workspaces REST API requests"""

    url = 'lab/api/workspaces'

    def get(self, section_name):
        return self._req('GET', section_name)

    def put(self, section_name, body):
        return self._req('PUT', section_name, json.dumps(body))


class WorkspacesAPITest(LabTestBase):
    """Test the workspaces web service API"""

    def setUp(self):
        self.workspaces_api = WorkspacesAPI(self.request)

    def test_get(self):
        id = 'foo'
        data = self.workspaces_api.get(id).json()
        assert data['metadata']['id'] == id

    def test_put(self):
        id = 'foo'
        data = self.workspaces_api.get(id).json()
        resp = self.workspaces_api.put(id, data)
        assert resp.status_code == 204
