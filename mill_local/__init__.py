"""Local support for Mill wifi-enabled home heaters."""
import asyncio
import json
import logging
from enum import Enum

import aiohttp.client_exceptions
import async_timeout

_LOGGER = logging.getLogger(__name__)


class OperationMode(Enum):
    """Heater Operation Mode"""

    # Follow the single set value, but not use any timers or weekly program
    CONTROL_INDIVIDUALLY = "Control individually"

    # The device is in off mode
    OFF = "OFF"

    # Follow the weekly program
    WEEKLY_PROGRAM = "Weekly program"

    # Follow the single set value, with timers enabled
    INDEPENDENT_DEVICE = "Independent device"


class Mill:
    """Mill data handler."""

    def __init__(self, device_ip, websession, timeout=15):
        """Init Mill data handler."""
        self.device_ip = device_ip.replace("http://", "").replace("/", "").strip()
        self.websession = websession
        self.url = "http://" + self.device_ip
        self._timeout = timeout
        self._status = {}

    @property
    def version(self):
        """Return the API version."""
        return self._status.get("version", "")

    @property
    def name(self):
        """Return heater name."""
        return self._status.get("name", "")

    @property
    def mac_address(self):
        """Return heater MAC address."""
        return self._status.get("mac_address")

    async def set_target_temperature(self, target_temperature):
        """Set target temperature."""
        _LOGGER.debug("Setting target temperature to: '%s'", target_temperature)
        return await self._post_request(
            command="set-temperature",
            payload={
                "type": "Normal",
                "value": target_temperature,
            }
        )

    async def set_operation_mode_control_individually(self):
        """Set operation mode to 'control individually'."""
        return await self._set_operation_mode(OperationMode.CONTROL_INDIVIDUALLY)

    async def set_operation_mode_off(self):
        """Set operation mode to 'off'."""
        return await self._set_operation_mode(OperationMode.OFF)

    async def connect(self):
        """Get heater status."""
        return await self.get_status()

    async def get_status(self):
        """Get summary of the heater device information."""
        try:
            self._status = await self._get_request("status")
        except (aiohttp.client_exceptions.ClientError, asyncio.TimeoutError):
            _LOGGER.error("Failed to get status", exc_info=True)
            return None
        return self._status

    async def fetch_heater_and_sensor_data(self):
        """Get current heater state and control status."""
        return await self._get_request("control-status")

    async def _set_operation_mode(self, mode: OperationMode):
        """Set heater operation mode."""
        _LOGGER.debug("Setting operation mode to: '%s'", mode.value)
        return await self._post_request(command="operation-mode", payload={"mode": mode.value})

    async def _post_request(self, command: str, payload: dict):
        """HTTP POST request to Mill Local Api."""
        with async_timeout.timeout(self._timeout):
            async with self.websession.post(
                    url=f"{self.url}/{command}",
                    data=json.dumps(payload),
            ) as response:
                _LOGGER.debug("POST '%s' response status: %s", command, response.status)
                res = await response.json()
                if response.status != 200 or res["status"] != "ok":
                    _LOGGER.error(
                        "POST '%s' failed with result.status: %s, response.status: %s, response.reason: %s",
                        command,
                        res,
                        response.status,
                        response.reason,
                    )
                return response.status

    async def _get_request(self, command: str):
        """HTTP GET request to Mill Local Api."""
        with async_timeout.timeout(self._timeout):
            async with self.websession.get(
                    url=f"{self.url}/{command}",
                    raise_for_status=True
            ) as response:
                _LOGGER.debug("GET '%s' response status: %s", command, response.status)
                res = await response.json()
                if response.status != 200 or res["status"] != "ok":
                    _LOGGER.error(
                        "GET '%s' failed with result.status: %s, response.status: %s, response.reason: %s",
                        command,
                        res,
                        response.status,
                        response.reason,
                    )
                    return None
                return res
