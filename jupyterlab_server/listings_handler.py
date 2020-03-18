"""Tornado handlers for dynamic listings loading."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import time
import json
import re
import tornado

from .server import APIHandler

import requests


LISTINGS_URL_SUFFIX='@jupyterlab/extensionmanager-extension/listings.json'


def fetch_listings(log):
    def log_info(message):
        if log:
            return log.info(message)
        return print(message)
    if len(ListingsHandler.blacklist_uris) > 0:
        blacklist = []
        for blacklist_uri in ListingsHandler.blacklist_uris:
            log_info('Fetching blacklist from {}'.format(ListingsHandler.blacklist_uris))
            r = requests.request('GET', blacklist_uri, **ListingsHandler.listings_request_opts)
            j = json.loads(r.text)
            for b in j['blacklist']:
                blacklist.append(b)
            ListingsHandler.blacklist = blacklist
    if len(ListingsHandler.whitelist_uris) > 0:
        whitelist = []
        for whitelist_uri in ListingsHandler.whitelist_uris:
            log_info('Fetching whitelist from {}'.format(ListingsHandler.whitelist_uris))
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

    """Below fields are class level fields that are accessed and populated
    by the initialization and the fetch_listings methods.
    Some fields are initialized before the handler creation in the 
    handlers.py#add_handlers method.
    Having those fields predefined reduces the guards in the methods using
    them.
    """
    # The list of blacklist URIS.
    blacklist_uris = set()
    # The list of whitelist URIS.
    whitelist_uris = set()
    # The blacklisted extensions.
    blacklist = []
    # The whitelisted extensions.
    whitelist = []
    # The computed listing to be returned
    # It will contain the uris and the listings.
    listings = ''
    # The provider request options to be used for the request library.
    listings_request_opts = {}
    # The PeriodicCallback that schedule the call to fetch_listings method.
    pc = None


    def initialize(self):

        if len(ListingsHandler.blacklist_uris) > 0 or len(ListingsHandler.whitelist_uris) > 0:
            from tornado import ioloop
            ListingsHandler.pc = ioloop.PeriodicCallback(
                lambda: fetch_listings(self.log),
                callback_time=ListingsHandler.listings_refresh_ms,
                jitter=0.1
                )
            ListingsHandler.pc.start()

    def get(self, path):
        self.set_header('Content-Type', 'application/json')
        if path == LISTINGS_URL_SUFFIX:
            self.write(ListingsHandler.listings)
        else:
            raise tornado.web.HTTPError(400)
