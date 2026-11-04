#!/usr/bin/env python3
"""Structural priors and verification-theatre statistics for LongRCA.
(a) exact-hit rate of simple structural rules per source (first delegation, final JSON write, first verifier turn, ...)
(b) TravelPlanner verifier: all-pass before final write; verifier flagged passed:false but run completed anyway
(c) TravelPlanner final-write inconsistency: duplicates across days / items absent from the blackboard snapshot"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402

recs = load('longrca')


def first_idx(r, pred):
    return next((s['idx'] for s in r['steps'] if pred(s)), None)


def last_idx(r, pred):
    return next((s['idx'] for s in reversed(r['steps']) if pred(s)), None)


RULES = {
    'first DiagnostAgent->ActionAgent delegation': lambda r: first_idx(r, lambda s: s['agent'] == 'DiagnostAgent (-> ActionAgent)'),
    'last DiagnostAgent->ActionAgent delegation': lambda r: last_idx(r, lambda s: s['agent'] == 'DiagnostAgent (-> ActionAgent)'),
    'first file edit (str_replace/create)': lambda r: first_idx(r, lambda s: s['role'] == 'agent' and re.search(r'```(str_replace|create)', s['content'])),
    'final itinerary JSON write': lambda r: last_idx(r, lambda s: s['role'] == 'agent' and '"days": [' in s['content']),
    'first Task_Planner delegation (step 2)': lambda r: 2 if len(r['steps']) > 2 else None,
    'first accommodation_search call': lambda r: first_idx(r, lambda s: s['role'] == 'agent' and 'accommodation_search' in s['content'][:60]),
    'first Verification_Expert turn': lambda r: first_idx(r, lambda s: s['agent'] == 'Verification_Expert'),
    'last Action_Expert turn': lambda r: last_idx(r, lambda s: s['agent'] == 'Action_Expert'),
    'first Action_Expert turn': lambda r: first_idx(r, lambda s: s['agent'] == 'Action_Expert'),
    'last agent step': lambda r: last_idx(r, lambda s: s['role'] == 'agent'),
    'first order/pay tool call (vita)': lambda r: first_idx(r, lambda s: s['role'] == 'agent' and re.search(r'Tool call: (create_|pay_|instore_book)', s['content'])),
    'last agent turn before an user complaint (vita)': lambda r: None,
}


def main():
    srcs = sorted(set(r['subset'] for r in recs))
    print('## (a) structural-rule exact hit rates (and within 5) per source\n')
    tbl = []
    for name, f in RULES.items():
        row = [name]
        for src in srcs:
            xs = [r for r in recs if r['subset'] == src]
            hits = sum(1 for r in xs if f(r) is not None and f(r) == error_step(r))
            near = sum(1 for r in xs if f(r) is not None and abs(f(r) - error_step(r)) <= 5)
            fires = sum(1 for r in xs if f(r) is not None)
            row.append(f'{100 * hits / len(xs):.0f}% / {100 * near / len(xs):.0f}% (fires {100 * fires / len(xs):.0f}%)')
        tbl.append(row)
    # random/position prior: 1/n_agent_steps
    row = ['uniform over agent steps (expected exact)']
    for src in srcs:
        xs = [r for r in recs if r['subset'] == src]
        row.append(f"{100 * sum(1 / max(1, sum(1 for s in r['steps'] if s['role'] == 'agent')) for r in xs) / len(xs):.1f}%")
    tbl.append(row)
    print(md_table(['rule'] + srcs, tbl))

    print('\n## (b) TravelPlanner verifier behaviour\n')
    tp = [r for r in recs if r['subset'] == 'travelplanner']
    allpass = flagged_but_completed = flagged = nover = 0
    for r in tp:
        st = r['steps']
        concl = [s for s in st if s['role'] == 'agent' and 'add_verifier_conclusion' in s['content'][:60]]
        if not concl:
            nover += 1
            continue
        fails = [s for s in concl if '"passed": false' in s['content']]
        if not fails:
            allpass += 1
        else:
            flagged += 1
            last_fail = fails[-1]['idx']
            fin = st[-1]['content']
            if 'TASK_COMPLETE' in fin or 'successfully' in fin.lower() or 'verified' in fin.lower():
                # did a re-search / fix happen after last fail? crude: any tool call by a specialist after the last fail
                flagged_but_completed += 1
    print(f'TP runs: no verifier conclusion at all {nover}/{len(tp)}; verifier conclusions all passed:true {allpass}; at least one passed:false {flagged}; of those, run still terminated as complete {flagged_but_completed}')

    print('\n## (c) TravelPlanner final-write inconsistencies\n')
    dup = absent = n_fin = 0; both = 0; late_root_fin = 0; late_root_fin_inconsistent = 0
    for r in tp:
        st = r['steps']
        fin = next((s for s in reversed(st) if s['role'] == 'agent' and '"days": [' in s['content']), None)
        if fin is None:
            continue
        n_fin += 1
        bb = next((s['content'] for s in st if 'Blackboard snapshot' in s['content']), '')
        try:
            j = json.loads(fin['content'][fin['content'].index('{'):])
            days = j.get('days') or j.get('plan') or []
        except Exception:
            days = []
        names = []
        for d in days:
            for k in ('breakfast', 'lunch', 'dinner', 'attraction', 'accommodation'):
                v = d.get(k)
                if isinstance(v, str) and v != '-':
                    for part in v.split(';'):
                        names.append((k, part.split(',')[0].strip()))
        meals = [n for k, n in names if k in ('breakfast', 'lunch', 'dinner')]
        has_dup = len(meals) != len(set(meals))
        has_absent = any(n and n not in bb for k, n in names)
        dup += has_dup; absent += has_absent; both += has_dup or has_absent
        g = error_step(r)
        if g == fin['idx']:
            late_root_fin += 1
            late_root_fin_inconsistent += (has_dup or has_absent)
    print(f'TP runs with a final JSON: {n_fin}; duplicate meal names across the plan {dup} ({100 * dup / n_fin:.0f}%); some named item absent from the blackboard snapshot {absent} ({100 * absent / n_fin:.0f}%); either {both}')
    print(f'runs whose root IS the final JSON write: {late_root_fin}; of those with a detectable inconsistency (dup or absent): {late_root_fin_inconsistent}')


if __name__ == '__main__':
    main()
