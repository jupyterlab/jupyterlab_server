
from .utils import validate_request


async def test_get_theme(jp_fetch, labserverapp):
    r = await jp_fetch("lab", "api", "themes", "@jupyterlab", "foo", "index.css")
    validate_request(r)
