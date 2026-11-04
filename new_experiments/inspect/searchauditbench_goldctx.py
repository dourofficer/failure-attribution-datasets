#!/usr/bin/env python3
"""Show, for given ids, where the gold answer (or predicted answer) appears in tool returns, with context, plus the
labelled rationale. Usage: python3 -I inspect/searchauditbench_goldctx.py 1188,305 [--ctx 300]"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from loaders import load  # noqa: E402


def norm(s):
    return re.sub(r'[^0-9a-z一-鿿]+', ' ', str(s).lower()).strip()


def variants(g):
    g = str(g).strip()
    vs = {norm(g), norm(re.sub(r'\(.*?\)', '', g))}
    for part in re.split(r'\s*(?:/|\bor\b|;|,)\s*', g):
        if len(norm(part)) >= 3:
            vs.add(norm(part))
    return {v for v in vs if len(v) >= 3}


def main():
    ids = set(sys.argv[1].split(','))
    ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    for r in load('searchauditbench'):
        if r['id'] not in ids:
            continue
        ex = r['labels']['extra']
        k = ex['critical_idx']
        print(f"\n##### {r['id']} {r['meta']['backbone']} {r['subset']} cat={r['labels']['categories']} k={k} span={ex['span_start']}-{ex['span_end']} n={len(r['steps'])}")
        print('GOLD:', str(r['ground_truth'])[:200])
        print('PRED:', re.sub(r'\s+', ' ', str(r['final_output']))[:400])
        print('RATIONALE:', r['labels']['reason'])
        gv = variants(r['ground_truth'])
        for s in r['steps']:
            if s['role'] != 'tool':
                continue
            c = norm(s['content'])
            for v in gv:
                i = c.find(v)
                if i >= 0:
                    print(f"  [gold '{v}' in tool step {s['idx']}{' (before k)' if s['idx'] < k else ''}]: ...{c[max(0, i - ctx):i + len(v) + ctx]}...")
                    break
        print('--- critical step content:')
        print(r['steps'][k]['content'][:3000])


if __name__ == '__main__':
    main()
