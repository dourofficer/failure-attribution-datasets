#!/usr/bin/env python3
"""Analyse SymFail (SymTrace, arXiv:2608.25920). Usage: python3 -I analyze_symtrace.py
Data: data/symtrace/extracted/SymFail/{human_annotations_536.jsonl, initial_failure_logs_536/<mas>/<task_id>/attempt_000/*}
plus the newer 437-case snapshot (human_annotations_437.jsonl, initial_failure_logs_437/...)."""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SLUG = 'symtrace'
R = os.path.join(C.DATA, SLUG, 'extracted', 'SymFail')
CAT = {'c1': 'C1 Task-constraint violation', 'c2': 'C2 Repeated / stalled progress',
       'c3': 'C3 Unresolved runtime condition', 'c4': 'C4 Plan-action-outcome inconsistency'}


def jload(p):
    return json.load(open(p, encoding='utf-8'))


def node_text(nd):
    """Readable content of one graph node."""
    k = nd['kind']
    act, obs = nd.get('action') or {}, nd.get('observation') or {}
    if k in ('sys_prompt', 'user_input'):
        return str(obs.get('content') or '')
    if k == 'agent_action':
        msg = act.get('message')
        if isinstance(msg, dict) and msg.get('content') is not None:
            s = str(msg['content'])
        elif act.get('content') is not None:
            s = str(act['content'])
        else:
            s = json.dumps({kk: vv for kk, vv in act.items() if kk != 'type'}, ensure_ascii=False)
        t = act.get('type')
        return (f'[{t}] ' if t else '') + s
    if k == 'tool_call':
        tc = nd.get('tool_call') or act
        return json.dumps(tc, ensure_ascii=False)
    if k == 'tool_result':
        return str(obs.get('content') or json.dumps(nd.get('tool_result'), ensure_ascii=False))
    if k == 'final_result':
        return str(nd.get('final_answer') or act.get('answer') or '')
    if k == 'error':
        return str(nd.get('error'))
    return json.dumps({'action': act, 'observation': obs}, ensure_ascii=False)


def token_total(tu):
    if isinstance(tu, dict):
        for key in ('total_tokens', 'total'):
            if isinstance(tu.get(key), (int, float)):
                return int(tu[key])
        s = 0
        for key in ('prompt_tokens', 'completion_tokens', 'input_tokens', 'output_tokens'):
            if isinstance(tu.get(key), (int, float)):
                s += int(tu[key])
        return s or None
    if isinstance(tu, (int, float)):
        return int(tu)
    return None


# ---------------- 536-case package (the paper's SymFail) ----------------
ann = [json.loads(l) for l in open(os.path.join(R, 'human_annotations_536.jsonl'), encoding='utf-8') if l.strip()]
recs = []
missing_dirs = 0
for a in ann:
    d = os.path.join(R, 'initial_failure_logs_536', a['mas'], a['task_id'], 'attempt_000')
    if not os.path.isdir(d):
        missing_dirs += 1
        continue
    g = jload(os.path.join(d, 'graph.json'))
    nodes = {nd['node_id']: nd for nd in g['nodes']}
    order = g.get('topological_order') or [nd['node_id'] for nd in g['nodes']]
    order = [nid for nid in order if nid in nodes]
    tr = jload(os.path.join(d, 'trajectory.json'))
    res = tr.get('result') or jload(os.path.join(d, 'result_record.json'))
    task = tr.get('task') or {}
    cs = (g.get('metadata') or {}).get('capture_summary') or {}
    fid = a['failure_node_id']
    fidx = order.index(fid) if fid in nodes else None
    kinds = collections.Counter(nodes[n]['kind'] for n in order)
    texts = [node_text(nodes[n]) for n in order]
    chars = sum(len(t) for t in texts)
    api_lines = sum(1 for _ in open(os.path.join(d, 'api_records.jsonl'), encoding='utf-8'))
    bench = 'WebArena-Verified Hard' if a['task_id'].startswith('webarena') else 'AssistantBench'
    recs.append(dict(
        ann=a, dir=d, mas=a['mas'], task_id=a['task_id'], bench=bench, order=order, nodes=nodes, texts=texts,
        T=len(order), fidx=fidx, rel=(fidx / (len(order) - 1)) if fidx is not None and len(order) > 1 else None,
        fkind=a['failure_node_kind'], fagent=nodes[fid]['agent_id'] if fid in nodes else None,
        kinds=kinds, chars=chars, llm_calls=cs.get('llm_call_count'), api_lines=api_lines,
        tool_fail=cs.get('tool_failure_count'), tool_res=cs.get('tool_result_count'),
        tokens=token_total(res.get('token_usage')), latency=res.get('latency'), model=res.get('model'),
        temperature=res.get('temperature'), task_type=task.get('task_type'), difficulty=task.get('difficulty_tag'),
        primary=a['primary_failure_label'], labels=tuple(a['failure_labels']),
        iaa=a['inter_annotator_agreement'], final_answer=res.get('final_answer'),
        ref=task.get('reference_answer') or ((task.get('evaluator') or {}).get('answer')),
        ev=res.get('evaluator_evidence'),
    ))
