#!/bin/bash
cd /dataDisk/home/thanhdo/failure-attribution-datasets/new_experiments
for p in 8210 8211 8212; do until curl -s -m 2 localhost:$p/v1/models >/dev/null; do sleep 15; done; echo "server $p up"; done
export LLM_BASE_URLS=http://localhost:8210/v1,http://localhost:8211/v1,http://localhost:8212/v1
run() { echo "### $(date +%H:%M) $*"; python3 inspect/oc_classify.py "$@" 2>&1 | grep -v Warning; }
run who_and_when --all --workers 90
run agentrx --all --workers 90
run mp_bench --all --workers 90
run traceelephant --all --workers 90
run trail --all --workers 90
run agenterrorbench --all --workers 90
run agenthallu --n 150 --workers 90
run searchauditbench --n 150 --workers 90
run symtrace --n 120 --workers 90
run trajerrbench --n 120 --workers 90
run horizon --n 120 --workers 90
run longrca --n 120 --workers 90
run tracertraj --n 120 --workers 90
run who_and_when_pro --n 120 --workers 90
run aegis --n 80 --workers 90
run correct_error --n 80 --workers 90
run memtrace --n 60 --workers 90
echo "### $(date +%H:%M) ALL DONE"
