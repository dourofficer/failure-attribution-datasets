"""TracerTraj (AgenTracer data release v1.0.0, arXiv:2509.03312) loader.

Files: data/tracertraj/extracted/agentracer-data-v1.0.0/{agentic,coding,math}/{train,test}.jsonl, read in that
fixed order.  3,208 train + 790 test = 3,998 rows, all failures (outcome 0).

Step unit / index mapping
-------------------------
One entry of ``history`` = one step, in file order.  ``native_idx`` is the entry's own ``step`` field, which is
**1-based in the agentic domain and 0-based in coding/math** (verified contiguous in every row).  The label
``mistake_step`` is stored as a *string*; it is mapped as
``faulty_step = the position i with history[i].step == int(mistake_step)`` (unique in every row; for agentic
this equals ``int(mistake_step) - 1``, for coding/math ``int(mistake_step)``).  ``faulty_steps = [faulty_step]``.
The named sender of the labelled step equals ``mistake_agent`` in 100 % of rows.

Every history entry has chat role ``assistant`` (role ``agent``); agentic rows carry no ``name``, so their
agent is the generic ``assistant``.  The task is NOT part of ``history`` (it is the ``question`` field) and is
not inserted as a step.  ``question_ID`` is not unique (97 repeats inside math/train, 21 ids in both splits), so
``id = '<domain>/<split>/<question_ID>'`` with a ``#k`` suffix for the k-th repeat inside one file.
``system`` is inferred from the paper (coding = MetaGPT roles, math = AFlow operators, agentic = unknown).
subset = '<domain>/<split>' (a bare domain name also matches both splits).
"""
import json
import os

SLUG = 'tracertraj'
ROOT = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/tracertraj/extracted/agentracer-data-v1.0.0'
DOMAINS = ['agentic', 'coding', 'math']
SPLITS = ['train', 'test']
SYSTEM = {'agentic': '', 'coding': 'MetaGPT', 'math': 'AFlow'}


def _agent_of(x):
    return str(x.get('name') or x.get('role') or '').strip()


def load(limit=None, subset=None):
    n = 0
    for dom in DOMAINS:
        for sp in SPLITS:
            key = f'{dom}/{sp}'
            if subset is not None and subset not in (key, dom):
                continue
            path = os.path.join(ROOT, dom, f'{sp}.jsonl')
            seen = {}
            with open(path, encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    h = d.get('history') or []
                    ms = int(d['mistake_step'])
                    pos = [i for i, x in enumerate(h) if x.get('step') == ms]
                    fidx = pos[0] if len(pos) == 1 else None
                    qid = str(d.get('question_ID'))
                    k = seen.get(qid, 0)
                    seen[qid] = k + 1
                    tid = f'{key}/{qid}' + (f'#{k + 1}' if k else '')
                    steps = []
                    for i, x in enumerate(h):
                        steps.append({'idx': i, 'native_idx': x.get('step'), 'agent': _agent_of(x), 'role': 'agent',
                                      'content': x.get('content') if isinstance(x.get('content'), str) else json.dumps(x.get('content'), ensure_ascii=False),
                                      'meta': {'chat_role': x.get('role'), 'name': x.get('name')}})
                    yield {
                        'dataset': SLUG,
                        'id': tid,
                        'subset': key,
                        'system': SYSTEM[dom],
                        'task': d.get('question') or '',
                        'ground_truth': d.get('ground_truth'),
                        'final_output': h[-1].get('content') if h else None,
                        'outcome': 0,
                        'steps': steps,
                        'annotation': {
                            'faulty_step': fidx,
                            'faulty_steps': [fidx] if fidx is not None else [],
                            'faulty_agent': d.get('mistake_agent'),
                            'category': d.get('error_source'),
                            'reason': d.get('mistake_reason') or None,
                            'extra': {
                                'mistake_step_raw': d['mistake_step'],
                                'step_base': h[0].get('step') if h else None,
                                'error_source': d.get('error_source'),
                                'agent_at_faulty_step': _agent_of(h[fidx]) if fidx is not None else None,
                            },
                        },
                        'meta': {'domain': dom, 'split': sp, 'question_ID': qid, 'error_source': d.get('error_source'),
                                 'ground_truth': d.get('ground_truth'), 'file': path,
                                 'system_note': 'system inferred from the paper (MetaGPT roles / AFlow operators); agentic MAS not identifiable from the row',
                                 'license': 'none stated'},
                    }
                    n += 1
                    if limit is not None and n >= limit:
                        return
