# Energy / Smart-Devices

Local (LAN) control foundation for Wi-Fi smart devices that sit on the Energy side of the desk:
**WiZ bulbs** (UDP 38899 JSON) and **Unbranded Smart Plug BSD01** (Tuya / Smart Life, ESP8266).
Future feature — **collector gated OFF** (`RR_SMART_DEVICES=1`); drivers never run from the poller unless gated on.

Architecture + runbook: Library `Documentation/00-architecture/Smart-Devices-Energy.md`.

## Status (2026-09-29 13:30 HST)

| Item | State |
| --- | --- |
| `scripts/wiz.py` (stdlib driver: discover / status / on / off / dim / temp / restore) | **LANDED** — mock-bulb test PASS; real bulbs **BLOCKED** (0 replies on UDP 38899) |
| `scripts/tuya.py` (tinytuya scaffold: listen / config-check / status / on / off) | **LANDED** — control **BLOCKED** (no `local_key`) |
| `scripts/smart_devices_collect.py` → Database `Energy/Smart-Devices/*-last.json` | **PASS** (manual run 13:30 HST) |
| Poller job `smart_devices_collect` (jobs.py `EVERY_SECONDS`) | **LANDED, gated OFF** — `RR_SMART_DEVICES=1` at poller start |

## Layout

```text
Energy/Smart-Devices/
  README.md
  scripts/wiz.py                    WiZ UDP driver (stdlib)
  scripts/tuya.py                   Tuya local scaffold (venv: tinytuya)
  scripts/smart_devices_collect.py  read-only collector -> Database *-last.json
  config/wiz-devices.json           known bulbs (IP/MAC; tracked, not secret)
  config/tuya-devices.example.json  template (tracked, placeholders only)
  config/tuya-devices.local.json    REAL plug ids + local_keys (GITIGNORED — create by hand)
  config/tuya-cloud.env             Tuya IoT cloud creds if used (GITIGNORED)
  .venv/                            tinytuya venv (GITIGNORED)
```

## Commands (run at nice 10)

```bash
cd "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/Smart-Devices"
nice -n 10 python3 scripts/wiz.py discover --timeout 3 --sweep 192.168.1   # ufw drops broadcast replies -> use --sweep
nice -n 10 python3 scripts/wiz.py status 192.168.1.X
nice -n 10 .venv/bin/python scripts/tuya.py listen --seconds 20            # no key; id/ip/version only
nice -n 10 .venv/bin/python scripts/tuya.py config-check                   # never prints keys
nice -n 10 python3 scripts/smart_devices_collect.py [--discover] [--dry-run]
```

Recreate venv: `python3 -m venv .venv && .venv/bin/pip install tinytuya` (tinytuya 1.20.0 on 2026-09-29).

## Rules

- Wi-Fi only. **Never touch BLE** — `Energy/scripts/ble/ble-owner.py` owns the adapter.
- Collector is read-only; switching is manual CLI only until an automation is explicitly approved.
- `local_key` / Tuya cloud creds live only in the gitignored files above; never print or log them.
- Never join the plug's `SmartLife-XXXX` AP from the desk (takes the desk off the LAN: poller, Starlink, tunnel).

*Smart-Devices foundation 2026-09-29 HST.*
