#!/usr/bin/env python3
"""TRAIL targeted statistics: (1) outcome (final_output vs GAIA true answer), (2) earliest error impact vs primary HIGH,
(3) evidence visibility (is the annotator's 'evidence' text a substring of the labelled step content?),
(4) consequence in next TOOL span after a primary LLM-span error, (5) error categories by position/impact, (6) search-agent use.
Writes results/trail/stats.json and prints tables."""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, write_json  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip().lower()


def answer_match(fo, gt):
    if fo is None or gt is None:
        return None
    a, b = norm(fo), norm(gt)
    if not a or not b:
        return None
    if a == b or b in a:
        return True
    # numeric
    na = re.findall(r'-?\d+(?:[.,]\d+)?', a); nb = re.findall(r'-?\d+(?:[.,]\d+)?', b)
    if nb and na and nb == na:
        return True
    return False


def main():
    recs = load('trail')
    rows = []
    for r in recs:
        ex = r['labels']['extra']
        errs = [e for e in ex['errors'] if e['idx'] is not None]
        steps = r['steps']
        p = ex['primary_idx']
        earliest = min((e['idx'] for e in errs), default=None)
        earliest_errs = [e for e in errs if e['idx'] == earliest]
        prim_errs = [e for e in errs if e['idx'] == p]
        # evidence visibility
        vis = []
        for e in errs:
            ev = norm(e.get('evidence'))
            c = norm(steps[e['idx']]['content'])
            if not ev:
                vis.append(None); continue
            frag = ev[:80]
            vis.append(frag in c or (len(ev) > 30 and ev[-80:] in c))
        # consequence in the next tool span after primary
        nxt_tool = None
        if p is not None:
            for s in steps[p + 1:p + 4]:
                if s['role'] == 'tool':
                    nxt_tool = s; break
        cons = None
        if nxt_tool is not None:
            c = nxt_tool['content'].lower()
            cons = any(k in c for k in ('error', 'exception', 'traceback', 'not found', 'no results', 'failed', 'invalid', 'could not'))
        used_search = any(s['agent'] == 'ToolCallingAgent' for s in steps)
        am = answer_match(r.get('final_output'), r.get('ground_truth'))
        rows.append({'id': r['id'], 'subset': r['subset'], 'n_steps': len(steps), 'n_agent_steps': sum(1 for s in steps if s['role'] == 'agent'),
                     'n_errors': len(errs), 'n_error_spans': len({e['idx'] for e in errs}), 'impacts': Counter(e['impact'] for e in errs),
                     'primary': p, 'primary_impact': [e['impact'] for e in prim_errs], 'primary_cats': [e['category'] for e in prim_errs],
                     'primary_kind': steps[p]['meta']['kind'] if p is not None else None,
                     'earliest': earliest, 'earliest_impacts': [e['impact'] for e in earliest_errs], 'earliest_cats': [e['category'] for e in earliest_errs],
                     'n_errs_before_primary': sum(1 for e in errs if e['idx'] < p) if p is not None else 0,
                     'n_HIGH': sum(1 for e in errs if e['impact'] == 'HIGH'),
                     'evidence_visible': vis, 'next_tool_consequence': cons, 'used_search_agent': used_search,
                     'answer_match': am, 'final_output': (r.get('final_output') or '')[:200], 'gt': (r.get('ground_truth') or '')[:200],
                     'overall_score': (ex.get('scores') or {}).get('overall') if isinstance(ex.get('scores'), dict) else ex.get('scores'),
                     'rel_primary': p / max(1, len(steps) - 1) if p is not None else None,
                     'errs': [{'idx': e['idx'], 'impact': e['impact'], 'cat': e['category'], 'kind': e['kind'], 'agent': e['agent']} for e in errs]})
    write_json(os.path.join(RESULTS, 'trail', 'stats.json'), rows)
    n = len(rows)
    print('records', n, Counter(r['subset'] for r in rows))
    print('no errors:', [r['id'] for r in rows if r['n_errors'] == 0])
    print('answer_match:', Counter(r['answer_match'] for r in rows), ' per subset', Counter((r['subset'], r['answer_match']) for r in rows))
    print('correct-ending traces:', [(r['id'], r['n_errors'], dict(r['impacts'])) for r in rows if r['answer_match']])
    print('\nearliest error impact vs primary:')
    t = Counter()
    for r in rows:
        if r['primary'] is None: continue
        if r['earliest'] == r['primary']:
            t['primary is earliest span'] += 1
        else:
            t['primary later than earliest; earliest impacts=' + '/'.join(sorted(set(r['earliest_impacts'])))] += 1
    for k, v in t.most_common(): print(f'  {k}: {v}')
    print('n errs before primary: ', Counter(min(r['n_errs_before_primary'], 5) for r in rows if r['primary'] is not None))
    print('n HIGH per trace:', Counter(min(r['n_HIGH'], 6) for r in rows))
    print('traces with no HIGH:', sum(1 for r in rows if r['n_HIGH'] == 0 and r['n_errors'] > 0))
    allv = [v for r in rows for v in r['evidence_visible']]
    print('evidence visible in labelled step content:', Counter(allv))
    byk = Counter()
    for r in rows:
        for e, v in zip(r['errs'], r['evidence_visible']):
            byk[(e['kind'], v)] += 1
    print(' by span kind:', dict(byk))
    print('primary span kind:', Counter(r['primary_kind'] for r in rows))
    print('next tool span after primary shows error-ish text:', Counter(r['next_tool_consequence'] for r in rows))
    print('used search agent:', Counter((r['subset'], r['used_search_agent']) for r in rows))
    # category by impact
    ci = defaultdict(Counter)
    for r in rows:
        for e in r['errs']:
            ci[e['cat']][e['impact']] += 1
    print(md_table(['category', 'HIGH', 'MEDIUM', 'LOW', 'total'], [[c, d['HIGH'], d['MEDIUM'], d['LOW'], sum(d.values())] for c, d in sorted(ci.items(), key=lambda x: -sum(x[1].values()))]))
    # category of primary
    print('primary categories:', Counter(c for r in rows for c in r['primary_cats']).most_common(12))
    print('earliest (non-primary) categories:', Counter(c for r in rows if r['earliest'] != r['primary'] for c in r['earliest_cats']).most_common(12))


if __name__ == '__main__':
    main()
