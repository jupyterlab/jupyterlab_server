# coding: utf-8
"""JupyterLab Server"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os, jinja2
from traitlets import Unicode

from .handlers import add_handlers, LabConfig

from jupyter_server.extension.application import ExtensionApp

class LabServerApp(ExtensionApp):

    default_url = Unicode('/lab',
                          help='The default URL to redirect to from `/`')

    lab_config = LabConfig()

    # The name of the extension
    extension_name = "lab"

    # Te url that your extension will serve its homepage.
    default_url = '/lab'

    # Should your extension expose other server extensions when launched directly?
    load_other_extensions = True

    # Local path to static files directory.
    static_paths = [
        lab_config.static_url
    ]

    # Local path to templates directory.
    template_paths = [
        lab_config.templates_dir
    ]

    def initialize_handlers(self):
        add_handlers(self.serverapp.web_app, self.lab_config)

    def initialize_templates(self):
        jenv_opt = {"autoescape": True}
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_paths),
            extensions=["jinja2.ext.i18n"],
            **jenv_opt
        )
        template_settings = {"lab_jinja2_env": env}
        self.settings.update(**template_settings)

    def initialize_settings(self):
        settings = self.serverapp.web_app.settings
        # By default, make terminals available.
        settings.setdefault('terminals_available', True)

main = launch_new_instance = LabServerApp.launch_instance
