#!/usr/bin/env python3
"""starlink_status.py — READ-ONLY Starlink dish status for Root Monitor (added 2026-09-29).

Runs in Apps/Control-Panel/Starlink/.venv (python 3.12 + starlink-grpc-core, installed with uv, no sudo).
Calls only the dish's get_status over gRPC at 192.168.100.1:9200 (status_data). Never reboots, stows or changes
anything. Prints one JSON object per poll on stdout.
  --once        one poll then exit
  --loop SEC    poll every SEC seconds (>= 10) until stdin closes / SIGTERM (Root Monitor kills it on page leave)
"""
import argparse
import json
import sys
import time

TARGET = "192.168.100.1:9200"


def poll(ctx):
    import starlink_grpc as sg
    t0 = time.time()
    try:
        status, obstruct, alerts = sg.status_data(ctx)
        out = {"ok": True, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rpc_ms": round((time.time() - t0) * 1000),
               "state": status.get("state"), "uptime_s": status.get("uptime"),
               "pop_ping_latency_ms": status.get("pop_ping_latency_ms"), "pop_ping_drop_rate": status.get("pop_ping_drop_rate"),
               "downlink_bps": status.get("downlink_throughput_bps"), "uplink_bps": status.get("uplink_throughput_bps"),
               "fraction_obstructed": status.get("fraction_obstructed"), "currently_obstructed": status.get("currently_obstructed"),
               "seconds_obstructed": status.get("seconds_obstructed"),
               "hardware_version": status.get("hardware_version"), "software_version": status.get("software_version"),
               "alerts": sorted(k for k, v in (alerts or {}).items() if v)}
        # never forward the dish id / serial
        return out
    except Exception as e:
        return {"ok": False, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "error": f"{type(e).__name__}: {str(e)[:160]}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", type=int, default=0)
    a = ap.parse_args()
    import starlink_grpc as sg
    ctx = sg.ChannelContext(target=TARGET)
    try:
        if a.once or a.loop <= 0:
            print(json.dumps(poll(ctx)), flush=True)
            return
        iv = max(10, a.loop)
        while True:
            print(json.dumps(poll(ctx)), flush=True)
            time.sleep(iv)
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        try:
            ctx.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
