#!/bin/bash
# Thinking runs with a 32k completion budget (the 12k budget truncated 26% of Who&When answers).
cd /dataDisk/home/thanhdo/failure-attribution-datasets/experiments
echo "=== thinking32k who_and_when (redo truncated) $(date)"; python3 -I baseline/all_at_once.py who_and_when --thinking --max-tokens 32000 --ids baseline/ids_think_redo.txt --workers 8
for args in "agentrx" "trajerrbench --subset tau2bench --sample 150"; do echo "=== thinking32k $args $(date)"; python3 -I baseline/all_at_once.py $args --thinking --max-tokens 32000 --workers 8; done
echo "=== queue 8 done $(date)"
