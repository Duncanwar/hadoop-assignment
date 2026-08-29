#!/usr/bin/env bash
# wait_job.sh <evidence_name> [max_seconds]
EV=/home/claude/taxi_project/evidence
NAME=$1; MAX=${2:-540}; W=0
while [ ! -f "$EV/${NAME}.done" ] && [ $W -lt $MAX ]; do sleep 10; W=$((W+10)); done
if [ -f "$EV/${NAME}.done" ]; then
  echo "FINISHED $NAME : $(cat $EV/${NAME}.done)"
  grep -o 'application_[0-9_]*' "$EV/${NAME}.log" | head -1 | sed 's/^/APP=/'
else
  echo "STILL RUNNING $NAME after ${W}s"
  grep -E 'map [0-9]+% reduce' "$EV/${NAME}.log" | tail -1
fi
