#!/usr/bin/env python3
"""MemTrace: (1) position of the gold op among ops of the same op_name in the slice (is it the last / only one?), (2) how many
ops of the gold's op_name exist in the slice, (3) for evermemos (not dumped by memtrace_dump.py because slices are > 400 steps)
write a condensed read of two records: gold op +-2 and an op_name histogram. Writes results/memtrace/opstats.json."""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, write_json  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402

OUT = os.path.join(RESULTS, 'memtrace')
rows = []
systems = sys.argv[1].split(',') if len(sys.argv) > 1 else ['mem0', 'rag', 'evermemos', 'long_context']
dumped = 0
for sp in systems:
    for r in load('memtrace', systems=[sp]):
        g = error_step(r)
        names = [s['meta']['op_name'] for s in r['steps']]
        hist = Counter(names)
        row = {'id': r['id'], 'system': sp, 'type': r['labels']['categories'][0], 'n': len(names), 'gold': g, 'n_opnames': len(hist),
               'top_ops': hist.most_common(6)}
        if g is not None:
            same = [i for i, n in enumerate(names) if n == names[g]]
            row.update({'gold_op': names[g], 'n_same_op': len(same), 'gold_rank_among_same': same.index(g), 'gold_is_last_same': same[-1] == g,
                        'gold_is_only_same': len(same) == 1, 'gold_session': r['steps'][g]['meta']['session_id'],
                        'n_steps_after': len(names) - 1 - g, 'ops_after': Counter(names[g + 1:]).most_common(4)})
        rows.append(row)
        if sp == 'evermemos' and g is not None and dumped < 2 and r['labels']['categories'][0] in ('RetrievalError', 'ResponseError'):
            dumped += 1
            lines = [f"=== {r['id']} n={len(names)} gold={g} type={r['labels']['categories'][0]} gold_op={names[g]}",
                     f"QUERY: {r['task']}", f"GOLD: {r['ground_truth']}", f"PRED: {str(r['final_output'])[:800]}", f"REASON: {r['labels']['reason']}",
                     f"EVIDENCE: {str(r['labels']['extra'].get('source_evidence'))[:1200]}", f"op histogram: {hist.most_common(15)}", '']
            for s in r['steps'][max(0, g - 3):g + 3]:
                c = s['content'][:3500] + (' ...' if len(s['content']) > 3500 else '')
                lines.append(f"--- [step {s['idx']}] {s['agent']} op={s['meta']['op_name']}{' <<<< GOLD' if s['idx'] == g else ''}\n{c}\n")
            open(os.path.join(OUT, 'reads', r['id'].replace('/', '__').replace('::', '__') + '.txt'), 'w').write('\n'.join(lines))
write_json(os.path.join(OUT, 'opstats.json'), rows)
for sp in systems:
    rs = [x for x in rows if x['system'] == sp and x['gold'] is not None]
    print(f"## {sp}: n={len(rs)} median slice {sorted(x['n'] for x in rs)[len(rs)//2]} distinct op names median {sorted(x['n_opnames'] for x in rs)[len(rs)//2]}")
    print('  gold op names:', Counter(x['gold_op'] for x in rs).most_common())
    print('  gold is the ONLY op of its name:', sum(x['gold_is_only_same'] for x in rs), '| gold is the LAST op of its name:', sum(x['gold_is_last_same'] for x in rs),
          '| median #same-name ops:', sorted(x['n_same_op'] for x in rs)[len(rs)//2])
    print('  steps after gold median:', sorted(x['n_steps_after'] for x in rs)[len(rs)//2], '| by type:', Counter((x['type'], x['gold_is_last_same']) for x in rs))