print('536 package: annotations', len(ann), 'bundles found', len(recs), 'missing dirs', missing_dirs)
by_mas = collections.defaultdict(list)
for r in recs:
    by_mas[r['mas']].append(r)
MAS_NAME = {'ag2': 'AG2', 'crewai': 'CrewAI', 'magnetic_one': 'Magentic-One'}

decision_kinds = ('agent_action', 'tool_call', 'final_result')
stats = {
    'n_trajectories': len(recs), 'n_failed': len(recs), 'n_success': 0,
    'package_note': 'statistics are for the 536-case package described in the paper (arXiv:2608.25920v2); the repository also ships a newer 437-case package, summarised separately below',
    'steps_per_traj': [r['T'] for r in recs],
    'decision_steps_per_traj': [sum(r['kinds'][k] for k in decision_kinds) for r in recs],
    'agent_action_steps_per_traj': [r['kinds']['agent_action'] for r in recs],
    'llm_calls_per_traj': [r['llm_calls'] for r in recs if r['llm_calls'] is not None],
    'api_records_per_traj': [r['api_lines'] for r in recs],
    'tool_results_per_traj': [r['tool_res'] for r in recs if r['tool_res'] is not None],
    'tool_failures_per_traj': [r['tool_fail'] for r in recs if r['tool_fail'] is not None],
    'error_step_abs': [r['fidx'] for r in recs if r['fidx'] is not None],
    'error_step_rel_pos': [round(r['rel'], 4) for r in recs if r['rel'] is not None],
    'agents_per_traj': [len(set(r['nodes'][n]['agent_id'] for n in r['order'])) for r in recs],
    'chars_per_traj': [r['chars'] for r in recs],
    'tokens_per_traj': [r['tokens'] for r in recs if r['tokens']],
    'latency_s_per_traj': [round(r['latency'], 1) for r in recs if isinstance(r['latency'], (int, float))],
    'category_counts': dict(collections.Counter(CAT[r['primary']] for r in recs)),
    'label_marginals': dict(collections.Counter(CAT[c] for r in recs for c in r['labels'])),
    'label_set_size': dict(collections.Counter(len(r['labels']) for r in recs)),
    'label_set_counts': {'+'.join(k): v for k, v in collections.Counter(r['labels'] for r in recs).most_common()},
    'faulty_agent_counts': dict(collections.Counter(f"{r['fagent']} ({MAS_NAME[r['mas']]})" for r in recs)),
    'failure_node_kind_counts': dict(collections.Counter(r['fkind'] for r in recs)),
    'source_benchmark_counts': dict(collections.Counter(r['bench'] for r in recs)),
    'framework_counts': dict(collections.Counter(MAS_NAME[r['mas']] for r in recs)),
    'task_type_counts': dict(collections.Counter(str(r['task_type']) for r in recs)),
    'difficulty_counts': dict(collections.Counter(str(r['difficulty']) for r in recs)),
    'model_counts': dict(collections.Counter(str(r['model']) for r in recs)),
    'temperature_counts': dict(collections.Counter(str(r['temperature']) for r in recs)),
    'node_kind_totals': dict(sum((r['kinds'] for r in recs), collections.Counter())),
    'agent_id_totals': dict(collections.Counter(r['nodes'][n]['agent_id'] for r in recs for n in r['order'])),
    'agreement': {
        'failure_node_unanimous': sum(1 for r in recs if r['iaa']['failure_node_unanimous']),
        'failure_node_support_ge2': sum(1 for r in recs if r['iaa']['final_failure_node_support_count'] >= 2),
        'failure_node_kind_unanimous': sum(1 for r in recs if r['iaa']['failure_node_kind_unanimous']),
        'primary_label_unanimous': sum(1 for r in recs if r['iaa']['primary_failure_label_unanimous']),
        'label_set_unanimous': sum(1 for r in recs if r['iaa']['failure_label_set_unanimous']),
        'strict_unanimous': sum(1 for r in recs if r['iaa']['strict_annotation_unanimous']),
        'confidence': dict(collections.Counter(r['ann']['confidence'] for r in recs)),
        'individual_confidence': dict(collections.Counter(x['confidence'] for r in recs for x in r['ann']['individual_annotations'])),
        'final_label_set_differs_from_all_three': sum(1 for r in recs if r['iaa']['final_failure_label_set_support_count'] == 0),
    },
    'failure_at_last_step': sum(1 for r in recs if r['fidx'] == r['T'] - 1),
    'failure_at_first_agent_action': sum(1 for r in recs if r['fidx'] is not None and r['nodes'][r['order'][r['fidx']]]['kind'] == 'agent_action'
                                         and all(r['nodes'][n]['kind'] != 'agent_action' for n in r['order'][:r['fidx']])),
    'per_mas': {MAS_NAME[m]: {
        'n': len(v), 'steps_per_traj': [r['T'] for r in v], 'error_step_rel_pos': [round(r['rel'], 4) for r in v if r['rel'] is not None],
        'error_step_abs': [r['fidx'] for r in v], 'chars_per_traj': [r['chars'] for r in v],
        'llm_calls_per_traj': [r['llm_calls'] for r in v if r['llm_calls'] is not None],
        'category_counts': dict(collections.Counter(CAT[r['primary']] for r in v)),
        'failure_node_kind_counts': dict(collections.Counter(r['fkind'] for r in v)),
        'faulty_agent_counts': dict(collections.Counter(str(r['fagent']) for r in v)),
        'bench': dict(collections.Counter(r['bench'] for r in v)),
        'tool_failures_total': sum(r['tool_fail'] or 0 for r in v),
    } for m, v in by_mas.items()},
    'per_bench': {b: {'n': sum(1 for r in recs if r['bench'] == b),
                      'category_counts': dict(collections.Counter(CAT[r['primary']] for r in recs if r['bench'] == b)),
                      'steps_per_traj': [r['T'] for r in recs if r['bench'] == b]} for b in sorted(set(r['bench'] for r in recs))},
}

