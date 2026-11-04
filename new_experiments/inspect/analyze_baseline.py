#!/usr/bin/env python3
"""Categorise all-at-once baseline errors and dump reasoning excerpts.
Usage: python3 -I inspect/analyze_baseline.py <slug> [results file name, default all_at_once_std] [--dump N]
Prints: metrics by subset, signed distance histogram (pred - gold), categories, and writes
results/<slug>/<name>_analysis.md with reasoning excerpts of failures and successes.
"""
import argparse
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_jsonl, md_table  # noqa: E402


def cat(row):
    if row['pred_step'] is None:
        return 'parse_fail' if row.get('finish_reason') != 'length' else 'truncated'
    d = row['step_dist']
    if d == 0:
        return 'exact'
    if row.get('step_in_set'):
        return 'in_label_set'
    if d > 0:
        return 'later(+1..3)' if d <= 3 else 'later(>3)'
    return 'earlier(-1..3)' if d >= -3 else 'earlier(<-3)'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('name', nargs='?', default='all_at_once_std')
    ap.add_argument('--dump', type=int, default=8)
    a = ap.parse_args()
    path = os.path.join(RESULTS, a.slug, a.name + '.jsonl')
    rows = read_jsonl(path)
    by_sub = defaultdict(list)
    for r in rows:
        by_sub[r.get('subset')].append(r)
    keys = ['agent_ok', 'step_exact', 'step_within_3', 'step_in_set']
    tbl = []
    for sub, rs in list(by_sub.items()) + [('ALL', rows)]:
        tbl.append([sub, len(rs)] + [f"{100 * sum(1 for x in rs if x[k]) / max(1, len(rs)):.1f}" for k in keys])
    print(md_table(['subset', 'n'] + keys, tbl))
    cats = Counter(cat(r) for r in rows)
    print('\ncategories:', dict(cats))
    agent_only = sum(1 for r in rows if r['agent_ok'] and not r['step_exact'])
    print(f'agent right but step wrong: {agent_only}; step right but agent wrong: {sum(1 for r in rows if r["step_exact"] and not r["agent_ok"])}')
    # relation between n_steps and success
    bins = [(0, 10), (11, 30), (31, 1000)]
    print(md_table(['n_steps', 'n', 'step_exact%', 'within3%', 'agent%'],
                   [[f'{lo}-{hi}', len(rs := [r for r in rows if lo <= r['n_steps'] <= hi])] +
                    [f"{100 * sum(1 for x in rs if x[k]) / max(1, len(rs)):.1f}" for k in ('step_exact', 'step_within_3', 'agent_ok')]
                    for lo, hi in bins]))
    out = [f'# {a.slug} / {a.name}: error analysis\n']
    fails = [r for r in rows if not r['step_exact']][:a.dump]
    succ = [r for r in rows if r['step_exact']][:max(3, a.dump // 2)]
    for title, rs in (('Failures', fails), ('Successes', succ)):
        out.append(f'## {title}\n')
        for r in rs:
            out.append(f"### {r['id']} (n_steps={r['n_steps']}, gold={r['gold_step']} {r['gold_agent']}, pred={r['pred_step']} {r['pred_agent']}, cat={cat(r)})\n")
            out.append(f"gold reason: {r.get('gold_reason')}\n\npred reason: {(r.get('pred') or {}).get('reason')}\n")
            out.append('reasoning excerpt (tail):\n```\n' + (r.get('reasoning') or '')[-2500:] + '\n```\n')
    with open(os.path.join(RESULTS, a.slug, a.name + '_analysis.md'), 'w') as fh:
        fh.write('\n'.join(out))
    print('wrote', os.path.join(RESULTS, a.slug, a.name + '_analysis.md'))


if __name__ == '__main__':
    main()
