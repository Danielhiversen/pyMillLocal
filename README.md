# Python Mill Local module

Python module for local access to the Gen 3 Mill Heaters using
the [local REST API over WiFi](https://github.com/Mill-International-AS/Generation_3_REST_API).

## Run tests

```bash
pip install -r requirements-test.txt
python -m pytest -v

# with logging to STDOUT
python -m pytest -v -p no:logging -s
```
