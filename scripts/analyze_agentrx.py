#!/usr/bin/env python3
"""Analyse AgentRx public data (GitHub microsoft/AgentRx data/). Run: python3 -I analyze_agentrx.py [EXAMPLE_ID] [SCRATCH_DIR]"""
import json, os, sys, glob, statistics, collections, re

GB = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/agentrx/github/data'
NOTES = '/dataDisk/home/thanhdo/failure-attribution-datasets/notes'
SCR = sys.argv[2] if len(sys.argv) > 2 else NOTES
SLUG = 'agentrx'


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


CANON = [('system failure', 'System Failure'), ('guardrail', 'Guardrails Triggered'), ('not supported', 'Intent Not Supported'),
         ('specified', 'Under-specified User Intent'), ('misalign', 'Intent-Plan Misalignment'), ('misinterpret', 'Misinterpretation of Tool Output'),
         ('invalid', 'Invalid Invocation'), ('invention', 'Invention of New Information'), ('hallucin', 'Invention of New Information'),
         ('adherence', 'Instruction/Plan Adherence Failure')]


def canon(c):
    cl = str(c).lower()
    for k, v in CANON:
        if k in cl: return v
    return 'OTHER:' + str(c)


def magentic_agent(role):
    m = re.match(r'^(\w+)', str(role)); return m.group(1) if m else str(role)


# ---------------- tau-bench retail ----------------
tau_traj = {t['task_id']: t for t in json.load(open(f'{GB}/tau_retail/tau_dataset_failed.json'))}
tau_gt = {g['trajectory_id']: g for g in json.load(open(f'{GB}/ground_truth/tau_ground_truth.json'))}
tau_gt_old = {g['trajectory_id']: g for g in json.load(open(f'{GB}/ground_truth/tau_retail.json'))}
# ---------------- magentic-one ----------------
mag_files = {os.path.basename(f)[:-5]: f for f in glob.glob(f'{GB}/magentic_dataset/*.json') if 'steps_by_id' not in f}
mag_gt = {g['trajectory_id']: g for g in json.load(open(f'{GB}/ground_truth/magentic_one_ground_truth.json'))}
ww_files = {os.path.basename(f)[:-5] for f in glob.glob(f'{GB}/magentic_dataset_whowhen/*.json')}


def tau_steps(t):
    """1-based steps incl. system message; returns list of (idx, agent, content)."""
    out = []
    for i, m in enumerate(t['traj'], start=1):
        role = m.get('role'); c = m.get('content') or ''
        if role == 'assistant' and m.get('tool_calls'):
            calls = '; '.join(f"{tc['function']['name']}({tc['function']['arguments']})" for tc in m['tool_calls'])
            c = (c + '\n' if c else '') + 'Action: ' + calls
            agent = 'Assistant'
        elif role == 'assistant': agent = 'Assistant'
        elif role == 'tool': agent = f"Tool:{m.get('name')}"; c = 'Observation: ' + c
        elif role == 'user': agent = 'User'
        else: agent = role.capitalize() if role else 'unknown'
        out.append((i, agent, c))
    return out


def mag_steps(d):
    return [(i, m.get('role'), m.get('content') or '') for i, m in enumerate(d, start=1)]


recs = []; raw = {}
for tid, g in tau_gt.items():
    t = tau_traj[tid]; steps = tau_steps(t)
    rc_id = g['root_cause']['failure_id']; rc = next((f for f in g['failures'] if str(f['failure_id']) == str(rc_id)), None)
    recs.append(dict(domain='tau_retail', id=str(tid), n=len(steps), n_agents=len(set(a for _, a, _ in steps if not a.startswith('Tool:'))) ,
                     agents=sorted(set(a for _, a, _ in steps)), chars=sum(len(c) for _, _, c in steps), n_failures=len(g['failures']),
                     rc_step=rc['step_number'] if rc else None, rc_cat=canon(rc['failure_category']) if rc else None, rc_cat_raw=rc['failure_category'] if rc else None,
                     rc_agent=rc['failed_agent'] if rc else None, all_cats=[canon(f['failure_category']) for f in g['failures']],
                     all_agents=[f['failed_agent'] for f in g['failures']], rc_is_first=(rc_id == min(f['failure_id'] for f in g['failures'])) if rc else None,
                     reward=t.get('reward'), expected_outputs=t['info']['task'].get('outputs'), instruction=t['info']['task'].get('instruction')))
    raw[('tau_retail', str(tid))] = {'ground_truth': g, 'trajectory': t}
