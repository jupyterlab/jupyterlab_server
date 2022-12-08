import os

os.environ["JUPYTER_PLATFORM_DIRS"] = "1"
pytest_plugins = ["pytest_jupyter.jupyter_server"]
