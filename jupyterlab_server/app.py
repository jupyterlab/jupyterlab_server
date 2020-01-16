# coding: utf-8
"""JupyterLab Server"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os, jinja2
from traitlets import Unicode
from jinja2 import Environment, FileSystemLoader

from .handlers import add_handlers, LabConfig

from jupyter_server.extension.application import ExtensionApp, ExtensionAppJinjaMixin

class LabServerApp(ExtensionAppJinjaMixin, ExtensionApp):

    default_url = Unicode('/lab',
                          help='The default URL to redirect to from `/`')

    lab_config = LabConfig()

    # The name of the extension
    extension_name = "lab"

    # Te url that your extension will serve its homepage.
    default_url = '/lab'

    template_paths = [
        lab_config.templates_dir
    ]

    # Local path to static files directory.
    static_paths = [
        lab_config.static_url
    ]

    # Should your extension expose other server extensions when launched directly?
    load_other_extensions = True

    def initialize_settings(self):
        settings = self.serverapp.web_app.settings
        # By default, make terminals available.
        settings.setdefault('terminals_available', True)

    def initialize_templates(self):
        self.template_paths = [
            self.lab_config.templates_dir
        ]
        self.static_paths = [
            self.lab_config.static_url
        ]
        if len(self.template_paths) > 0:
            self.settings.update({
                "{}_template_paths".format(self.extension_name): self.template_paths
            })
        self.jinja2_env = Environment(
            loader=FileSystemLoader(self.template_paths), 
            extensions=['jinja2.ext.i18n'],
            autoescape=True,
            **self.jinja2_options
        )
        self.settings.update(
            {
                "{}_jinja2_env".format(self.extension_name): self.jinja2_env 
            }
        )
        
    def initialize_handlers(self):
        add_handlers(self, self.serverapp.web_app, self.lab_config)

main = launch_new_instance = LabServerApp.launch_instance
