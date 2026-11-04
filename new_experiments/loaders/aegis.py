"""AEGIS (Fancylalala/AEGIS): data/aegis/Aegis-Bench/test.jsonl (600) + Aegis-Training/{train,val}.jsonl (7,146 + 1,787).
Steps = input.conversation_history turns ({step (1-based), agent_name, agent_role?, content, phase, is_injected?}).
labels: error_agent = first faulty agent (output.faulty_agents[0]); categories = all error_type values;
extra = faulty_agents list, injected_agents (with malicious_action_description), is_injection_successful;
error_steps = [first turn with is_injected true] if any turn carries the flag, else [] (most rows have no step-level marker)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA

FILES = {'test': 'Aegis-Bench/test.jsonl', 'train': 'Aegis-Training/train.jsonl', 'val': 'Aegis-Training/val.jsonl'}


def load(limit=None, splits=('test', 'train', 'val')):
    recs = []
    for sp in splits:
        f = os.path.join(DATA, 'aegis', FILES[sp])
        with open(f, encoding='utf-8') as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                h = d['input']['conversation_history']
                md = d.get('metadata') or {}
                fa = d['output']['faulty_agents']
                steps = []
                for i, x in enumerate(h):
                    a = x.get('agent_name') or 'unknown'
                    role = 'user' if a.lower() in ('user', 'human') else 'agent'
                    steps.append(make_step(i, a, role, x.get('content') or '', native_step=x.get('step'),
                                           meta={'phase': x.get('phase'), 'agent_role': x.get('agent_role'), 'is_injected': x.get('is_injected')}))
                inj_steps = [i for i, x in enumerate(h) if x.get('is_injected')]
                recs.append(make_record('aegis', f"{sp}/{d['id']}", d['input'].get('query'), steps, subset=sp,
                                        ground_truth=d['ground_truth'].get('correct_answer'), final_output=d['input'].get('final_output'),
                                        outcome='fail', error_steps=inj_steps[:1], error_agent=fa[0]['agent_name'] if fa else None,
                                        categories=[x['error_type'] for x in fa], reason=None,
                                        extra={'faulty_agents': fa, 'injected_agents': d['ground_truth'].get('injected_agents'),
                                               'is_injection_successful': d['ground_truth'].get('is_injection_successful'),
                                               'injected_steps': inj_steps, 'has_step_marker': any('is_injected' in x for x in h)},
                                        meta={'file': f, 'framework': md.get('framework'), 'benchmark': md.get('benchmark'),
                                              'backbone': md.get('model'), 'task_type': md.get('task_type'),
                                              'num_agents': md.get('num_agents'), 'num_injected_agents': md.get('num_injected_agents')}))
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
        if r['labels']['error_steps']:
            a = r['steps'][r['labels']['error_steps'][0]]['agent']
            m[('first', a == r['labels']['error_agent'])] += 1
            m[('any', a in {x['agent_name'] for x in r['labels']['extra']['faulty_agents']})] += 1
    print(sorted(m.items()))
