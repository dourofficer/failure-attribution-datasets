#!/usr/bin/env python3
"""Condensed trajectory view: ledgers summarised, each step cut to --cap chars, labelled step and +-W neighbours shown with --full chars.
Usage: python3 -I inspect/g1_condensed.py <slug> --ids a,b [--cap 250] [--full 1500] [--window 1]"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.schema import error_step
from loaders import load
ap = argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('--ids', required=True)
ap.add_argument('--cap', type=int, default=250); ap.add_argument('--full', type=int, default=1500); ap.add_argument('--window', type=int, default=1)
a = ap.parse_args()
want = a.ids.split(',')
recs = {r['id']: r for r in load(a.slug)}
def ledger(c):
    if not c.startswith('Updated Ledger'): return None
    try:
        j = json.loads(c[len('Updated Ledger:'):].strip())
        return 'LEDGER sat=%s loop=%s prog=%s next=%s :: %s' % (j['is_request_satisfied']['answer'], j['is_in_loop']['answer'], j['is_progress_being_made']['answer'], j['next_speaker']['answer'], j['instruction_or_question']['answer'][:160])
    except Exception:
        return 'LEDGER(unparsed) ' + c[:160].replace('\n', ' ')
for k in want:
    r = recs[k]; g = error_step(r); es = set(r['labels']['error_steps'])
    print(f"\n######## {k} n={len(r['steps'])} gold={g} set={sorted(es)} agent={r['labels']['error_agent']} cats={r['labels']['categories']}\nTASK: {r['task'][:600]}\nGT: {r['ground_truth']}\nREASON: {str(r['labels']['reason'])[:700]}")
    for s in r['steps']:
        c = s['content']; L = ledger(c)
        near = any(abs(s['idx'] - e) <= a.window for e in es)
        if L and not near: c = L
        else:
            cap = a.full if near else a.cap
            c = c if len(c) <= cap else c[:int(cap*0.75)] + f' ...[{len(c)-cap} cut]... ' + c[-int(cap*0.25):]
            c = re.sub(r'\n+', ' | ', c)
        mark = ' <<<<GOLD' if s['idx'] == g else (' <<labelled' if s['idx'] in es else '')
        v = (r['labels'].get('votes') or {}).get(s['idx'])
        print(f"[{s['idx']}] {s['agent']}{' v'+str(v) if v else ''}{mark}: {c}")
