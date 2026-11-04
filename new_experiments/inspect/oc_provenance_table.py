#!/usr/bin/env python3
"""One table over results/omission_commission/provenance_*.jsonl (failed runs only)."""
import glob, os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_jsonl, md_table
OUT = os.path.join(RESULTS, 'omission_commission')
def pct(a, b): return f'{100*a/b:.0f}%' if b else '-'
rows = []
for f in sorted(glob.glob(os.path.join(OUT, 'provenance_*.jsonl'))):
    slug = os.path.basename(f)[11:-6]
    rs = [r for r in read_jsonl(f) if r['outcome'] != 'success']
    gtu = [r for r in rs if r['gt_usable']]
    fu = [r for r in rs if r['final_usable'] and not r['final_eq_gt']]
    both = [r for r in rs if r['gt_usable'] and r['final_usable'] and not r['final_eq_gt']]
    c = collections.Counter(r['final_origin'] for r in fu)
    rows.append([slug, len(rs), len(gtu), pct(sum(1 for r in gtu if r['gt_obs_first'] is None), len(gtu)),
                 pct(sum(1 for r in gtu if r.get('gt_obs_rel') in ('before', 'at')), len(gtu)),
                 len(fu), pct(c['evidence'], len(fu)), pct(c['memory'], len(fu)), pct(c['none'], len(fu)),
                 len(both), pct(sum(1 for r in both if r['pair_proxy']), len(both)), pct(sum(1 for r in both if r['ignored_proxy']), len(both))])
print(md_table(['dataset', 'failed runs', 'GT usable', 'GT never in an observation', 'GT observed at/before label', 'final usable', 'final from evidence', 'final from memory', 'final appears nowhere before end', 'both usable', 'pair proxy', 'ignored-evidence proxy'], rows))
