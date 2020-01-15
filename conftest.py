import pytest
from jupyterlab_server.app import LabServerApp

pytest_plugins = "pytest_jupyter_server"

@pytest.fixture
def labserverapp(serverapp):
    app = LabServerApp()
    app.initialize(serverapp)
    return app
