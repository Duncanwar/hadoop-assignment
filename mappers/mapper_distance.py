#!/usr/bin/env python3
"""
mapper_distance.py -- Analysis (f): fare behaviour by distance band.

KEY-VALUE DESIGN
    output key   = "<n>_<band>"  e.g. "3_5-10mi"   (ordinal prefix = sort order)
    output value = "count,fare,total,distance,tip,duration_minutes"
Binning in the MAPPER rather than the reducer is deliberate: it turns a
high-cardinality continuous variable into 5 keys, so the shuffle moves almost
nothing and a combiner reduces each map task's output to 5 lines.
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

def band(d):
    if d <= 2:  return "1_0-2mi"
    if d <= 5:  return "2_2-5mi"
    if d <= 10: return "3_5-10mi"
    if d <= 20: return "4_10-20mi"
    return "5_20+mi"

def main():
    for row, pu, do in records():
        try:
            d = float(row[DIST])
            mins = (do - pu).total_seconds() / 60.0
            sys.stdout.write("%s\t1,%.2f,%.2f,%.2f,%.2f,%.2f\n" % (
                band(d), float(row[FARE]), float(row[TOTAL]), d,
                float(row[TIP]), mins))
        except (ValueError, IndexError):
            continue

if __name__ == "__main__":
    main()
