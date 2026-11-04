"""MAST-Data / MAD (mcemri/MAST-Data): data/mast_data/MAST-Data/MAD_full_dataset.json (1,642 traces, LLM-judge labels).
Each trace is one raw log string (trace.trajectory); steps are produced by the framework-specific heuristic splitters
from scripts/analyze_mast.py (AG2 message dicts, MetaGPT NEW MESSAGES blocks, ChatDev INFO lines, Magentic-One
'---------- Agent ----------' delimiters, OpenManus 'Executing step', AppWorld 'Response from X Agent', HyperAgent log
lines). If a splitter fails or yields nothing the record has ONE step holding the whole log and meta['parsed']=False.
labels.categories = failure modes with value 1 (e.g. '1.3'); error_steps = []; outcome None (no outcome in the data)."""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # for python3 -I
from common.schema import make_record, make_step
from common.util import DATA, read_json

FILE = os.path.join(DATA, 'mast_data', 'MAST-Data', 'MAD_full_dataset.json')
MODES = {'1.1': 'Disobey task specification', '1.2': 'Disobey role specification', '1.3': 'Step repetition',
         '1.4': 'Loss of conversation history', '1.5': 'Unaware of termination conditions',
         '2.1': 'Conversation reset', '2.2': 'Fail to ask for clarification', '2.3': 'Task derailment',
         '2.4': 'Information withholding', '2.5': "Ignored other agent's input", '2.6': 'Reasoning-action mismatch',
         '3.1': 'Premature termination', '3.2': 'No or incomplete verification', '3.3': 'Incorrect verification'}


def split_ag2(t):
    msgs = ast.literal_eval('[' + re.sub(r"\}\s+\{'content'", "}, {'content'", t) + ']')
    out = []
    for m in msgs:
        c = m.get('content')
        if isinstance(c, list):
            c = '\n'.join(str(x) for x in c)
        out.append((m.get('name') or m.get('role'), str(c)))
    return out


def split_metagpt(t):
    out = []
    first = re.search(r'FROM: (\w+) TO: .*?\nACTION: .*?\nCONTENT:\n(.*?)\n-{20,}', t, re.S)
    if first:
        out.append((first.group(1), first.group(2)))
    for blk in re.split(r'\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\] NEW MESSAGES:\n', t)[1:]:
        blk = blk.strip()
        m = re.match(r'([A-Za-z_]+): ?(.*)', blk, re.S)
        if m:
            body = re.split(r'\n-{20,}', m.group(2))[0]
            out.append((m.group(1), body.strip()))
    return out


def split_chatdev(t):
    pat = re.compile(r'^\[[^\]]+ INFO\] (?!System|HTTP|flask|\*\*)([^:\n]{2,40}): (.*?)(?=^\[[^\]]+ INFO\]|\Z)', re.M | re.S)
    return [(m.group(1).strip(), m.group(2).strip()) for m in pat.finditer(t)]


def split_magentic(t):
    parts = re.split(r'^---------- (\S+) ----------$', t, flags=re.M)
    return [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]


def split_openmanus(t):
    out = []
    for m in re.finditer(r'Executing step (\d+)/\d+\n(.*?)(?=Executing step \d+/\d+\n|\Z)', t, re.S):
        who = re.search(r"✨ (\w+)'s thoughts", m.group(2))
        out.append((who.group(1) if who else 'Manus', m.group(2).strip()))
    return out


def split_appworld(t):
    pat = re.compile(r'^\s*Response from (\S+) Agent\n(.*?)(?=^\s*(?:Response from|Message to|Code Execution Output|Entering)|\Z)', re.M | re.S)
    return [(m.group(1), m.group(2).strip()) for m in pat.finditer(t)]


def split_hyperagent(t):
    pat = re.compile(r"HyperAgent_\S+ - INFO - ((?:Planner|Navigator|Executor|Editor|Inner-\w+-Assistant)(?:'s Response|->\w+)?):?(.*?)(?=HyperAgent_\S+ - INFO - |\Z)", re.S)
    out = []
    for m in pat.finditer(t):
        who = m.group(1).split("'")[0].split('->')[0]
        out.append((who, m.group(2).strip()))
    return out


SPLIT = {'AG2': split_ag2, 'MetaGPT': split_metagpt, 'ChatDev': split_chatdev, 'Magentic': split_magentic,
         'OpenManus': split_openmanus, 'AppWorld': split_appworld, 'HyperAgent': split_hyperagent}


def _ann(a):
    if isinstance(a, str):
        try:
            a = ast.literal_eval(a)
        except Exception:  # noqa
            return {}
    return a or {}


def load(limit=None, frameworks=None):
    recs = []
    for r in read_json(FILE):
        mas = r['mas_name']
        if frameworks and mas not in frameworks:
            continue
        t = r['trace']['trajectory'] or ''
        try:
            msgs = SPLIT[mas](t)
        except Exception:  # noqa
            msgs = []
        parsed = bool(msgs)
        if parsed:
            steps = []
            for i, (who, c) in enumerate(msgs):
                a = str(who or 'unknown')
                role = 'user' if a.lower() in ('user', 'human', 'user_proxy') else 'agent'
                steps.append(make_step(i, a, role, c, native_step=i))
        else:
            steps = [make_step(0, mas, 'agent', t, native_step=0)]
        ann = _ann(r.get('mast_annotation'))
        flagged = sorted(k for k, v in ann.items() if v == 1)
        recs.append(make_record('mast_data', f"{r['trace']['key']}/{r['trace_id']}", steps[0]['content'] if steps else '', steps,
                                subset=mas, ground_truth=None, final_output=None, outcome=None, error_steps=[], error_agent=None,
                                categories=flagged, reason=None,
                                extra={'mast_annotation': ann, 'all_null': all(v is None for v in ann.values()) if ann else True,
                                       'mode_names': [MODES.get(k, k) for k in flagged]},
                                meta={'file': FILE, 'framework': mas, 'backbone': r.get('llm_name'), 'benchmark': r.get('benchmark_name'),
                                      'trace_key': r['trace']['key'], 'trace_index': r['trace'].get('index'), 'parsed': parsed,
                                      'raw_chars': len(t), 'task_is_first_step': True}))
        if limit and len(recs) >= limit:
            break
    return recs


if __name__ == '__main__':
    rs = load()
    from collections import Counter
    print(len(rs), 'records;', sum(len(r['steps']) for r in rs), 'steps;', sum(1 for r in rs if not r['meta']['parsed']), 'unparsed;',
          sum(1 for r in rs if r['labels']['categories']), 'with >=1 mode')
    print(Counter((r['subset'], r['meta']['parsed']) for r in rs))
