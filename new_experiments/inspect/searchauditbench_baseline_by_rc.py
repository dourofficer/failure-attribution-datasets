#!/usr/bin/env python3
"""Join all-at-once baseline results with the index: accuracy per root cause / per model / critical-is-final, signed
offset, and whether the prediction lands on an echo-polluted step, a gold-bearing step, or the final answer.
Usage: python3 -I inspect/searchauditbench_baseline_by_rc.py [all_at_once_std_nogt] [other_name ...]"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_jsonl, md_table  # noqa: E402

D = os.path.join(RESULTS, 'searchauditbench')
idx = {r['id']: r for r in read_jsonl(os.path.join(D, 'index.jsonl'))}
echo = {r['id']: r for r in read_jsonl(os.path.join(D, 'echo.jsonl'))}


def report(name):
    rows = read_jsonl(os.path.join(D, name + '.jsonl'))
    print(f'\n## {name}  (n={len(rows)})')
    def acc(rs, k):
        return f"{sum(1 for x in rs if x[k])}/{len(rs)}"
    by = defaultdict(list)
    for x in rows:
        by[idx[x['id']]['rc']].append(x)
    print(md_table(['root cause', 'n', 'exact', 'in span', 'within3', 'later', 'earlier', 'pred=final', 'gold=final'],
                   [[rc, len(rs), acc(rs, 'step_exact'), acc(rs, 'step_in_set'), acc(rs, 'step_within_3'),
                     sum(1 for x in rs if x['step_dist'] is not None and x['step_dist'] > 0), sum(1 for x in rs if x['step_dist'] is not None and x['step_dist'] < 0),
                     sum(1 for x in rs if x['pred_step'] == idx[x['id']]['last_asst']), sum(1 for x in rs if idx[x['id']]['critical_is_final'])]
                    for rc, rs in sorted(by.items())] + [['ALL', len(rows), acc(rows, 'step_exact'), acc(rows, 'step_in_set'), acc(rows, 'step_within_3'),
                                                           sum(1 for x in rows if x['step_dist'] is not None and x['step_dist'] > 0), sum(1 for x in rows if x['step_dist'] is not None and x['step_dist'] < 0),
                                                           sum(1 for x in rows if x['pred_step'] == idx[x['id']]['last_asst']), sum(1 for x in rows if idx[x['id']]['critical_is_final'])]]))
    bym = defaultdict(list)
    for x in rows:
        bym[idx[x['id']]['model']].append(x)
    print(md_table(['model', 'n', 'n_asst med', 'exact', 'in span', 'within3'],
                   [[m, len(rs), sorted(idx[x['id']]['n_asst'] for x in rs)[len(rs) // 2], acc(rs, 'step_exact'), acc(rs, 'step_in_set'), acc(rs, 'step_within_3')] for m, rs in sorted(bym.items())]))
    fin = [x for x in rows if idx[x['id']]['critical_is_final']]
    nfin = [x for x in rows if not idx[x['id']]['critical_is_final']]
    print('critical=final: exact', acc(fin, 'step_exact'), '| critical mid: exact', acc(nfin, 'step_exact'), 'in span', acc(nfin, 'step_in_set'))
    dists = [x['step_dist'] for x in rows if x['step_dist'] is not None]
    print('signed offset (pred-gold) in messages: median', sorted(dists)[len(dists) // 2], 'hist', Counter(max(-20, min(20, d)) for d in dists))
    # relation of prediction to evidence steps
    on_gold = sum(1 for x in rows if x['pred_step'] is not None and idx[x['id']]['first_asst_after_gold'] == x['pred_step'])
    print('pred == first assistant step after first gold-bearing tool return:', on_gold, '(records with gold visible before k:', sum(1 for x in rows if idx[x['id']]['n_gold_tool_before'] > 0), ')')
    print('pred lands on an agent step whose preceding tool return is echo-polluted:', sum(1 for x in rows if x['pred_step'] is not None and (x['pred_step'] - 1) in echo[x['id']]['echo_steps']))
    print('agent_ok', acc(rows, 'agent_ok'), 'parse fail', sum(1 for x in rows if x['pred_step'] is None), 'fallback', sum(1 for x in rows if x.get('fallback')))
    return rows


if __name__ == '__main__':
    names = sys.argv[1:] or ['all_at_once_std_nogt']
    res = {n: report(n) for n in names}
    if len(names) == 2:
        a, b = (res[n] for n in names)
        bi = {x['id']: x for x in b}
        print('\nper-record change exact', names[0], '->', names[1], Counter((x['step_exact'], bi[x['id']]['step_exact']) for x in a if x['id'] in bi))
        byrc = defaultdict(Counter)
        for x in a:
            if x['id'] in bi:
                byrc[idx[x['id']]['rc']][(x['step_exact'], bi[x['id']]['step_exact'])] += 1
        for rc, c in byrc.items():
            print(' ', rc, dict(c))
