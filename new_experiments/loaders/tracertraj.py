"""TracerTraj / AgenTracer data release v1.0.0 (data/tracertraj/extracted/agentracer-data-v1.0.0/{agentic,coding,math}/{train,test}.jsonl).
history entries {step, role, name?, content}; mistake_step is a string. The `step` field is 1-based in agentic and 0-based in
coding/math; the labelled step is found by matching history[i].step == int(mistake_step) (checked empirically: this
matches the mistake_agent name/role in 100% of rows in every domain, versus 83-89% for +-1 offsets), i.e.
idx = mistake_step - 1 (agentic) and idx = mistake_step (coding, math). subset = domain/split; extra = error_source."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA

ROOT = os.path.join(DATA, 'tracertraj', 'extracted', 'agentracer-data-v1.0.0')
DOMAINS = ('agentic', 'coding', 'math')
SPLITS = ('train', 'test')


def agent_of(x):
    return x.get('name') or x.get('role') or 'unknown'


def load(limit=None, domains=DOMAINS, splits=SPLITS):
    recs = []
    for dom in domains:
        for sp in splits:
            f = os.path.join(ROOT, dom, f'{sp}.jsonl')
            with open(f, encoding='utf-8') as fh:
                for ln, line in enumerate(fh):
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    h = d['history']
                    steps = []
                    for i, x in enumerate(h):
                        a = agent_of(x)
                        role = 'user' if x.get('role') == 'user' or a in ('user', 'human') else ('system' if x.get('role') == 'system' else 'agent')
                        steps.append(make_step(i, a, role, x.get('content') or '', native_step=x.get('step'), meta={'native_role': x.get('role')}))
                    ms = int(str(d['mistake_step']).strip())
                    pos = next((i for i, x in enumerate(h) if x.get('step') == ms), None)
                    if pos is None:  # fall back to the domain convention
                        pos = ms - 1 if dom == 'agentic' else ms
                    err = [pos] if 0 <= pos < len(steps) else []
                    final = next((s['content'] for s in reversed(steps) if s['role'] == 'agent'), None)
                    recs.append(make_record('tracertraj', f"{dom}/{sp}/{ln}_{d['question_ID']}", d.get('question'), steps,
                                            subset=f'{dom}/{sp}', ground_truth=d.get('ground_truth'), final_output=final, outcome='fail',
                                            error_steps=err, error_agent=d.get('mistake_agent'), categories=[],
                                            reason=d.get('mistake_reason'),
                                            extra={'error_source': d.get('error_source'), 'mistake_step_raw': d['mistake_step'],
                                                   'step_offset': 'idx = mistake_step - 1' if dom == 'agentic' else 'idx = mistake_step'},
                                            meta={'file': f, 'domain': dom, 'split': sp, 'line': ln, 'question_ID': d['question_ID'],
                                                  'framework': {'agentic': 'OPPO deep-research agent (single assistant)', 'coding': 'multi-agent coding (AgenTracer)', 'math': 'multi-agent math (AgenTracer)'}[dom]}))
                    if limit and len(recs) >= limit:
                        return recs
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    print(Counter(r['subset'] for r in rs))
    m = Counter()
    for r in rs:
        m[(r['subset'].split('/')[0], r['steps'][r['labels']['error_steps'][0]]['agent'] == r['labels']['error_agent'])] += 1
    print(sorted(m.items()))
    r = rs[0]
    print(r['id'], r['labels']['error_steps'], r['labels']['error_agent'], [(s['native_step'], s['agent'], len(s['content'])) for s in r['steps']][:4])
