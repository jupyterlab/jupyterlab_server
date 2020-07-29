"""Test the kernels service API."""

import json
import os
import shutil

from strict_rfc3339 import rfc3339_to_timestamp

from jupyterlab_server.tests.utils import LabTestBase, APITester
from notebook.tests.launchnotebook import assert_http_error

from .utils import maybe_patch_ioloop, big_unicode_string

maybe_patch_ioloop()


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
        metadata = self.workspaces_api.get(id).json()['metadata']
        assert metadata['id'] == id
        assert rfc3339_to_timestamp(metadata['created'])
        assert rfc3339_to_timestamp(metadata['last_modified'])

    def test_get_non_existant(self):
        id = 'baz'
        ws = self.workspaces_api.get(id).json()
        assert 'created' not in ws['metadata']
        assert 'last_modified' not in ws['metadata']

    def test_listing(self):
        # ID fields are from workspaces/*.jupyterlab-workspace
        listing = set(['foo', 'f/o/o/'])
        output = set(self.workspaces_api.get().json()['workspaces']['ids'])
        assert output == listing

    def test_listing_dates(self):
        values = self.workspaces_api.get().json()['workspaces']['values']
        times = sum(
            [
                [ws['metadata'].get('last_modified'), ws['metadata'].get('created')]
                for ws in values
            ],
            []
        )
        assert None not in times
        [rfc3339_to_timestamp(t) for t in times]

    def test_put(self):
        id = 'foo'
        data = self.workspaces_api.get(id).json()
        data["metadata"]["big-unicode-string"] = big_unicode_string[::-1]
        assert self.workspaces_api.put(id, data).status_code == 204
        first_metadata = self.workspaces_api.get(id).json()["metadata"]
        first_created = rfc3339_to_timestamp(first_metadata['created'])
        first_modified = rfc3339_to_timestamp(first_metadata['last_modified'])

        assert self.workspaces_api.put(id, data).status_code == 204
        second_metadata = self.workspaces_api.get(id).json()["metadata"]
        second_created = rfc3339_to_timestamp(second_metadata['created'])
        second_modified = rfc3339_to_timestamp(second_metadata['last_modified'])

        assert first_created <= second_created
        assert first_modified < second_modified

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
