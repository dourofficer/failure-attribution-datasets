#!/usr/bin/env python3
"""Analyse AgenTracer data release v1.0.0 (TracerTraj). Run: python3 -I analyze_tracertraj.py [EXAMPLE_ID] [SCRATCH_DIR]"""
import json, os, sys, glob, statistics, collections

DATA = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/tracertraj/extracted/agentracer-data-v1.0.0'
NOTES = '/dataDisk/home/thanhdo/failure-attribution-datasets/notes'
SCR = sys.argv[2] if len(sys.argv) > 2 else NOTES
SLUG = 'tracertraj'


def summ(xs):
    xs = sorted(xs); n = len(xs)
    if not n: return {}
    q = lambda p: xs[min(n - 1, int(p * n))]
    return {'n': n, 'mean': round(statistics.mean(xs), 2), 'median': statistics.median(xs), 'min': xs[0], 'max': xs[-1], 'p10': q(0.1), 'p90': q(0.9)}


def hist(xs, edges):
    out = collections.OrderedDict()
    for i in range(len(edges) - 1):
        out[f'[{edges[i]},{edges[i+1]})'] = sum(1 for x in xs if edges[i] <= x < edges[i + 1])
    out[f'>={edges[-1]}'] = sum(1 for x in xs if x >= edges[-1])
    return out


def trunc(s, n=500):
    s = str(s).replace('\r', '')
    return s if len(s) <= n else s[:n] + ' […]'


def trim_norm(s):
    s = str(s)
    return (s[:3000] + ' […] ' + s[-500:], True) if len(s) > 4000 else (s, False)


def fmt_summ(d):
    return f"mean {d['mean']}, median {d['median']}, min {d['min']}, max {d['max']}, p10 {d['p10']}, p90 {d['p90']}"


def agent_of(x):
    return x.get('name') or x.get('role')


recs, raw = [], {}
for dom in ['agentic', 'coding', 'math']:
    for sp in ['train', 'test']:
        with open(f'{DATA}/{dom}/{sp}.jsonl', encoding='utf-8') as fh:
            for line in fh:
                d = json.loads(line)
                h = d['history']; n = len(h)
                first = h[0]['step']
                ms = int(d['mistake_step'])
                pos = next((i for i, x in enumerate(h) if x['step'] == ms), None)
                agents = [agent_of(x) for x in h]
                chars = sum(len(str(x.get('content', ''))) for x in h)
                key = f"{dom}/{sp}/{d['question_ID']}"
                raw[key] = d
                recs.append(dict(key=key, qid=d['question_ID'], domain=dom, split=sp, n=n, first=first, ms=ms, pos=pos,
                                 rel=(pos / (n - 1)) if (pos is not None and n > 1) else (0.0 if pos is not None else None),
                                 agents=sorted(set(a for a in agents if a)), n_agents=len(set(a for a in agents if a)), chars=chars,
                                 mistake_agent=d['mistake_agent'], error_source=d.get('error_source'),
                                 has_reason='mistake_reason' in d, has_gt='ground_truth' in d,
                                 sender_at_root=agent_of(h[pos]) if pos is not None else None,
                                 generic_assistant_only=set(a for a in agents if a) <= {'assistant', 'user', 'system'}))

doms = ['agentic', 'coding', 'math']
groups = {f'{d}/{s}': [r for r in recs if r['domain'] == d and r['split'] == s] for d in doms for s in ['train', 'test']}
test = [r for r in recs if r['split'] == 'test']
qid_dup = collections.Counter(r['qid'] for r in recs)
train_ids = set(r['qid'] for r in recs if r['split'] == 'train'); test_ids = set(r['qid'] for r in recs if r['split'] == 'test')


