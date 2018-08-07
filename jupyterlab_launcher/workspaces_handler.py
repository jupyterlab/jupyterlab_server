"""Tornado handlers for frontend config storage."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import hashlib
import json
import os
import re

from notebook.base.handlers import APIHandler, json_errors
from notebook.utils import url_path_join as ujoin
from tornado import web
from translitcodec import codecs
from urllib.parse import unquote


# A cache of workspace names and their slug file name counterparts.
_cache = dict()

# The JupyterLab workspace file extension.
_file_extension = '.jupyterlab-workspace'

# Regular expression for transforming a URL path into a slug.
# cf. http://flask.pocoo.org/snippets/5/
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def _list_workspaces(directory, prefix):
    workspaces = []
    if not os.path.exists(directory):
        return workspaces

    items = [item
             for item in os.listdir(directory)
             if item.startswith(prefix) and
             item.endswith(_file_extension)]
    items.sort()

    for slug in items:
        if slug in _cache:
            workspaces.append(_cache[slug])
            continue
        workspace_path = os.path.join(directory, slug)
        if os.path.exists(workspace_path):
            with open(workspace_path) as fid:
                try:  # to load and parse the workspace file.
                    _cache[slug] = json.load(fid)['metadata']['id']
                    workspaces.append(_cache[slug])
                except Exception as e:
                    raise web.HTTPError(500, str(e))
    return workspaces


def _slug(raw, base, sign=True):
    """Transform a raw workspace name as a file system safe slug."""
    result = []
    raw = ujoin(base, raw)
    raw = unquote(raw)
    for word in _punct_re.split(raw.lower()):
        word = codecs.encode(word, 'translit/long')
        if word:
            result.append(word)
    if sign:
        signature = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:4]
        result.append(signature)
    return u'-'.join(result)


class WorkspacesHandler(APIHandler):

    def initialize(self, path, workspaces_url=None):
        self.workspaces_dir = path

    def ensure_directory(self):
        """Return the workspaces directory if set or raise error if not set."""
        if not self.workspaces_dir:
            raise web.HTTPError(500, 'Workspaces directory is not set')

        return self.workspaces_dir

    @json_errors
    @web.authenticated
    def delete(self, space_name):
        base_url = self.settings['base_url']
        directory = self.ensure_directory()

        if not space_name:
            raise web.HTTPError(400, 'Workspace name is required for DELETE')

        slug = _slug(space_name, base_url)
        workspace_path = os.path.join(directory, slug + _file_extension)

        if not os.path.exists(workspace_path):
            raise web.HTTPError(404, 'Workspace %r not found' % space_name)

        try:  # to delete the workspace file.
            os.remove(workspace_path)
            return self.set_status(204)
        except Exception as e:
            raise web.HTTPError(500, str(e))

    @json_errors
    @web.authenticated
    def get(self, space_name=''):
        base_url = self.settings['base_url']
        directory = self.ensure_directory()

        if not space_name:
            prefix = _slug('', base_url, sign=False)
            workspaces = _list_workspaces(directory, prefix)
            return self.finish(json.dumps(dict(workspaces=workspaces)))

        slug = _slug(space_name, base_url)
        workspace_path = os.path.join(directory, slug + _file_extension)

        if os.path.exists(workspace_path):
            with open(workspace_path) as fid:
                try:  # to load and parse the workspace file.
                    return self.finish(json.dumps(json.load(fid)))
                except Exception as e:
                    raise web.HTTPError(500, str(e))
        else:
            raise web.HTTPError(404, 'Workspace %r not found' % space_name)

    @json_errors
    @web.authenticated
    def put(self, space_name):
        base_url = self.settings['base_url']
        directory = self.ensure_directory()

        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception as e:
                raise web.HTTPError(500, str(e))

        raw = self.request.body.strip().decode(u'utf-8')
        workspace = dict()

        # Make sure the data is valid JSON.
        try:
            decoder = json.JSONDecoder()
            workspace = decoder.decode(raw)
        except Exception as e:
            raise web.HTTPError(400, str(e))

        # Make sure metadata ID matches the workspace name.
        metadata_id = workspace['metadata']['id']
        if metadata_id != space_name:
            message = ('Workspace metadata ID mismatch: expected %r got %r'
                       % (space_name, metadata_id))
            raise web.HTTPError(400, message)

        slug = _slug(space_name, base_url)
        workspace_path = os.path.join(directory, slug + _file_extension)

        # Write the workspace data to a file.
        with open(workspace_path, 'w') as fid:
            fid.write(raw)

        self.set_status(204)
