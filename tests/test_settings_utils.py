# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""Unit tests for settings_utils."""

import json

import json5  # type:ignore
import pytest

from jupyterlab_server.settings_utils import _get_overrides, _override, get_settings


@pytest.mark.parametrize("ext", ["json", "json5"])
def test_overrides_null_value(tmp_path, monkeypatch, ext):
    monkeypatch.setenv("JUPYTER_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JUPYTER_DATA_DIR", str(tmp_path / "data"))

    app_settings_dir = tmp_path / "app_settings"
    schemas_dir = tmp_path / "schemas"
    settings_dir = tmp_path / "user_settings"
    app_settings_dir.mkdir()
    settings_dir.mkdir()

    plugin_dir = schemas_dir / "@jupyterlab" / "archive-extension"
    plugin_dir.mkdir(parents=True)
    schema = {
        "title": "Archive",
        "type": "object",
        "properties": {
            "format": {
                "type": ["string", "null"],
                "default": "zip",
            },
            "nested": {
                "type": "object",
                "default": {
                    "keep": "value",
                    "nullable": "initial",
                },
            },
            "nullableObject": {
                "type": ["object", "null"],
                "default": {"a": 1},
            },
        },
    }
    (plugin_dir / "archive.json").write_text(json.dumps(schema), encoding="utf-8")

    overrides_d = app_settings_dir / "overrides.d"
    overrides_d.mkdir()
    (overrides_d / f"01-base.{ext}").write_text(
        json.dumps(
            {
                "@jupyterlab/archive-extension:archive": {
                    "format": "tgz",
                    "nested": {"nullable": "from-d"},
                }
            }
        ),
        encoding="utf-8",
    )

    override_payload = {
        "@jupyterlab/archive-extension:archive": {
            "format": None,
            "nested": {"nullable": None},
            "nullableObject": None,
        }
    }
    dump = json5.dumps if ext == "json5" else json.dumps
    (app_settings_dir / f"overrides.{ext}").write_text(dump(override_payload), encoding="utf-8")

    overrides, error = _get_overrides(str(app_settings_dir))
    assert not error
    assert overrides["@jupyterlab/archive-extension:archive"] == {
        "format": None,
        "nested": {"nullable": None},
        "nullableObject": None,
    }

    result, warnings = get_settings(
        str(app_settings_dir),
        str(schemas_dir),
        str(settings_dir),
        schema_name="@jupyterlab/archive-extension:archive",
    )
    assert warnings == [None]
    props = result["schema"]["properties"]
    assert props["format"]["default"] is None
    assert props["nested"]["default"] == {"keep": "value", "nullable": None}
    assert props["nullableObject"]["default"] is None


def test_override_dict_with_nested_null_and_null_replacement():
    schema = {
        "properties": {
            "nested": {"default": {"a": 1, "b": 2}},
            "whole": {"default": {"x": 1}},
        }
    }
    overrides = {
        "pkg:plugin": {
            "nested": {"a": None},
            "whole": None,
        }
    }
    updated = _override("pkg:plugin", schema, overrides)
    assert updated["properties"]["nested"]["default"] == {"a": None, "b": 2}
    assert updated["properties"]["whole"]["default"] is None
