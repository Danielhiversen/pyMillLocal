"""Local support for Mill wifi-enabled home heaters."""
import asyncio
import json
import logging

import async_timeout

_LOGGER = logging.getLogger(__name__)


class Mill:
    """Mill data handler."""

    def __init__(self, device_ip, websession, timeout=15):
        """Init Mill data handler."""
        self.device_ip = device_ip
        self.websession = websession
        self.url = "http://" + device_ip
        self._timeout = timeout
        self._status = {}

    @property
    def version(self):
        """Return version."""
        return self._status.get("version", "")

    @property
    def name(self):
        """Return name."""
        return self._status.get("name", "")

    async def set_target_temperature(self, target_temperature):
        """Set target temperature."""
        payload = {
            "type": "Normal",
            "value": target_temperature,
        }
        with async_timeout.timeout(self._timeout):
            async with self.websession.post(
                f"{self.url}/set-temperature",
                data=json.dumps(payload),
            ) as response:
                _LOGGER.debug("Heater response %s", response.status)
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to set target temperature %s %s",
                        response.status,
                        response.reason,
                    )
                return response.status

    async def set_normal_operation_mode(self):
        """Set target temperature."""
        payload = {"mode": "Control individually"}
        with async_timeout.timeout(self._timeout):
            async with self.websession.post(
                f"{self.url}/operation-mode",
                payload=payload,
            ) as response:
                _LOGGER.debug("Heater response %s", response.status)
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to set target temperature %s %s",
                        response.status,
                        response.reason,
                    )
                return response.status

    async def get_status(self):
        """Get heater control status."""
        self._status = await self._request("status")
        return self._status

    async def get_control_status(self):
        """Get heater status."""
        return await self._request("control-status")

    async def _request(self, command):
        try:
            with async_timeout.timeout(self._timeout):
                async with self.websession.get(
                    f"{self.url}/{command}",
                ) as response:
                    if response.status != 200:
                        _LOGGER.error(
                            "Failed to get %s %s %s",
                            command,
                            response.status,
                            response.reason,
                        )
                        return None
                    res = await response.json()
                    if res["status"] != "ok":
                        _LOGGER.error("Request %s failed: %s", command, res)
                        return None
                    return res
        except asyncio.TimeoutError:
            return None
