"""AEGIS / Aegis-Bench (Fancylalala/AEGIS, arXiv:2509.14295) loader.

Files: data/aegis/Aegis-Bench/test.jsonl (600), data/aegis/Aegis-Training/train.jsonl (7,146) and val.jsonl
(1,787), read in the order test, train, val.  All 9,533 trajectories are injected failures (outcome 0).

Step unit / index mapping
-------------------------
One entry of ``input.conversation_history`` = one step, in file order; ``native_idx`` is the entry's 1-based
``step`` field (contiguous from 1 in every record), so ``idx = step - 1``.

AEGIS has NO step-level label: the ground truth is the set of (agent, error mode) pairs in
``output.faulty_agents``.  Therefore ``faulty_step = None`` and ``faulty_steps`` = indices of every turn whose
``agent_name`` is one of the faulty agents (every faulty agent speaks at least once in every record).
``faulty_agent`` = the distinct faulty agent names joined by ``|`` (in pair order), ``category`` = the pair
``error_type`` values joined by ``,`` (same order, one per pair, so an agent with two modes appears twice in
``category`` but once in ``faulty_agent``).  MacNet records flag turns with ``is_injected``; their indices go
to ``annotation.extra.injected_step_idxs`` (note: they also flag turns of ``Node-2``, which is never a faulty
agent, so the two sets differ).

Roles: ``User``/``user`` turns -> user, ``System`` -> system, ``ComputerTerminal`` -> tool, everything else
-> agent.  ``content`` is ``None`` in 152 turns (rendered as '').  Two ids occur in both train and val with
different histories; the second occurrence gets ``#<split>`` appended so ids stay unique.
subset = split in {test, train, val}.
"""
import json
import os

SLUG = 'aegis'
ROOT = '/dataDisk/home/thanhdo/failure-attribution-datasets/data/aegis'
FILES = [('test', os.path.join(ROOT, 'Aegis-Bench', 'test.jsonl')),
         ('train', os.path.join(ROOT, 'Aegis-Training', 'train.jsonl')),
         ('val', os.path.join(ROOT, 'Aegis-Training', 'val.jsonl'))]
SYSTEM = {'agentverse': 'AgentVerse', 'llm_debate': 'LLM Debate', 'macnet': 'MacNet', 'dylan': 'DyLAN',
          'smoagents': 'SmolAgents', 'magentic_one': 'Magentic-One'}


def _role(name):
    low = (name or '').strip().lower()
    if low == 'user':
        return 'user'
    if low == 'system':
        return 'system'
    if low == 'computerterminal':
        return 'tool'
    return 'agent'


def load(limit=None, subset=None):
    n = 0
    seen = set()
    for split, path in FILES:
        if subset is not None and subset != split:
            continue
        with open(path, encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                md = d.get('metadata') or {}
                inp = d.get('input') or {}
                h = inp.get('conversation_history') or []
                pairs = (d.get('output') or {}).get('faulty_agents') or []
                inj = (d.get('ground_truth') or {}).get('injected_agents') or []
                faulty_names = []
                for p in pairs:
                    if p.get('agent_name') not in faulty_names:
                        faulty_names.append(p.get('agent_name'))
                steps = []
                for i, x in enumerate(h):
                    name = str(x.get('agent_name') or '').strip()
                    meta = {'phase': x.get('phase')}
                    if 'agent_role' in x:
                        meta['agent_role'] = x.get('agent_role')
                    if 'is_injected' in x:
                        meta['is_injected'] = bool(x.get('is_injected'))
                    c = x.get('content')
                    steps.append({'idx': i, 'native_idx': x.get('step', i + 1), 'agent': name, 'role': _role(name),
                                  'content': c if isinstance(c, str) else ('' if c is None else json.dumps(c, ensure_ascii=False)),
                                  'meta': meta})
                faulty_steps = [i for i, x in enumerate(h) if x.get('agent_name') in faulty_names]
                injected_idxs = [i for i, x in enumerate(h) if x.get('is_injected')]
                tid = d['id']
                if tid in seen:
                    tid = f'{tid}#{split}'
                seen.add(tid)
                descs = [x.get('malicious_action_description') for x in inj if x.get('malicious_action_description')]
                yield {
                    'dataset': SLUG,
                    'id': tid,
                    'subset': split,
                    'system': SYSTEM.get(md.get('framework'), md.get('framework') or ''),
                    'task': inp.get('query') or '',
                    'ground_truth': (d.get('ground_truth') or {}).get('correct_answer'),
                    'final_output': inp.get('final_output'),
                    'outcome': 0,
                    'steps': steps,
                    'annotation': {
                        'faulty_step': None,
                        'faulty_steps': faulty_steps,
                        'faulty_agent': '|'.join(faulty_names) if faulty_names else None,
                        'category': ','.join(p.get('error_type') or '' for p in pairs) if pairs else None,
                        'reason': ' ; '.join(descs) if descs else None,
                        'extra': {
                            'faulty_agents': pairs,
                            'injected_agents': inj,
                            'injection_strategies': sorted(set(p.get('injection_strategy') for p in pairs if p.get('injection_strategy'))),
                            'malicious_action_description': descs,
                            'injected_step_idxs': injected_idxs,
                            'is_injection_successful': (d.get('ground_truth') or {}).get('is_injection_successful'),
                            'num_injected_agents': md.get('num_injected_agents'),
                            'label_note': 'agent + error-mode pairs only; faulty_steps = all turns of the faulty agents, not a decisive step',
                        },
                    },
                    'meta': {'framework': md.get('framework'), 'benchmark': md.get('benchmark'), 'model': md.get('model'),
                             'task_type': md.get('task_type'), 'num_agents': md.get('num_agents'), 'split': split,
                             'native_id': d['id'], 'file': path, 'license': 'MIT'},
                }
                n += 1
                if limit is not None and n >= limit:
                    return
