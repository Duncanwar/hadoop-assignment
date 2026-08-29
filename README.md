# Hadoop Assignment
#ID 101413
Big Data Essentials — Individual Practical Case Study
NYC TLC Yellow Taxi trip records, January–March 2026.

---

## 1. Environment assumptions

| Component | Version|
|---|---|
| Apache Hadoop | 3.5.0 (binary distribution) |
| Java | OpenJDK 21 (`JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64`) |
| Python | 3.11 — used for every mapper, reducer and combiner via Hadoop Streaming |
| Cluster mode | pseudo-distributed, single node (NameNode + DataNode + SecondaryNameNode + ResourceManager + NodeManager + JobHistoryServer) |
| Host | 2 vCPU, 8 GB RAM, Linux x86-64 |
| HDFS replication | 1 (single DataNode) |
| HDFS block size | 128 MB |
| Python libraries | `pyarrow` and `pandas` for the Parquet→CSV conversion and the benchmark only. **No mapper or reducer imports a third-party library** — they use only the standard library, so they run unchanged on any cluster node. |

---

## 2. Project layout

```
taxi_project/
├── README.md                  
├── commands.txt               
├── data/                      
├── mappers/                   
│   ├── mapper_clean.py            
│   ├── mapper_hourly.py           
│   ├── mapper_daily.py            
│   ├── mapper_location.py         
│   ├── mapper_revenue.py          
│   ├── mapper_payment.py         
│   ├── mapper_distance.py         
│   ├── mapper_route.py            
│   ├── mapper_duration.py        
│   ├── mapper_anomaly.py         
│   └── mapper_topn.py             
├── reducers/                  
│   ├── reducer_clean.py          
│   ├── combiner_sums.py           
│   ├── reducer_hourly.py          
│   ├── reducer_daily.py
│   ├── reducer_location.py
│   ├── reducer_revenue.py
│   ├── reducer_payment.py
│   ├── reducer_distance.py
│   ├── reducer_route.py
│   ├── reducer_duration.py
│   ├── reducer_anomaly.py
│   └── reducer_topn.py            
├── scripts/                  
│   ├── parquet_to_csv.py          
│   ├── run_all_jobs.sh            
│   ├── fetch_results.sh           
│   ├── pandas_benchmark.py        
│   ├── make_charts.py            
│   └── zones.py                   
├── output/                    
├── charts/                    
├── evidence/                  
└── docs/                      
```

---

## 3. How to reproduce

```bash
# 0. environment
source hadoop_env.sh             

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
bash -c 'sed -n "/^# 3\./,/^# 5\./p" commands.txt'  
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

## 5. Deliverables

| File | Contents |
|---|---|
| `docs/Big_Data_Hadoop_Taxi_Analytics_Report.docx` | the final report |
| `commands.txt` | every command needed to reproduce the work |
| `mappers/`, `reducers/` | all Python MapReduce programs |
| `evidence/` | job logs, counter dumps, HDFS and YARN evidence |
| `charts/` | the seven required figures |
| `output/` | the raw reducer output behind every figure and table |

---


Run it with:

```bash
hdfs dfs -get /taxi_project/input/cleaned local_cleaned
python3 scripts/verify_results.py
```
# hadoop-assignment
