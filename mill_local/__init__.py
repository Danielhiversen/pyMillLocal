"""Local support for Mill wifi-enabled home heaters."""
import asyncio
import json
import logging

import aiohttp.client_exceptions
import async_timeout

_LOGGER = logging.getLogger(__name__)


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

    async def connect(self):
        """Get heater status."""
        return await self.get_status()

    async def get_status(self):
        """Get heater status."""
        for k in range(3, -1, -1):
            try:
                self._status = await self._request("status")
            except (aiohttp.client_exceptions.ClientError, asyncio.TimeoutError):
                if k > 0:
                    await asyncio.sleep(1)
                    _LOGGER.warning("Failed to get status, retrying")
                else:
                    _LOGGER.error("Failed to get status", exc_info=True)
                    return None
            else:
                break
        return self._status

    async def fetch_heater_and_sensor_data(self):
        """Get heater status."""
        return await self._request("control-status")

    async def _request(self, command):
        with async_timeout.timeout(self._timeout):
            async with self.websession.get(
                f"{self.url}/{command}",
                    raise_for_status=True
            ) as response:
                res = await response.json()
                if res["status"] != "ok":
                    _LOGGER.error("Request %s failed: %s", command, res)
                    return None
                return res
