import errno
import os
import sys
from contextlib import contextmanager

import tornado


here = os.path.dirname(__file__)


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
