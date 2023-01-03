"""pytest fixtures."""
import json
import os
import os.path as osp
import shutil
from os.path import join as pjoin

import pytest

from jupyterlab_server import LabServerApp

pytest_plugins = ["pytest_jupyter.jupyter_server"]


def mkdir(tmp_path, *parts):
    """Util for making a directory."""
    path = tmp_path.joinpath(*parts)
    if not path.exists():
        path.mkdir(parents=True)
    return path


HERE = os.path.abspath(os.path.dirname(__file__))

app_settings_dir = pytest.fixture(lambda tmp_path: mkdir(tmp_path, "app_settings"))
user_settings_dir = pytest.fixture(lambda tmp_path: mkdir(tmp_path, "user_settings"))
schemas_dir = pytest.fixture(lambda tmp_path: mkdir(tmp_path, "schemas"))
workspaces_dir = pytest.fixture(lambda tmp_path: mkdir(tmp_path, "workspaces"))
labextensions_dir = pytest.fixture(lambda tmp_path: mkdir(tmp_path, "labextensions_dir"))


@pytest.fixture
def make_labserver_extension_app(
    jp_root_dir,
    jp_template_dir,
    app_settings_dir,
    user_settings_dir,
    schemas_dir,
    workspaces_dir,
    labextensions_dir,
):
    """Return a factory function for a labserver extension app."""

    def _make_labserver_extension_app(**kwargs):
        """Factory function for lab server extension apps."""
        return LabServerApp(
            static_dir=str(jp_root_dir),
            templates_dir=str(jp_template_dir),
            app_url="/lab",
            app_settings_dir=str(app_settings_dir),
            user_settings_dir=str(user_settings_dir),
            schemas_dir=str(schemas_dir),
            workspaces_dir=str(workspaces_dir),
            extra_labextensions_path=[str(labextensions_dir)],
        )

    # Create the index files.
    index = jp_template_dir.joinpath("index.html")
    index.write_text(
        """
<!DOCTYPE html>
<html>
<head>
  <title>{{page_config['appName'] | e}}</title>
</head>
<body>
    {# Copy so we do not modify the page_config with updates. #}
    {% set page_config_full = page_config.copy() %}

    {# Set a dummy variable - we just want the side effect of the update. #}
    {% set _ = page_config_full.update(baseUrl=base_url, wsUrl=ws_url) %}

      <script id="jupyter-config-data" type="application/json">
        {{ page_config_full | tojson }}
      </script>
  <script src="{{page_config['fullStaticUrl'] | e}}/bundle.js" main="index"></script>

  <script type="text/javascript">
    /* Remove token from URL. */
    (function () {
      var parsedUrl = new URL(window.location.href);
      if (parsedUrl.searchParams.get('token')) {
        parsedUrl.searchParams.delete('token');
        window.history.replaceState({ }, '', parsedUrl.href);
      }
    })();
  </script>
</body>
</html>
"""
    )

    # Copy the schema files.
    src = pjoin(HERE, "test_data", "schemas", "@jupyterlab")
    dst = pjoin(str(schemas_dir), "@jupyterlab")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    # Create the federated extensions
    for name in ["apputils-extension", "codemirror-extension"]:
        target_name = name + "-federated"
        target = pjoin(str(labextensions_dir), "@jupyterlab", target_name)
        src = pjoin(HERE, "test_data", "schemas", "@jupyterlab", name)
        dst = pjoin(target, "schemas", "@jupyterlab", target_name)
        if osp.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        with open(pjoin(target, "package.orig.json"), "w") as fid:
            data = dict(name=target_name, jupyterlab=dict(extension=True))
            json.dump(data, fid)

    # Copy the overrides file.
    src = pjoin(HERE, "test_data", "app-settings", "overrides.json")
    dst = pjoin(str(app_settings_dir), "overrides.json")
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copyfile(src, dst)

    # Copy workspaces.
    ws_path = pjoin(HERE, "test_data", "workspaces")
    for item in os.listdir(ws_path):
        src = pjoin(ws_path, item)
        dst = pjoin(str(workspaces_dir), item)
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy(src, str(workspaces_dir))

    return _make_labserver_extension_app


@pytest.fixture
def labserverapp(jp_serverapp, make_labserver_extension_app):
    """A lab server app."""
    app = make_labserver_extension_app()
    app._link_jupyter_server_extension(jp_serverapp)
    app.initialize()
    return app
