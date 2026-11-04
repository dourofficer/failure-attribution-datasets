"""MAST-Data / MAD (mcemri/MAST-Data, arXiv:2503.13657) loader.

Files: data/mast_data/MAST-Data/MAD_full_dataset.json (1,642 traces, labelled by the o1 judge) followed by
MAD_human_labelled_dataset.json (19 traces, three human annotators).  Each trace is ONE raw log string in a
framework-specific layout.  Trace-level failure-mode flags only: no faulty step, no faulty agent, no outcome
(``outcome = None``).

Step unit / index mapping
-------------------------
Steps are obtained by the framework-specific heuristic splitters copied from ``scripts/analyze_mast.py``
(AG2 printed message dicts via ``ast.literal_eval``; MetaGPT ``NEW MESSAGES`` blocks; ChatDev ``[.. INFO] Role:``
blocks; Magentic ``---------- source ----------`` transcript; OpenManus ``Executing step k/n``; AppWorld
``Response from X Agent``; HyperAgent logger lines).  ``native_idx = i`` = position of the parsed message.
32 traces of the full file do not parse (30 AG2 GSM/GPT-4o traces stored as a YAML-like dump instead of a
printed list; 2 traces labelled ``HyperAgent`` that are in fact ChatDev logs); they are yielded as ONE step
holding the raw log, role ``system``, with ``meta.parse_failed = True``.
The human file stores some traces inside a JSON wrapper: AG2 as ``{"trajectory": [{content, name, role}]}``
(messages taken directly), HyperAgent as ``{"trajectory": [log lines]}`` (joined and split with the
HyperAgent parser) and MetaGPT as ``{"content": "<loguru log>"}`` (split on ``Name(Role): to do ...``
lines); the other human traces use the full-file layouts.  Its two GAIA rows have ``mas_name`` and
``benchmark_name`` swapped, which is corrected here.

Annotation: ``category`` = the flagged mode codes joined by ',' (e.g. ``'1.3,1.5'``), None when nothing is
flagged (401 traces) or the annotation is all-null (4 traces).  ``annotation.extra.mast_annotation`` is the
full 14-key dict; for the human file ``extra.votes`` holds the per-annotator booleans per mode and
``category`` is the majority vote (>= 2 of 3) over that round's OWN mode list (18/17/17 modes in rounds
1-3 with different numbering; the 14-mode final taxonomy only in the ``Generlazability`` round), so human
codes of rounds 1-3 are not comparable with the full-file codes -- the mode names are in ``extra.modes``.
Roles: senders named user/human -> user, system -> system, ComputerTerminal -> tool, everything else
-> agent (AG2's ``mathproxyagent`` user-proxy is left as agent).  ``task`` is taken from the log header
(ChatDev ``task_prompt``, OpenManus ``Read prompt from task.txt`` -- truncated by the logger itself,
AppWorld ``Task k/n`` banner, HyperAgent/AG2 ``problem_statement``, human MetaGPT ``prompt``), else the
first parsed message ('' for parse failures).
ids: full file ``<trace.key>#<trace.index>`` (``trace_id`` is NOT unique there: 1,642 records share 206
values), human file ``human/<trace_id>``.  subset = mas_name (AG2, MetaGPT, ChatDev, Magentic,
OpenManus, AppWorld, HyperAgent).  ``limit`` stops early but the full JSON must be parsed first (190 MB).
"""
import ast
import json
import os
import re

SLUG = 'mast_data'
ROOT = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/mast_data/MAST-Data'
FULL = os.path.join(ROOT, 'MAD_full_dataset.json')
HUMAN = os.path.join(ROOT, 'MAD_human_labelled_dataset.json')
MODES = {"1.1": "Disobey task specification", "1.2": "Disobey role specification", "1.3": "Step repetition",
         "1.4": "Loss of conversation history", "1.5": "Unaware of termination conditions",
         "2.1": "Conversation reset", "2.2": "Fail to ask for clarification", "2.3": "Task derailment",
         "2.4": "Information withholding", "2.5": "Ignored other agent's input", "2.6": "Reasoning-action mismatch",
         "3.1": "Premature termination", "3.2": "No or incomplete verification", "3.3": "Incorrect verification"}


