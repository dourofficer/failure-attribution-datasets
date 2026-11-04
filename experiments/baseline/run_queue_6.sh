#!/bin/bash
# Queue 6: levers that could raise step accuracy, on a fixed panel. Cheap variants first, extended reasoning last.
cd /dataDisk/home/thanhdo/failure-attribution-datasets/experiments
PANEL=("who_and_when" "agentrx" "trajerrbench --subset tau2bench --sample 150" "traceelephant --sample 120" "longrca --sample 60" "agenterrorbench --sample 100")
for args in "${PANEL[@]}"; do echo "=== fewshot3 $args $(date)"; python3 -I baseline/all_at_once.py $args --fewshot 3 --workers 8; done
for args in "${PANEL[@]}"; do echo "=== twostage $args $(date)"; python3 -I baseline/all_at_once.py $args --variant twostage --workers 8; done
for args in "who_and_when" "traceelephant --sample 120" "agentrx"; do echo "=== gold $args $(date)"; python3 -I baseline/all_at_once.py $args --gold --workers 8; done
for args in "${PANEL[@]}"; do echo "=== sc5 $args $(date)"; python3 -I baseline/all_at_once.py $args --samples 5 --temperature 0.7 --workers 8; done
for args in "who_and_when" "agentrx" "trajerrbench --subset tau2bench --sample 150" "traceelephant --sample 120"; do echo "=== thinking $args $(date)"; python3 -I baseline/all_at_once.py $args --thinking --max-tokens 12000 --workers 8; done
echo "=== queue 6 done $(date)"
