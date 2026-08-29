#!/usr/bin/env python3
"""
mapper_daily.py -- Analysis (b): demand by day of week.

KEY-VALUE DESIGN
    output key   = "<n>_<DayName>_<WEEKDAY|WEEKEND>"  e.g. "1_Monday_WEEKDAY"
                   The leading ordinal keeps the reducer output in calendar
                   order under Hadoop's lexicographic sort.
    output value = 1
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

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

def main():
    for row, pu, do in records():
        w = pu.weekday()
        kind = "WEEKEND" if w >= 5 else "WEEKDAY"
        sys.stdout.write("%d_%s_%s\t1\n" % (w + 1, DAYS[w], kind))

if __name__ == "__main__":
    main()
