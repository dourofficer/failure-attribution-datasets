#!/usr/bin/env python3
"""TraceElephant vs Who&When: match runs by task text, compare blamed agent and the content of the labelled step.
Writes results/traceelephant/ww_overlap.json."""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, write_json, md_table  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402


def norm(t):
    return re.sub(r'\s+', ' ', (t or '').strip().lower())[:300]


def base(a):
    return re.sub(r'\s*\(.*\)$', '', str(a or '')).strip().lower()


def main():
    te = [r for r in load('traceelephant') if r['subset'] != 'swe-agent']
    ww = load('who_and_when')
    by_task = {}
    for w in ww:
        by_task.setdefault(norm(w['task']), []).append(w)
    rows = []
    for r in te:
        ws = by_task.get(norm(r['task']))
        if not ws:
            continue
        for w in ws:
            g_te, g_ww = error_step(r), error_step(w)
            rows.append({'te_id': r['id'], 'te_subset': r['subset'], 'ww_id': w['id'], 'ww_subset': w['subset'],
                         'te_agent': r['labels']['error_agent'], 'ww_agent': w['labels']['error_agent'],
                         'agent_eq': base(r['labels']['error_agent']) == base(w['labels']['error_agent']),
                         'te_step': g_te, 'te_n': len(r['steps']), 'ww_step': g_ww, 'ww_n': len(w['steps']),
                         'te_rel': g_te / max(1, len(r['steps']) - 1) if g_te is not None else None, 'ww_rel': g_ww / max(1, len(w['steps']) - 1),
                         'te_reason': r['labels']['reason'], 'ww_reason': w['labels']['reason'],
                         'te_step_text': r['steps'][g_te]['content'][:400] if g_te is not None else None,
                         'ww_step_text': w['steps'][g_ww]['content'][:400],
                         'te_final': (r.get('final_output') or '')[-300:], 'ww_final': (w.get('final_output') or '')[-300:] if w.get('final_output') else None,
                         'gt': r.get('ground_truth')})
    write_json(os.path.join(RESULTS, 'traceelephant', 'ww_overlap.json'), rows)
    print(len(rows), 'matched pairs;', len({x['te_id'] for x in rows}), 'TE runs;', Counter((x['te_subset'], x['ww_subset']) for x in rows))
    print('agent agree:', sum(x['agent_eq'] for x in rows))
    print('agent pairs:', Counter((x['te_agent'], x['ww_agent']) for x in rows).most_common(12))
    print('te_rel vs ww_rel mean:', sum(x['te_rel'] for x in rows if x['te_rel'] is not None) / len(rows), sum(x['ww_rel'] for x in rows) / len(rows))
    print('TE later than WW (relative):', sum(1 for x in rows if x['te_rel'] is not None and x['te_rel'] > x['ww_rel'] + 0.1),
          'earlier:', sum(1 for x in rows if x['te_rel'] is not None and x['te_rel'] < x['ww_rel'] - 0.1))
    # are the two runs the same run? compare the first agent output text
    same = 0
    for x in rows:
        pass
    print('WW subsets of matches:', Counter(x['ww_subset'] for x in rows))


if __name__ == '__main__':
    main()