# ---------------- heuristic step splitting per framework (from scripts/analyze_mast.py) ----------------
def split_ag2(t):
    msgs = ast.literal_eval("[" + re.sub(r"\}\s+\{'content'", "}, {'content'", t) + "]")
    out = []
    for m in msgs:
        c = m.get("content")
        if isinstance(c, list):
            c = "\n".join(str(x) for x in c)
        out.append((m.get("name") or m.get("role"), str(c)))
    return out


def split_metagpt(t):
    out = []
    first = re.search(r"FROM: (\w+) TO: .*?\nACTION: .*?\nCONTENT:\n(.*?)\n-{20,}", t, re.S)
    if first:
        out.append((first.group(1), first.group(2)))
    for blk in re.split(r"\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\] NEW MESSAGES:\n", t)[1:]:
        blk = blk.strip()
        m = re.match(r"([A-Za-z_]+): ?(.*)", blk, re.S)
        if m:
            body = re.split(r"\n-{20,}", m.group(2))[0]
            out.append((m.group(1), body.strip()))
    return out


def split_chatdev(t):
    out = []
    pat = re.compile(r"^\[[^\]]+ INFO\] (?!System|HTTP|flask|\*\*)([^:\n]{2,40}): (.*?)(?=^\[[^\]]+ INFO\]|\Z)", re.M | re.S)
    for m in pat.finditer(t):
        out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def split_magentic(t):
    parts = re.split(r"^---------- (\S+) ----------$", t, flags=re.M)
    out = []
    for i in range(1, len(parts) - 1, 2):
        out.append((parts[i], parts[i + 1].strip()))
    return out


def split_openmanus(t):
    out = []
    for m in re.finditer(r"Executing step (\d+)/\d+\n(.*?)(?=Executing step \d+/\d+\n|\Z)", t, re.S):
        who = re.search(r"✨ (\w+)'s thoughts", m.group(2))
        out.append((who.group(1) if who else "Manus", m.group(2).strip()))
    return out


def split_appworld(t):
    out = []
    for m in re.finditer(r"^\s*Response from (\S+) Agent\n(.*?)(?=^\s*(?:Response from|Message to|Code Execution Output|Entering)|\Z)", t, re.M | re.S):
        out.append((m.group(1), m.group(2).strip()))
    return out


def split_hyperagent(t):
    out = []
    pat = re.compile(r"HyperAgent_\S+ - INFO - ((?:Planner|Navigator|Executor|Editor|Inner-\w+-Assistant)(?:'s Response|->\w+)?):?(.*?)(?=HyperAgent_\S+ - INFO - |\Z)", re.S)
    for m in pat.finditer(t):
        who = m.group(1).split("'")[0].split("->")[0]
        out.append((who, m.group(2).strip()))
    return out


def split_metagpt_loguru(t):
    """Human-file MetaGPT layout: loguru lines '... | INFO | ... - Alice(SimpleCoder): to do X' followed by the output."""
    pat = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+ \| INFO\s+\| [^\n]*? - ([A-Za-z_]+)\(([A-Za-z_]+)\): (.*?)(?=^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+ \| INFO|\Z)", re.M | re.S)
    out = []
    for m in pat.finditer(t):
        out.append((f"{m.group(1)}({m.group(2)})", m.group(3).strip()))
    return out


SPLIT = {"AG2": split_ag2, "MetaGPT": split_metagpt, "ChatDev": split_chatdev, "Magentic": split_magentic,
         "OpenManus": split_openmanus, "AppWorld": split_appworld, "HyperAgent": split_hyperagent}


def _role(name):
    low = (name or '').strip().lower()
    if low in ('user', 'human', 'user_proxy'):
        return 'user'
    if low == 'system':
        return 'system'
    if low == 'computerterminal':
        return 'tool'
    return 'agent'