# ---------------- 437-case package (newer snapshot) ----------------
ann2 = [json.loads(l) for l in open(os.path.join(R, 'human_annotations_437.jsonl'), encoding='utf-8') if l.strip()]
p437 = []
for a in ann2:
    cands = glob.glob(os.path.join(R, 'initial_failure_logs_437', a['mas'], a['cell'], a['task_id'], 'attempt_*', 'graph_manifest.json'))
    gm = jload(cands[0]) if cands else {}
    cs = gm.get('capture_summary') or {}
    p437.append(dict(a=a, nodes=gm.get('node_count'), llm=cs.get('llm_call_count'), tool_fail=cs.get('tool_failure_count'), found=bool(cands)))
stats['package_437'] = {
    'n': len(ann2), 'bundles_found': sum(1 for x in p437 if x['found']),
    'per_mas': dict(collections.Counter(a['mas'] for a in ann2)), 'per_model': dict(collections.Counter(a['model'] for a in ann2)),
    'per_benchmark': dict(collections.Counter(a['benchmark'] for a in ann2)),
    'per_cell': dict(collections.Counter(a['cell'] for a in ann2)),
    'task_family': dict(collections.Counter(a['task_id'].split('_')[0] for a in ann2)),
    'primary_label': dict(collections.Counter(CAT[a['primary_label']] for a in ann2)),
    'failure_node_id': dict(collections.Counter(a['failure_node_id'] for a in ann2)),
    'reason': dict(collections.Counter(a['reason'] for a in ann2)),
    'reviewer_id': dict(collections.Counter(a['reviewer_id'] for a in ann2)),
    'nodes_per_traj': [x['nodes'] for x in p437 if x['nodes']],
    'llm_calls_per_traj': [x['llm'] for x in p437 if x['llm'] is not None],
    'nodes_per_traj_by_mas': {m: [x['nodes'] for x in p437 if x['a']['mas'] == m and x['nodes']] for m in sorted(set(a['mas'] for a in ann2))},
    'reviewed_at_range': [min(a['reviewed_at'] for a in ann2), max(a['reviewed_at'] for a in ann2)],
}

