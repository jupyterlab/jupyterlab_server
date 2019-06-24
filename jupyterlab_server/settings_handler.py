"""Tornado handlers for frontend config storage."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import json
import os

from glob import glob
import json5
from jsonschema import ValidationError
from jsonschema import Draft4Validator as Validator
from tornado import web

from .server import APIHandler, json_errors


# The JupyterLab settings file extension.
SETTINGS_EXTENSION = '.jupyterlab-settings'


def _get_schema(schemas_dir, schema_name, overrides):
    """Returns a dict containing a parsed and validated JSON schema."""

    path = _path(schemas_dir, schema_name)
    notfound_error = 'Schema not found: %s'
    parse_error = 'Failed parsing schema (%s): %s'
    validation_error = 'Failed validating schema (%s): %s'

    if not os.path.exists(path):
        raise web.HTTPError(404, notfound_error % path)

    with open(path) as fid:
        # Attempt to load the schema file.
        try:
            schema = json.load(fid)
        except Exception as e:
            name = schema_name
            raise web.HTTPError(500, parse_error % (name, str(e)))

    schema = _override(schema_name, schema, overrides)

    # Validate the schema.
    try:
        Validator.check_schema(schema)
    except Exception as e:
        name = schema_name
        raise web.HTTPError(500, validation_error % (name, str(e)))

    return schema


def _get_settings(settings_dir, schema_name, schema):
    """
    Returns a tuple containing the raw user settings, the parsed user
    settings, and a validation warning for a schema.
    """

    path = _path(settings_dir, schema_name, False, SETTINGS_EXTENSION)
    raw = '{}'
    settings = dict()
    warning = ''
    validation_warning = 'Failed validating settings (%s): %s'
    parse_error = 'Failed loading settings (%s): %s'

    if os.path.exists(path):
        with open(path) as fid:
            try:  # to load and parse the settings file.
                raw = fid.read() or raw
                settings = json5.loads(raw)
            except Exception as e:
                raise web.HTTPError(500, parse_error % (schema_name, str(e)))

    # Validate the parsed data against the schema.
    if len(settings):
        validator = Validator(schema)
        try:
            validator.validate(settings)
        except ValidationError as e:
            warning = validation_warning % (schema_name, str(e))
            raw = '{}'

    return (raw, settings, warning)


def _get_version(schemas_dir, schema_name):
    """Returns the package version for a given schema or 'N/A' if not found."""

    path = _path(schemas_dir, schema_name)
    package_path = os.path.join(os.path.split(path)[0], 'package.json.orig')

    try:  # to load and parse the package.json.orig file.
        with open(package_path) as fid:
            package = json.load(fid)
            return package['version']
    except Exception:
        return 'N/A'


def _list_settings(schemas_dir, settings_dir, overrides, extension='.json'):
    """
    Returns a tuple containing:
     - the list of plugins, schemas, and their settings,
       respecting any defaults that may have been overridden.
     - the list of warnings that were generated when
       validating the user overrides against the schemas.
    """

    settings_list = []
    warnings = []

    if not os.path.exists(schemas_dir):
        return (settings_list, warnings)

    schema_pattern = schemas_dir + '/**/*' + extension
    schema_paths = [path for path in glob(schema_pattern, recursive=True)]
    schema_paths.sort()

    for schema_path in schema_paths:
        # Generate the schema_name used to request individual settings.
        rel_path = os.path.relpath(schema_path, schemas_dir)
        rel_schema_dir, schema_base = os.path.split(rel_path)
        id = schema_name = ':'.join([
            rel_schema_dir,
            schema_base[:-len(extension)]  # Remove file extension.
        ]).replace('\\', '/')               # Normalize slashes.
        schema = _get_schema(schemas_dir, schema_name, overrides)
        raw, settings, warning = _get_settings(
            settings_dir, schema_name, schema)
        version = _get_version(schemas_dir, schema_name)

        if warning:
            warnings.append(warning)

        # Add the plugin to the list of settings.
        settings_list.append(dict(
            id=id,
            raw=raw,
            schema=schema,
            settings=settings,
            version=version
        ))

    return (settings_list, warnings)


def _override(schema_name, schema, overrides):
    """Override default values in the schema if necessary."""

    if schema_name in overrides:
        defaults = overrides[schema_name]
        for key in defaults:
            if key in schema['properties']:
                schema['properties'][key]['default'] = defaults[key]
            else:
                schema['properties'][key] = dict(default=defaults[key])

    return schema


def _path(root_dir, schema_name, make_dirs=False, extension='.json'):
    """
    Returns the local file system path for a schema name in the given root
    directory. This function can be used to filed user overrides in addition to
    schema files. If the `make_dirs` flag is set to `True` it will create the
    parent directory for the calculated path if it does not exist.
    """

    parent_dir = root_dir
    notfound_error = 'Settings not found (%s)'
    write_error = 'Failed writing settings (%s): %s'

    try:  # to parse path, e.g. @jupyterlab/apputils-extension:themes.
        package_dir, plugin = schema_name.split(':')
        parent_dir = os.path.join(root_dir, package_dir)
        path = os.path.join(parent_dir, plugin + extension)
    except Exception:
        raise web.HTTPError(404, notfound_error % schema_name)

    if make_dirs and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir)
        except Exception as e:
            raise web.HTTPError(500, write_error % (schema_name, str(e)))

    return path


class SettingsHandler(APIHandler):

    def initialize(self, app_settings_dir, schemas_dir, settings_dir):
        self.overrides = dict()
        self.schemas_dir = schemas_dir
        self.settings_dir = settings_dir

        overrides_path = os.path.join(app_settings_dir, 'overrides.json')
        overrides_warning = 'Failed loading overrides: %s'

        if os.path.exists(overrides_path):
            with open(overrides_path) as fid:
                try:
                    self.overrides = json.load(fid)
                except Exception as e:
                    self.log.warn(overrides_warning % str(e))

    @web.authenticated
    def get(self, schema_name=''):
        overrides = self.overrides
        schemas_dir = self.schemas_dir
        settings_dir = self.settings_dir

        if not schema_name:
            settings_list, warnings = _list_settings(
                schemas_dir, settings_dir, overrides)
            if warnings:
                self.log.warn('\n'.join(warnings))
            return self.finish(json.dumps(dict(settings=settings_list)))

        schema = _get_schema(schemas_dir, schema_name, overrides)
        raw, settings, warning = _get_settings(
            settings_dir, schema_name, schema)
        version = _get_version(schemas_dir, schema_name)

        if warning:
            self.log.warn(warning)

        self.finish(json.dumps(dict(
            id=schema_name,
            raw=raw,
            schema=schema,
            settings=settings,
            version=version
        )))

    @web.authenticated
    def put(self, schema_name):
        overrides = self.overrides
        schemas_dir = self.schemas_dir
        settings_dir = self.settings_dir
        settings_error = 'No current settings directory'
        validation_error = 'Failed validating input: %s'

        if not settings_dir:
            raise web.HTTPError(500, settings_error)

        raw = self.request.body.strip().decode(u'utf-8')

        # Validate the data against the schema.
        schema = _get_schema(schemas_dir, schema_name, overrides)
        validator = Validator(schema)
        try:
            validator.validate(json5.loads(raw))
        except ValidationError as e:
            raise web.HTTPError(400, validation_error % str(e))

        # Write the raw data (comments included) to a file.
        path = _path(settings_dir, schema_name, True, SETTINGS_EXTENSION)
        with open(path, 'w') as fid:
            fid.write(raw)

        self.set_status(204)
