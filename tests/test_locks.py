"""Verify independent device lock endpoints, validation and transport errors."""

import asyncio
import json
from unittest.mock import patch

import pytest
from aiohttp import ClientConnectionError, ClientResponseError

from mill_local import Mill

ADDRESS = "192.168.2.123"
LOCKS = ["child", "commercial"]


@pytest.mark.parametrize("lock", LOCKS)
@pytest.mark.parametrize("enabled", [True, False])
async def test_read_lock(mocked_response, client_session, lock, enabled):
    """Both getters return the endpoint response without changing the device."""
    url = f"http://{ADDRESS}/{lock}-lock"
    response = {"value": enabled, "status": "ok"}
    mocked_response.get(url, payload=response)
    mill = Mill(ADDRESS, client_session)

    assert await getattr(mill, f"fetch_{lock}_lock")() == response
    mocked_response.assert_called_once_with(method="GET", url=url)


@pytest.mark.parametrize("lock", LOCKS)
@pytest.mark.parametrize("enabled", [True, False])
async def test_set_lock(mocked_response, client_session, lock, enabled):
    """Each setter sends a JSON boolean only to the selected lock endpoint."""
    url = f"http://{ADDRESS}/{lock}-lock"
    mocked_response.post(url, payload={"status": "ok"})
    mill = Mill(ADDRESS, client_session)

    assert await getattr(mill, f"set_{lock}_lock")(enabled) is None
    mocked_response.assert_called_once_with(
        method="POST", url=url, data=json.dumps({"value": enabled})
    )


@pytest.mark.parametrize("lock", LOCKS)
@pytest.mark.parametrize("enabled", [0, 1, -1, 0.0, 1.0, "true", "false", "", None, [], {}])
async def test_invalid_state_never_calls_device(
    mocked_response, client_session, lock, enabled
):
    """Avoid treating truthy strings/integers as authorization to enable locks."""
    mill = Mill(ADDRESS, client_session)
    with pytest.raises(ValueError, match="must be a boolean"):
        await getattr(mill, f"set_{lock}_lock")(enabled)
    assert mocked_response.calls == []


@pytest.mark.parametrize("lock", LOCKS)
@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("status", [400, 404, 500])
async def test_http_errors_propagate(
    mocked_response, client_session, lock, method, status
):
    """Unsupported endpoints and failed requests must reach the caller."""
    url = f"http://{ADDRESS}/{lock}-lock"
    getattr(mocked_response, method)(url, status=status, payload={"status": "failed"})
    mill = Mill(ADDRESS, client_session)
    with pytest.raises(ClientResponseError) as error:
        if method == "get":
            await getattr(mill, f"fetch_{lock}_lock")()
        else:
            await getattr(mill, f"set_{lock}_lock")(True)
    assert error.value.status == status


@pytest.mark.parametrize("lock", LOCKS)
@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("error", [asyncio.TimeoutError, ClientConnectionError])
async def test_transport_errors_propagate(client_session, lock, method, error):
    """Connection errors and timeouts must not look like success."""
    mill = Mill(ADDRESS, client_session)
    with patch.object(client_session, method, side_effect=error), pytest.raises(error):
        if method == "get":
            await getattr(mill, f"fetch_{lock}_lock")()
        else:
            await getattr(mill, f"set_{lock}_lock")(False)


async def test_weekly_mode_shared_transport(mocked_response, client_session):
    """Cover the existing shared operation-mode path as a regression check."""
    url = f"http://{ADDRESS}/operation-mode"
    mocked_response.post(url, payload={"status": "ok"})
    mill = Mill(ADDRESS, client_session)
    await mill.set_operation_mode_weekly_program()
    mocked_response.assert_called_once_with(
        method="POST", url=url, data=json.dumps({"mode": "Weekly program"})
    )
