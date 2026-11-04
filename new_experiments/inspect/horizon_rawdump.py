#!/usr/bin/env python3
"""Dump raw result_2/result_3/result_5 judge records (full trajectory text + both judge verdicts) for close reading.
Usage: python3 -I inspect/horizon_rawdump.py id1,id2,... [--cap N]"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import DATA  # noqa
R = os.path.join(DATA, 'horizon', 'hf')
ids = sys.argv[1].split(',')
cap = int(sys.argv[sys.argv.index('--cap') + 1]) if '--cap' in sys.argv else 60000
d2 = {x['id']: x for x in json.load(open(os.path.join(R, 'result_2', 'classified_results.json')))}
d3 = {x['id']: x for x in json.load(open(os.path.join(R, 'result_3', 'classified_results.json')))}
d5 = {x['id']: x for x in json.load(open(os.path.join(R, 'result_5', 'classified_results.json')))}
od = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'g3_dumps')
os.makedirs(od, exist_ok=True)
for i in ids:
    x = d2.get(i) or d5.get(i)
    fn = os.path.join(od, 'horizon_raw__' + i + '.txt')
    with open(fn, 'w') as fh:
        fh.write(f"ID {i} domain={x['domain']} model={x['model']} run={x.get('run')} passed={x.get('passed')} score={x.get('score')}\n")
        for k, d in (('r2', d2), ('r3', d3), ('r5', d5)):
            if i in d:
                fh.write(f"[{k}] {d[i]['failure_type']} | step={d[i].get('failure_step_number')} | {d[i]['reason']}\n")
        if i in d5 and d5[i].get('steps'):
            fh.write('JUDGE WINDOW: ' + json.dumps([(w.get('label'), w.get('summary')) for w in d5[i]['steps']], ensure_ascii=False) + '\n')
        t = x['trajectory']
        fh.write('\n' + (t if len(t) <= cap else t[:int(cap*0.7)] + f'\n...[{len(t)-cap} cut]...\n' + t[-int(cap*0.3):]) + '\n')
    print('wrote', fn, len(x['trajectory']))
