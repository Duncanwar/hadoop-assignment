#!/usr/bin/env python3
"""report_data.py -- assemble every figure the report quotes into report_data.json,
straight from the MapReduce output in output/*.tsv and the job logs in evidence/.
Nothing in the report is typed by hand; if a job is re-run, the report follows."""
import json, os, glob, sys
sys.path.insert(0, os.path.dirname(__file__))
import zones

B = os.path.join(os.path.dirname(__file__), "..")
def rows(n):
    p = os.path.join(B, "output", n + ".tsv")
    return [l.rstrip("\n").split("\t") for l in open(p) if l.strip()]

D = {}

# ---- cleaning counters ----
js = json.load(open(os.path.join(B, "evidence", "job_stats.json")))
clean = js["10_job_clean"]
D["clean"] = clean["custom"]
D["jobs"] = [{"log": k, "name": v["name"], "app": v["app_id"], "job": v["job_id"],
              "elapsed": v["elapsed_s"],
              "map_in": v["counters"].get("Map input records"),
              "map_out": v["counters"].get("Map output records"),
              "comb_in": v["counters"].get("Combine input records"),
              "comb_out": v["counters"].get("Combine output records"),
              "red_in": v["counters"].get("Reduce input records"),
              "red_out": v["counters"].get("Reduce output records"),
              "maps": v["counters"].get("Launched map tasks"),
              "reds": v["counters"].get("Launched reduce tasks"),
              "cpu_ms": v["counters"].get("CPU time spent (ms)"),
              "hdfs_read": v.get("hdfs_read"), "hdfs_written": v.get("hdfs_written"),
              "peak_map_mem": v["counters"].get("Peak Map Physical memory (bytes)"),
              "peak_red_mem": v["counters"].get("Peak Reduce Physical memory (bytes)"),
              "spilled": v["counters"].get("Spilled Records"),
              "map_out_bytes": v["counters"].get("Map output bytes"),
              "map_out_mat": v["counters"].get("Map output materialized bytes"),
              } for k, v in sorted(js.items())]

# ---- hourly ----
h = sorted((r[0], int(r[1])) for r in rows("hourly"))
D["hourly"] = [{"hour": k, "trips": v} for k, v in h]
D["hourly_total"] = sum(v for _, v in h)
D["hour_peak"] = max(h, key=lambda x: x[1])
D["hour_low"] = min(h, key=lambda x: x[1])

# ---- daily ----
d = []
for r in rows("daily"):
    n, day, kind = r[0].split("_")
    d.append({"n": int(n), "day": day, "kind": kind, "trips": int(r[1])})
d.sort(key=lambda x: x["n"])
D["daily"] = d
D["weekday_trips"] = sum(x["trips"] for x in d if x["kind"] == "WEEKDAY")
D["weekend_trips"] = sum(x["trips"] for x in d if x["kind"] == "WEEKEND")
D["weekday_avg"] = D["weekday_trips"] / 5.0
D["weekend_avg"] = D["weekend_trips"] / 2.0
D["day_peak"] = max(d, key=lambda x: x["trips"])
D["day_low"] = min(d, key=lambda x: x["trips"])

# ---- zones ----
D["top10_zones"] = [{"rank": int(r[0]), "id": int(r[1]), "name": zones.name(int(r[1])),
                     "trips": int(r[2])} for r in rows("top10_zones_trips")]
D["bottom10_zones"] = [{"rank": int(r[0]), "id": int(r[1]), "name": zones.name(int(r[1])),
                        "trips": int(r[2])} for r in rows("bottom10_zones_trips")]
D["n_zones"] = len(rows("locations"))

