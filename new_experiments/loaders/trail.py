"""TRAIL (PatronusAI/TRAIL, GitHub mirror): data/trail/trail_github/benchmarking/data/{GAIA,SWE Bench}/<trace_id>.json
(OpenInference span trees) + processed_annotations_{gaia,swe_bench}/<trace_id>.json ({errors:[{category, location
(span_id), evidence, description, impact}], scores}). Steps = spans in DFS (pre-order) order, one span per step:
LLM spans render the last input message + output; TOOL spans input + output; CHAIN/AGENT/other spans name + input/output
(or the logged function call). native_step = span_id. labels.error_steps = every span carrying >=1 error (sorted by
make_record); labels.extra['primary_idx'] = earliest HIGH-impact error span (earliest error span if none is HIGH);
extra['errors'] = full error list with idx/span_id/category/impact/evidence/description. outcome None (traces were not
selected by outcome). task / ground_truth from the answer_single_question log (GAIA) when present."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA

BENCH = os.path.join(DATA, 'trail', 'trail_github', 'benchmarking')
SPLITS = [('gaia', 'data/GAIA', 'processed_annotations_gaia'), ('swe_bench', 'data/SWE Bench', 'processed_annotations_swe_bench')]
IMPACT_RANK = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}


def lj(path):
    with open(path, encoding='utf-8') as fh:
        s = fh.read()
    try:
        return json.loads(s), False
    except json.JSONDecodeError:
        return json.loads(re.sub(r',(\s*[}\]])', r'\1', s)), True


def flatten(span, depth, agent, out):
    at = span.get('span_attributes', {}) or {}
    if at.get('openinference.span.kind') == 'AGENT':
        agent = span['span_name'].replace('.run', '')
    out.append({'depth': depth, 'agent': agent, 'span': span})
    for c in span.get('child_spans', []) or []:
        flatten(c, depth + 1, agent, out)


def span_content(span):
    at = span.get('span_attributes', {}) or {}
    kind = at.get('openinference.span.kind')
    parts = []
    if kind == 'LLM':
        idx = sorted({int(m.group(1)) for k in at for m in [re.match(r'llm\.input_messages\.(\d+)\.message\.content', k)] if m})
        if idx:
            i = idx[-1]
            parts.append(f"Input (last of {len(idx)} msgs, role={at.get(f'llm.input_messages.{i}.message.role')}): {at.get(f'llm.input_messages.{i}.message.content')}")
        out = at.get('llm.output_messages.0.message.content') or at.get('output.value')
        calls = {k: v for k, v in at.items() if re.match(r'llm\.output_messages\.0\.message\.tool_calls\.', k)}
        parts.append(f"Output ({at.get('llm.model_name')}): {out}")
        if calls:
            parts.append('Tool calls: ' + json.dumps(calls, ensure_ascii=False, default=str))
    elif kind == 'TOOL':
        parts.append(f"Tool: {at.get('tool.name')} | Input: {at.get('input.value')}")
        if at.get('output.value') is not None:
            parts.append(f"Observation: {at.get('output.value')}")
    else:
        parts.append(f"[{kind or 'INTERNAL'}] {span.get('span_name')}")
        if at.get('input.value') is not None:
            parts.append(f"Input: {at.get('input.value')}")
        if at.get('output.value') is not None:
            parts.append(f"Output: {at.get('output.value')}")
        if len(parts) == 1:
            logs = span.get('logs') or []
            if logs:
                body = logs[0].get('body', {}) or {}
                parts.append('Function call: ' + json.dumps({k: body.get(k) for k in ('function.name', 'function.arguments')}, default=str, ensure_ascii=False))
    return '\n'.join(str(p) for p in parts)


def load(limit=None, splits=('gaia', 'swe_bench')):
    recs = []
    for split, sub, ann in SPLITS:
        if split not in splits:
            continue
        for fn in sorted(os.listdir(os.path.join(BENCH, sub))):
            tf = os.path.join(BENCH, sub, fn)
            t, f1 = lj(tf)
            a, f2 = lj(os.path.join(BENCH, ann, fn))
            fl = []
            for root in t['spans']:
                flatten(root, 0, None, fl)
            ids = [x['span']['span_id'] for x in fl]
            steps = []
            task = gt = final = None
            for i, x in enumerate(fl):
                sp = x['span']
                at = sp.get('span_attributes') or {}
                kind = at.get('openinference.span.kind')
                role = 'agent' if kind == 'LLM' else ('tool' if kind == 'TOOL' else 'env')
                steps.append(make_step(i, x['agent'] or 'framework', role, span_content(sp), native_step=sp['span_id'],
                                       meta={'span_name': sp.get('span_name'), 'kind': kind or 'INTERNAL', 'depth': x['depth'],
                                             'parent_span_id': sp.get('parent_span_id'), 'model': at.get('llm.model_name'),
                                             'status_code': sp.get('status_code')}))
                for lg in sp.get('logs') or []:
                    args = (lg.get('body') or {}).get('function.arguments') or {}
                    exm = args.get('example') if isinstance(args, dict) else None
                    if isinstance(exm, dict) and exm.get('question') and task is None:
                        task = exm.get('question')
                        gt = exm.get('true_answer') or exm.get('Final answer') or exm.get('answer')
                if sp.get('span_name') == 'FinalAnswerTool':
                    final = at.get('input.value')
            errs = []
            for e in a.get('errors', []):
                loc = e.get('location')
                idx = ids.index(loc) if loc in ids else None
                errs.append({'idx': idx, 'span_id': loc, 'category': e.get('category'), 'impact': (e.get('impact') or '').upper(),
                             'evidence': e.get('evidence'), 'description': e.get('description'),
                             'agent': fl[idx]['agent'] if idx is not None else None,
                             'kind': (fl[idx]['span'].get('span_attributes') or {}).get('openinference.span.kind') if idx is not None else None})
            located = [e for e in errs if e['idx'] is not None]
            primary = min(located, key=lambda e: (IMPACT_RANK.get(e['impact'], 3) if e['impact'] == 'HIGH' else 1, e['idx']))['idx'] if located else None
            if task is None:
                # fall back: first input.value of the root span tree
                for x in fl:
                    v = (x['span'].get('span_attributes') or {}).get('input.value')
                    if v:
                        task = str(v)
                        break
            recs.append(make_record('trail', f"{split}/{t.get('trace_id') or fn[:-5]}", task, steps, subset=split, ground_truth=gt,
                                    final_output=final, outcome=None, error_steps=sorted({e['idx'] for e in located}),
                                    error_agent=next((e['agent'] for e in located if e['idx'] == primary), None) if primary is not None else None,
                                    categories=sorted({e['category'] for e in errs if e['category']}),
                                    reason='; '.join(f"[{e['impact']} {e['category']} @{e['idx']}] {e['description']}" for e in errs) or None,
                                    extra={'errors': errs, 'primary_idx': primary, 'n_errors': len(errs), 'n_unlocated': len(errs) - len(located),
                                           'scores': a.get('scores'), 'impact_counts': {k: sum(1 for e in errs if e['impact'] == k) for k in ('HIGH', 'MEDIUM', 'LOW')}},
                                    meta={'file': tf, 'annotation_file': os.path.join(BENCH, ann, fn), 'framework': 'smolagents (CodeAgent / ToolCallingAgent)',
                                          'benchmark': 'GAIA' if split == 'gaia' else 'SWE-bench Lite', 'json_fixed': f1 or f2,
                                          'span_kinds': {k: sum(1 for s in steps if s['meta']['kind'] == k) for k in {s['meta']['kind'] for s in steps}}}))
            if limit and len(recs) >= limit:
                return recs
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps;',
          sum(r['labels']['extra']['n_errors'] for r in rs), 'errors;', sum(r['labels']['extra']['n_unlocated'] for r in rs), 'unlocated')
    print(Counter(r['subset'] for r in rs), sum(1 for r in rs if r['task']), 'with task', sum(1 for r in rs if r['ground_truth']), 'with gt')
    print(Counter(e['impact'] for r in rs for e in r['labels']['extra']['errors']))
