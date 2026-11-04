#!/usr/bin/env python3
"""Skeleton view of a LongRCA record: one line per step (agent, first N chars) + full text in a window around gold."""
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.schema import error_step
from loaders import load
ids = sys.argv[1].split(','); W = int(sys.argv[2]) if len(sys.argv) > 2 else 3; N = int(sys.argv[3]) if len(sys.argv) > 3 else 160
recs = {r['id']: r for r in load('longrca') if r['id'] in ids}
for i in ids:
    r = recs[i]; g = error_step(r)
    print(f"=== {i} n={len(r['steps'])} gold={g} agent={r['labels']['error_agent']}\nREASON: {r['labels']['reason']}\n")
    for s in r['steps']:
        c = re.sub(r'\s+', ' ', s['content'])
        c = re.sub(r'<think>.*?</think>', '[think] ', c)[:N]
        print(f"[{s['idx']}] {s['agent']}: {c}")
    print('\n--- WINDOW ---')
    for s in r['steps'][max(0, g - W): g + W + 1]:
        mark = ' <<<< GOLD' if s['idx'] == g else ''
        print(f"\n[{s['idx']}] {s['agent']}{mark}\n{s['content'][:4000]}")
