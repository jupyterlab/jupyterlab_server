# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os

import json5  # type:ignore
import pytest

from jupyterlab_server.config import get_page_config


@pytest.mark.parametrize(
    "lib,extension",
    [
        (json, "json"),
        (json5, "json5"),
    ],
)
def test_get_page_config(tmp_path, lib, extension):
    labext_path = [os.path.join(tmp_path, "ext")]
    settings_path = os.path.join(tmp_path, "settings")
    os.mkdir(settings_path)

    with open(os.path.join(settings_path, f"page_config.{extension}"), "w") as fid:
        data = dict(deferredExtensions=["foo"])
        lib.dump(data, fid)

    static_dir = os.path.join(tmp_path, "static")
    os.mkdir(static_dir)
    with open(os.path.join(static_dir, "package.json"), "w") as fid:
        data2 = dict(jupyterlab=dict(extensionMetadata=dict(foo=dict(disabledExtensions=["bar"]))))
        json.dump(data2, fid)

    config = get_page_config(labext_path, settings_path)
    assert config == {
        "deferredExtensions": ["foo"],
        "federated_extensions": [],
        "disabledExtensions": ["bar"],
    }


def test_get_page_config_forwards_build_metadata(tmp_path):
    """The build metadata of a prebuilt extension reaches the page config.

    JupyterLab reads `plugins` to tell whether it has to load a module during
    the initial page load, so an entry which does not reach the page config
    costs it that decision.
    """
    labext_path = [str(tmp_path / "ext")]
    ext_dir = tmp_path / "ext" / "myextension"
    ext_dir.mkdir(parents=True)
    (ext_dir / "package.json").write_text(
        json.dumps(
            {
                "name": "myextension",
                "version": "0.1.0",
                "jupyterlab": {
                    "_build": {
                        "load": "static/remoteEntry.abc.js",
                        "extension": "./extension",
                        "style": "./style",
                        "plugins": {"./extension": [{"id": "myextension:plugin"}]},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    config = get_page_config(labext_path)

    assert config["federated_extensions"] == [
        {
            "name": "myextension",
            "load": "static/remoteEntry.abc.js",
            "extension": "./extension",
            "style": "./style",
            "plugins": {"./extension": [{"id": "myextension:plugin"}]},
            "entrypoints": None,
        }
    ]
