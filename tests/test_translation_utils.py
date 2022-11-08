import sys

from jupyterlab_server.translation_utils import (
    TranslationBundle,
    _main,
    get_installed_packages_locale,
    get_language_packs,
    translator,
)


def test_transutils_main():
    sys.argv = ["", "get_language_packs"]
    _main()
    sys.argv = [""]


def test_get_installed_packages_locale(jp_environ):
    get_installed_packages_locale("es_co")


def test_get_language_packs(jp_environ):
    get_language_packs("es_co")


def test_translation_bundle():
    bundle = TranslationBundle("foo", "bar")
    bundle.update_locale("fizz")
    bundle.gettext("hi")
    bundle.ngettext("hi", "his", 1)
    bundle.npgettext("foo", "bar", "bars", 2)
    bundle.pgettext("foo", "bar")


def test_translator():
    t = translator()
    t.load("foo")
    t.normalize_domain("bar")
    t.set_locale("fizz")
    t.translate_schema({})
