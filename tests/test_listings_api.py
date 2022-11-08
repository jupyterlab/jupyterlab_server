import json

import requests_mock

from jupyterlab_server.listings_handler import ListingsHandler, fetch_listings
from jupyterlab_server.test_utils import validate_request


async def test_get_listing(jp_fetch, labserverapp):
    url = r"lab/api/listings/@jupyterlab/extensionmanager-extension/listings.json"
    r = await jp_fetch(*url.split("/"))
    validate_request(r)


def test_fetch_listings():
    ListingsHandler.allowed_extensions_uris = ["http://foo"]
    ListingsHandler.blocked_extensions_uris = ["http://bar"]
    with requests_mock.Mocker() as m:
        data = dict(blocked_extensions=[])
        m.get("http://bar", text=json.dumps(data))
        data = dict(allowed_extensions=[])
        m.get("http://foo", text=json.dumps(data))
        fetch_listings(None)
    ListingsHandler.allowed_extensions_uris = []
    ListingsHandler.blocked_extensions_uris = []
