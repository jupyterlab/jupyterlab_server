"""Tornado handlers for dynamic listings loading."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import time
import json
import re

from .server import FileFindHandler

import requests


LISTINGS_URL_SUFFIX='@jupyterlab/extensionmanager-extension/listings.json'


def init_listings_uris(abs_path):
    with open(abs_path, 'rb') as fid:
        data = fid.read().decode('utf-8')
    listings = json.loads(data)
    if len(ListingsHandler.blacklist_uris) == 0:
        for b in listings['listings']['blacklist_uris']:
            ListingsHandler.blacklist_uris.add(b)
    if len(ListingsHandler.whitelist_uris) == 0:
        for w in listings['listings']['whitelist_uris']:
            ListingsHandler.whitelist_uris.add(w)


def fetch_listings():
    print('Fetching Blacklist from {}'.format(ListingsHandler.blacklist_uris))
    blacklist = []
    for blacklist_uri in ListingsHandler.blacklist_uris:
        r = requests.request('GET', blacklist_uri, **ListingsHandler.listings_request_opts)
        j = json.loads(r.text)
        for b in j['blacklist']:
            blacklist.append(b)
    ListingsHandler.blacklist = blacklist
    print('Fetching Whitelist from {}'.format(ListingsHandler.whitelist_uris))
    whitelist = []
    for whitelist_uri in ListingsHandler.whitelist_uris:
        r = requests.request('GET', whitelist_uri, **ListingsHandler.listings_request_opts)
        j = json.loads(r.text)
        for w in j['whitelist']:
            whitelist.append(w)
    ListingsHandler.whitelist = whitelist
    j = {
        'blacklist_uris': list(ListingsHandler.blacklist_uris),
        'whitelist_uris': list(ListingsHandler.whitelist_uris),
        'blacklist': ListingsHandler.blacklist,
        'whitelist': ListingsHandler.whitelist,
    }
    ListingsHandler.listings = json.dumps(j)


class ListingsHandler(FileFindHandler):
    """A file handler that returns file content from the listings directory."""

    blacklist_uris = set()
    whitelist_uris = set()
    blacklist = []
    whitelist = []
    listings = ''
    listings_request_opts = {}
    pc = None

    def initialize(self, path, default_filename=None,
                   no_cache_paths=None):

        FileFindHandler.initialize(self, path,
                                   default_filename=default_filename,
                                   no_cache_paths=no_cache_paths)
        if len(ListingsHandler.blacklist_uris) > 0 or len(ListingsHandler.whitelist_uris) > 0:
            from tornado import ioloop
            ListingsHandler.pc = ioloop.PeriodicCallback(
                fetch_listings,
                callback_time=ListingsHandler.listings_refresh_ms,
                jitter=0.1
                )
            ListingsHandler.pc.start()

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
