#!/usr/bin/env python3
"""Compact view of a TRAIL trace: step skeleton (idx, agent, kind, span_name, chars, first line), then each labelled
error with description/evidence and the labelled step's output (capped) + the next tool observation (capped).
Usage: python3 -I inspect/trail_view.py <id>[,<id>] [--cap 1200] [--skel-only]"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from loaders import load  # noqa: E402


def first(s, n=110):
    s = re.sub(r'\s+', ' ', s.strip())
    return s[:n]


def out_part(content):
    i = content.find('Output (')
    return content[i:] if i >= 0 else content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ids')
    ap.add_argument('--cap', type=int, default=1200)
    ap.add_argument('--skel-only', action='store_true')
    a = ap.parse_args()
    by = {r['id']: r for r in load('trail')}
    for i in a.ids.split(','):
        r = by[i]
        ex = r['labels']['extra']
        print(f"\n##### {i} n_steps={len(r['steps'])} primary={ex['primary_idx']} gt={str(r.get('ground_truth'))[:80]!r} final={str(r.get('final_output'))[:150]!r}")
        print('TASK:', first(r['task'] or '', 400))
        errs_at = {}
        for e in ex['errors']:
            errs_at.setdefault(e['idx'], []).append(e)
        for s in r['steps']:
            tag = ''.join(f" [{e['impact'][0]}:{e['category']}]" for e in errs_at.get(s['idx'], []))
            c = s['content']
            o = out_part(c) if s['role'] == 'agent' else c
            print(f"{s['idx']:3d} {s['agent'][:16]:16s} {s['meta']['kind'][:8]:8s} {str(s['meta']['span_name'])[:22]:22s} {len(c):7d} | {first(o)}{tag}")
        if a.skel_only:
            continue
        for k in sorted(errs_at):
            if k is None:
                continue
            print(f"\n=== labelled step {k} ({r['steps'][k]['agent']}, {r['steps'][k]['meta']['kind']})")
            for e in errs_at[k]:
                print(f"  * {e['impact']} {e['category']}: {e['description']}\n    evidence: {str(e['evidence'])[:400]!r}")
            c = r['steps'][k]['content']
            o = out_part(c) if r['steps'][k]['role'] == 'agent' else c
            print('  CONTENT:', o[:a.cap].replace('\n', '\n    '))
            for s in r['steps'][k + 1:k + 4]:
                if s['role'] == 'tool':
                    print(f"  NEXT TOOL [{s['idx']}]:", s['content'][:a.cap // 2].replace('\n', '\n    '))
                    break


if __name__ == '__main__':
    main()
