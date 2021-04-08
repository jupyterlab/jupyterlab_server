
from .utils import validate_request


async def test_get_listing(jp_fetch, labserverapp):
    url = r"lab/api/listings/@jupyterlab/extensionmanager-extension/listings.json"
    r = await jp_fetch(*url.split('/'))
    validate_request(r)
