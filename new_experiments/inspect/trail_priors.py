#!/usr/bin/env python3
"""Structural priors for the TRAIL primary (earliest HIGH) span, to test whether the label is structural:
  P_first_action : first CodeAgent LLM span after the facts+plan calls (idx 8 in GAIA, first LLM after Step-1 CHAIN in SWE)
  P_last_code    : last CodeAgent LLM span before FinalAnswerTool
  P_first_toolerr: first LLM span whose next TOOL span has status Error
  P_first_llm    : first LLM span of the trace
Reports exact-hit and within-3 against primary_idx and against the error-span set, per subset."""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import md_table  # noqa: E402
from loaders import load  # noqa: E402


def priors(r):
    st = r['steps']
    llm = [s['idx'] for s in st if s['role'] == 'agent']
    code_llm = [s['idx'] for s in st if s['role'] == 'agent' and s['agent'] == 'CodeAgent']
    chain1 = next((s['idx'] for s in st if s['meta']['kind'] == 'CHAIN' and s['agent'] == 'CodeAgent'), None)
    first_action = next((i for i in code_llm if chain1 is not None and i > chain1), None)
    fa = next((s['idx'] for s in st if s['meta']['span_name'] == 'FinalAnswerTool'), None)
    last_code = max((i for i in code_llm if fa is None or i < fa), default=None)
    first_toolerr = None
    for s in st:
        if s['role'] == 'tool' and s['meta'].get('status_code') == 'Error':
            prev = max((i for i in llm if i < s['idx']), default=None)
            first_toolerr = prev
            break
    return {'first_action': first_action, 'last_code': last_code, 'first_toolerr': first_toolerr, 'first_llm': llm[0] if llm else None}


def main():
    recs = [r for r in load('trail') if r['labels']['extra']['primary_idx'] is not None]
    rows = []
    for sub in ('gaia', 'swe_bench', 'ALL'):
        rs = [r for r in recs if sub == 'ALL' or r['subset'] == sub]
        for name in ('first_action', 'last_code', 'first_toolerr', 'first_llm'):
            hit = w3 = inset = fired = 0
            for r in rs:
                p = priors(r)[name]
                if p is None:
                    continue
                fired += 1
                g = r['labels']['extra']['primary_idx']
                hit += p == g
                w3 += abs(p - g) <= 3
                inset += p in set(r['labels']['error_steps'])
            rows.append([sub, name, len(rs), fired, f'{100 * hit / len(rs):.1f}', f'{100 * w3 / len(rs):.1f}', f'{100 * inset / len(rs):.1f}'])
        # random agent-step prior
        import random
        rng = random.Random(0)
        hit = 0
        for r in rs:
            for _ in range(20):
                p = rng.choice([s['idx'] for s in r['steps'] if s['role'] == 'agent'])
                hit += p == r['labels']['extra']['primary_idx']
        rows.append([sub, 'random LLM span', len(rs), len(rs), f'{100 * hit / (20 * len(rs)):.1f}', '', ''])
    print(md_table(['subset', 'prior', 'n', 'fired', 'exact% (primary)', 'within3%', 'in error set%'], rows))


if __name__ == '__main__':
    main()
