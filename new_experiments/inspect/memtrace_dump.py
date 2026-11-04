#!/usr/bin/env python3
"""MemTrace spot-check: per system, list all records (id, n_steps, gold, rel pos, error type, op_in_slice) and dump a few
records (one per error type + one out-of-slice) with short step rendering. Writes results/memtrace/list.tsv and reads/."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402

OUT = os.path.join(RESULTS, 'memtrace')
os.makedirs(os.path.join(OUT, 'reads'), exist_ok=True)
systems = sys.argv[1].split(',') if len(sys.argv) > 1 else ['mem0', 'rag', 'evermemos', 'long_context']
lst = open(os.path.join(OUT, 'list.tsv'), 'a')
for sp in systems:
    recs = load('memtrace', systems=[sp])
    done = set()
    for r in recs:
        g = error_step(r)
        n = len(r['steps'])
        et = r['labels']['categories'][0]
        lst.write('\t'.join(map(str, [r['id'], sp, n, g, round(g / max(1, n - 1), 3) if g is not None else None, et, r['meta']['op_in_slice'],
                                      r['labels']['extra'].get('final_op_name'), r['labels']['extra'].get('final_op_global_pos'),
                                      r['meta']['graph_size']['operations'], (r['labels']['reason'] or '')[:160].replace('\n', ' ')])) + '\n')
        key = (et, r['meta']['op_in_slice'])
        if key in done or n > 400:
            continue
        done.add(key)
        # dump: task, labels, all steps with content capped at 500 chars; gold +-1 capped at 4000
        lines = [f"=== {r['id']} system={sp} n_steps={n} gold={g} type={et} op_in_slice={r['meta']['op_in_slice']} final_op={r['labels']['extra'].get('final_op_name')}",
                 f"QUERY: {r['task']}", f"GOLD ANSWERS: {r['ground_truth']}", f"PREDICTION: {r['final_output']}", f"REASON: {r['labels']['reason']}",
                 f"EVIDENCE: {str(r['labels']['extra'].get('source_evidence'))[:1500]}", '']
        for s in r['steps']:
            near = g is not None and abs(s['idx'] - g) <= 1
            cap = 4000 if near else 500
            c = s['content'] if len(s['content']) <= cap else s['content'][:cap] + f' ...[{len(s["content"]) - cap} more]'
            lines.append(f"--- [step {s['idx']}] {s['agent']} op={s['meta']['op_name']} session={s['meta']['session_id']}{' <<<< GOLD' if s['idx'] == g else ''}\n{c}\n")
        p = os.path.join(OUT, 'reads', r['id'].replace('/', '__').replace('::', '__') + '.txt')
        open(p, 'w').write('\n'.join(lines))
        print('wrote', p, file=sys.stderr)
    lst.flush()
