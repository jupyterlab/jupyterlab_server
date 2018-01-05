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

    @json_errors
    @web.authenticated
    def get(self, space_name):
        directory = self.workspaces_dir
        self.set_header('Content-Type', 'application/json')
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
        directory = self.workspaces_dir
        if not directory:
            raise web.HTTPError(500, 'No current workspaces directory')

        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
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
        if workspace['metadata']['id'] != space_name:
            message = 'Workspace metadata ID mismatch: %r' % space_name
            raise web.HTTPError(400, message)

        # Write the workspace data to a file.
        workspace_path = os.path.join(directory, space_name + _file_extension)
        with open(workspace_path, 'w') as fid:
            fid.write(raw)

        self.set_status(204)
