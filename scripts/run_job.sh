#!/usr/bin/env bash
# run_job.sh <evidence_name> <output_hdfs_dir> <extra hadoop-streaming args...>
# Wraps a Hadoop Streaming submission: deletes the output dir, times the job,
# tees the full driver log to evidence/, and records the YARN application id.
set -o pipefail
source /home/claude/hadoop_env.sh
NAME=$1; OUT=$2; shift 2
EV=/home/claude/taxi_project/evidence
hdfs dfs -rm -r -skipTrash "$OUT" >/dev/null 2>&1
START=$(date +%s)
hadoop jar "$HADOOP_STREAMING_JAR" "$@" -output "$OUT" > "$EV/${NAME}.log" 2>&1
RC=$?
END=$(date +%s)
echo "ELAPSED_SECONDS=$((END-START))" >> "$EV/${NAME}.log"
APP=$(grep -o 'application_[0-9_]*' "$EV/${NAME}.log" | head -1)
echo "JOB=$NAME  RC=$RC  APP=$APP  ELAPSED=$((END-START))s"
if [ $RC -ne 0 ]; then echo "--- last 30 lines ---"; tail -30 "$EV/${NAME}.log"; fi
exit $RC
