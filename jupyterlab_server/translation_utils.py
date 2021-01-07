"""
Localization utilities to find available language packs and packages with
localization data.
"""

import gettext
import json
import importlib
import os
import subprocess
import sys
import traceback

import babel
import pkg_resources
from packaging.version import parse as parse_version

# Entry points
JUPYTERLAB_LANGUAGEPACK_ENTRY = "jupyterlab.languagepack"
JUPYTERLAB_LOCALE_ENTRY = "jupyterlab.locale"

# Constants
DEFAULT_LOCALE = "en"
LOCALE_DIR = "locale"
LC_MESSAGES_DIR = "LC_MESSAGES"


# --- Private process helpers
# ----------------------------------------------------------------------------
def _get_installed_language_pack_locales():
    """
    Get available installed language pack locales.

    Returns
    -------
    tuple
        A tuple, where the first item is the result and the second item any
        error messages.

    Notes
    -----
    This functions are meant to be called via a subprocess to guarantee the
    results represent the most up-to-date entry point information, which
    seems to be defined on interpreter startup.
    """
    data = {}
    messages = []
    for entry_point in pkg_resources.iter_entry_points(JUPYTERLAB_LANGUAGEPACK_ENTRY):
        try:
            data[entry_point.name] = os.path.dirname(entry_point.load().__file__)
        except Exception:
            messages.append(traceback.format_exc())

    message = "\n".join(messages)
    return data, message


def _get_installed_package_locales():
    """
    Get available installed packages containing locale information.

    Returns
    -------
    tuple
        A tuple, where the first item is the result and the second item any
        error messages. The value for the key points to the root location
        the package.

    Notes
    -----
    This functions are meant to be called via a subprocess to guarantee the
    results represent the most up-to-date entry point information, which
    seems to be defined on interpreter startup.
    """
    data = {}
    messages = []
    for entry_point in pkg_resources.iter_entry_points(JUPYTERLAB_LOCALE_ENTRY):
        try:
            data[entry_point.name] = os.path.dirname(entry_point.load().__file__)
        except Exception:
            messages.append(traceback.format_exc())

    message = "\n".join(messages)
    return data, message


def _main():
    """
    Run functions in this file in a subprocess and prints to stdout the results.
    """
    data = {}
    message = ""
    if len(sys.argv) == 2:
        func_name = sys.argv[-1]
        func = globals().get(func_name, None)

        if func:
            try:
                data, message = func()
            except Exception:
                message = traceback.format_exc()
    else:
        message = "Invalid number of arguments!"

    sys.stdout.write(json.dumps({"data": data, "message": message}))


# --- Helpers
# ----------------------------------------------------------------------------
def run_process_and_parse(cmd: list):
    """
    Run a list of commands and return the result parsed form stdout.

    Parameters
    ----------
    cmd: list
        List of commands

    Returns
    -------
    tuple
        A tuple in the form `(result_dict, message)`.
    """
    result = {"data": {}, "message": ""}
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        result = json.loads(stdout.decode('utf-8'))
    except Exception:
        result["message"] = traceback.format_exc() + "\n" + repr(stderr.decode('utf-8'))

    return result["data"], result["message"]


def is_valid_locale(locale: str) -> bool:
    """
    Check if a `locale` value is valid.

    Parameters
    ----------
    locale: str
        Language locale code.

    Notes
    -----
    A valid locale is in the form language (See ISO-639 standard) and an
    optional territory (See ISO-3166 standard).

    Examples of valid locales:
    - English: DEFAULT_LOCALE
    - Australian English: "en_AU"
    - Portuguese: "pt"
    - Brazilian Portuguese: "pt_BR"

    Examples of invalid locales:
    - Australian Spanish: "es_AU"
    - Brazilian German: "de_BR"
    """
    valid = False
    try:
        babel.Locale.parse(locale)
        valid = True
    except babel.core.UnknownLocaleError:
        pass
    except ValueError:
        pass

    return valid


