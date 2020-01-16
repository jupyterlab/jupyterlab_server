import pytest
from jupyterlab_server.app import LabServerApp

pytest_plugins = "pytest_jupyter_server"

from jupyterlab_server.tests.utils import here
from jupyterlab_server.app import LabServerApp

@pytest.fixture
def make_lab_extension_app(template_dir):
    def _make_lab_extension_app(**kwargs):
        app = LabServerApp()
        app.template_paths = [str(template_dir)]
        app._prepare_templates()
        return app
    index = template_dir.joinpath("index.html")
    index.write_text("""
<!DOCTYPE HTML>
<html>
<head>
    <meta charset="utf-8">
    <title>{% block title %}Jupyter Server 1{% endblock %}</title>
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {% block meta %}
    {% endblock %}
</head>
<body>
  <div id="site">
    {% block site %}
    {% endblock site %}
  </div>
  {% block after_site %}
  {% endblock after_site %}
</body>
</html>""")
    return _make_lab_extension_app


@pytest.fixture
def labserverapp(serverapp, make_lab_extension_app):
    app = make_lab_extension_app()
    app.initialize(serverapp)
    return app
