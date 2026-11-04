#!/usr/bin/env python3
"""MemTrace: where does the gold evidence get lost? For every record with the faulty op in the slice, compute for each step
the overlap between the evidence's content words and the step's Inputs / Outputs sections, find the first 'loss' step
(evidence present in inputs, absent in outputs, or an update/extraction step after which no later step carries the
evidence) and compare with the gold op. Also: is the gold op the last step whose inputs contain the query (retrieval ops)?
Writes results/memtrace/evidence_loss.json and prints a summary."""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, write_json  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402

STOP = set('the a an and or of to in on at for with is are was were be been by it this that i my me you your he she they we his her their its as from about have has had do did not no so if but up out then than when what which who how last week month year ago says role user assistant timestamp speaker name content metadata below this message'.split())


def words(t):
    return {w for w in re.findall(r'[a-z][a-z0-9\-]{2,}', (t or '').lower()) if w not in STOP}


def split_io(content):
    i = content.find('Inputs:')
    o = content.find('Outputs:')
    if i < 0 or o < 0:
        return content, ''
    return content[i:o], content[o:]


def main():
    systems = sys.argv[1].split(',') if len(sys.argv) > 1 else ['mem0', 'rag', 'evermemos', 'long_context']
    rows = []
    for sp in systems:
        for r in load('memtrace', systems=[sp]):
            g = error_step(r)
            ev = r['labels']['extra'].get('source_evidence') or []
            evw = set()
            for e in (ev if isinstance(ev, list) else [ev]):
                try:
                    d = json.loads(e) if isinstance(e, str) else e
                    evw |= words(d.get('content', '') if isinstance(d, dict) else str(d))
                except Exception:  # noqa
                    evw |= words(str(e))
            if not evw:
                continue
            per = []
            for s in r['steps']:
                ins, outs = split_io(s['content'])
                wi, wo = words(ins), words(outs)
                per.append({'idx': s['idx'], 'cat': s['agent'], 'op': s['meta']['op_name'],
                            'in': len(evw & wi) / len(evw), 'out': len(evw & wo) / len(evw),
                            'has_query': (r['task'] or '')[:60].lower() in ins.lower()})
            # evidence carriers: steps whose inputs or outputs contain >=50% of evidence words
            thr = 0.5
            carriers_out = [p['idx'] for p in per if p['out'] >= thr]
            carriers_in = [p['idx'] for p in per if p['in'] >= thr]
            last_out = carriers_out[-1] if carriers_out else None
            last_in = carriers_in[-1] if carriers_in else None
            # loss step: first step with in>=thr and out<thr/2 after which no later step has out>=thr
            loss = None
            for p in per:
                if p['in'] >= thr and p['out'] < thr / 2 and not any(q['out'] >= thr for q in per if q['idx'] > p['idx']):
                    loss = p['idx']
                    break
            query_steps = [p['idx'] for p in per if p['has_query']]
            rows.append({'id': r['id'], 'system': sp, 'type': r['labels']['categories'][0], 'n': len(per), 'gold': g, 'in_slice': g is not None,
                         'gold_cat': r['labels']['error_agent'], 'n_ev_words': len(evw), 'last_out': last_out, 'last_in': last_in, 'loss': loss,
                         'ev_ever_in_output': bool(carriers_out), 'ev_ever_in_input': bool(carriers_in), 'query_steps': query_steps[:5],
                         'n_query_steps': len(query_steps), 'gold_in': per[g]['in'] if g is not None else None, 'gold_out': per[g]['out'] if g is not None else None,
                         'gold_has_query': per[g]['has_query'] if g is not None else None})
    write_json(os.path.join(RESULTS, 'memtrace', 'evidence_loss.json'), rows)
    print(len(rows), 'records with evidence')
    for sp in systems:
        rs = [x for x in rows if x['system'] == sp]
        ins = [x for x in rs if x['in_slice']]
        print(f'\n## {sp}: n={len(rs)} in_slice={len(ins)}')
        print(' evidence words ever in some step output (>=50%):', sum(x['ev_ever_in_output'] for x in rs), '| ever in input:', sum(x['ev_ever_in_input'] for x in rs))
        print(' gold == loss step:', sum(1 for x in ins if x['loss'] == x['gold']), '| gold == last_in:', sum(1 for x in ins if x['last_in'] == x['gold']),
              '| gold == last_out+1:', sum(1 for x in ins if x['last_out'] is not None and x['last_out'] + 1 == x['gold']))
        print(' gold step has the query in its inputs:', sum(1 for x in ins if x['gold_has_query']), '| n steps with query (median):',
              sorted(x['n_query_steps'] for x in ins)[len(ins) // 2] if ins else None)
        print(' by type:', Counter((x['type'], x['loss'] == x['gold']) for x in ins))
        print(' out-of-slice: evidence in some output?', Counter((x['type'], x['ev_ever_in_output']) for x in rs if not x['in_slice']))


if __name__ == '__main__':
    main()
