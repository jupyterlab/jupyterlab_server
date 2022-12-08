"""Test the Settings service API.
"""
import csv
import io
import json
import mimetypes

import mistune  # type:ignore
import pytest

from jupyterlab_server import LicensesApp
from jupyterlab_server.licenses_handler import DEFAULT_THIRD_PARTY_LICENSE_FILE, LicensesManager

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


def _make_static_dir(app, tmp_path, has_licenses=True, license_json=None, package_in_app=False):
    app_dir = tmp_path / "app"
    static_dir = app_dir / "static"
    static_dir.mkdir(parents=True)

    package_text = json.dumps({"name": "@jupyterlab/top", "version": "0.0.1"})
    package_json = (app_dir if package_in_app else static_dir) / "package.json"
    package_json.write_text(package_text, encoding="utf-8")

    if has_licenses:
        (static_dir / DEFAULT_THIRD_PARTY_LICENSE_FILE).write_text(
            license_json or _good_license_json(),
            encoding="utf-8",
        )

    app.static_dir = str(static_dir)


def _good_license_json():
    return json.dumps({"packages": [dict(FULL_ENTRY[:i]) for i in range(1 + len(FULL_ENTRY))]})


@pytest.fixture(
    params=[
        ["application/json", "json", json.loads],
        ["text/csv", "csv", _read_csv],
        ["text/markdown", "markdown", mistune.markdown],
    ]
)
def mime_format_parser(request):
    return request.param


@pytest.fixture(params=[True, False])
def has_licenses(request):
    return request.param


@pytest.fixture
def licenses_app(tmp_path, has_licenses):
    app = LicensesApp()
    _make_static_dir(app, tmp_path, has_licenses)
    return app


# the actual tests


@pytest.mark.parametrize("has_static_dir", [True, False])
@pytest.mark.parametrize("full_text", ["true", "false"])
@pytest.mark.parametrize("bundles_pattern", ["", "@jupyterlab/.*", "nothing"])
async def test_get_license_report(
    mime_format_parser,
    has_static_dir,
    has_licenses,
    full_text,
    bundles_pattern,
    jp_fetch,
    labserverapp,
    tmp_path,
):
    if has_static_dir:
        _make_static_dir(labserverapp, tmp_path, has_licenses)
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


async def test_dev_mode_license_report(
    jp_fetch,
    labserverapp,
    tmp_path,
):
    _make_static_dir(labserverapp, tmp_path, package_in_app=True)
    r = await jp_fetch("lab", "api", "licenses/")
    assert r.code == 200


@pytest.mark.parametrize(
    "license_json",
    [
        "// leading comment\n" + _good_license_json(),
        _good_license_json().replace("packages", "whatever"),
    ],
)
async def test_malformed_license_report(
    license_json,
    jp_fetch,
    labserverapp,
    tmp_path,
):
    _make_static_dir(labserverapp, tmp_path, license_json=license_json)
    r = await jp_fetch("lab", "api", "licenses/")
    assert r.code == 200


async def test_licenses_cli(licenses_app, capsys, mime_format_parser):
    mime, fmt, parse = mime_format_parser
    args = []
    if fmt != "markdown":
        args += [f"--{fmt}"]
    licenses_app.initialize(args)

    with pytest.raises(SystemExit) as exited:
        licenses_app.start()

    assert exited.type == SystemExit
    assert exited.value.code == 0

    captured = capsys.readouterr()
    assert parse(captured.out) is not None


@pytest.fixture
def a_fake_labextension(tmp_path):
    """just enough of an extension to be parsed"""
    ext_name = "@an-org/an-extension"
    ext_path = tmp_path / ext_name
    package_data = {"name": ext_name}
    bundle_data = {"packages": [dict(FULL_ENTRY)]}

    package_json = ext_path / "package.json"
    third_party_licenses = ext_path / "static" / DEFAULT_THIRD_PARTY_LICENSE_FILE

    third_party_licenses.parent.mkdir(parents=True)

    package_json.write_text(json.dumps(package_data), encoding="utf-8")
    third_party_licenses.write_text(json.dumps(bundle_data), encoding="utf-8")

    yield ext_path, ext_name


@pytest.fixture
def a_licenses_manager():
    yield LicensesManager()


def test_labextension_bundle(a_fake_labextension, a_licenses_manager):
    ext_path, ext_name = a_fake_labextension
    bundle = a_licenses_manager.license_bundle(ext_path, ext_name)
    assert bundle["packages"][0]["name"] == dict(FULL_ENTRY)["name"]  # noqa
