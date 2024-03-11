"""Test Mill."""
import json

import pytest
from aiohttp import ClientResponseError

from mill_local import Mill, MillOilHeater, OperationMode, OilHeaterPowerLevels

device_ip = "192.168.2.123"
local_api_url = f"http://{device_ip}"


async def test_init_when_websession_is_present(client_session):
    """Test Mill init and default values."""
    mill = Mill(device_ip, client_session)

    # test default values
    assert mill.device_ip == device_ip
    assert mill.websession is not None
    assert mill.url == local_api_url
    assert mill._timeout_seconds == 15
    assert mill.name == ""
    assert mill.version == ""
    assert mill.mac_address is None


async def test_connect_when_successful(mocked_response, client_session, status_command_response):
    """Test successful connection to Mill device."""
    mill = Mill(device_ip, client_session)
    mocked_response.get(f"{local_api_url}/status", status=200, payload=status_command_response)
    returned_data = await mill.connect()

    # assert returned data, we don't bother asserting every response property
    assert returned_data is not None
    assert len(returned_data.keys()) == 6

    # assert data in Mill object
    assert mill.name == "Mill panel"
    assert mill.version == "0x221017"
    assert mill.mac_address == "13:37:A6:5E:D3:CB"


async def test_connect_when_error_raised(mocked_response, client_session):
    """Test error raised when connecting to Mill device and None returned."""
    mill = Mill(device_ip, client_session)
    mocked_response.get(f"{local_api_url}/status", status=400)

    with pytest.raises(ClientResponseError) as exp_400_info:
        returned_data = await mill.connect()
        assert exp_400_info.value.status == 400
        assert returned_data is None
        assert mill.name == ""
        assert mill.version == ""
        assert mill.mac_address is None


async def test_fetch_heater_sensor_when_successful(mocked_response, client_session, control_status_response):
    """Test successful reading heater and sensor data."""
    mill = Mill(device_ip, client_session)
    mocked_response.get(f"{local_api_url}/control-status", status=200, payload=control_status_response)

    returned_data = await mill.fetch_heater_and_sensor_data()
    assert returned_data is not None
    # we don't bother asserting every response property
    assert len(returned_data.keys()) == 11


async def test_fetch_heater_sensor_when_error_raised(mocked_response, client_session, control_status_response):
    """Test error raised when reading heater and sensor data and None returned."""
    mill = Mill(device_ip, client_session)
    mocked_response.get(f"{local_api_url}/control-status", status=400)

    with pytest.raises(ClientResponseError) as exp_400_info:
        returned_data = await mill.fetch_heater_and_sensor_data()
        assert exp_400_info.value.status == 400
        assert returned_data is None


async def test_set_target_temperature_when_successful(mocked_response, client_session,
                                                      generic_status_ok_response):
    """Test successful setting the device target temperature."""
    mill = Mill(device_ip, client_session)
    mocked_response.post(f"{local_api_url}/set-temperature", status=200, payload=generic_status_ok_response)

    returned_data = await mill.set_target_temperature(20.5)
    assert returned_data is None
    mocked_response.assert_called_once_with(url=f"{local_api_url}/set-temperature",
                                            method="POST",
                                            data=json.dumps({
                                                "type": "Normal",
                                                "value": 20.5
                                            }))


async def test_set_target_temperature_when_error_raised(mocked_response, client_session,
                                                        generic_status_ok_response):
    """Test error raised when setting the device target temperature."""
    mill = Mill(device_ip, client_session)
    mocked_response.post(f"{local_api_url}/set-temperature", status=400)

    with pytest.raises(ClientResponseError) as exp_400_info:
        returned_data = await mill.set_target_temperature(20.5)
        assert exp_400_info.value.status == 400
        assert returned_data is None
        mocked_response.assert_called_once_with(url=f"{local_api_url}/set-temperature",
                                                method="POST",
                                                data=json.dumps({
                                                    "type": "Normal",
                                                    "value": 20.5
                                                }))

async def test_set_heater_power_when_successful(mocked_response, client_session,
                                                      generic_status_ok_response):
    """Test successful setting the device oil heater power."""
    mill = MillOilHeater(device_ip, client_session)
    mocked_response.post(f"{local_api_url}/oil-heater-power", status=200, payload=generic_status_ok_response)

    returned_data = await mill.set_heater_power(OilHeaterPowerLevels.HIGH)
    assert returned_data is None
    mocked_response.assert_called_once_with(url=f"{local_api_url}/oil-heater-power",
                                            method="POST",
                                            data=json.dumps({
                                                "heating_level_percentage": OilHeaterPowerLevels.HIGH.value,
                                            }))


async def test_set_heater_power_when_error_raised(mocked_response, client_session,
                                                        generic_status_ok_response):
    """Test error raised when setting the device oil heater power."""
    mill = MillOilHeater(device_ip, client_session)
    mocked_response.post(f"{local_api_url}/oil-heater-power", status=400)

    with pytest.raises(ClientResponseError) as exp_400_info:
        returned_data = await mill.set_heater_power(OilHeaterPowerLevels.HIGH)
        assert exp_400_info.value.status == 400
        assert returned_data is None
        mocked_response.assert_called_once_with(url=f"{local_api_url}/oil-heater-power",
                                                method="POST",
                                                data=json.dumps({
                                                    "heating_level_percentage": OilHeaterPowerLevels.HIGH.value,
                                                }))


