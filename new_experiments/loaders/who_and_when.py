"""Who&When (Kevin355/Who_and_When). One record per log; steps = history entries (incl. the human question).
Native convention: mistake_step is a 0-based index into history, so native_step == idx."""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

ROOT = os.path.join(DATA, 'who_and_when', 'Who&When')


def _agent(h):
    return h.get('name') or h.get('role') or 'unknown'


def base_agent(a):
    return re.sub(r'\s*\(.*\)$', '', str(a)).strip()


def _clean(v):
    return str(v).strip().strip('\'"')


def load(limit=None, subsets=('Hand-Crafted', 'Algorithm-Generated')):
    recs = []
    for sub in subsets:
        files = sorted(glob.glob(os.path.join(ROOT, sub, '*.json')), key=lambda p: int(os.path.basename(p).split('.')[0]))
        for f in files:
            d = read_json(f)
            steps = []
            for i, h in enumerate(d['history']):
                a = _agent(h)
                role = 'user' if a in ('human', 'user') else 'agent'
                steps.append(make_step(i, a, role, h.get('content', ''), native_step=i, meta={'base_agent': base_agent(a)}))
            ms = int(_clean(d['mistake_step']))
            ma = _clean(d['mistake_agent'])
            gt = d.get('ground_truth', d.get('groundtruth'))
            final = steps[-1]['content'] if steps else None
            recs.append(make_record('who_and_when', f'{sub}/{os.path.basename(f)}', d['question'], steps, subset=sub,
                                    ground_truth=gt, final_output=final, outcome='fail', error_steps=[ms], error_agent=ma,
                                    categories=[d['mistake_type']] if d.get('mistake_type') else [],
                                    reason=d.get('mistake_reason'),
                                    meta={'file': f, 'question_ID': _clean(d.get('question_ID')), 'level': d.get('level'),
                                          'system_prompt': d.get('system_prompt'), 'is_correct': d.get('is_correct')}))
            if limit and len(recs) >= limit:
                return recs
    return recs


if __name__ == '__main__':
    rs = load()
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps')
    r = rs[0]
    print(r['id'], r['labels'], [(s['idx'], s['agent'], len(s['content'])) for s in r['steps']][:8])
