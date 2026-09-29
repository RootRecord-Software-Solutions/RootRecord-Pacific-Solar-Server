"""RootRecord telemetry condensation engine.

Aggregates canonical observations into fixed reporting periods. Missing values
remain missing; measured zero remains a real measurement.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
import math
from zoneinfo import ZoneInfo

LAYERS=("1sec","1min","5min","15min","1hour","day","7days","month","year")
SECONDS={"1sec":1,"1min":60,"5min":300,"15min":900,"1hour":3600,"7days":604800}
LOCAL=ZoneInfo("Pacific/Honolulu")
MAX_INTERPOLATION_GAP_S=60.0

def _dt(s): return datetime.fromisoformat(s.replace("Z","+00:00"))
def _iso(d): return d.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")

def period_bounds(layer,at):
    d=at.astimezone(LOCAL)
    if layer=="1sec": start=d.replace(microsecond=0)
    elif layer=="1min": start=d.replace(second=0,microsecond=0)
    elif layer=="5min": start=d.replace(minute=(d.minute//5)*5,second=0,microsecond=0)
    elif layer=="15min": start=d.replace(minute=(d.minute//15)*15,second=0,microsecond=0)
    elif layer=="1hour": start=d.replace(minute=0,second=0,microsecond=0)
    elif layer=="day": start=d.replace(hour=0,minute=0,second=0,microsecond=0)
    elif layer=="7days":
        start=datetime.combine(d.date()-timedelta(days=d.weekday()),datetime.min.time(),LOCAL)
    elif layer=="month": start=d.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    elif layer=="year": start=d.replace(month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
    else: raise ValueError(layer)
    if layer in SECONDS: end=start+timedelta(seconds=SECONDS[layer])
    elif layer=="month":
        y=start.year+int(start.month==12); m=1 if start.month==12 else start.month+1
        end=start.replace(year=y,month=m)
    else: end=start.replace(year=start.year+1) if layer=="year" else start+timedelta(days=1)
    return start,end

def _state(rows):
    states={r["state"] for r in rows if r.get("in_period",True)}
    if "measured" in states or "defaulted" in states: return "measured"
    if states and states <= {"not_applicable"}: return "not_applicable"
    return "missing"

def _energy(rows,start,end):
    total=0.0; covered=0.0
    points=[(r["value"],_dt(r["at"])) for r in rows
            if r["value"] is not None and r["state"] in ("measured","defaulted")]
    if len(points)<2: return None,0.0
    for (v1,t1),(v2,t2) in zip(points,points[1:]):
        gap=(t2-t1).total_seconds()
        if gap<=0 or gap>MAX_INTERPOLATION_GAP_S: continue
        a=max(t1,start); b=min(t2,end)
        if b<=a: continue
        frac1=(a-t1).total_seconds()/gap; frac2=(b-t1).total_seconds()/gap
        va=v1+(v2-v1)*frac1; vb=v1+(v2-v1)*frac2
        dt=(b-a).total_seconds()
        total += (va+vb)*0.5*dt/3600.0
        covered += dt
    return total,covered

def _aggregate(rows,start,end,power=False):
    period_rows=[r for r in rows if r.get("in_period",True)]
    numeric=[r for r in period_rows if r["value"] is not None and r["state"] in ("measured","defaulted")]
    vals=[float(r["value"]) for r in numeric]
    if not vals:
        return {"sample_count":len(period_rows),"valid_sample_count":0,"coverage_pct":0.0,
                "observed_span_s":0.0,"valid_duration_s":0.0 if power else None,
                "value_avg":None,"value_min":None,"value_max":None,"value_sum":None,
                "value_delta":None,"energy_wh":None,"state":_state(rows)}
    energy,covered=_energy(rows,start,end) if power else (None,0.0)
    observed_span_s=max(0.0,(_dt(numeric[-1]["at"])-_dt(numeric[0]["at"])).total_seconds()) if len(numeric)>1 else 0.0
    span=(end-start).total_seconds()
    coverage=100.0*covered/span if power else 100.0*len(numeric)/max(1,len(period_rows))
    return {"sample_count":len(period_rows),"valid_sample_count":len(vals),"coverage_pct":min(100.0,coverage),"observed_span_s":observed_span_s,"valid_duration_s":covered if power else None,
            "value_avg":sum(vals)/len(vals),"value_min":min(vals),"value_max":max(vals),
            "value_sum":sum(vals),"value_delta":vals[-1]-vals[0],"energy_wh":energy,
            "state":"measured"}

def aggregate_period(conn,layer,start,end,source_layer="raw"):
    if layer not in LAYERS: raise ValueError(layer)
    period_start,period_end=_iso(start),_iso(end)
    now=_iso(datetime.now(timezone.utc))
    conn.execute("""INSERT INTO aggregation_run(layer,period_start,period_end,source_layer,status,started_at)
                    VALUES(?,?,?,?,?,?)
                    ON CONFLICT(layer,period_start,period_end) DO UPDATE SET
                    source_layer=excluded.source_layer,status='running',started_at=excluded.started_at,
                    completed_at=NULL,row_count=NULL""",
                 (layer,period_start,period_end,source_layer,"running",now))
    run=conn.execute("SELECT aggregation_run_id FROM aggregation_run WHERE layer=? AND period_start=? AND period_end=?",
                     (layer,period_start,period_end)).fetchone()[0]
    conn.execute("DELETE FROM aggregate_measurement WHERE aggregation_run_id=?",(run,))

    grouped={}
    def add(subject_type,subject_id,metric,value,at,state,unit,in_period):
        grouped.setdefault((subject_type,subject_id,metric,unit),[]).append(
            {"value":value,"at":at,"state":state,"in_period":in_period})

    # Include a one-minute neighbor window so power integration can use the
    # last valid point before and first valid point after a reporting boundary.
    # Statistics/counts still use only observations inside the period.
    neighbor_start=_iso(start-timedelta(seconds=MAX_INTERPOLATION_GAP_S))
    neighbor_end=_iso(end+timedelta(seconds=MAX_INTERPOLATION_GAP_S))

    for r in conn.execute("""SELECT o.device_id,dm.metric_key,dm.value_num,dm.value_bool,
                                    dm.value_text,dm.unit,dm.state,o.observed_at
                             FROM device_measurement dm JOIN observation o ON o.observation_id=dm.observation_id
                             WHERE o.observed_at>=? AND o.observed_at<? ORDER BY dm.metric_key,o.observed_at""",
                          (neighbor_start,neighbor_end)):
        value=r["value_num"] if r["value_num"] is not None else r["value_bool"]
        add("device",r["device_id"],r["metric_key"],value,r["observed_at"],r["state"],r["unit"],
            period_start<=r["observed_at"]<period_end)

    for r in conn.execute("""SELECT b.battery_id,bm.metric_key,bm.value_num,bm.value_bool,bm.unit,bm.state,o.observed_at
                             FROM battery_measurement bm JOIN battery b ON b.battery_id=bm.battery_id
                             JOIN observation o ON o.observation_id=bm.observation_id
                             WHERE o.observed_at>=? AND o.observed_at<? ORDER BY b.battery_id,bm.metric_key,o.observed_at""",
                          (neighbor_start,neighbor_end)):
        value=r["value_num"] if r["value_num"] is not None else r["value_bool"]
        add("battery",r["battery_id"],r["metric_key"],value,r["observed_at"],r["state"],r["unit"],
            period_start<=r["observed_at"]<period_end)

    for r in conn.execute("""SELECT o.device_id,em.channel,em.metric_key,em.value_num,em.unit,em.state,o.observed_at
                             FROM electrical_measurement em JOIN observation o ON o.observation_id=em.observation_id
                             WHERE o.observed_at>=? AND o.observed_at<? ORDER BY o.device_id,em.channel,em.metric_key,o.observed_at""",
                          (neighbor_start,neighbor_end)):
        add("device",r["device_id"],f"electrical:{r['channel']}:{r['metric_key']}",r["value_num"],r["observed_at"],r["state"],r["unit"],
            period_start<=r["observed_at"]<period_end)

    for r in conn.execute("""SELECT o.device_id,o.online,o.observed_at
                             FROM observation o WHERE o.observed_at>=? AND o.observed_at<? AND o.online IS NOT NULL
                             ORDER BY o.device_id,o.observed_at""",(neighbor_start,neighbor_end)):
        add("device",r["device_id"],"online",r["online"],r["observed_at"],"measured",None,
            period_start<=r["observed_at"]<period_end)

    for r in conn.execute("""SELECT o.device_id,pm.port_id,pm.metric_key,pm.value_num,pm.value_bool,
                                    pm.value_text,pm.unit,pm.state,o.observed_at
                             FROM port_measurement pm JOIN observation o ON o.observation_id=pm.observation_id
                             WHERE o.observed_at>=? AND o.observed_at<? ORDER BY pm.port_id,pm.metric_key,o.observed_at""",
                          (neighbor_start,neighbor_end)):
        value=r["value_num"] if r["value_num"] is not None else r["value_bool"]
        # aggregate_measurement is numeric by design; text port metadata stays
        # in the canonical port_measurement table and is never coerced to float.
        if value is not None:
            add("port",r["port_id"],r["metric_key"],value,r["observed_at"],r["state"],r["unit"],
                period_start<=r["observed_at"]<period_end)

    count=0
    for (stype,sid,metric,unit),rows in grouped.items():
        rows.sort(key=lambda r:r["at"])
        power=unit=="W" or metric.endswith(":power_w") or metric in ("input_power","output_power")
        s=_aggregate(rows,start,end,power)
        conn.execute("""INSERT INTO aggregate_measurement
          (aggregation_run_id,subject_type,subject_id,metric_key,unit,sample_count,valid_sample_count,
           expected_sample_count,coverage_pct,observed_span_s,valid_duration_s,value_avg,value_min,value_max,value_sum,value_delta,energy_wh,state)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (run,stype,sid,metric,unit,s["sample_count"],s["valid_sample_count"],
           math.ceil((end-start).total_seconds()/10),s["coverage_pct"],s["observed_span_s"],s["valid_duration_s"],
           s["value_avg"],s["value_min"],s["value_max"],s["value_sum"],s["value_delta"],s["energy_wh"],s["state"]))
        count+=1
    watermark=conn.execute("SELECT MAX(observed_at) FROM observation WHERE observed_at>=? AND observed_at<?",
                           (period_start,period_end)).fetchone()[0]
    conn.execute("UPDATE aggregation_run SET status='complete',completed_at=?,source_watermark=?,row_count=? WHERE aggregation_run_id=?",
                 (now,watermark,count,run))
    conn.commit()
    return count

def aggregate_at(conn,layer,at,source_layer="raw"):
    start,end=period_bounds(layer,at)
    return aggregate_period(conn,layer,start,end,source_layer)
