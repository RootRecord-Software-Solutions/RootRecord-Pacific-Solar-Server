# Energy / River-Car

Policy for the River 2 Pro car/12V port that powers external drives. Default off. Dry-run unless `--execute`, and `--execute` still refuses unless `RR_RIVER_CAR_EXECUTE=1`.

The live switch stays in `Energy/scripts/actions/river2pro-dc-on.sh` and `river2pro-dc-off.sh` (`enable_dc_12v_port`). This folder does not replace those scripts, the BLE poller, or `ecoflow_api.py`. It does not call the EcoFlow cloud API and it does not switch AC.

Poller job `energy_river_car_drive` is gated off (`RR_RIVER_CAR_DRIVE=1` at poller start). The tick still skips until state `auto` is true and an enabled copy job exists. Copy is a stub.

State and logs (runtime, not git):

- `2 - RootRecord-Database/Energy/River-Car/`
- `2 - RootRecord-Database/Logs/Energy/River-Car/`

```bash
cd "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/River-Car"
nice -n 10 python3 scripts/drive_automation.py --tick
nice -n 10 python3 scripts/river_car_dc.py --on
nice -n 10 python3 scripts/river_car_dc.py --status
```
