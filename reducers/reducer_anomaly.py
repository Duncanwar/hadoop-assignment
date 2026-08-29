#!/usr/bin/env python3
"""
reducer_anomaly.py -- Analysis (i) reducer: anomaly counts and percentages.

INPUT   "<label>\t1" pairs.  Because "AAA_TOTAL_RECORDS" and
        "AAB_ANOMALOUS_RECORDS" sort before every real label, the reducer has
        already seen the denominator by the time the first anomaly label
        arrives - so each label can be printed with its percentage in a single
        streaming pass, with no second job and no in-memory table.
        This ordering trick only works with ONE reducer, which is why the job
        is submitted with -D mapreduce.job.reduces=1.
OUTPUT  "<label>\t<count>\t<percent_of_all_records>"
"""
import sys

def main():
    total = 0
    cur, n = None, 0

    def emit(k, c):
        pct = (c / total * 100.0) if total else 0.0
        sys.stdout.write("%s\t%d\t%.4f\n" % (k, c, pct))

    for line in sys.stdin:
        try:
            key, val = line.rstrip("\n").split("\t", 1)
            v = int(float(val))
        except ValueError:
            continue
        if key != cur:
            if cur is not None:
                if cur == "AAA_TOTAL_RECORDS":
                    total = n
                emit(cur, n)
            cur, n = key, 0
        n += v
    if cur is not None:
        if cur == "AAA_TOTAL_RECORDS":
            total = n
        emit(cur, n)

if __name__ == "__main__":
    main()
