# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""
Translation handler.
"""

import json
import os
import traceback

import tornado
from tornado import gen, web

from .settings_handler import get_settings
from .translation_utils import get_language_pack, get_language_packs, is_valid_locale

from .server import APIHandler, url_path_join

SCHEMA_NAME = '@jupyterlab/translation-extension:plugin'


def get_current_locale(config):
    """
    Get the current locale for given `config`.

    Parameters
    ----------
    config: LabConfig
        The config.

    Returns
    -------
    str
        The current locale string.

    Notes
    -----
    If the locale setting is not valid, it will default to "en".
    """
    settings, _warnings = get_settings(
        config.app_settings_dir,
        config.schemas_dir,
        config.user_settings_dir,
        schema_name=SCHEMA_NAME,
    )
    current_locale = settings.get("settings", {}).get("locale", "en")
    if not is_valid_locale(current_locale):
        current_locale = "en"

    return current_locale


class TranslationsHandler(APIHandler):

    def initialize(self, lab_config):
        self.lab_config = lab_config

    @gen.coroutine
    @tornado.web.authenticated
    def get(self, locale=""):
        """
        Get installed language packs.

        Parameters
        ----------
        locale: str, optional
            If no locale is provided, it will list all the installed language packs.
            Default is `""`.
        """
        data, message = {}, ""
        try:
            if locale == "":
                data, message = get_language_packs(
                    display_locale=get_current_locale(self.lab_config))
            else:
                data, message = get_language_pack(locale)
                if data == {} and message == "":
                    if is_valid_locale(locale):
                        message = "Language pack '{}' not installed!".format(locale)
                    else:
                        message = "Language pack '{}' not valid!".format(locale)
        except Exception:
            message = traceback.format_exc()

        self.set_status(200)
        self.finish(json.dumps({"data": data, "message": message}))
