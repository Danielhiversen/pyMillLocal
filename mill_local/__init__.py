"""Local support for Mill wifi-enabled home heaters."""
import json
import logging
from enum import Enum
from typing import Union

import aiohttp.client_exceptions
from aiohttp import ClientSession
from async_timeout import timeout

_LOGGER = logging.getLogger(__name__)


class OperationMode(Enum):
    """Heater Operation Mode."""

    # Follow the single set value, but not use any timers or weekly program
    CONTROL_INDIVIDUALLY = "Control individually"

    # The device is in off mode
    OFF = "OFF"

    # Follow the weekly program, referred to from the HA integration only in read-only mode
    WEEKLY_PROGRAM = "Weekly program"

    # Follow the single set value, with timers enabled
    INDEPENDENT_DEVICE = "Independent device"


class Mill:
    """Mill data handler."""

    def __init__(self, device_ip: str, websession: ClientSession, timeout_seconds: int = 15) -> None:
        """Init Mill data handler."""
        self.device_ip = device_ip.replace("http://", "").replace("/", "").strip()
        self.websession = websession
        self.url = "http://" + self.device_ip
        self._timeout_seconds = timeout_seconds
        self._status = {}

    @property
    def version(self) -> str:
        """Return the API version."""
        return self._status.get("version", "")

    @property
    def name(self) -> str:
        """Return heater name."""
        return self._status.get("name", "")

    @property
    def mac_address(self) -> Union[str, None]:
        """Return heater MAC address."""
        return self._status.get("mac_address")

    async def set_target_temperature(self, target_temperature: float) -> None:
        """Set target temperature."""
        _LOGGER.debug("Setting target temperature to: '%s'", target_temperature)
        await self._post_request(
            command="set-temperature",
            payload={
                "type": "Normal",
                "value": target_temperature,
            }
        )

    async def set_operation_mode_control_individually(self) -> None:
        """Set operation mode to 'control individually'."""
        await self._set_operation_mode(OperationMode.CONTROL_INDIVIDUALLY)

    async def set_operation_mode_off(self) -> None:
        """Set operation mode to 'off'."""
        await self._set_operation_mode(OperationMode.OFF)

    async def connect(self) -> dict:
        """Connect to the device and return its status."""
        return await self.get_status()

    async def get_status(self) -> dict:
        """Get status summary of the device."""
        self._status = await self._get_request("status")
        return self._status

    async def fetch_heater_and_sensor_data(self) -> dict:
        """Get current heater state and control status."""
        return await self._get_request("control-status")

    async def _set_operation_mode(self, mode: OperationMode) -> None:
        """Set heater operation mode."""
        _LOGGER.debug("Setting operation mode to: '%s'", mode.value)
        await self._post_request(command="operation-mode", payload={"mode": mode.value})

    async def _post_request(self, command: str, payload: dict) -> None:
        """HTTP POST request to Mill Local Api."""
        async with timeout(self._timeout_seconds):
            async with self.websession.post(
                    url=f"{self.url}/{command}",
                    data=json.dumps(payload)
            ) as response:
                # Since body is not available when using raise_for_status=True, we use raise_for_status()
                json_response = await response.json()

                # Guard in case response body is missing and Error is raised
                if json_response is None:
                    json_response = {"status": ""}

                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError:
                    _LOGGER.error(
                        "POST request to '%s' failed with status code: '%s (%s)' and status message: '%s'",
                        command,
                        response.status,
                        response.reason,
                        json_response.get("status", "")  # Guard in case status property is missing in body
                    )
                    raise

    async def _get_request(self, command: str) -> Union[dict, None]:
        """HTTP GET request to Mill Local Api."""
        async with timeout(self._timeout_seconds):
            async with self.websession.get(
                    url=f"{self.url}/{command}"
            ) as response:
                # Since body is not available when using raise_for_status=True, we use raise_for_status()
                json_response = await response.json()

                # Guard in case response body is missing and Error is raised
                if json_response is None:
                    json_response = {"status": ""}

                try:
                    response.raise_for_status()
                    return json_response
                except aiohttp.ClientResponseError:
                    _LOGGER.error(
                        "GET request to '%s' failed with status code: '%s (%s)' and status message: '%s'",
                        command,
                        response.status,
                        response.reason,
                        json_response.get("status", "")  # Guard in case status property is missing in body
                    )
                    raise
