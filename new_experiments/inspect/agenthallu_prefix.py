#!/usr/bin/env python3
"""G3 copy of inspect/prefix_probe.py with a fix for records whose task is a list (agenthallu BFCL). Prefix-only step probe: for each candidate step k, show the model ONLY steps 0..k (plus the task, no ground
truth) and ask whether step k is a mistake. Produces a per-step score curve per record, which lets us measure
(a) local detectability of the labelled step, (b) how many later 'symptom' steps are flagged, (c) the earliest
flagged step vs the label.

Usage: python3 -I inspect/prefix_probe.py <slug> [--n 20] [--seed 0] [--ids a,b] [--max-steps 40]
       [--window W: only probe steps within W of the gold step (default: all agent steps)] [--workers 6] [--no-think]
Writes results/<slug>/prefix_probe.jsonl (one line per record with scores per probed step) and prints summary.
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, append_jsonl, md_table  # noqa: E402
from common.llm import chat_json_many  # noqa: E402
from common.render import render_steps, render_task  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402


def _fix(r):
    r = dict(r); r["task"] = r["task"] if isinstance(r["task"], str) else json.dumps(r["task"], ensure_ascii=False); return r

SYSTEM = ('You are monitoring an LLM agent system while it runs. You see the task and the trajectory so far, up to and '
          'including the latest step. You do NOT know the final outcome. Judge ONLY the latest step.')
PROMPT = ('{task}\n\nTRAJECTORY SO FAR:\n\n{traj}\n\nQuestion: is the LATEST step ([step {k}], by {agent}) a mistake, '
          'i.e. does it do something wrong, unjustified, or that is likely to prevent the task from being solved '
          'correctly? Consider wrong facts, wrong tool use, ignoring available evidence, unjustified assumptions, '
          'premature conclusions, and actions that deviate from the task. Answer with one JSON object only: '
          '{{"mistake": true|false, "confidence": <0.0-1.0>, "what": "<one line>"}}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--n', type=int, default=20)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--ids', default=None)
    ap.add_argument('--subset', default=None)
    ap.add_argument('--max-steps', type=int, default=40)
    ap.add_argument('--window', type=int, default=None)
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--no-think', action='store_true')
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    recs = [_fix(r) for r in load(a.slug) if r['labels']['error_steps'] and len(r['steps']) <= a.max_steps]
    if a.subset:
        recs = [r for r in recs if r['subset'] == a.subset]
    if a.ids:
        want = set(a.ids.split(','))
        recs = [r for r in recs if r['id'] in want]
    else:
        random.Random(a.seed).shuffle(recs)
        recs = recs[:a.n]
    jobs = []
    for r in recs:
        g = error_step(r)
        for s in r['steps']:
            if s['role'] != 'agent':
                continue
            if a.window is not None and abs(s['idx'] - g) > a.window:
                continue
            prefix = {**r, 'steps': r['steps'][:s['idx'] + 1]}
            traj, _ = render_steps(prefix, total_cap_tokens=100000)
            user = PROMPT.format(task=render_task(r, with_gt=False), traj=traj, k=s['idx'], agent=s['agent'])
            jobs.append((r, s['idx'], [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}]))
    print(f'{len(recs)} records, {len(jobs)} probes', file=sys.stderr)
    outs = chat_json_many([j[2] for j in jobs], workers=a.workers, max_tokens=8192, think=not a.no_think, tag='prefix_probe')
    per = {}
    for (r, k, _), (p, o) in zip(jobs, outs):
        p = p or {}
        per.setdefault(r['id'], {'id': r['id'], 'subset': r['subset'], 'n_steps': len(r['steps']), 'gold': error_step(r),
                                 'gold_agent': r['labels']['error_agent'], 'scores': {}})
        try:
            conf = float(p.get('confidence', 0))
        except Exception:  # noqa: BLE001
            conf = 0.0
        per[r['id']]['scores'][k] = {'mistake': bool(p.get('mistake')), 'conf': conf, 'what': p.get('what'), 'agent': r['steps'][k]['agent'],
                                     'parsed': bool(p), 'finish': o.get('finish_reason'), 'fallback': o.get('fallback'), 'raw': (o['content'] or '')[-300:]}
    name = 'prefix_probe_g3' + (f'_{a.tag}' if a.tag else '')
    path = os.path.join(RESULTS, a.slug, name + '.jsonl')
    if os.path.exists(path):
        os.remove(path)
    rows = []
    for rec in per.values():
        sc = rec['scores']
        g = rec['gold']
        flagged = sorted(k for k, v in sc.items() if v['mistake'])
        rec['gold_flagged'] = bool(sc.get(g, {}).get('mistake'))
        rec['gold_conf'] = sc.get(g, {}).get('conf')
        rec['n_flagged_before'] = sum(1 for k in flagged if k < g)
        rec['n_flagged_after'] = sum(1 for k in flagged if k > g)
        rec['n_probed_before'] = sum(1 for k in sc if k < g)
        rec['n_probed_after'] = sum(1 for k in sc if k > g)
        rec['earliest_flagged'] = flagged[0] if flagged else None
        rec['argmax_conf'] = max(sc, key=lambda k: (sc[k]['mistake'], sc[k]['conf'])) if sc else None
        rec['scores'] = {str(k): v for k, v in sc.items()}
        rows.append(rec)
        append_jsonl(path, rec)
    n = len(rows)
    gf = sum(1 for x in rows if x['gold_flagged'])
    ef = sum(1 for x in rows if x['earliest_flagged'] == x['gold'])
    am = sum(1 for x in rows if x['argmax_conf'] == x['gold'])
    fb = sum(x['n_flagged_before'] for x in rows); pb = sum(x['n_probed_before'] for x in rows)
    fa = sum(x['n_flagged_after'] for x in rows); pa = sum(x['n_probed_after'] for x in rows)
    print(md_table(['metric', 'value'], [
        ['records', n],
        ['gold step flagged as mistake (local detectability)', f'{gf} ({100 * gf / max(1, n):.1f}%)'],
        ['earliest flagged step == gold', f'{ef} ({100 * ef / max(1, n):.1f}%)'],
        ['argmax-confidence step == gold', f'{am} ({100 * am / max(1, n):.1f}%)'],
        ['flag rate on steps BEFORE gold', f'{fb}/{pb} ({100 * fb / max(1, pb):.1f}%)'],
        ['flag rate on steps AFTER gold', f'{fa}/{pa} ({100 * fa / max(1, pa):.1f}%)'],
    ]))
    print('wrote', path)


if __name__ == '__main__':
    main()
