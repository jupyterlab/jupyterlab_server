"""Tornado handlers for dynamic listings loading."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import json
import re

from .server import FileFindHandler

import requests


LISTINGS_URL_SUFFIX='@jupyterlab/extensionmanager-extension/listings.json'


class ListingsHandler(FileFindHandler):
    """A file handler that returns file content from the listings directory."""

    blacklist_uris = set()
    whitelist_uris = set()
    blacklist = set()
    whitelist = set()
    listings = ""
    initialized = False

    def initialize(self, path, default_filename=None,
                   no_cache_paths=None, listings_url=None):

        FileFindHandler.initialize(self, path,
                                   default_filename=default_filename,
                                   no_cache_paths=no_cache_paths)

        if not ListingsHandler.initialized:

            if type(self.config['LabServerApp']['blacklist_uris']) == str:
                ListingsHandler.blacklist_uris = set(self.config['LabServerApp']['blacklist_uris'].split(','))
            if type(self.config['LabServerApp']['whitelist_uris']) == str:
                ListingsHandler.whitelist_uris = set(self.config['LabServerApp']['whitelist_uris'].split(','))

            self.init_listings_uris(os.path.join(path, LISTINGS_URL_SUFFIX))
            self.fetch_listings_uris()

            j = {
                'blacklist_uris': list(ListingsHandler.blacklist_uris),
                'whitelist_uris': list(ListingsHandler.whitelist_uris),
                'blacklist': list(ListingsHandler.blacklist),
                'whitelist': list(ListingsHandler.whitelist)
            }
            ListingsHandler.listings = json.dumps(j)
            print(ListingsHandler.listings)

            ListingsHandler.initialized = True


    def init_listings_uris(self, abs_path):
        with open(abs_path, 'rb') as fid:
            data = fid.read().decode('utf-8')
        listings = json.loads(data)
        if len(ListingsHandler.blacklist_uris) == 0:
            for b in listings['listings']['blacklist_uris']:
                ListingsHandler.blacklist_uris.add(b)
        if len(ListingsHandler.whitelist_uris) == 0:
            for w in listings['listings']['whitelist_uris']:
                ListingsHandler.whitelist_uris.add(w)


    def fetch_listings_uris(self):
        for ListingsHandler.blacklist_uri in ListingsHandler.blacklist_uris:
            r = requests.get(ListingsHandler.blacklist_uri)
            j = json.loads(r.text)
            for b in j['blacklist']:
                ListingsHandler.blacklist.add(b)
        for ListingsHandler.whitelist_uri in ListingsHandler.whitelist_uris:
            r = requests.get(ListingsHandler.whitelist_uri)
            j = json.loads(r.text)
            for w in j['whitelist']:
                ListingsHandler.whitelist.add(w)


    def get_content(self, abspath, start=None, end=None):
        """Retrieve the content of the requested resource which is located
        at the given absolute path.

        This method should either return a byte string or an iterator
        of byte strings.
        """
        if not abspath.endswith(LISTINGS_URL_SUFFIX):
            return FileFindHandler.get_content(abspath, start, end)

        self.set_header('Content-Type', 'application/json')
        return self._get_listings()


    def get_content_size(self):
        """Retrieve the total size of the resource at the given path."""
        if not self.absolute_path.endswith(LISTINGS_URL_SUFFIX):
            return FileFindHandler.get_content_size(self)

        return len(self._get_listings())


    def _get_listings(self):
        return ListingsHandler.listings
