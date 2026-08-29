# Distributed Taxi Trip Analytics — Apache Hadoop, HDFS and Python MapReduce

Big Data Essentials — Individual Practical Case Study
NYC TLC Yellow Taxi trip records, January–March 2026.

**11,077,209 raw trip records / 1.1 GB of CSV, processed on a live single-node
pseudo-distributed Apache Hadoop 3.5.0 cluster.** Every number in the report is
the output of a MapReduce job that actually ran; every job log, counter dump and
YARN application record is in `evidence/`.

---

## 1. Environment assumptions

| Component | Version / setting |
|---|---|
| Apache Hadoop | 3.5.0 (binary distribution) |
| Java | OpenJDK 21 (`JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64`) |
| Python | 3.11 — used for every mapper, reducer and combiner via Hadoop Streaming |
| Cluster mode | pseudo-distributed, single node (NameNode + DataNode + SecondaryNameNode + ResourceManager + NodeManager + JobHistoryServer) |
| Host | 2 vCPU, 8 GB RAM, Linux x86-64 |
| HDFS replication | 1 (single DataNode) |
| HDFS block size | 128 MB |
| Python libraries | `pyarrow` and `pandas` for the Parquet→CSV conversion and the benchmark only. **No mapper or reducer imports a third-party library** — they use only the standard library, so they run unchanged on any cluster node. |

Two deviations from a textbook install, both documented rather than hidden:

1. **The daemons are started individually** (`hdfs --daemon start namenode`, …)
   instead of with `start-dfs.sh` / `start-yarn.sh`, because the container has
   no `sshd` and those scripts drive the daemons over SSH. The running cluster
   is identical; only the launch mechanism differs.
2. **`yarn.nodemanager.disk-health-checker.max-disk-utilization-per-disk-percentage`
   is raised to 99.** The host presents a 252 GB device of which ~26 GB is
   writable, so YARN's default 90 % check reads the node as full and flaps it
   to `UNHEALTHY` mid-job. An absolute floor
   (`min-free-space-per-disk-mb=2048`) is set instead. This is a property of
   the sandbox, not of Hadoop.

Hadoop's native libraries are not present, so every job logs
`WARN util.NativeCodeLoader: Unable to load native-hadoop library`. That is a
performance note (Java implementations of CRC and compression are used), not an
error.

---

## 2. Project layout

```
taxi_project/
├── README.md                  this file
├── commands.txt               every HDFS and Hadoop Streaming command, in order
├── data/                      source Parquet + the TLC zone lookup table
├── mappers/                   11 mapper programs
│   ├── mapper_clean.py            validation + duplicate key emission
│   ├── mapper_hourly.py           (a) hourly demand
│   ├── mapper_daily.py            (b) day-of-week demand
│   ├── mapper_location.py         (c) pickup-zone trip counts
│   ├── mapper_revenue.py          (d) revenue by pickup zone  [STAGE 1]
│   ├── mapper_payment.py          (e) payment-method behaviour
│   ├── mapper_distance.py         (f) distance bands
│   ├── mapper_route.py            (g) pickup→drop-off routes
│   ├── mapper_duration.py         (h) trip-duration bands
│   ├── mapper_anomaly.py          (i) anomaly detection (runs on the RAW feed)
│   └── mapper_topn.py             generic Top-N mapper  [STAGE 2]
├── reducers/                  11 reducer/combiner programs
│   ├── reducer_clean.py           deduplication
│   ├── combiner_sums.py           ONE generic combiner shared by five analyses
│   ├── reducer_hourly.py          also used as its own combiner
│   ├── reducer_daily.py
│   ├── reducer_location.py
│   ├── reducer_revenue.py
│   ├── reducer_payment.py
│   ├── reducer_distance.py
│   ├── reducer_route.py
│   ├── reducer_duration.py
│   ├── reducer_anomaly.py
│   └── reducer_topn.py            global Top-N  [STAGE 2]
├── scripts/                   orchestration and non-MapReduce helpers
│   ├── parquet_to_csv.py          Parquet → line-oriented CSV
│   ├── run_all_jobs.sh            submits all 15 jobs in order
│   ├── fetch_results.sh           pulls every result out of HDFS
│   ├── pandas_benchmark.py        the single-machine comparison
│   ├── make_charts.py             the seven required figures
│   └── zones.py                   LocationID → zone name
├── output/                    reducer output pulled out of HDFS (*.tsv)
├── charts/                    the seven required figures (PNG)
├── evidence/                  job logs, counters, HDFS and YARN evidence
└── docs/                      the final report
```

---

## 3. How to reproduce

