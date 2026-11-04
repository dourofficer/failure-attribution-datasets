#!/bin/bash
cd /dataDisk/home/thanhdo/failure-attribution-datasets/experiments
for args in "who_and_when" "agentrx" "mp_bench" "trajerrbench --subset tau2bench --sample 150" "traceelephant --sample 120" "longrca --sample 60" "agenterrorbench --sample 100" "searchauditbench --sample 100"; do
  echo "=== backward $args $(date)"; python3 -I baseline/all_at_once.py $args --variant backward --workers 6
done
echo "=== queue 7 done $(date)"
