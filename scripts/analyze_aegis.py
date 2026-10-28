#!/usr/bin/env python3
"""Analyse AEGIS (Fancylalala/AEGIS). Run: python3 -I analyze_aegis.py [EXAMPLE_ID] [SCRATCH_DIR]"""
import json, os, sys, statistics, collections

DATA = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/aegis'
NOTES = '/dataDisk/home/thanhdo/failure-attribution-datasets/notes'
SCR = sys.argv[2] if len(sys.argv) > 2 else NOTES
SLUG = 'aegis'
FILES = {'test(Aegis-Bench)': 'Aegis-Bench/test.jsonl', 'train': 'Aegis-Training/train.jsonl', 'val': 'Aegis-Training/val.jsonl'}


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


recs = []; raw = {}
for split, rel in FILES.items():
    with open(f'{DATA}/{rel}', encoding='utf-8') as fh:
        for line in fh:
            d = json.loads(line)
            h = d['input']['conversation_history']; n = len(h)
            md = d['metadata']
            fa = d['output']['faulty_agents']
            inj = d['ground_truth'].get('injected_agents', [])
            inj_steps = [i for i, x in enumerate(h) if x.get('is_injected')]
            has_marker = any('is_injected' in x for x in h)
            agents = [x.get('agent_name') for x in h]
            chars = sum(len(str(x.get('content', ''))) for x in h)
            r = dict(id=d['id'], split=split, framework=md.get('framework'), benchmark=md.get('benchmark'), model=md.get('model'), task_type=md.get('task_type'),
                     n=n, agents=sorted(set(a for a in agents if a)), n_agents=len(set(a for a in agents if a)), meta_num_agents=md.get('num_agents'),
                     meta_num_injected=md.get('num_injected_agents'), n_pairs=len(fa), n_faulty_agents=len(set(x['agent_name'] for x in fa)),
                     faulty_names=sorted(set(x['agent_name'] for x in fa)), error_types=[x['error_type'] for x in fa], strategies=[x.get('injection_strategy') for x in fa],
                     chars=chars, has_marker=has_marker, inj_steps=inj_steps, first_inj_rel=(inj_steps[0] / (n - 1)) if inj_steps and n > 1 else None,
                     inj_success=d['ground_truth'].get('is_injection_successful'), faulty_eq_injected=[(x['agent_name'], x['error_type']) for x in fa] == [(x['agent_name'], x['error_type']) for x in inj],
                     faulty_in_history=all(x['agent_name'] in set(agents) for x in fa), steps_1based=(h[0].get('step') == 1 if h else None),
                     phases=sorted(set(str(x.get('phase')) for x in h)), has_final=bool(d['input'].get('final_output')), has_answer=bool(d['ground_truth'].get('correct_answer')),
                     malicious_desc_nonempty=sum(1 for x in inj if x.get('malicious_action_description')))
            raw[d['id']] = d; recs.append(r)

splits = list(FILES)
fws = sorted(set(r['framework'] for r in recs)); bms = sorted(set(r['benchmark'] for r in recs))


def block(rs):
    return {'n': len(rs), 'steps': summ([r['n'] for r in rs]), 'chars': summ([r['chars'] for r in rs]), 'agents': summ([r['n_agents'] for r in rs]),
            'pairs_per_traj': summ([r['n_pairs'] for r in rs]), 'faulty_agents_per_traj': summ([r['n_faulty_agents'] for r in rs]),
            'frac_with_is_injected_marker': round(sum(r['has_marker'] for r in rs) / len(rs), 4) if rs else None,
            'first_injected_step_rel_pos': summ([r['first_inj_rel'] for r in rs if r['first_inj_rel'] is not None]),
            'error_type_counts': dict(collections.Counter(e for r in rs for e in r['error_types']).most_common()),
            'strategy_counts': dict(collections.Counter(s for r in rs for s in r['strategies']).most_common()),
            'framework_counts': dict(collections.Counter(r['framework'] for r in rs).most_common()),
            'benchmark_counts': dict(collections.Counter(r['benchmark'] for r in rs).most_common()),
            'model_counts': dict(collections.Counter(r['model'] for r in rs).most_common()),
            'faulty_agent_name_top': dict(collections.Counter(a for r in rs for a in r['faulty_names']).most_common(25))}


