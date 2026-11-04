#!/usr/bin/env python3
"""Generic all-at-once attribution baseline on any loader.

Usage: python3 -I baseline/all_at_once.py <slug> [--n 40] [--seed 0] [--ids id1,id2] [--no-gt] [--no-think]
       [--variant std|inventory] [--mask-last K] [--tag TAG] [--workers 8] [--max-steps N] [--subset S]
Writes results/<slug>/all_at_once_<variant>[_<tag>].jsonl (one line per record with prediction, raw output,
reasoning and correctness) and prints metrics. Cached in cache/llm_cache.sqlite.

Variants:
  std       : predict (agent, step, reason) as JSON.
  inventory : first list EVERY step that contains a mistake (with a 1-line reason each), then name the
              decisive (earliest failure-causing) one. Lets us see symptom-vs-cause confusion.
"""
import argparse
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, append_jsonl, md_table  # noqa: E402
from common.llm import chat_json_many  # noqa: E402
from common.render import render_steps, render_task  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402

SYSTEM = ('You are an expert at debugging LLM agent systems. You will read the full execution trajectory of an '
          'agent system that FAILED its task and must identify the root cause: the earliest step at which an agent '
          'made the decisive mistake, i.e. the step such that, had it been done correctly, the task would most '
          'likely have succeeded. Later steps that merely inherit or repeat the consequences of that mistake are '
          'symptoms, not the cause.')

PROMPT_STD = ('{task}\n\nTRAJECTORY (steps are numbered; the number in [step N] is the step index you must report):\n\n'
              '{traj}\n\nAnswer with a single JSON object and nothing else:\n'
              '{{"agent": "<name of the agent that made the decisive mistake, exactly as written in the trajectory>", '
              '"step": <integer step index>, "reason": "<one or two sentences>"}}')

PROMPT_INV = ('{task}\n\nTRAJECTORY (steps are numbered; the number in [step N] is the step index you must report):\n\n'
              '{traj}\n\nFirst, list EVERY step that contains a mistake of any kind (wrong fact, wrong tool use, '
              'wrong reasoning, ignoring evidence, premature stop, ...). Then decide which one is the decisive root '
              'cause (earliest step whose correction would have led to success).\n'
              'Answer with a single JSON object and nothing else:\n'
              '{{"mistakes": [{{"step": <int>, "agent": "<name>", "what": "<one line>"}}, ...], '
              '"agent": "<decisive agent>", "step": <decisive step index>, "reason": "<one or two sentences>"}}')


def norm_agent(a):
    if a is None:
        return ''
    a = re.sub(r'\s*\(.*\)$', '', str(a)).strip().lower()
    return re.sub(r'[^a-z0-9]', '', a)


def score(rec, pred):
    gold = error_step(rec)
    es = set(rec['labels']['error_steps'])
    ps = pred.get('step') if pred else None
    try:
        ps = int(ps)
    except Exception:  # noqa: BLE001
        ps = None
    ga = norm_agent(rec['labels']['error_agent'])
    pa = norm_agent(pred.get('agent') if pred else None)
    out = {'gold_step': gold, 'pred_step': ps, 'gold_agent': rec['labels']['error_agent'], 'pred_agent': pred.get('agent') if pred else None,
           'agent_ok': bool(ga) and (pa == ga or (pa and ga and (pa in ga or ga in pa))),
           'step_exact': ps is not None and gold is not None and ps == gold,
           'step_in_set': ps is not None and ps in es,
           'step_dist': (ps - gold) if (ps is not None and gold is not None) else None}
    for k in (1, 3, 5):
        out[f'step_within_{k}'] = ps is not None and gold is not None and abs(ps - gold) <= k
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--n', type=int, default=40)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--ids', default=None, help='comma-separated record ids (overrides --n)')
    ap.add_argument('--subset', default=None)
    ap.add_argument('--no-gt', action='store_true')
    ap.add_argument('--no-think', action='store_true')
    ap.add_argument('--variant', default='std', choices=['std', 'inventory'])
    ap.add_argument('--mask-last', type=int, default=0)
    ap.add_argument('--max-steps', type=int, default=None, help='skip records longer than this')
    ap.add_argument('--tag', default='')
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--budget-tokens', type=int, default=120000)
    ap.add_argument('--max-tokens', type=int, default=16384)
    args = ap.parse_args()

    recs = load(args.slug)
    if args.subset:
        recs = [r for r in recs if r['subset'] == args.subset]
    if args.max_steps:
        recs = [r for r in recs if len(r['steps']) <= args.max_steps]
    recs = [r for r in recs if r['labels']['error_steps']]
    if args.ids:
        want = set(args.ids.split(','))
        recs = [r for r in recs if r['id'] in want]
    else:
        random.Random(args.seed).shuffle(recs)
        recs = recs[:args.n]
    print(f'{len(recs)} records', file=sys.stderr)

    msgs, rendered = [], []
    for r in recs:
        traj, used = render_steps(r, total_cap_tokens=args.budget_tokens, mask_last=args.mask_last)
        tmpl = PROMPT_STD if args.variant == 'std' else PROMPT_INV
        user = tmpl.format(task=render_task(r, with_gt=not args.no_gt), traj=traj)
        msgs.append([{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}])
        rendered.append({'n_rendered': len(used), 'prompt_chars': len(user)})
    outs = chat_json_many(msgs, workers=args.workers, max_tokens=args.max_tokens, think=not args.no_think,
                          tag=f'aao_{args.variant}')

    name = f"all_at_once_{args.variant}" + (f'_{args.tag}' if args.tag else '') + ('_nogt' if args.no_gt else '') + ('_nothink' if args.no_think else '')
    path = os.path.join(RESULTS, args.slug, name + '.jsonl')
    if os.path.exists(path):
        os.remove(path)
    rows = []
    for r, (pred, o), m in zip(recs, outs, rendered):
        pred = pred or {}
        sc = score(r, pred)
        row = {'id': r['id'], 'subset': r['subset'], 'n_steps': len(r['steps']), **m, 'pred': pred, **sc,
               'raw': o['content'], 'reasoning': o['reasoning'][:20000], 'usage': o['usage'], 'finish_reason': o.get('finish_reason'), 'fallback': o.get('fallback'), 'error': o.get('error'),
               'gold_reason': r['labels']['reason'], 'gold_categories': r['labels']['categories']}
        rows.append(row)
        append_jsonl(path, row)
    n = len(rows)
    keys = ['agent_ok', 'step_exact', 'step_in_set', 'step_within_1', 'step_within_3', 'step_within_5']
    tbl = [[k, sum(1 for x in rows if x[k]), f'{100 * sum(1 for x in rows if x[k]) / max(1, n):.1f}'] for k in keys]
    parse_fail = sum(1 for x in rows if x['pred_step'] is None)
    print(md_table(['metric', 'n', '%'], tbl))
    dists = [x['step_dist'] for x in rows if x['step_dist'] is not None]
    late = sum(1 for d in dists if d > 0)
    early = sum(1 for d in dists if d < 0)
    print(f'\nn={n} parse_fail={parse_fail} pred later than gold: {late}, earlier: {early}, exact: {len(dists) - late - early}')
    print('wrote', path)


if __name__ == '__main__':
    main()
