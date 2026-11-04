#!/usr/bin/env python3
"""SymTrace/SymFail targeted statistics:
 1. environment failure share: runs whose tool results hit the literal site placeholder (__SHOPPING__ etc. / MissingSchema / NameResolutionError), runs with no tool call at all
 2. what the failure node is when there is no agent mistake possible (no tool reached the site): node kind, position, label
 3. C1-C4 primary label predictability from node kind / structural features (majority-class, simple rules, per-MAS)
 4. failure node = first agent action / final node; relation to the first failed tool result
 5. final answer type ('cannot complete' vs confident answer) vs label and failure node position
Writes results/symtrace/stats.json"""
import json, os, re, sys, collections, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, write_json
from common.schema import error_step
from loaders import load

PLACEHOLDER = re.compile(r'__(SHOPPING|SHOPPING_ADMIN|REDDIT|GITLAB|MAP|WIKIPEDIA|HOMEPAGE)__|MissingSchema|NameResolutionError|Failed to resolve|No scheme supplied', re.I)
GIVEUP = re.compile(r"(unable|cannot|can't|could not|not possible|not able|no access|insufficient|unknown|n/a|not available|failed)", re.I)

recs = load('symtrace')
rows = []
for r in recs:
    g = error_step(r); n = len(r['steps']); kinds = [s['meta']['kind'] for s in r['steps']]
    tool_results = [s for s in r['steps'] if s['meta']['kind'] == 'tool_result']
    tool_calls = [s for s in r['steps'] if s['meta']['kind'] == 'tool_call']
    ph = [s['idx'] for s in tool_results if PLACEHOLDER.search(s['content'])]
    fail_tr = [s['idx'] for s in tool_results if re.search(r'error|exception|failed|timeout|404|403|500', s['content'][:600], re.I)]
    ok_tr = [s['idx'] for s in tool_results if s['idx'] not in fail_tr]
    agent_actions = [s['idx'] for s in r['steps'] if s['meta']['kind'] == 'agent_action']
    fa = r['final_output'] or ''
    rows.append({'id': r['id'], 'mas': r['subset'], 'bench': r['meta']['benchmark'], 'n': n, 'gold': g, 'gold_kind': kinds[g], 'gold_rel': g / max(1, n - 1),
                 'primary': r['labels']['extra']['primary_failure_label'], 'labels': r['labels']['categories'], 'conf': r['labels']['extra']['confidence'],
                 'n_tool_calls': len(tool_calls), 'n_tool_results': len(tool_results), 'n_placeholder': len(ph), 'n_failed_tr': len(fail_tr), 'n_ok_tr': len(ok_tr),
                 'env_blocked': bool(tool_calls) and len(ok_tr) == 0, 'no_tool': len(tool_calls) == 0,
                 'gold_is_first_action': bool(agent_actions) and g == agent_actions[0], 'gold_is_final': kinds[g] == 'final_result', 'gold_is_last': g == n - 1,
                 'gold_after_first_failed_tr': bool(fail_tr) and g > fail_tr[0], 'gold_is_tool_call': kinds[g] == 'tool_call',
                 'first_failed_tr': fail_tr[0] if fail_tr else None, 'gold_minus_first_failed_tr': (g - fail_tr[0]) if fail_tr else None,
                 'giveup': bool(GIVEUP.search(fa[:300])), 'final_len': len(fa), 'unanimous': (r['labels']['extra']['inter_annotator_agreement'] or {}).get('node_unanimous') if isinstance(r['labels']['extra']['inter_annotator_agreement'], dict) else None,
                 'kinds': kinds})
print('## environment reach')
for mas in ('ag2', 'crewai', 'magnetic_one'):
    rs = [x for x in rows if x['mas'] == mas]
    wa = [x for x in rs if x['bench'] and 'webarena' in str(x['bench']).lower()]
    print(f"{mas}: n={len(rs)} no_tool_call={sum(x['no_tool'] for x in rs)} env_blocked(all tool results failed)={sum(x['env_blocked'] for x in rs)} placeholder_hit={sum(1 for x in rs if x['n_placeholder'])} any_ok_tool_result={sum(1 for x in rs if x['n_ok_tr'])} giveup_final={sum(x['giveup'] for x in rs)}")
