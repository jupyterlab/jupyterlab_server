# coding: utf-8
"""Jupyter Lab Launcher"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from notebook.notebookapp import NotebookApp
from traitlets import Unicode

from .handlers import add_handlers


class LabLauncherApp(NotebookApp):

    default_url = Unicode('/lab',
                          help='The default URL to redirect to from `/`')

    def start(self):
        add_handlers(self.web_app, self.lab_config)
        NotebookApp.start(self)


main = LabLauncherApp.launch_instance