# ---------------- environment / adapter signals ----------------
def tool_results(r):
    return [r['nodes'][n] for n in r['order'] if r['nodes'][n]['kind'] == 'tool_result']
def tr_text(nd):
    return str((nd.get('observation') or {}).get('content') or json.dumps(nd.get('tool_result'), ensure_ascii=False))
env = {
    'llm_calls_distribution': dict(collections.Counter(r['llm_calls'] for r in recs)),
    'trajectories_without_tool_call': sum(1 for r in recs if r['kinds']['tool_call'] == 0),
    'trajectories_with_failed_tool_result': sum(1 for r in recs if any("'status': 'failed'" in tr_text(nd) or '"status": "failed"' in tr_text(nd) for nd in tool_results(r))),
    'trajectories_all_tool_results_failed': sum(1 for r in recs if tool_results(r) and all("'status': 'failed'" in tr_text(nd) or '"status": "failed"' in tr_text(nd) for nd in tool_results(r))),
    'trajectories_with_placeholder_url_error': sum(1 for r in recs if any(('MissingSchema' in tr_text(nd) or 'NameResolutionError' in tr_text(nd) or 'getaddrinfo' in tr_text(nd)) and '__' in tr_text(nd) for nd in tool_results(r))),
    'webarena_trajectories_with_placeholder_url_error': sum(1 for r in recs if r['bench'].startswith('WebArena') and any(('MissingSchema' in tr_text(nd) or 'NameResolutionError' in tr_text(nd) or 'getaddrinfo' in tr_text(nd)) and '__' in tr_text(nd) for nd in tool_results(r))),
    'webarena_trajectories_with_any_successful_tool_result': sum(1 for r in recs if r['bench'].startswith('WebArena') and any("'status': 'success'" in tr_text(nd) for nd in tool_results(r))),
    'assistantbench_trajectories_with_any_successful_tool_result': sum(1 for r in recs if r['bench'] == 'AssistantBench' and any("'status': 'success'" in tr_text(nd) for nd in tool_results(r))),
    'evaluator_has_real_tool_event_false': sum(1 for r in recs if isinstance(r['ev'], dict) and r['ev'].get('has_real_tool_event') is False),
    'evaluator_has_real_tool_event_true': sum(1 for r in recs if isinstance(r['ev'], dict) and r['ev'].get('has_real_tool_event') is True),
    'evaluator_methods': dict(collections.Counter(str((r['ev'] or {}).get('method')) for r in recs)),
    'magentic_failure_node_agent_user_kind': dict(collections.Counter(r['fkind'] for r in recs if r['mas'] == 'magnetic_one' and r['fagent'] == 'user')),
    'final_answer_contains_unable_or_cannot': sum(1 for r in recs if r['final_answer'] and any(w in str(r['final_answer']).lower() for w in ('unable', 'cannot', 'could not', 'not possible', 'unavailable'))),
    'distinct_tasks': len(set(r['task_id'] for r in recs)),
    'tasks_failed_by_all_three_mas': sum(1 for t, c in collections.Counter(r['task_id'] for r in recs).items() if c == 3),
}
stats['environment_signals'] = env
C.write_json(os.path.join(C.NOTES, f'{SLUG}_stats.json'), stats)

