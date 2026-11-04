#!/usr/bin/env python3
"""H-W2 / H-A1 test on Who&When HC: distance to the label of (a) the first orchestrator instruction that paraphrases an
earlier instruction (difflib ratio > 0.75), (b) the first ledger loop/no-progress flag, (c) the first repeated WebSurfer
action, (d) the first 'Stalled' step. Also H-A2: for Orchestrator-labelled HC logs, does the labelled ledger claim
satisfaction/progress?"""
import difflib, json, os, re, sys, statistics, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.schema import error_step
from loaders import load

def ledger(c):
    if not c.startswith('Updated Ledger'): return None
    try: return json.loads(c[len('Updated Ledger:'):].strip())
    except Exception: return None

rows = []
for r in load('who_and_when'):
    if r['subset'] != 'Hand-Crafted': continue
    g = error_step(r); n = len(r['steps'])
    instr = [(s['idx'], s['content']) for s in r['steps'] if s['agent'].startswith('Orchestrator (->')]
    para = None
    for i, (k, c) in enumerate(instr):
        for _, c0 in instr[:i]:
            if difflib.SequenceMatcher(None, c0[:400], c[:400]).ratio() > 0.75: para = k; break
        if para is not None: break
    flag = next((s['idx'] for s in r['steps'] if (L := ledger(s['content'])) and (L.get('is_in_loop', {}).get('answer') is True or L.get('is_progress_being_made', {}).get('answer') is False)), None)
    stall = next((s['idx'] for s in r['steps'] if s['content'].startswith('Stalled')), None)
    seen = set(); rep = None
    for s in r['steps']:
        if s['meta'].get('base_agent') == 'WebSurfer':
            key = s['content'].split('\n')[0][:120]
            if key in seen: rep = s['idx']; break
            seen.add(key)
    rows.append({'id': r['id'], 'n': n, 'gold': g, 'para': para, 'flag': flag, 'stall': stall, 'rep': rep, 'agent': r['labels']['error_agent'],
                 'gold_ledger': ledger(r['steps'][g]['content'])})
print('n HC', len(rows))
for key in ('para', 'flag', 'rep', 'stall'):
    d = [x[key] - x['gold'] for x in rows if x[key] is not None]
    print(f"{key:5s}: present {len(d):2d}; before label {sum(1 for v in d if v < 0):2d}, at {sum(1 for v in d if v == 0)}, after {sum(1 for v in d if v > 0):2d}; median signed {statistics.median(d) if d else None}; |d|<=3: {sum(1 for v in d if abs(v) <= 3)}")
# pairs: when both para and flag exist, which is closer / earlier
both = [x for x in rows if x['para'] is not None and x['flag'] is not None]
print('both para & flag:', len(both), '; para earlier than flag:', sum(1 for x in both if x['para'] < x['flag']), '; para closer to label:', sum(1 for x in both if abs(x['para'] - x['gold']) < abs(x['flag'] - x['gold'])))
# H-A2: orchestrator-labelled ledgers
ol = [x for x in rows if x['gold_ledger']]
print('Orchestrator ledger labels:', len(ol), '; ledger says satisfied:', sum(1 for x in ol if x['gold_ledger'].get('is_request_satisfied', {}).get('answer') is True), '; says progress & not loop:', sum(1 for x in ol if x['gold_ledger'].get('is_progress_being_made', {}).get('answer') is True and x['gold_ledger'].get('is_in_loop', {}).get('answer') is False))
# how many labelled steps of ANY type are followed within 2 steps by a ledger that says satisfied
