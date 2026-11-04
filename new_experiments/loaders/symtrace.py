"""SymTrace / SymFail (arXiv:2608.25920), the paper's 536-case package only:
data/symtrace/extracted/SymFail/human_annotations_536.jsonl + initial_failure_logs_536/<mas>/<task_id>/attempt_000/
{graph.json, trajectory.json, result_record.json, api_records.jsonl}. Steps = graph nodes in topological_order
(kinds: sys_prompt, user_input, agent_action, tool_call, tool_result, final_result, error, ...); native_step = node_id.
labels.error_steps = [position of failure_node_id in topological_order]; categories = failure_labels (c1..c4);
extra = primary_failure_label, confidence, individual_annotations, inter_annotator_agreement.
Ground truth = trajectory.json task.reference_answer (stringified for WebArena evaluator specs)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json, read_jsonl

R = os.path.join(DATA, 'symtrace', 'extracted', 'SymFail')
CAT = {'c1': 'C1 Task-constraint violation', 'c2': 'C2 Repeated / stalled progress',
       'c3': 'C3 Unresolved runtime condition', 'c4': 'C4 Plan-action-outcome inconsistency'}
ROLE = {'sys_prompt': 'system', 'user_input': 'user', 'agent_action': 'agent', 'tool_call': 'agent',
        'tool_result': 'tool', 'final_result': 'agent', 'error': 'env'}


def node_text(nd):
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
        s = (f'[{t}] ' if t else '') + s
        if nd.get('thought'):
            s = 'Thought: ' + str(nd['thought']) + '\n' + s
        return s
    if k == 'tool_call':
        return 'Tool call: ' + json.dumps(nd.get('tool_call') or act, ensure_ascii=False)
    if k == 'tool_result':
        return 'Tool result: ' + str(obs.get('content') if obs.get('content') is not None else json.dumps(nd.get('tool_result'), ensure_ascii=False))
    if k == 'final_result':
        return 'Final answer: ' + str(nd.get('final_answer') if nd.get('final_answer') is not None else act.get('answer') or '')
    if k == 'error':
        return 'Error: ' + str(nd.get('error'))
    return json.dumps({'action': act, 'observation': obs}, ensure_ascii=False)


def _str(v):
    if v is None:
        return None
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def load(limit=None, mas=None):
    recs = []
    missing = 0
    for a in read_jsonl(os.path.join(R, 'human_annotations_536.jsonl')):
        if mas and a['mas'] not in mas:
            continue
        d = os.path.join(R, 'initial_failure_logs_536', a['mas'], a['task_id'], 'attempt_000')
        if not os.path.isdir(d):
            missing += 1
            continue
        g = read_json(os.path.join(d, 'graph.json'))
        nodes = {nd['node_id']: nd for nd in g['nodes']}
        order = [n for n in (g.get('topological_order') or [nd['node_id'] for nd in g['nodes']]) if n in nodes]
        tr = read_json(os.path.join(d, 'trajectory.json'))
        res = tr.get('result') or read_json(os.path.join(d, 'result_record.json'))
        task = tr.get('task') or {}
        steps = []
        for i, nid in enumerate(order):
            nd = nodes[nid]
            steps.append(make_step(i, nd.get('agent_id') or nd['kind'], ROLE.get(nd['kind'], 'env'), node_text(nd), native_step=nid,
                                   meta={'kind': nd['kind'], 'step_id': nd.get('step_id'), 'sequence_index': nd.get('sequence_index'),
                                         'parent_node_ids': nd.get('parent_node_ids'), 'has_api_messages': bool(nd.get('api_messages'))}))
        fid = a['failure_node_id']
        fidx = order.index(fid) if fid in nodes else None
        recs.append(make_record('symtrace', f"{a['mas']}/{a['task_id']}", task.get('task') or '', steps, subset=a['mas'],
                                ground_truth=_str(task.get('reference_answer')), final_output=_str(res.get('final_answer')),
                                outcome='fail', error_steps=[fidx] if fidx is not None else [],
                                error_agent=nodes[fid].get('agent_id') if fid in nodes else None,
                                categories=list(a.get('failure_labels') or []), reason=None,
                                extra={'primary_failure_label': a.get('primary_failure_label'), 'confidence': a.get('confidence'),
                                       'failure_node_kind': a.get('failure_node_kind'), 'failure_node_exists': a.get('failure_node_exists'),
                                       'failure_node_in_graph': fid in nodes,
                                       'individual_annotations': a.get('individual_annotations'),
                                       'inter_annotator_agreement': a.get('inter_annotator_agreement'),
                                       'category_names': [CAT.get(c, c) for c in a.get('failure_labels') or []],
                                       'evaluator_evidence': res.get('evaluator_evidence')},
                                meta={'file': os.path.join(d, 'graph.json'), 'framework': a['mas'],
                                      'benchmark': task.get('source_benchmark'), 'source_split': task.get('source_split'),
                                      'backbone': res.get('model'), 'task_type': task.get('task_type'),
                                      'difficulty': task.get('difficulty_tag'), 'annotation_id': a.get('annotation_id'),
                                      'case_id': a.get('case_id'), 'n_edges': len(g.get('edges') or [])}))
        if limit and len(recs) >= limit:
            break
    load.missing = missing
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps;', load.missing, 'missing dirs')
    print(Counter(r['subset'] for r in rs), Counter(s['meta']['kind'] for r in rs for s in r['steps']))
    r = rs[0]
    print(r['id'], r['labels']['error_steps'], r['labels']['error_agent'], r['labels']['categories'], [(s['idx'], s['agent'], s['role'], len(s['content'])) for s in r['steps']][:8])
