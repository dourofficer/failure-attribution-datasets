#!/usr/bin/env python3
"""Dump records of a dataset as readable text for close reading.
Usage: python3 -I inspect/g1_dump.py <slug> [--ids a,b] [--list] [--cap 3000] [--out results/<slug>/dumps]
"""
import argparse, os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS
from common.schema import error_step
from loaders import load

ap = argparse.ArgumentParser()
ap.add_argument('slug'); ap.add_argument('--ids', default=None); ap.add_argument('--list', action='store_true')
ap.add_argument('--cap', type=int, default=3000); ap.add_argument('--out', default=None)
a = ap.parse_args()
recs = load(a.slug)
if a.list:
    for r in recs:
        print(r['id'], r['subset'], len(r['steps']), 'gold', error_step(r), r['labels']['error_steps'][:6], r['labels']['error_agent'], (r['labels']['categories'] or [''])[:2])
    sys.exit()
out = a.out or os.path.join(RESULTS, a.slug, 'dumps')
os.makedirs(out, exist_ok=True)
want = set(a.ids.split(',')) if a.ids else None
for r in recs:
    if want and r['id'] not in want:
        continue
    g = error_step(r); es = r['labels']['error_steps']
    L = [f"ID {r['id']}  subset={r['subset']}  n_steps={len(r['steps'])}  gold={g}  error_steps={es}  agent={r['labels']['error_agent']}  cats={r['labels']['categories']}",
         f"TASK: {r['task'][:1500]}", f"GT: {r['ground_truth']}", f"FINAL: {(r['final_output'] or '')[:800]}",
         f"REASON: {r['labels']['reason']}", f"EXTRA: {json.dumps({k: v for k, v in r['labels']['extra'].items() if k not in ('per_annotator','failures','individual_annotations','expected_actions')}, ensure_ascii=False)[:1500]}", '']
    if 'failures' in r['labels']['extra']:
        for f in r['labels']['extra']['failures']:
            L.append(f"  FAILURE id={f['failure_id']} step={int(f['step_number'])-1} agent={f['failed_agent']} cat={f['failure_category']} :: {f['step_reason'][:300]}")
    if 'per_annotator' in r['labels']['extra']:
        for aid, lst in r['labels']['extra']['per_annotator'].items():
            for x in lst:
                L.append(f"  ANN {aid} step={x['step']} cat={x['category']} :: {(x['reason'] or '')[:250]} || ideal: {(x['ideal_action'] or '')[:150]}")
    L.append('')
    for s in r['steps']:
        mark = ' <<<< GOLD' if s['idx'] == g else (' <<< labelled' if s['idx'] in es else '')
        votes = r['labels'].get('votes') or {}
        v = f" votes={votes.get(s['idx'])}" if votes.get(s['idx']) else ''
        c = s['content']
        if len(c) > a.cap:
            c = c[:int(a.cap*0.7)] + f"\n ... [{len(c)-a.cap} chars cut] ...\n" + c[-int(a.cap*0.3):]
        L.append(f"---- [step {s['idx']}] {s['agent']} ({s['role']}){v}{mark}\n{c}\n")
    fn = os.path.join(out, r['id'].replace('/', '__') + '.txt')
    with open(fn, 'w') as fh:
        fh.write('\n'.join(L))
    print('wrote', fn)
