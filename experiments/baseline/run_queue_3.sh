#!/bin/bash
cd /dataDisk/home/thanhdo/failure-attribution-datasets/experiments
for args in "symtrace" "tracertraj --subset agentic/test --sample 150" "tracertraj --subset coding/test" "tracertraj --subset math/test" "correct_error --sample 300" "trail"; do
  echo "=== std $args $(date)"; python3 -I baseline/all_at_once.py $args --variant std --workers 6
done
for args in "symtrace --sample 200" "correct_error --sample 300" "tracertraj --subset coding/test"; do
  echo "=== inventory $args $(date)"; python3 -I baseline/all_at_once.py $args --variant inventory --workers 6 --max-tokens 6000
done
echo "=== queue 3 done $(date)"
