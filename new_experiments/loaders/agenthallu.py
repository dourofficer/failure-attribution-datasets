"""AgentHallu (arXiv 2601.06818): data/agenthallu/repo/AgentHallu/<framework>/NNN.json (693 runs; 443 hallucinated).
history = [{step, role, content, tool_calls?, tool_responses?}]; hallucination_step is a 1-based string that matches
history[i].step -> idx found by matching the step field. Content = content + rendered tool_calls + tool_responses.
outcome 'success' when is_hallucination == 'false' (error_steps []), else 'fail'; error_agent = role of the labelled step;
categories = [hallucination_category, hallucination_subcategory]."""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

ROOT = os.path.join(DATA, 'agenthallu', 'repo', 'AgentHallu')
ROLE = {'assistant': 'agent', 'user': 'user', 'system': 'system', 'tool': 'tool'}


def render(s):
    parts = []
    if s.get('content'):
        parts.append(str(s['content']))
    if s.get('tool_calls'):
        parts.append('Tool calls: ' + json.dumps(s['tool_calls'], ensure_ascii=False))
    if s.get('tool_responses'):
        parts.append('Tool responses: ' + json.dumps(s['tool_responses'], ensure_ascii=False))
    return '\n'.join(parts)


def load(limit=None, frameworks=None):
    recs = []
    for f in sorted(glob.glob(os.path.join(ROOT, '*', '*.json'))):
        fw = f.split(os.sep)[-2]
        if frameworks and fw not in frameworks:
            continue
        d = read_json(f)
        h = d.get('history', [])
        steps = []
        for i, s in enumerate(h):
            role = s.get('role', 'assistant')
            steps.append(make_step(i, role, ROLE.get(role, 'agent'), render(s), native_step=s.get('step'),
                                   meta={'n_tool_calls': len(s.get('tool_calls') or []), 'n_tool_responses': len(s.get('tool_responses') or [])}))
        hall = str(d.get('is_hallucination')).lower() == 'true'
        err = []
        if hall:
            try:
                hs = int(str(d.get('hallucination_step')).strip())
                idx = next((i for i, s in enumerate(h) if s.get('step') == hs), None)
                if idx is None and 1 <= hs <= len(h):
                    idx = hs - 1
                if idx is not None:
                    err = [idx]
            except ValueError:
                pass
        cats = [c for c in (d.get('hallucination_category'), d.get('hallucination_subcategory')) if hall and c and c != 'None']
        recs.append(make_record('agenthallu', f'{fw}/{os.path.basename(f)}', d.get('question'), steps, subset=fw,
                                ground_truth=d.get('true_answer'), final_output=d.get('agent_answer'),
                                outcome='fail' if hall else 'success', error_steps=err,
                                error_agent=steps[err[0]]['agent'] if err else None, categories=cats,
                                reason=d.get('hallucination_reason') if hall else None,
                                extra={'is_hallucination': d.get('is_hallucination'), 'hallucination_step_raw': d.get('hallucination_step'),
                                       'explanation': d.get('explanation')},
                                meta={'file': f, 'framework': fw, 'agent_type': d.get('agent_type'), 'backbone': d.get('model_id'),
                                      'benchmark': d.get('question_source'), 'domain': d.get('question_domain')}))
        if limit and len(recs) >= limit:
            break
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', Counter(r['outcome'] for r in rs),
          sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    print(Counter(r['subset'] for r in rs))
    print(Counter(r['labels']['error_agent'] for r in rs if r['labels']['error_steps']))
    print([r['id'] for r in rs if r['outcome'] == 'fail' and not r['labels']['error_steps']])
