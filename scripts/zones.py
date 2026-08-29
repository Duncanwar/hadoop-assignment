#!/usr/bin/env python3
"""zones.py -- helper: map TLC LocationID -> "Zone, Borough" for readable output."""
import csv, os
_P = os.path.join(os.path.dirname(__file__), "..", "data", "taxi_zone_lookup.csv")
ZONE = {}
with open(_P) as fh:
    for r in csv.DictReader(fh):
        ZONE[int(r["LocationID"])] = (r["Zone"], r["Borough"])

def name(i):
    z, b = ZONE.get(int(i), ("Unknown", "Unknown"))
    return f"{z} ({b})"

def short(i):
    return ZONE.get(int(i), ("Unknown", "Unknown"))[0]
