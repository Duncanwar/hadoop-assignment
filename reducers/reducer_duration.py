#!/usr/bin/env python3
"""
reducer_duration.py -- Analysis (h) reducer: statistics per trip-duration band.

INPUT   "<n>_<band>\tcount,fare,total,distance,tip,duration_minutes"
OUTPUT  trips, total_revenue, avg_fare, avg_total, avg_distance, avg_tip,
        avg_duration_min, fare_per_mile, avg_speed_mph
fare_per_mile and avg_speed are RATIOS OF SUMS, not means of ratios: computing
them from the aggregate protects the figure from being dominated by a handful
of 0.01-mile trips whose individual ratio explodes.
"""
import sys

def emit(key, a):
    n = a[0]
    if n <= 0:
        return
    fare, total, dist, tip, mins = a[1], a[2], a[3], a[4], a[5]
    fpm = fare / dist if dist > 0 else 0.0
    mph = dist / (mins / 60.0) if mins > 0 else 0.0
    sys.stdout.write("%s\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n" %
                     (key, int(n), total, fare / n, total / n, dist / n,
                      tip / n, mins / n, fpm, mph))

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
