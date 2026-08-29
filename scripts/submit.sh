#!/usr/bin/env bash
# submit.sh <evidence_name> <output_hdfs_dir> <args...>  -- fire and forget
source /home/claude/hadoop_env.sh
NAME=$1; OUT=$2; shift 2
EV=/home/claude/taxi_project/evidence
hdfs dfs -rm -r -skipTrash "$OUT" >/dev/null 2>&1
rm -f "$EV/${NAME}.log" "$EV/${NAME}.done"
nohup bash -c "
  source /home/claude/hadoop_env.sh
  cd /home/claude/taxi_project
  S=\$(date +%s)
  hadoop jar \"\$HADOOP_STREAMING_JAR\" $(printf '%q ' "$@") -output $OUT > $EV/${NAME}.log 2>&1
  RC=\$?
  E=\$(date +%s)
  echo \"ELAPSED_SECONDS=\$((E-S))\" >> $EV/${NAME}.log
  echo \"RC=\$RC ELAPSED=\$((E-S))\" > $EV/${NAME}.done
" > /dev/null 2>&1 &
echo "submitted $NAME"