for tid, g in mag_gt.items():
    d = json.load(open(mag_files[tid])); steps = mag_steps(d)
    rc_id = g['root_cause']['failure_id']; rc = next((f for f in g['failures'] if str(f['failure_id']) == str(rc_id)), None)
    recs.append(dict(domain='magentic_one', id=tid, n=len(steps), n_agents=len(set(magentic_agent(a) for _, a, _ in steps)),
                     agents=sorted(set(magentic_agent(a) for _, a, _ in steps)), chars=sum(len(c) for _, _, c in steps), n_failures=len(g['failures']),
                     rc_step=rc['step_number'] if rc else None, rc_cat=canon(rc['failure_category']) if rc else None, rc_cat_raw=rc['failure_category'] if rc else None,
                     rc_agent=rc['failed_agent'] if rc else None, all_cats=[canon(f['failure_category']) for f in g['failures']],
                     all_agents=[f['failed_agent'] for f in g['failures']], rc_is_first=(rc_id == min(f['failure_id'] for f in g['failures'])) if rc else None,
                     in_whowhen_dir=tid in ww_files, instruction=d[0].get('content') if d else None))
    raw[('magentic_one', tid)] = {'ground_truth': g, 'trajectory': d}
for r in recs:
    r['rel'] = (r['rc_step'] - 1) / (r['n'] - 1) if r['rc_step'] is not None and r['n'] > 1 else None
    r['rc_in_range'] = r['rc_step'] is not None and 1 <= r['rc_step'] <= r['n']

doms = ['tau_retail', 'magentic_one']


def block(rs):
    return {'n': len(rs), 'steps': summ([r['n'] for r in rs]), 'chars': summ([r['chars'] for r in rs]), 'agents': summ([r['n_agents'] for r in rs]),
            'failures_per_traj': summ([r['n_failures'] for r in rs]), 'rc_rel_pos': summ([r['rel'] for r in rs if r['rel'] is not None]),
            'rc_abs_step': summ([r['rc_step'] for r in rs if r['rc_step'] is not None]),
            'rc_category_counts': dict(collections.Counter(r['rc_cat'] for r in rs).most_common()),
            'rc_category_raw_counts': dict(collections.Counter(r['rc_cat_raw'] for r in rs).most_common()),
            'all_failure_category_counts': dict(collections.Counter(c for r in rs for c in r['all_cats']).most_common()),
            'rc_agent_counts': dict(collections.Counter(r['rc_agent'] for r in rs).most_common()),
            'frac_root_cause_is_first_failure': round(sum(bool(r['rc_is_first']) for r in rs) / len(rs), 4) if rs else None,
            'frac_rc_step_in_range': round(sum(r['rc_in_range'] for r in rs) / len(rs), 4) if rs else None,
            'frac_multi_failure': round(sum(r['n_failures'] >= 2 for r in rs) / len(rs), 4) if rs else None}