def _task(mas, text, steps):
    """Task statement from the framework-specific log header; falls back to the first parsed message."""
    m = None
    if mas == 'ChatDev':
        m = re.search(r'\*\*task_prompt\*\*: (.*?)\n', text)
    elif mas == 'OpenManus':
        m = re.search(r'Read prompt from task\.txt: (.*?)\n', text)
    elif mas == 'AppWorld':
        m = re.search(r'\*{10,} Task \d+/\d+ \([^)]*\)\s*\*{10,}\n(.*?)\n', text)
    elif mas == 'HyperAgent':
        m = re.search(r'^problem_statement:\n(.*?)\n(?=other_data:|\S)', text, re.M | re.S)
    if not m:  # layout does not match mas_name (e.g. the ChatDev logs filed as HyperAgent) or the AG2 YAML dump
        for pat in (r'\*\*task_prompt\*\*: (.*?)\n', r'^problem_statement: (.*?)\n', r'^problem_statement:\n(.*?)\n(?=other_data:|\S)',
                    r'Read prompt from task\.txt: (.*?)\n', r'\*{10,} Task \d+/\d+ \([^)]*\)\s*\*{10,}\n(.*?)\n'):
            m = re.search(pat, text, re.M | re.S)
            if m:
                break
    if m:
        return m.group(1).strip()
    if text.lstrip().startswith('{'):
        try:
            j = json.loads(text)
        except Exception:
            j = None
        if isinstance(j, dict):
            ps = j.get('problem_statement')
            if isinstance(ps, list) and ps:
                return '\n'.join(str(x) for x in ps).strip()
            if isinstance(ps, str):
                return ps.strip()
            if isinstance(j.get('prompt'), str):
                return j['prompt'].strip()
    return steps[0]['content'] if steps and not steps[0]['meta'].get('parse_failed') else ''


def _parse(mas, text):
    """Return (list of (agent, content), parser_name) or (None, parser_name) on failure."""
    stripped = text.lstrip()
    if stripped.startswith('{'):
        try:
            j = json.loads(text)
        except Exception:
            j = None
        if isinstance(j, dict):
            traj = j.get('trajectory')
            if isinstance(traj, list) and traj and all(isinstance(x, dict) for x in traj):
                out = []
                for m in traj:
                    c = m.get('content')
                    if isinstance(c, list):
                        c = '\n'.join(str(x) for x in c)
                    out.append((str(m.get('name') or m.get('role') or mas), str(c)))
                return out, 'json_trajectory_messages'
            if isinstance(traj, list) and all(isinstance(x, str) for x in traj):
                joined = '\n'.join(traj)
                fn = SPLIT.get(mas, split_hyperagent)
                try:
                    out = fn(joined)
                except Exception:
                    out = []
                return (out or None), f'json_trajectory_lines+{fn.__name__}'
            if isinstance(j.get('content'), str):
                out = split_metagpt_loguru(j['content'])
                if not out:
                    try:
                        out = SPLIT.get(mas, split_metagpt)(j['content'])
                    except Exception:
                        out = []
                return (out or None), 'json_content+split_metagpt_loguru'
    fn = SPLIT.get(mas)
    if fn is None:
        return None, 'none'
    try:
        out = fn(text)
    except Exception:
        return None, fn.__name__
    return (out or None), fn.__name__


def _steps(mas, text):
    msgs, parser = _parse(mas, text)
    if not msgs:
        return [{'idx': 0, 'native_idx': 0, 'agent': mas, 'role': 'system', 'content': text,
                 'meta': {'parse_failed': True, 'parser': parser}}], True, parser
    steps = []
    for i, (who, c) in enumerate(msgs):
        who = str(who or '').strip()
        steps.append({'idx': i, 'native_idx': i, 'agent': who, 'role': _role(who), 'content': c, 'meta': {}})
    return steps, False, parser


