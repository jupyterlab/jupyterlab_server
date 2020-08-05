# coding: utf-8
"""JupyterLab Server handlers"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os
from urllib.parse import urlparse

from jinja2 import FileSystemLoader, TemplateError
from tornado import template, web
from traitlets import Bool, HasTraits, List, Unicode, default

from jupyter_core.paths import jupyter_path
from jupyter_server.extension.handler import ExtensionHandlerMixin, ExtensionHandlerJinjaMixin

from .listings_handler import ListingsHandler, fetch_listings
from .server import FileFindHandler, JupyterHandler
from .server import url_path_join as ujoin
from .settings_handler import SettingsHandler
from .themes_handler import ThemesHandler
from .translations_handler import TranslationsHandler
from .workspaces_handler import WorkspacesHandler

# -----------------------------------------------------------------------------
# Module globals
# -----------------------------------------------------------------------------

DEFAULT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')

MASTER_URL_PATTERN = '/(?P<mode>{}|doc)(?P<workspace>/workspaces/[a-zA-Z0-9\-\_]+)?(?P<tree>/tree/.*)?'

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


class LabHandler(ExtensionHandlerJinjaMixin, ExtensionHandlerMixin, JupyterHandler):
    """Render the JupyterLab View."""

    def initialize(self, name, lab_config={}):
        super().initialize(name)
        self.lab_config = lab_config
        
    @web.authenticated
    @web.removeslash
    def get(self, mode = None, workspace = None, tree = None):
        workspace = 'default' if workspace is None else workspace.replace('/workspaces/','')
        tree_path = '' if tree is None else tree.replace('/tree/','')

        self.application.store_id = getattr(self.application, 'store_id', 0)
        config = LabConfig()
        app = self.extensionapp
        settings_dir = app.app_settings_dir

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
        # TODO Remove CDN usage.
        mathjax_url = self.settings.get('mathjax_url',
                                           'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js')
        page_config.setdefault('mathjaxConfig', mathjax_config)
        page_config.setdefault('fullMathjaxUrl', mathjax_url)

        # Add parameters parsed from the URL
        if mode == 'doc':   
            page_config['mode'] = 'single-document'
        else:
            page_config['mode'] = 'multiple-document'
        page_config['workspace'] = workspace
        page_config['treePath'] = tree_path
        
        # Put all our config in page_config
        for name in config.trait_names():
            page_config[_camelCase(name)] = getattr(app, name)

        # Add full versions of all the urls
        for name in config.trait_names():
            if not name.endswith('_url'):
                continue
            full_name = _camelCase('full_' + name)
            full_url = getattr(app, name)
            if not is_url(full_url):
                # Relative URL will be prefixed with base_url
                full_url = ujoin(base_url, full_url)
            page_config[full_name] = full_url

        # Load the current page config file if available.
        page_config_file = os.path.join(settings_dir, 'page_config.json')
        if os.path.exists(page_config_file):
            with open(page_config_file, encoding='utf-8') as fid:
                try:
                    page_config.update(json.load(fid))
                except Exception as e:
                    print(e)

        # Write the template with the config.
        tpl = self.render_template('index.html', page_config=page_config)
        self.write(tpl)


class LabConfig(HasTraits):
    """The lab application configuration object.
    """
    app_name = Unicode('', help='The name of the application.')

    app_version = Unicode('', help='The version of the application.')

    app_namespace = Unicode('', help='The namespace of the application.')

    app_url = Unicode('/lab', help='The url path for the application.')

    app_settings_dir = Unicode('', help='The application settings directory.')

    extra_labextensions_path = List(Unicode(),
        help="""Extra paths to look for dynamic JupyterLab extensions"""
    )

    labextensions_path = List(Unicode(), help='The standard paths to look in for dynamic JupyterLab extensions')

    templates_dir = Unicode('', help='The application templates directory.')

    static_dir = Unicode('',
                         help=('The optional location of local static files. '
                               'If given, a static file handler will be '
                               'added.'))

    static_url = Unicode(help=('The url path for static application '
                               'assets. This can be a CDN if desired.'))


    labextensions_url = Unicode('', help='The url for dynamic JupyterLab extensions')

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

    listings_url = Unicode(help='The listings url.')

    themes_url = Unicode(help='The theme url.')

    themes_dir = Unicode('',
                         help=('The optional location of the themes '
                               'directory. If given, a handler will be added '
                               'for themes.'))

    translations_api_url = Unicode(help='The url path of the translations handler.')
 
    tree_url = Unicode(help='The url path of the tree handler.')

    cache_files = Bool(True,
                       help=('Whether to cache files on the server. '
                             'This should be `True` except in dev mode.'))

    @default('template_dir')
    def _default_template_dir(self):
        return DEFAULT_TEMPLATE_PATH

    @default('static_url')
    def _default_static_url(self):
        return ujoin('static/', self.app_namespace)

    @default('labextensions_url')
    def _default_labextensions_url(self):
        return ujoin(self.app_url, "extensions/")

    @default('labextensions_path')
    def _default_labextensions_path(self):
        return jupyter_path('labextensions')

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
        
    @default('translations_api_url')
    def _default_translations_api_url(self):
        return ujoin(self.app_url, 'api', 'translations/')

    @default('tree_url')
    def _default_tree_url(self):
        return ujoin(self.app_url, 'tree/')


class NotFoundHandler(LabHandler):
    def render_template(self, name, **ns):
        if 'page_config' in ns:
            ns['page_config'] = ns['page_config'].copy()
            ns['page_config']['notFoundUrl'] = self.request.path
        return super().render_template(name, **ns)


def add_handlers(handlers, app):
    """Add the appropriate handlers to the web app.
    """
    # Normalize directories.
    for name in LabConfig.class_trait_names():
        if not name.endswith('_dir'):
            continue
        value = getattr(app, name)
        setattr(app, name, value.replace(os.sep, '/'))

    # Normalize urls
    # Local urls should have a leading slash but no trailing slash
    for name in LabConfig.class_trait_names():
        if not name.endswith('_url'):
            continue
        value = getattr(app, name)
        if is_url(value):
            continue
        if not value.startswith('/'):
            value = '/' + value
        if value.endswith('/'):
            value = value[:-1]
        setattr(app, name, value)

    url_pattern = MASTER_URL_PATTERN.format(app.app_url.replace('/', ''))
    lab_path = ujoin(app.settings.get('base_url'), url_pattern)
    handlers.append((lab_path, LabHandler, {'lab_config': app}))

    # Cache all or none of the files depending on the `cache_files` setting.
    no_cache_paths = [] if app.cache_files else ['/']

    # Handle dynamic lab extensions.
    labextensions_path = app.extra_labextensions_path + app.labextensions_path
    labextensions_url = ujoin(app.labextensions_url, "(.*)")
    handlers.append(
        (labextensions_url, FileFindHandler, {
            'path': labextensions_path,
            'no_cache_paths': ['/'], # don't cache anything in labextensions
        }))

    # Handle local settings.
    if app.schemas_dir:
        settings_config = {
            'app_settings_dir': app.app_settings_dir,
            'schemas_dir': app.schemas_dir,
            'settings_dir': app.user_settings_dir,
            'labextensions_path': labextensions_path
        }

        # Handle requests for the list of settings. Make slash optional.
        settings_path = ujoin(app.settings_url, '?')
        handlers.append((settings_path, SettingsHandler, settings_config))

        # Handle requests for an individual set of settings.
        setting_path = ujoin(app.settings_url, '(?P<schema_name>.+)')
        handlers.append((setting_path, SettingsHandler, settings_config))

    # Handle saved workspaces.
    if app.workspaces_dir:

        workspaces_config = {
            'path': app.workspaces_dir
        }

        # Handle requests for the list of workspaces. Make slash optional.
        workspaces_api_path = ujoin(app.workspaces_api_url, '?')
        handlers.append((
            workspaces_api_path, WorkspacesHandler, workspaces_config))

        # Handle requests for an individually named workspace.
        workspace_api_path = ujoin(app.workspaces_api_url, '(?P<space_name>.+)')
        handlers.append((
            workspace_api_path, WorkspacesHandler, workspaces_config))

    # Handle local listings.

    settings_config = app.settings.get('config', {}).get('LabServerApp', {})
    blacklist_uris = settings_config.get('blacklist_uris', '')
    whitelist_uris = settings_config.get('whitelist_uris', '')

    if (blacklist_uris) and (whitelist_uris):
        print('Simultaneous blacklist_uris and whitelist_uris is not supported. Please define only one of those.')
        import sys
        sys.exit(-1)

    ListingsHandler.listings_refresh_seconds = settings_config.get('listings_refresh_seconds', 60 * 60)
    ListingsHandler.listings_request_opts = settings_config.get('listings_request_options', {})
    base_url = app.settings.get('base_url')
    listings_url = ujoin(base_url, app.listings_url)
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
    if app.themes_dir:
        themes_url = app.themes_url
        themes_path = ujoin(themes_url, '(.*)')
        handlers.append((
            themes_path,
            ThemesHandler,
            {
                'themes_url': themes_url,
                'path': app.themes_dir,
                'labextensions_path': labextensions_path,
                'no_cache_paths': no_cache_paths
            }
        ))

    # Handle translations.
    if app.translations_api_url:
        # Handle requests for the list of language packs available.
        # Make slash optional.
        translations_path = ujoin(base_url, app.translations_api_url, '?')
        handlers.append((translations_path, TranslationsHandler, {'lab_config': app}))

        # Handle requests for an individual language pack.
        translations_lang_path = ujoin(
            base_url, app.translations_api_url, '(?P<locale>.*)')
        handlers.append((translations_lang_path, TranslationsHandler, {'lab_config': app}))

    # Let the lab handler act as the fallthrough option instead of a 404.
    fallthrough_url = ujoin(app.app_url, r'.*')
    handlers.append((fallthrough_url, NotFoundHandler))


def _camelCase(base):
    """Convert a string to camelCase.
    https://stackoverflow.com/a/20744956
    """
    output = ''.join(x for x in base.title() if x.isalpha())
    return output[0].lower() + output[1:]
