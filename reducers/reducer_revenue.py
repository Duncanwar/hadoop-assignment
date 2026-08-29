#!/usr/bin/env python3
"""
reducer_revenue.py -- Analysis (d) reducer: revenue profile per pickup zone.
Stage 1 output of the compulsory two-stage workflow.

INPUT   "<PULocationID>\tcount,fare,tip,tolls,total,distance"  (possibly
        pre-aggregated by combiner_sums.py)
OUTPUT  "<PULocationID>\ttrips  total_fare  total_tips  total_revenue
                         avg_fare  avg_tip  avg_distance  revenue_per_mile"
The averages are computed HERE, once, from the summed count and summed totals -
the reason the mapper had to emit sums rather than means.
"""
import sys

HDR = "#zone\ttrips\ttotal_fare\ttotal_tips\ttotal_revenue\tavg_fare\tavg_tip\tavg_distance\trevenue_per_mile"

def emit(key, a):
    n = a[0]
    if n <= 0:
        return
    fare, tip, tolls, total, dist = a[1], a[2], a[3], a[4], a[5]
    rpm = total / dist if dist > 0 else 0.0
    sys.stdout.write("%s\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n" %
                     (key, int(n), fare, tip, total, fare / n, tip / n, dist / n, rpm))

def main():
    cur, acc = None, None
    for line in sys.stdin:
        try:
            key, val = line.rstrip("\n").split("\t", 1)
            vals = [float(x) for x in val.split(",")]
        except ValueError:
            continue
        if key != cur:
            if cur is not None:
                emit(cur, acc)
            cur, acc = key, vals
        else:
            acc = [x + y for x, y in zip(acc, vals)]
    if cur is not None:
        emit(cur, acc)

if __name__ == "__main__":
    main()
