#!/usr/bin/env bash
# collect_evidence.sh -- gathers the cluster/HDFS/YARN evidence required by
# section 16 of the assignment into evidence/*.txt
source /home/claude/hadoop_env.sh
cd /home/claude/taxi_project
EV=evidence

{ echo "############### 1. HADOOP SERVICES RUNNING (jps) ###############"
  echo "\$ jps"; jps
  echo; echo "\$ hadoop version"; hadoop version
} > $EV/E1_services_running.txt 2>&1

{ echo "############### 2. HDFS DIRECTORY STRUCTURE ###############"
  echo "\$ hdfs dfs -ls -R /taxi_project"; hdfs dfs -ls -R /taxi_project
} > $EV/E2_hdfs_structure.txt 2>&1

{ echo "############### 3. DATASET IN HDFS + BLOCK INFORMATION ###############"
  echo "\$ hdfs dfs -ls -h /taxi_project/input/raw/";     hdfs dfs -ls -h /taxi_project/input/raw/
  echo; echo "\$ hdfs dfs -ls -h /taxi_project/input/cleaned/"; hdfs dfs -ls -h /taxi_project/input/cleaned/
  echo; echo "\$ hdfs dfs -du -h /taxi_project/input/raw/";     hdfs dfs -du -h /taxi_project/input/raw/
  echo; echo "\$ hdfs dfs -du -s -h /taxi_project";             hdfs dfs -du -s -h /taxi_project
  echo; echo "\$ hdfs fsck /taxi_project/input -files -blocks"; hdfs fsck /taxi_project/input -files -blocks
  echo; echo "\$ hdfs dfsadmin -report";                        hdfs dfsadmin -report
} > $EV/E3_hdfs_data_and_blocks.txt 2>&1

{ echo "############### 4. YARN APPLICATIONS ###############"
  echo "\$ yarn node -list -all"; yarn node -list -all
  echo; echo "\$ yarn application -list -appStates ALL"; yarn application -list -appStates ALL
  echo; echo "############### PER-APPLICATION DETAIL ###############"
  for a in $(yarn application -list -appStates ALL 2>/dev/null | grep -o 'application_[0-9_]*' | sort -u); do
     echo "-------------------------------------------------------------"
     echo "\$ yarn application -status $a"
     yarn application -status $a 2>/dev/null
  done
  echo; echo "############### RM REST API: /ws/v1/cluster/apps ###############"
  curl -s "http://localhost:8088/ws/v1/cluster/apps" | python3 -m json.tool 2>/dev/null | head -400
} > $EV/E4_yarn_applications.txt 2>&1

{ echo "############### 5. INTERMEDIATE (STAGE-1) MAPREDUCE OUTPUT ###############"
  echo "This is what the two-stage workflow hands from job 1 to job 2."
  echo; echo "\$ hdfs dfs -ls -h /taxi_project/output/revenue"; hdfs dfs -ls -h /taxi_project/output/revenue
  echo; echo "\$ hdfs dfs -cat /taxi_project/output/revenue/part-00000 | head -12"
  hdfs dfs -cat /taxi_project/output/revenue/part-00000 2>/dev/null | head -12
  echo; echo "############### 6. FINAL (STAGE-2) RESULT ###############"
  echo "\$ hdfs dfs -cat /taxi_project/output/top10_revenue_zones/part-00000"
  hdfs dfs -cat /taxi_project/output/top10_revenue_zones/part-00000 2>/dev/null
} > $EV/E5_multistage_output.txt 2>&1

{ echo "############### 7. ALL FINAL RESULTS IN HDFS ###############"
  hdfs dfs -ls -R /taxi_project/output
} > $EV/E6_final_results.txt 2>&1

echo "evidence collected:"; ls -1 $EV/E*.txt