def get_display_name(locale: str, display_locale: str=DEFAULT_LOCALE) -> str:
    """
    Return the language name to use with a `display_locale` for a given language locale.

    Parameters
    ----------
    locale: str
        The language name to use.
    display_locale: str, optional
        The language to display the `locale`.

    Returns
    -------
    str
        Localized `locale` and capitalized language name using `display_locale` as language.
    """
    locale = locale if is_valid_locale(locale) else DEFAULT_LOCALE
    display_locale = display_locale if is_valid_locale(display_locale) else DEFAULT_LOCALE
    loc = babel.Locale.parse(locale)
    return loc.get_display_name(display_locale).capitalize()


def merge_locale_data(language_pack_locale_data, package_locale_data):
    """
    Merge language pack data with locale data bundled in packages.

    Parameters
    ----------
    language_pack_locale_data: dict
        The dictionary with language pack locale data.
    package_locale_data: dict
        The dictionary with package locale data.

    Returns
    -------
    dict
        Merged locale data.
    """
    result = language_pack_locale_data
    package_lp_metadata = language_pack_locale_data.get("", {})
    package_lp_version = package_lp_metadata.get("version", None)
    package_lp_domain = package_lp_metadata.get("domain", None)

    package_metadata = package_locale_data.get("", {})
    package_version = package_metadata.get("version", None)
    package_domain = package_metadata.get("domain", "None")

    if package_lp_version and package_version and package_domain == package_lp_domain:
        package_version = parse_version(package_version)
        package_lp_version = parse_version(package_lp_version)

        if package_version > package_lp_version:
            # If package version is more recent, then update keys of the language pack
            result = language_pack_locale_data.copy()
            result.update(package_locale_data)

    return result


def get_installed_packages_locale(locale: str) -> dict:
    """
    Get all jupyterlab extensions installed that contain locale data.

    Returns
    -------
    dict
        Ordered list of available language packs.
        >>> {"package-name": locale_data, ...}

    Examples
    --------
    - `entry_points={"jupyterlab.locale": "package-name = package_module"}`
    - `entry_points={"jupyterlab.locale": "jupyterlab-git = jupyterlab_git"}`
    """
    cmd = [sys.executable, __file__, "_get_installed_package_locales"]
    found_package_locales, message = run_process_and_parse(cmd)
    packages_locale_data = {}
    messages = message.split("\n")
    if not message:
        for package_name, package_root_path in found_package_locales.items():
            locales = {}
            try:
                locale_path = os.path.join(package_root_path, LOCALE_DIR)
                # Handle letter casing
                locales = {
                    loc.lower(): loc
                    for loc in os.listdir(locale_path)
                    if os.path.isdir(os.path.join(locale_path, loc))
                }
            except Exception:
                messages.append(traceback.format_exc())

            if locale.lower() in locales:
                locale_json_path = os.path.join(
                    locale_path,
                    locales[locale.lower()],
                    LC_MESSAGES_DIR,
                    "{0}.json".format(package_name),
                )
                if os.path.isfile(locale_json_path):
                    try:
                        with open(locale_json_path, "r", encoding='utf-8') as fh:
                            packages_locale_data[package_name] = json.load(fh)
                    except Exception:
                        messages.append(traceback.format_exc())

    return packages_locale_data, "\n".join(messages)


