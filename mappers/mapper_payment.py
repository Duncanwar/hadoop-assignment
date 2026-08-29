#!/usr/bin/env python3
"""
mapper_payment.py -- Analysis (e): behaviour by payment type.

KEY-VALUE DESIGN
    output key   = "<code>_<label>"   e.g. "1_CreditCard"
    output value = "count,fare,tip,total,distance,tipped_trips"
"tipped_trips" counts trips with tip > 0 so the reducer can report both the
mean tip and the share of trips that tipped at all - cash tips are not recorded
by the meter, which is the single most important caveat in this analysis.
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

LABEL = {0:"FlexFare", 1:"CreditCard", 2:"Cash", 3:"NoCharge",
         4:"Dispute", 5:"Unknown", 6:"Voided"}

def main():
    for row, pu, do in records():
        try:
            p = int(float(row[PAY]))
            tip = float(row[TIP])
            sys.stdout.write("%d_%s\t1,%.2f,%.2f,%.2f,%.2f,%d\n" % (
                p, LABEL.get(p, "Other"), float(row[FARE]), tip,
                float(row[TOTAL]), float(row[DIST]), 1 if tip > 0 else 0))
        except (ValueError, IndexError):
            continue

if __name__ == "__main__":
    main()
