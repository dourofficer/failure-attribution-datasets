#!/usr/bin/env python3
"""Cross-dataset summary of prefix-probe outputs (results/<slug>/prefix_probe*.jsonl)."""
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_jsonl, md_table  # noqa: E402

rows = []
for path in sorted(glob.glob(os.path.join(RESULTS, '*', 'prefix_probe*.jsonl'))):
    slug = os.path.basename(os.path.dirname(path))
    name = os.path.basename(path).replace('.jsonl', '')
    rs = [r for r in read_jsonl(path) if 'scores' in r]
    if not rs:
        continue
    n = len(rs)
    gf = sum(1 for r in rs if r.get('gold_flagged'))
    ef = sum(1 for r in rs if r.get('earliest_flagged') == r.get('gold'))
    fb = sum(r.get('n_flagged_before', 0) for r in rs); pb = sum(r.get('n_probed_before', 0) for r in rs)
    fa = sum(r.get('n_flagged_after', 0) for r in rs); pa = sum(r.get('n_probed_after', 0) for r in rs)
    probes = sum(len(r['scores']) for r in rs)
    rows.append([slug, name, n, probes, f'{100*gf/n:.0f}', f'{100*ef/n:.0f}', f'{100*fb/max(1,pb):.0f} ({pb})', f'{100*fa/max(1,pa):.0f} ({pa})'])
print(md_table(['dataset', 'file', 'records', 'probes', 'gold flagged%', 'earliest flag=gold%', 'flag% before gold (n)', 'flag% after gold (n)'], rows))
