#!/usr/bin/env python3
"""
reducer_clean.py  --  Stage 2 of the data-cleaning MapReduce job.

Shuffle-and-Sort has grouped byte-identical records together.  For each
distinct record the reducer writes it out exactly ONCE, and counts every
extra copy as a duplicate.  Output is written as plain CSV (the trailing
"\t1" value is dropped) so downstream jobs read a normal CSV line.
"""
import sys

def cnt(name, n=1):
    sys.stderr.write("reporter:counter:CLEANING,%s,%d\n" % (name, n))

def main():
    current = None
    copies = 0
    for line in sys.stdin:
        key = line.rstrip("\n").split("\t", 1)[0]
        if key != current:
            if current is not None:
                sys.stdout.write(current + "\n")
                cnt("DISTINCT_RECORDS")
                if copies > 1:
                    cnt("DUPLICATE_RECORDS", copies - 1)
            current, copies = key, 0
        copies += 1
    if current is not None:
        sys.stdout.write(current + "\n")
        cnt("DISTINCT_RECORDS")
        if copies > 1:
            cnt("DUPLICATE_RECORDS", copies - 1)

if __name__ == "__main__":
    main()