def _traj(tid, mas, bench, llm, text, category, extra, meta):
    steps, failed, parser = _steps(mas, text)
    task = _task(mas, text, steps)
    meta = dict(meta)
    meta.update({'mas_name': mas, 'llm_name': llm, 'benchmark_name': bench, 'parse_failed': failed, 'parser': parser,
                 'trace_chars': len(text), 'license': 'CC BY 4.0'})
    return {
        'dataset': SLUG, 'id': tid, 'subset': mas, 'system': mas,
        'task': task, 'ground_truth': None,
        'final_output': steps[-1]['content'] if not failed else None,
        'outcome': None, 'steps': steps,
        'annotation': {'faulty_step': None, 'faulty_steps': [], 'faulty_agent': None, 'category': category,
                       'reason': None, 'extra': extra},
        'meta': meta,
    }


def _code(label):
    """'1.3 Step repetition\\n\\n...' -> ('1.3', 'Step repetition')."""
    head = label.split('\n')[0].strip()
    m = re.match(r'(\d+\.\d+)\s*(.*)', head)
    return (m.group(1), m.group(2).strip()) if m else (head, head)


def load(limit=None, subset=None):
    n = 0
    with open(FULL, encoding='utf-8') as f:
        full = json.load(f)
    for r in full:
        mas = r['mas_name']
        if subset is not None and mas != subset:
            continue
        ann = r.get('mast_annotation') or {}
        all_null = all(v is None for v in ann.values())
        flagged = [k for k, v in ann.items() if v == 1]
        extra = {'mast_annotation': ann, 'flagged_modes': flagged,
                 'flagged_mode_names': [f'FM-{k} {MODES.get(k, "")}' for k in flagged],
                 'annotation_null': all_null, 'annotator': 'LLM judge (OpenAI o1, few-shot), trace-level binary flags'}
        yield _traj(f"{r['trace']['key']}#{r['trace']['index']}", mas, r.get('benchmark_name'), r.get('llm_name'),
                    r['trace']['trajectory'], ','.join(flagged) if flagged else None, extra,
                    {'file': FULL, 'trace_key': r['trace'].get('key'), 'trace_index': r['trace'].get('index'),
                     'trace_id': r['trace_id'], 'source': 'MAD_full_dataset.json'})
        n += 1
        if limit is not None and n >= limit:
            return
    del full
    with open(HUMAN, encoding='utf-8') as f:
        human = json.load(f)
    for r in human:
        mas, bench = r.get('mas_name'), r.get('benchmark_name')
        if mas not in SPLIT and bench in SPLIT:  # the two GAIA rows have the fields swapped
            mas, bench = bench, mas
        if subset is not None and mas != subset:
            continue
        votes = []
        flagged = []
        modes = {}
        for a in r.get('annotations') or []:
            code, name = _code(a.get('failure mode', ''))
            vs = {k: a.get(k) for k in ('annotator_1', 'annotator_2', 'annotator_3') if k in a}
            modes[code] = name
            votes.append({'code': code, 'name': name, **vs})
            if sum(1 for v in vs.values() if v) >= 2:
                flagged.append(code)
        extra = {'mast_annotation': {c: (1 if c in flagged else 0) for c in modes},
                 'flagged_modes': flagged, 'flagged_mode_names': [f'{c} {modes[c]}' for c in flagged],
                 'votes': votes, 'modes': modes, 'round': r.get('round'),
                 'annotation_null': False,
                 'annotator': 'three human annotators; category = majority vote over the round\'s own mode list',
                 'codes_note': 'rounds 1-3 use an earlier 18/17/17-mode taxonomy whose codes differ from the final 14 modes'}
        yield _traj(f"human/{r['trace_id']}", mas, bench, r.get('llm_name') or '', r['trace'],
                    ','.join(flagged) if flagged else None, extra,
                    {'file': HUMAN, 'trace_id': r['trace_id'], 'round': r.get('round'), 'source': 'MAD_human_labelled_dataset.json',
                     'mas_benchmark_swapped_in_file': (mas != r.get('mas_name'))})
        n += 1
        if limit is not None and n >= limit:
            return
