import errno
import json
import os
import sys
import requests
from contextlib import contextmanager

import tornado


here = os.path.dirname(__file__)

with open(
    os.path.join(here, 'app-settings', 'overrides.json'),
    encoding='utf-8'
) as fpt:
    big_unicode_string = json.load(fpt)["@jupyterlab/unicode-extension:plugin"]["comment"]


def maybe_patch_ioloop():
    """ a windows 3.8+ patch for the asyncio loop
    """
    if sys.platform.startswith("win"):
        if sys.version_info >= (3, 8):
            import asyncio
            try:
                from asyncio import (
                    WindowsProactorEventLoopPolicy,
                    WindowsSelectorEventLoopPolicy,
                )
            except ImportError:
                pass
                # not affected
            else:
                if type(asyncio.get_event_loop_policy()) is WindowsProactorEventLoopPolicy:
                    # WindowsProactorEventLoopPolicy is not compatible with tornado 6
                    # fallback to the pre-3.8 default of Selector
                    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())


def expected_http_error(error, expected_code, expected_message=None):
    """Check that the error matches the expected output error."""
    e = error.value
    if isinstance(e, tornado.web.HTTPError):
        if expected_code != e.status_code:
            return False
        if expected_message is not None and expected_message != str(e):
            return False
        return True
    elif any([
        isinstance(e, tornado.httpclient.HTTPClientError),
        isinstance(e, tornado.httpclient.HTTPError)
    ]):
        if expected_code != e.code:
            return False
        if expected_message:
            message = json.loads(e.response.body.decode())['message']
            if expected_message != message:
                return False
        return True

@contextmanager
def assert_http_error(status, msg=None):
    try:
        yield
    except requests.HTTPError as e:
        real_status = e.response.status_code
        assert real_status == status, \
                    "Expected status %d, got %d" % (status, real_status)
        if msg:
            assert msg in str(e), e
    else:
        assert False, "Expected HTTP error status"
