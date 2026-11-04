"""Unified record schema shared by all loaders.

record = {
  'dataset': str,            # loader slug
  'id': str,                 # unique within dataset (file name / row id)
  'subset': str|None,        # e.g. 'Hand-Crafted', 'tau2bench'
  'task': str,               # the user task / question
  'ground_truth': str|None,  # reference answer if released
  'final_output': str|None,  # the system's final answer if identifiable
  'outcome': 'fail'|'success'|None,
  'steps': [ {'idx': int,            # 0-based position in this list
              'agent': str,          # acting agent / role name as in the data (normalised lightly)
              'role': 'agent'|'user'|'tool'|'system'|'env',   # who produced the text
              'content': str,        # the text of the step (tool calls rendered inline)
              'native_step': any,    # the dataset's own index / id for this step (for mapping back)
              'meta': dict } ],
  'labels': { 'error_steps': [int],  # 0-based idx of labelled error step(s); [] if none; earliest first
              'error_agent': str|None,
              'categories': [str],   # failure-mode / category labels if any
              'reason': str|None,    # free-text rationale if any
              'votes': {int: int}|None,   # MP-Bench style per-step vote counts (idx -> n)
              'extra': dict },       # anything dataset-specific (t_lock, spans, per-annotator labels ...)
  'meta': dict }                     # source file, framework, backbone, benchmark, ...
"""
ROLES = {'agent', 'user', 'tool', 'system', 'env'}


def make_step(idx, agent, role, content, native_step=None, meta=None):
    assert role in ROLES, role
    return {'idx': idx, 'agent': str(agent), 'role': role, 'content': content if content is not None else '',
            'native_step': native_step, 'meta': meta or {}}


def make_record(dataset, id, task, steps, subset=None, ground_truth=None, final_output=None, outcome='fail',
                error_steps=None, error_agent=None, categories=None, reason=None, votes=None, extra=None, meta=None):
    for i, s in enumerate(steps):
        s['idx'] = i
    rec = {'dataset': dataset, 'id': str(id), 'subset': subset, 'task': task or '', 'ground_truth': ground_truth,
           'final_output': final_output, 'outcome': outcome, 'steps': steps,
           'labels': {'error_steps': sorted(set(error_steps or [])), 'error_agent': error_agent,
                      'categories': list(categories or []), 'reason': reason, 'votes': votes, 'extra': extra or {}},
           'meta': meta or {}}
    validate(rec)
    return rec


def validate(rec):
    n = len(rec['steps'])
    for k in rec['labels']['error_steps']:
        assert 0 <= k < n, (rec['dataset'], rec['id'], k, n)
    for s in rec['steps']:
        assert s['role'] in ROLES
    assert rec['outcome'] in ('fail', 'success', None)
    return True


PRIMARY_KEYS = ('root_cause_idx', 'primary_idx', 'critical_idx', 'earliest_majority_step')


def error_step(rec):
    """Primary labelled error step idx or None: the dataset's own primary label when the loader stored one in
    labels.extra (agentrx root cause, trail HIGH-impact span, searchauditbench critical message, mp_bench earliest
    majority-vote step), else the earliest labelled step."""
    ex = rec['labels'].get('extra') or {}
    for k in PRIMARY_KEYS:
        if ex.get(k) is not None:
            return int(ex[k])
    es = rec['labels']['error_steps']
    return es[0] if es else None


def agent_steps(rec):
    return [s for s in rec['steps'] if s['role'] == 'agent']
