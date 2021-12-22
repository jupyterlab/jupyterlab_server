# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from .app import LabServerApp
from .licenses_app import LicensesApp
from .handlers import add_handlers, LabHandler, LabConfig
from .translation_utils import translator
from .workspaces_app import WorkspaceExportApp, WorkspaceImportApp, WorkspaceListApp
from .workspaces_handler import slugify, WORKSPACE_EXTENSION
from ._version import __version__

__all__ = [
    '__version__',
    'add_handlers',
    'LabConfig',
    'LabHandler',
    'LabServerApp',
    'LicensesApp',
    'SETTINGS_EXTENSION',
    'slugify',
    'translator',
    'WORKSPACE_EXTENSION',
    'WorkspaceExportApp',
    'WorkspaceImportApp',
    'WorkspaceListApp'
]

def _jupyter_server_extension_points():
    return [
        {
            'module': 'jupyterlab_server',
            'app': LabServerApp
        }
    ]
