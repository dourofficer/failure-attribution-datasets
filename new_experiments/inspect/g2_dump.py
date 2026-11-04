#!/usr/bin/env python3
"""G2 helper: dump one record (or a list) as readable text for close reading.
Usage: python3 -I inspect/g2_dump.py <slug> <id>[,<id>...] [--cap 3000] [--out results/<slug>/reads/] [--around K --window W]
Prints the task, labels, and every step (content capped per step; the labelled step and its +-2 neighbours uncapped
unless --cap-all). With --list, prints a one-line summary of every record instead (id, subset, n_steps, gold, agent)."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402


def trunc(t, cap):
    if cap is None or len(t) <= cap:
        return t
    return t[:int(cap * 0.75)] + f'\n   ... [{len(t) - cap} chars cut] ...\n' + t[-int(cap * 0.25):]


def dump(r, cap=3000, full_window=2, cap_all=False, max_gt=1500):
    g = error_step(r)
    L = r['labels']
    out = [f"=== {r['dataset']} / {r['id']}  subset={r['subset']}  n_steps={len(r['steps'])}  gold={g}  error_steps={L['error_steps'][:20]}  agent={L['error_agent']}  cats={L['categories']}",
           f"TASK: {trunc(r['task'] or '', 2500)}", f"GROUND TRUTH: {trunc(str(r.get('ground_truth')), max_gt)}",
           f"FINAL OUTPUT: {trunc(str(r.get('final_output')), 1500)}", f"REASON: {L['reason']}",
           f"EXTRA: {trunc(str({k: v for k, v in (L.get('extra') or {}).items() if k not in ('errors',)}), 1500)}", '']
    for s in r['steps']:
        near = g is not None and abs(s['idx'] - g) <= full_window
        c = s['content'] if (near and not cap_all) else trunc(s['content'], cap)
        mark = ' <<<< GOLD' if s['idx'] == g else (' <<< labelled' if s['idx'] in L['error_steps'] else '')
        out.append(f"--- [step {s['idx']}] {s['agent']} ({s['role']}) native={s['native_step']}{mark}\n{c}\n")
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('ids', nargs='?')
    ap.add_argument('--cap', type=int, default=3000)
    ap.add_argument('--cap-all', action='store_true')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--out', default=None)
    ap.add_argument('--kw', default=None, help='loader kwargs as k=v,k=v (e.g. systems=mem0)')
    a = ap.parse_args()
    kw = {}
    if a.kw:
        for kv in a.kw.split(','):
            k, v = kv.split('=')
            kw[k] = v.split('+') if '+' in v or k in ('systems', 'sources') else v
    recs = load(a.slug, **kw)
    if a.list:
        for r in recs:
            print(f"{r['id']}\t{r['subset']}\t{len(r['steps'])}\t{error_step(r)}\t{r['labels']['error_agent']}\t{(r['labels']['categories'] or [''])[0]}\t{str(r['labels']['reason'])[:100]!r}")
        return
    want = a.ids.split(',')
    by = {r['id']: r for r in recs}
    for i in want:
        r = by.get(i)
        if r is None:
            print('missing', i); continue
        txt = dump(r, cap=a.cap, cap_all=a.cap_all)
        if a.out:
            os.makedirs(a.out, exist_ok=True)
            p = os.path.join(a.out, i.replace('/', '__') + '.txt')
            open(p, 'w').write(txt)
            print('wrote', p, len(txt))
        else:
            print(txt)


if __name__ == '__main__':
    main()
