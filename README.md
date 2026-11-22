# Python module for local access to Gen 3 Mill heaters

Python module for local access to the Gen 3 Mill Heaters using
the [local REST API over WiFi](https://github.com/Mill-International-AS/Generation_3_REST_API).

This python module is used to integrate Gen 3 Mill heaters into Home Assistant,
see Mill Integration [documentation](https://www.home-assistant.io/integrations/mill/)
and [source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/mill).

## Implemented features

Not all REST API endpoints are available through this module.

These features are currently supported:

- read device information summary (`GET /status`)
- read detailed device state and control status (`GET /control-status`)
- set target temperature for Normal type (`POST /set-temperature`)
- set operation mode to `Control individually` and `Off` (`POST /operation-mode`)
- read temperature calibration offset (`GET /temperature-calibration-offset`)
- set temperature calibration offset (`POST /temperature-calibration-offset`)
- read and set child lock (`GET` / `POST /child-lock`)
- read and set commercial lock (`GET` / `POST /commercial-lock`)

### Child and commercial locks

`await mill.fetch_child_lock()` and `await mill.fetch_commercial_lock()` return
the respective device response, including its boolean `value` and `status`.
Use `await mill.set_child_lock(True)` or
`await mill.set_commercial_lock(True)` to enable a lock, and `False` to disable
it. Setters require a Python boolean; strings and integers are rejected before
any network request. Each call addresses only its named endpoint.

These are device-button locks, not API authentication or transport security.
The separate `/commercial-lock-customization` endpoint is not covered here.

## Install

```bash
pip install mill_local
```

## Contribution

### Install requirements

```bash
pip install -r requirements.txt
```

### Run tests

```bash
pip install -r requirements-test.txt
python -m pytest -v

# with logging to STDOUT
python -m pytest -v -p no:logging -s
```
