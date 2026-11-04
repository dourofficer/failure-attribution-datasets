"""TRAIL (PatronusAI/TRAIL, arXiv:2505.08638) loader -- GitHub copy of the benchmark data.

Files: data/trail/trail_github/benchmarking/data/GAIA/<trace_id>.json (117) and data/SWE Bench/<trace_id>.json
(31) plus the matching processed_annotations_{gaia,swe_bench}/<trace_id>.json.  One annotation file needs a
trailing-comma fix before it parses (done here as in scripts/analyze_trail.py).

LICENCE / USE RESTRICTION: the GitHub copy is MIT, but the Hugging Face dataset card adds "evaluation only --
do not train automatic evaluators on it" and a no-resharing pledge.  Treat TRAIL as an evaluation-only set.

Step unit / index mapping
-------------------------
One OpenTelemetry span = one step.  The span tree is flattened in DFS (document) order over all roots
(``trace['spans']`` holds one root except one SWE-bench trace with seven), which is chronological order.
``native_idx = span_id``.  Errors are addressed by ``location`` = span id; ``faulty_steps`` = the sorted DFS
positions of every error's location span (one SWE-bench trace has a duplicated span id -> first occurrence;
two SWE-bench error locations match no span and are kept in ``extra.errors`` with ``idx = None``).
``faulty_step`` = the earliest DFS position among errors with impact HIGH (None if the trace has no HIGH
error); ``category``/``reason`` are taken from that error (canonicalised category; raw spelling in extra).
``faulty_agent`` = the agent of that step.

Role by ``openinference.span.kind``: LLM -> agent, TOOL -> tool, AGENT / CHAIN / framework functions
(no kind) -> system.  ``agent`` = name of the enclosing AGENT span (``CodeAgent`` or ``ToolCallingAgent``);
for LLM/TOOL spans outside any AGENT span it is the issuing framework function (GAIA's final
answer-reformulation LLM call under ``answer_single_question``; 117 spans, 8 of them error locations) or
``CodeAgent`` for the one SWE-bench trace whose ``Step N`` spans are roots; other framework spans carry
their own span name.  Content: LLM spans show the last input message (with its
role and the message count) and the output message (content, or the tool call when the output is a tool
call); TOOL spans show the tool name, input and output values; other spans their input/output values or the
logged function call.  Nothing is truncated.
``task``/``ground_truth``: GAIA from the ``answer_single_question`` log (``question`` / ``true_answer``);
SWE-bench from the agent's task string and the gold ``patch`` of the ``process_item`` log.  ``final_output`` =
the last FinalAnswerTool argument (else the top agent's output).  ``outcome`` = 1 when the GAIA final answer
equals ``true_answer`` after GAIA-style normalisation, otherwise None (not labelled; many traces end with the
right answer despite the errors).  subset = 'gaia' | 'swebench'.
"""
import json
import os
import re

SLUG = 'trail'
ROOT = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/trail/trail_github/benchmarking'
SPLITS = [('gaia', os.path.join(ROOT, 'data', 'GAIA'), os.path.join(ROOT, 'processed_annotations_gaia'),
           'smolagents OpenDeepResearch (CodeAgent manager + ToolCallingAgent search_agent)'),
          ('swebench', os.path.join(ROOT, 'data', 'SWE Bench'), os.path.join(ROOT, 'processed_annotations_swe_bench'),
           'smolagents CodeAgent (single agent, gitingest + python)')]
CANON = ["Language-only", "Tool-related", "Poor Information Retrieval", "Incorrect Memory Usage",
         "Tool Output Misinterpretation", "Incorrect Problem Identification", "Tool Selection Errors",
         "Formatting Errors", "Instruction Non-compliance", "Tool Definition Issues",
         "Environment Setup Errors", "Rate Limiting", "Authentication Errors", "Service Errors",
         "Resource Not Found", "Resource Exhaustion", "Timeout Issues", "Context Handling Failures",
         "Resource Abuse", "Goal Deviation", "Task Orchestration"]
ROLE_BY_KIND = {'LLM': 'agent', 'TOOL': 'tool', 'AGENT': 'system', 'CHAIN': 'system'}


def canon(cat):
    c = (cat or "").lower().strip().replace("-", " ")
    c = re.sub(r"\s+", " ", c)
    c = re.sub(r"\s*errors?$", "", c) if c not in ("formatting errors", "tool selection errors", "service errors", "environment setup errors", "authentication errors") else c
    for s in CANON:
        sl = s.lower().replace("-", " ")
        if c == sl or c == re.sub(r"\s*errors?$", "", sl) or c.replace(" ", "") == sl.replace(" ", ""):
            return s
    for s in CANON:
        sl = s.lower().replace("-", " ")
        if c.replace(" ", "") in sl.replace(" ", "") or sl.replace(" ", "") in c.replace(" ", ""):
            return s
    if "complien" in c or "compli" in c:
        return "Instruction Non-compliance"
    return cat


