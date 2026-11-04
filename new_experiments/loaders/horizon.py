"""HORIZON (xwang2775/long-horizon-agent-failures): data/horizon/hf/result_2/classified_results.json (3,782 LLM-judge
records over web / os / database / embodied runs) + result_5/classified_results.json (371 web/GPT records with a
failure_step_number; 147 share an id with result_2 and are merged into those records, the other 224 are appended as
records with meta['source']='result_5' unless include_r5_only=False).
Steps: web '[Step n]' blocks (native_step = n; content = Page/Agent/Action lines); os = the '[Task]' block as a user
step then alternating '[Agent]' (agent) / '[OS response]' (env) blocks; database and embodied = one step with the whole
record. outcome from passed / score (>= 1.0 -> success); the judge label failure_type ('Success' or a category) is in
meta['judge_failure_type'] and categories = [failure_type] when it is not 'Success'. error_steps: web records with a
failure_step_number n -> idx of the '[Step n]' block (if n exceeds the number of blocks the label is left unmapped and
kept in extra['failure_step_number'])."""
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

ROOT = os.path.join(DATA, 'horizon', 'hf')
MODEL = {'gpt': 'gpt-5-mini', 'claude': 'claude-4-sonnet'}


def _b(v):
    if isinstance(v, str):
        return {'true': True, 'false': False}.get(v.strip().lower())
    return v


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _i(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def parse_web(t, model):
    head, *parts = re.split(r'^\[Step (\d+)\]\n', t, flags=re.M)
    task = re.search(r'^Task: (.*)$', head, re.M)
    exp = re.search(r'^Expected answer: (.*)$', head, re.M)
    steps = []
    for i in range(0, len(parts), 2):
        n = int(parts[i])
        body = parts[i + 1].strip()
        page = re.search(r'^Page\s*:\s*(.*)$', body, re.M)
        agent = re.search(r'^Agent:\s*(.*?)(?=^Action:|\Z)', body, re.M | re.S)
        action = re.search(r'^Action:\s*(.*)$', body, re.M | re.S)
        c = ''
        if page:
            c += 'Observation: ' + page.group(1).strip() + '\n'
        if agent:
            c += 'Thought: ' + agent.group(1).strip() + '\n'
        if action:
            c += 'Action: ' + action.group(1).strip()
        steps.append(make_step(len(steps), f'web agent ({model})', 'agent', c.strip() or body, native_step=n))
    m = re.search(r'stop \[(.*?)\]', t)
    return (task.group(1).strip() if task else head.strip()), (exp.group(1).strip() if exp else None), steps, (m.group(1) if m else None)


def parse_os(t, model):
    parts = re.split(r'^\[(Task|Agent|OS response)\]\n', t, flags=re.M)
    steps = []
    task = None
    for i in range(1, len(parts) - 1, 2):
        kind, body = parts[i], parts[i + 1].strip()
        if kind == 'Task':
            task = body
            steps.append(make_step(len(steps), 'user', 'user', body, native_step='task'))
        elif kind == 'Agent':
            steps.append(make_step(len(steps), f'os agent ({model})', 'agent', body, native_step=sum(1 for s in steps if s['role'] == 'agent') + 1))
        else:
            steps.append(make_step(len(steps), 'OS', 'env', body, native_step=None))
    final = None
    m = re.findall(r'answer\((.*?)\)', t)
    if m:
        final = m[-1]
    return task or parts[0].strip(), None, steps, final


def parse_db(t, model):
    q = re.search(r'^Question\s*:\s*(.*)$', t, re.M)
    gold = re.search(r'^Gold\s+SQL\s*:\s*(.*)$', t, re.M)
    agent = re.search(r'^Agent SQL\s*:\s*(.*)$', t, re.M)
    return (q.group(1).strip() if q else t[:500]), (gold.group(1).strip() if gold else None), \
        [make_step(0, f'sql agent ({model})', 'agent', t, native_step=1)], (agent.group(1).strip() if agent else None)


def parse_embodied(t, model):
    task = re.search(r'^Task: (.*)$', t, re.M)
    return (task.group(1).strip() if task else t[:300]), None, [make_step(0, f'embodied planner ({model})', 'agent', t, native_step=1)], None


PARSE = {'web': parse_web, 'os': parse_os, 'database': parse_db, 'embodied': parse_embodied}


def _record(x, source, r5=None):
    model = MODEL.get(x.get('model'), x.get('model'))
    task, gt, steps, final = PARSE.get(x['domain'], parse_embodied)(x.get('trajectory') or '', model)
    passed, score = _b(x.get('passed')), _f(x.get('score'))
    if passed is not None:
        outcome = 'success' if passed else 'fail'
    elif score is not None:
        outcome = 'success' if score >= 1.0 else 'fail'
    else:
        outcome = None
    ft = x.get('failure_type')
    fs = _i((r5 or x).get('failure_step_number'))
    err = []
    mapped = None
    if fs is not None and x['domain'] == 'web':
        mapped = next((s['idx'] for s in steps if s['native_step'] == fs), None)
        if mapped is not None:
            err = [mapped]
    judge_steps = (r5 or x).get('steps')
    if isinstance(judge_steps, str):
        try:
            judge_steps = ast.literal_eval(judge_steps)
        except Exception:  # noqa
            pass
    return make_record('horizon', x['id'], task, steps, subset=x['domain'], ground_truth=gt, final_output=final, outcome=outcome,
                       error_steps=err, error_agent=steps[err[0]]['agent'] if err else None,
                       categories=[ft] if ft and ft != 'Success' else [], reason=x.get('reason'),
                       extra={'failure_step_number': fs, 'failure_step_mapped': mapped is not None if fs is not None else None,
                              'judge_failure_type': ft, 'judge_step_windows': judge_steps, 'r5_failure_type': r5.get('failure_type') if r5 else None,
                              'r5_reason': r5.get('reason') if r5 else None, 'existing_category': x.get('existing_category')},
                       meta={'file': os.path.join(ROOT, source, 'classified_results.json'), 'source': source, 'framework': f"{x['domain']} agent",
                             'benchmark': {'web': 'WebArena (admin)', 'os': 'AgentBench OS', 'database': 'BIRD / MAC-SQL', 'embodied': 'IsaacSim bimanual'}.get(x['domain']),
                             'backbone': model, 'run': x.get('run'), 'task_id': x.get('task_id'), 'passed': passed, 'score': score,
                             'judge': 'LLM-as-a-judge (not human)', 'has_r5_label': r5 is not None})


def load(limit=None, domains=None, include_r5_only=True):
    main = read_json(os.path.join(ROOT, 'result_2', 'classified_results.json'))
    r5 = {x['id']: x for x in read_json(os.path.join(ROOT, 'result_5', 'classified_results.json'))}
    recs = []
    seen = set()
    for x in main:
        if domains and x['domain'] not in domains:
            continue
        seen.add(x['id'])
        recs.append(_record(x, 'result_2', r5.get(x['id'])))
        if limit and len(recs) >= limit:
            return recs
    if include_r5_only:
        for xid, x in r5.items():
            if xid in seen or (domains and x['domain'] not in domains):
                continue
            recs.append(_record(x, 'result_5', x))
            if limit and len(recs) >= limit:
                return recs
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    print(Counter(r['meta']['source'] for r in rs), Counter(r['subset'] for r in rs), Counter(r['outcome'] for r in rs))
    fs = [r for r in rs if r['labels']['extra']['failure_step_number'] is not None]
    print(len(fs), 'with failure_step_number;', sum(1 for r in fs if r['labels']['extra']['failure_step_mapped']), 'mapped')
    print(Counter((r['outcome'], r['labels']['extra']['judge_failure_type'] == 'Success') for r in rs))
