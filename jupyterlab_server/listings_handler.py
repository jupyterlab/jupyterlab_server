"""Tornado handlers for dynamic listings loading."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import json
import re

from .server import FileFindHandler


LISTINGS='@jupyterlab/extensionmanager-extension/listings.json'

class ListingsHandler(FileFindHandler):
    """A file handler that returns file conttent from the listings directory."""


    def initialize(self, path, default_filename=None,
                   no_cache_paths=None, listings_url=None):
        FileFindHandler.initialize(self, path,
                                   default_filename=default_filename,
                                   no_cache_paths=no_cache_paths)
        if type(self.config['LabServerApp']['blacklist_uri']) == str:
            self.blacklist_uri = self.config['LabServerApp']['blacklist_uri']
        else:
            self.blacklist_uri = ''
        if type(self.config['LabServerApp']['whitelist_uri']) == str:
            self.whitelist_uri = self.config['LabServerApp']['whitelist_uri']
        else:
            self.whitelist_uri = ''

    def get_content(self, abspath, start=None, end=None):
        """Retrieve the content of the requested resource which is located
        at the given absolute path.

        This method should either return a byte string or an iterator
        of byte strings.
        """
        if not abspath.endswith(LISTINGS):
            return FileFindHandler.get_content(abspath, start, end)

        return self._get_listings()

    def get_content_size(self):
        """Retrieve the total size of the resource at the given path."""
        if not self.absolute_path.endswith(LISTINGS):
            return FileFindHandler.get_content_size(self)

        return len(self._get_listings())

    def _get_listings(self):
        with open(self.absolute_path, 'rb') as fid:
            data = fid.read().decode('utf-8')
        listings = json.loads(data)
        if self.blacklist_uri != '':
            listings['listings']['blacklist_uri'] = self.blacklist_uri
        if self.whitelist_uri != '':
            listings['listings']['whitelist_uri'] = self.whitelist_uri
        return json.dumps(listings)
