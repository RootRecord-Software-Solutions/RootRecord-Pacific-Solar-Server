# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Status (2026-09-29 22:26 HST) — reads LIVE

API reads are live. At 22:26 HST the poller logged Delta 2 at 7% (57 W AC out, 9 W USB-C) and River 2 Pro at 100%. The laptop was 43% and discharging at 22:21. The BLE owner is Pacific `Energy/scripts/ble/ble-owner.py`. There is no lowercase `energy` symlink, and no Pacific Energy file still says `import energy`.

Do not arm, disarm, or switch AC from this page. Those actions stay on WO-ECO-001 Phase 2.

## Desired upgrades

Hardware Alexander intends to add later. These notes do not authorize a purchase or a control change.

| Upgrade | State | Note |
| --- | --- | --- |
| Four corner actuators for sun tilt | DESIRED | One actuator on each corner of a wood or aluminum frame. Until then a person sets left-up, flat, or right-up, and the energy desk asks when channel 1 shows the wrong tilt. [Library note](../../../5%20-%20RootRecord-Library/Documentation/09-desired-upgrades/2026-09-30-four-corner-sun-tilt-actuators.md). |

## Earlier status (2026-09-28) — Phase 1 layout

| Item | State |
| --- | --- |
| Domain folder | **`Energy/` only** (no lowercase `energy` sibling) |
| Python package | **`Energy`** — matches folder; rewrite G2 `import energy` → `import Energy` |
| Launcher | `Energy/lib/py` — PYTHONPATH = vendor + Pacific root |
| jobs.py | Pacific paths (quoted) |
| Data | `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/` (sqlite store: `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/RootRecord/`) |
| Sun times | `scripts/sun_times.py` (G1 `hourly-solar-weather/sun_times.py` port, stdlib, Open-Meteo once per HST day) → Database `Energy/sun/sun-times-last.json`. Job `energy_sun_times` (EVERY_HOUR) **gated OFF** (`RR_SUN_TIMES=1`). LANDED · PASS one run 2026-09-29 13:26 HST |
| Load categories | `scripts/load_categories.py [--input F]` (G1 `load-categories` logic verbatim + adapter from G3 BLE `Energy/watts` / `soc` last-files; sun state from `Energy/sun`). Prints Starlink / lights, house AC, transfer, E-Batt callout lines. On demand, writes nothing. Smoke PASS 2026-09-29 14:33 HST. Check-later: no USB-A / 12 V / car fields in G3 (`car_w`=0), thresholds; G1 `append_history` (deleted old logs) not ported |
| Smart devices | `Smart-Devices/` — WiZ bulbs + Tuya BSD01 plugs (Wi-Fi, not BLE). Collector `smart_devices_collect` (EVERY_SECONDS 300 s) **gated OFF** (`RR_SMART_DEVICES=1`) → Database `Energy/Smart-Devices/*-last.json`. Plug control BLOCKED (no `local_key`). See `Smart-Devices/README.md`. LANDED 2026-09-29 13:30 HST |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/
```

### Package rule (standing)

Do **not** create `energy` → `Energy` symlinks. Folder name is the package name.

After any G2 copy that still says `import energy`:

```bash
find Energy -name '*.py' -print0 | xargs -0 sed -i \
  's/\bfrom energy\./from Energy./g; s/\bimport energy\./import Energy./g; s/\bimport energy\b/import Energy/g'
rm -f ../energy   # if a leftover symlink exists at Pacific root
```

### Policy

No old desk for Energy reads. See Library: `Pacific-Domain-Import-Playbook` standing rules.

---

*Naming SOP 2026-09-28 HST.*
