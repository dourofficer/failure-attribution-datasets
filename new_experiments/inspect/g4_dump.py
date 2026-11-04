"""Dump records of a slug as readable text for close reading: python3 -I inspect/g4_dump.py <slug> id1,id2,... [--out file] [--cap N]
Marks the labelled step(s) with >>> and (who_and_when_pro) injected / replayed / live flags."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.schema import error_step  # noqa: E402


def dump(rec, cap=3000, fh=sys.stdout):
    g = error_step(rec)
    es = set(rec['labels']['error_steps'])
    print(f"\n{'=' * 100}\nID {rec['id']}  subset={rec['subset']}  n_steps={len(rec['steps'])}  label={rec['labels']['error_steps']} agent={rec['labels']['error_agent']} cats={rec['labels']['categories']}", file=fh)
    print(f"meta: { {k: v for k, v in rec['meta'].items() if k in ('framework', 'benchmark', 'backbone', 'domain', 'task_type')} } extra: { {k: v for k, v in rec['labels']['extra'].items() if k in ('mode', 'error_source', 'faulty_agents', 'injected_agents', 'mistake_agent_raw')} }", file=fh)
    print(f"TASK: {rec['task'][:1500]}", file=fh)
    print(f"GT: {str(rec['ground_truth'])[:300]}", file=fh)
    print(f"REASON: {rec['labels'].get('reason')}", file=fh)
    for s in rec['steps']:
        m = s['meta']
        fl = ''.join([' [INJ]' if m.get('injected') else '', ' [REPLAYED]' if m.get('replayed') else '', ' [LIVE]' if m.get('live') else '',
                      ' [FINAL]' if m.get('final_answer') else '', ' [is_injected]' if m.get('is_injected') else ''])
        mark = '>>> ' if s['idx'] in es else '    '
        c = s['content']
        if len(c) > cap:
            c = c[:int(cap * 0.7)] + f'\n ... [{len(c) - cap} chars cut] ...\n' + c[-int(cap * 0.3):]
        print(f"\n{mark}[step {s['idx']}] {s['agent']} ({s['role']}) native={s['native_step']}{fl}\n{c}", file=fh)
    print(f"\nFINAL OUTPUT: {str(rec['final_output'])[:800]}", file=fh)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('ids')
    ap.add_argument('--out', default=None)
    ap.add_argument('--cap', type=int, default=3000)
    a = ap.parse_args()
    if a.slug == 'who_and_when_pro':
        from g4_common import load_flagged
        recs = load_flagged()
    else:
        from loaders import load
        recs = load(a.slug)
    want = a.ids.split(',')
    by = {r['id']: r for r in recs}
    fh = open(a.out, 'w') if a.out else sys.stdout
    for i in want:
        if i in by:
            dump(by[i], cap=a.cap, fh=fh)
        else:
            print('MISSING', i, file=fh)
