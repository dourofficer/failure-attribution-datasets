#!/bin/bash
# Baseline queue 1: single-agent debugging datasets (loaders from group C). Sequential to keep the GPU busy but not oversubscribed.
cd /dataDisk/home/thanhdo/failure-attribution-datasets/experiments
for args in "agenterrorbench" "trajerrbench --subset tau2bench" "trajerrbench --subset swebenchpro" "agenthallu" "horizon" "searchauditbench --sample 200"; do
  echo "=== std $args $(date)"; python3 -I baseline/all_at_once.py $args --variant std --workers 8
done
for args in "agenterrorbench" "trajerrbench --subset tau2bench" "trajerrbench --subset swebenchpro" "agenthallu" "searchauditbench --sample 200"; do
  echo "=== inventory $args $(date)"; python3 -I baseline/all_at_once.py $args --variant inventory --workers 8 --max-tokens 6000
done
echo "=== queue 1 done $(date)"
