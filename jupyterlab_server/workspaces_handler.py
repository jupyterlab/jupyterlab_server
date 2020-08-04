"""Tornado handlers for frontend config storage."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import hashlib
import json
import os
import re
import unicodedata
import urllib
from datetime import datetime
from tornado import web

from .server import APIHandler, json_errors, url_path_join as ujoin, tz

from jupyter_server.extension.handler import ExtensionHandlerMixin, ExtensionHandlerJinjaMixin

# The JupyterLab workspace file extension.
WORKSPACE_EXTENSION = '.jupyterlab-workspace'

def _list_workspaces(directory, prefix):
    """
    Return the list of workspaces in a given directory beginning with the
    given prefix.
    """
    workspaces = { 'ids': [], 'values': [] }
    if not os.path.exists(directory):
        return workspaces

    items = [item
             for item in os.listdir(directory)
             if item.startswith(prefix) and
             item.endswith(WORKSPACE_EXTENSION)]
    items.sort()

    for slug in items:
        workspace_path = os.path.join(directory, slug)
        if os.path.exists(workspace_path):
            try:
                workspace = _load_with_file_times(workspace_path)
                workspaces.get('ids').append(workspace['metadata']['id'])
                workspaces.get('values').append(workspace)
            except Exception as e:
                raise web.HTTPError(500, str(e))

    return workspaces


def _load_with_file_times(workspace_path):
    """
    Load workspace JSON from disk, overwriting the `created` and `last_modified`
    metadata with current file stat information
    """
    stat = os.stat(workspace_path)
    with open(workspace_path, encoding='utf-8') as fid:
        workspace = json.load(fid)
        workspace["metadata"].update(
            last_modified=tz.utcfromtimestamp(stat.st_mtime).isoformat(),
            created=tz.utcfromtimestamp(stat.st_ctime).isoformat()
        )
    return workspace


def slugify(raw, base='', sign=True, max_length=128 - len(WORKSPACE_EXTENSION)):
    """
    Use the common superset of raw and base values to build a slug shorter
    than max_length. By default, base value is an empty string.
    Convert spaces to hyphens. Remove characters that aren't alphanumerics
    underscores, or hyphens. Convert to lowercase. Strip leading and trailing
    whitespace.
    Add an optional short signature suffix to prevent collisions.
    Modified from Django utils:
    https://github.com/django/django/blob/master/django/utils/text.py
    """
    raw = raw if raw.startswith('/') else '/' + raw
    signature = ''
    if sign:
        data = raw[1:]  # Remove initial slash that always exists for digest.
        signature = '-' + hashlib.sha256(data.encode('utf-8')).hexdigest()[:4]
    base = (base if base.startswith('/') else '/' + base).lower()
    raw = raw.lower()
    common = 0
    limit = min(len(base), len(raw))
    while common < limit and base[common] == raw[common]:
        common += 1
    value = ujoin(base[common:], raw)
    value = urllib.parse.unquote(value)
    value = (unicodedata
             .normalize('NFKC', value)
             .encode('ascii', 'ignore')
             .decode('ascii'))
    value = re.sub(r'[^\w\s-]', '', value).strip()
    value = re.sub(r'[-\s]+', '-', value)
    return value[:max_length - len(signature)] + signature


class WorkspacesHandler(ExtensionHandlerMixin, ExtensionHandlerJinjaMixin, APIHandler):

    def initialize(self, name, path, workspaces_url=None, **kwargs):
        super().initialize(name)
        self.workspaces_dir = path

    def ensure_directory(self):
        """Return the workspaces directory if set or raise error if not set."""
        if not self.workspaces_dir:
            raise web.HTTPError(500, 'Workspaces directory is not set')

        return self.workspaces_dir

    @web.authenticated
    def delete(self, space_name):
        directory = self.ensure_directory()

        if not space_name:
            raise web.HTTPError(400, 'Workspace name is required for DELETE')

        slug = slugify(space_name)
        workspace_path = os.path.join(directory, slug + WORKSPACE_EXTENSION)

        if not os.path.exists(workspace_path):
            raise web.HTTPError(404, 'Workspace %r (%r) not found' %
                                     (space_name, slug))

        try:  # to delete the workspace file.
            os.remove(workspace_path)
            return self.set_status(204)
        except Exception as e:
            raise web.HTTPError(500, str(e))

    @web.authenticated
    def get(self, space_name=''):
        directory = self.ensure_directory()

        if not space_name:
            prefix = slugify('', sign=False)
            workspaces = _list_workspaces(directory, prefix)
            return self.finish(json.dumps(dict(workspaces=workspaces)))

        slug = slugify(space_name)
        workspace_path = os.path.join(directory, slug + WORKSPACE_EXTENSION)

        if os.path.exists(workspace_path):
            try:  # to load and parse the workspace file.
                workspace = _load_with_file_times(workspace_path)
            except Exception as e:
                raise web.HTTPError(500, str(e))
        else:
            id = (space_name if space_name.startswith('/')
                             else '/' + space_name)
            workspace = dict(data=dict(), metadata=dict(id=id))

        return self.finish(json.dumps(workspace))

    @web.authenticated
    def put(self, space_name=''):
        if not space_name:
            raise web.HTTPError(400, 'Workspace name is required for PUT.')

        directory = self.ensure_directory()

        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception as e:
                raise web.HTTPError(500, str(e))

        raw = self.request.body.strip().decode('utf-8')
        workspace = dict()

        # Make sure the data is valid JSON.
        try:
            decoder = json.JSONDecoder()
            workspace = decoder.decode(raw)
        except Exception as e:
            raise web.HTTPError(400, str(e))

        # Make sure metadata ID matches the workspace name.
        # Transparently support an optional inital root `/`.
        metadata_id = workspace['metadata']['id']
        metadata_id = (metadata_id if metadata_id.startswith('/')
                       else '/' + metadata_id)
        metadata_id = urllib.parse.unquote(metadata_id)
        if metadata_id != '/' + space_name:
            message = ('Workspace metadata ID mismatch: expected %r got %r'
                       % (space_name, metadata_id))
            raise web.HTTPError(400, message)

        slug = slugify(space_name)
        workspace_path = os.path.join(directory, slug + WORKSPACE_EXTENSION)

        # Write the workspace data to a file.
        with open(workspace_path, 'w', encoding='utf-8') as fid:
            fid.write(raw)

        self.set_status(204)
