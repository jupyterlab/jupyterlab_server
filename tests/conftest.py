import os
import sys

os.environ["JUPYTER_PLATFORM_DIRS"] = "1"
pytest_plugins = ["jupyterlab_server.pytest_plugin"]

if sys.implementation.name.lower() == "pypy":
    import warnings

    warnings.filterwarnings("ignore")
