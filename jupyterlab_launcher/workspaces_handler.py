"""Tornado handlers for frontend config storage."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os
from tornado import web

from notebook.base.handlers import APIHandler, json_errors


_file_extension = '.jupyterlab-workspace'


class WorkspacesHandler(APIHandler):

    def initialize(self, path, default_filename=None, workspaces_url=None):
        self.workspaces_dir = path

    def ensure_directory(self):
        if not self.workspaces_dir:
            raise web.HTTPError(500, 'No current workspaces directory set')

    @json_errors
    @web.authenticated
    def delete(self, space_name):
        self.set_header('Content-Type', 'application/json')
        self.ensure_directory()
        directory = self.workspaces_dir

        if not space_name:
            raise web.HTTPError(400, 'Workspace name is required for DELETE')

        workspace_path = os.path.join(directory, space_name + _file_extension)
        if not os.path.exists(workspace_path):
            raise web.HTTPError(404, 'Workspace not found: %r' % space_name)

        # Attempt to delete the workspace file.
        try:
            os.remove(workspace_path)
        except Exception as e:
            raise web.HTTPError(500, str(e))

        self.set_status(204)

    @json_errors
    @web.authenticated
    def get(self, space_name=''):
        self.set_header('Content-Type', 'application/json')
        self.ensure_directory()
        directory = self.workspaces_dir

        if not space_name:
            raise web.HTTPError(404, 'Workspaces list not yet implemented')

        workspace_path = os.path.join(directory, space_name + _file_extension)
        if os.path.exists(workspace_path):
            with open(workspace_path) as fid:
                # Attempt to load and parse the workspace file.
                try:
                    workspace = json.load(fid)
                except Exception as e:
                    raise web.HTTPError(500, str(e))
        else:
            raise web.HTTPError(404, 'Workspace not found: %r' % space_name)

        self.finish(json.dumps(workspace))

    @json_errors
    @web.authenticated
    def put(self, space_name):
        self.ensure_directory()
        directory = self.workspaces_dir

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
            message = ('Workspace metadata ID mismatch: expected "%r" got "%r"'
                       % (space_name, metadata_id))
            raise web.HTTPError(400, message)

        # Write the workspace data to a file.
        workspace_path = os.path.join(directory, space_name + _file_extension)
        with open(workspace_path, 'w') as fid:
            fid.write(raw)

        self.set_status(204)