# ---------------- markdown fragments ----------------
L = []
L.append(C.md_table(C.SUMM_HEADERS, [
    C.summ_row('graph nodes (= steps) per trajectory, all', stats['steps_per_traj']),
    C.summ_row('graph nodes per trajectory, AG2', stats['per_mas']['AG2']['steps_per_traj']),
    C.summ_row('graph nodes per trajectory, CrewAI', stats['per_mas']['CrewAI']['steps_per_traj']),
    C.summ_row('graph nodes per trajectory, Magentic-One', stats['per_mas']['Magentic-One']['steps_per_traj']),
    C.summ_row('decision nodes (agent_action + tool_call + final_result)', stats['decision_steps_per_traj']),
    C.summ_row('agent_action nodes per trajectory', stats['agent_action_steps_per_traj']),
    C.summ_row('LLM calls per trajectory (capture_summary)', stats['llm_calls_per_traj']),
    C.summ_row('tool results per trajectory', stats['tool_results_per_traj']),
    C.summ_row('tool failures per trajectory', stats['tool_failures_per_traj']),
    C.summ_row('distinct agent_id per trajectory', stats['agents_per_traj']),
    C.summ_row('failure node index (0-based, topological order)', stats['error_step_abs']),
    C.summ_row('failure node relative position (idx / last idx)', stats['error_step_rel_pos']),
    C.summ_row('characters per trajectory (all node texts)', stats['chars_per_traj']),
    C.summ_row('tokens per trajectory (result.token_usage)', stats['tokens_per_traj']),
    C.summ_row('wall-clock latency per trajectory (s)', stats['latency_s_per_traj']),
]))
L.append('\nHistogram of graph nodes per trajectory:\n')
L.append(C.hist_md(stats['steps_per_traj'], [0, 5, 10, 15, 20, 25, 30], 'nodes'))
L.append('\nHistogram of failure-node relative position:\n')
rp = stats['error_step_rel_pos']
L.append(C.md_table(['rel. position', 'n', '%'], [[f'{a:.1f}-{a + 0.2:.1f}', c, f'{100 * c / len(rp):.1f}'] for a in [0.0, 0.2, 0.4, 0.6, 0.8] for c in [sum(1 for x in rp if a <= x < a + 0.2 or (a == 0.8 and x >= 1.0))]]))
L.append('\nFramework × benchmark:\n')
L.append(C.counts_md(collections.Counter(f"{MAS_NAME[r['mas']]} / {r['bench']}" for r in recs), 'MAS / benchmark'))
L.append('\nPrimary symptom category:\n')
L.append(C.counts_md(collections.Counter(CAT[r['primary']] for r in recs), 'primary label'))
L.append('\nMulti-label marginals (a case carries 1–4 labels):\n')
L.append(C.counts_md(collections.Counter(CAT[c] for r in recs for c in r['labels']), 'label', total=len(recs)))
L.append('\nLabel-set size: ' + json.dumps(stats['label_set_size']) + '; most common sets: ' + json.dumps(dict(list(stats['label_set_counts'].items())[:8])))
L.append('\nPrimary category by MAS:\n')
cats = list(CAT.values())
L.append(C.md_table(['MAS'] + [c.split(' ')[0] for c in cats], [[m] + [stats['per_mas'][m]['category_counts'].get(c, 0) for c in cats] for m in ['AG2', 'CrewAI', 'Magentic-One']]))
L.append('\nFailure node kind / agent_id of the failure node:\n')
L.append(C.counts_md(collections.Counter(r['fkind'] for r in recs), 'failure_node_kind'))
L.append(C.counts_md(collections.Counter(f"{r['fagent']} ({MAS_NAME[r['mas']]})" for r in recs), 'agent_id of failure node'))
L.append('\nNode kinds over all trajectories: ' + json.dumps(stats['node_kind_totals']) + '; agent_id totals: ' + json.dumps(stats['agent_id_totals']))
L.append('\nTask types / difficulty tags (from trajectory.json task): ' + json.dumps(stats['task_type_counts']) + ' / ' + json.dumps(stats['difficulty_counts']))
L.append('\nBackbone model / temperature recorded in result: ' + json.dumps(stats['model_counts']) + ' / ' + json.dumps(stats['temperature_counts']))
L.append('\nAgreement (536 cases, 3 annotators + 1 adjudicator): ' + json.dumps(stats['agreement']))
L.append(f"\nFailure node is the last node in {stats['failure_at_last_step']} cases; it is the first agent_action node in {stats['failure_at_first_agent_action']} cases.")
L.append('\nEnvironment / adapter signals: ' + json.dumps(stats['environment_signals']))
L.append('\n### The newer 437-case package\n')
L.append(json.dumps({k: v for k, v in stats['package_437'].items() if not k.startswith('nodes_per') and k != 'llm_calls_per_traj'}, ensure_ascii=False, indent=1))
L.append('\n' + C.md_table(C.SUMM_HEADERS, [C.summ_row('graph nodes per trajectory (437 package)', stats['package_437']['nodes_per_traj']),
                                            C.summ_row('LLM calls per trajectory (437 package)', stats['package_437']['llm_calls_per_traj'])] +
                         [C.summ_row(f'graph nodes per trajectory, {m}', v) for m, v in stats['package_437']['nodes_per_traj_by_mas'].items()]))
