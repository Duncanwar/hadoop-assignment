#!/usr/bin/env python3
"""
combiner_sums.py -- a single generic COMBINER shared by every vector analysis.

WHY A COMBINER
    A combiner is a reducer that Hadoop may run on the MAP side, on the output
    of one map task, before the shuffle.  It is only legal when the aggregation
    is commutative and associative and when its output has the SAME shape as
    its input.  Element-wise addition of a fixed-length numeric vector satisfies
    both conditions, so this one script serves mapper_revenue, mapper_payment,
    mapper_distance, mapper_duration and mapper_route.

    It is precisely because averages are NOT associative that the mappers emit
    (count, sum, sum, ...) instead of a mean: the mean is reconstructed only at
    the very end, in the reducer.

    Effect on this dataset: mapper_route emits ~11 M pairs; after combining,
    each map task ships at most ~70 k - typically a 30x-100x cut in shuffle
    bytes, which on a single-node cluster is the difference between a job that
    spills to disk repeatedly and one that does not.
"""
import sys

def flush(key, acc):
    if key is not None:
        sys.stdout.write(key + "\t" + ",".join("%.2f" % v for v in acc) + "\n")

def main():
    cur, acc = None, None
    for line in sys.stdin:
        try:
            key, val = line.rstrip("\n").split("\t", 1)
            vals = [float(x) for x in val.split(",")]
        except ValueError:
            continue
        if key != cur:
            flush(cur, acc)
            cur, acc = key, vals
        else:
            if len(vals) != len(acc):
                continue
            acc = [a + b for a, b in zip(acc, vals)]
    flush(cur, acc)

if __name__ == "__main__":
    main()