# --- API
# ----------------------------------------------------------------------------
def get_language_packs(display_locale: str=DEFAULT_LOCALE) -> tuple:
    """
    Return the available language packs installed in the system.

    The returned information contains the languages displayed in the current
    locale.

    Parameters
    ----------
    display_locale: str, optional
        Default is DEFAULT_LOCALE.

    Returns
    -------
    tuple
        A tuple in the form `(locale_data_dict, message)`.

    Notes
    -----
    We call `_get_installed_language_pack_locales` via a subprocess to
    guarantee the results represent the most up-to-date entry point
    information, which seems to be defined on interpreter startup.
    """
    cmd = [sys.executable, __file__, "_get_installed_language_pack_locales"]
    found_locales, message = run_process_and_parse(cmd)
    locales = {}
    messages = message.split("\n")
    if not message:
        invalid_locales = []
        valid_locales = []
        messages = []
        for locale in found_locales:
            if is_valid_locale(locale):
                valid_locales.append(locale)
            else:
                invalid_locales.append(locale)

        display_locale = display_locale if display_locale in valid_locales else DEFAULT_LOCALE
        locales = {
            DEFAULT_LOCALE: {
                "displayName": get_display_name(DEFAULT_LOCALE, display_locale),
                "nativeName": get_display_name(DEFAULT_LOCALE, DEFAULT_LOCALE),
            }
        }
        for locale in valid_locales:
            locales[locale] = {
                "displayName": get_display_name(locale, display_locale),
                "nativeName": get_display_name(locale, locale),
            }

        if invalid_locales:
            messages.append("The following locales are invalid: {0}!".format(invalid_locales))

    return locales, "\n".join(messages)


def get_language_pack(locale: str) -> tuple:
    """
    Get a language pack for a given `locale` and update with any installed
    package locales.

    Returns
    -------
    tuple
        A tuple in the form `(locale_data_dict, message)`.

    Notes
    -----
    We call `_get_installed_language_pack_locales` via a subprocess to
    guarantee the results represent the most up-to-date entry point
    information, which seems to be defined on interpreter startup.
    """
    cmd = [sys.executable, __file__, "_get_installed_language_pack_locales"]
    found_locales, message = run_process_and_parse(cmd)
    found_packages_locales, message = get_installed_packages_locale(locale)
    locale_data = {}
    messages = message.split("\n")
    if not message and is_valid_locale(locale):
        if locale in found_locales:
            path = found_locales[locale]
            for root, __, files in os.walk(path, topdown=False):
                for name in files:
                    if name.endswith(".json"):
                        pkg_name = name.replace(".json", "")
                        json_path = os.path.join(root, name)
                        try:
                            with open(json_path, "r", encoding='utf-8') as fh:
                                merged_data = json.load(fh)
                        except Exception:
                            messages.append(traceback.format_exc())

                        # Load packages with locale data and merge them
                        if pkg_name in found_packages_locales:
                            pkg_data = found_packages_locales[pkg_name]
                            merged_data = merge_locale_data(merged_data, pkg_data)

                        locale_data[pkg_name] = merged_data

            # Check if package locales exist that do not exists in language pack
            for pkg_name, data in found_packages_locales.items():
                if pkg_name not in locale_data:
                    locale_data[pkg_name] = data

    return locale_data, "\n".join(messages)


