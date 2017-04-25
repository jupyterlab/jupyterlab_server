# coding: utf-8
"""Jupyter Lab Launcher"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os

from notebook.notebookapp import NotebookApp
from traitlets import Unicode

from .handlers import add_handlers, LabConfig


class LabLauncherApp(NotebookApp):

    default_url = Unicode('/lab',
        help="The default URL to redirect to from `/`")

    lab_config = LabConfig()

    def start(self):
        config_dir = self.lab_config_dir
        page_file = os.path.join(config_dir, 'page_config.json')
        build_file = os.path.join(config_dir, 'build_config.json')
        with open(build_file) as fid:
            build_config = json.load(fid)
        build_dir = os.path.join(build_config['location'], 'build')
        add_handlers(
            self.web_app, page_file, build_dir, self.lab_page_title,
            self.default_url
        )
        super.start()


main = LabLauncherApp.launch_instance
