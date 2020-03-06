"""Tornado handlers for dynamic listings loading."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from .server import FileFindHandler


class ListingsHandler(FileFindHandler):
    """A file handler that returns file conttent from the listings directory."""

    def initialize(self, path, default_filename=None,
                   no_cache_paths=None, listings_url=None):
        FileFindHandler.initialize(self, path,
                                   default_filename=default_filename,
                                   no_cache_paths=no_cache_paths)
