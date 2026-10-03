# Energy

Energy monitoring, EcoFlow device reads, and power subsystem ownership for the Pacific desk.

---

## Current (2026-10-02)

2026-10-02 ~17:08–17:09 HST: BLE was still failing (Delta `error_not_found`, River `NeedBindInstallFirst`) and `read_runner` was printing `cloud not used`, so watt files stayed STALE. Restored API fallback after the 3-minute BLE hold; longer grace on NeedBindInstallFirst; one BLE connect retry after a fresh scan. Live cloud write: Delta ~81% SOC, River ~24% SOC / 32 W solar / 52 W AC out. Timer left running. No commit.

2026-10-02 ~16:07–16:10 HST: `Energy/lib/read_runner.py` waits 2.5 s after an auth-flag miss and keeps the BLE sample when `soc` is present. `Energy/scripts/read/leapfrog-read.sh` reads Delta first then tries River when River’s last watt `source` is not `ble` or `ble+cloud`; when River already has live BLE it still leapfrogs the older watt file. Soft gate and live timers left as they were. No commit.

2026-10-02 ~15:16 HST: `Energy/scripts/ble/ble-owner.py` may run `leapfrog-read.sh` once when a watt sample under Database `Energy/watts/` is older than 30 minutes and `/tmp/ecoflow-owner-wake` is past cooldown. It still does not hold a GATT session. Standing rule remains Library `2026-10-01-ecoflow-ble-reads.md`.

Pack readings come from EcoFlow BLE into Database `Energy/soc` and `Energy/watts`. The repeating read is user timer `rr-ecoflow-read.timer` (`leapfrog-read.sh`). Poller job `ecoflow_read_cycle` is off. A Bluetooth miss keeps the last BLE file for 3 minutes and does not publish quota. If both watt files are at least 3 minutes old, that script runs `bluetoothctl power on` once per cooldown, then reads. It does not power `hci0` off. When River’s last watt `source` is not `ble` or `ble+cloud`, leapfrog reads Delta first then tries River; otherwise it prefers the older watt file, falls back once on failure, then rewrites the agent desk via `desk-live.py`. Quota is labeled `source: cloud` and runs only after that quiet window. If the pack is in range but the inverter heartbeat never arrives, only the missing AC watts are filled from quota when the outlet is on (`source: ble+cloud`). An outlet Bluetooth measured as off is 0 watts, not a cloud number. The standing rule is Library `Documentation/01-Operations/2026-10-01-ecoflow-ble-reads.md`. Pack watts and the channel-1 look are spoken on Bruce’s combined `solar_desk` at :22 and :52 (title “Energy and solar”); the separate Carly `energy_report` job is retired. A reading older than 30 minutes is "out of range." A last reading of 5 percent or less that is older than 30 minutes is discharged and powered off, not a pack that is still reporting. Delta 2 AC in above 550 W is generator. River 2 Pro AC in above 300 W is generator, unless that input matches the Delta's AC output, which is a transfer. The same rules are in `Energy/lib/read_runner.py` and `Energy/scripts/load_categories.py`.

River 2 Pro AC auto-recover is verified live via `rr-river2pro-ac-recover.timer`, kept enabled persistently 24/7 with `OnBootSec=45`, `OnUnitActiveSec=45`, and `Persistent=true`; `COOLDOWN_SEC=0` retries each tick while AC is off and `rootrecord` linger is enabled (`linger=yes`). AC off triggers recovery with no SOC floor (`COOLDOWN_SEC=0`); fresh `ac_input_power`≥50W still triggers when the switch is unknown. A stale `ac_ports=false` does not block forever unless fresh AC output shows the outlet already delivering. AC already on is a no-op. Alexander verified recovery after power-off at ~04:30 HST.

Measured 2026-10-02, not a new policy. Pre-dawn, River SOC fell to about 0–1.1%. The recover gate (on only if SOC ≥5% or AC-in ≥50 W) blocked re-enable, and cloudflared and the desk died with power. Last-known before the drop (overnight, not a live read at 11:45): River about 1.1% SOC, Delta 2 about 2.7%. Desk Cursor was offline from about 05:44–05:51 HST through about 11:45 HST; River SOC and AC were unmeasurable from Master in that window. At reconnect (~11:45–11:49 HST) River was about 16% SOC (cloud), AC out about 46 W, USB-C about 20 W (AC appears on); Delta 2 was about 11% with about 71 W solar in. A `river2pro-ac-on` attempt over BLE returned NeedBindInstallFirst / auth failed and did not change the outlet. Recover no-op reason was `ac_unknown_or_stale` because the `ac_ports` sample was stale from about 05:45. The soft gate was not touched and the poller was not flipped. The BLE write attempt failed (`NeedBindInstallFirst`), but BLE reads were not fully blocked; live read/trigger behavior remained separate and write behavior was still unmeasured. Alexander’s keep-retry (`COOLDOWN_SEC=0`, 45-second timer) remains the verified timer behavior above. Master’s measured block is the gate refusing re-enable when SOC was about 0–1.1% and AC-in was not ≥50 W. This page states both and does not pick a winner; Alexander ordered ~12:00 HST that the floor be dropped. Landed ~12:06 HST on the desk: no SOC floor, and a stale false no longer blocks when the outlet is not already delivering. BLE auth failures now name the exception (`NeedBindInstallFirst` was River encrypted-session labeling, not a re-pair order for both packs). The 04:30 keep-retry stays. Master landed the BLE/read-side and force-AC portions for `prefer_api=0`; `read_runner` no longer falls through to cloud, and `ac-force.sh` turns AC on only from in-range BLE sight/samples, treats fresh `ac_ports=true` as a no-op, never forces AC off, and is used by River recover. `rr-delta2-ac-force.timer` is active at ~45s; `ble-owner.py` watches both MACs, rescans when sight is older than 90s, and holds no GATT session so the reader can connect. Delta BLE authenticates and reads: 12:23 HST, ~16.5% SOC, ~166W solar, AC on; the force timer is already-on/no-op. River’s last field BLE remains ~05:45; sighting flickers (`seen=1`) but the session ends `error_not_found`, so there is no new field sample; AC-on fired at 12:27 with null readback, not confirmed. `NeedBindInstallFirst` was River encrypted-session labeling, not a re-pair order or dead radio. Cloud is no longer the recover source for BLE packs. **Paused ~12:32 HST:** River BLE chase is paused until Alexander says go; no more edits from Master. Soft gate and live timers were left as they were. **Still open, not fixed:** River still has no field sample since ~05:45. `RR_LOCAL_DATA_POLL=0` remains. Backups are `*.bak-20261002-dual-ac-force`; no commit/push or invented SHA.


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
| Data | `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/layers/` (raw in `1sec.db`, then condensed layers) |
| Sun times | `scripts/sun_times.py` (G1 `hourly-solar-weather/sun_times.py` port, stdlib, Open-Meteo once per HST day) → Database `Energy/sun/sun-times-last.json`. Pacific hourly `energy_sun_times` was removed 2026-10-02. ML2 catalog has the name and no clock yet. LANDED · PASS one run 2026-09-29 13:26 HST |
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
