import json
import os

from jupyterlab_server.config import get_page_config


def test_get_page_config(tmp_path):
    labext_path = [os.path.join(tmp_path, "ext")]
    settings_path = os.path.join(tmp_path, "settings")
    os.mkdir(settings_path)

    with open(os.path.join(settings_path, "page_config.json"), "w") as fid:
        data = dict(deferredExtensions=["foo"])
        json.dump(data, fid)

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