```bash
# 0. environment
source hadoop_env.sh              # or paste section 0 of commands.txt

# 1. start the cluster and confirm six JVMs
hdfs --daemon start namenode  &&  hdfs --daemon start datanode
hdfs --daemon start secondarynamenode
yarn --daemon start resourcemanager && yarn --daemon start nodemanager
mapred --daemon start historyserver
jps

# 2. convert Parquet to CSV
for m in 01 02 03; do
  python3 scripts/parquet_to_csv.py data/yellow_tripdata_2026-$m.parquet \
                                    data/yellow_tripdata_2026-$m.csv
done

# 3. create the HDFS tree and load the data
bash -c 'sed -n "/^# 3\./,/^# 5\./p" commands.txt'   # or run the commands directly
hdfs dfs -mkdir -p /taxi_project/input/raw
hdfs dfs -put data/yellow_tripdata_2026-*.csv /taxi_project/input/raw/

# 4. run every job (cleaning, the nine analyses, the five Top-N stage-2 jobs)
./scripts/run_all_jobs.sh

# 5. collect results, build the charts, run the benchmark
./scripts/fetch_results.sh
python3 scripts/make_charts.py
hdfs dfs -get /taxi_project/input/cleaned local_cleaned
python3 scripts/pandas_benchmark.py 'local_cleaned/part-*' both
```

`run_all_jobs.sh` writes one log per job to `evidence/` and a one-line summary
per job (return code, elapsed seconds, YARN application id) to
`evidence/JOBS_STATUS.txt`.

---

## 4. The design ideas worth knowing before reading the code

**The key is the algorithm.** In MapReduce you do not choose a `GROUP BY`
clause; you choose what the mapper emits as its key, and the Shuffle-and-Sort
stage does the grouping for you, in parallel, with no shared state. Every
analysis here is a different answer to "what should the key be":

| Analysis | Key | Why |
|---|---|---|
| hourly | `"14"` (zero-padded hour) | 24 keys — padding matters because Hadoop sorts keys as **text**, so `"9"` would sort after `"23"` |
| daily | `"3_Wednesday_WEEKDAY"` | an ordinal prefix forces calendar order out of a lexicographic sort |
| routes | `"132->230"` | a **composite key** — this is the whole analysis; it is a two-column `GROUP BY` expressed as string concatenation |
| cleaning | *the entire record* | identical records collide in the shuffle → distributed `DISTINCT` |
| Top-N | the constant `"TOPN"` | deliberately forces one reducer, the only place a **global** ordering can exist |
| anomalies | the label, with `AAA_`/`AAB_` prefixes on the two totals | the totals sort first, so percentages can be printed in one streaming pass |

**Averages are not associative — so no mapper emits one.** Mappers emit
`(count, sum, sum, …)` vectors and the reducer divides at the very end. That is
what makes a single generic combiner (`combiner_sums.py`) legal for five
different analyses: element-wise addition is commutative and associative and
its output has the same shape as its input, which are exactly the two
conditions a combiner must satisfy.

**Reducers stream; they do not accumulate.** Values for one key arrive as one
contiguous run, so each reducer holds one key's accumulator and nothing more.
The only exception is `reducer_topn.py`, which holds at most *M × N* candidate
rows by design.

---

## 5. A note on the data cleaning

The first cleaning run rejected 2,823,332 records — 25.5 % of the feed —
because `passenger_count` was blank or zero. That rule was **wrong** and was
changed. `passenger_count` is a driver-entered field that a quarter of the 2026
feed leaves empty, and it is not an input to any of the nine required analyses;
deleting a quarter of the trips to enforce it would have biased every demand,
revenue and route figure in the report. Those records are now flagged
(`PASSENGER_FLAGGED`) and kept, with the field normalised to an explicit
"unknown". Records are only rejected when the defect makes them unusable for
the analysis at hand — a non-positive distance, a non-positive duration, a
negative fare. Section 6 of the report gives the full rule set with counts and
percentages.

---

## 6. Deliverables

| File | Contents |
|---|---|
| `docs/Big_Data_Hadoop_Taxi_Analytics_Report.docx` | the final report |
| `commands.txt` | every command needed to reproduce the work |
| `mappers/`, `reducers/` | all Python MapReduce programs |
| `evidence/` | job logs, counter dumps, HDFS and YARN evidence |
| `charts/` | the seven required figures |
| `output/` | the raw reducer output behind every figure and table |

---

## 7. Verification

`scripts/verify_results.py` re-computes every aggregate independently with Pandas,
directly from the cleaned dataset, and compares it against the reducer output. It
shares no code with any mapper or reducer. All checks pass — see
`evidence/E7_verification.txt` and Section 9.10 of the report:

```
total cleaned records ........ 10,493,916  (mapreduce == pandas)
all 24 hourly counts ......... exact match
all 7 day-of-week counts ..... exact match
total revenue ................ $316,116,721.15  (mapreduce == pandas, to the cent)
distinct pickup zones ........ 262
distinct routes .............. 47,937
top-10 rankings .............. same zones, same order as pandas nlargest
five independent partitions .. each sums to exactly 10,493,916
```

Run it with:

```bash
hdfs dfs -get /taxi_project/input/cleaned local_cleaned
python3 scripts/verify_results.py
```
# hadoop-assignment
