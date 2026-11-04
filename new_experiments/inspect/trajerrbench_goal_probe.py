#!/usr/bin/env python3
"""tau2 subset: does knowing the user's hidden goal (shipped only in the zh edition's task_description) change
all-at-once attribution? Runs the std baseline prompt on the same records with the goal text prepended.
Usage: python3 -I inspect/trajerrbench_goal_probe.py [--n 50] [--workers 4]"""
import argparse, json, os, re, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, DATA, append_jsonl, md_table, read_json
from common.llm import chat_json_many
from common.render import render_steps, render_task
from common.schema import error_step
from loaders import load
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'baseline'))
from all_at_once import SYSTEM, PROMPT_STD, score  # noqa

ap = argparse.ArgumentParser(); ap.add_argument('--n', type=int, default=50); ap.add_argument('--workers', type=int, default=4); ap.add_argument('--seed', type=int, default=0)
a = ap.parse_args()
recs = [r for r in load('trajerrbench') if r['subset'] == 'tau2bench']
random.Random(a.seed).shuffle(recs); recs = recs[:a.n]
ZH = os.path.join(DATA, 'trajerrbench', 'repo_TrajDebug', 'data', 'trajerrbench', 'zh', 'tau2bench')
def goal(r):
    d = read_json(os.path.join(ZH, os.path.basename(r['meta']['file'])))
    t = d['metadata']['task_description']
    m = re.search(r'用户目的[:：]\s*(.*)', t, re.S)
    return (m.group(1) if m else t).strip()
msgs = {'std': [], 'goal': []}
for r in recs:
    traj, _ = render_steps(r, total_cap_tokens=150000)
    task = render_task(r, with_gt=True)
    msgs['std'].append([{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': PROMPT_STD.format(task=task, traj=traj)}])
    task_g = task + ('\n\nHIDDEN USER GOAL (the simulated user\'s scenario instructions, in Chinese; the agent never saw this, but it defines what a successful outcome is):\n' + goal(r))
    msgs['goal'].append([{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': PROMPT_STD.format(task=task_g, traj=traj)}])
out = {}
for k in ('std', 'goal'):
    res = chat_json_many(msgs[k], workers=a.workers, max_tokens=16384, think=True, tag='aao_std')
    path = os.path.join(RESULTS, 'trajerrbench', f'goal_probe_{k}.jsonl')
    if os.path.exists(path): os.remove(path)
    rows = []
    for r, (p, o) in zip(recs, res):
        sc = score(r, p or {}); row = {'id': r['id'], 'n_steps': len(r['steps']), 'pred': p, **sc, 'cat': r['labels']['categories'], 'reasoning': (o.get('reasoning') or '')[-3000:]}
        rows.append(row); append_jsonl(path, row)
    out[k] = rows
tbl = []
for k, rows in out.items():
    n = len(rows); d = [x['step_dist'] for x in rows if x['step_dist'] is not None]
    tbl.append([k, n, sum(x['step_exact'] for x in rows), sum(x['step_within_3'] for x in rows), sum(1 for x in d if x > 0), sum(1 for x in d if x < 0), sum(1 for x in rows if x['pred_step'] is None)])
print(md_table(['condition', 'n', 'exact', 'within3', 'later', 'earlier', 'parse_fail'], tbl))
both = sum(1 for x, y in zip(out['std'], out['goal']) if x['step_exact'] and y['step_exact']); only_g = sum(1 for x, y in zip(out['std'], out['goal']) if not x['step_exact'] and y['step_exact']); only_s = sum(1 for x, y in zip(out['std'], out['goal']) if x['step_exact'] and not y['step_exact'])
print('both exact', both, 'goal-only exact', only_g, 'std-only exact', only_s)
print('pred changed by goal:', sum(1 for x, y in zip(out['std'], out['goal']) if x['pred_step'] != y['pred_step']))