# --- Translators
# ----------------------------------------------------------------------------
class TranslationBundle:
    """
    Translation bundle providing gettext translation functionality.
    """

    def __init__(self, domain: str, locale: str):
        self._domain = domain
        self._locale = locale

        self.update_locale(locale)

    def update_locale(self, locale: str):
        """
        Update the locale environment variables.

        Parameters
        ----------
        locale: str
            The language name to use.
        """
        # TODO: Need to handle packages that provide their own .mo files
        self._locale = locale
        localedir = None
        if locale != DEFAULT_LOCALE:
            language_pack_module = f"jupyterlab_language_pack_{locale}"
            try:
                mod = importlib.import_module(language_pack_module)
                localedir = os.path.join(os.path.dirname(mod.__file__), LOCALE_DIR)
            except Exception:
                pass

        gettext.bindtextdomain(self._domain, localedir=localedir)

    def gettext(self, msgid: str) -> str:
        """
        Translate a singular string.

        Parameters
        ----------
        msgid: str
            The singular string to translate.

        Returns
        -------
        str
            The translated string.
        """
        return gettext.dgettext(self._domain, msgid)

    def ngettext(self, msgid: str, msgid_plural: str, n: int) -> str:
        """
        Translate a singular string with pluralization.

        Parameters
        ----------
        msgid: str
            The singular string to translate.
        msgid_plural: str
            The plural string to translate.
        n: int
            The number for pluralization.

        Returns
        -------
        str
            The translated string.
        """
        return gettext.dngettext(self._domain, msgid, msgid_plural, n)

    def pgettext(self, msgctxt: str, singular: str) -> str:
        """
        Translate a singular string with context.

        Parameters
        ----------
        msgctxt: str
            The message context.
        msgid: str
            The singular string to translate.

        Returns
        -------
        str
            The translated string.
        """
        return gettext.dpgettext(self._domain, msgctxt, msgid)

    def npgettext(self, msgctxt: str, msgid: str, msgid_plural: str, n: int) -> str:
        """
        Translate a singular string with context and pluralization.

        Parameters
        ----------
        msgctxt: str
            The message context.
        msgid: str
            The singular string to translate.
        msgid_plural: str
            The plural string to translate.
        n: int
            The number for pluralization.

        Returns
        -------
        str
            The translated string.
        """
        return gettext.dnpgettext(self._domain, msgctxt, msgid, msgid_plural, n)

    # Shorthands
    def __(self, msgid: str) -> str:
        """
        Shorthand for gettext.

        Parameters
        ----------
        msgid: str
            The singular string to translate.

        Returns
        -------
        str
            The translated string.
        """
        return self.gettext(msgid)

    def _n(self, msgid: str, msgid_plural: str, n: int) -> str:
        """
        Shorthand for ngettext.

        Parameters
        ----------
        msgid: str
            The singular string to translate.
        msgid_plural: str
            The plural string to translate.
        n: int
            The number for pluralization.

        Returns
        -------
        str
            The translated string.
        """
        return self.ngettext(msgid, plural, n)

    def _p(self, msgctxt: str, msgid: str) -> str:
        """
        Shorthand for pgettext.

        Parameters
        ----------
        msgctxt: str
            The message context.
        msgid: str
            The singular string to translate.

        Returns
        -------
        str
            The translated string.
        """
        return self.pgettext(msgctxt, msgid)

    def _np(self, msgctxt: str, msgid: str, msgid_plular: str, n: str) -> str:
        """
        Shorthand for npgettext.

        Parameters
        ----------
        msgctxt: str
            The message context.
        msgid: str
            The singular string to translate.
        msgid_plural: str
            The plural string to translate.
        n: int
            The number for pluralization.

        Returns
        -------
        str
            The translated string.
        """
        return self.npgettext(msgctxt, msgid, msgid_plular, n)


class translator:
    """
    Translations manager.
    """
    _TRANSLATORS = {}
    _LOCALE = DEFAULT_LOCALE

    @staticmethod
    def _update_env(locale: str):
        """
        Update the locale environment variables based on the settings.

        Parameters
        ----------
        locale: str
            The language name to use.
        """
        for key in ["LANGUAGE", "LANG"]:
            os.environ[key] = f"{locale}.UTF-8"

    @classmethod
    def set_locale(cls, locale: str):
        """
        Set locale for the translation bundles based on the settings.

        Parameters
        ----------
        locale: str
            The language name to use.
        """
        if is_valid_locale(locale):
            cls._LOCALE = locale
            translator._update_env(locale)
            for domain, bundle in cls._TRANSLATORS.items():
                bundle.update_locale(locale)

    @classmethod
    def load(cls, domain: str) -> TranslationBundle:
        """
        Load translation domain.

        The domain is usually the normalized ``package_name``.

        Parameters
        ----------
        domain: str
            The translations domain. The normalized python package name.
        
        Returns
        -------
        Translator
            A translator instance bound to the domain.
        """
        if domain in cls._TRANSLATORS:
            trans = cls._TRANSLATORS[domain]
        else:
            trans = TranslationBundle(domain, cls._LOCALE)
            cls._TRANSLATORS[domain] = trans

        return trans


if __name__ == "__main__":
    _main()
