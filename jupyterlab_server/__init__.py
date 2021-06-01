# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from .app import LabServerApp
from .licenses_app import LicensesApp
from .handlers import add_handlers, LabHandler, LabConfig
from .workspaces_handler import slugify, WORKSPACE_EXTENSION
from ._version import __version__

__all__ = [
    '__version__',
    'add_handlers',
    'LabConfig',
    'LabHandler',
    'LabServerApp',
    'slugify',
    'SETTINGS_EXTENSION',
    'WORKSPACE_EXTENSION'
]

def _jupyter_server_extension_points():
    return [
        {
            'module': 'jupyterlab_server',
            'app': LabServerApp
        }
    ]
