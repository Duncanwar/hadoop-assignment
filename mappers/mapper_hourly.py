#!/usr/bin/env python3
"""
mapper_hourly.py -- Analysis (a): hourly taxi demand.

KEY-VALUE DESIGN
    output key   = pickup hour of day, zero padded "00".."23"
    output value = 1
Zero padding matters: Hadoop sorts keys as TEXT, so "9" would sort after "23".
The reducer is a pure sum, therefore it can also be used as a COMBINER, which
collapses ~11 million map outputs down to at most 24 pairs per map task.
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
        sys.stdout.write("%02d\t1\n" % pu.hour)

if __name__ == "__main__":
    main()
