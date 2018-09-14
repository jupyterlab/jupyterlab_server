# coding: utf-8
"""JupyterLab Server"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from traitlets import Unicode

from .server import ServerApp
from .handlers import add_handlers, LabConfig


class LabServerApp(ServerApp):

    default_url = Unicode('/lab',
                          help='The default URL to redirect to from `/`')

    lab_config = LabConfig()

    def start(self):
        add_handlers(self.web_app, self.lab_config)
        super().start()


main = LabServerApp.launch_instance
