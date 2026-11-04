#!/bin/bash
# Queue 5 (after queue 4): LongRCA trajectories whose rationale mentions a recovered earlier error (tag A) or failed later repairs (tag B).
cd /dataDisk/home/thanhdo/failure-attribution-datasets/experiments
while pgrep -f "run_queue_[24].sh" > /dev/null; do sleep 60; done
for ids in ids_longrca_recovered ids_longrca_repairfailed; do
  echo "=== std longrca --ids $ids $(date)"; python3 -I baseline/all_at_once.py longrca --ids baseline/$ids.txt --variant std --workers 8
  echo "=== inventory longrca --ids $ids $(date)"; python3 -I baseline/all_at_once.py longrca --ids baseline/$ids.txt --variant inventory --workers 8 --max-tokens 6000
done
echo "=== queue 5 done $(date)"
