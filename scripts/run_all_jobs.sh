#!/usr/bin/env bash
# run_all_jobs.sh -- submits every analytical MapReduce job in sequence.
source /home/claude/hadoop_env.sh
cd /home/claude/taxi_project
EV=evidence
CLEAN=/taxi_project/input/cleaned
RAW=/taxi_project/input/raw
J="hadoop jar $HADOOP_STREAMING_JAR"

run () {  # run <name> <outdir> <args...>
  local name=$1 out=$2; shift 2
  hdfs dfs -rm -r -skipTrash "$out" >/dev/null 2>&1
  local s=$(date +%s)
  $J "$@" -output "$out" > "$EV/${name}.log" 2>&1
  local rc=$?
  local e=$(date +%s)
  echo "ELAPSED_SECONDS=$((e-s))" >> "$EV/${name}.log"
  echo "$name RC=$rc ELAPSED=$((e-s))s APP=$(grep -o 'application_[0-9_]*' $EV/${name}.log | head -1)" >> $EV/JOBS_STATUS.txt
}

: > $EV/JOBS_STATUS.txt

# ---- (a) hourly demand ----
run 11_job_hourly /taxi_project/output/hourly \
  -D mapreduce.job.name=02-HourlyTaxiDemand -D mapreduce.job.reduces=1 \
  -input $CLEAN -mapper "python3 mapper_hourly.py" -combiner "python3 reducer_hourly.py" \
  -reducer "python3 reducer_hourly.py" -file mappers/mapper_hourly.py -file reducers/reducer_hourly.py

# ---- (b) daily demand ----
run 12_job_daily /taxi_project/output/daily \
  -D mapreduce.job.name=03-DailyDemandWeekdayWeekend -D mapreduce.job.reduces=1 \
  -input $CLEAN -mapper "python3 mapper_daily.py" -combiner "python3 reducer_daily.py" \
  -reducer "python3 reducer_daily.py" -file mappers/mapper_daily.py -file reducers/reducer_daily.py

# ---- (c) pickup locations ----
run 13_job_locations /taxi_project/output/locations \
  -D mapreduce.job.name=04-PickupLocationTripCounts -D mapreduce.job.reduces=1 \
  -input $CLEAN -mapper "python3 mapper_location.py" -combiner "python3 reducer_location.py" \
  -reducer "python3 reducer_location.py" -file mappers/mapper_location.py -file reducers/reducer_location.py

# ---- (d) revenue by pickup zone  == STAGE 1 of the two-stage workflow ----
run 14_job_revenue /taxi_project/output/revenue \
  -D mapreduce.job.name=05-RevenueByPickupZone-STAGE1 -D mapreduce.job.reduces=1 \
  -input $CLEAN -mapper "python3 mapper_revenue.py" -combiner "python3 combiner_sums.py" \
  -reducer "python3 reducer_revenue.py" -file mappers/mapper_revenue.py \
  -file reducers/combiner_sums.py -file reducers/reducer_revenue.py

# ---- (e) payment methods ----
run 15_job_payment /taxi_project/output/payment \
  -D mapreduce.job.name=06-PaymentMethodAnalysis -D mapreduce.job.reduces=1 \
  -input $CLEAN -mapper "python3 mapper_payment.py" -combiner "python3 combiner_sums.py" \
  -reducer "python3 reducer_payment.py" -file mappers/mapper_payment.py \
  -file reducers/combiner_sums.py -file reducers/reducer_payment.py

# ---- (f) distance bands ----
run 16_job_distance /taxi_project/output/distance \
  -D mapreduce.job.name=07-DistanceBasedFareAnalysis -D mapreduce.job.reduces=1 \
  -input $CLEAN -mapper "python3 mapper_distance.py" -combiner "python3 combiner_sums.py" \
  -reducer "python3 reducer_distance.py" -file mappers/mapper_distance.py \
  -file reducers/combiner_sums.py -file reducers/reducer_distance.py

