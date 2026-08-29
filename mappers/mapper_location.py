#!/usr/bin/env python3
"""
mapper_location.py -- Analysis (c): trips per pickup zone.

KEY-VALUE DESIGN
    output key   = PULocationID (zero padded to 3 chars for stable sorting)
    output value = 1
The Top-10 / Bottom-10 ranking is deliberately NOT done here: a mapper sees
only its own input split and cannot know the global ranking.  Ranking is done
after the reduce phase (see the two-stage job for the MapReduce version).
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
        sys.stdout.write("%03d\t1\n" % int(row[PU_LOC]))

if __name__ == "__main__":
    main()