def block(rs):
    return {'n': len(rs), 'steps': summ([r['n'] for r in rs]), 'chars': summ([r['chars'] for r in rs]), 'agents': summ([r['n_agents'] for r in rs]),
            'error_rel_pos': summ([r['rel'] for r in rs if r['rel'] is not None]), 'error_abs_index': summ([r['pos'] for r in rs if r['pos'] is not None]),
            'faulty_agent_top': dict(collections.Counter(r['mistake_agent'] for r in rs).most_common(15)),
            'error_source_counts': dict(collections.Counter(r['error_source'] for r in rs)),
            'frac_sender_at_root_equals_mistake_agent': round(sum(r['sender_at_root'] == r['mistake_agent'] for r in rs) / len(rs), 4) if rs else None,
            'frac_generic_assistant_label_only': round(sum(r['generic_assistant_only'] for r in rs) / len(rs), 4) if rs else None,
            'first_step_index_values': dict(collections.Counter(r['first'] for r in rs)),
            'has_mistake_reason': sum(r['has_reason'] for r in rs), 'has_ground_truth': sum(r['has_gt'] for r in rs)}


stats = {
    'n_trajectories': len(recs), 'n_test': len(test), 'n_train': len(recs) - len(test),
    'all_failed': True,
    'steps_per_traj': [r['n'] for r in recs], 'error_step_rel_pos': [round(r['rel'], 4) for r in recs if r['rel'] is not None],
    'agents_per_traj': [r['n_agents'] for r in recs], 'chars_per_traj': [r['chars'] for r in recs],
    'faulty_agent_counts': dict(collections.Counter(r['mistake_agent'] for r in recs).most_common()),
    'category_counts': dict(collections.Counter(r['error_source'] or 'n/a (coding/math: no error_source field)' for r in recs)),
    'source_benchmark_counts': {d: sum(1 for r in recs if r['domain'] == d) for d in doms},
    'splits': {k: len(v) for k, v in groups.items()},
    'summary_all': block(recs), 'summary_test': block(test),
    'per_group': {k: block(v) for k, v in groups.items()},
    'steps_hist': hist([r['n'] for r in recs], [0, 5, 10, 15, 20, 30, 40, 60, 100]),
    'steps_hist_test': hist([r['n'] for r in test], [0, 5, 10, 15, 20, 30, 40, 60, 100]),
    'rel_pos_hist': hist([r['rel'] for r in recs if r['rel'] is not None], [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]),
    'duplicate_question_ids': sum(1 for v in qid_dup.values() if v > 1), 'train_test_qid_overlap': len(train_ids & test_ids),
    'mistake_step_always_in_history': all(r['pos'] is not None for r in recs),
}
json.dump(stats, open(f'{NOTES}/{SLUG}_stats.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- example ----------------
cands = [r for r in test if r['n'] <= 15 and r['n_agents'] >= 2 and r['chars'] / r['n'] <= 2500 and not r['generic_assistant_only']]
cands.sort(key=lambda r: (-(r['has_reason']), -(r['n_agents'] >= 3), r['chars']))
ex_key = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != '-' else (cands[0]['key'] if cands else sorted(test, key=lambda r: r['n'])[0]['key'])
ex = raw[ex_key]; exr = next(r for r in recs if r['key'] == ex_key)
json.dump(ex, open(f'{NOTES}/{SLUG}_example.json', 'w'), indent=1, ensure_ascii=False)
ms = int(ex['mistake_step'])
norm_steps = []
for x in ex['history']:
    c, trimmed = trim_norm(x.get('content', ''))
    st = {'idx': x['step'], 'agent': agent_of(x), 'content': c}
    if trimmed: st['trimmed'] = True
    norm_steps.append(st)
norm = {'dataset': SLUG, 'source_id': ex['question_ID'], 'task': ex.get('question'), 'ground_truth': ex.get('ground_truth'),
        'final_output': ex['history'][-1].get('content') if ex['history'] else None, 'steps': norm_steps,
        'annotation': {'faulty_agent': ex['mistake_agent'], 'faulty_step': ms, 'category': ex.get('error_source'),
                       'reason': ex.get('mistake_reason'),
                       'extra': {'domain': exr['domain'], 'split': exr['split'], 'file': ex_key.rsplit('/', 1)[0] + '.jsonl',
                                 'step_indexing': f"field history[].step, first step = {exr['first']}", 'mistake_step_raw_type': type(ex['mistake_step']).__name__}}}
json.dump(norm, open(f'{NOTES}/{SLUG}_example_norm.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- markdown ----------------
L = [f"n={len(recs)} test={len(test)} dup_qids={stats['duplicate_question_ids']} train_test_overlap={stats['train_test_qid_overlap']} ms_in_history={stats['mistake_step_always_in_history']}"]
L.append("\n### Example candidates (test, <=15 steps, >=2 agents)\n")
for r in cands[:15]: L.append(f"- {r['key']}: {r['n']} steps, {r['chars']} chars, agents={r['agents']}, faulty={r['mistake_agent']} @ step {r['ms']}, reason={r['has_reason']}")
L.append("\n### Split table\n")
L.append("| Domain/split | N | steps mean/median/min/max | chars mean | agents mean | rel. error pos mean | error_source | sender@root==agent | generic 'assistant' only |\n|---|---|---|---|---|---|---|---|---|")
for k, v in stats['per_group'].items():
    b = v; L.append(f"| {k} | {b['n']} | {b['steps']['mean']}/{b['steps']['median']}/{b['steps']['min']}/{b['steps']['max']} | {b['chars']['mean']} | {b['agents']['mean']} | {b['error_rel_pos']['mean']} | {b['error_source_counts']} | {b['frac_sender_at_root_equals_mistake_agent']} | {b['frac_generic_assistant_label_only']} |")
b = stats['summary_all']; L.append(f"| ALL | {b['n']} | {b['steps']['mean']}/{b['steps']['median']}/{b['steps']['min']}/{b['steps']['max']} | {b['chars']['mean']} | {b['agents']['mean']} | {b['error_rel_pos']['mean']} | {b['error_source_counts']} | {b['frac_sender_at_root_equals_mistake_agent']} | {b['frac_generic_assistant_label_only']} |")
L.append("\n### Steps histogram (all / test)\n")
L.append("| bin | all | test |\n|---|---|---|")
for k in stats['steps_hist']: L.append(f"| {k} | {stats['steps_hist'][k]} | {stats['steps_hist_test'][k]} |")
L.append("\n### Relative error position histogram (all)\n")
L.append("| bin | count |\n|---|---|")
for k, v in stats['rel_pos_hist'].items(): L.append(f"| {k} | {v} |")
L.append("\n### Faulty agent top per domain\n")
for d in doms:
    rs = [r for r in recs if r['domain'] == d]
    L.append(f"- **{d}**: " + ', '.join(f"{k} ({v})" for k, v in collections.Counter(r['mistake_agent'] for r in rs).most_common(12)))
L.append(f"\n### Example {ex_key} ({len(ex['history'])} steps; faulty {ex['mistake_agent']} @ step {ms})\n")
L.append(f"Question: {trunc(ex.get('question'), 800)}\n")
for x in ex['history']:
    mark = '  ⟵ ANNOTATED ERROR STEP' if x['step'] == ms else ''
    L.append(f"**[{x['step']}] {agent_of(x)} (role={x.get('role')}){mark}**\n\n```\n{trunc(x.get('content',''))}\n```\n")
L.append(f"**Annotation**: mistake_agent=`{ex['mistake_agent']}`, mistake_step=`{ms}`, error_source=`{ex.get('error_source')}`\n\nmistake_reason: {ex.get('mistake_reason')}\n\nground_truth: {trunc(ex.get('ground_truth'), 800)}\n")
open(f'{SCR}/{SLUG}_summary.md', 'w').write('\n'.join(L))
print('\n'.join(L[:45])); print('... written', f'{SCR}/{SLUG}_summary.md')
