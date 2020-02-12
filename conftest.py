import pytest

from jupyterlab_server import LabServerApp, LabConfig

from traitlets import Unicode

pytest_plugins = "pytest_jupyter_server"

from jupyterlab_server.tests.utils import here
from jupyterlab_server.app import LabServerApp

@pytest.fixture
def make_lab_extension_app(root_dir, template_dir):
    def _make_lab_extension_app(**kwargs):
        class TestLabServerApp(LabServerApp):
            base_url = '/lab'
            default_url = Unicode('/',
                                help='The default URL to redirect to from `/`')
            lab_config = LabConfig(
                app_name = 'JupyterLab Test App',
                static_dir = str(root_dir),
                templates_dir = str(template_dir),
                app_url = '/',
            )
        app = TestLabServerApp()
        return app
    index = template_dir.joinpath("index.html")
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
    return _make_lab_extension_app


@pytest.fixture
def labserverapp(serverapp, make_lab_extension_app):
    app = make_lab_extension_app()
    app.initialize(serverapp)
    return app
