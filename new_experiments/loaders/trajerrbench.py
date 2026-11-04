"""TrajErrBench (TrajDebug repo): data/trajerrbench/repo_TrajDebug/data/trajerrbench/en/{tau2bench,swebenchpro}/*.json
(486 = 400 + 86; the zh edition and the converted whoandwhen/ and agentdebugbench/ copies are not loaded).
messages {step, role, name, content, judgable, compress_role}; step is a contiguous 0-based index so native_step == idx.
metadata.annotation.critical_error_step is 0-based = idx; categories = [critical_error_type]; subset = source benchmark."""
import ast
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

R = os.path.join(DATA, 'trajerrbench', 'repo_TrajDebug', 'data', 'trajerrbench', 'en')
ROLE = {'assistant': 'agent', 'user': 'user', 'system': 'system', 'tool': 'tool'}


def _extra(v):
    if isinstance(v, str):
        try:
            return ast.literal_eval(v)
        except Exception:  # noqa
            return {'raw': v}
    return v or {}


def load(limit=None, subsets=('tau2bench', 'swebenchpro')):
    recs = []
    for sub in subsets:
        for p in sorted(glob.glob(os.path.join(R, sub, '*.json'))):
            d = read_json(p)
            md = d['metadata']
            ann = md.get('annotation') or {}
            msgs = d['messages']
            steps = []
            for i, m in enumerate(msgs):
                steps.append(make_step(i, m.get('name') or m['role'], ROLE.get(m['role'], 'env'), m.get('content') or '',
                                       native_step=m.get('step'), meta={'native_role': m['role'], 'judgable': m.get('judgable'),
                                                                        'compress_role': m.get('compress_role')}))
            k = ann.get('critical_error_step')
            if k is not None and not (0 <= k < len(steps) and msgs[k].get('step') == k):
                k = next((i for i, m in enumerate(msgs) if m.get('step') == k), k)
            tid = md['task_id']
            if sub == 'tau2bench':
                dom, model = tid.split('_failed_')[0], tid.split('_failed_')[1].split('::')[0]
            else:
                dom, model = 'swe', tid.split('_instance_')[0]
            reward = md.get('reward')
            try:
                reward = float(reward)
            except (TypeError, ValueError):
                pass
            final = next((s['content'] for s in reversed(steps) if s['role'] == 'agent'), None)
            recs.append(make_record('trajerrbench', f'{sub}/{os.path.basename(p)[:-5]}', md.get('task_description'), steps, subset=sub,
                                    ground_truth=None, final_output=final, outcome='fail' if reward in (0, 0.0, '0') else ('success' if reward in (1, 1.0, '1') else 'fail'),
                                    error_steps=[k] if k is not None and 0 <= k < len(steps) else [],
                                    error_agent=steps[k]['agent'] if k is not None and 0 <= k < len(steps) else None,
                                    categories=[ann['critical_error_type']] if ann.get('critical_error_type') else [],
                                    reason=ann.get('human_rationale'),
                                    extra={'annotation': ann, 'module': (ann.get('critical_error_type') or '').split('.')[0] or None,
                                           'reward': reward, 'n_judgable': sum(1 for m in msgs if m.get('judgable'))},
                                    meta={'file': p, 'framework': 'tau2-bench single assistant' if sub == 'tau2bench' else 'SWE-Agent-style single assistant',
                                          'benchmark': sub, 'domain': dom, 'backbone': model, 'task_id': tid, 'extra': _extra(md.get('extra'))}))
            if limit and len(recs) >= limit:
                return recs
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    print(Counter(r['subset'] for r in rs), Counter(r['outcome'] for r in rs), Counter(r['labels']['error_agent'] for r in rs))
    print('native==idx', all(s['native_step'] == s['idx'] for r in rs for s in r['steps']))
