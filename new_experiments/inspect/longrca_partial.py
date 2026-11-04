#!/usr/bin/env python3
"""Read partial results of the running longrca baseline (60 records, seed 0) and prefix probe (10 records) straight from the
LLM cache, so analysis can start before the jobs finish. Writes results/longrca/all_at_once_std_partial.jsonl and
results/longrca/prefix_probe_partial.jsonl (same row format as the official scripts) and prints metrics."""
import importlib.util
import json
import os
import random
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import llm  # noqa: E402
from common.util import RESULTS, md_table  # noqa: E402
from common.render import render_steps, render_task  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ao = mod(os.path.join(HERE, '..', 'baseline', 'all_at_once.py'), 'ao')
pp = mod(os.path.join(HERE, 'prefix_probe.py'), 'pp')
con = sqlite3.connect(llm.CACHE_PATH)


def key(messages, max_tokens, think, tag):
    payload = {'model': llm.MODEL, 'messages': messages, 'max_tokens': max_tokens, 'temperature': 0.0, 'top_p': 1.0, 'seed': 0,
               'chat_template_kwargs': {'enable_thinking': bool(think)}}
    return llm._key({**payload, 'tag': tag})


def cached(messages, max_tokens, think, tag):
    row = con.execute('SELECT response FROM cache WHERE key=?', (key(messages, max_tokens, think, tag),)).fetchone()
    return json.loads(row[0]) if row else None


def main():
    recs = [r for r in load('longrca') if r['labels']['error_steps']]
    sel = list(recs)
    random.Random(0).shuffle(sel)
    sel = sel[:60]
    rows = []
    for r in sel:
        traj, used = render_steps(r, total_cap_tokens=150000, mask_last=0)
        user = ao.PROMPT_STD.format(task=render_task(r, with_gt=True), traj=traj)
        m = [{'role': 'system', 'content': ao.SYSTEM}, {'role': 'user', 'content': user}]
        o = cached(m, 20000, True, 'aao_std')
        if o is None:
            continue
        pred = llm.extract_json(o['content']) or {}
        sc = ao.score(r, pred)
        rows.append({'id': r['id'], 'subset': r['subset'], 'n_steps': len(r['steps']), 'n_rendered': len(used), 'prompt_chars': len(user), 'pred': pred, **sc,
                     'raw': o['content'], 'reasoning': (o.get('reasoning') or '')[:20000], 'usage': o.get('usage'), 'finish_reason': o.get('finish_reason'),
                     'fallback': o.get('fallback'), 'gold_reason': r['labels']['reason'], 'gold_categories': r['labels']['categories']})
    path = os.path.join(RESULTS, 'longrca', 'all_at_once_std_partial.jsonl')
    with open(path, 'w') as fh:
        for x in rows:
            fh.write(json.dumps(x, ensure_ascii=False) + '\n')
    n = len(rows)
    print(f'baseline: {n}/60 cached')
    if n:
        keys = ['agent_ok', 'step_exact', 'step_within_1', 'step_within_3', 'step_within_5']
        print(md_table(['metric', 'n', '%'], [[k, sum(1 for x in rows if x[k]), f'{100 * sum(1 for x in rows if x[k]) / n:.1f}'] for k in keys]))
        d = [x['step_dist'] for x in rows if x['step_dist'] is not None]
        print('later:', sum(1 for v in d if v > 0), 'earlier:', sum(1 for v in d if v < 0), 'exact:', sum(1 for v in d if v == 0), 'parse_fail:', n - len(d))
    # probe
    pr = [r for r in recs if len(r['steps']) <= 80]
    random.Random(0).shuffle(pr)
    pr = pr[:10]
    per = {}
    tot = hit = 0
    for r in pr:
        g = error_step(r)
        for s in r['steps']:
            if s['role'] != 'agent' or abs(s['idx'] - g) > 5:
                continue
            prefix = {**r, 'steps': r['steps'][:s['idx'] + 1]}
            traj, _ = render_steps(prefix, total_cap_tokens=100000)
            user = pp.PROMPT.format(task=render_task(r, with_gt=False), traj=traj, k=s['idx'], agent=s['agent'])
            m = [{'role': 'system', 'content': pp.SYSTEM}, {'role': 'user', 'content': user}]
            tot += 1
            o = cached(m, 8192, True, 'prefix_probe')
            if o is None:
                continue
            hit += 1
            p = llm.extract_json(o['content']) or {}
            rec = per.setdefault(r['id'], {'id': r['id'], 'subset': r['subset'], 'n_steps': len(r['steps']), 'gold': g, 'gold_agent': r['labels']['error_agent'], 'scores': {}})
            try:
                conf = float(p.get('confidence', 0))
            except Exception:  # noqa
                conf = 0.0
            rec['scores'][s['idx']] = {'mistake': bool(p.get('mistake')), 'conf': conf, 'what': p.get('what'), 'agent': s['agent']}
    print(f'probe: {hit}/{tot} cached over {len(pr)} records')
    out = []
    for rec in per.values():
        sc = rec['scores']; g = rec['gold']
        flagged = sorted(k for k, v in sc.items() if v['mistake'])
        rec.update(gold_probed=g in sc, gold_flagged=bool(sc.get(g, {}).get('mistake')), gold_conf=sc.get(g, {}).get('conf'),
                   n_flagged_before=sum(1 for k in flagged if k < g), n_flagged_after=sum(1 for k in flagged if k > g),
                   n_probed_before=sum(1 for k in sc if k < g), n_probed_after=sum(1 for k in sc if k > g),
                   earliest_flagged=flagged[0] if flagged else None)
        rec['scores'] = {str(k): v for k, v in sc.items()}
        out.append(rec)
    with open(os.path.join(RESULTS, 'longrca', 'prefix_probe_partial.jsonl'), 'w') as fh:
        for x in out:
            fh.write(json.dumps(x, ensure_ascii=False) + '\n')
    gp = [x for x in out if x['gold_probed']]
    if gp:
        print('gold probed', len(gp), 'gold flagged', sum(x['gold_flagged'] for x in gp), 'flags before', sum(x['n_flagged_before'] for x in out), '/', sum(x['n_probed_before'] for x in out),
              'flags after', sum(x['n_flagged_after'] for x in out), '/', sum(x['n_probed_after'] for x in out))
        for x in out:
            print(' ', x['id'], 'gold', x['gold'], 'flagged', x['gold_flagged'], 'conf', x['gold_conf'], {k: (v['mistake'], v['conf']) for k, v in x['scores'].items()})


if __name__ == '__main__':
    main()
