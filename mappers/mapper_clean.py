#!/usr/bin/env python3
"""
mapper_clean.py  --  Stage 1 of the data-cleaning MapReduce job.

KEY-VALUE DESIGN
    input  : one raw CSV line of the TLC yellow-taxi feed (20 fields)
    output : key   = the *entire* validated CSV record
             value = "1"
    Emitting the whole record as the KEY is what allows the Shuffle-and-Sort
    stage to bring byte-identical records together, so reducer_clean.py can
    collapse duplicates.  This is the classic MapReduce "distributed DISTINCT".

VALIDATION RULES (and why each one exists)
    Records are *not* silently thrown away: every rejection increments a named
    Hadoop counter (reporter:counter:...) so the exact number and percentage of
    each defect is recoverable from the job report.

    MALFORMED          wrong number of fields / unparsable CSV
    HEADER             the CSV header line (present once per input file)
    BAD_TIMESTAMP      pickup or drop-off timestamp cannot be parsed
    OUT_OF_WINDOW      timestamp outside the 2026-01-01 .. 2026-04-01 study window
                       (the TLC feed contains a handful of 2001/2098 typos)
    NONPOS_DURATION    drop-off <= pickup  (impossible)
    LONG_DURATION      duration > 24 h     (meter left running / data error)
    NONPOS_DISTANCE    trip_distance <= 0  (meter never engaged)
    LONG_DISTANCE      trip_distance > 200 miles (beyond any NYC taxi trip)
    PASSENGER_FLAGGED  passenger_count missing, <=0 or > 8.  These records are
                       KEPT, not deleted: passenger_count is a driver-entered
                       field that ~25% of the 2026 feed leaves blank or zero,
                       and it is not an input to any of the nine required
                       analyses.  Discarding a quarter of the trips to enforce
                       a field nobody reads would bias every demand, revenue
                       and route figure in this report.  The field is instead
                       normalised to empty (an explicit "unknown") and counted.
    NEG_FARE           fare_amount < 0 or total_amount < 0 (refund/void rows)
    HIGH_FARE          fare_amount > 1000 USD
    BAD_LOCATION       PULocationID / DOLocationID outside 1..265
    BAD_PAYMENT        payment_type outside 0..6
"""
import sys, csv
from datetime import datetime

LO = datetime(2026, 1, 1)
HI = datetime(2026, 4, 2)

def cnt(name, n=1):
    sys.stderr.write("reporter:counter:CLEANING,%s,%d\n" % (name, n))

def main():
    rdr = csv.reader(sys.stdin)
    for row in rdr:
        cnt("INPUT_RECORDS")
        if len(row) != 20:
            cnt("MALFORMED"); continue
        if row[0] == "VendorID":
            cnt("HEADER"); continue
        try:
            pu = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            do = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
        except Exception:
            cnt("BAD_TIMESTAMP"); continue
        if not (LO <= pu < HI) or not (LO <= do < HI):
            cnt("OUT_OF_WINDOW"); continue
        dur = (do - pu).total_seconds()
        if dur <= 0:
            cnt("NONPOS_DURATION"); continue
        if dur > 86400:
            cnt("LONG_DURATION"); continue
        try:
            dist = float(row[4])
        except Exception:
            cnt("NONPOS_DISTANCE"); continue
        if dist <= 0:
            cnt("NONPOS_DISTANCE"); continue
        if dist > 200:
            cnt("LONG_DISTANCE"); continue
        # passenger_count: FLAG-AND-KEEP rather than reject (see docstring)
        try:
            pax = int(float(row[3])) if row[3] != "" else -1
        except Exception:
            pax = -1
        if pax <= 0 or pax > 8:
            cnt("PASSENGER_FLAGGED")
            row[3] = ""          # normalise to an explicit "unknown"
        else:
            row[3] = str(pax)
        try:
            fare = float(row[10]); total = float(row[16])
        except Exception:
            cnt("NEG_FARE"); continue
        if fare < 0 or total < 0:
            cnt("NEG_FARE"); continue
        if fare > 1000:
            cnt("HIGH_FARE"); continue
        try:
            pul = int(row[7]); dol = int(row[8])
        except Exception:
            cnt("BAD_LOCATION"); continue
        if not (1 <= pul <= 265) or not (1 <= dol <= 265):
            cnt("BAD_LOCATION"); continue
        try:
            pay = int(float(row[9]))
        except Exception:
            cnt("BAD_PAYMENT"); continue
        if pay < 0 or pay > 6:
            cnt("BAD_PAYMENT"); continue

        cnt("VALID_RECORDS")
        # whole record becomes the shuffle key -> duplicates collide
        sys.stdout.write(",".join(row) + "\t1\n")

if __name__ == "__main__":
    main()
