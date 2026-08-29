#!/usr/bin/env python3
"""
mapper_topn.py -- STAGE 2 mapper of the multi-stage MapReduce workflow.

It does not read the raw trips at all: its input is the HDFS output directory
of a stage-1 job (e.g. /taxi_project/output/revenue/part-*).  That is what
makes this a genuine two-stage pipeline - HDFS is the hand-off medium between
the two jobs.

TOP-N PATTERN
    A naive implementation would emit every stage-1 row to a single reducer and
    sort there.  Instead each mapper keeps its OWN local heap of the best N rows
    it has seen ("in-mapper combining") and emits only those N in close().  With
    M map tasks the single reducer receives M x N rows instead of all of them,
    which is what keeps the final serial step cheap no matter how wide the
    cluster gets.

KEY-VALUE DESIGN
    output key   = the constant "TOPN"   -> forces every candidate onto the one
                   reducer that can see the global ordering
    output value = "<sort_value>\t<original stage-1 line>"

PARAMETERS (passed with -cmdenv)
    SORT_FIELD  0-based index of the numeric column to rank on
    TOPN        how many rows to keep
    ORDER       "desc" (largest first, default) or "asc" (smallest first)
"""
import sys, os, heapq

FIELD = int(os.environ.get("SORT_FIELD", "1"))
N     = int(os.environ.get("TOPN", "10"))
ORDER = os.environ.get("ORDER", "desc").lower()

def main():
    heap = []          # min-heap of (signed_value, line) of size <= N
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) <= FIELD:
            continue
        try:
            v = float(parts[FIELD])
        except ValueError:
            continue
        sort_v = v if ORDER == "desc" else -v
        if len(heap) < N:
            heapq.heappush(heap, (sort_v, line))
        elif sort_v > heap[0][0]:
            heapq.heapreplace(heap, (sort_v, line))
    for sort_v, line in heap:
        sys.stdout.write("TOPN\t%.6f\t%s\n" % (sort_v, line))

if __name__ == "__main__":
    main()