print('\n## failure node kind x primary label (all)')
tab = collections.Counter((x['gold_kind'], x['primary']) for x in rows)
kinds = sorted({x['gold_kind'] for x in rows}); labs = ['c1', 'c2', 'c3', 'c4']
print(md_table(['node kind'] + labs + ['total'], [[k] + [tab[(k, l)] for l in labs] + [sum(tab[(k, l)] for l in labs)] for k in kinds]))
print('\n## primary label by (mas, situation)')
def sit(x):
    if x['no_tool']: return 'no_tool_call'
    if x['env_blocked']: return 'env_blocked'
    return 'reached_env'
tab2 = collections.Counter((x['mas'], sit(x), x['primary']) for x in rows)
keys = sorted({(a, b) for a, b, _ in tab2})
print(md_table(['mas', 'situation'] + labs + ['n', 'gold=first action', 'gold=final', 'gold=tool_call'],
               [[a, b] + [tab2[(a, b, l)] for l in labs] + [sum(tab2[(a, b, l)] for l in labs), sum(1 for x in rows if x['mas'] == a and sit(x) == b and x['gold_is_first_action']), sum(1 for x in rows if x['mas'] == a and sit(x) == b and x['gold_is_final']), sum(1 for x in rows if x['mas'] == a and sit(x) == b and x['gold_is_tool_call'])] for a, b in keys]))
print('\n## predictability of primary label')
maj = collections.Counter(x['primary'] for x in rows).most_common(1)[0]
print('majority class', maj, '-> acc %.3f' % (maj[1] / len(rows)))
for feat in ('gold_kind', 'mas'):
    byf = collections.defaultdict(collections.Counter)
    for x in rows: byf[x[feat]][x['primary']] += 1
    acc = sum(c.most_common(1)[0][1] for c in byf.values()) / len(rows)
    print(f'rule: majority label per {feat}: acc {acc:.3f}', {k: c.most_common(1)[0] for k, c in byf.items()})
byf = collections.defaultdict(collections.Counter)
for x in rows: byf[(x['mas'], x['gold_kind'], sit(x))][x['primary']] += 1
print('rule: majority per (mas, kind, situation): acc %.3f' % (sum(c.most_common(1)[0][1] for c in byf.values()) / len(rows)))
byf = collections.defaultdict(collections.Counter)
for x in rows: byf[(x['mas'], x['gold_kind'], sit(x), x['giveup'])][x['primary']] += 1
print('rule: + giveup final: acc %.3f' % (sum(c.most_common(1)[0][1] for c in byf.values()) / len(rows)))
print('\n## failure node position relative to the first failed tool result')
d = [x['gold_minus_first_failed_tr'] for x in rows if x['gold_minus_first_failed_tr'] is not None]
print('runs with a failed tool result:', len(d), '; gold before it', sum(1 for v in d if v < 0), '; gold = the call just before it (-1)', sum(1 for v in d if v == -1), '; gold after it', sum(1 for v in d if v > 0), '; median', statistics.median(d))
print('gold is last node:', sum(x['gold_is_last'] for x in rows), '; gold is first agent action:', sum(x['gold_is_first_action'] for x in rows), '; unanimous:', sum(1 for x in rows if x['unanimous']))
print('\n## give-up finals vs confident finals: primary label')
print(collections.Counter((x['giveup'], x['primary']) for x in rows))
print('\n## magnetic_one: agent of failure node', collections.Counter(r['labels']['error_agent'] for r in recs if r['subset'] == 'magnetic_one'))
print('\n## kinds sequence patterns (top 8 per mas)')
for mas in ('ag2', 'crewai', 'magnetic_one'):
    c = collections.Counter(','.join(k[:4] for k in x['kinds']) for x in rows if x['mas'] == mas)
    print(mas, len(c), 'distinct;', c.most_common(5))
write_json(os.path.join(RESULTS, 'symtrace', 'stats.json'), rows)
