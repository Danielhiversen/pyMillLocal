"""Test helpers"""

import json
import pathlib
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import ClientResponseError, ClientSession


class FakeResponse:
    """Minimal stand-in for aiohttp.ClientResponse."""

    def __init__(self, method, url, status, body):
        self.status = status
        self.reason = HTTPStatus(status).phrase
        self._body = body
        self._request_info = MagicMock(real_url=url, method=method)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def json(self):
        return json.loads(self._body) if self._body else None

    def raise_for_status(self):
        if self.status >= 400:
            raise ClientResponseError(
                self._request_info, (), status=self.status, message=self.reason
            )


class MockedSession:
    """Register canned responses and record calls made through ClientSession.get/post."""

    def __init__(self):
        self._responses = {}
        self.calls = []

    def get(self, url, status=200, payload=None, body=""):
        self._register("GET", url, status, payload, body)

    def post(self, url, status=200, payload=None, body=""):
        self._register("POST", url, status, payload, body)

    def assert_called_once_with(self, **expected):
        assert self.calls == [expected]

    def _register(self, method, url, status, payload, body):
        if payload is not None:
            body = json.dumps(payload)
        self._responses.setdefault((method, url), []).append((status, body))

    def _handle(self, method, **kwargs):
        self.calls.append({"method": method, **kwargs})
        status, body = self._responses[(method, kwargs["url"])].pop(0)
        return FakeResponse(method, kwargs["url"], status, body)


@pytest.fixture
def mocked_response():
    mock = MockedSession()
    with patch.object(
        ClientSession, "get", lambda self, **kw: mock._handle("GET", **kw)
    ), patch.object(
        ClientSession, "post", lambda self, **kw: mock._handle("POST", **kw)
    ):
        yield mock


@pytest.fixture(autouse=True)
async def client_session():
    """Fixture to execute asserts before and after a test is run"""
    # Setup
    client_session = ClientSession()

    yield client_session

    # Teardown
    await client_session.close()


@pytest.fixture(scope="session")
def status_command_response():
    """A response for GET /status request."""
    return load_fixture("status_command_response.json")


@pytest.fixture(scope="session")
def control_status_response():
    """A response for GET /control-status call."""
    return load_fixture("control_status_response.json")


@pytest.fixture(scope="session")
def generic_status_ok_response():
    """A generic response with status OK."""
    return load_fixture("generic_status_ok_response.json")


@pytest.fixture(scope="session")
def oil_heater_power_response():
    """A generic response with status OK."""
    return load_fixture("oil_heater_power_response.json")


def load_fixture(name: str):
    """Load a fixture from disk."""
    path = pathlib.Path(__file__).parent / "fixtures" / name

    content = path.read_text()

    if name.endswith(".json"):
        return json.loads(content)

    return content