def _lj(path):
    with open(path, encoding='utf-8') as f:
        s = f.read()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return json.loads(re.sub(r",(\s*[}\]])", r"\1", s))


def _s(v):
    if v is None:
        return ''
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def _flatten(span, depth, agent, out):
    at = span.get('span_attributes') or {}
    if at.get('openinference.span.kind') == 'AGENT':
        agent = span['span_name'].replace('.run', '')
    out.append((depth, agent, span))
    for c in span.get('child_spans') or []:
        _flatten(c, depth + 1, agent, out)


def _msg_indices(at, direction):
    return sorted({int(m.group(1)) for k in at for m in [re.match(rf'llm\.{direction}_messages\.(\d+)\.message\.', k)] if m})


def span_content(span):
    at = span.get('span_attributes') or {}
    kind = at.get('openinference.span.kind')
    name = span.get('span_name')
    parts = []
    if kind == 'LLM':
        idx = _msg_indices(at, 'input')
        if idx:
            i = idx[-1]
            parts.append(f"[LLM {at.get('llm.model_name') or ''}] last input message (role={at.get(f'llm.input_messages.{i}.message.role')}, {len(idx)} messages):\n"
                         + _s(at.get(f'llm.input_messages.{i}.message.content')))
        else:
            parts.append(f"[LLM {at.get('llm.model_name') or ''}] input:\n" + _s(at.get('input.value')))
        out = at.get('llm.output_messages.0.message.content')
        if out is None:
            calls = []
            j = 0
            while f'llm.output_messages.0.message.tool_calls.{j}.tool_call.function.name' in at:
                calls.append(f"{at.get(f'llm.output_messages.0.message.tool_calls.{j}.tool_call.function.name')}({_s(at.get(f'llm.output_messages.0.message.tool_calls.{j}.tool_call.function.arguments'))})")
                j += 1
            out = '\n'.join('[tool_call] ' + c for c in calls) if calls else _s(at.get('output.value'))
        parts.append('--- output:\n' + _s(out))
    elif kind == 'TOOL':
        parts.append(f"[TOOL {at.get('tool.name') or name}] input: " + _s(at.get('input.value')))
        if at.get('output.value') is not None:
            parts.append('--- output:\n' + _s(at.get('output.value')))
    else:
        parts.append(f"[{kind or 'FUNCTION'} {name}]")
        if at.get('input.value') is not None:
            parts.append('input: ' + _s(at.get('input.value')))
        if at.get('output.value') is not None:
            parts.append('--- output:\n' + _s(at.get('output.value')))
        if at.get('input.value') is None and at.get('output.value') is None:
            logs = span.get('logs') or []
            if logs:
                body = logs[0].get('body') or {}
                parts.append('function call: ' + _s({k: body.get(k) for k in ('function.name', 'function.arguments', 'function.output')}))
            else:
                parts.append('(no content)')
    return '\n'.join(parts)


def _norm_answer(s):
    s = _s(s).strip().lower()
    s = re.sub(r'[\s,]+', '', s)
    s = re.sub(r'[.!?;:"\']+$', '', s)
    return s


def _derive_outcome(final, gt):
    if final is None or gt is None:
        return None
    a, b = _norm_answer(final), _norm_answer(gt)
    if not a or not b:
        return None
    if a == b:
        return 1
    try:
        if abs(float(a.replace('$', '').replace('%', '')) - float(b.replace('$', '').replace('%', ''))) < 1e-9:
            return 1
    except ValueError:
        pass
    return None


