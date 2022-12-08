import json
import os
import sys

from jupyterlab_server.workspaces_app import (
    WorkspaceExportApp,
    WorkspaceImportApp,
    WorkspaceListApp,
)


def test_workspace_apps(jp_environ, tmp_path):

    sys.argv = [sys.argv[0]]

    data = {
        "data": {
            "layout-restorer:data": {
                "main": {
                    "dock": {
                        "type": "tab-area",
                        "currentIndex": 1,
                        "widgets": ["notebook:Untitled1.ipynb"],
                    },
                    "current": "notebook:Untitled1.ipynb",
                },
                "down": {"size": 0, "widgets": []},
                "left": {
                    "collapsed": False,
                    "current": "filebrowser",
                    "widgets": [
                        "filebrowser",
                        "running-sessions",
                        "@jupyterlab/toc:plugin",
                        "extensionmanager.main-view",
                    ],
                },
                "right": {
                    "collapsed": True,
                    "widgets": ["jp-property-inspector", "debugger-sidebar"],
                },
                "relativeSizes": [0.17370242214532872, 0.8262975778546713, 0],
            },
            "notebook:Untitled1.ipynb": {
                "data": {"path": "Untitled1.ipynb", "factory": "Notebook"}
            },
        },
        "metadata": {"id": "default"},
    }

    data_file = os.path.join(tmp_path, "test.json")
    with open(data_file, "w") as fid:
        json.dump(data, fid)

    app = WorkspaceImportApp(workspaces_dir=str(tmp_path))
    app.initialize()
    app.extra_args = [data_file]
    app.start()

    app1 = WorkspaceExportApp(workspaces_dir=str(tmp_path))
    app1.initialize()
    app1.start()

    app2 = WorkspaceListApp(workspaces_dir=str(tmp_path))
    app2.initialize()
    app2.start()

    app2.jsonlines = True
    app2.start()