C.write_fragment(SLUG, 'stats', '\n'.join(L))

# ---------------- example ----------------
cands = [r for r in recs if r['fkind'] == 'agent_action' and r['iaa']['failure_node_unanimous'] and r['fidx'] is not None and r['fidx'] < r['T'] - 1 and r['T'] >= 10 and r['kinds']['tool_call'] >= 1]
cands.sort(key=lambda r: (r['T'], r['chars']))
# prefer a WebArena case (the majority) among the shortest ones
pool = [r for r in cands if r['bench'] == 'WebArena-Verified Hard' and r['T'] <= cands[0]['T'] + 2] or cands
pool.sort(key=lambda r: (r['T'], r['chars']))
ex = pool[0]
print('example', ex['task_id'], ex['mas'], 'T', ex['T'], 'fidx', ex['fidx'], ex['primary'], ex['labels'], 'chars', ex['chars'])
raw = {'annotation': ex['ann'], 'graph': jload(os.path.join(ex['dir'], 'graph.json')), 'result_record': jload(os.path.join(ex['dir'], 'result_record.json'))}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example.json'), {'dir': os.path.relpath(ex['dir'], C.DATA), 'record': raw})
steps_norm = []
for i, nid in enumerate(ex['order']):
    nd = ex['nodes'][nid]
    c, trimmed = C.norm_content(ex['texts'][i])
    st = {'idx': i, 'agent': f"{nd['agent_id']} [{nd['kind']}]", 'content': c, 'node_id': nid.split(':')[-1], 'kind': nd['kind']}
    if trimmed:
        st['trimmed'] = True
    steps_norm.append(st)
task_text = (ex['nodes'][ex['order'][1]].get('observation') or {}).get('content') or ''
tr = jload(os.path.join(ex['dir'], 'trajectory.json'))
task_text = (tr.get('task') or {}).get('task') or task_text
norm = {'dataset': SLUG, 'source_id': f"initial_failure_logs_536/{ex['mas']}/{ex['task_id']}", 'task': task_text,
        'ground_truth': ex['ref'], 'final_output': ex['final_answer'], 'steps': steps_norm,
        'annotation': {'faulty_agent': ex['fagent'], 'faulty_step': ex['fidx'],
                       'category': f"{CAT[ex['primary']]} (primary); label set {{{', '.join(c.upper() for c in ex['labels'])}}}",
                       'reason': '(annotation rationales and evidence excerpts are withheld from the public export: annotation_prose_in_public_export = false; the label is the earliest trace-supported actionable node carrying the symptom)',
                       'extra': {'mas': MAS_NAME[ex['mas']], 'source_benchmark': ex['bench'], 'task_type': ex['task_type'], 'difficulty': ex['difficulty'],
                                 'failure_node_id': ex['ann']['failure_node_id'].split(':')[-1], 'failure_node_kind': ex['fkind'],
                                 'confidence': ex['ann']['confidence'], 'inter_annotator_agreement': ex['iaa'],
                                 'evaluator_evidence': ex['ev'], 'llm_call_count': ex['llm_calls'], 'tool_failure_count': ex['tool_fail'],
                                 'step_indexing': '0-based position of the node in graph.json topological_order (sys_prompt = 0, user_input = 1)'}}}
C.write_json(os.path.join(C.NOTES, f'{SLUG}_example_norm.json'), norm)
C.write_fragment(SLUG, 'example', C.example_md(norm, f"Chosen: `{norm['source_id']}` ({MAS_NAME[ex['mas']]}, {ex['bench']}, {ex['T']} graph nodes, {ex['chars']} characters): the shortest trajectory with at least one tool call whose unanimous failure node is an agent_action that is not the final node. Step index = position in `topological_order`."))
