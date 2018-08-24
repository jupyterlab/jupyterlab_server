# Shim for notebook server or jupyter_server
#
# Provides:
#  - JupyterHandler
#  - FileFindHandler
#  - APIHandler
#  - json_errors
#  - url_path_join
#  - ServerApp
#
# Also provides the constants GREEN_ENABLED, GREEN_OK, RED_DISABLED, RED_X

try:
    from notebook.base.handlers import (
        APIHandler,
        FileFindHandler,
        IPythonHandler as JupyterHandler,
        json_errors
    )
    from notebook.notebookapp import aliases, flags, NotebookApp as ServerApp
    from notebook.serverextensions import (
        GREEN_ENABLED, GREEN_OK, RED_DISABLED, RED_X
    )
    from notebook.utils import url_escape, url_path_join
except ImportError:
    from jupyter_server.base.handlers import (                          # noqa
        APIHandler, FileFindHandler, json_errors, JupyterHandler
    )
    from jupyter_server.extensions import (                             # noqa
        GREEN_ENABLED, GREEN_OK, RED_DISABLED, RED_X
    )
    from jupyter_server.serverapp import ServerApp, aliases, flags      # noqa
    from jupyter_server.utils import url_escape, url_path_join          # noqa
