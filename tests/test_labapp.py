# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""Basic tests for the lab handlers.
"""

import json
import re
from pathlib import Path

import pytest
import tornado.httpclient

from jupyterlab_server.test_utils import expected_http_error


@pytest.fixture
def notebooks(jp_create_notebook, labserverapp):
    nbpaths = (
        "notebook1.ipynb",
        "jlab_test_notebooks/notebook2.ipynb",
        "jlab_test_notebooks/level2/notebook3.ipynb",
    )
    for nb in nbpaths:
        jp_create_notebook(nb)
    return nbpaths


def extract_page_config(html):
    return json.loads(
        re.search(
            r'<script id="jupyter-config-data" type="application/json">\s*(?P<data>.*?)\s*</script>',
            html,
        ).group(  # type: ignore
            "data"
        )
    )


async def test_lab_handler(notebooks, jp_fetch):
    r = await jp_fetch("lab", "jlab_test_notebooks")
    assert r.code == 200
    # Check that the lab template is loaded
    html = r.body.decode()
    assert "Files" in html
    assert "JupyterLab Server Application" in html


async def test_page_config(labserverapp, jp_fetch):
    r = await jp_fetch("lab")
    assert r.code == 200
    # Check that the lab template is loaded
    html = r.body.decode()
    page_config = extract_page_config(html)
    assert not page_config["treePath"]
    assert page_config["preferredPath"] == "/"

    def ispath(p):
        return p.endswith("Dir") or p.endswith("Path") or p == "serverRoot"

    nondirs = {k: v for k, v in page_config.items() if not ispath(k)}
    assert nondirs == {
        "appName": "JupyterLab Server Application",
        "appNamespace": "jupyterlab_server",
        "appUrl": "/lab",
        "appVersion": "",
        "baseUrl": "/a%40b/",
        "cacheFiles": True,
        "disabledExtensions": [],
        "federated_extensions": [],
        "fullAppUrl": "/a%40b/lab",
        "fullLabextensionsUrl": "/a%40b/lab/extensions",
        "fullLicensesUrl": "/a%40b/lab/api/licenses",
        "fullListingsUrl": "/a%40b/lab/api/listings",
        "fullMathjaxUrl": "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js",
        "fullSettingsUrl": "/a%40b/lab/api/settings",
        "fullStaticUrl": "/a%40b/static/jupyterlab_server",
        "fullThemesUrl": "/a%40b/lab/api/themes",
        "fullTranslationsApiUrl": "/a%40b/lab/api/translations",
        "fullTreeUrl": "/a%40b/lab/tree",
        "fullWorkspacesApiUrl": "/a%40b/lab/api/workspaces",
        "ignorePlugins": [],
        "labextensionsUrl": "/lab/extensions",
        "licensesUrl": "/lab/api/licenses",
        "listingsUrl": "/lab/api/listings",
        "mathjaxConfig": "TeX-AMS_HTML-full,Safe",
        "mode": "multiple-document",
        "notebookStartsKernel": True,
        "settingsUrl": "/lab/api/settings",
        "store_id": 0,
        "terminalsAvailable": True,
        "themesUrl": "/lab/api/themes",
        "translationsApiUrl": "/lab/api/translations",
        "treeUrl": "/lab/tree",
        "workspace": "default",
        "workspacesApiUrl": "/lab/api/workspaces",
        "wsUrl": "",
    }


@pytest.fixture(scope="function")
def serverapp_preferred_dir(jp_server_config, jp_root_dir):
    preferred_dir = Path(jp_root_dir, "my", "preferred_dir")
    preferred_dir.mkdir(parents=True, exist_ok=True)
    jp_server_config.ServerApp.preferred_dir = str(preferred_dir)
    return preferred_dir


async def test_app_preferred_dir(serverapp_preferred_dir, labserverapp, jp_fetch):
    r = await jp_fetch("lab")
    assert r.code == 200
    # Check that the lab template is loaded
    html = r.body.decode()
    page_config = extract_page_config(html)
    api_path = str(serverapp_preferred_dir.relative_to(labserverapp.serverapp.root_dir).as_posix())
    assert page_config["preferredPath"] == api_path


async def test_contents_manager_preferred_dir(jp_root_dir, labserverapp, jp_fetch):
    preferred_dir = Path(jp_root_dir, "my", "preferred_dir")
    preferred_dir.mkdir(parents=True, exist_ok=True)
    try:
        _ = labserverapp.serverapp.contents_manager.preferred_dir
        labserverapp.serverapp.contents_manager.preferred_dir = str(preferred_dir)
    except AttributeError:
        pytest.skip("Skipping contents manager test, trait not present")

    r = await jp_fetch("lab")
    assert r.code == 200
    # Check that the lab template is loaded
    html = r.body.decode()
    page_config = extract_page_config(html)
    api_path = str(preferred_dir.relative_to(labserverapp.serverapp.root_dir).as_posix())
    assert page_config["preferredPath"] == api_path


async def test_notebook_handler(notebooks, jp_fetch):
    for nbpath in notebooks:
        r = await jp_fetch("lab", nbpath)
        assert r.code == 200
        # Check that the lab template is loaded
        html = r.body.decode()
        assert "JupyterLab Server Application" in html


async def test_404(notebooks, jp_fetch):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await jp_fetch("foo")
    assert expected_http_error(e, 404)
