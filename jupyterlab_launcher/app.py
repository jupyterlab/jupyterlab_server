# coding: utf-8
"""Jupyter Lab Launcher"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
try:
    from notebook.notebookapp import NotebookApp as ServerApp
except ImportError:
    from jupyter_server.serverapp import ServerApp

from traitlets import Unicode

from .handlers import add_handlers, LabConfig


class LabLauncherApp(ServerApp):

    default_url = Unicode('/lab',
                          help='The default URL to redirect to from `/`')

    lab_config = LabConfig()

    def start(self):
        add_handlers(self.web_app, self.lab_config)
        ServerApp.start(self)


main = LabLauncherApp.launch_instance
