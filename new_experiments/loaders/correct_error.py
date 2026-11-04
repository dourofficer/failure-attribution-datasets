"""CORRECT-Error (yifanyu/CORRECT-Error), parquet test split (2,226 rows) under data/correct_error/CORRECT-Error/data/.
history = [{role, content}]; mistake_step is a 0-based index into history (the user message is index 0), so
native_step == idx. No ground-truth answer and no mistake_reason beyond what the parquet carries."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA

FILE = os.path.join(DATA, 'correct_error', 'CORRECT-Error', 'data', 'test-00000-of-00001.parquet')


def norm_agent(a):
    return re.sub(r'\s*\(.*\)$', '', (a or '').strip().strip('[]').strip()).strip()


def _get(row, k):
    v = row.get(k) if hasattr(row, 'get') else None
    try:
        import math
        if isinstance(v, float) and math.isnan(v):
            return None
    except Exception:  # noqa
        pass
    return v


def load(limit=None):
    import pandas as pd
    df = pd.read_parquet(FILE)
    recs = []
    for _, row in df.iterrows():
        row = row.to_dict()
        h = list(row['history'])
        steps = []
        for i, m in enumerate(h):
            a = m.get('role') or 'unknown'
            role = 'user' if a.lower() in ('user', 'human') else 'agent'
            steps.append(make_step(i, a, role, m.get('content') or '', native_step=i, meta={'base_agent': norm_agent(a)}))
        ms = int(row['mistake_step'])
        task = _get(row, 'question') or (steps[0]['content'] if steps else '')
        final = next((s['content'] for s in reversed(steps) if s['role'] == 'agent'), None)
        recs.append(make_record('correct_error', str(row['trajectory_id']), task, steps, subset=str(row.get('dataset')),
                                ground_truth=_get(row, 'groundtruth') or _get(row, 'ground_truth'), final_output=final, outcome='fail',
                                error_steps=[ms] if 0 <= ms < len(steps) else [], error_agent=norm_agent(row.get('mistake_agent')),
                                categories=[], reason=_get(row, 'mistake_reason') or None,
                                extra={'mistake_agent_raw': row.get('mistake_agent')},
                                meta={'file': FILE, 'benchmark': row.get('dataset'), 'backbone': row.get('generator_model'),
                                      'gaia_level': _get(row, 'gaia_level'), 'question_id': row.get('question_id'),
                                      'framework': 'Magentic-One variant (AutoGen selector group chat)',
                                      'other_columns': {k: (str(v)[:200] if v is not None else None) for k, v in row.items()
                                                        if k not in ('history', 'question', 'trajectory_id', 'dataset', 'generator_model', 'gaia_level', 'question_id', 'mistake_step', 'mistake_agent', 'mistake_reason', 'groundtruth')}}))
        if limit and len(recs) >= limit:
            break
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    print(Counter(r['subset'] for r in rs))
    m = [r['steps'][r['labels']['error_steps'][0]]['meta']['base_agent'] == r['labels']['error_agent'] for r in rs if r['labels']['error_steps']]
    print('agent match', sum(m), '/', len(m))
    print(rs[0]['id'], rs[0]['labels'], rs[0]['meta']['other_columns'])
