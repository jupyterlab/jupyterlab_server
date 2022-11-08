from unittest.mock import Mock

from tornado.httpserver import HTTPRequest
from tornado.web import Application

from jupyterlab_server.test_utils import validate_request
from jupyterlab_server.themes_handler import ThemesHandler


async def test_get_theme(jp_fetch, labserverapp):
    r = await jp_fetch("lab", "api", "themes", "@jupyterlab", "foo", "index.css")
    validate_request(r)


def test_themes_handler(tmp_path):
    app = Application()
    request = HTTPRequest(connection=Mock())
    data_path = f"{tmp_path}/test.txt"
    with open(data_path, "w") as fid:
        fid.write("hi")
    handler = ThemesHandler(app, request, path=str(tmp_path))
    handler.absolute_path = data_path
    handler.get_content_size()
    handler.get_content("test.txt")

    css_path = f"{tmp_path}/test.css"
    with open(css_path, "w") as fid:
        fid.write("url('./foo.css')")
    handler.absolute_path = css_path
    handler.path = "/"
    handler.themes_url = "foo"
    content = handler.get_content(css_path)
    assert content == b"url('foo/./foo.css')"
