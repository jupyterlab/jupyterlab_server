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
        self.set_header('Content-Type', 'application/json')
        workspace_path = os.path.join(self.workspaces_dir, space_name)
        if os.path.exists(workspace_path):
            with open(workspace_path) as fid:
                # Attempt to load and parse the workspace file.
                try:
                    workspace = json.load(fid)
                except Exception as e:
                    raise web.HTTPError(500, str(e))
        else:
            raise web.HTTPError(404, 'Workspace not found: %r' % space_name)

        self.finish(json.dumps(dict(id=space_name, workspace=workspace)))

    @json_errors
    @web.authenticated
    def put(self, space_name):
        if not self.workspaces_dir:
            raise web.HTTPError(404, 'No current workspaces directory')

        raw = self.request.body.strip().decode(u'utf-8')

        # Make sure the data is valid JSON.
        try:
            decoder = json.JSONDecoder()
            decoder.decode(raw)
        except Exception as e:
            raise web.HTTPError(400, str(e))

        # Write the workspace data to a file.
        workspace_path = os.path.join(self.workspaces_dir, space_name)
        with open(workspace_path, 'w') as fid:
            fid.write(raw)

        self.set_status(204)
