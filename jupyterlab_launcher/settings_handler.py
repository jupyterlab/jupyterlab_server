"""Tornado handlers for frontend config storage."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os
from tornado import web
from .json_minify import json_minify

from notebook.base.handlers import APIHandler, json_errors

try:
    from jsonschema import ValidationError
    from jsonschema import Draft4Validator as Validator
except ImportError:
    Validator = None


_file_extension = ".jupyterlab-settings"


class SettingsHandler(APIHandler):

    def initialize(self, schemas_dir, settings_dir):
        self.schemas_dir = schemas_dir
        self.settings_dir = settings_dir

    @json_errors
    @web.authenticated
    def get(self, section_name):
        self.set_header("Content-Type", "application/json")

        schema = _get_schema(self.schemas_dir, section_name)
        path = _path(self.settings_dir, section_name, _file_extension)
        user = ''
        settings = dict()

        if os.path.exists(path):
            with open(path) as fid:
                # Attempt to load the settings file.
                try:
                    user = fid.read()
                    minified = json_minify(user)
                    settings = json.loads(minified)
                except Exception as e:
                    self.log.warn(str(e))

        # Validate the data against the schema.
        if Validator is not None and len(settings):
            validator = Validator(schema)
            try:
                validator.validate(settings)
            except ValidationError as e:
                self.log.warn(str(e))
                user = ''
                settings = dict()

        resp = dict(id=section_name, data=dict(user=user), schema=schema)
        self.finish(json.dumps(resp))

    @json_errors
    @web.authenticated
    def patch(self, section_name):
        if not self.settings_dir:
            raise web.HTTPError(404, "No current settings directory")

        # Will raise 400 if content is not valid JSON.
        data = self.get_json_body()

        # Validate the data against the schema.
        if Validator is not None:
            validator = Validator(_get_schema(self.schemas_dir, section_name))
            try:
                validator.validate(data)
            except ValidationError as e:
                raise web.HTTPError(400, str(e))

        path = _path(self.settings_dir, section_name, _file_extension, True)
        with open(path, "w") as fid:
            json.dump(data, fid)

        self.set_status(204)


def _get_schema(schemas_dir, section_name):
    """Retrieve and parse a JSON schema."""

    path = _path(schemas_dir, section_name)

    if not os.path.exists(path):
        raise web.HTTPError(404, "Schema not found: %r" % path)

    with open(path) as fid:
        # Attempt to load the schema file.
        try:
            schema = json.load(fid)
        except Exception as e:
            name = section_name
            message = "Failed parsing schema ({}): {}".format(name, str(e))
            raise web.HTTPError(500, message)

    return schema


def _path(root_dir, section_name, file_extension = ".json", make_dirs = False):
    """Parse the URL section name and find the local file system path."""

    parent_dir = root_dir

    # Attempt to parse path, e.g. @jupyterlab/apputils-extension:themes.
    try:
        package_dir, plugin = section_name.split(":")
        parent_dir = os.path.join(root_dir, package_dir)
        path = os.path.join(parent_dir, plugin + file_extension)
    # This is deprecated and exists to support the older URL scheme.
    except:
        path = os.path.join(root_dir, section_name + file_extension)

    if make_dirs and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir)
        except Exception as e:
            name = section_name
            message = "Failed writing settings ({}): {}".format(name, str(e))
            raise web.HTTPError(500, message)

    return path
