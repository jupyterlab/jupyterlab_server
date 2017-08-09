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
from traitlets import HasTraits, Unicode, Bool, List

from .settings_handler import SettingsHandler

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

        base_url = self.settings['base_url']
        url = ujoin(base_url, config.static_url)

        bundle_files = set(config.static_css_files)
        css_files = set(config.static_bundle_files)

        if config.assets_dir:
            for entry in ['main']:
                css_file = entry + '.css'
                if os.path.isfile(os.path.join(assets_dir, css_file)):
                    css_files.add(ujoin(url, css_file))
                bundle_file = entry + '.bundle.js'
                if os.path.isfile(os.path.join(assets_dir, bundle_file)):
                    bundle_files.add(ujoin(url, bundle_file))

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
        page_config.setdefault(
            'settingsDir', config.settings_dir.replace(os.sep, '/')
        )
        page_config.setdefault(
            'assetsDir', config.assets_dir.replace(os.sep, '/')
        )

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
            page_config=page_config,
            public_url=url
        )
        self.write(self.render_template('index.html', **config))

    def get_template(self, name):
        return FILE_LOADER.load(self.settings['jinja2_env'], name)


class LabConfig(HasTraits):
    """The lab application configuration object.
    """
    settings_dir = Unicode('',
        help='The application settings directory')

    assets_dir = Unicode('',
        help='The assets directory or path')

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

    static_url = Unicode('/lab/static/',
        help='The static url for the application')

    static_bundle_files = List(Unicode(),
        help='The optional list of static bundle files to serve, can be used' \
             ' to serve the core assets over cdn')

    static_css_files = List(Unicode(),
        help='The optional list of static css files to serve, can be used' \
             ' to serve the core assets over cdn')

    dev_mode = Bool(False,
        help='Whether the application is in dev mode')

    settings_path = Unicode(r"/lab/api/settings/(?P<section_name>[\w.-]+)",
        help='The path of the settings handler')

    schemas_dir = Unicode('',
        help='The location of the settings schemas directory')

    user_settings_dir = Unicode('',
        help='The location of the user settings directory')

    themes_path = Unicode('/lab/api/themes/',
        help='The path of the theme handler')

    themes_dir = Unicode('',
        help='The location of the themes directory')


def add_handlers(web_app, config):
    """Add the appropriate handlers to the web app.
    """
    base_url = web_app.settings['base_url']
    url = ujoin(base_url, config.page_url)
    assets_dir = config.assets_dir
    web_app.settings.setdefault('page_config_data', dict())

    handlers = [
        (ujoin(base_url, config.page_url, r'/?'), LabHandler, {
            'lab_config': config
        })
    ]

    if config.assets_dir:
        static_url = ujoin(base_url, config.static_url, "/(.*)")
        handlers.append((static_url, FileFindHandler, {
            'path': assets_dir
        }))

        package_file = os.path.join(assets_dir, 'package.json')
        with open(package_file) as fid:
            data = json.load(fid)

        config.version = (config.version or data['jupyterlab']['version'] or
                          data['version'])
        config.name = config.name or data['jupyterlab']['name']
    
    if config.schemas_dir:
        settings_url = ujoin(base_url, config.settings_path)
        handlers.append((settings_url, SettingsHandler, {
            'schemas_dir': config.schemas_dir,
            'settings_dir': config.user_settings_dir
        }))

    themes_url = ujoin(base_url, config.themes_path)
    web_app.settings['page_config_data']['themePath'] = themes_url

    if config.themes_dir:
        handlers.append((ujoin(themes_url, "(.*)"), FileFindHandler, {
            'path': config.themes_dir
        }))

    web_app.add_handlers(".*$", handlers)
