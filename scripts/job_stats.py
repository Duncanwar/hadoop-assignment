#!/usr/bin/env python3
"""job_stats.py -- parse the Hadoop Streaming driver logs in evidence/ into a
single machine-readable summary of every job that ran (counters, timings,
application id).  Used to build the report's job table and the performance
comparison, so no figure in the report is typed by hand."""
import re, os, json, glob

EV = os.path.join(os.path.dirname(__file__), "..", "evidence")
WANT = ["Map input records","Map output records","Combine input records",
        "Combine output records","Reduce input records","Reduce output records",
        "Reduce input groups","Launched map tasks","Launched reduce tasks",
        "CPU time spent (ms)","Physical memory (bytes) snapshot",
        "Total time spent by all map tasks (ms)",
        "Total time spent by all reduce tasks (ms)",
        "Peak Map Physical memory (bytes)","Peak Reduce Physical memory (bytes)",
        "Bytes Read","Bytes Written","Map output bytes","Map output materialized bytes",
        "Failed Shuffles","Merged Map outputs","Spilled Records","Shuffled Maps "]

NAMES = {
 "10_job_clean": "01-DataCleaning-Validate-and-Deduplicate",
 "11_job_hourly": "02-HourlyTaxiDemand",
 "12_job_daily": "03-DailyDemandWeekdayWeekend",
 "13_job_locations": "04-PickupLocationTripCounts",
 "14_job_revenue": "05-RevenueByPickupZone-STAGE1",
 "15_job_payment": "06-PaymentMethodAnalysis",
 "16_job_distance": "07-DistanceBasedFareAnalysis",
 "17_job_routes": "08-BusiestPickupDropoffRoutes",
 "18_job_duration": "09-TripDurationAnalysis",
 "19_job_anomaly": "10-AnomalyDetection-RawFeed",
 "20_job_top10_revenue_zones": "11-Top10RevenueZones-STAGE2",
 "21_job_top10_zones_trips": "12-Top10PickupZonesByTrips",
 "22_job_bottom10_zones_trips": "13-Bottom10PickupZonesByTrips",
 "23_job_top20_routes_trips": "14-Top20RoutesByTripCount",
 "24_job_top20_routes_revenue": "15-Top20RoutesByRevenue",
 "25_job_revenue_bench": "BENCH-RevenueByPickupZone",
 "26_bench_hadoop_tiny": "BENCH-tiny-100k-records",
 "27_bench_hadoop_half": "BENCH-half-5.2M-records",
}

def parse(path):
    txt = open(path, errors="replace").read()
    j = {"log": os.path.basename(path)}
    m = re.search(r"application_[0-9_]+", txt);       j["app_id"] = m.group(0) if m else None
    m = re.search(r"job_[0-9_]+", txt);               j["job_id"] = m.group(0) if m else None
    m = re.search(r"ELAPSED_SECONDS=(\d+)", txt);     j["elapsed_s"] = int(m.group(1)) if m else None
    j["name"] = NAMES.get(os.path.basename(path).replace(".log", ""))
    m = re.search(r"HDFS: Number of bytes read=(\d+)", txt); j["hdfs_read"] = int(m.group(1)) if m else None
    m = re.search(r"HDFS: Number of bytes written=(\d+)", txt); j["hdfs_written"] = int(m.group(1)) if m else None
    c = {}
    for w in WANT:
        m = re.search(re.escape(w) + r"=(\d+)", txt)
        if m: c[w.strip()] = int(m.group(1))
    j["counters"] = c
    g = {}
    for m in re.finditer(r"^\t\t([A-Z_]+)=(\d+)$", txt, re.M):
        g[m.group(1)] = int(m.group(2))
    j["custom"] = g
    j["success"] = "Job complete" in txt or "Output directory:" in txt
    return j

if __name__ == "__main__":
    out = {}
    for p in sorted(glob.glob(os.path.join(EV, "[0-9][0-9]_*.log"))):
        j = parse(p)
        out[os.path.basename(p).replace(".log", "")] = j
    with open(os.path.join(EV, "job_stats.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    for k, v in out.items():
        print("%-32s %-40s %5ss  app=%s" % (k, (v["name"] or "")[:40], v["elapsed_s"], v["app_id"]))
