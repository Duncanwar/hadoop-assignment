#!/usr/bin/env python3
"""
mapper_anomaly.py -- Analysis (i): anomaly detection.

This mapper runs over the RAW dataset (not the cleaned one) so that it can
measure how much of the original feed is suspicious.

KEY-VALUE DESIGN
    output key   = anomaly label, e.g. "ZERO_DISTANCE"
    output value = 1
    A record can trigger several labels, so it may emit several pairs; two
    bookkeeping keys, "AAA_TOTAL_RECORDS" and "AAB_ANOMALOUS_RECORDS", let the
    reducer express every count as a percentage without a second pass.
    ("AAA"/"AAB" prefixes simply force those two keys to sort first.)

DETECTORS
    ZERO_DISTANCE        trip_distance <= 0
    EXTREME_DISTANCE     trip_distance > 200 miles
    ZERO_PASSENGER       passenger_count missing or 0
    EXTREME_PASSENGER    passenger_count > 8
    NEGATIVE_FARE        fare_amount < 0
    EXTREME_FARE         fare_amount > 1000
    NEGATIVE_TOTAL       total_amount < 0
    ZERO_DURATION        drop-off <= pickup
    EXTREME_DURATION     duration > 12 h
    EXTREME_FARE_PER_MI  fare/mile > 100 USD  (meter fault or 0.01-mile trips)
    IMPOSSIBLE_SPEED     average speed > 100 mph
    TIP_EXCEEDS_FARE     tip > 5 x fare
    BAD_LOCATION_ID      location id outside 1..265
    OUT_OF_WINDOW_DATE   timestamp outside the 2026-Q1 study window
"""
import sys, csv
from datetime import datetime

LO = datetime(2026, 1, 1); HI = datetime(2026, 4, 2)

def main():
    for row in csv.reader(sys.stdin):
        if len(row) != 20 or row[0] == "VendorID":
            continue
        sys.stdout.write("AAA_TOTAL_RECORDS\t1\n")
        flags = []
        try:
            dist = float(row[4] or 0)
        except ValueError:
            dist = 0.0
        try:
            fare = float(row[10] or 0)
        except ValueError:
            fare = 0.0
        try:
            total = float(row[16] or 0)
        except ValueError:
            total = 0.0
        try:
            tip = float(row[13] or 0)
        except ValueError:
            tip = 0.0
        try:
            pax = int(float(row[3])) if row[3] != "" else 0
        except ValueError:
            pax = 0

        if dist <= 0:    flags.append("ZERO_DISTANCE")
        if dist > 200:   flags.append("EXTREME_DISTANCE")
        if pax <= 0:     flags.append("ZERO_PASSENGER")
        if pax > 8:      flags.append("EXTREME_PASSENGER")
        if fare < 0:     flags.append("NEGATIVE_FARE")
        if fare > 1000:  flags.append("EXTREME_FARE")
        if total < 0:    flags.append("NEGATIVE_TOTAL")
        if tip > 5 * abs(fare) and tip > 0: flags.append("TIP_EXCEEDS_FARE")

        try:
            p = int(row[7]); d = int(row[8])
            if not (1 <= p <= 265) or not (1 <= d <= 265):
                flags.append("BAD_LOCATION_ID")
        except ValueError:
            flags.append("BAD_LOCATION_ID")

        try:
            pu = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            do = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
            if not (LO <= pu < HI) or not (LO <= do < HI):
                flags.append("OUT_OF_WINDOW_DATE")
            secs = (do - pu).total_seconds()
            if secs <= 0:
                flags.append("ZERO_DURATION")
            elif secs > 43200:
                flags.append("EXTREME_DURATION")
            elif dist > 0 and (dist / (secs / 3600.0)) > 100:
                flags.append("IMPOSSIBLE_SPEED")
        except Exception:
            flags.append("BAD_TIMESTAMP")

        if dist > 0 and fare / dist > 100:
            flags.append("EXTREME_FARE_PER_MI")

        if flags:
            sys.stdout.write("AAB_ANOMALOUS_RECORDS\t1\n")
            for f in flags:
                sys.stdout.write(f + "\t1\n")

if __name__ == "__main__":
    main()
