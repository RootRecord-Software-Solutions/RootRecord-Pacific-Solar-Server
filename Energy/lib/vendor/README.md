# eflib vendor

**Canonical (2026-09-30):** this Pacific folder (`Energy/lib/vendor/`, 102 files: 101 Python modules and this README) is the eflib vendor tree. `~/.ollama/skills/energy` does not exist.

`Energy/lib/ble_client.py` puts this folder first on `sys.path`. Pacific `jobs.py` sets `ENERGY_EFLIB_PATH` to `{PACIFIC}/Energy/lib/vendor` for the energy read jobs, and `Energy/lib/py` defaults to this folder.