async def test_fetch_heater_power_when_successful(mocked_response, client_session, oil_heater_power_response):
    """Test successful reading heater and sensor data."""
    mill = MillOilHeater(device_ip, client_session)
    mocked_response.get(f"{local_api_url}/oil-heater-power", status=200, payload=oil_heater_power_response)

    returned_data = await mill.fetch_heater_power_data()
    assert returned_data is not None
    assert len(returned_data.keys()) == 2
    assert type(returned_data.get("value")) is int


async def test_fetch_heater_power_when_error_raised(mocked_response, client_session, oil_heater_power_response):
    """Test error raised when reading heater and sensor data and None returned."""
    mill = MillOilHeater(device_ip, client_session)
    mocked_response.get(f"{local_api_url}/oil-heater-power", status=400)

    with pytest.raises(ClientResponseError) as exp_400_info:
        returned_data = await mill.fetch_heater_power_data()
        assert exp_400_info.value.status == 400
        assert returned_data is None


async def test_set_operation_mode_control_individually_when_successful(mocked_response, client_session,
                                                                       generic_status_ok_response):
    """Test successful setting the device operation mode to 'control individually'."""
    mill = Mill(device_ip, client_session)
    mocked_response.post(f"{local_api_url}/operation-mode", status=200, payload=generic_status_ok_response)

    returned_data = await mill.set_operation_mode_control_individually()
    assert returned_data is None
    mocked_response.assert_called_once_with(url=f"{local_api_url}/operation-mode",
                                            method="POST",
                                            data=json.dumps({
                                                "mode": OperationMode.CONTROL_INDIVIDUALLY.value
                                            }))


async def test_set_operation_mode_control_individually_when_error_raised(mocked_response, client_session,
                                                                       generic_status_ok_response):
    """Test error raised when setting the device operation mode to 'control individually'."""
    mill = Mill(device_ip, client_session)
    mocked_response.post(f"{local_api_url}/operation-mode", status=400)

    with pytest.raises(ClientResponseError) as exp_400_info:
        returned_data = await mill.set_operation_mode_control_individually()
        assert exp_400_info.value.status == 400
        assert returned_data is None
        mocked_response.assert_called_once_with(url=f"{local_api_url}/operation-mode",
                                                method="POST",
                                                data=json.dumps({
                                                    "mode": OperationMode.CONTROL_INDIVIDUALLY.value
                                                }))


async def test_set_operation_mode_off_when_successful(mocked_response, client_session, generic_status_ok_response):
    """Test successful setting the device operation mode to 'off'."""
    mill = Mill(device_ip, client_session)
    mocked_response.post(f"{local_api_url}/operation-mode", status=200, payload=generic_status_ok_response)

    returned_data = await mill.set_operation_mode_off()
    assert returned_data is None
    mocked_response.assert_called_once_with(url=f"{local_api_url}/operation-mode",
                                            method="POST",
                                            data=json.dumps({
                                                "mode": OperationMode.OFF.value
                                            }))


async def test_set_operation_mode_off_when_error_raised(mocked_response, client_session, generic_status_ok_response):
    """Test error raised when setting the device operation mode to 'off'."""
    mill = Mill(device_ip, client_session)
    mocked_response.post(f"{local_api_url}/operation-mode", status=400)

    with pytest.raises(ClientResponseError) as exp_400_info:
        returned_data = await mill.set_operation_mode_off()
        assert exp_400_info.value.status == 400
        assert returned_data is None
        mocked_response.assert_called_once_with(url=f"{local_api_url}/operation-mode",
                                                method="POST",
                                                data=json.dumps({
                                                    "mode": OperationMode.OFF.value
                                                }))


async def test_post_request_rais_error_on_400_and_500(mocked_response, client_session):
    """Test that get_request rais exception when status 400 or higher."""
    mill = Mill(device_ip, client_session)
    # with response body
    mocked_response.post(f"{local_api_url}/operation-mode", status=400, body=json.dumps({
        "status": "Failed to parse message body"
    }))
    # without response body
    mocked_response.post(f"{local_api_url}/operation-mode", status=500)

    with pytest.raises(ClientResponseError) as exp_400_info:
        await mill._post_request(command="operation-mode", payload={"mode": OperationMode.OFF.value})

    assert exp_400_info.value.status == 400

    with pytest.raises(ClientResponseError) as exp_500_info:
        await mill._post_request(command="operation-mode", payload={"mode": OperationMode.OFF.value})

    assert exp_500_info.value.status == 500


async def test_get_request_rais_error_on_400_and_500(mocked_response, client_session):
    """Test that get_request rais exception when status 400 or higher."""
    mill = Mill(device_ip, client_session)
    # with response body
    mocked_response.get(f"{local_api_url}/status", status=400, body=json.dumps({
        "status": "Failed to parse message body"
    }))
    # without response body
    mocked_response.get(f"{local_api_url}/status", status=500)

    with pytest.raises(ClientResponseError) as exp_400_info:
        await mill._get_request("status")

    assert exp_400_info.value.status == 400

    with pytest.raises(ClientResponseError) as exp_500_info:
        await mill._get_request("status")

    assert exp_500_info.value.status == 500
