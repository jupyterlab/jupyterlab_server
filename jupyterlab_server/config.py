# coding: utf-8
"""JupyterLab Server config"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from glob import glob
import json
from os.path import join as pjoin
import os.path as osp
import os

from jupyter_core.paths import jupyter_path
from jupyter_server.services.config.manager import ConfigManager, recursive_update
from traitlets import Bool, HasTraits, List, Unicode, default

from .server import url_path_join as ujoin


# -----------------------------------------------------------------------------
# Module globals
# -----------------------------------------------------------------------------

DEFAULT_TEMPLATE_PATH = osp.join(osp.dirname(__file__), 'templates')


def get_federated_extensions(labextensions_path):
    """Get the metadata about federated extensions
    """
    federated_exts = dict()
    for ext_dir in labextensions_path:
        ext_pattern = ext_dir + '/**/package.json'
        for ext_path in [path for path in glob(ext_pattern, recursive=True)]:
            with open(ext_path) as fid:
                data = json.load(fid)
            if data['name'] not in federated_exts:
                data['ext_dir'] = ext_dir
                data['ext_path'] = osp.dirname(ext_path)
                data['is_local'] = False
                federated_exts[data['name']] = data
    return federated_exts


def get_static_page_config(app_settings_dir=None, logger=None):
    # Start with the deprecated `share/jupyter/lab/settings/page_config.json` data

    cm = ConfigManager(config_dir_name="labconfig")
    page_config = cm.get('page_config')

    # TODO: remove in JupyterLab 4.0
    if app_settings_dir:
        keyname = 'disabled_labextensions'
        old_page_config = pjoin(app_settings_dir, 'page_config.json')
        if osp.exists(old_page_config):
            if logger:
                logger.warn('** Upgrading deprecated page_config in %s' % old_page_config)
                logger.warn('** This will no longer have an effect in JupyterLab 4.0')
                logger.warn('')
            with open(old_page_config) as fid:
                data = json.load(fid)
            os.remove(old_page_config)
            # Convert disabled_labextensions list to a dict
            oldKey = "disabledExtensions"
            if oldKey in data:
                data[keyname] = dict((key, True) for key in data[oldKey])
            del data[oldKey]

            recursive_update(page_config, data)
            cm.set('page_config', page_config)

    return page_config


def get_page_config(labextensions_path, app_settings_dir=None, logger=None):
    """Get the page config for the application"""
    page_config = get_static_page_config(app_settings_dir=app_settings_dir, logger=logger)

    # Handle federated extensions
    extensions = page_config['federated_extensions'] = []
    disabled_by_extensions_all = dict()

    federated_exts = get_federated_extensions(labextensions_path)

    for (ext, ext_data) in federated_exts.items():
        if not 'jupyterlab' in ext_data or not '_build' in ext_data['jupyterlab']:
            logger.warn('%s is not a valid extension' % ext_data['name'])
            continue
        extbuild = ext_data['jupyterlab']['_build']
        extension = {
            'name': ext_data['name'],
            'load': extbuild['load']
        }
        if 'extension' in extbuild:
            extension['extension'] = extbuild['extension']
        if 'mimeExtension' in extbuild:
            extension['mimeExtension'] = extbuild['mimeExtension']
        if 'style' in extbuild:
            extension['style'] = extbuild['style']
        extensions.append(extension)

        # If there is disabledExtensions metadata, consume it.
        if ext_data['jupyterlab'].get('disabledExtensions'):
            disabled_by_extensions_all[ext_data['name']] = ext_data['jupyterlab']['disabledExtensions']

    disabled_by_extensions = dict()
    for name in sorted(disabled_by_extensions_all):
        disabled_list = disabled_by_extensions_all[name]
        for item in disabled_list:
            disabled_by_extensions[item] = True

    disabled_extensions = disabled_by_extensions
    keyname = 'disabled_labextensions'
    disabled_extensions.update(page_config.get(keyname, []))
    page_config[keyname] = disabled_extensions
    
    return page_config


def write_page_config(page_config):
    """Write page config to disk"""
    cm = ConfigManager(config_dir_name='labconfig')
    cm.set('page_config', page_config)


class LabConfig(HasTraits):
    """The lab application configuration object.
    """
    app_name = Unicode('', help='The name of the application.')

    app_version = Unicode('', help='The version of the application.')

    app_namespace = Unicode('', help='The namespace of the application.')

    app_url = Unicode('/lab', help='The url path for the application.')

    app_settings_dir = Unicode('', help='The application settings directory.')

    extra_labextensions_path = List(Unicode(),
        help="""Extra paths to look for federated JupyterLab extensions"""
    )

    labextensions_path = List(Unicode(), help='The standard paths to look in for federated JupyterLab extensions')

    templates_dir = Unicode('', help='The application templates directory.')

    static_dir = Unicode('',
                         help=('The optional location of local static files. '
                               'If given, a static file handler will be '
                               'added.'))


    labextensions_url = Unicode('', help='The url for federated JupyterLab extensions')

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
        