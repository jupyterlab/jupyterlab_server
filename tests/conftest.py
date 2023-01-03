# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os

os.environ["JUPYTER_PLATFORM_DIRS"] = "1"
pytest_plugins = ["jupyterlab_server.pytest_plugin"]
