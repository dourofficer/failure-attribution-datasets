#!/bin/bash
cd /dataDisk/home/thanhdo/failure-attribution-datasets/experiments
for args in "who_and_when" "agentrx" "traceelephant" "mp_bench" "longrca --sample 200" "who_and_when_pro --sample 300"; do
  echo "=== std $args $(date)"; python3 -I baseline/all_at_once.py $args --variant std --workers 8
done
for args in "who_and_when" "agentrx" "traceelephant" "mp_bench" "longrca --sample 200"; do
  echo "=== inventory $args $(date)"; python3 -I baseline/all_at_once.py $args --variant inventory --workers 8 --max-tokens 6000
done
echo "=== queue 2 done $(date)"
