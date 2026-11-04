#!/usr/bin/env python3
"""AgentRx targeted statistics:
 1. root vs first failure: gap, what happened between (recovered events), orchestrator reaction to recovered failures
 2. visibility of failure events: error strings / tool errors at failure steps vs unflagged steps; at root vs non-root failures
 3. category of recovered (non-root, pre-root) failures vs root failures
 4. who is blamed vs who could have caught it (tau: assistant after a user message / policy); magentic: orchestrator ledger after a WebSurfer failure
 5. failure density after root (symptom cascade) vs before
Writes results/agentrx/stats.json"""
import json, os, re, sys, collections, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, write_json
from common.schema import error_step
from loaders import load

ERR = re.compile(r'(timeout|timed out|error|traceback|exception|unable to|could not|cannot|failed to|not found|no results|invalid)', re.I)
def norm_cat(c):
    c = (c or '').lower()
    for k in ('adherence', 'invention', 'invalid invocation', 'misinterpretation', 'misalignment', 'under', 'not supported', 'guardrail', 'system'):
        if k in c: return k
    return c[:20]

recs = load('agentrx')
rows = []
cat_root = collections.Counter(); cat_pre = collections.Counter(); cat_post = collections.Counter()
err_at = collections.defaultdict(list)
for r in recs:
    n = len(r['steps']); root = error_step(r); fails = r['labels']['extra']['failures']
    fidx = sorted({int(f['step_number']) - 1 for f in fails if 0 <= int(f['step_number']) - 1 < n})
    pre = [k for k in fidx if k < root]; post = [k for k in fidx if k > root]
    for f in fails:
        k = int(f['step_number']) - 1
        c = norm_cat(f['failure_category'])
        if k == root: cat_root[c] += 1
        elif k < root: cat_pre[c] += 1
        else: cat_post[c] += 1
    for s in r['steps']:
        if s['role'] in ('agent',):
            key = 'root' if s['idx'] == root else ('pre_fail' if s['idx'] in pre else ('post_fail' if s['idx'] in post else 'unflagged'))
            err_at[(r['subset'], key)].append(bool(ERR.search(s['content'][:4000])))
    # next step after each pre-root failure: who speaks and does it mention a problem
    react = []
    for k in pre:
        nxt = r['steps'][k + 1] if k + 1 < n else None
        react.append({'fail_step': k, 'fail_agent': r['steps'][k]['agent'], 'next_agent': nxt['agent'] if nxt else None,
                      'next_mentions_problem': bool(nxt and ERR.search(nxt['content'][:3000])),
                      'ledger_flags': bool(nxt and re.search(r'is_progress_being_made"\s*:\s*\{[^}]*"answer"\s*:\s*false', nxt['content'])) or bool(nxt and re.search(r'is_in_loop"\s*:\s*\{[^}]*"answer"\s*:\s*true', nxt['content'])),
                      'next_repeats_instruction': bool(nxt and k + 3 < n and r['steps'][k + 2]['content'][:80] == r['steps'][k - 1]['content'][:80] if k >= 1 else False)})
    rows.append({'id': r['id'], 'subset': r['subset'], 'n': n, 'root': root, 'root_agent': r['labels']['error_agent'], 'root_cat': r['labels']['categories'][0] if r['labels']['categories'] else None,
                 'n_fail': len(fidx), 'n_pre': len(pre), 'n_post': len(post), 'first': fidx[0] if fidx else None, 'gap_root_first': root - fidx[0] if fidx else None,
                 'root_is_last_fail': bool(fidx) and fidx[-1] == root, 'root_rel': root / max(1, n - 1), 'react': react,
                 'steps_before_root': root, 'steps_after_root': n - root - 1, 'root_err': bool(ERR.search(r['steps'][root]['content'][:4000]))})
for sub in ('tau_retail', 'magentic_one'):
    rs = [x for x in rows if x['subset'] == sub]
    print(f'\n## {sub} n={len(rs)}')
    nr = [x for x in rs if x['n_pre'] > 0]
    print('root != first failure:', len(nr), '; gap root-first (steps) median', statistics.median([x['gap_root_first'] for x in nr]) if nr else None, 'max', max([x['gap_root_first'] for x in nr], default=None))
    print('root is the LAST annotated failure:', sum(x['root_is_last_fail'] for x in rs), '; root is the only failure:', sum(1 for x in rs if x['n_fail'] == 1))
    print('failure density before root: %.3f/step; after root: %.3f/step' % (sum(x['n_pre'] for x in rs) / max(1, sum(x['steps_before_root'] for x in rs)), sum(x['n_post'] for x in rs) / max(1, sum(x['steps_after_root'] for x in rs))))
    print('root step contains error string:', sum(x['root_err'] for x in rs))
    for key in ('root', 'pre_fail', 'post_fail', 'unflagged'):
        v = err_at[(sub, key)]
        if v: print(f'  error-string rate at {key}: {statistics.mean(v):.2f} (n={len(v)})')
    rc = [a for x in rs for a in x['react']]
    if rc:
        print('reaction to pre-root (recovered) failures: next speaker', collections.Counter(a['next_agent'] for a in rc).most_common(5), '; next step mentions problem', sum(a['next_mentions_problem'] for a in rc), '/', len(rc), '; ledger flags no-progress', sum(a['ledger_flags'] for a in rc))
    print('root category:', collections.Counter(norm_cat(x['root_cat']) for x in rs).most_common())
print('\n## category by role of failure event (all 73):')
print(md_table(['category', 'root', 'pre-root (recovered)', 'post-root (symptom)'], [[c, cat_root[c], cat_pre[c], cat_post[c]] for c in sorted(set(cat_root) | set(cat_pre) | set(cat_post), key=lambda c: -cat_root[c])]))
print('\n## agent blamed at root vs at pre-root failures')
print('root agents:', collections.Counter((x['subset'], x['root_agent']) for x in rows).most_common())
print('pre-root failure agents:', collections.Counter((x['subset'], a['fail_agent']) for x in rows for a in x['react']).most_common())
write_json(os.path.join(RESULTS, 'agentrx', 'stats.json'), rows)
