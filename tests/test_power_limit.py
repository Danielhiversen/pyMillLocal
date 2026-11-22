"""Panel/storage percentage limits and shared transport failure paths."""
import asyncio
import json
from unittest.mock import patch

import pytest
from aiohttp import ClientConnectionError, ClientResponseError

from mill_local import Mill

URL = 'http://192.168.2.123/limited-heating-power'


@pytest.mark.parametrize('percentage', [10, 30, 60, 65, 80, 100])
async def test_percentage_roundtrip(mocked_response, client_session, percentage):
    mill = Mill('192.168.2.123', client_session)
    response = {'status': 'ok', 'limited_heating_power': percentage}
    mocked_response.post(URL, payload={'status': 'ok'})
    mocked_response.get(URL, payload=response)
    await mill.set_limited_heating_power(percentage)
    assert await mill.fetch_limited_heating_power() == response
    assert mocked_response.calls == [
        {'method': 'POST', 'url': URL,
         'data': json.dumps({'limited_heating_power': percentage})},
        {'method': 'GET', 'url': URL},
    ]


@pytest.mark.parametrize('percentage', [True, False, None, '65', 65.0, 65.5, 9, 101, -1])
async def test_invalid_limit_never_calls_device(mocked_response, client_session, percentage):
    mill = Mill('192.168.2.123', client_session)
    with pytest.raises(ValueError):
        await mill.set_limited_heating_power(percentage)
    assert mocked_response.calls == []


@pytest.mark.parametrize('method', ['get', 'post'])
@pytest.mark.parametrize('status', [400, 404, 500])
async def test_device_http_errors_propagate(mocked_response, client_session, method, status):
    mill = Mill('192.168.2.123', client_session)
    getattr(mocked_response, method)(URL, status=status, payload={'status': 'failed'})
    with pytest.raises(ClientResponseError) as error:
        if method == 'get':
            await mill.fetch_limited_heating_power()
        else:
            await mill.set_limited_heating_power(65)
    assert error.value.status == status


@pytest.mark.parametrize('method', ['get', 'post'])
@pytest.mark.parametrize('error', [asyncio.TimeoutError, ClientConnectionError])
async def test_transport_errors_propagate(client_session, method, error):
    mill = Mill('192.168.2.123', client_session)
    with patch.object(client_session, method, side_effect=error), pytest.raises(error):
        if method == 'get':
            await mill.fetch_limited_heating_power()
        else:
            await mill.set_limited_heating_power(65)


async def test_weekly_mode_shared_transport(mocked_response, client_session):
    mill = Mill('192.168.2.123', client_session)
    mocked_response.post('http://192.168.2.123/operation-mode', payload={'status': 'ok'})
    await mill.set_operation_mode_weekly_program()
    mocked_response.assert_called_once_with(
        method='POST', url='http://192.168.2.123/operation-mode',
        data=json.dumps({'mode': 'Weekly program'}))
