#!/bin/bash
# Runs the all-at-once baselines for every dataset in three parallel chains (shared vLLM server).
# Each dataset gets results/<slug>/DONE when both its variants have finished.
cd "$(dirname "$0")/.."
run() { # slug args...
  slug=$1; shift
  mkdir -p results/$slug
  python3 -I baseline/all_at_once.py $slug "$@" >> results/$slug/run.log 2>&1
}
done_mark() { python3 -I inspect/analyze_baseline.py $1 >> results/$1/run.log 2>&1; python3 -I inspect/analyze_baseline.py $1 all_at_once_std_nogt >> results/$1/run.log 2>&1; touch results/$1/DONE; }
chainA() {  # short / medium, natural
  run agentrx --n 73 --workers 4; run agentrx --n 73 --workers 4 --variant inventory; done_mark agentrx
  run agenthallu --n 80 --workers 4; done_mark agenthallu
  run trajerrbench --n 80 --workers 4 --budget-tokens 150000; done_mark trajerrbench
  run symtrace --n 60 --workers 4; done_mark symtrace
  run agenterrorbench --n 60 --workers 4; done_mark agenterrorbench
  run horizon --n 60 --workers 4; done_mark horizon
}
chainB() {  # long traces
  run traceelephant --n 90 --workers 4; run traceelephant --n 90 --workers 4 --variant inventory; done_mark traceelephant
  run mp_bench --n 80 --workers 4; run mp_bench --n 80 --workers 4 --variant inventory; done_mark mp_bench
  run longrca --n 60 --workers 4 --budget-tokens 150000 --max-tokens 20000; done_mark longrca
  run trail --n 40 --workers 4 --budget-tokens 150000; run trail --n 40 --workers 4 --budget-tokens 150000 --variant inventory; done_mark trail
  run searchauditbench --n 40 --workers 4 --no-gt --budget-tokens 150000; done_mark searchauditbench
  run memtrace --n 30 --workers 4 --budget-tokens 150000; done_mark memtrace
}
chainC() {  # injected / taxonomy
  run who_and_when_pro --n 100 --workers 4; done_mark who_and_when_pro
  run correct_error --n 80 --workers 4 --no-gt; done_mark correct_error
  run tracertraj --n 60 --workers 4; done_mark tracertraj
  run aegis --n 60 --workers 4; done_mark aegis
}
chainA & chainB & chainC &
wait
echo ALL_DONE
