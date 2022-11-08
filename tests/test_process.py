import os
import sys
import warnings

import pytest

from jupyterlab_server.process import Process, WatchHelper, which
from jupyterlab_server.process_app import ProcessApp


def test_which():
    assert which("python")


async def test_process():
    p = Process([sys.executable, "--version"])
    p.get_log().info("test")
    assert p.wait() == 0

    p = Process([sys.executable, "--version"])
    p.get_log().info("test")
    assert await p.wait_async() == 0
    assert p.terminate() == 0


@pytest.mark.skipif(os.name == "nt", reason="Fails on Windows")
async def test_watch_helper():
    helper = WatchHelper([sys.executable, "-i"], ">>>")
    helper.terminate()
    helper.wait()


def test_process_app():
    class TestApp(ProcessApp):
        name = "tests"

    app = TestApp()
    app.initialize_server([])
    try:
        app.initialize()
        with pytest.raises(SystemExit):
            app.start()
    # Kandle exception on older versions of server.
    except Exception as e:
        # Convert to warning so the test will pass on min version test.
        warnings.warn(str(e))
