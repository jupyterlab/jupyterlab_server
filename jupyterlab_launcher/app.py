# coding: utf-8
"""Jupyter Lab Launcher"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os

from notebook.notebookapp import NotebookApp
from jupyter_core.paths import ENV_CONFIG_PATH
from traitlets import Unicode

from .handlers import add_handlers


class LabLauncherApp(NotebookApp):

    default_url = Unicode('/lab',
        help="The default URL to redirect to from `/`")

    def start(self):
        config_dir = ENV_CONFIG_PATH[0]
        page_file = os.path.join(config_dir, 'page_config.json')
        with open(page_file) as fid:
            page_config = json.load(fid)
        build_file = os.path.join(config_dir, 'build_config.json')
        with open(build_file) as fid:
            build_config = json.load(fid)
        add_handlers(self.web_app, page_config, build_config, self.default_url)
        super.start()


main = LabLauncherApp.launch_instance
