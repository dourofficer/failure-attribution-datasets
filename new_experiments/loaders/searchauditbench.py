"""SearchAuditBench: data/searchauditbench/extracted/benchmark_data_1243.jsonl (313 MB, streamed line by line).
Steps = trajectory messages ({message_index, role, content, reasoning_content?, tool_calls?, name?}); message_index
is 0-based and contiguous so native_step == idx (asserted; otherwise the labelled index is mapped by message_index).
Content = reasoning_content (as 'Reasoning:') + content + rendered tool_calls. labels.error_steps = [critical_step.message_index]
+ the other indices of the tolerance span (sorted by make_record); extra['critical_idx'] keeps the strict critical
message; extra also has span_start/end, repair_directive, repair_rubrics, rationale. categories = [root_cause_primary];
ground_truth = gold_answer; final_output = predicted_answer. Fields that are JSON-encoded strings are decoded."""
import ast
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA

FILE = os.path.join(DATA, 'searchauditbench', 'extracted', 'benchmark_data_1243.jsonl')


def J(v):
    if isinstance(v, str):
        s = v.strip()
        if s[:1] in '{[':
            try:
                return json.loads(s)
            except Exception:  # noqa
                try:
                    return ast.literal_eval(s)
                except Exception:  # noqa
                    return v
    return v


def render(m):
    parts = []
    if m.get('reasoning_content'):
        parts.append('Reasoning: ' + str(m['reasoning_content']))
    if m.get('content'):
        parts.append(str(m['content']))
    tc = m.get('tool_calls')
    if tc:
        parts.append('Tool calls: ' + json.dumps(tc, ensure_ascii=False))
    return '\n'.join(parts)


def load(limit=None, models=None, datasets=None):
    recs = []
    with open(FILE, encoding='utf-8') as fh:
        for ln, line in enumerate(fh):
            if not line.strip():
                continue
            d = json.loads(line)
            if models and d.get('model') not in models:
                continue
            if datasets and d.get('dataset') not in datasets:
                continue
            tr = d['trajectory']
            steps = []
            by_mi = {}
            for i, m in enumerate(tr):
                role = {'assistant': 'agent', 'user': 'user', 'system': 'system', 'tool': 'tool'}.get(m['role'], 'env')
                agent = m['role'] if m['role'] != 'tool' else f"tool:{m.get('name') or ''}".rstrip(':')
                steps.append(make_step(i, agent, role, render(m), native_step=m.get('message_index'),
                                       meta={'native_role': m['role'], 'tool_call_id': m.get('tool_call_id'),
                                             'has_reasoning': bool(m.get('reasoning_content'))}))
                by_mi.setdefault(m.get('message_index'), i)
            cs = J(d['critical_step'])
            k = by_mi.get(cs['message_index'])
            ks, ke = cs.get('span_start_message_index'), cs.get('span_end_message_index')
            span = [by_mi[j] for j in range(ks, ke + 1) if j in by_mi] if ks is not None and ke is not None else []
            err = ([k] if k is not None else []) + [j for j in span if j != k]
            rat = J(d.get('rationale'))
            recs.append(make_record('searchauditbench', str(d['index']), d.get('query'), steps, subset=d.get('dataset'),
                                    ground_truth=d.get('gold_answer'), final_output=d.get('predicted_answer'), outcome='fail',
                                    error_steps=err, error_agent='assistant', categories=[d['root_cause_primary']] if d.get('root_cause_primary') else [],
                                    reason=(rat.get('failure_rationale') if isinstance(rat, dict) else rat) if rat else None,
                                    extra={'critical_idx': k, 'critical_step': cs, 'span_start': ks, 'span_end': ke, 'span_idxs': span,
                                           'rationale': rat, 'repair_directive': d.get('repair_directive'),
                                           'repair_rubrics': J(d.get('repair_rubrics'))},
                                    meta={'file': FILE, 'line': ln, 'backbone': d.get('model'), 'benchmark': d.get('dataset'),
                                          'framework': 'single deep-search agent (tool-calling)'}))
            if limit and len(recs) >= limit:
                break
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    print(Counter(r['subset'] for r in rs))
    print('native==idx', all(s['native_step'] == s['idx'] for r in rs for s in r['steps']))
    print(Counter(r['steps'][r['labels']['extra']['critical_idx']]['agent'] for r in rs))
    print(rs[0]['id'], rs[0]['labels']['error_steps'], rs[0]['labels']['categories'])
