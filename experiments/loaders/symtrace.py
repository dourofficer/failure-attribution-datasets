"""SymFail (SymTrace, arXiv:2608.25920) loader -- the paper's 536-case package only.

Files: data/symtrace/extracted/SymFail/human_annotations_536.jsonl and one bundle per case under
initial_failure_logs_536/<mas>/<task_id>/attempt_000/{graph.json, trajectory.json, result_record.json,
api_records.jsonl}.  The newer 437-case package is NOT loaded (different study, failure node always the
final node).

Step unit / index mapping
-------------------------
One node of graph.json ``topological_order`` = one step, in that order (0-based).  Node 0 is always the
``sys_prompt`` node and node 1 the ``user_input`` node; the remaining nodes are ``agent_action``,
``tool_call``, ``tool_result`` and the closing ``final_result`` (no ``error`` node occurs in the package).
``steps[i].native_idx`` is the node-id suffix (e.g. ``agent_action_0000``, ``ag2_hook_0001_d2cddc1d``).
The annotation's ``failure_node_id`` is mapped with ``faulty_step = topological_order.index(failure_node_id)``;
``faulty_steps = [faulty_step]``.  Every annotator's individual ``failure_node_id`` is mapped the same way in
``annotation.extra.individual_annotations[*].failure_step_idx``.

Role by node kind: sys_prompt -> system, user_input -> user, agent_action -> agent, tool_call -> agent (the
agent's decision rendered as the call), tool_result -> tool, final_result -> agent, error -> env.  One
deliberate exception: Magentic-One bundles contain ``agent_action`` nodes whose ``agent_id`` is ``user``
(autogen's echo of the task message); these get role ``user`` (102 of the 536 failure nodes point at such a
node -- see the report notes).  Hook-captured ``agent_action`` nodes (``agent_id`` ``masd_*_assistant``)
usually repeat the text of the following framework-level ``agent_action``; both are kept as steps.

Content: sys_prompt/user_input -> observation.content; agent_action -> the message text
(action.message.content or action.content); tool_call -> ``[tool_call] <type> <json>``;
tool_result -> ``[tool_result] <observation.content>``; final_result -> ``[final_result] <answer>``.
Nothing is truncated.  ``ground_truth`` is the AssistantBench reference answer or, for WebArena-Verified,
the JSON of the evaluator specification (there is no single reference string).  Every case is a failure
(outcome 0).  subset = mas in {ag2, crewai, magnetic_one}.
"""
import json
import os

SLUG = 'symtrace'
ROOT = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/symtrace/extracted/SymFail'
ANN = os.path.join(ROOT, 'human_annotations_536.jsonl')
LOGS = os.path.join(ROOT, 'initial_failure_logs_536')
MAS_NAME = {'ag2': 'AG2', 'crewai': 'CrewAI', 'magnetic_one': 'Magentic-One'}
CAT = {'c1': 'C1 Task-constraint violation', 'c2': 'C2 Repeated / stalled progress',
       'c3': 'C3 Unresolved runtime condition', 'c4': 'C4 Plan-action-outcome inconsistency'}
ROLE_BY_KIND = {'sys_prompt': 'system', 'user_input': 'user', 'agent_action': 'agent', 'tool_call': 'agent',
                'tool_result': 'tool', 'final_result': 'agent', 'error': 'env'}


