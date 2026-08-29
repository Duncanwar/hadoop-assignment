#!/usr/bin/env python3
"""
reducer_daily.py -- Analysis (b) reducer: total trips per day of week.

INPUT   the Shuffle-and-Sort stage delivers every "<day>\t1" pair, sorted by
        key, so all values for one day arrive as one contiguous run.  The
        reducer therefore needs O(1) memory: it just watches for the key to
        change.
OUTPUT  "<n>_<DayName>_<WEEKDAY|WEEKEND>\t<trips>"
This reducer is idempotent on its own output shape, so it is ALSO used as the
combiner (-combiner reducer_daily.py).
"""
import sys

def main():
    cur, total = None, 0
    for line in sys.stdin:
        try:
            key, val = line.rstrip("\n").split("\t", 1)
            v = int(float(val))
        except ValueError:
            continue
        if key != cur:
            if cur is not None:
                sys.stdout.write("%s\t%d\n" % (cur, total))
            cur, total = key, 0
        total += v
    if cur is not None:
        sys.stdout.write("%s\t%d\n" % (cur, total))

if __name__ == "__main__":
    main()
