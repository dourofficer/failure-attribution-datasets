#!/usr/bin/env python3
"""Analyse SearchAuditBench. Usage: python3 -I analyze_searchauditbench.py"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SLUG = 'searchauditbench'
F = os.path.join(C.DATA, SLUG, 'extracted', 'benchmark_data_1243.jsonl')


def msg_chars(m):
    n = 0
    for k in ('content', 'reasoning_content'):
        v = m.get(k)
        if isinstance(v, str):
            n += len(v)
    tc = m.get('tool_calls')
    if tc:
        n += len(json.dumps(tc, ensure_ascii=False))
    return n


recs = []
models, datasets, causes = collections.Counter(), collections.Counter(), collections.Counter()
roles = collections.Counter()
tool_names = collections.Counter()
keys_seen = collections.Counter()
with open(F, encoding='utf-8') as fh:
    for line in fh:
        d = json.loads(line)
        keys_seen.update(d.keys())
        tr = d['trajectory']
        n_msg = len(tr)
        last_idx = tr[-1]['message_index']
        assist = [m['message_index'] for m in tr if m['role'] == 'assistant']
        cs = d['critical_step']
        k = cs['message_index']
        ks, ke = cs['span_start_message_index'], cs['span_end_message_index']
        roles.update(m['role'] for m in tr)
        for m in tr:
            for c in (m.get('tool_calls') or []):
                tool_names[c.get('tool_name')] += 1
        chars = sum(msg_chars(m) for m in tr)
        crit_role = next((m['role'] for m in tr if m['message_index'] == k), None)
        crit_is_final = (k == assist[-1]) if assist else None
        recs.append(dict(index=d['index'], model=d['model'], dataset=d['dataset'], n_msg=n_msg, last_idx=last_idx,
                         n_assist=len(assist), k=k, ks=ks, ke=ke, span=ke - ks + 1,
                         k_rank=(assist.index(k) + 1) if k in assist else None,
                         rel=k / last_idx if last_idx else None, cause=d['root_cause_primary'],
                         n_rubrics=len(d['repair_rubrics']), chars=chars, crit_role=crit_role,
                         crit_is_final=crit_is_final, n_tool=sum(1 for m in tr if m['role'] == 'tool'),
                         q_len=len(d['query']), pred_len=len(d['predicted_answer'] or '')))
        models[d['model']] += 1
        datasets[d['dataset']] += 1
        causes[d['root_cause_primary']] += 1
print('records', len(recs), 'keys', keys_seen)
print('roles', roles, 'tools', tool_names)
print('critical role', collections.Counter(r['crit_role'] for r in recs), 'crit is final answer', collections.Counter(r['crit_is_final'] for r in recs))

stats = {
    'n_trajectories': len(recs), 'n_failed': len(recs), 'n_success': 0,
    'steps_per_traj': [r['n_msg'] for r in recs],
    'assistant_steps_per_traj': [r['n_assist'] for r in recs],
    'error_step_rel_pos': [round(r['rel'], 4) for r in recs if r['rel'] is not None],
    'error_step_rel_pos_among_assistant_steps': [round(r['k_rank'] / r['n_assist'], 4) for r in recs if r['k_rank']],
    'error_step_abs_message_index': [r['k'] for r in recs],
    'tolerance_span_len_messages': [r['span'] for r in recs],
    'agents_per_traj': [1] * len(recs),
    'faulty_agent_counts': {'assistant (single search agent)': len(recs)},
    'category_counts': dict(causes),
    'source_benchmark_counts': dict(datasets),
    'model_counts': dict(models),
    'chars_per_traj': [r['chars'] for r in recs],
    'tool_messages_per_traj': [r['n_tool'] for r in recs],
    'rubrics_per_repair': [r['n_rubrics'] for r in recs],
    'critical_step_role_counts': dict(collections.Counter(r['crit_role'] for r in recs)),
    'critical_step_is_final_answer_counts': dict(collections.Counter(str(r['crit_is_final']) for r in recs)),
    'role_message_counts': dict(roles), 'tool_call_name_counts': dict(tool_names),
    'splits': {'single file benchmark_data_1243.jsonl (no official split)': len(recs)},
}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_stats.json'), stats)

L = []
L.append(C.md_table(C.SUMM_HEADERS, [
    C.summ_row('messages per trajectory (system+user+assistant+tool)', stats['steps_per_traj']),
    C.summ_row('assistant decision steps per trajectory', stats['assistant_steps_per_traj']),
    C.summ_row('tool-return messages per trajectory', stats['tool_messages_per_traj']),
    C.summ_row('critical message index (0-based)', stats['error_step_abs_message_index']),
    C.summ_row('critical rel. position (idx / last idx)', stats['error_step_rel_pos']),
    C.summ_row('critical rel. position among assistant steps (rank/n)', stats['error_step_rel_pos_among_assistant_steps']),
    C.summ_row('tolerance span length (messages)', stats['tolerance_span_len_messages']),
    C.summ_row('repair rubrics per instance', stats['rubrics_per_repair']),
    C.summ_row('characters per trajectory (content+reasoning+tool_calls)', stats['chars_per_traj']),
    C.summ_row('query length (chars)', [r['q_len'] for r in recs]),
    C.summ_row('predicted answer length (chars)', [r['pred_len'] for r in recs]),
]))
L.append('\nHistogram of messages per trajectory:\n')
L.append(C.hist_md(stats['steps_per_traj'], [0, 20, 40, 60, 80, 100, 150, 200, 300], 'messages'))
L.append('\nHistogram of critical-step relative position (message index / last index):\n')
rp = stats['error_step_rel_pos']
L.append(C.md_table(['rel. position', 'n', '%'], [[f'{a:.1f}-{a + 0.2:.1f}', c, f'{100 * c / len(rp):.1f}'] for a in [0.0, 0.2, 0.4, 0.6, 0.8] for c in [sum(1 for x in rp if a <= x < a + 0.2 or (a == 0.8 and x >= 1.0))]]))
L.append('\nRoot-cause distribution (one primary label per trajectory):\n')
L.append(C.counts_md(causes, 'root cause'))
L.append('\nSource benchmark:\n')
L.append(C.counts_md(datasets, 'benchmark'))
L.append('\nGenerating agent (model):\n')
L.append(C.counts_md(models, 'model'))
L.append('\nModel × benchmark:\n')
cross = collections.Counter((r['model'], r['dataset']) for r in recs)
ds = sorted(datasets)
L.append(C.md_table(['model'] + ds + ['total'], [[m] + [cross[(m, d)] for d in ds] + [models[m]] for m in sorted(models)]))
L.append('\nRoot cause × median relative position:\n')
bycause = collections.defaultdict(list)
for r in recs:
    bycause[r['cause']].append(r['rel'])
L.append(C.md_table(['root cause', 'n', 'median rel. pos', 'share in final third'], [[c, len(v), round(sorted(v)[len(v) // 2], 3), f"{100 * sum(1 for x in v if x >= 2 / 3) / len(v):.1f}%"] for c, v in sorted(bycause.items(), key=lambda kv: -len(kv[1]))]))
L.append(f"\nCritical step attached to: {stats['critical_step_is_final_answer_counts']} (True = the final-answer assistant message). Critical-step role counts: {stats['critical_step_role_counts']}. Tool-call names: {dict(tool_names)}.")
C.write_fragment(SLUG, 'stats', '\n'.join(L))

# ---------- example ----------
cands = [r for r in recs if r['n_msg'] <= 15 and r['dataset'] != 'BrowseComp-ZH']
cands.sort(key=lambda r: (r['chars'], r['n_msg']))
# prefer a case whose critical step is not the final answer, so the propagation is visible
pref = [r for r in cands if not r['crit_is_final'] and r['chars'] <= 2500 * r['n_msg']]
ex = (pref or cands)[0]
print('example', ex)
with open(F, encoding='utf-8') as fh:
    for line in fh:
        d = json.loads(line)
        if d['index'] == ex['index']:
            break
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example.json'), d)

steps_norm = []
for m in d['trajectory']:
    parts = []
    if m.get('reasoning_content'):
        parts.append('Thought: ' + m['reasoning_content'])
    if m.get('tool_calls'):
        parts.append('Action (tool_calls): ' + json.dumps(m['tool_calls'], ensure_ascii=False))
    if m.get('content'):
        parts.append(('Observation (tool return): ' if m['role'] == 'tool' else 'Content: ') + m['content'])
    c, trimmed = C.norm_content('\n'.join(parts))
    agent = m['role'] + (f" ({m['name']})" if m.get('name') else '')
    st = {'idx': m['message_index'], 'agent': agent, 'content': c}
    if trimmed:
        st['trimmed'] = True
    steps_norm.append(st)
norm = {'dataset': SLUG, 'source_id': str(d['index']), 'task': d['query'], 'ground_truth': d['gold_answer'],
        'final_output': d['predicted_answer'], 'steps': steps_norm,
        'annotation': {'faulty_agent': 'assistant (single search agent)', 'faulty_step': d['critical_step']['message_index'],
                       'category': d['root_cause_primary'], 'reason': d['rationale'].get('failure_rationale'),
                       'extra': {'tolerance_span': [d['critical_step']['span_start_message_index'], d['critical_step']['span_end_message_index']],
                                 'repair_directive': d['repair_directive'], 'repair_rubrics': d['repair_rubrics'],
                                 'model': d['model'], 'source_benchmark': d['dataset']}}}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example_norm.json'), norm)
C.write_fragment(SLUG, 'example', C.example_md(norm, f"Chosen: index `{d['index']}` ({d['model']} on {d['dataset']}), {ex['n_msg']} messages ({ex['n_assist']} assistant decision steps), {ex['chars']} characters; shortest English-benchmark trajectory with ≤15 messages whose critical step is not the final answer. Step index = `message_index` (0-based; system and user prompt are steps 0–1)."))
