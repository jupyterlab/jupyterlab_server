"""Tornado handlers for frontend config storage."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os

from glob import glob
from jsonschema import ValidationError
from jsonschema import Draft4Validator as Validator
from tornado import web

from .json_minify import json_minify
from .server import APIHandler, json_errors


def _override(section_name, schema, overrides):
    """Override default values in the schema if necessary."""
    if section_name in overrides:
        defaults = overrides[section_name]
        for key in defaults:
            if key in schema['properties']:
                schema['properties'][key]['default'] = defaults[key]
            else:
                schema['properties'][key] = dict(default=defaults[key])
    return schema


def _list_settings(schemas_dir, settings_dir, overrides, extension='.json'):
    """
    Return the list of plugins, schemas, and their settings, respecting any
    defaults that may have been overridden.
    """
    settings = []
    if not os.path.exists(schemas_dir):
        return settings

    schema_pattern = schemas_dir + '/**/*' + extension
    schema_paths = [path for path in glob(schema_pattern, recursive=True)]
    schema_paths.sort()

    for schema_path in schema_paths:
        # Generate the section_name used to request individual settings.
        rel_path = os.path.relpath(schema_path, schemas_dir)
        section_dir, section_base = os.path.split(rel_path)
        section_name = ':'.join([
            section_dir,
            section_base[:-len(extension)]  # Remove file extension.
        ]).replace('\\', '/')               # Normalize slashes.

        # Create plugin dictionary to populate with schema and settings.
        plugin = dict(id=section_name)

        # Populate the schema and its default overrides.
        with open(schema_path) as fid:
            try:  # to load and parse the schema file.
                schema = json.load(fid)
                plugin['schema'] = _override(section_name, schema, overrides)
            except Exception as e:
                raise web.HTTPError(500, str(e))

        # Populate the user setting overrides.
        plugin_path = _path(settings_dir, section_name)
        plugin['raw'] = '{}'
        plugin['settings'] = dict()
        if os.path.exists(plugin_path):
            with open(plugin_path) as fid:
                try:  # to load and parse the settings file.
                    plugin['raw'] = fid.read() or plugin['raw']
                    plugin['settings'] = json.loads(json_minify(plugin['raw']))
                except Exception as e:
                    message = 'Failed loading settings (%s): %s'
                    raise web.HTTPError(500, message % (section_name, str(e)))

        # Add the plugin to the list of settings.
        settings.append(plugin)

    return settings


class SettingsHandler(APIHandler):

    def initialize(self, app_settings_dir, schemas_dir, settings_dir):
        self.overrides = dict()
        self.schemas_dir = schemas_dir
        self.settings_dir = settings_dir

        overrides_path = os.path.join(app_settings_dir, 'overrides.json')
        if os.path.exists(overrides_path):
            with open(overrides_path) as fid:
                try:
                    self.overrides = json.load(fid)
                except Exception as e:
                    self.log.warn('Failed loading overrides {}'.format(str(e)))

    @json_errors
    @web.authenticated
    def get(self, section_name=''):
        overrides = self.overrides
        schemas_dir = self.schemas_dir
        settings_dir = self.settings_dir

        if not section_name:
            settings = _list_settings(schemas_dir, settings_dir, overrides)
            return self.finish(json.dumps(dict(settings=settings)))

        schema = _get_schema(schemas_dir, section_name, overrides)
        path = _path(settings_dir, section_name)
        raw = '{}'
        settings = dict()

        if os.path.exists(path):
            with open(path) as fid:
                try:  # to load and parse the settings file.
                    raw = fid.read() or raw
                    settings = json.loads(json_minify(raw))
                except Exception as e:
                    message = 'Failed loading settings ({}): {}'
                    self.log.warn(message.format(section_name, str(e)))

        # Validate the parsed data against the schema.
        if len(settings):
            validator = Validator(schema)
            try:
                validator.validate(settings)
            except ValidationError as e:
                message = 'Failed validating settings ({}): {}'
                self.log.warn(message.format(section_name, str(e)))
                raw = '{}'

        # Send back the raw data to the client.
        resp = dict(id=section_name, raw=raw, schema=schema)
        self.finish(json.dumps(resp))

    @json_errors
    @web.authenticated
    def put(self, section_name):
        overrides = self.overrides
        schemas_dir = self.schemas_dir
        settings_dir = self.settings_dir

        if not settings_dir:
            raise web.HTTPError(404, 'No current settings directory')

        raw = self.request.body.strip().decode(u'utf-8')

        # Validate the data against the schema.
        schema = _get_schema(schemas_dir, section_name, overrides)
        validator = Validator(schema)
        try:
            validator.validate(json.loads(json_minify(raw)))
        except ValidationError as e:
            raise web.HTTPError(400, str(e))

        # Write the raw data (comments included) to a file.
        path = _path(settings_dir, section_name, True)
        with open(path, 'w') as fid:
            fid.write(raw)

        self.set_status(204)


def _get_schema(schemas_dir, section_name, overrides):
    """Retrieve and parse a JSON schema."""

    path = _path(schemas_dir, section_name)

    if not os.path.exists(path):
        raise web.HTTPError(404, 'Schema not found: %r' % path)

    with open(path) as fid:
        # Attempt to load the schema file.
        try:
            schema = json.load(fid)
        except Exception as e:
            name = section_name
            message = 'Failed parsing schema ({}): {}'.format(name, str(e))
            raise web.HTTPError(500, message)

    schema = _override(section_name, schema, overrides)

    # Validate the schema.
    try:
        Validator.check_schema(schema)
    except Exception as e:
        name = section_name
        message = 'Failed validating schema ({}): {}'.format(name, str(e))
        raise web.HTTPError(500, message)

    return schema


def _path(root_dir, section_name, make_dirs=False, extension='.json'):
    """Parse the URL section name and find the local file system path."""

    parent_dir = root_dir

    try:  # to parse path, e.g. @jupyterlab/apputils-extension:themes.
        package_dir, plugin = section_name.split(':')
        parent_dir = os.path.join(root_dir, package_dir)
        path = os.path.join(parent_dir, plugin + extension)
    except Exception:
        message = 'Settings not found ({})'.format(section_name)
        raise web.HTTPError(404, message)

    if make_dirs and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir)
        except Exception as e:
            name = section_name
            message = 'Failed writing settings ({}): {}'.format(name, str(e))
            raise web.HTTPError(500, message)

    return path