stats = {
    'n_trajectories': len(recs), 'all_failed': True,
    'availability': {'hf_gated_access_denied': True, 'github_public_subset': True, 'paper_total': 170, 'hf_card_total_claimed': 115,
                     'github_tau_trajectories_file': len(tau_traj), 'github_tau_ground_truth': len(tau_gt), 'github_tau_ground_truth_old_file': len(tau_gt_old),
                     'github_magentic_trajectory_files': len(mag_files), 'github_magentic_ground_truth': len(mag_gt), 'github_magentic_whowhen_dir_files': len(ww_files),
                     'flash_released': False, 'relwork_released': False},
    'steps_per_traj': [r['n'] for r in recs], 'error_step_rel_pos': [round(r['rel'], 4) for r in recs if r['rel'] is not None],
    'agents_per_traj': [r['n_agents'] for r in recs], 'chars_per_traj': [r['chars'] for r in recs],
    'faulty_agent_counts': dict(collections.Counter(r['rc_agent'] for r in recs).most_common()),
    'category_counts': dict(collections.Counter(r['rc_cat'] for r in recs).most_common()),
    'category_counts_raw_labels': dict(collections.Counter(r['rc_cat_raw'] for r in recs).most_common()),
    'all_failure_events_category_counts': dict(collections.Counter(c for r in recs for c in r['all_cats']).most_common()),
    'source_benchmark_counts': {d: sum(1 for r in recs if r['domain'] == d) for d in doms},
    'splits': {d: sum(1 for r in recs if r['domain'] == d) for d in doms},
    'summary_all': block(recs), 'per_domain': {d: block([r for r in recs if r['domain'] == d]) for d in doms},
    'steps_hist': hist([r['n'] for r in recs], [0, 10, 20, 30, 40, 60, 80, 100, 130]),
    'rel_pos_hist': hist([r['rel'] for r in recs if r['rel'] is not None], [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]),
    'unresolved_root_cause_ids': [(r['domain'], r['id'], raw[(r['domain'], r['id'])]['ground_truth']['root_cause']) for r in recs if r['rc_step'] is None],
    'step_indexing': 'step_number is a 1-based index into the message list; tau-bench list includes the system (policy) message at step 1',
    'paper_table1_percent': {'tau_bench': {'n': 39}, 'flash': {'n': 42}, 'magentic': {'n': 44}, 'relwork': {'n': 45}},
}
json.dump(stats, open(f'{NOTES}/{SLUG}_stats.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- example ----------------
cands = sorted(recs, key=lambda r: (r['n'], r['chars']))[:12]
ex_sel = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != '-' else cands[0]['id']
exr = next(r for r in recs if r['id'] == ex_sel); ex = raw[(exr['domain'], exr['id'])]
json.dump(ex, open(f'{NOTES}/{SLUG}_example.json', 'w'), indent=1, ensure_ascii=False)
steps = tau_steps(ex['trajectory']) if exr['domain'] == 'tau_retail' else mag_steps(ex['trajectory'])
g = ex['ground_truth']; rc_id = g['root_cause']['failure_id']; rc = next(f for f in g['failures'] if str(f['failure_id']) == str(rc_id))
norm_steps = []
for i, a, c in steps:
    cc, trimmed = trim_norm(c); st = {'idx': i, 'agent': a, 'content': cc}
    if trimmed: st['trimmed'] = True
    norm_steps.append(st)
if exr['domain'] == 'tau_retail':
    task = ex['trajectory']['info']['task'].get('instruction'); gt = {'expected_outputs': ex['trajectory']['info']['task'].get('outputs'), 'expected_actions': ex['trajectory']['info']['task'].get('actions')}
    final = next((c for i, a, c in reversed(steps) if a == 'Assistant'), None)
else:
    task = steps[0][2] if steps else None; gt = None; final = steps[-1][2] if steps else None
norm = {'dataset': SLUG, 'source_id': f"{exr['domain']}/{exr['id']}", 'task': task, 'ground_truth': gt, 'final_output': final, 'steps': norm_steps,
        'annotation': {'faulty_agent': rc['failed_agent'], 'faulty_step': rc['step_number'], 'category': rc['failure_category'],
                       'reason': rc['step_reason'] + ' | category_reason: ' + rc['category_reason'] + ' | root_cause: ' + g['root_cause']['reason_for_root_cause'],
                       'extra': {'all_failures': g['failures'], 'root_cause': g['root_cause'], 'failure_summary': g.get('failure_summary'),
                                 'step_indexing': stats['step_indexing'], 'canonical_category': canon(rc['failure_category'])}}}
json.dump(norm, open(f'{NOTES}/{SLUG}_example_norm.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- markdown ----------------
def fs(d): return f"mean {d['mean']}, median {d['median']}, min {d['min']}, max {d['max']}, p10 {d['p10']}, p90 {d['p90']}" if d else 'n/a'
L = [f"n={len(recs)} availability={json.dumps(stats['availability'])}"]
L.append("\n### Shortest candidates\n")
for r in cands: L.append(f"- {r['domain']}/{r['id']}: {r['n']} steps, {r['chars']} chars, agents={r['agents']}, rc={r['rc_agent']}@{r['rc_step']} {r['rc_cat_raw']}, n_failures={r['n_failures']}")
L.append("\n### Stats table\n")
L.append("| Quantity | tau_retail | magentic_one | all public |\n|---|---|---|---|")
P = stats['per_domain']; A = stats['summary_all']
for lab, key in [('Steps per trajectory', 'steps'), ('Distinct agents per trajectory', 'agents'), ('Annotated failure events per trajectory', 'failures_per_traj'), ('Root-cause step (1-based)', 'rc_abs_step'), ('Root-cause relative position (step-1)/(T-1)', 'rc_rel_pos'), ('Characters per trajectory', 'chars')]:
    L.append(f"| {lab} | {fs(P['tau_retail'][key])} | {fs(P['magentic_one'][key])} | {fs(A[key])} |")
L.append(f"| Trajectories | {P['tau_retail']['n']} | {P['magentic_one']['n']} | {A['n']} |")
L.append(f"| Root cause == first annotated failure | {P['tau_retail']['frac_root_cause_is_first_failure']} | {P['magentic_one']['frac_root_cause_is_first_failure']} | {A['frac_root_cause_is_first_failure']} |")
L.append(f"| Trajectories with >=2 failure events | {P['tau_retail']['frac_multi_failure']} | {P['magentic_one']['frac_multi_failure']} | {A['frac_multi_failure']} |")
L.append(f"| Root-cause step within range | {P['tau_retail']['frac_rc_step_in_range']} | {P['magentic_one']['frac_rc_step_in_range']} | {A['frac_rc_step_in_range']} |")
L.append("\n### Root-cause category (canonicalised) per domain\n")
cats = sorted(set(A['rc_category_counts']), key=str)
L.append("| category | tau_retail | magentic_one | all |\n|---|---|---|---|")
for c in cats: L.append(f"| {c} | {P['tau_retail']['rc_category_counts'].get(c,0)} | {P['magentic_one']['rc_category_counts'].get(c,0)} | {A['rc_category_counts'][c]} |")
L.append("\n### Raw category labels found in ground truth (root cause)\n")
for k, v in stats['category_counts_raw_labels'].items(): L.append(f"- {k}: {v}")
L.append("\n### All annotated failure events (not only root cause), canonicalised\n")
for k, v in stats['all_failure_events_category_counts'].items(): L.append(f"- {k}: {v}")
L.append("\n### Root-cause failed agent\n")
for d in doms: L.append(f"- **{d}**: " + ', '.join(f"{k} ({v})" for k, v in P[d]['rc_agent_counts'].items()))
L.append("\n### Steps histogram\n| bin | count |\n|---|---|")
for k, v in stats['steps_hist'].items(): L.append(f"| {k} | {v} |")
L.append("\n### Relative root-cause position histogram\n| bin | count |\n|---|---|")
for k, v in stats['rel_pos_hist'].items(): L.append(f"| {k} | {v} |")
L.append(f"\n### Example {exr['domain']}/{exr['id']} ({len(steps)} steps; root cause {rc['failed_agent']} @ step {rc['step_number']}, {rc['failure_category']})\n")
if task: L.append(f"Task: {trunc(task, 800)}\n")
fail_steps = {f['step_number']: f for f in g['failures']}
for i, a, c in steps:
    mark = '  ⟵ ANNOTATED ERROR STEP (root cause)' if i == rc['step_number'] else ('  ⟵ other annotated failure' if i in fail_steps else '')
    L.append(f"**[{i}] {a}{mark}**\n\n```\n{trunc(c)}\n```\n")
L.append(f"**Annotation**: failures = {json.dumps(g['failures'], ensure_ascii=False)}\n\nroot_cause = {json.dumps(g['root_cause'], ensure_ascii=False)}\n\nfailure_summary = {g.get('failure_summary')}\n")
if gt: L.append(f"**Ground truth (tau)**: {json.dumps(gt)}\n")
open(f'{SCR}/{SLUG}_summary.md', 'w').write('\n'.join(L))
print('\n'.join(L[:60])); print('... written', f'{SCR}/{SLUG}_summary.md')
