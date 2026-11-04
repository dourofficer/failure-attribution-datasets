#!/usr/bin/env python3
"""Dump records of a dataset to plain text for close reading (G3 agent helper).
Usage: python3 -I inspect/g3_dump.py <slug> [--ids a,b] [--n N] [--seed S] [--subset S] [--cap CHARS] [--out dir] [--list]
--list prints one line per record (id, subset, n_steps, gold, categories) and exits.
"""
import argparse, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.schema import error_step  # noqa
from loaders import load  # noqa

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('slug'); ap.add_argument('--ids'); ap.add_argument('--n', type=int, default=5)
    ap.add_argument('--seed', type=int, default=0); ap.add_argument('--subset'); ap.add_argument('--cap', type=int, default=3000)
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'g3_dumps')); ap.add_argument('--list', action='store_true')
    ap.add_argument('--grep')
    a = ap.parse_args()
    recs = load(a.slug)
    if a.subset: recs = [r for r in recs if r['subset'] == a.subset]
    if a.list:
        for r in recs:
            g = error_step(r); n = len(r['steps']); na = sum(1 for s in r['steps'] if s['role'] == 'agent')
            print(f"{r['id']}\t{r['subset']}\tn={n}\tagent={na}\tgold={g}\trel={(g / max(1, n - 1)):.2f}" if g is not None else f"{r['id']}\t{r['subset']}\tn={n}\tagent={na}\tgold=None",
                  '\t', '|'.join(r['labels']['categories']), '\t', r['meta'].get('backbone'), '\t', r['outcome'])
        return
    if a.ids:
        want = a.ids.split(','); recs = [r for r in recs if r['id'] in want]
    else:
        random.Random(a.seed).shuffle(recs); recs = recs[:a.n]
    os.makedirs(a.out, exist_ok=True)
    for r in recs:
        g = error_step(r)
        fn = os.path.join(a.out, a.slug + '__' + r['id'].replace('/', '__') + '.txt')
        with open(fn, 'w') as fh:
            fh.write(f"ID {r['id']}  subset={r['subset']} backbone={r['meta'].get('backbone')} outcome={r['outcome']} n_steps={len(r['steps'])}\n")
            fh.write(f"GOLD step={g} agent={r['labels']['error_agent']} cats={r['labels']['categories']}\nREASON: {r['labels']['reason']}\n")
            ex = {k: v for k, v in (r['labels'].get('extra') or {}).items() if k not in ('step_annotations',)}
            fh.write(f"EXTRA: {str(ex)[:1500]}\n")
            fh.write(f"TASK: {r['task'][:3000]}\nGROUND_TRUTH: {str(r['ground_truth'])[:500]}\nFINAL: {str(r['final_output'])[:1500]}\n\n")
            for s in r['steps']:
                mark = ' <<<<<<<<<< GOLD' if s['idx'] == g else ''
                c = s['content']
                if len(c) > a.cap: c = c[:int(a.cap * 0.7)] + f'\n...[{len(c) - a.cap} chars cut]...\n' + c[-int(a.cap * 0.3):]
                fh.write(f"===== [step {s['idx']}] {s['agent']} ({s['role']}) native={s['native_step']}{mark}\n{c}\n\n")
        print('wrote', fn, 'steps', len(r['steps']), 'gold', g)

if __name__ == '__main__':
    main()
