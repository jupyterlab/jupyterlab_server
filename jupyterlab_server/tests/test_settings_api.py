"""Test the Settings service API.
"""

import pytest, json

async def test_get(fetch, labserverapp):
    id = '@jupyterlab/apputils-extension:themes'
    r = await fetch('/lab/api/settings/{}'.format(id))
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    assert data['id'] == id
    schema = data['schema']
    # Check that overrides.json file is respected.
    assert schema['properties']['theme']['default'] == 'JupyterLab Dark'
    assert 'raw' in res

"""
    def test_get_bad(self):
        with assert_http_error(404):
            self.settings_api.get('foo')

    def test_listing(self):
        ids = [
            '@jupyterlab/apputils-extension:themes',
            '@jupyterlab/codemirror-extension:commands',
            '@jupyterlab/shortcuts-extension:plugin'
        ]
        versions = ['N/A', 'N/A', 'test-version']
        response = self.settings_api.get('').json()
        response_ids = [item['id'] for item in response['settings']]
        response_versions = [item['version'] for item in response['settings']]
        assert set(response_ids) == set(ids)
        assert set(response_versions) == set(versions)

    def test_patch(self):
        id = '@jupyterlab/shortcuts-extension:plugin'
        assert self.settings_api.put(id, dict()).status_code == 204

    def test_patch_wrong_id(self):
        with assert_http_error(404):
            self.settings_api.put('foo', dict())

    def test_patch_bad_data(self):
        id = '@jupyterlab/codemirror-extension:commands'
        with assert_http_error(400):
            self.settings_api.put(id, dict(keyMap=10))
"""