test = [r for r in recs if r['split'].startswith('test')]
stats = {
    'n_trajectories': len(recs), 'all_failed': True,
    'steps_per_traj': [r['n'] for r in recs], 'error_step_rel_pos': [round(r['first_inj_rel'], 4) for r in recs if r['first_inj_rel'] is not None],
    'error_step_rel_pos_note': 'only for records whose conversation items carry is_injected=true; first injected step index/(T-1)',
    'agents_per_traj': [r['n_agents'] for r in recs], 'chars_per_traj': [r['chars'] for r in recs],
    'faulty_agent_counts': dict(collections.Counter(a for r in recs for a in r['faulty_names']).most_common()),
    'category_counts': dict(collections.Counter(e for r in recs for e in r['error_types']).most_common()),
    'source_benchmark_counts': dict(collections.Counter(r['benchmark'] for r in recs).most_common()),
    'framework_counts': dict(collections.Counter(r['framework'] for r in recs).most_common()),
    'splits': {s: sum(1 for r in recs if r['split'] == s) for s in splits},
    'split_by_benchmark': {s: dict(collections.Counter(r['benchmark'] for r in recs if r['split'] == s)) for s in splits},
    'split_by_framework': {s: dict(collections.Counter(r['framework'] for r in recs if r['split'] == s)) for s in splits},
    'framework_x_benchmark': {f: dict(collections.Counter(r['benchmark'] for r in recs if r['framework'] == f)) for f in fws},
    'summary_all': block(recs), 'summary_test': block(test),
    'per_framework': {f: block([r for r in recs if r['framework'] == f]) for f in fws},
    'per_benchmark': {b: block([r for r in recs if r['benchmark'] == b]) for b in bms},
    'steps_hist': hist([r['n'] for r in recs], [0, 5, 10, 15, 20, 30, 40, 60, 100]),
    'rel_pos_hist': hist([r['first_inj_rel'] for r in recs if r['first_inj_rel'] is not None], [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]),
    'checks': {'faulty_agents_equals_injected_agents': round(sum(r['faulty_eq_injected'] for r in recs) / len(recs), 4),
               'faulty_agent_name_appears_in_history': round(sum(r['faulty_in_history'] for r in recs) / len(recs), 4),
               'is_injection_successful_true': round(sum(bool(r['inj_success']) for r in recs) / len(recs), 4),
               'steps_1based': round(sum(bool(r['steps_1based']) for r in recs) / len(recs), 4),
               'has_final_output': round(sum(r['has_final'] for r in recs) / len(recs), 4), 'has_correct_answer': round(sum(r['has_answer'] for r in recs) / len(recs), 4),
               'meta_num_injected_equals_n_pairs': round(sum(r['meta_num_injected'] == r['n_pairs'] for r in recs) / len(recs), 4),
               'malicious_action_description_nonempty_records': sum(r['malicious_desc_nonempty'] > 0 for r in recs),
               'duplicate_ids': sum(1 for v in collections.Counter(r['id'] for r in recs).values() if v > 1),
               'n_pairs_hist': dict(collections.Counter(r['n_pairs'] for r in recs)), 'n_faulty_agents_hist': dict(collections.Counter(r['n_faulty_agents'] for r in recs)),
               'phases_values': sorted(set(p for r in recs for p in r['phases']))[:30]},
}
json.dump(stats, open(f'{NOTES}/{SLUG}_stats.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- example ----------------
cands = [r for r in test if r['n'] <= 15 and r['chars'] / r['n'] <= 2500 and r['n_agents'] >= 2]
cands.sort(key=lambda r: (-r['has_marker'], r['n_pairs'], r['chars']))
ex_id = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != '-' else cands[0]['id']
ex = raw[ex_id]; exr = next(r for r in recs if r['id'] == ex_id)
json.dump(ex, open(f'{NOTES}/{SLUG}_example.json', 'w'), indent=1, ensure_ascii=False)
h = ex['input']['conversation_history']
inj_idx = [x['step'] for x in h if x.get('is_injected')]
norm_steps = []
for x in h:
    c, trimmed = trim_norm(x.get('content', ''))
    st = {'idx': x['step'], 'agent': x.get('agent_name'), 'content': c}
    if x.get('phase') is not None: st['phase'] = x.get('phase')
    if x.get('is_injected'): st['is_injected'] = True
    if trimmed: st['trimmed'] = True
    norm_steps.append(st)
fa = ex['output']['faulty_agents']
norm = {'dataset': SLUG, 'source_id': ex['id'], 'task': ex['input']['query'], 'ground_truth': ex['ground_truth'].get('correct_answer'),
        'final_output': ex['input'].get('final_output'), 'steps': norm_steps,
        'annotation': {'faulty_agent': sorted(set(x['agent_name'] for x in fa)) if len(set(x['agent_name'] for x in fa)) > 1 else fa[0]['agent_name'],
                       'faulty_step': inj_idx if inj_idx else None, 'category': [x['error_type'] for x in fa] if len(fa) > 1 else fa[0]['error_type'],
                       'reason': '; '.join(x.get('malicious_action_description') for x in ex['ground_truth'].get('injected_agents', []) if x.get('malicious_action_description')) or None,
                       'extra': {'faulty_agents_pairs': fa, 'injected_agents': ex['ground_truth'].get('injected_agents'), 'injection_strategies': sorted(set(x.get('injection_strategy') for x in fa)),
                                 'metadata': ex['metadata'], 'is_injection_successful': ex['ground_truth'].get('is_injection_successful'),
                                 'step_indexing': '1-based field conversation_history[].step', 'note': 'AEGIS labels are agent+error-mode level; step-level label only via is_injected markers where present'}}}
json.dump(norm, open(f'{NOTES}/{SLUG}_example_norm.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- markdown ----------------
def fs(d): return f"mean {d['mean']}, median {d['median']}, min {d['min']}, max {d['max']}, p10 {d['p10']}, p90 {d['p90']}" if d else 'n/a'
L = [f"n={len(recs)} splits={stats['splits']} checks={json.dumps(stats['checks'])}"]
L.append("\n### Example candidates (test, <=15 steps)\n")
for r in cands[:12]: L.append(f"- {r['id']}: {r['framework']}/{r['benchmark']} {r['n']} steps, {r['chars']} chars, agents={r['agents']}, faulty={[(x) for x in zip(r['faulty_names'])]} types={r['error_types']} marker={r['has_marker']} inj_steps={r['inj_steps']}")
S = stats['summary_all']; T = stats['summary_test']
L.append("\n### Overall table\n")
L.append("| Quantity | All (9,533) | Test / Aegis-Bench |\n|---|---|---|")
L.append(f"| Trajectories | {S['n']} | {T['n']} |")
L.append(f"| Steps per trajectory | {fs(S['steps'])} | {fs(T['steps'])} |")
L.append(f"| Distinct agent names per trajectory | {fs(S['agents'])} | {fs(T['agents'])} |")
L.append(f"| Faulty (agent,error) pairs per trajectory | {fs(S['pairs_per_traj'])} | {fs(T['pairs_per_traj'])} |")
L.append(f"| Distinct faulty agents per trajectory | {fs(S['faulty_agents_per_traj'])} | {fs(T['faulty_agents_per_traj'])} |")
L.append(f"| Characters per trajectory | {fs(S['chars'])} | {fs(T['chars'])} |")
L.append(f"| Frac. with step-level is_injected marker | {S['frac_with_is_injected_marker']} | {T['frac_with_is_injected_marker']} |")
L.append(f"| First injected step rel. position (where marked) | {fs(S['first_injected_step_rel_pos'])} | {fs(T['first_injected_step_rel_pos'])} |")
L.append(f"| Injection strategies | {S['strategy_counts']} | {T['strategy_counts']} |")
L.append("\n### Split x benchmark / framework\n")
L.append("| split | " + ' | '.join(bms) + " | " + ' | '.join(fws) + " |\n|---|" + '---|' * (len(bms) + len(fws)))
for s in splits: L.append(f"| {s} | " + ' | '.join(str(stats['split_by_benchmark'][s].get(b, 0)) for b in bms) + ' | ' + ' | '.join(str(stats['split_by_framework'][s].get(f, 0)) for f in fws) + ' |')
L.append("\n### Framework x benchmark (all)\n")
L.append("| framework | " + ' | '.join(bms) + " | total |\n|---|" + '---|' * (len(bms) + 1))
for f in fws: L.append(f"| {f} | " + ' | '.join(str(stats['framework_x_benchmark'][f].get(b, 0)) for b in bms) + f" | {sum(stats['framework_x_benchmark'][f].values())} |")
L.append("\n### Per framework\n")
L.append("| framework | N | steps mean/median/min/max | agents mean | pairs/traj mean | chars mean | is_injected marker frac | first-inj rel pos mean | top faulty agent names |\n|---|---|---|---|---|---|---|---|---|")
for f in fws:
    b = stats['per_framework'][f]
    L.append(f"| {f} | {b['n']} | {b['steps']['mean']}/{b['steps']['median']}/{b['steps']['min']}/{b['steps']['max']} | {b['agents']['mean']} | {b['pairs_per_traj']['mean']} | {b['chars']['mean']} | {b['frac_with_is_injected_marker']} | {b['first_injected_step_rel_pos'].get('mean','n/a')} | {', '.join(f'{k} ({v})' for k,v in list(b['faulty_agent_name_top'].items())[:6])} |")
L.append("\n### Per benchmark\n")
L.append("| benchmark | N | steps mean/median | chars mean | task_type |\n|---|---|---|---|---|")
for bm in bms:
    b = stats['per_benchmark'][bm]; tt = collections.Counter(r['task_type'] for r in recs if r['benchmark'] == bm).most_common(1)[0][0]
    L.append(f"| {bm} | {b['n']} | {b['steps']['mean']}/{b['steps']['median']} | {b['chars']['mean']} | {tt} |")
L.append("\n### Error-mode counts (all / test)\n")
L.append("| error mode | all | test |\n|---|---|---|")
for k in sorted(S['error_type_counts']): L.append(f"| {k} | {S['error_type_counts'][k]} | {T['error_type_counts'].get(k,0)} |")
L.append("\n### Steps histogram (all)\n| bin | count |\n|---|---|")
for k, v in stats['steps_hist'].items(): L.append(f"| {k} | {v} |")
L.append("\n### First injected step relative position histogram (marked subset)\n| bin | count |\n|---|---|")
for k, v in stats['rel_pos_hist'].items(): L.append(f"| {k} | {v} |")
L.append(f"\n### Example {ex_id} ({len(h)} steps)\n")
L.append(f"Query: {trunc(ex['input']['query'], 800)}\n")
for x in h:
    mark = '  ⟵ ANNOTATED (INJECTED) ERROR STEP' if x.get('is_injected') else ''
    L.append(f"**[{x['step']}] {x.get('agent_name')} (phase={x.get('phase')}){mark}**\n\n```\n{trunc(x.get('content',''))}\n```\n")
L.append(f"**Final output**: {trunc(ex['input'].get('final_output'), 600)}\n")
L.append(f"**Correct answer**: {trunc(ex['ground_truth'].get('correct_answer'), 600)}\n")
L.append(f"**Annotation**: faulty_agents = {json.dumps(fa)}; injected_agents = {json.dumps(ex['ground_truth'].get('injected_agents'))}; metadata = {json.dumps(ex['metadata'])}\n")
open(f'{SCR}/{SLUG}_summary.md', 'w').write('\n'.join(L))
print('\n'.join(L[:50])); print('... written', f'{SCR}/{SLUG}_summary.md')
