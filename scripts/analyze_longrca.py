#!/usr/bin/env python3
"""Analyse LongRCA Bench (CLoud5-real/longrca-bench). Run: python3 -I analyze_longrca.py [EXAMPLE_ID]"""
import json, os, sys, glob, statistics, collections

DATA = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/longrca'
NOTES = '/dataDisk/home/thanhdo/failure-attribution-datasets/notes'
SCR = sys.argv[2] if len(sys.argv) > 2 else NOTES
SLUG = 'longrca'


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


# ---------------- load ----------------
full = {}
for f in sorted(glob.glob(f'{DATA}/data/full/*/*.json')):
    d = json.load(open(f, encoding='utf-8'))
    full[d['question_ID']] = d
mini = {}
for f in sorted(glob.glob(f'{DATA}/data/mini/*/*.json')):
    d = json.load(open(f, encoding='utf-8'))
    mini[d['question_ID']] = d
mini_subset = all(q in full for q in mini)
mini_identical = all(json.dumps(mini[q], sort_keys=True) == json.dumps(full[q], sort_keys=True) for q in mini if q in full)

recs = []
contig_ok = 0
for qid, d in full.items():
    h = d['history']
    n = len(h)
    steps = [x['step'] for x in h]
    if steps == list(range(n)): contig_ok += 1
    ms = int(d['mistake_step'])
    names = [x.get('name') for x in h]
    roles = [x.get('role') for x in h]
    chars = sum(len(str(x.get('content', ''))) for x in h)
    rec = dict(qid=qid, source=qid.split('__')[0], n=n, ms=ms, rel=ms / (n - 1) if n > 1 else 0.0,
               root_to_end=n - 1 - ms, agents=sorted(set(a for a in names if a)), n_agents=len(set(a for a in names if a)),
               roles=sorted(set(r for r in roles if r)), chars=chars, mistake_agent=d['mistake_agent'],
               sender_at_root=h[ms].get('name') if 0 <= ms < n else None, in_mini=qid in mini,
               handoff=any('->' in str(x.get('name', '')) for x in h))
    recs.append(rec)

sources = sorted(set(r['source'] for r in recs))
by_src = {s: [r for r in recs if r['source'] == s] for s in sources}