# ---- revenue by zone (stage 1) + stage 2 top 10 ----
rev = rows("revenue")
D["revenue_total"] = sum(float(r[4]) for r in rev)
D["fare_total"] = sum(float(r[2]) for r in rev)
D["tips_total"] = sum(float(r[3]) for r in rev)
D["top10_revenue"] = [{"rank": int(r[0]), "id": int(r[1]), "name": zones.name(int(r[1])),
                       "trips": int(r[2]), "fare": float(r[3]), "tips": float(r[4]),
                       "revenue": float(r[5]), "avg_fare": float(r[6]),
                       "avg_tip": float(r[7]), "avg_dist": float(r[8]),
                       "rev_per_mile": float(r[9])} for r in rows("top10_revenue_zones")]
D["revenue_sample"] = [{"id": int(r[0]), "name": zones.name(int(r[0])), "trips": int(r[1]),
                        "revenue": float(r[4])} for r in rev[:6]]

# ---- payment ----
pay = []
for r in rows("payment"):
    code, label = r[0].split("_", 1)
    pay.append({"code": int(code), "label": label, "trips": int(r[1]),
                "revenue": float(r[2]), "avg_fare": float(r[3]), "avg_tip": float(r[4]),
                "avg_total": float(r[5]), "avg_dist": float(r[6]),
                "tip_rate": float(r[7]), "pct_tipped": float(r[8])})
pay.sort(key=lambda x: -x["revenue"])
D["payment"] = pay
D["payment_revenue_total"] = sum(x["revenue"] for x in pay)

# ---- distance ----
D["distance"] = [{"band": r[0].split("_", 1)[1], "trips": int(r[1]), "revenue": float(r[2]),
                  "avg_fare": float(r[3]), "avg_total": float(r[4]), "avg_dist": float(r[5]),
                  "avg_tip": float(r[6]), "avg_min": float(r[7]),
                  "fare_per_mile": float(r[8]), "mph": float(r[9])} for r in rows("distance")]

# ---- duration ----
D["duration"] = [{"band": r[0].split("_", 1)[1], "trips": int(r[1]), "revenue": float(r[2]),
                  "avg_fare": float(r[3]), "avg_total": float(r[4]), "avg_dist": float(r[5]),
                  "avg_tip": float(r[6]), "avg_min": float(r[7]),
                  "fare_per_mile": float(r[8]), "mph": float(r[9])} for r in rows("duration")]

# ---- routes ----
def route(r):
    pu, do = r[1].split("->")
    return {"rank": int(r[0]), "route": f"{zones.short(int(pu))} -> {zones.short(int(do))}",
            "ids": f"{int(pu)}->{int(do)}", "trips": int(r[2]), "revenue": float(r[3]),
            "avg_rev": float(r[4]), "avg_dist": float(r[5]), "avg_min": float(r[6])}
D["top20_routes_trips"] = [route(r) for r in rows("top20_routes_trips")]
D["top20_routes_revenue"] = [route(r) for r in rows("top20_routes_revenue")]
D["n_routes"] = len(rows("routes"))
tt = {r["ids"] for r in D["top20_routes_trips"]}
tr = {r["ids"] for r in D["top20_routes_revenue"]}
D["routes_overlap"] = sorted(tt & tr)

# ---- anomalies ----
an = {r[0]: (int(r[1]), float(r[2])) for r in rows("anomalies")}
D["anom_total"] = an["AAA_TOTAL_RECORDS"][0]
D["anom_flagged"] = an["AAB_ANOMALOUS_RECORDS"]
D["anomalies"] = sorted([{"label": k, "count": v[0], "pct": v[1]}
                         for k, v in an.items() if not k.startswith("AA")],
                        key=lambda x: -x["count"])

with open(os.path.join(B, "docs", "report_data.json"), "w") as fh:
    json.dump(D, fh, indent=1)
print("report_data.json written")
print("  cleaned records :", D["clean"]["VALID_RECORDS"])
print("  total revenue   : $%,.2f".replace("%,", "%") % D["revenue_total"])
print("  zones / routes  :", D["n_zones"], "/", D["n_routes"])
print("  anomalous       : %d (%.2f%%)" % D["anom_flagged"])
