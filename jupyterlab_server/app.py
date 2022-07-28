"""JupyterLab Server Application"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from jupyter_server.extension.application import ExtensionApp, ExtensionAppJinjaMixin
from traitlets import Dict, Integer, Unicode, observe

from ._version import __version__
from .handlers import LabConfig, add_handlers


class LabServerApp(ExtensionAppJinjaMixin, LabConfig, ExtensionApp):
    """A Lab Server Application that runs out-of-the-box"""

    name = "jupyterlab_server"
    extension_url = "/lab"
    app_name = "JupyterLab Server Application"
    file_url_prefix = "/lab/tree"

    @property
    def app_namespace(self):
        return self.name

    default_url = Unicode("/lab", help="The default URL to redirect to from `/`")

    # Should your extension expose other server extensions when launched directly?
    load_other_extensions = True

    app_version = Unicode("", help="The version of the application.").tag(default=__version__)

    blocked_extensions_uris = Unicode(
        "",
        config=True,
        help="""
        A list of comma-separated URIs to get the blocked extensions list
        """,
    )

    allowed_extensions_uris = Unicode(
        "",
        config=True,
        help="""
        A list of comma-separated URIs to get the allowed extensions list
        """,
    )

    listings_refresh_seconds = Integer(
        60 * 60, config=True, help="The interval delay in seconds to refresh the lists"
    )

    listings_tornado_options = Dict(
        {},
        config=True,
        help="The optional kwargs to use for the listings HTTP requests \
            as described on https://www.tornadoweb.org/en/stable/httpclient.html#tornado.httpclient.HTTPRequest",
    )

    def initialize_templates(self):
        self.static_paths = [self.static_dir]
        self.template_paths = [self.templates_dir]

    def initialize_settings(self):
        settings = self.serverapp.web_app.settings
        # By default, make terminals available.
        settings.setdefault("terminals_available", True)

    def initialize_handlers(self):
        add_handlers(self.handlers, self)


main = launch_new_instance = LabServerApp.launch_instance
