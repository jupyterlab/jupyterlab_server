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

# The default paths for the application.
default_static_path = r'lab/static/'
default_settings_path = r'lab/api/settings/'
default_themes_path = r'/lab/api/themes/'


class LabHandler(IPythonHandler):
    """Render the JupyterLab View."""

    def initialize(self, lab_config):
        self.lab_config = lab_config

    @web.authenticated
    @web.removeslash
    def get(self):
        config = self.lab_config
        settings_dir = config.settings_dir
        page_config_file = os.path.join(settings_dir, 'page_config.json')
        assets_dir = config.assets_dir

        js_files = set(config.static_js_urls)
        css_files = set(config.static_css_urls)

        if config.assets_dir:
            for entry in ['main']:
                css_file = entry + '.css'
                if os.path.isfile(os.path.join(assets_dir, css_file)):
                    css_files.add(ujoin(config.static_url, css_file))
                bundle_file = entry + '.bundle.js'
                if os.path.isfile(os.path.join(assets_dir, bundle_file)):
                    js_files.add(ujoin(config.static_url, bundle_file))

        if not js_files:
            msg = '%s assets not found in "%s"'
            msg = msg % (config.name, config.assets_dir)
            self.log.error(config.error_message or msg)
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
        page_config.setdefault('settingsPath', config.settings_url)
        page_config.setdefault('themePath', config.themes_url)
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
            js_files=js_files,
            page_config=page_config,
            public_url=config.static_url
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
        help='The location of the static assets directory')

    name = Unicode('',
        help='The name of the application')

    version = Unicode('',
        help='The version of the application')

    namespace = Unicode('',
        help='The namespace for the application')

    error_message = Unicode('',
        help='The error message to show when assets are not detected')

    page_title = Unicode('JupyterLab',
        help='The page title for the application')

    page_url = Unicode('/lab',
        help='The url for the application')

    static_url = Unicode('',
        help='The optional override static url for the application')

    static_js_urls = List(Unicode(),
        help='The optional list of static JavaScript urls to serve')

    static_css_urls = List(Unicode(),
        help='The optional list of static CSS urls to serve')

    dev_mode = Bool(False,
        help='Whether the application is in dev mode')

    settings_url = Unicode('',
        help='The optional override url of the settings handler')

    schemas_dir = Unicode('',
        help='The location of the settings schemas directory')

    user_settings_dir = Unicode('',
        help='The location of the user settings directory')

    themes_url = Unicode('',
        help='The optional theme override url')

    themes_dir = Unicode('',
        help='The location of the themes directory')


def add_handlers(web_app, config):
    """Add the appropriate handlers to the web app.
    """
    # Set up the main page handler.
    base_url = web_app.settings['base_url']
    handlers = [
        (ujoin(base_url, config.page_url, r'/?'), LabHandler, {
            'lab_config': config
        })
    ]

    # Handle the static assets.
    if config.assets_dir and not config.static_url:
        config.static_url = ujoin(base_url, default_static_path)
        handlers.append((config.static_url + "(.*)", FileFindHandler, {
            'path': config.assets_dir,
            'no_cache_paths': ['/']  # don't cache anything
        }))

        package_file = os.path.join(config.assets_dir, 'package.json')
        if os.path.exists(package_file):
            with open(package_file) as fid:
                data = json.load(fid)

            config.version = (
                config.version or data['jupyterlab']['version'] or
                data['version']
            )
            config.name = config.name or data['jupyterlab']['name']

    # Handle the settings.
    if config.schemas_dir and not config.settings_url:
        config.settings_url = ujoin(base_url, default_settings_path)
        settings_path = config.settings_url + '(?P<section_name>.+)'
        handlers.append((settings_path, SettingsHandler, {
            'schemas_dir': config.schemas_dir,
            'settings_dir': config.user_settings_dir
        }))

    # Handle the themes.
    if config.themes_dir and not config.themes_url:
        config.themes_url = ujoin(base_url, default_themes_path)
        handlers.append((ujoin(config.themes_url, "(.*)"), FileFindHandler, {
            'path': config.themes_dir,
            'no_cache_paths': ['/']  # don't cache anything
        }))

    config.name = config.name or 'Application'

    web_app.add_handlers(".*$", handlers)