def _jload(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def _text(v):
    if v is None:
        return ''
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


def node_content(nd):
    k = nd['kind']
    act = nd.get('action') or {}
    obs = nd.get('observation') or {}
    if k in ('sys_prompt', 'user_input'):
        return _text(obs.get('content'))
    if k == 'agent_action':
        msg = act.get('message')
        if isinstance(msg, dict) and msg.get('content') is not None:
            return _text(msg['content'])
        if act.get('content') is not None:
            return _text(act['content'])
        if msg is not None:
            return _text(msg)
        return _text({kk: vv for kk, vv in act.items() if kk != 'type'})
    if k == 'tool_call':
        tc = nd.get('tool_call') or act
        t = (tc or {}).get('type') or act.get('type') or 'tool'
        return f'[tool_call] {t} ' + _text(tc)
    if k == 'tool_result':
        body = obs.get('content')
        if not body:
            body = _text(nd.get('tool_result'))
        return '[tool_result] ' + _text(body)
    if k == 'final_result':
        ans = nd.get('final_answer')
        if ans is None:
            ans = act.get('answer')
        return '[final_result] ' + _text(ans)
    if k == 'error':
        return '[error] ' + _text(nd.get('error'))
    return _text({'action': act, 'observation': obs})


def node_role(nd):
    if nd.get('agent_id') == 'user':
        return 'user'
    return ROLE_BY_KIND.get(nd['kind'], 'env')


def _count_lines(p):
    n = 0
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    n += 1
    return n


def load(limit=None, subset=None):
    n = 0
    with open(ANN, encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            a = json.loads(line)
            if subset is not None and a['mas'] != subset:
                continue
            d = os.path.join(LOGS, a['mas'], a['task_id'], 'attempt_000')
            g = _jload(os.path.join(d, 'graph.json'))
            nodes = {nd['node_id']: nd for nd in g['nodes']}
            order = [nid for nid in (g.get('topological_order') or [nd['node_id'] for nd in g['nodes']]) if nid in nodes]
            tr = _jload(os.path.join(d, 'trajectory.json'))
            task = tr.get('task') or {}
            res = _jload(os.path.join(d, 'result_record.json'))
            cs = (g.get('metadata') or {}).get('capture_summary') or {}
            pos = {nid: i for i, nid in enumerate(order)}
            steps = []
            for i, nid in enumerate(order):
                nd = nodes[nid]
                act = nd.get('action') or {}
                meta = {'kind': nd['kind'], 'node_id': nid, 'source': (nd.get('metadata') or {}).get('source'),
                        'sequence_index': nd.get('sequence_index'), 'step_id': nd.get('step_id')}
                if act.get('type'):
                    meta['action_type'] = act['type']
                if nd['kind'] == 'agent_action' and act.get('parsed_action') is not None:
                    meta['parsed_action'] = act['parsed_action']
                if nd.get('api_messages'):
                    meta['n_api_messages'] = len(nd['api_messages'])
                if nd['kind'] == 'tool_result' and isinstance(nd.get('tool_result'), dict):
                    meta['tool_status'] = nd['tool_result'].get('status')
                    meta['tool_status_code'] = nd['tool_result'].get('status_code')
                if nd['kind'] == 'tool_call':
                    meta['tool_name'] = ((nd.get('tool_call') or act) or {}).get('type')
                steps.append({'idx': i, 'native_idx': nid.rsplit(':', 1)[-1], 'agent': str(nd.get('agent_id') or ''),
                              'role': node_role(nd), 'content': node_content(nd), 'meta': meta})
            fid = a['failure_node_id']
            fidx = pos.get(fid)
            fnode = nodes.get(fid)
            indiv = []
            for x in a.get('individual_annotations') or []:
                x = dict(x)
                x['failure_step_idx'] = pos.get(x.get('failure_node_id'))
                indiv.append(x)
            ref = task.get('reference_answer')
            if ref is None:
                ref = (task.get('evaluator') or {}).get('answer')
            ground_truth = ref if isinstance(ref, str) or ref is None else json.dumps(ref, ensure_ascii=False)
            primary = a['primary_failure_label']
            yield {
                'dataset': SLUG,
                'id': f"{a['mas']}/{a['task_id']}",
                'subset': a['mas'],
                'system': MAS_NAME.get(a['mas'], a['mas']),
                'task': task.get('task') or '',
                'ground_truth': ground_truth,
                'final_output': res.get('final_answer'),
                'outcome': 0,
                'steps': steps,
                'annotation': {
                    'faulty_step': fidx,
                    'faulty_steps': [fidx] if fidx is not None else [],
                    'faulty_agent': str(fnode['agent_id']) if fnode else None,
                    'category': CAT.get(primary, primary),
                    'reason': None,  # rationales/evidence are withheld from the public export
                    'extra': {
                        'primary_failure_label': primary,
                        'failure_labels': list(a.get('failure_labels') or []),
                        'failure_label_names': [CAT.get(c, c) for c in (a.get('failure_labels') or [])],
                        'confidence': a.get('confidence'),
                        'failure_node_id': fid,
                        'failure_node_kind': a.get('failure_node_kind'),
                        'failure_node_exists': a.get('failure_node_exists'),
                        'inter_annotator_agreement': a.get('inter_annotator_agreement'),
                        'individual_annotations': indiv,
                        'annotation_status': a.get('annotation_status'),
                        'annotation_protocol_version': a.get('annotation_protocol_version'),
                        'evaluator_evidence': res.get('evaluator_evidence'),
                        'suspicious_labels': res.get('suspicious_labels'),
                    },
                },
                'meta': {
                    'mas': a['mas'], 'case_id': a.get('case_id'), 'annotation_id': a.get('annotation_id'),
                    'task_id': a['task_id'],
                    'source_benchmark': task.get('source_benchmark'), 'source_split': task.get('source_split'),
                    'source_task_id': task.get('source_task_id'), 'task_type': task.get('task_type'),
                    'difficulty_tag': task.get('difficulty_tag'), 'evaluator_type': (task.get('evaluator') or {}).get('type'),
                    'start_urls': task.get('start_urls'),
                    'model': res.get('model'), 'temperature': res.get('temperature'), 'latency': res.get('latency'),
                    'token_usage': res.get('token_usage'), 'success': res.get('success'),
                    'llm_call_count': cs.get('llm_call_count'), 'tool_failure_count': cs.get('tool_failure_count'),
                    'tool_result_count': cs.get('tool_result_count'), 'api_records': _count_lines(os.path.join(d, 'api_records.jsonl')),
                    'n_nodes': len(order), 'n_edges': len(g.get('edges') or []),
                    'dir': d, 'license': 'CC BY 4.0 (SymFail annotations/graphs); tasks keep their own terms',
                },
            }
            n += 1
            if limit is not None and n >= limit:
                return
