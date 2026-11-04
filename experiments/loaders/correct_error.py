"""CORRECT-Error (yifanyu/CORRECT-Error, arXiv:2509.24088) loader.

File: data/correct_error/CORRECT-Error/data/test-00000-of-00001.parquet (the only split, 2,226 rows), read
with pandas/pyarrow from the user site-packages.  All rows are injected failures (outcome 0).

Step unit / index mapping
-------------------------
One entry of ``history`` (``{role, content}``) = one step in order; ``history[0]`` is always the ``user`` task
message.  ``native_idx = i`` (0-based position).  ``mistake_step`` is a 0-based index into ``history`` that
counts the user message at 0 (verified: 91.6 % of rows have ``history[mistake_step].role == mistake_agent``
under this reading vs 4.3 % under a 1-based one), so ``faulty_step = int(mistake_step)`` with no shift;
``faulty_steps = [faulty_step]``.  43 rows label step 0 (the user message; their ``mistake_agent`` is
``Unknown`` in 42 of them) and 186 rows name an agent that is not the sender of the labelled step
(``annotation.extra.agent_matches_step`` records this).

Roles: ``user`` -> user, ``CodeExecutor`` -> tool (it returns execution output), Planner / WebSurfer /
Coder / FileSurfer -> agent.  ``faulty_agent`` is ``mistake_agent`` with surrounding brackets / whitespace
stripped (``[Planner]`` -> ``Planner``); the raw string is kept in ``annotation.extra.mistake_agent_raw``.
``mistake_reason`` and ``groundtruth`` are empty in every row (None here).  subset = ``dataset`` field
(wikimqa, hotpot, musique, arc, math500, mmlu_pro, gaia).
"""
import math
import os
import sys

USER_SITE = '/dataDisk/home/thanhdo/.local/lib/python3.10/site-packages'
if USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

SLUG = 'correct_error'
PARQUET = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/correct_error/CORRECT-Error/data/test-00000-of-00001.parquet'
SYSTEM = 'Magentic-One variant (AutoGen selector group chat: Planner/WebSurfer/Coder/CodeExecutor/FileSurfer)'


def _norm_agent(a):
    a = (a or '').strip()
    a = a.strip('[]').strip()
    return a


def _role(r):
    low = (r or '').strip().lower()
    if low == 'user':
        return 'user'
    if low == 'codeexecutor':
        return 'tool'
    return 'agent'


def _clean(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def load(limit=None, subset=None):
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(PARQUET)
    n = 0
    for batch in pf.iter_batches(batch_size=256):
        for row in batch.to_pylist():
            if subset is not None and row.get('dataset') != subset:
                continue
            h = list(row.get('history') or [])
            ms = int(row['mistake_step'])
            steps = []
            for i, m in enumerate(h):
                role = str(m.get('role') or '')
                steps.append({'idx': i, 'native_idx': i, 'agent': role.strip(), 'role': _role(role),
                              'content': m.get('content') if isinstance(m.get('content'), str) else '', 'meta': {}})
            fidx = ms if 0 <= ms < len(h) else None
            agent_raw = row.get('mistake_agent')
            agent = _norm_agent(agent_raw)
            step_agent = h[fidx].get('role') if fidx is not None else None
            gl = _clean(row.get('gaia_level'))
            yield {
                'dataset': SLUG,
                'id': row['trajectory_id'],
                'subset': row.get('dataset') or '',
                'system': SYSTEM,
                'task': row.get('question') or '',
                'ground_truth': row.get('groundtruth') or None,
                'final_output': h[-1].get('content') if h else None,
                'outcome': 0,
                'steps': steps,
                'annotation': {
                    'faulty_step': fidx,
                    'faulty_steps': [fidx] if fidx is not None else [],
                    'faulty_agent': agent or None,
                    'category': None,
                    'reason': row.get('mistake_reason') or None,
                    'extra': {
                        'mistake_step_raw': ms,
                        'mistake_agent_raw': agent_raw,
                        'agent_at_faulty_step': step_agent,
                        'agent_matches_step': (_norm_agent(step_agent) == agent) if step_agent is not None else None,
                        'is_corrected': bool(row.get('is_corrected')),
                        'level': _clean(row.get('level')),
                    },
                },
                'meta': {'generator_model': row.get('generator_model'), 'question_id': row.get('question_id'),
                         'gaia_level': gl, 'dataset': row.get('dataset'), 'file': PARQUET, 'license': 'Apache-2.0'},
            }
            n += 1
            if limit is not None and n >= limit:
                return
