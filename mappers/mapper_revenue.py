#!/usr/bin/env python3
"""
mapper_revenue.py -- Analysis (d): revenue by pickup zone. Stage 1 of the
compulsory two-stage workflow.

KEY-VALUE DESIGN
    output key   = PULocationID (3-digit, zero padded)
    output value = "count,fare,tip,tolls,total,distance"
A fixed-width numeric VECTOR is emitted instead of a single number so that one
generic combiner (combiner_sums.py) can pre-aggregate any of these analyses.
Averages are NOT computed in the mapper - an average is not associative, so it
must be derived in the reducer from the summed count and summed totals.
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
            sys.stdout.write("%03d\t1,%.2f,%.2f,%.2f,%.2f,%.2f\n" % (
                int(row[PU_LOC]), float(row[FARE]), float(row[TIP]),
                float(row[TOLLS]), float(row[TOTAL]), float(row[DIST])))
        except (ValueError, IndexError):
            continue

if __name__ == "__main__":
    main()
