"""Tornado handlers for dynamic listings loading."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import time
import json
import re

from .server import APIHandler

import requests


LISTINGS_URL_SUFFIX='@jupyterlab/extensionmanager-extension/listings.json'


def fetch_listings():
    if len(ListingsHandler.blacklist_uris) > 0:
        blacklist = []
        for blacklist_uri in ListingsHandler.blacklist_uris:
            print('Fetching blacklist from {}'.format(ListingsHandler.blacklist_uris))
            r = requests.request('GET', blacklist_uri, **ListingsHandler.listings_request_opts)
            j = json.loads(r.text)
            for b in j['blacklist']:
                blacklist.append(b)
            ListingsHandler.blacklist = blacklist
    if len(ListingsHandler.whitelist_uris) > 0:
        whitelist = []
        for whitelist_uri in ListingsHandler.whitelist_uris:
            print('Fetching whitelist from {}'.format(ListingsHandler.whitelist_uris))
            r = requests.request('GET', whitelist_uri, **ListingsHandler.listings_request_opts)
            j = json.loads(r.text)
            for w in j['whitelist']:
                whitelist.append(w)
        ListingsHandler.whitelist = whitelist
    ListingsHandler.listings = json.dumps({
        'blacklist_uris': list(ListingsHandler.blacklist_uris),
        'whitelist_uris': list(ListingsHandler.whitelist_uris),
        'blacklist': ListingsHandler.blacklist,
        'whitelist': ListingsHandler.whitelist,
    })


class ListingsHandler(APIHandler):
    """An handler that returns the listings specs."""

    blacklist_uris = set()
    whitelist_uris = set()
    blacklist = []
    whitelist = []
    listings = ''
    listings_request_opts = {}
    pc = None

    def initialize(self):

        if len(ListingsHandler.blacklist_uris) > 0 or len(ListingsHandler.whitelist_uris) > 0:
            from tornado import ioloop
            ListingsHandler.pc = ioloop.PeriodicCallback(
                fetch_listings,
                callback_time=ListingsHandler.listings_refresh_ms,
                jitter=0.1
                )
            ListingsHandler.pc.start()

    def get(self, path):
        self.set_header('Content-Type', 'application/json')
        if path == LISTINGS_URL_SUFFIX:
            self.write(ListingsHandler.listings)
        else:
            self.write({})
