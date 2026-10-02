# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Current (2026-10-02)

Pack readings come from EcoFlow BLE into Database `Energy/soc` and `Energy/watts`. The repeating read is user timer `rr-ecoflow-read.timer` (`leapfrog-read.sh`). Poller job `ecoflow_read_cycle` is off. A Bluetooth miss keeps the last BLE file for 3 minutes and does not publish quota. If both watt files are at least 3 minutes old, that script power-cycles `hci0` once, then reads. Leapfrog prefers the older watt file; if that read fails it tries the other pack once, then rewrites the agent desk via `desk-live.py`. Quota is labeled `source: cloud` and runs only after that quiet window. If the pack is in range but the inverter heartbeat never arrives, only the missing AC watts are filled from quota when the outlet is on (`source: ble+cloud`). An outlet Bluetooth measured as off is 0 watts, not a cloud number. The standing rule is Library `Documentation/01-Operations/2026-10-01-ecoflow-ble-reads.md`. Pack watts and the channel-1 look are spoken on Bruce’s combined `solar_desk` at :22 and :52 (title “Energy and solar”); the separate Carly `energy_report` job is retired. A reading older than 30 minutes is "out of range." A last reading of 5 percent or less that is older than 30 minutes is discharged and powered off, not a pack that is still reporting. Delta 2 AC in above 550 W is generator. River 2 Pro AC in above 300 W is generator, unless that input matches the Delta's AC output, which is a transfer. The same rules are in `Energy/lib/read_runner.py` and `Energy/scripts/load_categories.py`.

River 2 Pro AC auto-recover is verified live via `rr-river2pro-ac-recover.timer`, kept enabled persistently 24/7 with `OnBootSec=45`, `OnUnitActiveSec=45`, and `Persistent=true`; `COOLDOWN_SEC=0` retries each tick while AC is off and `rootrecord` linger is enabled (`linger=yes`). Fresh SOC≥5% (≤5 min) **or** `ac_input_power`≥50W, whichever arrives first, triggers recovery; AC already on is a no-op. Alexander verified recovery after power-off at ~04:30 HST.


Channel 1 is looked at once per hour from the combined solar desk. Left side up is morning, flat is day, right side up is evening. The desk asks for a person when the tilt is wrong. It does not move the panels. Full record: [voice desk](../../../5%20-%20RootRecord-Library/Documentation/01-Operations/2026-09-30-voice-desk.md). The actuator plan is in [Desired upgrades](#desired-upgrades).

Host and weather speech units are not in this folder. Host temperature is Celsius. Weather degrees stay Fahrenheit.

The 2026-09-29 22:26 snapshot below is that moment only.

## Status snapshot (2026-09-29 22:26 HST) — reads were live then

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
