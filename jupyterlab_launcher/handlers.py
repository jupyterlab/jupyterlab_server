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


#-----------------------------------------------------------------------------
# Module globals
#-----------------------------------------------------------------------------

HERE = os.path.dirname(__file__)
FILE_LOADER = FileSystemLoader(HERE)


class LabHandler(IPythonHandler):
    """Render the JupyterLab View."""

    def initialize(self, page_title, css_files, bundle_files, page_config_file):
        self.page_title = page_title
        self.css_files = css_files
        self.bundle_files = bundle_files
        self.page_config_file = page_config_file

    @web.authenticated
    def get(self):
        # Handle page config data.
        page_config = dict()
        page_config.update(self.settings.get('page_config_data', {}))
        terminals = self.settings.get('terminals_available', False)
        page_config.setdefault('terminalsAvailable', terminals)
        page_config.setdefault('ignorePlugins', [])

        if os.path.exists(self.page_config_file):
            with open(self.page_config_file) as fid:
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


def add_handlers(web_app, page_config_file, build_dir, page_title, prefix):
    """Add the appropriate handlers to the web app.
    """
    base_url = web_app.settings['base_url']
    prefix = ujoin(base_url, prefix)

    bundle_files = []
    css_files = []
    for entry in ['main']:
        css_file = entry + '.css'
        if os.path.isfile(os.path.join(build_dir, css_file)):
            css_files.append(ujoin(prefix, css_file))
        bundle_files.append(ujoin(prefix, entry + '.bundle.js'))

    handlers = [
        (prefix + r'/?', LabHandler, {
            'page_config_file': page_config_file,
            'css_files': css_files,
            'bundle_files': bundle_files,
            'page_title': page_title
        }),
        (prefix + r"/(.*)", FileFindHandler, {
            'path': build_dir
        })
    ]
    web_app.add_handlers(".*$", handlers)
