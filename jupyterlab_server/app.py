# coding: utf-8
"""JupyterLab Server"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os, jinja2
from traitlets import Unicode
from jinja2 import Environment, FileSystemLoader
from traitlets import Bool, Unicode, default
from jupyter_server.extension.application import ExtensionApp, ExtensionAppJinjaMixin

from .server import url_path_join as ujoin


from .handlers import add_handlers, LabConfig


class LabServerApp(ExtensionAppJinjaMixin, LabConfig, ExtensionApp):

    default_url = Unicode('/lab',
                          help='The default URL to redirect to from `/`')

    # The name of the extension
    extension_name = "jupyterlab_server"

    # Te url that your extension will serve its homepage.
    default_url = '/lab'

    # Should your extension expose other server extensions when launched directly?
    load_other_extensions = True

    @default('static_url')
    def _default_static_url(self):
        return ujoin('static/', self.extension_name)

    @default('workspaces_url')
    def _default_workspaces_url(self):
        return ujoin(self.app_url, 'workspaces/')

    @default('workspaces_api_url')
    def _default_workspaces_api_url(self):
        return ujoin(self.app_url, 'api', 'workspaces/')

    @default('settings_url')
    def _default_settings_url(self):
        return ujoin(self.app_url, 'api', 'settings/')

    @default('themes_url')
    def _default_themes_url(self):
        return ujoin(self.app_url, 'api', 'themes/')

    @default('tree_url')
    def _default_tree_url(self):
        return ujoin(self.app_url, 'tree/')

    def initialize_settings(self):
        settings = self.serverapp.web_app.settings
        # By default, make terminals available.
        settings.setdefault('terminals_available', True)

    def initialize_handlers(self):
        add_handlers(self.handlers, self)


main = launch_new_instance = LabServerApp.launch_instance
