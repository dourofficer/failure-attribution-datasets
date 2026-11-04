"""LongRCA Bench (CLoud5-real/longrca-bench). One record per JSON under data/longrca/data/full/<source>/<source>__NNN.json
(1,140; the 200 mini trajectories are a subset -> meta['mini']). history entries {step, name, role, content}; step is a
contiguous 0-based index so native_step == idx; mistake_step is 0-based. role 'user' entries are terminal / tool /
evaluator records -> role 'tool' (the first 'human' entry -> role 'user'); 'assistant' entries -> 'agent'."""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

ROOT = os.path.join(DATA, 'longrca', 'data')


def base_agent(a):
    return re.sub(r'\s*\(.*\)$', '', str(a)).strip()


def load(limit=None, sources=None, mini_only=False):
    mini = set()
    for f in glob.glob(os.path.join(ROOT, 'mini', '*', '*.json')):
        mini.add(os.path.basename(f)[:-5])
    recs = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'full', '*', '*.json'))):
        d = read_json(f)
        qid = d['question_ID']
        src = qid.split('__')[0]
        if sources and src not in sources:
            continue
        if mini_only and qid not in mini:
            continue
        steps = []
        for i, h in enumerate(d['history']):
            name = h.get('name') or h.get('role') or 'unknown'
            if h.get('role') == 'assistant':
                role = 'agent'
            elif name in ('human', 'user') and i == 0:
                role = 'user'
            else:
                role = 'tool'
            steps.append(make_step(i, name, role, h.get('content') or '', native_step=h.get('step'),
                                   meta={'native_role': h.get('role'), 'base_agent': base_agent(name)}))
        ms = int(str(d['mistake_step']).strip())
        task = steps[0]['content'] if steps else ''
        final = next((s['content'] for s in reversed(steps) if s['role'] == 'agent'), None)
        recs.append(make_record('longrca', qid, task, steps, subset=src, ground_truth=None, final_output=final,
                                outcome='fail', error_steps=[ms], error_agent=d['mistake_agent'], categories=[],
                                reason=d.get('mistake_reason'),
                                meta={'file': f, 'mini': qid in mini, 'benchmark': src, 'framework': 'longrca-' + src,
                                      'task_is_first_step': True}))
        if limit and len(recs) >= limit:
            return recs
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(r['meta']['mini'] for r in rs), 'mini')
    print(Counter(r['subset'] for r in rs))
    m = [r['steps'][r['labels']['error_steps'][0]]['agent'] == r['labels']['error_agent'] for r in rs]
    print('agent match', sum(m), '/', len(m))
    r = rs[0]
    print(r['id'], r['labels']['error_steps'], r['labels']['error_agent'], [(s['idx'], s['agent'], s['role'], len(s['content'])) for s in r['steps']][:6])
