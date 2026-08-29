#!/usr/bin/env python3
"""
pandas_benchmark.py -- Section 12: conventional single-machine processing.

Runs the SAME analysis as the Hadoop job "04-RevenueByPickupZone"
(mapper_revenue.py + combiner_sums.py + reducer_revenue.py): trip count,
total fare, total tips, total revenue, average fare and average distance,
grouped by PULocationID, over the identical cleaned dataset.

It records wall-clock time and peak resident memory so the two approaches can
be compared on like-for-like terms.  Two variants are timed:

  full     -- read the whole cleaned dataset into one DataFrame, then groupby.
              This is what a data scientist writes first, and it is the variant
              that shows the memory wall.
  chunked  -- stream the same CSV in 500k-row chunks and accumulate partial
              group sums.  This is, in effect, a hand-written single-threaded
              MapReduce, and it is the fair comparison for "can Pandas do this
              at all".
"""
import sys, time, resource, glob
import pandas as pd

COLS = ["PULocationID", "fare_amount", "tip_amount", "tolls_amount",
        "total_amount", "trip_distance"]
NAMES = ["VendorID","tpep_pickup_datetime","tpep_dropoff_datetime","passenger_count",
         "trip_distance","RatecodeID","store_and_fwd_flag","PULocationID","DOLocationID",
         "payment_type","fare_amount","extra","mta_tax","tip_amount","tolls_amount",
         "improvement_surcharge","total_amount","congestion_surcharge","Airport_fee",
         "cbd_congestion_fee"]

def peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

def aggregate(df):
    g = df.groupby("PULocationID")
    out = g.agg(trips=("fare_amount", "size"),
                total_fare=("fare_amount", "sum"),
                total_tips=("tip_amount", "sum"),
                total_revenue=("total_amount", "sum"),
                sum_distance=("trip_distance", "sum"))
    out["avg_fare"] = out.total_fare / out.trips
    out["avg_distance"] = out.sum_distance / out.trips
    return out

def run_full(paths):
    t0 = time.time()
    frames = [pd.read_csv(p, header=None, names=NAMES, usecols=COLS) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    n = len(df)
    res = aggregate(df)
    return time.time() - t0, n, res

def run_chunked(paths, chunk=500_000):
    t0 = time.time()
    parts, n = [], 0
    for p in paths:
        for ch in pd.read_csv(p, header=None, names=NAMES, usecols=COLS, chunksize=chunk):
            n += len(ch)
            g = ch.groupby("PULocationID").agg(
                trips=("fare_amount", "size"), total_fare=("fare_amount", "sum"),
                total_tips=("tip_amount", "sum"), total_revenue=("total_amount", "sum"),
                sum_distance=("trip_distance", "sum"))
            parts.append(g)
    comb = pd.concat(parts).groupby(level=0).sum()
    comb["avg_fare"] = comb.total_fare / comb.trips
    comb["avg_distance"] = comb.sum_distance / comb.trips
    return time.time() - t0, n, comb

if __name__ == "__main__":
    paths = sorted(glob.glob(sys.argv[1])) if len(sys.argv) > 1 else sorted(glob.glob("local_cleaned/part-*"))
    mode = sys.argv[2] if len(sys.argv) > 2 else "both"
    print("input files:", len(paths))
    if mode in ("both", "chunked"):
        t, n, res = run_chunked(paths)
        print("CHUNKED  seconds=%.2f  records=%d  groups=%d  peak_rss_mb=%.1f" % (t, n, len(res), peak_mb()))
        res.sort_values("total_revenue", ascending=False).head(10).to_csv("output/pandas_top10_revenue.csv")
    if mode in ("both", "full"):
        t, n, res = run_full(paths)
        print("FULL     seconds=%.2f  records=%d  groups=%d  peak_rss_mb=%.1f" % (t, n, len(res), peak_mb()))
        res.to_csv("output/pandas_revenue_by_zone.csv")
