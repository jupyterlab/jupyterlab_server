"""Tornado handlers for frontend config storage."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os
from tornado import web

from notebook.base.handlers import APIHandler, json_errors


_file_extension = '.jupyterlab-session'


class SessionsHandler(APIHandler):

    def initialize(self, path, default_filename=None, sessions_url=None):
        self.sessions_dir = path

    @json_errors
    @web.authenticated
    def get(self, section_name):
        self.set_header('Content-Type', 'application/json')
        session_path = os.path.join(self.sessions_dir, section_name)
        if os.path.exists(session_path):
            with open(session_path) as fid:
                # Attempt to load and parse the session file.
                try:
                    session = json.load(fid)
                except Exception as e:
                    raise web.HTTPError(500, str(e))
        else:
            raise web.HTTPError(404, 'Session not found: %r' % section_name)

        self.finish(json.dumps(dict(id=section_name, session=session)))

    @json_errors
    @web.authenticated
    def put(self, section_name):
        if not self.sessions_dir:
            raise web.HTTPError(404, 'No current sessions directory')

        raw = self.request.body.strip().decode(u'utf-8')

        # Make sure the data is valid JSON.
        try:
            decoder = json.JSONDecoder()
            decoder.decode(raw)
        except Exception as e:
            raise web.HTTPError(400, str(e))

        # Write the session data to a file.
        session_path = os.path.join(self.sessions_dir, section_name)
        with open(session_path, 'w') as fid:
            fid.write(raw)

        self.set_status(204)
