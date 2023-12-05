"""Test helpers """

import json
import pathlib

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses


# See https://github.com/pnuckowski/aioresponses/issues/218
@pytest.fixture
def mocked_response():
    with aioresponses() as m:
        yield m


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
