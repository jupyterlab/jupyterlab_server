import pytest, shutil, os

from jupyterlab_server import LabServerApp, LabConfig

from traitlets import Unicode

from jupyterlab_server.tests.utils import here
from jupyterlab_server.app import LabServerApp

def mkdir(tmp_path, *parts):
    path = tmp_path.joinpath(*parts)
    if not path.exists():
        path.mkdir(parents=True)
    return path

app_settings_dir = pytest.fixture(lambda tmp_path: mkdir(tmp_path, 'app_settings'))
user_settings_dir = pytest.fixture(lambda tmp_path: mkdir(tmp_path, 'user_settings'))
schemas_dir = pytest.fixture(lambda tmp_path: mkdir(tmp_path, 'schemas'))
workspaces_dir = pytest.fixture(lambda tmp_path: mkdir(tmp_path, 'workspaces'))

@pytest.fixture
def make_labserver_extension_app(
    root_dir,
    template_dir,
    app_settings_dir,
    user_settings_dir,
    schemas_dir,
    workspaces_dir
    ):

    def _make_labserver_extension_app(**kwargs):

        return LabServerApp(
            static_dir = str(root_dir),
            templates_dir = str(template_dir),
            app_url = '/lab',
            app_settings_dir = str(app_settings_dir),
            user_settings_dir = str(user_settings_dir),
            schemas_dir = str(schemas_dir),
            workspaces_dir = str(workspaces_dir)
        )

    # Create the index files.
    index = template_dir.joinpath('index.html')
    index.write_text("""
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
""")

    # Copy the schema files.
    src = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'tests',
        'schemas',
        '@jupyterlab')
    dst = os.path.join(str(schemas_dir), '@jupyterlab')
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    # Copy the overrides file.
    src = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'tests',
        'app-settings',
        'overrides.json')
    dst = os.path.join(str(app_settings_dir), 'overrides.json')
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copyfile(src, dst)

    # Copy workspaces.
    data = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'tests',
        'workspaces')
    for item in os.listdir(data):
        src = os.path.join(data, item)
        dst = os.path.join(str(workspaces_dir), item)
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy(src, str(workspaces_dir))

    return _make_labserver_extension_app


@pytest.fixture
def labserverapp(serverapp, make_labserver_extension_app):
    app = make_labserver_extension_app()
    app._link_jupyter_server_extension(serverapp)
    app.initialize()
    return app
