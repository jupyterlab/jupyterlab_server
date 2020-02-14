"""Test the Settings service API.
"""

import pytest
import json
import tornado

from .utils import expected_http_error

async def test_get(fetch, labserverapp):
    id = '@jupyterlab/apputils-extension:themes'
    r = await fetch('lab', 'api', 'settings', id)
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    assert data['id'] == id
    schema = data['schema']
    # Check that overrides.json file is respected.
    assert schema['properties']['theme']['default'] == 'JupyterLab Dark'
    assert 'raw' in res

async def test_get_bad(fetch, labserverapp):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await fetch('foo')
    assert expected_http_error(e, 404)

async def test_listing(fetch, labserverapp):
    ids = [
        '@jupyterlab/apputils-extension:themes',
        '@jupyterlab/codemirror-extension:commands',
        '@jupyterlab/shortcuts-extension:plugin'
    ]
    versions = ['N/A', 'N/A', 'test-version']
    r = await fetch('lab', 'api', 'settings')
    assert r.code == 200
    res = r.body.decode()
    response = json.loads(res)
    response_ids = [item['id'] for item in response['settings']]
    response_versions = [item['version'] for item in response['settings']]
    assert set(response_ids) == set(ids)
    assert set(response_versions) == set(versions)

async def test_patch(fetch, labserverapp):
    id = '@jupyterlab/shortcuts-extension:plugin'
    r = await fetch('lab', 'api', 'settings', id, 
        method='PUT',
        body=json.dumps({})
        )
    assert r.code == 204

async def test_patch_wrong_id(fetch, labserverapp):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await fetch('foo',
            method='PUT',
            body=json.dumps({})
        )
    assert expected_http_error(e, 404)

async def test_patch_bad_data(fetch, labserverapp):
    id = '@jupyterlab/codemirror-extension:commands'
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await fetch('foo',
            method='PUT',
            body=json.dumps({'keyMap': 10})
        )
    assert expected_http_error(e, 404)
