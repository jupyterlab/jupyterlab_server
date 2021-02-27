"""Test the Settings service API.
"""
import io
import csv
import json
import mimetypes

import pytest
import mistune

from ..licenses_handler import DEFAULT_THIRD_PARTY_LICENSE_FILE

# utilities

FULL_ENTRY = (
    ("name", "@jupyterlab/foo"),
    ("versionInfo", "0.0.1"),
    ("licenseId", "BSD-3-Clause"),
    ("extractedText", "> license text goes here"),
)


def _read_csv(csv_text):
    with io.StringIO() as csvfile:
        csvfile.write(csv_text)
        csvfile.seek(0)
        return [*csv.DictReader(csvfile)]


def _make_app_dir(labserverapp, tmp_path, has_licenses=True, license_json=None):
    app_dir = tmp_path / "app"
    static = app_dir / "static"
    static.mkdir(parents=True)

    (static / "package.json").write_text(
        json.dumps({"name": "@jupyterlab/top", "version": "0.0.1"}), encoding="utf-8"
    )

    if has_licenses:
        (static / DEFAULT_THIRD_PARTY_LICENSE_FILE).write_text(
            license_json or _good_license_json(),
            encoding="utf-8",
        )

    setattr(labserverapp, "app_dir", str(app_dir))


def _good_license_json():
    return json.dumps(
        {"packages": [dict(FULL_ENTRY[:i]) for i in range(1 + len(FULL_ENTRY))]}
    )


@pytest.fixture(
    params=[
        ["application/json", "json", json.loads],
        ["text/csv", "csv", _read_csv],
        ["text/markdown", "markdown", mistune.markdown],
    ]
)
def mime_format_parser(request):
    return request.param


# the actual tests


@pytest.mark.parametrize("has_app_dir", [True, False])
@pytest.mark.parametrize("has_licenses", [True, False])
@pytest.mark.parametrize("full_text", ["true", "false"])
@pytest.mark.parametrize("bundles_pattern", ["", "@jupyterlab/.*", "nothing"])
async def test_get_license_report(
    mime_format_parser,
    has_app_dir,
    has_licenses,
    full_text,
    bundles_pattern,
    jp_fetch,
    labserverapp,
    tmp_path,
):
    if has_app_dir:
        _make_app_dir(labserverapp, tmp_path, has_licenses)
    mime, fmt, parse = mime_format_parser
    params = {"format": fmt, "full_text": full_text}
    if bundles_pattern:
        params["bundles"] = bundles_pattern
    r = await jp_fetch("lab", "api", "licenses/", params=params)
    assert r.code == 200
    assert r.headers["Content-type"] == mime
    res = r.body.decode()
    assert parse(res) is not None


async def test_download_license_report(
    jp_fetch,
    labserverapp,
    mime_format_parser,
):
    mime, fmt, parse = mime_format_parser
    params = {"format": fmt, "download": "1"}
    r = await jp_fetch("lab", "api", "licenses/", params=params)
    assert r.code == 200
    assert r.headers["Content-type"] == mime
    extension = mimetypes.guess_extension(mime)
    assert extension, f"no extension guessed for {mime}"
    assert extension in r.headers["Content-Disposition"], f"{r.headers}"


@pytest.mark.parametrize(
    "license_json",
    [
        "// leading comment\n" + _good_license_json(),
        _good_license_json().replace("packages", "whatever"),
    ],
)
async def test_malformed_license_report(
    license_json,
    mime_format_parser,
    jp_fetch,
    labserverapp,
    tmp_path,
):
    _make_app_dir(labserverapp, tmp_path, license_json=license_json)
    mime, fmt, parse = mime_format_parser
    r = await jp_fetch("lab", "api", "licenses/")
    assert r.code == 200
