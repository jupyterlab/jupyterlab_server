"""Test the kernels service API."""
import json
import os
import pytest
import shutil
import tornado

from .utils import expected_http_error

async def test_delete(fetch, labserverapp):
    orig = 'f/o/o/'
    copy = 'baz'
    r = await fetch('lab', 'api', 'workspaces', orig)
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    data['metadata']['id'] = copy
    r2 = await fetch('lab', 'api', 'workspaces', copy, 
        method='PUT',
        body=json.dumps(data))
    assert r2.code == 204
    r3 = await fetch('lab', 'api', 'workspaces', copy,
        method='DELETE',
        )
    assert r3.code == 204

async def test_get(fetch, labserverapp):
    id = 'foo'
    r = await fetch('lab', 'api', 'workspaces', id)
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    assert data['metadata']['id'] == id

async def test_listing(fetch, labserverapp):
    # ID fields are from workspaces/*.jupyterlab-workspace
    listing = set(['foo', 'f/o/o/'])
    r = await fetch('lab', 'api', 'workspaces')
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    output = set(data['workspaces']['ids'])
    assert output == listing

async def test_put(fetch, labserverapp):
    id = 'foo'
    r = await fetch('lab', 'api', 'workspaces', id)
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    r2 = await fetch('lab', 'api', 'workspaces', id, 
        method='PUT',
        body=json.dumps(data)
        )
    assert r2.code == 204

async def test_bad_put(fetch, labserverapp):
    orig = 'foo'
    copy = 'bar'
    r = await fetch('lab', 'api', 'workspaces', orig)
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await fetch('lab', 'api', 'workspaces', copy,
            method='PUT',
            body=json.dumps(data)
        )
    assert expected_http_error(e, 400)

async def test_blank_put(fetch, labserverapp):
    orig = 'foo'
    r = await fetch('lab', 'api', 'workspaces', orig)
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await fetch('lab', 'api', 'workspaces',
            method='PUT',
            body=json.dumps(data)
        )
    assert expected_http_error(e, 400)
