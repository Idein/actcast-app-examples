# Repository Guidelines

## Project Structure & Module Organization
- `app/`: Runtime code.
  - `main.py`: Actcast entrypoint (heartbeat + sensor publish).
  - `main`: Bash launcher used by Actcast runtime.
  - `healthchecker`: Liveness probe script for Actcast.
  - `sensor/`: I2C sensor drivers (e.g., `BME280.py`, `LTR390.py`, `TSL2591.py`, `SGP40.py`, `ICM20948.py`).
- `.actdk/`: Actcast SDK config (`dependencies.json`, `files.json`, `setting.json`).
- `manifesto/`: Device permission manifests per target (I2C, GPIO, etc.).
- `README.md`: Hardware setup and I2C enablement notes.
- `tests/`: Optional `pytest` tests for logic.

## Build, Test, and Development Commands
- Build (Actcast): `actdk build` — package app using `.actdk` configs.
- Local run (Raspberry Pi): `python3 app/main.py` — publishes sensor data via `actfw`.
- Direct sensor debug: `python3 app/sensor_i2c.py` — prints values without Actcast.
- Pi dependencies: `sudo apt install python3-smbus i2c-tools && pip3 install actfw-core actfw-raspberrypi bme680`.
- Run tests (if present): `pytest -q`.

## Coding Style & Naming Conventions
- Python 3; 4-space indentation; PEP 8 where practical.
- Names: `snake_case` for functions/variables; `CapWords` for classes.
- Modules: keep device drivers in `app/sensor/`; name after hardware (e.g., `TSL2591.py`).
- Constants: keep I2C addresses and other constants near the top of modules; avoid magic numbers elsewhere.

## Testing Guidelines
- Add minimal `pytest` tests under `tests/` for logic (e.g., `tests/test_sensor_utils.py`).
- Prefer pure functions for calculations (e.g., compensation formulas) to ease testing.
- Quick sanity: run `python3 app/sensor_i2c.py`; verify fields, error handling, and `invalid_sensors` reporting.

## Commit & Pull Request Guidelines
- Commits: concise, imperative (e.g., "Add BME688 calibration handling"); reference issues (`#123`).
- PRs: include description, hardware used, logs or sample payloads, and screenshots if Actcast Writer settings are relevant.
- Call out changes to `.actdk/*.json` or `manifesto/*.json` and why.

## Security & Configuration Tips
- Enable I2C in Actcast Writer (see `README.md`). BME688 must be at address `0x77` (cut ADDR pad per notes).
- `ACTCAST_SOCKS_SERVER` is supported by `app/main` for proxy use.
- Update `manifesto/*` when adding devices requiring new permissions (e.g., additional I2C buses).

