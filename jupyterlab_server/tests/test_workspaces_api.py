"""Test the kernels service API."""
import json
import os
import pytest
import shutil
import tornado

from strict_rfc3339 import rfc3339_to_timestamp

from .utils import expected_http_error, maybe_patch_ioloop, big_unicode_string


maybe_patch_ioloop()


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


async def test_get_non_existant(fetch, labserverapp):
    id = 'foo'

    r = await fetch('lab', 'api', 'workspaces', id)
    data = json.loads(r.body.decode())

    r2 = await fetch('lab', 'api', 'workspaces', id, 
        method='PUT',
        body=json.dumps(data))
    assert r2.code == 204

    r3 = await fetch('lab', 'api', 'workspaces', id)
    data = json.loads(r3.body.decode())
    first_metadata = data["metadata"]
    first_created = rfc3339_to_timestamp(first_metadata['created'])
    first_modified = rfc3339_to_timestamp(first_metadata['last_modified'])

    r4 = await fetch('lab', 'api', 'workspaces', id, 
        method='PUT',
        body=json.dumps(data))
    assert r4.code == 204

    r5 = await fetch('lab', 'api', 'workspaces', id)
    data = json.loads(r5.body.decode())
    second_metadata = data["metadata"]
    second_created = rfc3339_to_timestamp(second_metadata['created'])
    second_modified = rfc3339_to_timestamp(second_metadata['last_modified'])

    assert first_created <= second_created
    assert first_modified < second_modified


@pytest.mark.skipif(os.name == "nt", reason="Temporal failure on windows")
async def test_get(fetch, labserverapp):
    id = 'foo'
    r = await fetch('lab', 'api', 'workspaces', id)
    data = json.loads(r.body.decode())
    metadata = data['metadata']
    assert metadata['id'] == id
    assert rfc3339_to_timestamp(metadata['created'])
    assert rfc3339_to_timestamp(metadata['last_modified'])

    r2 = await fetch('lab', 'api', 'workspaces', id)
    assert r2.code == 200
    data = json.loads(r.body.decode())
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


async def test_listing_dates(fetch, labserverapp):
    r = await fetch('lab', 'api', 'workspaces')
    data = json.loads(r.body.decode())
    values = data['workspaces']['values']
    times = sum(
        [
            [ws['metadata'].get('last_modified'), ws['metadata'].get('created')]
            for ws in values
        ],
        []
    )
    assert None not in times
    [rfc3339_to_timestamp(t) for t in times]


async def test_put(fetch, labserverapp):
    id = 'foo'
    r = await fetch('lab', 'api', 'workspaces', id)
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    data["metadata"]["big-unicode-string"] = big_unicode_string[::-1]
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
