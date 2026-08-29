#!/usr/bin/env python3
"""
reducer_topn.py -- STAGE 2 reducer of the multi-stage MapReduce workflow.

Every candidate arrives under the single key "TOPN", so this reducer is the one
place in the pipeline that sees a global ordering.  It re-ranks the M x N
candidates shipped by the mappers and writes the final Top-N.

The job MUST be submitted with -D mapreduce.job.reduces=1: with two reducers
there would be two partial rankings and no global answer.  This is the standard
trade-off of the Top-N pattern - the final step is deliberately serial, but it
operates on a tiny, already-reduced candidate set.

OUTPUT  "<rank>\t<original stage-1 line>"
"""
import sys, os

N = int(os.environ.get("TOPN", "10"))

def main():
    rows = []
    for line in sys.stdin:
        parts = line.rstrip("\n").split("\t", 2)
        if len(parts) < 3:
            continue
        try:
            v = float(parts[1])
        except ValueError:
            continue
        rows.append((v, parts[2]))
    rows.sort(key=lambda r: -r[0])
    for i, (v, payload) in enumerate(rows[:N], start=1):
        sys.stdout.write("%d\t%s\n" % (i, payload))

if __name__ == "__main__":
    main()
