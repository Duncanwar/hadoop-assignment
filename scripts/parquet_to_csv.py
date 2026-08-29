#!/usr/bin/env python3
"""
parquet_to_csv.py
-----------------
Converts the NYC TLC monthly Yellow-Taxi Parquet files into line-oriented CSV
so they can be consumed by Hadoop Streaming (which is a line-based framework).

Why Parquet for storage / CSV for streaming
  * Parquet is columnar + compressed: ~64 MB holds 3.7 M rows and a scan of a
    single column touches only that column's pages. Ideal for archival storage.
  * Parquet is NOT line oriented, so a Hadoop Streaming mapper (which receives
    one text line on stdin) cannot read it directly without a custom InputFormat.
    CSV is therefore produced as the "streaming-friendly" representation.

Usage:  python3 parquet_to_csv.py <in.parquet> <out.csv>
"""
import sys, csv, pyarrow.parquet as pq

COLS = ["VendorID","tpep_pickup_datetime","tpep_dropoff_datetime","passenger_count",
        "trip_distance","RatecodeID","store_and_fwd_flag","PULocationID","DOLocationID",
        "payment_type","fare_amount","extra","mta_tax","tip_amount","tolls_amount",
        "improvement_surcharge","total_amount","congestion_surcharge","Airport_fee",
        "cbd_congestion_fee"]

def main(src, dst):
    pf = pq.ParquetFile(src)
    n = 0
    with open(dst, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(COLS)                       # header (mappers skip it)
        for batch in pf.iter_batches(batch_size=200_000, columns=COLS):
            d = batch.to_pydict()
            cols = [d[c] for c in COLS]
            for row in zip(*cols):
                out = []
                for v in row:
                    if v is None:
                        out.append("")
                    elif hasattr(v, "strftime"):
                        out.append(v.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        out.append(v)
                w.writerow(out)
                n += 1
    print(f"{src} -> {dst}: {n:,} rows")
    return n

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
