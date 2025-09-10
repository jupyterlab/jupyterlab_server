.. Copyright (c) Jupyter Development Team.
.. Distributed under the terms of the Modified BSD License.

========
Handlers
========

Module: :mod:`jupyterlab_server.handlers`
=========================================

.. automodule:: jupyterlab_server.handlers

.. currentmodule:: jupyterlab_server.handlers

.. autoclass:: LabHandler
    :members:

.. rubric:: Page config hook

``page_config_hook`` is an optional callable you can provide via the Jupyter Server web application settings to customize the page configuration before it is rendered.

- Where: ``web_app.settings['page_config_hook']``
- Signature: ``callable(handler, page_config) -> dict``
    - ``handler``: the active ``LabHandler`` instance
    - ``page_config``: a dict containing the current page configuration
- Return: the updated page configuration dict.

Example (in a server extension ``load_jupyter_server_extension`` or ``_load_jupyter_server_extension``):

.. code-block:: python

        def my_page_config_hook(handler, page_config: dict) -> dict:
            page_config.setdefault("extraKeys", {})
            page_config["extraKeys"]["hello"] = "world"
            return page_config


        def load_jupyter_server_extension(serverapp):
            web_app = serverapp.web_app
            web_app.settings["page_config_hook"] = my_page_config_hook

With this hook set, JupyterLab Server will call it during page configuration assembly, letting you inject or tweak values prior to rendering the index page.

.. autofunction:: add_handlers

.. autofunction:: is_url


Module: :mod:`jupyterlab_server.listings_handler`
=================================================

.. automodule:: jupyterlab_server.listings_handler

.. currentmodule:: jupyterlab_server.listings_handler

.. autoclass:: ListingsHandler
    :members:

.. autofunction:: fetch_listings


Module: :mod:`jupyterlab_server.settings_handler`
=================================================

.. automodule:: jupyterlab_server.settings_handler

.. currentmodule:: jupyterlab_server.settings_handler

.. autoclass:: SettingsHandler
    :members:

.. autofunction:: get_settings


Module: :mod:`jupyterlab_server.themes_handler`
=================================================

.. automodule:: jupyterlab_server.themes_handler

.. currentmodule:: jupyterlab_server.themes_handler

.. autoclass:: ThemesHandler
    :members:


Module: :mod:`jupyterlab_server.translations_handler`
=====================================================

.. automodule:: jupyterlab_server.translations_handler

.. currentmodule:: jupyterlab_server.translations_handler

.. autoclass:: TranslationsHandler
    :members:


Module: :mod:`jupyterlab_server.workspaces_handler`
=====================================================

.. automodule:: jupyterlab_server.workspaces_handler

.. currentmodule:: jupyterlab_server.workspaces_handler

.. autoclass:: WorkspacesHandler
    :members:

.. autofunction:: slugify
