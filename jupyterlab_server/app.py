# coding: utf-8
"""JupyterLab Server"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from traitlets import Unicode, Integer, Dict

from .server import ServerApp
from .handlers import add_handlers, LabConfig


class LabServerApp(ServerApp):

    default_url = Unicode('/lab',
                          help='The default URL to redirect to from `/`')

    lab_config = LabConfig()

    blacklist_uris = Unicode('', config=True,
        help="A list of comma-separated URIs to get the blacklist")

    whitelist_uris = Unicode('', config=True,
        help="A list of comma-separated URIs to get the whitelist")

    listings_refresh_seconds = Integer(60 * 60, config=True,
        help="The interval delay in seconds to refresh the lists")

    listings_request_options = Dict({}, config=True,
        help="The optional kwargs to use for the listings HTTP requests \
            as described on https://2.python-requests.org/en/v2.7.0/api/#requests.request")

    def start(self):
        add_handlers(self.web_app, self.lab_config)
        super().start()


main = LabServerApp.launch_instance
