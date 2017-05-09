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
from traitlets import HasTraits, Unicode, Bool


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
        settings_dir = config.settings_dir
        page_config_file = os.path.join(settings_dir, 'page_config.json')
        assets_dir = config.assets_dir
        url = config.page_url

        bundle_files = []
        css_files = []
        for entry in ['main']:
            css_file = entry + '.css'
            if os.path.isfile(os.path.join(assets_dir, css_file)):
                css_files.append(ujoin(url, css_file))
            bundle_file = entry + '.bundle.js'
            if os.path.isfile(os.path.join(assets_dir, bundle_file)):
                bundle_files.append(ujoin(url, bundle_file))

        if not bundle_files:
            msg = ('%s build artifacts not detected in "%s".\n' +
                   'Please see README for build instructions.')
            msg = msg % (config.name, config.assets_dir)
            self.log.error(msg)
            self.write(self.render_template('error.html',
                       status_code=500,
                       status_message='%s Error' % config.name,
                       page_title='%s Error' % config.name,
                       message=msg))
            return

        # Handle page config data.
        page_config = dict()
        page_config.update(self.settings.get('page_config_data', {}))
        terminals = self.settings.get('terminals_available', False)
        page_config.setdefault('terminalsAvailable', terminals)
        page_config.setdefault('ignorePlugins', [])
        page_config.setdefault('appName', config.name)
        page_config.setdefault('appVersion', config.version)
        page_config.setdefault('appNamespace', config.namespace)
        page_config.setdefault('devMode', config.dev_mode)
        page_config.setdefault('settingsDir', config.settings_dir)
        page_config.setdefault('assetsDir', config.assets_dir)

        if os.path.exists(page_config_file):
            with open(page_config_file) as fid:
                try:
                    page_config.update(json.load(fid))
                except Exception as e:
                    print(e)

        mathjax_config = self.settings.get('mathjax_config',
                                           'TeX-AMS_HTML-full,Safe')
        config = dict(
            page_title=config.page_title,
            mathjax_url=self.mathjax_url,
            mathjax_config=mathjax_config,
            css_files=css_files,
            bundle_files=bundle_files,
            page_config=page_config
        )
        self.write(self.render_template('index.html', **config))

    def get_template(self, name):
        return FILE_LOADER.load(self.settings['jinja2_env'], name)


class LabConfig(HasTraits):
    """The lab application configuration object.
    """
    settings_dir = Unicode('',
        help='The settings directory')

    assets_dir = Unicode('',
        help='The assets directory')

    name = Unicode('',
        help='The name of the application')

    version = Unicode('',
        help='The version of the application')

    namespace = Unicode('',
        help='The namespace for the application')

    page_title = Unicode('JupyterLab',
        help='The page title for the application')

    page_url = Unicode('/lab',
        help='The url for the application')

    dev_mode = Bool(False,
        help='Whether the application is in dev mode')


def add_handlers(web_app, config):
    """Add the appropriate handlers to the web app.
    """
    base_url = web_app.settings['base_url']
    url = ujoin(base_url, config.page_url)
    assets_dir = config.assets_dir

    package_file = os.path.join(assets_dir, 'package.json')
    with open(package_file) as fid:
        data = json.load(fid)

    public_url = data['jupyterlab']['publicPath']
    config.version = (config.version or data['jupyter']['version'] or
                      data['version'])
    config.name = config.name or data['jupyterlab']['name']

    handlers = [
        (url + r'/?', LabHandler, {
            'lab_config': config
        }),
        (url + r"/(.*)", FileFindHandler, {
            'path': assets_dir
        }),
        (public_url + r"/(.*)", FileFindHandler, {
            'path': assets_dir
        })
    ]
    web_app.add_handlers(".*$", handlers)