# ---- (g) routes ----
run 17_job_routes /taxi_project/output/routes \
  -D mapreduce.job.name=08-BusiestPickupDropoffRoutes -D mapreduce.job.reduces=2 \
  -input $CLEAN -mapper "python3 mapper_route.py" -combiner "python3 combiner_sums.py" \
  -reducer "python3 reducer_route.py" -file mappers/mapper_route.py \
  -file reducers/combiner_sums.py -file reducers/reducer_route.py

# ---- (h) trip duration ----
run 18_job_duration /taxi_project/output/duration \
  -D mapreduce.job.name=09-TripDurationAnalysis -D mapreduce.job.reduces=1 \
  -input $CLEAN -mapper "python3 mapper_duration.py" -combiner "python3 combiner_sums.py" \
  -reducer "python3 reducer_duration.py" -file mappers/mapper_duration.py \
  -file reducers/combiner_sums.py -file reducers/reducer_duration.py

# ---- (i) anomaly detection -- runs over the RAW feed ----
run 19_job_anomaly /taxi_project/output/anomalies \
  -D mapreduce.job.name=10-AnomalyDetection-RawFeed -D mapreduce.job.reduces=1 \
  -input $RAW -mapper "python3 mapper_anomaly.py" -combiner "python3 reducer_hourly.py" \
  -reducer "python3 reducer_anomaly.py" -file mappers/mapper_anomaly.py \
  -file reducers/reducer_hourly.py -file reducers/reducer_anomaly.py

# ================= STAGE 2 JOBS: consume stage-1 HDFS output =================
run 20_job_top10_revenue_zones /taxi_project/output/top10_revenue_zones \
  -D mapreduce.job.name=11-Top10RevenueZones-STAGE2 -D mapreduce.job.reduces=1 \
  -input /taxi_project/output/revenue -mapper "python3 mapper_topn.py" \
  -reducer "python3 reducer_topn.py" -cmdenv SORT_FIELD=4 -cmdenv TOPN=10 -cmdenv ORDER=desc \
  -file mappers/mapper_topn.py -file reducers/reducer_topn.py

run 21_job_top10_zones_trips /taxi_project/output/top10_zones_trips \
  -D mapreduce.job.name=12-Top10PickupZonesByTrips -D mapreduce.job.reduces=1 \
  -input /taxi_project/output/locations -mapper "python3 mapper_topn.py" \
  -reducer "python3 reducer_topn.py" -cmdenv SORT_FIELD=1 -cmdenv TOPN=10 -cmdenv ORDER=desc \
  -file mappers/mapper_topn.py -file reducers/reducer_topn.py

run 22_job_bottom10_zones_trips /taxi_project/output/bottom10_zones_trips \
  -D mapreduce.job.name=13-Bottom10PickupZonesByTrips -D mapreduce.job.reduces=1 \
  -input /taxi_project/output/locations -mapper "python3 mapper_topn.py" \
  -reducer "python3 reducer_topn.py" -cmdenv SORT_FIELD=1 -cmdenv TOPN=10 -cmdenv ORDER=asc \
  -file mappers/mapper_topn.py -file reducers/reducer_topn.py

run 23_job_top20_routes_trips /taxi_project/output/top20_routes_trips \
  -D mapreduce.job.name=14-Top20RoutesByTripCount -D mapreduce.job.reduces=1 \
  -input /taxi_project/output/routes -mapper "python3 mapper_topn.py" \
  -reducer "python3 reducer_topn.py" -cmdenv SORT_FIELD=1 -cmdenv TOPN=20 -cmdenv ORDER=desc \
  -file mappers/mapper_topn.py -file reducers/reducer_topn.py

run 24_job_top20_routes_revenue /taxi_project/output/top20_routes_revenue \
  -D mapreduce.job.name=15-Top20RoutesByRevenue -D mapreduce.job.reduces=1 \
  -input /taxi_project/output/routes -mapper "python3 mapper_topn.py" \
  -reducer "python3 reducer_topn.py" -cmdenv SORT_FIELD=2 -cmdenv TOPN=20 -cmdenv ORDER=desc \
  -file mappers/mapper_topn.py -file reducers/reducer_topn.py

echo "ALL_JOBS_COMPLETE" >> $EV/JOBS_STATUS.txt
