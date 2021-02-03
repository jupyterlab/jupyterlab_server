"""Test the translations service API."""

import json
import os
import pytest
import shutil
import subprocess
import sys

from .utils import expected_http_error
from ..translation_utils import (_get_installed_language_pack_locales,
                                 _get_installed_package_locales,
                                 get_display_name,
                                 get_installed_packages_locale,
                                 get_language_pack, get_language_packs,
                                 is_valid_locale, merge_locale_data,
                                 run_process_and_parse, translator)

from .utils import maybe_patch_ioloop

maybe_patch_ioloop()

# Constants
HERE = os.path.abspath(os.path.dirname(__file__))

if not os.path.exists(os.path.join(HERE, 'translations')):
    pytest.skip("skipping translation tests", allow_module_level=True)


def setup_module(module):
    """ setup any state specific to the execution of this module."""
    for pkg in ['jupyterlab-some-package', 'jupyterlab-language-pack-es_CO']:
        src = os.path.join(HERE, 'translations', pkg)
        subprocess.Popen([sys.executable, '-m', 'pip', 'install', src]).communicate()


def teardown_module(module):
    """ teardown any state that was previously setup."""
    for pkg in ['jupyterlab-some-package', 'jupyterlab-language-pack-es_CO']:
        subprocess.Popen([sys.executable, '-m', 'pip', 'uninstall', pkg, '-y']).communicate()


@pytest.fixture(autouse=True)
def before_after_test(schemas_dir, user_settings_dir, labserverapp):

    # Code that will run before any test.

    # Copy the schema files.
    src = os.path.join(HERE, 'schemas', '@jupyterlab')
    dst = os.path.join(str(schemas_dir), '@jupyterlab')
    if os.path.exists(dst):
        shutil.rmtree(dst)

    shutil.copytree(src, dst)

    # Copy the overrides file.
    src = os.path.join(HERE, 'app-settings', 'overrides.json')
    dst = os.path.join(str(user_settings_dir), 'overrides.json')

    if os.path.exists(dst):
        os.remove(dst)

    shutil.copyfile(src, dst)

    # A test function will be run at this point.

    yield

    # Code that will run after your test.
    # N/A


async def test_get(jp_fetch):
    r = await jp_fetch("lab", "api", "translations", "")
    data = json.loads(r.body.decode())["data"]
    assert "en" in data

async def test_get_locale(jp_fetch):
    locale = "es_CO"
    r = await jp_fetch("lab", "api", "translations", locale)
    data = json.loads(r.body.decode())["data"]
    assert "jupyterlab" in data
    assert data["jupyterlab"][""]["language"] == locale

    assert "jupyterlab_some_package" in data
    assert data["jupyterlab_some_package"][""]["version"] == "0.1.0"
    assert data["jupyterlab_some_package"][""]["language"] == locale

async def test_get_locale_bad(jp_fetch):
    r = await jp_fetch("lab", "api", "translations", "foo_BAR")
    data = json.loads(r.body.decode())["data"]
    assert data == {}

async def test_get_locale_not_installed(jp_fetch):
    r = await jp_fetch("lab", "api", "translations", "es_AR")
    result = json.loads(r.body.decode())
    assert "not installed" in result["message"]
    assert result["data"] == {}

async def test_get_locale_not_valid(jp_fetch):
    r = await jp_fetch("lab", "api", "translations", "foo_BAR")
    result = json.loads(r.body.decode())
    assert "not valid" in result["message"]
    assert result["data"] == {}


# --- Backend locale
# ------------------------------------------------------------------------
async def test_backend_locale(jp_fetch):
    locale = "es_CO"
    r = await jp_fetch("lab", "api", "translations", locale)
    trans = translator.load("jupyterlab")
    result = trans.__("MORE ABOUT PROJECT JUPYTER")
    assert result == "Más sobre el proyecto jupyter"


