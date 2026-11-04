#!/usr/bin/env python3
"""MP-Bench targeted statistics:
 1. annotator duplication: how often two annotators' flag sets / reason texts are identical (ann1 vs ann3 etc.)
 2. what kind of step gets 1 / 2 / 3 votes (step type, agent, error strings, position, 'Next speaker' meta steps)
 3. 1-vote flags: before or after the earliest majority step (symptom vs alternative cause)
 4. earliest majority step: how often it is a content-free step (Next speaker / Stalled / instruction duplicate)
 5. category agreement on multi-vote steps
Writes results/mp_bench/stats.json"""
import json, os, re, sys, collections, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, write_json
from common.schema import error_step
from loaders import load

ERR = re.compile(r'(timeout|timed out|error|traceback|exception|unable to|could not|cannot|failed to|not found|no results)', re.I)

def steptype(s):
    a = s['meta'].get('base_agent', s['agent']); c = s['content']
    if a in ('Orchestrator', 'MagenticOneOrchestrator'):
        if c.startswith('Stalled'): return 'Orch:stalled'
        if c.startswith('Updated Ledger'): return 'Orch:ledger'
        if c.startswith('Next speaker'): return 'Orch:next_speaker'
        if c.startswith('Initial plan') or c.startswith('New plan'): return 'Orch:plan'
        if s['agent'].startswith('Orchestrator (->'): return 'Orch:instruction'
        if 'FINAL ANSWER' in c: return 'Orch:final'
        return 'Orch:other'
    if a == 'Computer_terminal': return 'terminal'
    if a in ('WebSurfer', 'Websurfer', 'FileSurfer', 'Assistant', 'Coder', 'ComputerTerminal'): return a
    if a.endswith('_Expert') or 'Expert' in a: return 'Expert'
    return a

recs = load('mp_bench')
# 1. duplication
dup = collections.Counter(); dup_logs = collections.defaultdict(list)
for r in recs:
    pa = r['labels']['extra']['per_annotator']
    ids = sorted(pa)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            A = {(x['step'], (x['reason'] or '').strip()) for x in pa[ids[i]]}; B = {(x['step'], (x['reason'] or '').strip()) for x in pa[ids[j]]}
            sA = {x['step'] for x in pa[ids[i]]}; sB = {x['step'] for x in pa[ids[j]]}
            key = (ids[i], ids[j])
            if A and A == B: dup[(key, 'identical_steps_and_reasons')] += 1; dup_logs[key].append(r['id'])
            elif sA and sA == sB: dup[(key, 'identical_steps_only')] += 1
            else: dup[(key, 'different')] += 1
print('## annotator pair agreement over', len(recs), 'logs')
for k, v in sorted(dup.items()): print(v, k)
for sub in ('manual', 'automatic'):
    n = sum(1 for r in recs if r['subset'] == sub)
    d13 = sum(1 for r in recs if r['subset'] == sub and r['id'] in dup_logs[('1', '3')])
    print(f'  {sub}: ann1==ann3 verbatim in {d13}/{n}')
# identical reasons but different steps? check reason text overlap between 1 and 3
same_text = 0; tot = 0
for r in recs:
    pa = r['labels']['extra']['per_annotator']
    if '1' in pa and '3' in pa and pa['1'] and pa['3']:
        tot += 1
        t1 = {(x['reason'] or '').strip() for x in pa['1']}; t3 = {(x['reason'] or '').strip() for x in pa['3']}
        if t1 & t3: same_text += 1
print('logs where ann1 and ann3 share at least one verbatim reason:', same_text, '/', tot)

# 2-5
rows = []
by_votes = collections.defaultdict(collections.Counter)
pos_by_votes = collections.defaultdict(list)
err_by_votes = collections.defaultdict(list)
one_vote_rel = collections.Counter()
prim_type = collections.Counter()
cat_agree = collections.Counter()
for r in recs:
    votes = r['labels']['votes'] or {}
    n = len(r['steps']); prim = r['labels']['extra']['earliest_majority_step']
    pa = r['labels']['extra']['per_annotator']
    for k, v in votes.items():
        s = r['steps'][k]
        by_votes[(r['subset'], v)][steptype(s)] += 1
        pos_by_votes[(r['subset'], v)].append(k / max(1, n - 1))
        err_by_votes[(r['subset'], v)].append(bool(ERR.search(s['content'][:4000])))
        if v == 1 and prim is not None:
            one_vote_rel[(r['subset'], 'before_majority' if k < prim else 'after_majority')] += 1
        if v >= 2:
            cats = [x['category'] for aid in pa for x in pa[aid] if x['step'] == k]
            cat_agree[(r['subset'], 'same_cat' if len(set(cats)) == 1 else 'diff_cat')] += 1
    if prim is not None:
        prim_type[(r['subset'], steptype(r['steps'][prim]))] += 1
    # unflagged steps baseline
    for s in r['steps']:
        if s['idx'] not in votes and s['role'] == 'agent':
            by_votes[(r['subset'], 0)][steptype(s)] += 1
            err_by_votes[(r['subset'], 0)].append(bool(ERR.search(s['content'][:4000])))
print('\n## step type by vote count (0 = agent steps never flagged)')
for key in sorted(by_votes):
    tot = sum(by_votes[key].values())
    print(key, tot, {k: f'{100*v/tot:.0f}%' for k, v in by_votes[key].most_common(7)})
print('\n## relative position (median) and error-string rate by vote count')
for key in sorted(pos_by_votes):
    print(key, 'median rel pos %.2f' % statistics.median(pos_by_votes[key]), 'err-string rate %.2f' % statistics.mean(err_by_votes[key]), 'n', len(pos_by_votes[key]))
for key in sorted(err_by_votes):
    if key[1] == 0: print(key, 'unflagged agent steps err-string rate %.2f' % statistics.mean(err_by_votes[key]), 'n', len(err_by_votes[key]))
print('\n## 1-vote flags relative to earliest majority step:', dict(one_vote_rel))
print('\n## earliest-majority (primary) step type:', sorted(prim_type.items(), key=lambda kv: -kv[1]))
print('\n## category agreement on >=2-vote steps:', dict(cat_agree))
# majority after excluding ann3 duplicates: recompute votes counting ann3 only when it differs from ann1
print('\n## effect of de-duplicating ann1/ann3 (count ann3 only if its (step, reason) differs from ann1)')
chg = collections.Counter()
for r in recs:
    pa = r['labels']['extra']['per_annotator']
    v = collections.defaultdict(set)
    a1 = {(x['step'], (x['reason'] or '').strip()) for x in pa.get('1', [])}
    for aid, lst in pa.items():
        for x in lst:
            if aid == '3' and (x['step'], (x['reason'] or '').strip()) in a1: continue
            v[x['step']].add(aid)
    maj = sorted(k for k, s in v.items() if len(s) >= 2)
    prim_old = r['labels']['extra']['earliest_majority_step']; prim_new = maj[0] if maj else None
    chg[(r['subset'], 'no_majority_left' if prim_new is None else ('same' if prim_new == prim_old else 'changed'))] += 1
    r['_prim_dedup'] = prim_new
print(dict(chg))
write_json(os.path.join(RESULTS, 'mp_bench', 'stats.json'), {'dup': {str(k): v for k, v in dup.items()}, 'dup_logs_1_3': dup_logs[('1', '3')],
            'prim_dedup': {r['id']: r['_prim_dedup'] for r in recs}, 'one_vote_rel': {str(k): v for k, v in one_vote_rel.items()},
            'prim_type': {str(k): v for k, v in prim_type.items()}})
