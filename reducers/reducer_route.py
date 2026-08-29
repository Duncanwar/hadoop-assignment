#!/usr/bin/env python3
"""
reducer_route.py -- Analysis (g) reducer: per-route aggregates.

INPUT   "<PU>-><DO>\tcount,total_revenue,distance,duration_minutes"
OUTPUT  route, trips, total_revenue, avg_revenue, avg_distance, avg_duration
The reducer emits EVERY route (~70 k rows).  Ranking to Top-20 by trips and
Top-20 by revenue is a separate concern, handled after the reduce phase, for
the same reason as analysis (c): no single reducer partition can see the
global ordering unless the job is forced down to one reducer.
"""
import sys

def emit(key, a):
    n = a[0]
    if n <= 0:
        return
    rev, dist, mins = a[1], a[2], a[3]
    sys.stdout.write("%s\t%d\t%.2f\t%.2f\t%.2f\t%.2f\n" %
                     (key, int(n), rev, rev / n, dist / n, mins / n))

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
