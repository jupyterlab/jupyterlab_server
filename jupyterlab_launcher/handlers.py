# coding: utf-8
"""Jupyter Lab Launcher handlers"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os
from tornado import web

from notebook.base.handlers import IPythonHandler, FileFindHandler
from jinja2 import FileSystemLoader
from notebook.utils import url_path_join as ujoin
from traitlets import HasTraits, Unicode


#-----------------------------------------------------------------------------
# Module globals
#-----------------------------------------------------------------------------

HERE = os.path.dirname(__file__)
FILE_LOADER = FileSystemLoader(HERE)


class LabHandler(IPythonHandler):
    """Render the JupyterLab View."""

    def initialize(self, lab_config):
        self.lab_config = lab_config

    @web.authenticated
    def get(self):
        config = self.lab_config
        page_config_file = os.path.join(config.config_dir, 'page_config.json')
        runtime_dir = config.runtime_dir
        prefix = config.prefix

        bundle_files = []
        css_files = []
        for entry in ['main']:
            css_file = entry + '.css'
            if os.path.isfile(os.path.join(runtime_dir, css_file)):
                css_files.append(ujoin(prefix, css_file))
            bundle_files.append(ujoin(prefix, entry + '.bundle.js'))

        # Handle page config data.
        page_config = dict()
        page_config.update(self.settings.get('page_config_data', {}))
        terminals = self.settings.get('terminals_available', False)
        page_config.setdefault('terminalsAvailable', terminals)
        page_config.setdefault('ignorePlugins', [])
        page_config.setdefault('appName', config.name)
        page_config.setdefault('appVersion', config.version)
        page_config.setdefault('configDir', config.config_dir)

        if os.path.exists(page_config_file):
            with open(page_config_file) as fid:
                try:
                    page_config.update(json.load(fid))
                except Exception as e:
                    print(e)

        mathjax_config = self.settings.get('mathjax_config',
                                           'TeX-AMS_HTML-full,Safe')
        config = dict(
            page_title=self.page_title,
            mathjax_url=self.mathjax_url,
            mathjax_config=mathjax_config,
            css_files=self.css_files,
            bundle_files=self.bundle_files,
            page_config=page_config
        )
        self.write(self.render_template('index.html', **config))

    def get_template(self, name):
        return FILE_LOADER.load(self.settings['jinja2_env'], name)


class LabConfig(HasTraits):
    """The lab application configuration object.
    """
    config_dir = Unicode('',
        help='The configuration directory')

    runtime_dir = Unicode('',
        help='The runtime directory')

    page_title = Unicode('JupyterLab',
        help='The application page title')

    prefix = Unicode('/lab',
        help='The handler prefix for the application')

    name = Unicode('JupyterLab',
        help='The name of the application')

    version = Unicode('',
        help='The version of the application')


def add_handlers(web_app, config):
    """Add the appropriate handlers to the web app.
    """
    base_url = web_app.settings['base_url']
    prefix = ujoin(base_url, config.prefix)
    runtime_dir = config.runtime_dir

    if not os.path.exists(runtime_dir):
        msg = 'Runtime directory does not exist: "%s"' % runtime_dir
        raise ValueError(msg)

    handlers = [
        (prefix + r'/?', LabHandler, {
            'lab_config': config
        }),
        (prefix + r"/(.*)", FileFindHandler, {
            'path': runtime_dir
        })
    ]
    web_app.add_handlers(".*$", handlers)
