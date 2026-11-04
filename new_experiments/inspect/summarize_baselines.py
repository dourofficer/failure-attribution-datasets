#!/usr/bin/env python3
"""One table across all datasets from results/<slug>/all_at_once_*.jsonl: n, agent%, exact%, ±1, ±3, in-set%, signed offset split."""
import glob
import os
import sys
from statistics import median

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_jsonl, md_table  # noqa: E402

rows = []
for path in sorted(glob.glob(os.path.join(RESULTS, '*', 'all_at_once_*.jsonl'))):
    slug = os.path.basename(os.path.dirname(path))
    name = os.path.basename(path).replace('all_at_once_', '').replace('.jsonl', '')
    rs = read_jsonl(path)
    n = len(rs)
    pct = lambda k: f"{100 * sum(1 for r in rs if r.get(k)) / max(1, n):.0f}"
    d = [r['step_dist'] for r in rs if r.get('step_dist') is not None]
    miss = [x for x in d if x != 0]
    later = sum(1 for x in miss if x > 0)
    trunc = sum(1 for r in rs if r.get('pred_step') is None)
    rows.append([slug, name, n, pct('agent_ok'), pct('step_exact'), pct('step_within_1'), pct('step_within_3'), pct('step_in_set'),
                 f"{later}/{len(miss)}", f"{median([abs(x) for x in miss]) if miss else '-'}", f"{int(median([r['n_steps'] for r in rs]))}", trunc])
print(md_table(['dataset', 'variant', 'n', 'agent%', 'exact%', '±1%', '±3%', 'in-set%', 'misses later/all', 'med|off|', 'med steps', 'no-pred'], rows))
