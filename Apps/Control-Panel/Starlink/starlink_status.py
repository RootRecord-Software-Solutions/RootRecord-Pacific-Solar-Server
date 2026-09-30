# ==============================================================================
# FILE: Apps/Control-Panel/Starlink/starlink_status.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""starlink_status.py — READ-ONLY Starlink dish status for Root Monitor (added 2026-09-29).

Runs in Apps/Control-Panel/Starlink/.venv (python 3.12 + starlink-grpc-core, installed with uv, no sudo).
Calls only the dish's get_status over gRPC at 192.168.100.1:9200 (status_data). Never reboots, stows or changes
anything. Prints one JSON object per poll on stdout.
  --once        one poll then exit
  --loop SEC    poll every SEC seconds (>= 10) until stdin closes / SIGTERM (Root Monitor kills it on page leave)
"""
import argparse  # info: import argparse
import json  # info: import json
import sys  # info: import sys
import time  # info: import time

TARGET = "192.168.100.1:9200"  # info: set TARGET


# ====================================================
# SECTION: function poll
# What it does: poll.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poll(ctx):  # info: def poll
    import starlink_grpc as sg  # info: import starlink_grpc as sg
    t0 = time.time()  # info: set t0
    try:  # info: try :
        status, obstruct, alerts = sg.status_data(ctx)  # info: status , obstruct , alerts = sg .
        out = {"ok": True, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rpc_ms": round((time.time() - t0) * 1000),  # info: set out
               "state": status.get("state"), "uptime_s": status.get("uptime"),  # info: "state" : status . get ( "state" )
               "pop_ping_latency_ms": status.get("pop_ping_latency_ms"), "pop_ping_drop_rate": status.get("pop_ping_drop_rate"),  # info: "pop_ping_latency_ms" : status . get ( "pop_ping_latency_ms" )
               "downlink_bps": status.get("downlink_throughput_bps"), "uplink_bps": status.get("uplink_throughput_bps"),  # info: "downlink_bps" : status . get ( "downlink_throughput_bps" )
               "fraction_obstructed": status.get("fraction_obstructed"), "currently_obstructed": status.get("currently_obstructed"),  # info: "fraction_obstructed" : status . get ( "fraction_obstructed" )
               "seconds_obstructed": status.get("seconds_obstructed"),  # info: "seconds_obstructed" : status . get ( "seconds_obstructed" )
               "hardware_version": status.get("hardware_version"), "software_version": status.get("software_version"),  # info: "hardware_version" : status . get ( "hardware_version" )
               "alerts": sorted(k for k, v in (alerts or {}).items() if v)}  # info: "alerts" : sorted ( k for k ,
        # never forward the dish id / serial
        return out  # info: return out
    except Exception as e:  # info: except Exception as e :
        return {"ok": False, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "error": f"{type(e).__name__}: {str(e)[:160]}"}  # info: return { "ok" : False , "at" :


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main():  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("--once", action="store_true")  # info: ap . add_argument ( "--once" , action =
    ap.add_argument("--loop", type=int, default=0)  # info: ap . add_argument ( "--loop" , type =
    a = ap.parse_args()  # info: set a
    import starlink_grpc as sg  # info: import starlink_grpc as sg
    ctx = sg.ChannelContext(target=TARGET)  # info: set ctx
    try:  # info: try :
        if a.once or a.loop <= 0:  # info: if a . once or a . loop
            print(json.dumps(poll(ctx)), flush=True)  # info: call print
            return  # info: return
        iv = max(10, a.loop)  # info: set iv
        while True:  # info: while True :
            print(json.dumps(poll(ctx)), flush=True)  # info: call print
            time.sleep(iv)  # info: time . sleep ( iv )
    except (BrokenPipeError, KeyboardInterrupt):  # info: except ( BrokenPipeError , KeyboardInterrupt ) :
        pass  # info: pass
    finally:  # info: finally :
        try:  # info: try :
            ctx.close()  # info: ctx . close ( )
        except Exception:  # info: except Exception :
            pass  # info: pass


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
