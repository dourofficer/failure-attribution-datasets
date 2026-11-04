"""TraceElephant (HF TraceElephant/TraceElephant, data.zip extracted under data/traceelephant/extracted/data/).
One record per run directory (trace_metadata.json + step_records.json). A step is one LLM call (step_id, 1-based).
Step content = the call's OUTPUT (assistant text + tool_calls) + tool_logs when they differ from the tool_calls +
the NEW tool-result messages that appear at the end of the next call's input (inputs repeat the whole history, so
they are not included; the last input message is kept in step meta['last_input']).
Native convention: mistake_step is a 1-based step_id string ('none' and 'Step 36' quirks) -> idx = step - 1."""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

ROOT = os.path.join(DATA, 'traceelephant', 'extracted', 'data')
SYSTEM_OF_DIR = {'magentic-runs-gaia': ('magentic-one', 'GAIA'),
                 'magentic-runs-assistant-bench': ('magentic-one', 'AssistantBench'),
                 'captain-runs-gaia': ('captain-agent', 'GAIA'),
                 'captain-runs-assistantbench': ('captain-agent', 'AssistantBench'),
                 'swe-agent-runs-swe-bench': ('swe-agent', 'SWE-Bench Verified')}


def msg_text(content):
    if content is None:
        return ''
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict):
                if p.get('type') == 'text':
                    parts.append(p.get('text', ''))
                elif p.get('type') == 'image_url':
                    parts.append('[image]')
                else:
                    parts.append(json.dumps(p, ensure_ascii=False))
            else:
                parts.append(str(p))
        return '\n'.join(parts)
    return json.dumps(content, ensure_ascii=False)


def step_output(st):
    try:
        msg = st['output']['choices'][0]['message']
    except Exception:  # noqa
        return '', []
    return msg_text(msg.get('content')), (msg.get('tool_calls') or [])


def _norm_calls(calls):
    return json.dumps([{k: v for k, v in c.items() if k != 'index'} for c in calls], sort_keys=True)


def parse_step(v):
    s = str(v).strip()
    digits = ''.join(ch for ch in s if ch.isdigit())
    return int(digits) if digits else None


def new_observations(st, nxt, text):
    """Trailing messages of the next call's input that were not in this call's input and are tool results
    (role 'tool', or a message under this step's own agent name in Magentic-One, where tool results are posted
    as messages of the calling agent)."""
    if nxt is None:
        return []
    seen = {(m.get('role'), msg_text(m.get('content'))) for m in st['input']['messages']}
    seen.add(('assistant', text))
    out = []
    for m in reversed(nxt['input']['messages']):
        key = (m.get('role'), msg_text(m.get('content')))
        if key in seen:
            break
        out.append(m)
    out.reverse()
    return [m for m in out if m.get('role') == 'tool' or m.get('role') == st['agent_name']]


def render_step(st, nxt):
    text, calls = step_output(st)
    content = text
    if calls:
        content += ('\n' if content else '') + 'Action: ' + json.dumps(calls, ensure_ascii=False)
    tl = st.get('tool_logs')
    if isinstance(tl, list) and tl and (not calls or _norm_calls(tl) != _norm_calls(calls)):
        content += '\nTool logs: ' + json.dumps(tl, ensure_ascii=False)
    obs = new_observations(st, nxt, text)
    if obs:
        content += '\nObservation: ' + '\n'.join(msg_text(m.get('content')) for m in obs)
    return content, len(obs)


def load(limit=None, systems=None):
    recs = []
    for d in sorted(glob.glob(os.path.join(ROOT, '*', '*'))):
        if not os.path.isdir(d):
            continue
        split = os.path.basename(os.path.dirname(d))
        sysn, bench = SYSTEM_OF_DIR[split]
        if systems and sysn not in systems:
            continue
        meta = read_json(os.path.join(d, 'trace_metadata.json'))
        S = read_json(os.path.join(d, 'step_records.json'))
        steps = []
        for i, st in enumerate(S):
            nxt = S[i + 1] if i + 1 < len(S) else None
            content, n_obs = render_step(st, nxt)
            ins = st['input']['messages']
            last = ins[-1] if ins else None
            usage = (st.get('output') or {}).get('usage') or {}
            steps.append(make_step(i, st['agent_name'], 'agent', content, native_step=int(st['step_id']),
                                   meta={'agent_id': st.get('agent_id'), 'n_input_messages': len(ins),
                                         'prompt_tokens': usage.get('prompt_tokens'), 'n_observations': n_obs,
                                         'last_input': {'role': last.get('role'), 'content': msg_text(last.get('content'))} if last else None}))
        ms = parse_step(meta.get('mistake_step'))
        err = [ms - 1] if ms is not None and 1 <= ms <= len(steps) else []
        final = None
        for s in reversed(steps):
            if 'FINAL ANSWER' in s['content'] or 'final answer' in s['content'].lower():
                final = s['content']
                break
        gt = meta.get('ground_truth')
        if gt is None and meta.get('tests_status') is not None:
            gt = json.dumps(meta['tests_status'], ensure_ascii=False)
        rel = os.path.relpath(d, ROOT)
        recs.append(make_record('traceelephant', rel, meta.get('task_instruction'), steps, subset=sysn,
                                ground_truth=gt, final_output=final, outcome='fail', error_steps=err,
                                error_agent=meta.get('mistake_agent'), categories=[], reason=meta.get('mistake_reason'),
                                extra={'mistake_step_raw': meta.get('mistake_step'), 'tests_status': meta.get('tests_status')},
                                meta={'file': os.path.join(d, 'step_records.json'), 'framework': sysn, 'benchmark': bench,
                                      'split': split, 'task_id': meta.get('task_id'), 'run_id': meta.get('run_id'),
                                      'backbone': (S[0].get('output') or {}).get('model') if S else None,
                                      'agent_configuration': meta.get('agent_configuration'),
                                      'n_images': len(glob.glob(os.path.join(d, 'images', '*.png')))}))
        if limit and len(recs) >= limit:
            return recs
    return recs


if __name__ == '__main__':
    rs = load()
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;',
          sum(1 for r in rs if r['labels']['error_steps']), 'with error_steps')
    from collections import Counter
    print(Counter(r['subset'] for r in rs))
    m = [r['steps'][r['labels']['error_steps'][0]]['agent'] == r['labels']['error_agent'] for r in rs if r['labels']['error_steps']]
    print('agent match', sum(m), '/', len(m))
    r = rs[0]
    print(r['id'], r['labels'], [(s['idx'], s['agent'], len(s['content'])) for s in r['steps']][:8])