async def test_backend_locale_extension(jp_fetch):
    locale = "es_CO"
    r = await jp_fetch("lab", "api", "translations", locale)
    trans = translator.load("jupyterlab_some_package")
    result = trans.__("BOOM")
    assert result == "Foo bar 2"


# --- Utils testing
# ------------------------------------------------------------------------
def test_get_installed_language_pack_locales_fails():
    # This should not be able to find entry points, since it needs to be
    # ran in a subprocess
    data, message = _get_installed_language_pack_locales()
    assert "es_CO" not in data
    assert message == ""

def test_get_installed_language_pack_locales_passes():
    utils_file = os.path.join(os.path.dirname(HERE), "translation_utils.py")
    cmd = [sys.executable, utils_file, "_get_installed_language_pack_locales"]
    data, message = run_process_and_parse(cmd)
    assert "es_CO" in data
    assert message == ""

def test_get_installed_package_locales_fails():
    # This should not be able to find entry points, since it needs to be
    # ran in a subprocess
    data, message = _get_installed_package_locales()
    assert "jupyterlab_some_package" not in data
    assert message == ""

def test_get_installed_package_locales():
    utils_file = os.path.join(os.path.dirname(HERE), "translation_utils.py")
    cmd = [sys.executable, utils_file, "_get_installed_package_locales"]
    data, message = run_process_and_parse(cmd)
    assert "jupyterlab_some_package" in data
    assert os.path.isdir(data["jupyterlab_some_package"])
    assert message == ""

def test_get_installed_packages_locale():
    data, message = get_installed_packages_locale("es_CO")
    assert "jupyterlab_some_package" in data
    assert "" in data["jupyterlab_some_package"]
    assert message == ""

def test_get_language_packs():
    data, message = get_language_packs("en")
    assert "en" in data
    assert "es_CO" in data
    assert message == ""

def test_get_language_pack():
    data, message = get_language_pack("es_CO")
    assert "jupyterlab" in data
    assert "jupyterlab_some_package" in data
    assert "" in data["jupyterlab"]
    assert "" in data["jupyterlab_some_package"]
    assert message == ""


# --- Utils
# ------------------------------------------------------------------------
def test_merge_locale_data():
    some_package_data_1 = {
        "": {
            "domain": "some_package",
            "version": "1.0.0"
        },
        "FOO": ["BAR"],
    }
    some_package_data_2 = {
        "": {
            "domain": "some_package",
            "version": "1.1.0"
        },
        "SPAM": ["BAR"],
    }
    some_package_data_3 = {
        "": {
            "domain": "some_different_package",
            "version": "1.4.0"
        },
        "SPAM": ["BAR"],
    }
    # Package data 2 has a newer version so it should update the package data 1
    result = merge_locale_data(some_package_data_1, some_package_data_2)
    assert "SPAM" in result
    assert "FOO" in result

    # Package data 2 has a older version so it should not update the package data 2
    result = merge_locale_data(some_package_data_2, some_package_data_1)
    assert "SPAM" in result
    assert "FOO" not in result

    # Package data 3 is a different package (domain) so it should not update package data 2
    result = merge_locale_data(some_package_data_2, some_package_data_3)
    assert result == some_package_data_2


def test_is_valid_locale_valid():
    assert is_valid_locale("en")
    assert is_valid_locale("es")
    assert is_valid_locale("es_CO")


def test_is_valid_locale_invalid():
    assert not is_valid_locale("foo_SPAM")
    assert not is_valid_locale("bar")


def test_get_display_name_valid():
    assert get_display_name("en", "en") == "English"
    assert get_display_name("en", "es") == "Inglés"
    assert get_display_name("en", "es_CO") == "Inglés"
    assert get_display_name("en", "fr") == "Anglais"
    assert get_display_name("es", "en") == "Spanish"
    assert get_display_name("fr", "en") == "French"


def test_get_display_name_invalid():
    assert get_display_name("en", "foo") == "English"
    assert get_display_name("foo", "en") == "English"
    assert get_display_name("foo", "bar") == "English"
