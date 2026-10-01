# Cloud-Quota

EcoFlow Open Platform quota, labeled `source: cloud`. BLE stays the live read.

The default run prints status and does not call EcoFlow:

```text
python3 scripts/quota_poll.py
```

A BLE miss in `Energy/lib/read_runner.py` calls this quota API when the device is online in the EcoFlow device list. Offline quota is not written, because that payload stays frozen. Repeat misses reuse the last cloud snapshot for two minutes. `RR_ECOFLOW_CLOUD` still gates `quota_poll.py`: that script prints `cloud=off` and does not HTTP unless the variable is `1`.

Key names, loaded only through `Energy/lib/envload.py` from `/home/rootrecord/master/master-key.env`: `ECOFLOW_ACCESS`, `ECOFLOW_SECRET`, `ECOFLOW_REGION`, `ECOFLOW_DELTA_2`, `ECOFLOW_RIVER_2_PRO`, `ECOFLOW_DELTA_2_SECONDARY`. Values are never printed.

Snapshots, when the gate is on, go to Database `Energy/Cloud-Quota/`. Logs go to Database `Logs/Energy/Cloud-Quota/`. BLE samples stay in `Energy/samples`.

Job `ecoflow_cloud_quota` stays out of `jobs.py` while that file has other edits. The proposed block is in the work order. It is off unless `RR_ECOFLOW_CLOUD=1` at poller start.
