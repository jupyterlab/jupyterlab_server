# coding: utf-8
"""JupyterLab Server"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os, jinja2
from traitlets import Unicode
from jinja2 import Environment, FileSystemLoader
from traitlets import Bool, Unicode, default
from jupyter_server.extension.application import ExtensionApp, ExtensionAppJinjaMixin

from ._version import __version__
from .server import url_path_join as ujoin
from .handlers import add_handlers, LabConfig


class LabServerApp(ExtensionAppJinjaMixin, LabConfig, ExtensionApp):
    """A Lab Server Application that runs out-of-the-box"""
    extension_name = "jupyterlab_server"
    app_name = "JupyterLab Server Application"
    app_version = __version__

    @property
    def app_namespace(self):
        return self.extension_name

    default_url = Unicode('/lab',
                          help='The default URL to redirect to from `/`')

    # Should your extension expose other server extensions when launched directly?
    load_other_extensions = True

    def initialize_templates(self):
        self.static_paths = [self.static_dir]
        self.template_paths = [self.templates_dir]

    def initialize_settings(self):
        settings = self.serverapp.web_app.settings
        # By default, make terminals available.
        settings.setdefault('terminals_available', True)

    def initialize_handlers(self):
        add_handlers(self.handlers, self)


main = launch_new_instance = LabServerApp.launch_instance
