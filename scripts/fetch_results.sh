#!/usr/bin/env bash
# fetch_results.sh -- copy every MapReduce result out of HDFS into ./output
source /home/claude/hadoop_env.sh
cd /home/claude/taxi_project
mkdir -p output
for d in hourly daily locations revenue payment distance routes duration anomalies \
         top10_revenue_zones top10_zones_trips bottom10_zones_trips \
         top20_routes_trips top20_routes_revenue; do
  hdfs dfs -cat /taxi_project/output/$d/part-* > output/$d.tsv 2>/dev/null
  n=$(wc -l < output/$d.tsv)
  printf "%-24s %6d rows\n" "$d" "$n"
done