def load(limit=None, subset=None):
    n = 0
    for split, tdir, adir, system in SPLITS:
        if subset is not None and subset != split:
            continue
        for fn in sorted(os.listdir(tdir)):
            if not fn.endswith('.json'):
                continue
            t = _lj(os.path.join(tdir, fn))
            apath = os.path.join(adir, fn)
            a = _lj(apath) if os.path.exists(apath) else {}
            fl = []
            for root in t.get('spans') or []:
                _flatten(root, 0, None, fl)
            pos = {}
            parent_name = {}
            has_agent_span = False
            for i, (_, _, sp) in enumerate(fl):
                pos.setdefault(sp['span_id'], i)
                parent_name.setdefault(sp['span_id'], sp.get('span_name'))
                if (sp.get('span_attributes') or {}).get('openinference.span.kind') == 'AGENT':
                    has_agent_span = True
            steps = []
            task = gt = final = None
            top_agent_out = None
            model = None
            for i, (depth, agent, sp) in enumerate(fl):
                at = sp.get('span_attributes') or {}
                kind = at.get('openinference.span.kind')
                name = sp.get('span_name')
                meta = {'span_name': name, 'kind': kind, 'depth': depth, 'parent_span_id': sp.get('parent_span_id'),
                        'status_code': sp.get('status_code'), 'duration': sp.get('duration')}
                if kind == 'LLM':
                    meta['model'] = at.get('llm.model_name')
                    model = model or at.get('llm.model_name')
                    for k in ('prompt', 'completion', 'total'):
                        if at.get(f'llm.token_count.{k}') is not None:
                            meta[f'tokens_{k}'] = at.get(f'llm.token_count.{k}')
                    meta['n_input_messages'] = len(_msg_indices(at, 'input'))
                if kind == 'TOOL':
                    meta['tool_name'] = at.get('tool.name')
                    if name == 'FinalAnswerTool':
                        try:
                            args = json.loads(at.get('input.value') or '{}')
                            final = _s(args.get('args', [None])[0]) if isinstance(args, dict) and args.get('args') else _s(at.get('input.value'))
                        except (json.JSONDecodeError, TypeError, IndexError):
                            final = _s(at.get('input.value'))
                if kind == 'AGENT':
                    if top_agent_out is None and at.get('output.value') is not None:
                        top_agent_out = _s(at.get('output.value'))
                    if task is None and at.get('input.value'):
                        try:
                            j = json.loads(at['input.value'])
                            if isinstance(j, dict) and j.get('task'):
                                task = _s(j['task'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                for lg in sp.get('logs') or []:
                    body = lg.get('body') or {}
                    args = body.get('function.arguments')
                    if isinstance(args, dict):
                        ex = args.get('example')
                        if isinstance(ex, dict) and ex.get('question'):
                            task = _s(ex.get('question'))
                            gt = _s(ex.get('true_answer')) if ex.get('true_answer') is not None else gt
                        item = args.get('item')
                        if isinstance(item, dict):
                            if item.get('patch') is not None:
                                gt = _s(item.get('patch'))
                            if task is None and item.get('problem_statement'):
                                task = _s(item.get('problem_statement'))
                if agent:
                    ag = agent
                elif kind in ('LLM', 'TOOL'):
                    # LLM/TOOL span outside any AGENT span: the framework function that issued it
                    # (GAIA: the final answer-reformulation call under answer_single_question);
                    # the one SWE-bench trace whose Step spans are roots has no AGENT span at all -> CodeAgent
                    ag = 'CodeAgent' if (split == 'swebench' and not has_agent_span) else (parent_name.get(sp.get('parent_span_id')) or name)
                else:
                    ag = name
                steps.append({'idx': i, 'native_idx': sp['span_id'], 'agent': ag,
                              'role': ROLE_BY_KIND.get(kind, 'system'), 'content': span_content(sp), 'meta': meta})
            errors = []
            for e in a.get('errors') or []:
                loc = e.get('location')
                idx = pos.get(loc)
                errors.append({'idx': idx, 'span_id': loc, 'category': canon(e.get('category')), 'category_raw': e.get('category'),
                               'impact': (e.get('impact') or '').upper(), 'evidence': e.get('evidence'), 'description': e.get('description'),
                               'agent': steps[idx]['agent'] if idx is not None else None,
                               'span_kind': steps[idx]['meta']['kind'] if idx is not None else None})
            faulty_steps = sorted({e['idx'] for e in errors if e['idx'] is not None})
            high = sorted([e for e in errors if e['impact'] == 'HIGH' and e['idx'] is not None], key=lambda e: e['idx'])
            primary = high[0] if high else None
            if final is None:
                final = top_agent_out
            yield {
                'dataset': SLUG,
                'id': t.get('trace_id') or fn[:-5],
                'subset': split,
                'system': system,
                'task': task or '',
                'ground_truth': gt,
                'final_output': final,
                'outcome': _derive_outcome(final, gt) if split == 'gaia' else None,
                'steps': steps,
                'annotation': {
                    'faulty_step': primary['idx'] if primary else None,
                    'faulty_steps': faulty_steps,
                    'faulty_agent': primary['agent'] if primary else None,
                    'category': primary['category'] if primary else None,
                    'reason': primary['description'] if primary else None,
                    'extra': {'errors': errors, 'scores': (a.get('scores') or [None])[0], 'n_errors': len(errors),
                              'n_high': len(high), 'unresolved_locations': [e['span_id'] for e in errors if e['idx'] is None],
                              'all_categories': sorted({e['category'] for e in errors if e['category']}),
                              'label_note': 'faulty_step = earliest HIGH-impact error span; faulty_steps = every error span (DFS order)'},
                },
                'meta': {'file': os.path.join(tdir, fn), 'annotation_file': apath, 'model': model, 'n_spans': len(fl),
                         'n_roots': len(t.get('spans') or []), 'benchmark': 'GAIA validation' if split == 'gaia' else 'SWE-bench Lite',
                         'license': 'MIT (GitHub); HF card: evaluation only, do not train automatic evaluators on it, no resharing'},
            }
            n += 1
            if limit is not None and n >= limit:
                return
