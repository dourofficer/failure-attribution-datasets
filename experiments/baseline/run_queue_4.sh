#!/bin/bash
# Queue 4: waits for queue 2, then anonymised-name runs (H7) and outcome-blind inventories incl. successful runs (H1 control).
cd /dataDisk/home/thanhdo/failure-attribution-datasets/experiments
while pgrep -f run_queue_2.sh > /dev/null; do sleep 60; done
for args in "who_and_when" "traceelephant" "mp_bench"; do
  echo "=== std anon $args $(date)"; python3 -I baseline/all_at_once.py $args --variant std --anonymise --workers 8
done
for args in "agenthallu" "trail" "horizon --subset web --sample 150"; do
  echo "=== inventory_blind $args $(date)"; python3 -I baseline/all_at_once.py $args --variant inventory_blind --workers 8 --max-tokens 6000
done
echo "=== queue 4 done $(date)"
