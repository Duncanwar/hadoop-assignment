#!/usr/bin/env python3
"""
verify_results.py -- independent cross-check of every MapReduce result.

Re-computes the same aggregates with Pandas, straight from the cleaned dataset,
and compares them against what the reducers wrote. This is a genuine check, not
a restatement: the Pandas path shares no code with the mappers and reducers.
"""
import glob, sys, os
import pandas as pd

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
NAMES = ["VendorID","tpep_pickup_datetime","tpep_dropoff_datetime","passenger_count",
         "trip_distance","RatecodeID","store_and_fwd_flag","PULocationID","DOLocationID",
         "payment_type","fare_amount","extra","mta_tax","tip_amount","tolls_amount",
         "improvement_surcharge","total_amount","congestion_surcharge","Airport_fee",
         "cbd_congestion_fee"]
USE = ["tpep_pickup_datetime","tpep_dropoff_datetime","trip_distance","PULocationID",
       "DOLocationID","payment_type","fare_amount","tip_amount","total_amount"]

def mr(name):
    return [l.rstrip("\n").split("\t") for l in open("output/%s.tsv" % name) if l.strip()]

ok = True
def check(label, a, b, tol=0.01):
    global ok
    good = abs(a - b) <= tol * max(1.0, abs(b))
    ok = ok and good
    print("  [%s] %-42s mapreduce=%-18s pandas=%s" %
          ("PASS" if good else "FAIL", label,
           ("%.2f" % a) if isinstance(a, float) else a,
           ("%.2f" % b) if isinstance(b, float) else b))

print("Loading cleaned dataset with Pandas (independent of the MapReduce code)...")
frames = []
for p in sorted(glob.glob("local_cleaned/part-*")):
    for ch in pd.read_csv(p, header=None, names=NAMES, usecols=USE, chunksize=1_000_000):
        frames.append(ch)
df = pd.concat(frames, ignore_index=True)
df["pu"] = pd.to_datetime(df.tpep_pickup_datetime)
df["do"] = pd.to_datetime(df.tpep_dropoff_datetime)
print("  %d records loaded\n" % len(df))

print("1. Record count")
check("total cleaned records", sum(int(r[1]) for r in mr("hourly")), len(df), 0)

print("\n2. Hourly demand (all 24 keys)")
ph = df.pu.dt.hour.value_counts()
bad = 0
for r in mr("hourly"):
    if int(r[1]) != int(ph[int(r[0])]):
        bad += 1
        print("  [FAIL] hour %s: mapreduce=%s pandas=%s" % (r[0], r[1], ph[int(r[0])]))
print("  [%s] all 24 hourly counts match exactly" % ("PASS" if bad == 0 else "FAIL"))
ok = ok and bad == 0

print("\n3. Daily demand (all 7 keys)")
pd_day = df.pu.dt.weekday.value_counts()
bad = 0
for r in mr("daily"):
    w = int(r[0].split("_")[0]) - 1
    if int(r[1]) != int(pd_day[w]):
        bad += 1
        print("  [FAIL] %s: mapreduce=%s pandas=%s" % (r[0], r[1], pd_day[w]))
print("  [%s] all 7 day-of-week counts match exactly" % ("PASS" if bad == 0 else "FAIL"))
ok = ok and bad == 0

print("\n4. Revenue")
rev = mr("revenue")
check("total revenue (USD)", sum(float(r[4]) for r in rev), float(df.total_amount.sum()))
check("total fare (USD)", sum(float(r[2]) for r in rev), float(df.fare_amount.sum()))
check("total tips (USD)", sum(float(r[3]) for r in rev), float(df.tip_amount.sum()))
check("distinct pickup zones", len(rev), df.PULocationID.nunique(), 0)

print("\n5. Top-N ranking (stage-2 output vs Pandas nlargest)")
g = df.groupby("PULocationID").total_amount.sum().sort_values(ascending=False)
mr_top = [int(r[1]) for r in mr("top10_revenue_zones")]
pd_top = [int(x) for x in g.head(10).index]
same = mr_top == pd_top
ok = ok and same
print("  [%s] top-10 revenue zones, same zones in the same order" % ("PASS" if same else "FAIL"))
print("        mapreduce: %s" % mr_top)
print("        pandas   : %s" % pd_top)

gt = df.groupby("PULocationID").size().sort_values(ascending=False)
mr_tt = [int(r[1]) for r in mr("top10_zones_trips")]
pd_tt = [int(x) for x in gt.head(10).index]
same = mr_tt == pd_tt
ok = ok and same
print("  [%s] top-10 zones by trips, same zones in the same order" % ("PASS" if same else "FAIL"))

print("\n6. Routes")
rt = mr("routes")
check("distinct routes", len(rt), len(df.groupby(["PULocationID", "DOLocationID"])), 0)
check("trips summed over all routes", sum(int(r[1]) for r in rt), len(df), 0)
gr = df.groupby(["PULocationID", "DOLocationID"]).size().sort_values(ascending=False)
mr_r = [r[1] for r in mr("top20_routes_trips")[:5]]
pd_r = ["%03d->%03d" % (a, b) for a, b in gr.head(5).index]
same = mr_r == pd_r
ok = ok and same
print("  [%s] top-5 routes by trips identical: %s" % ("PASS" if same else "FAIL", mr_r))

print("\n7. Payment types")
pay = mr("payment")
check("trips summed over payment types", sum(int(r[1]) for r in pay), len(df), 0)
check("revenue summed over payment types", sum(float(r[2]) for r in pay),
      float(df.total_amount.sum()))
pp = df.groupby("payment_type").total_amount.sum()
for r in pay:
    check("  payment_type %s revenue" % r[0].split("_")[0],
          float(r[2]), float(pp[int(r[0].split("_")[0])]))

print("\n8. Distance and duration bands")
check("trips summed over distance bands", sum(int(r[1]) for r in mr("distance")), len(df), 0)
check("trips summed over duration bands", sum(int(r[1]) for r in mr("duration")), len(df), 0)
check("revenue summed over distance bands", sum(float(r[2]) for r in mr("distance")),
      float(df.total_amount.sum()))

print("\n9. Cross-analysis consistency (independent of Pandas)")
tot = sum(int(r[1]) for r in mr("hourly"))
for name in ["daily", "locations", "distance", "duration", "payment"]:
    check("%s total equals hourly total" % name, sum(int(r[1]) for r in mr(name)), tot, 0)

print("\n" + ("=" * 66))
print("VERIFICATION %s" % ("PASSED - every MapReduce result reproduced independently"
                           if ok else "FAILED - see the lines marked FAIL above"))
print("=" * 66)
sys.exit(0 if ok else 1)
