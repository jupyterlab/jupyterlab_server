# coding: utf-8
"""JupyterLab Server handlers"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os
from urllib.parse import urlparse

from tornado import web, template
from jinja2 import FileSystemLoader, TemplateError

from traitlets import HasTraits, Bool, Unicode, default

from .server import JupyterHandler, FileFindHandler, url_path_join as ujoin
from .workspaces_handler import WorkspacesHandler
from .settings_handler import SettingsHandler
from .listings_handler import ListingsHandler, fetch_listings
from .themes_handler import ThemesHandler

# -----------------------------------------------------------------------------
# Module globals
# -----------------------------------------------------------------------------


DEFAULT_TEMPLATE = template.Template("""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Error</title>
</head>
<body>
<h2>Cannot find template: "{{name}}"</h2>
<p>In "{{path}}"</p>
</body>
</html>
""")


def is_url(url):
  """Test whether a string is a full url (e.g. https://nasa.gov)

  https://stackoverflow.com/a/52455972
  """
  try:
    result = urlparse(url)
    return all([result.scheme, result.netloc])
  except ValueError:
    return False


class LabHandler(JupyterHandler):
    """Render the JupyterLab View."""

    def initialize(self, lab_config):
        self.lab_config = lab_config
        self.file_loader = FileSystemLoader(lab_config.templates_dir)

    @web.authenticated
    @web.removeslash
    def get(self):
        self.application.store_id = getattr(self.application, 'store_id', 0)
        config = self.lab_config
        settings_dir = config.app_settings_dir

        # Handle page config data.
        page_config = self.settings.setdefault('page_config_data', {})
        terminals = self.settings.get('terminals_available', False)
        server_root = self.settings.get('server_root_dir', '')
        server_root = server_root.replace(os.sep, '/')
        base_url = self.settings.get('base_url')

        page_config.setdefault('terminalsAvailable', terminals)
        page_config.setdefault('ignorePlugins', [])
        page_config.setdefault('serverRoot', server_root)
        page_config['store_id'] = self.application.store_id
        self.application.store_id += 1

        mathjax_config = self.settings.get('mathjax_config',
                                           'TeX-AMS_HTML-full,Safe')
        page_config.setdefault('mathjaxConfig', mathjax_config)
        page_config.setdefault('fullMathjaxUrl', self.mathjax_url)

        # Put all our config in page_config
        for name in config.trait_names():
            page_config[_camelCase(name)] = getattr(config, name)

        # Add full versions of all the urls
        for name in config.trait_names():
            if not name.endswith('_url'):
                continue
            full_name = _camelCase('full_' + name)
            full_url = getattr(config, name)
            if not is_url(full_url):
                # Relative URL will be prefixed with base_url
                full_url = ujoin(base_url, full_url)
            page_config[full_name] = full_url

        # Load the current page config file if available.
        page_config_file = os.path.join(settings_dir, 'page_config.json')
        if os.path.exists(page_config_file):
            with open(page_config_file) as fid:
                try:
                    page_config.update(json.load(fid))
                except Exception as e:
                    print(e)

        # Write the template with the config.
        self.write(self.render_template('index.html', page_config=page_config))

    def get_template(self, name):
        return self.file_loader.load(self.settings['jinja2_env'], name)

    def render_template(self, name, **ns):
        try:
            return JupyterHandler.render_template(self, name, **ns)
        except TemplateError:
            return DEFAULT_TEMPLATE.generate(
                name=name, path=self.lab_config.templates_dir
            )


class LabConfig(HasTraits):
    """The lab application configuration object.
    """
    app_name = Unicode('', help='The name of the application.')

    app_version = Unicode('', help='The version of the application.')

    app_namespace = Unicode('', help='The namespace of the application.')

    app_url = Unicode('/lab', help='The url path for the application.')

    app_settings_dir = Unicode('', help='The application settings directory.')

    templates_dir = Unicode('', help='The application templates directory.')

    static_dir = Unicode('',
                         help=('The optional location of local static files. '
                               'If given, a static file handler will be '
                               'added.'))

    static_url = Unicode(help=('The url path for static application '
                               'assets. This can be a CDN if desired.'))

    settings_url = Unicode(help='The url path of the settings handler.')

    user_settings_dir = Unicode('',
                                help=('The optional location of the user '
                                      'settings directory.'))

    schemas_dir = Unicode('',
                          help=('The optional location of the settings '
                                'schemas directory. If given, a handler will '
                                'be added for settings.'))

    workspaces_api_url = Unicode(help='The url path of the workspaces API.')

    workspaces_dir = Unicode('',
                             help=('The optional location of the saved '
                                   'workspaces directory. If given, a handler '
                                   'will be added for workspaces.'))

    workspaces_url = Unicode(help='The url path of the workspaces handler.')

    listings_url = Unicode(help='The listings url.')

    themes_url = Unicode(help='The theme url.')

    themes_dir = Unicode('',
                         help=('The optional location of the themes '
                               'directory. If given, a handler will be added '
                               'for themes.'))

    tree_url = Unicode(help='The url path of the tree handler.')

    cache_files = Bool(True,
                       help=('Whether to cache files on the server. '
                             'This should be `True` except in dev mode.'))

    @default('static_url')
    def _default_static_url(self):
        return ujoin('static/', self.app_url)

    @default('workspaces_url')
    def _default_workspaces_url(self):
        return ujoin(self.app_url, 'workspaces/')

    @default('workspaces_api_url')
    def _default_workspaces_api_url(self):
        return ujoin(self.app_url, 'api', 'workspaces/')

    @default('settings_url')
    def _default_settings_url(self):
        return ujoin(self.app_url, 'api', 'settings/')

    @default('listings_url')
    def _default_listings_url(self):
        return ujoin(self.app_url, 'api', 'listings/')

    @default('themes_url')
    def _default_themes_url(self):
        return ujoin(self.app_url, 'api', 'themes/')

    @default('tree_url')
    def _default_tree_url(self):
        return ujoin(self.app_url, 'tree/')


class NotFoundHandler(LabHandler):
    def render_template(self, name, **ns):
        if 'page_config' in ns:
            ns['page_config'] = ns['page_config'].copy()
            ns['page_config']['notFoundUrl'] = self.request.path
        return LabHandler.render_template(self, name, **ns)


def add_handlers(web_app, config):
    """Add the appropriate handlers to the web app.
    """
    # Normalize directories.
    for name in config.trait_names():
        if not name.endswith('_dir'):
            continue
        value = getattr(config, name)
        setattr(config, name, value.replace(os.sep, '/'))

    # Normalize urls
    # Local urls should have a leading slash but no trailing slash
    for name in config.trait_names():
        if not name.endswith('_url'):
            continue
        value = getattr(config, name)
        if is_url(value):
            continue
        if not value.startswith('/'):
            value = '/' + value
        if value.endswith('/'):
            value = value[:-1]
        setattr(config, name, value)

    # Set up the main page handler and tree handler.
    base_url = web_app.settings['base_url']
    lab_path = ujoin(base_url, config.app_url)
    tree_path = ujoin(base_url, config.tree_url, r'.+')
    handlers = [
        (lab_path, LabHandler, {'lab_config': config}),
        (tree_path, LabHandler, {'lab_config': config})
    ]

    # Cache all or none of the files depending on the `cache_files` setting.
    no_cache_paths = [] if config.cache_files else ['/']

    # Handle local static assets.
    if config.static_dir:
        static_path = ujoin(base_url, config.static_url, '(.*)')
        handlers.append((static_path, FileFindHandler, {
            'path': config.static_dir,
            'no_cache_paths': no_cache_paths
        }))

    # Handle local settings.
    if config.schemas_dir:
        settings_config = {
            'app_settings_dir': config.app_settings_dir,
            'schemas_dir': config.schemas_dir,
            'settings_dir': config.user_settings_dir
        }

        # Handle requests for the list of settings. Make slash optional.
        settings_path = ujoin(base_url, config.settings_url, '?')
        handlers.append((settings_path, SettingsHandler, settings_config))

        # Handle requests for an individual set of settings.
        setting_path = ujoin(
            base_url, config.settings_url, '(?P<schema_name>.+)')
        handlers.append((setting_path, SettingsHandler, settings_config))

    # Handle saved workspaces.
    if config.workspaces_dir:
        # Handle JupyterLab client URLs that include workspaces.
        workspaces_path = ujoin(base_url, config.workspaces_url, r'.+')
        handlers.append((workspaces_path, LabHandler, {'lab_config': config}))

        workspaces_config = {
            'workspaces_url': config.workspaces_url,
            'path': config.workspaces_dir
        }

        # Handle requests for the list of workspaces. Make slash optional.
        workspaces_api_path = ujoin(base_url, config.workspaces_api_url, '?')
        handlers.append((
            workspaces_api_path, WorkspacesHandler, workspaces_config))

        # Handle requests for an individually named workspace.
        workspace_api_path = ujoin(
            base_url, config.workspaces_api_url, '(?P<space_name>.+)')
        handlers.append((
            workspace_api_path, WorkspacesHandler, workspaces_config))

    # Handle local listings.

    settings_config = web_app.settings.get('config', {}).get('LabServerApp', {})
    blacklist_uris = settings_config.get('blacklist_uris', '')
    whitelist_uris = settings_config.get('whitelist_uris', '')

    if (blacklist_uris) and (whitelist_uris):
        print('Simultaneous blacklist_uris and whitelist_uris is not supported. Please define only one of those.')
        import sys
        sys.exit(-1)

    ListingsHandler.listings_refresh_seconds = settings_config.get('listings_refresh_seconds', 60 * 60)
    ListingsHandler.listings_request_opts = settings_config.get('listings_request_options', {})
    listings_url = ujoin(base_url, config.listings_url)
    listings_path = ujoin(listings_url, '(.*)')

    if blacklist_uris:
        ListingsHandler.blacklist_uris = set(blacklist_uris.split(','))
    if whitelist_uris:
        ListingsHandler.whitelist_uris = set(whitelist_uris.split(','))
    
    fetch_listings(None)

    if len(ListingsHandler.blacklist_uris) > 0 or len(ListingsHandler.whitelist_uris) > 0:
        from tornado import ioloop
        ListingsHandler.pc = ioloop.PeriodicCallback(
            lambda: fetch_listings(None),
            callback_time=ListingsHandler.listings_refresh_seconds * 1000,
            jitter=0.1
            )
        ListingsHandler.pc.start()

    handlers.append((listings_path, ListingsHandler, {}))

    # Handle local themes.
    if config.themes_dir:
        themes_url = ujoin(base_url, config.themes_url)
        themes_path = ujoin(themes_url, '(.*)')
        handlers.append((
            themes_path,
            ThemesHandler,
            {
                'themes_url': themes_url,
                'path': config.themes_dir,
                'no_cache_paths': no_cache_paths
            }
        ))

    # Let the lab handler act as the fallthrough option instead of a 404.
    fallthrough_url = ujoin(base_url, config.app_url, r'.*')
    handlers.append((fallthrough_url, NotFoundHandler, {'lab_config': config}))

    web_app.add_handlers('.*$', handlers)


def _camelCase(base):
    """Convert a string to camelCase.
    https://stackoverflow.com/a/20744956
    """
    output = ''.join(x for x in base.title() if x.isalpha())
    return output[0].lower() + output[1:]
