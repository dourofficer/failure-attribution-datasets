#!/usr/bin/env python3
"""No-LLM 'first symptom' heuristics vs the human label on AgentErrorBench (turn units).
Candidates: first malformed/inadmissible action, first 'Nothing happens', first repeated action, first repeated observation,
first error-like tool result, first turn of the longest identical-action run, last turn, turn 1. Reports exact / ±1 / ±3 per env.
Writes results/agenterrorbench/heuristics.md"""
import json, os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_json, md_table  # noqa

R = os.path.join(RESULTS, 'agenterrorbench')
turns_all = read_json(os.path.join(R, 'compact_turns.json'))
per = {json.loads(l)['id']: json.loads(l) for l in open(os.path.join(R, 'stats_per_run.jsonl'))}


def norm(a):
    a = a.strip().strip("'\"").strip()
    q = re.findall(r"'([^']{3,60})'", a)
    if q and not a.startswith('search[') and not a.startswith('click['):
        a = q[0]
    return a.lower().rstrip('.').strip("'\" ")


def cands(rid):
    d = turns_all[rid]; p = per[rid]
    acts = [norm(t['action']) for t in d['turns']]
    obs = [(t['obs_after'] or '').strip()[:200] for t in d['turns']]
    n = len(acts)
    out = {'turn 1': 1, 'last turn': n}
    out['first malformed/inadmissible'] = min([x for x in (p['first_malformed_turn'], p['first_inadmissible_turn']) if x] or [None])
    out["first 'Nothing happens'"] = p['first_nothing_turn']
    seen = set(); fr = None
    for i, a in enumerate(acts):
        if a in seen: fr = i + 1; break
        seen.add(a)
    out['first repeated action'] = fr
    seen = set(); fo = None
    for i, o in enumerate(obs):
        if o in seen and o: fo = i + 1; break
        seen.add(o)
    out['first repeated observation'] = fo
    fe = next((i + 1 for i, o in enumerate(obs) if re.search(r'\b(error|exception|traceback|failed|not found|invalid)\b', o, re.I)), None)
    out['first error-like tool result'] = fe
    # longest identical run start
    best = (0, None); cur = 1
    for i in range(1, n):
        cur = cur + 1 if acts[i] == acts[i - 1] else 1
        if cur > best[0]: best = (cur, i - cur + 2)
    out['start of longest identical-action run'] = best[1] if best[0] >= 2 else None
    out['first anomaly (min of the above symptom turns)'] = min([v for k, v in out.items() if v and k not in ('turn 1', 'last turn')] or [None])
    return out

rows = []
names = None
for env in ('alfworld', 'webshop', 'gaia'):
    ids = [i for i in turns_all if i.startswith(env + '/') and per[i]['gold_turn']]
    agg = defaultdict(lambda: [0, 0, 0, 0])
    for rid in ids:
        g = per[rid]['gold_turn']
        c = cands(rid)
        names = list(c)
        for k, v in c.items():
            if v is None: agg[k][3] += 1; continue
            agg[k][0] += (v == g); agg[k][1] += abs(v - g) <= 1; agg[k][2] += abs(v - g) <= 3
    for k in names:
        rows.append([env, k, len(ids), f'{100 * agg[k][0] / len(ids):.0f}%', f'{100 * agg[k][1] / len(ids):.0f}%', f'{100 * agg[k][2] / len(ids):.0f}%', agg[k][3]])
txt = '# First-symptom heuristics vs human label (turn units)\n\n' + md_table(['env', 'heuristic', 'n', 'exact', '±1', '±3', 'undefined (counted as miss)'], rows)
open(os.path.join(R, 'heuristics.md'), 'w').write(txt)
print(txt)
