# eflib vendor

**Canonical (2026-09-29):** this Pacific folder (`Energy/lib/vendor/`) is the eflib vendor tree. It was diffed against the G2 copy at `~/.ollama/skills/energy/lib/vendor/`: all 102 files match except this README. The G2 copy is kept, not deleted.

`Energy/lib/ble_client.py` puts this folder first on `sys.path`. Pacific `jobs.py` sets `ENERGY_EFLIB_PATH` to `{PACIFIC}/Energy/lib/vendor` for the energy read jobs, and `Energy/lib/py` defaults to this folder. Do not point it at G2.
