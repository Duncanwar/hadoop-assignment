#!/usr/bin/env python3
"""
mapper_route.py -- Analysis (g): busiest pickup -> drop-off routes.

KEY-VALUE DESIGN
    output key   = "PULocationID->DOLocationID"  (a COMPOSITE key)
    output value = "count,total_revenue,distance,duration_minutes"
The composite key is the whole point of this analysis: Shuffle-and-Sort groups
every trip that shares an origin/destination pair onto one reducer, which is
exactly the grouping a SQL "GROUP BY pu, do" would produce - but computed in
parallel across the cluster with no shared state.
Cardinality is bounded by 265 x 265 = 70,225 keys, small enough for one reducer
to rank, yet large enough that a combiner materially reduces shuffle bytes.
"""
import sys, csv
from datetime import datetime

PU_DT, DO_DT = 1, 2
PAX, DIST = 3, 4
PU_LOC, DO_LOC = 7, 8
PAY, FARE, TIP, TOLLS, TOTAL = 9, 10, 13, 14, 16

def records():
    """Yield parsed rows from the CLEANED csv on stdin.

    The cleaned dataset has already passed mapper_clean.py, so this parser
    only has to guard against a split boundary landing mid-record."""
    for row in csv.reader(sys.stdin):
        if len(row) != 20 or row[0] == "VendorID":
            continue
        try:
            pu = datetime.strptime(row[PU_DT], "%Y-%m-%d %H:%M:%S")
            do = datetime.strptime(row[DO_DT], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        yield row, pu, do

def main():
    for row, pu, do in records():
        try:
            mins = (do - pu).total_seconds() / 60.0
            sys.stdout.write("%03d->%03d\t1,%.2f,%.2f,%.2f\n" % (
                int(row[PU_LOC]), int(row[DO_LOC]),
                float(row[TOTAL]), float(row[DIST]), mins))
        except (ValueError, IndexError):
            continue

if __name__ == "__main__":
    main()
