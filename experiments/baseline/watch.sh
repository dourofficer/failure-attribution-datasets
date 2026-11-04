#!/bin/bash
# emits one line per dataset start, dataset completion (N/N done), error or queue end
cd /dataDisk/home/thanhdo/failure-attribution-datasets/experiments
tail -n0 -F baseline/queue_8.log 2>/dev/null | python3 -u -c '
import sys, re
for line in sys.stdin:
    m = re.search(r"(\d+)/(\d+) done", line)
    if line.startswith("===") or "Traceback" in line or "Error" in line or (m and m.group(1) == m.group(2)):
        print(line.rstrip(), flush=True)
'
