"""Test the Settings service API.
"""
from pathlib import Path
import json

import pytest
import json5
import tornado

from strict_rfc3339 import rfc3339_to_timestamp

from .utils import expected_http_error
from .utils import maybe_patch_ioloop, big_unicode_string
from .utils import validate_request


async def test_get_settings_overrides_dicts(jp_fetch, labserverapp):
    # Check that values that are dictionaries in overrides.json are
    # merged with the schema.
    id = '@jupyterlab/apputils-extension:themes'
    r = await jp_fetch('lab', 'api', 'settings', id)
    validate_request(r)
    res = r.body.decode()
    data = json.loads(res)
    assert data['id'] == id
    schema = data['schema']
    # Check that overrides.json file is respected.
    assert schema['properties']['codeCellConfig']['default']["lineNumbers"] is True
    assert len(schema['properties']['codeCellConfig']['default']) == 15


@pytest.mark.parametrize('ext', ['json', 'json5'])
async def test_get_settings_overrides_d_dicts(jp_fetch, labserverapp, ext):
    # Check that values that are dictionaries in overrides.d/*.json are
    # merged with the schema.
    id = '@jupyterlab/apputils-extension:themes'
    overrides_d = Path(labserverapp.app_settings_dir) / "overrides.d"
    overrides_d.mkdir(exist_ok=True, parents=True)
    for i in range(10):
        text = json.dumps({id: {'codeCellConfig': {'cursorBlinkRate': 530 + i}}})
        if ext == 'json5':
            text += '\n// a comment'
        (overrides_d / f"foo-{i}.{ext}").write_text(text, encoding='utf-8')
    r = await jp_fetch('lab', 'api', 'settings', id)
    validate_request(r)
    res = r.body.decode()
    data = json.loads(res)
    assert data['id'] == id
    schema = data['schema']
    # Check that the last overrides.d/*.json file is respected.
    assert schema['properties']['codeCellConfig']['default']['cursorBlinkRate'] == 539


async def test_get_settings(jp_fetch, labserverapp):
    id = '@jupyterlab/apputils-extension:themes'
    r = await jp_fetch('lab', 'api', 'settings', id)
    validate_request(r)
    res = r.body.decode()
    data = json.loads(res)
    assert data['id'] == id
    schema = data['schema']
    # Check that overrides.json file is respected.
    assert schema['properties']['theme']['default'] == 'JupyterLab Dark'
    assert 'raw' in res


async def test_get_federated(jp_fetch, labserverapp):
    id = '@jupyterlab/apputils-extension-federated:themes'
    r = await jp_fetch('lab', 'api', 'settings', id)
    validate_request(r)
    res = r.body.decode()
    assert 'raw' in res


async def test_get_bad(jp_fetch, labserverapp):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch('foo')
    assert expected_http_error(e, 404)

async def test_listing(jp_fetch, labserverapp):
    ids = [
        '@jupyterlab/apputils-extension:themes',
        '@jupyterlab/apputils-extension-federated:themes',
        '@jupyterlab/codemirror-extension:commands',
        '@jupyterlab/codemirror-extension-federated:commands',
        '@jupyterlab/shortcuts-extension:plugin',
        '@jupyterlab/translation-extension:plugin',
        '@jupyterlab/unicode-extension:plugin'
    ]
    versions = ['N/A', 'N/A', 'test-version']
    r = await jp_fetch('lab', 'api', 'settings/')
    validate_request(r)
    res = r.body.decode()
    response = json.loads(res)
    response_ids = [item['id'] for item in response['settings']]
    response_schemas = [item['schema'] for item in response['settings']]
    response_versions = [item['version'] for item in response['settings']]
    assert set(response_ids) == set(ids)
    assert all(response_schemas)
    assert set(response_versions) == set(versions)
    last_modifieds = [item['last_modified'] for item in response['settings']]
    createds = [item['created'] for item in response['settings']]
    assert {None} == set(last_modifieds + createds)


async def test_patch(jp_fetch, labserverapp):
    id = '@jupyterlab/shortcuts-extension:plugin'

    r = await jp_fetch('lab', 'api', 'settings', id,
        method='PUT',
        body=json.dumps(dict(raw=json5.dumps(dict()))))
    validate_request(r)

    r = await jp_fetch('lab', 'api', 'settings', id,
        method='GET',
        )
    validate_request(r)
    data = json.loads(r.body.decode())
    first_created = rfc3339_to_timestamp(data['created'])
    first_modified = rfc3339_to_timestamp(data['last_modified'])

    r = await jp_fetch('lab', 'api', 'settings', id,
        method='PUT',
        body=json.dumps(dict(raw=json5.dumps(dict())))
        )
    validate_request(r)

    r = await jp_fetch('lab', 'api', 'settings', id,
        method='GET',
        )
    validate_request(r)
    data = json.loads(r.body.decode())
    second_created = rfc3339_to_timestamp(data['created'])
    second_modified = rfc3339_to_timestamp(data['last_modified'])

    assert first_created <= second_created
    assert first_modified < second_modified

    r = await jp_fetch('lab', 'api', 'settings/',
        method='GET',
        )
    validate_request(r)
    data = json.loads(r.body.decode())
    listing = data['settings']
    list_data = [item for item in listing if item['id'] == id][0]
    # TODO(@echarles) Check this...
#    assert list_data['created'] == data['created']
#    assert list_data['last_modified'] == data['last_modified']


async def test_patch_unicode(jp_fetch, labserverapp):
    id = '@jupyterlab/unicode-extension:plugin'
    settings = dict(comment=big_unicode_string[::-1])
    payload = dict(raw=json5.dumps(settings))

    r = await jp_fetch('lab', 'api', 'settings', id,
        method='PUT',
        body=json.dumps(payload)
        )
    validate_request(r)

    r = await jp_fetch('lab', 'api', 'settings', id,
        method='GET',
        )
    validate_request(r)
    data = json.loads(r.body.decode())
    assert data["settings"]["comment"] == big_unicode_string[::-1]

async def test_patch_wrong_id(jp_fetch, labserverapp):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch('foo',
            method='PUT',
            body=json.dumps(dict(raw=json5.dumps(dict())))
        )
    assert expected_http_error(e, 404)

async def test_patch_bad_data(jp_fetch, labserverapp):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        settings = dict(keyMap=10)
        payload = dict(raw=json5.dumps(settings))
        await jp_fetch('foo',
            method='PUT',
            body=json.dumps(payload)
        )
    assert expected_http_error(e, 404)

async def test_patch_invalid_payload_format(jp_fetch, labserverapp):
    id = '@jupyterlab/apputils-extension:themes'

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        settings = dict(keyMap=10)
        payload = dict(foo=json5.dumps(settings))
        await jp_fetch('lab', 'api', 'settings', id,
            method='PUT',
            body=json.dumps(payload)
        )
    assert expected_http_error(e, 400)

async def test_patch_invalid_json(jp_fetch, labserverapp):
    id = '@jupyterlab/apputils-extension:themes'

    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        payload_str = 'eh'
        await jp_fetch('lab', 'api', 'settings', id,
            method='PUT',
            body=json.dumps(payload_str)
        )
    assert expected_http_error(e, 400)
