#!/usr/bin/env python3
"""
mapper_duration.py -- Analysis (h): trip-duration profile.

KEY-VALUE DESIGN
    output key   = "<n>_<band>"  e.g. "4_20-30min"
    output value = "count,fare,total,distance,tip,duration_minutes"
Duration is a DERIVED field: it does not exist in the source feed and is
computed as drop-off minus pickup inside the mapper, where the two timestamps
are already in memory.  Deriving it map-side avoids shipping both timestamps
through the shuffle.
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

def band(m):
    if m <= 5:  return "1_0-5min"
    if m <= 10: return "2_5-10min"
    if m <= 20: return "3_10-20min"
    if m <= 30: return "4_20-30min"
    if m <= 60: return "5_30-60min"
    return "6_60+min"

def main():
    for row, pu, do in records():
        try:
            mins = (do - pu).total_seconds() / 60.0
            sys.stdout.write("%s\t1,%.2f,%.2f,%.2f,%.2f,%.2f\n" % (
                band(mins), float(row[FARE]), float(row[TOTAL]),
                float(row[DIST]), float(row[TIP]), mins))
        except (ValueError, IndexError):
            continue

if __name__ == "__main__":
    main()
