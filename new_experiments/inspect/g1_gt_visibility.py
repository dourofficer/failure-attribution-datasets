#!/usr/bin/env python3
"""Where does the answer-relevant evidence (the ground-truth answer string) first appear in the trajectory, relative to the label?
Datasets: who_and_when, mp_bench (string ground truths only; skips GT shorter than 3 chars or purely numeric < 3 digits)."""
import os, re, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.schema import error_step
from loaders import load
def norm(s): return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', str(s or '').lower())).strip()
for slug in ('who_and_when', 'mp_bench'):
    c = collections.Counter(); ex = collections.defaultdict(list)
    for r in load(slug):
        gt = norm(r['ground_truth']); g = error_step(r)
        if g is None or len(gt) < 3 or (gt.isdigit() and len(gt) < 4): c[(r['subset'], 'skipped')] += 1; continue
        hits = [s['idx'] for s in r['steps'] if s['role'] == 'agent' and gt in norm(s['content'])]
        if not hits: k = 'never'
        elif hits[0] < g: k = 'before_label'
        elif hits[0] == g: k = 'at_label'
        else: k = 'after_label'
        c[(r['subset'], k)] += 1
        if k == 'before_label': ex[r['subset']].append((r['id'], hits[0], g))
    print(slug, sorted(c.items()))
    for sub, l in ex.items(): print('  before-label examples', sub, l[:8])