# ---------------- stats ----------------
stats = {
    'n_trajectories': len(recs),
    'n_mini': len(mini), 'mini_is_subset_of_full': mini_subset, 'mini_records_identical_to_full': mini_identical,
    'all_failed': True,
    'steps_contiguous_0_based_all': contig_ok == len(recs),
    'steps_per_traj': [r['n'] for r in recs],
    'error_step_rel_pos': [round(r['rel'], 4) for r in recs],
    'error_step_abs': [r['ms'] for r in recs],
    'root_to_end': [r['root_to_end'] for r in recs],
    'agents_per_traj': [r['n_agents'] for r in recs],
    'chars_per_traj': [r['chars'] for r in recs],
    'faulty_agent_counts': dict(collections.Counter(r['mistake_agent'] for r in recs).most_common()),
    'faulty_agent_counts_by_source': {s: dict(collections.Counter(r['mistake_agent'] for r in by_src[s]).most_common()) for s in sources},
    'category_counts': {},
    'source_benchmark_counts': {s: len(by_src[s]) for s in sources},
    'source_benchmark_counts_mini': dict(collections.Counter(q.split('__')[0] for q in mini)),
    'splits': {'full(test)': len(recs), 'mini(test)': len(mini)},
    'summary': {
        'steps': summ([r['n'] for r in recs]), 'chars': summ([r['chars'] for r in recs]),
        'error_rel_pos': summ([r['rel'] for r in recs]), 'error_abs': summ([r['ms'] for r in recs]),
        'root_to_end': summ([r['root_to_end'] for r in recs]), 'agents': summ([r['n_agents'] for r in recs]),
        'frac_root_to_end_gt_50': round(sum(r['root_to_end'] > 50 for r in recs) / len(recs), 4),
        'frac_root_to_end_gt_100': round(sum(r['root_to_end'] > 100 for r in recs) / len(recs), 4),
        'frac_root_to_end_gt_200': round(sum(r['root_to_end'] > 200 for r in recs) / len(recs), 4),
        'frac_sender_at_root_equals_mistake_agent': round(sum(r['sender_at_root'] == r['mistake_agent'] for r in recs) / len(recs), 4),
        'frac_with_handoff_markers': round(sum(r['handoff'] for r in recs) / len(recs), 4),
        'total_steps': sum(r['n'] for r in recs), 'total_chars': sum(r['chars'] for r in recs),
    },
    'per_source': {s: {'n': len(by_src[s]), 'steps': summ([r['n'] for r in by_src[s]]), 'chars': summ([r['chars'] for r in by_src[s]]),
                       'error_rel_pos': summ([r['rel'] for r in by_src[s]]), 'root_to_end': summ([r['root_to_end'] for r in by_src[s]]),
                       'agents': summ([r['n_agents'] for r in by_src[s]]),
                       'agent_name_set': sorted(set(a for r in by_src[s] for a in r['agents']))[:40],
                       'role_values': sorted(set(x for r in by_src[s] for x in r['roles']))} for s in sources},
    'steps_hist': hist([r['n'] for r in recs], [0, 25, 50, 100, 150, 200, 300, 400, 600]),
    'rel_pos_hist': hist([r['rel'] for r in recs], [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]),
}
json.dump(stats, open(f'{NOTES}/{SLUG}_stats.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- example ----------------
cands = sorted(recs, key=lambda r: (r['n'], r['chars']))[:12]
ex_id = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != '-' else cands[0]['qid']
ex = full[ex_id]
json.dump(ex, open(f'{NOTES}/{SLUG}_example.json', 'w'), indent=1, ensure_ascii=False)
ms = int(ex['mistake_step'])
norm_steps = []
for x in ex['history']:
    c, trimmed = trim_norm(x.get('content', ''))
    st = {'idx': x['step'], 'agent': x.get('name') or x.get('role'), 'content': c}
    if trimmed: st['trimmed'] = True
    norm_steps.append(st)
task = ex['history'][0].get('content') if ex['history'] else None
norm = {'dataset': SLUG, 'source_id': ex['question_ID'], 'task': task, 'ground_truth': None, 'final_output': ex['history'][-1].get('content') if ex['history'] else None,
        'steps': norm_steps,
        'annotation': {'faulty_agent': ex['mistake_agent'], 'faulty_step': ms, 'category': None, 'reason': ex['mistake_reason'],
                       'extra': {'source_benchmark': ex_id.split('__')[0], 'step_indexing': '0-based, field history[].step', 'in_longrca_mini': ex_id in mini}}}
json.dump(norm, open(f'{NOTES}/{SLUG}_example_norm.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- markdown summary ----------------
L = []
L.append(f"n_full={len(recs)} n_mini={len(mini)} mini_subset={mini_subset} mini_identical={mini_identical} contiguous0={contig_ok == len(recs)}")
L.append("\n### Candidate shortest trajectories\n")
for r in cands: L.append(f"- {r['qid']}: {r['n']} steps, {r['chars']} chars, agents={r['agents']}, faulty={r['mistake_agent']} @ {r['ms']}, in_mini={r['in_mini']}")
L.append("\n### Stats table\n")
L.append("| Quantity | Value |\n|---|---|")
S = stats['summary']
L.append(f"| Trajectories (all failed, natural) | {len(recs)} full / {len(mini)} mini |")
L.append(f"| Steps per trajectory | {fmt_summ(S['steps'])} |")
L.append(f"| Distinct agents (name) per trajectory | {fmt_summ(S['agents'])} |")
L.append(f"| Root-cause step (0-based) | {fmt_summ(S['error_abs'])} |")
L.append(f"| Relative root position step/(T-1) | {fmt_summ(S['error_rel_pos'])} |")
L.append(f"| Root-to-end distance T-1-r* | {fmt_summ(S['root_to_end'])} |")
L.append(f"| Frac. with >50 / >100 / >200 steps after root | {S['frac_root_to_end_gt_50']} / {S['frac_root_to_end_gt_100']} / {S['frac_root_to_end_gt_200']} |")
L.append(f"| Characters per trajectory | {fmt_summ(S['chars'])} |")
L.append(f"| Total steps / characters | {S['total_steps']} / {S['total_chars']} |")
L.append(f"| Sender of root step == responsible role | {S['frac_sender_at_root_equals_mistake_agent']} |")
L.append(f"| Trajectories with explicit handoff markers ('->' in name) | {S['frac_with_handoff_markers']} |")
L.append("\n### Per source\n")
L.append("| Source | N | N mini | steps mean/median/min/max | chars mean | rel. root pos mean | root-to-end median | agents mean | agent names |\n|---|---|---|---|---|---|---|---|---|")
for s in sources:
    p = stats['per_source'][s]
    L.append(f"| {s} | {p['n']} | {stats['source_benchmark_counts_mini'].get(s,0)} | {p['steps']['mean']}/{p['steps']['median']}/{p['steps']['min']}/{p['steps']['max']} | {p['chars']['mean']} | {p['error_rel_pos']['mean']} | {p['root_to_end']['median']} | {p['agents']['mean']} | {', '.join(p['agent_name_set'][:12])} |")
L.append("\n### Steps histogram\n")
L.append("| bin | count |\n|---|---|")
for k, v in stats['steps_hist'].items(): L.append(f"| {k} | {v} |")
L.append("\n### Relative root position histogram\n")
L.append("| bin | count |\n|---|---|")
for k, v in stats['rel_pos_hist'].items(): L.append(f"| {k} | {v} |")
L.append("\n### Faulty agent (responsible role) distribution, overall top 20\n")
L.append("| role | count |\n|---|---|")
for k, v in list(stats['faulty_agent_counts'].items())[:20]: L.append(f"| {k} | {v} |")
L.append("\n### Faulty role by source\n")
for s in sources:
    L.append(f"- **{s}**: " + ', '.join(f"{k} ({v})" for k, v in list(stats['faulty_agent_counts_by_source'][s].items())[:10]))
L.append(f"\n### Example {ex_id} ({len(ex['history'])} steps; faulty agent {ex['mistake_agent']}, step {ms})\n")
for x in ex['history']:
    mark = '  ⟵ ANNOTATED ERROR STEP' if x['step'] == ms else ''
    L.append(f"**[{x['step']}] {x.get('name')} (role={x.get('role')}){mark}**\n\n```\n{trunc(x.get('content',''))}\n```\n")
L.append(f"**Annotation**: mistake_agent = `{ex['mistake_agent']}`, mistake_step = `{ms}`\n\nmistake_reason: {ex['mistake_reason']}\n")
open(f'{SCR}/{SLUG}_summary.md', 'w').write('\n'.join(L))
print('\n'.join(L[:60]))
print('... written', f'{SCR}/{SLUG}_summary.md')
