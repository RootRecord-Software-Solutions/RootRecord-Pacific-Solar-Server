# Cloud-Quota

EcoFlow Open Platform quota, labeled `source: cloud`. BLE stays the live read.

The default run prints status and does not call EcoFlow:

```text
python3 scripts/quota_poll.py
```

`RR_ECOFLOW_CLOUD` stays unset. A live quota call happens only when that variable is `1`. The same gate wraps `Energy/lib/read_runner.py`: a BLE miss returns WAITING and does not HTTP.

Key names, loaded only through `Energy/lib/envload.py` from `/home/rootrecord/master/master-key.env`: `ECOFLOW_ACCESS`, `ECOFLOW_SECRET`, `ECOFLOW_REGION`, `ECOFLOW_DELTA_2`, `ECOFLOW_RIVER_2_PRO`, `ECOFLOW_DELTA_2_SECONDARY`. Values are never printed.

Snapshots, when the gate is on, go to Database `Energy/Cloud-Quota/`. Logs go to Database `Logs/Energy/Cloud-Quota/`. BLE samples stay in `Energy/samples`.

Job `ecoflow_cloud_quota` stays out of `jobs.py` while that file has other edits. The proposed block is in the work order. It is off unless `RR_ECOFLOW_CLOUD=1` at poller start.
