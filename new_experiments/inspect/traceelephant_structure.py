#!/usr/bin/env python3
"""TraceElephant: step-type structure, ledger stall flags vs the labelled step, agent attribution of ledger calls.
Writes results/traceelephant/structure.json (per record) and prints summary tables."""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, write_json, summarize  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402


def ledger(content):
    """Parse a Magentic-One progress ledger JSON at the start of the content; return dict or None."""
    s = content.lstrip()
    if not s.startswith('{'):
        return None
    depth = 0
    for i, ch in enumerate(s):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                try:
                    d = json.loads(s[:i + 1])
                except Exception:  # noqa
                    return None
                return d if isinstance(d, dict) and 'is_progress_being_made' in d else None
    return None


def step_type(s, rec):
    c = s['content']
    sub = rec['subset']
    L = ledger(c)
    if L is not None:
        return 'ledger', L
    if sub == 'magentic-one':
        if c.startswith('1. GIVEN OR VERIFIED FACTS') or 'GIVEN OR VERIFIED FACTS' in c[:200]:
            return 'facts', None
        if 'FINAL ANSWER' in c:
            return 'final', None
        if '\nAction:' in c or c.startswith('Action:'):
            return 'action', None
        if s['agent'] == 'Orchestrator':
            return 'plan', None
        return 'text', None
    if sub == 'swe-agent':
        return ('action' if ('\nAction:' in c or c.startswith('Action:')) else 'text'), None
    # captain
    if 'FINAL ANSWER' in c or 'TERMINATE' in c:
        return 'final', None
    if '\nAction:' in c or c.startswith('Action:'):
        return 'action', None
    return 'text', None


def main():
    recs = load('traceelephant')
    per = []
    for r in recs:
        g = error_step(r)
        types, flags = [], []
        for s in r['steps']:
            t, L = step_type(s, r)
            types.append(t)
            f = None
            if L:
                def b(k):
                    v = L.get(k, {})
                    v = v.get('answer') if isinstance(v, dict) else v
                    return v
                f = {'loop': b('is_in_loop') is True, 'noprog': b('is_progress_being_made') is False, 'sat': b('is_request_satisfied') is True,
                     'next': b('next_speaker')}
            flags.append(f)
        stall = [i for i, f in enumerate(flags) if f and (f['loop'] or f['noprog'])]
        per.append({'id': r['id'], 'subset': r['subset'], 'n': len(r['steps']), 'gold': g, 'gold_agent': r['labels']['error_agent'],
                    'gold_type': types[g] if g is not None else None, 'gold_step_agent': r['steps'][g]['agent'] if g is not None else None,
                    'types': types, 'stall_steps': stall, 'first_stall': stall[0] if stall else None,
                    'n_ledger': sum(1 for t in types if t == 'ledger'), 'reason': r['labels']['reason']})
    write_json(os.path.join(RESULTS, 'traceelephant', 'structure.json'), per)
    # 1. step types per subset
    for sub in ('magentic-one', 'captain-agent', 'swe-agent'):
        rs = [p for p in per if p['subset'] == sub]
        print(f'\n## {sub}: n={len(rs)}')
        print('step types:', Counter(t for p in rs for t in p['types']))
        print('gold step type:', Counter(p['gold_type'] for p in rs))
    # 2. Magentic-One: ledger calls attributed to which agent_name?
    mo = [r for r in recs if r['subset'] == 'magentic-one']
    c = Counter()
    for r in mo:
        for s in r['steps']:
            if ledger(s['content']) is not None:
                c[s['agent']] += 1
    print('\nledger calls by recorded agent_name (Magentic-One):', dict(c))
    gl = [(p['gold_step_agent'], p['gold_agent']) for p in per if p['subset'] == 'magentic-one' and p['gold_type'] == 'ledger']
    print('gold steps that are ledger calls: n=%d; recorded agent of those: %s' % (len(gl), Counter(a for a, _ in gl)))
    # 3. stall flags vs gold
    rows = []
    for p in per:
        if p['subset'] != 'magentic-one' or p['gold'] is None:
            continue
        rows.append(p)
    with_stall = [p for p in rows if p['first_stall'] is not None]
    before = [p for p in with_stall if p['first_stall'] < p['gold']]
    after = [p for p in with_stall if p['first_stall'] > p['gold']]
    eq = [p for p in with_stall if p['first_stall'] == p['gold']]
    print(f'\nMagentic-One records with any stall flag: {len(with_stall)}/{len(rows)}; first stall before gold {len(before)}, at gold {len(eq)}, after gold {len(after)}')
    print('offset first_stall - gold (after):', summarize([p['first_stall'] - p['gold'] for p in after]))
    print('offset first_stall - gold (before):', summarize([p['first_stall'] - p['gold'] for p in before]))
    # stall flags per position relative to gold
    rel = Counter()
    for p in rows:
        for i in p['stall_steps']:
            rel['before' if i < p['gold'] else 'at' if i == p['gold'] else 'after'] += 1
    nled = Counter()
    for p in rows:
        for i, t in enumerate(p['types']):
            if t == 'ledger':
                nled['before' if i < p['gold'] else 'at' if i == p['gold'] else 'after'] += 1
    print('stall-flag rate on ledger calls before gold: %d/%d, at: %d/%d, after: %d/%d' % (rel['before'], nled['before'], rel['at'], nled['at'], rel['after'], nled['after']))
    # 4. is the step just after gold a ledger with a stall flag?
    nxt = Counter()
    for p in rows:
        g = p['gold']
        for k in range(1, 4):
            if g + k < p['n'] and p['types'][g + k] == 'ledger':
                nxt[k, (g + k) in p['stall_steps']] += 1
    print('ledger at gold+k is stall:', dict(nxt))


if __name__ == '__main__':
    main()
