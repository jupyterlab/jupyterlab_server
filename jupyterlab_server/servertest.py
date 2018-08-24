# Shim for notebook server or jupyter_server
#
# Provides:
#  - ServerTestBase
#  - assert_http_error
#

try:
    from notebook.tests.launchnotebook import (
        assert_http_error,
        NotebookTestBase as ServerTestBase
    )
except ImportError:
    from jupyter_server.tests.launchnotebook import assert_http_error   # noqa
    from jupyter_server.tests.launchserver import ServerTestBase        # noqa
