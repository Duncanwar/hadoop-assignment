#!/usr/bin/env python3
"""
reducer_payment.py -- Analysis (e) reducer: behaviour per payment type.

INPUT   "<code>_<label>\tcount,fare,tip,total,distance,tipped_trips"
OUTPUT  trips, total_revenue, avg_fare, avg_tip, avg_total, avg_distance,
        tip_rate_pct (tip as % of fare) and pct_trips_tipped.

INTERPRETATION NOTE that belongs with the number, not after it: the meter only
records a tip when it is charged to the card.  A cash tip is invisible, so the
"Cash" row's average tip is a measurement artefact (structurally ~0), not
evidence that cash customers do not tip.
"""
import sys

def emit(key, a):
    n = a[0]
    if n <= 0:
        return
    fare, tip, total, dist, tipped = a[1], a[2], a[3], a[4], a[5]
    rate = (tip / fare * 100.0) if fare > 0 else 0.0
    sys.stdout.write("%s\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n" %
                     (key, int(n), total, fare / n, tip / n, total / n,
                      dist / n, rate, tipped / n * 100.0))

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
