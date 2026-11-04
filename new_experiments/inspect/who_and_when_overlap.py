#!/usr/bin/env python3
"""Label-reliability test on overlapping logs: Who&When HC vs AgentRx Magentic-One (40 logs matched by question+length)
and Who&When (HC+AG) vs MP-Bench (177 logs via log_source URL). Also HC termination type vs label step type."""
import json, os, re, sys, collections, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, write_json
from common.schema import error_step
from loaders import load

ww = {r['id']: r for r in load('who_and_when')}
mp = {r['id']: r for r in load('mp_bench')}
rx = {r['id']: r for r in load('agentrx')}
m = json.load(open(os.path.join(RESULTS, 'who_and_when', 'overlap_map.json')))

def steptype(r, k):
    s = r['steps'][k]; a = s['meta'].get('base_agent', s['agent']); c = s['content']
    if a == 'Orchestrator':
        if c.startswith('Stalled'): return 'Orch:stalled'
        if c.startswith('Updated Ledger'): return 'Orch:ledger'
        if c.startswith('Initial plan') or c.startswith('New plan'): return 'Orch:plan'
        if s['agent'].startswith('Orchestrator (->'): return 'Orch:instruction'
        return 'Orch:other'
    return a

print('## HC termination type vs label step type')
tab = collections.Counter()
for r in ww.values():
    if r['subset'] != 'Hand-Crafted': continue
    last = r['steps'][-1]['content']
    term = 'max_time' if 'Max time' in last else ('satisfied' if any('Request satisfied' in s['content'] for s in r['steps'][-4:]) else 'other')
    fa = re.search(r'FINAL ANSWER:\s*(.*)', last)
    unable = bool(fa and re.search(r'unable|cannot|not (be )?determin|unknown|no answer', fa.group(1), re.I))
    tab[(term, 'unable' if unable else 'answer', steptype(r, error_step(r)))] += 1
for k, v in sorted(tab.items()): print(v, k)

print('\n## WW-HC vs AgentRx (root cause and full failure set)')
rows = []
for rid, wid in m['rx_to_ww'].items():
    if not isinstance(wid, str): continue
    a, b = rx[rid], ww[wid]
    g_ww = error_step(b); g_rx = error_step(a); fails = sorted(a['labels']['error_steps'])
    rows.append({'rx': rid[:22], 'ww': wid, 'n': len(b['steps']), 'ww_step': g_ww, 'ww_agent': b['labels']['error_agent'], 'rx_root': g_rx, 'rx_agent': a['labels']['error_agent'],
                 'rx_first': fails[0] if fails else None, 'rx_all': fails, 'ww_in_rx_set': g_ww in fails, 'ww_type': steptype(b, g_ww), 'rx_type': steptype(b, g_rx), 'rx_cat': a['labels']['categories']})
d = [r['rx_root'] - r['ww_step'] for r in rows]
print('n', len(rows), 'exact root==ww', sum(1 for x in d if x == 0), 'within1', sum(1 for x in d if abs(x) <= 1), 'within3', sum(1 for x in d if abs(x) <= 3),
      'rx later', sum(1 for x in d if x > 0), 'rx earlier', sum(1 for x in d if x < 0), 'median signed', statistics.median(d))
print('WW step inside AgentRx failure set:', sum(r['ww_in_rx_set'] for r in rows), '; AgentRx first failure == WW step:', sum(1 for r in rows if r['rx_first'] == r['ww_step']),
      '; agent agree:', sum(1 for r in rows if (r['ww_agent'] or '').lower() == (r['rx_agent'] or '').lower()))
print(md_table(['ww', 'n', 'ww_step', 'ww_type', 'rx_root', 'rx_type', 'rx_first', 'rx_all(first 8)', 'rx_cat'],
               [[r['ww'], r['n'], r['ww_step'], r['ww_type'], r['rx_root'], r['rx_type'], r['rx_first'], r['rx_all'][:8], r['rx_cat'][0][:28] if r['rx_cat'] else ''] for r in sorted(rows, key=lambda x: int(x['ww'].split('/')[1].split('.')[0]))]))

print('\n## WW vs MP-Bench (3 annotators)')
mrows = []
for mid, wid in m['mp_to_ww'].items():
    if not wid: continue
    a, b = mp[mid], ww[wid]
    g = error_step(b); votes = a['labels']['votes'] or {}; es = a['labels']['error_steps']
    maj = a['labels']['extra']['majority_steps']; prim = a['labels']['extra']['earliest_majority_step']
    mrows.append({'ww': wid, 'sub': b['subset'], 'n': len(b['steps']), 'ww_step': g, 'votes_on_ww': votes.get(g, 0), 'n_flagged': len(es), 'first_flag': es[0] if es else None,
                  'maj_first': prim, 'maj_steps': maj, 'ww_in_union': g in es, 'ww_in_majority': g in maj, 'ww_type': steptype(b, g),
                  'earlier_flags': sum(1 for e in es if e < g), 'later_flags': sum(1 for e in es if e > g), 'earlier_maj': sum(1 for e in maj if e < g), 'later_maj': sum(1 for e in maj if e > g),
                  'ww_agent': b['labels']['error_agent'], 'mp_agent': a['labels']['error_agent']})
for sub in ('Hand-Crafted', 'Algorithm-Generated'):
    rs = [r for r in mrows if r['sub'] == sub]
    print(f'\n{sub}: n={len(rs)}')
    print(' WW step votes 0/1/2/3:', collections.Counter(r['votes_on_ww'] for r in rs))
    print(' WW step in union', sum(r['ww_in_union'] for r in rs), '; in majority set', sum(r['ww_in_majority'] for r in rs), '; == earliest majority', sum(1 for r in rs if r['maj_first'] == r['ww_step']), '; == earliest flag', sum(1 for r in rs if r['first_flag'] == r['ww_step']))
    print(' majority steps strictly earlier than WW exist:', sum(1 for r in rs if r['earlier_maj'] > 0), '; strictly later exist:', sum(1 for r in rs if r['later_maj'] > 0))
    print(' mean flagged per log', statistics.mean(r['n_flagged'] for r in rs), '; agent agree (ww vs mp earliest-majority agent)', sum(1 for r in rs if (r['ww_agent'] or '').lower().replace(' ', '') == (r['mp_agent'] or '').lower().replace(' ', '')))
    d = [r['maj_first'] - r['ww_step'] for r in rs if r['maj_first'] is not None]
    print(' earliest-majority minus WW: median', statistics.median(d), 'later', sum(1 for x in d if x > 0), 'earlier', sum(1 for x in d if x < 0), 'same', sum(1 for x in d if x == 0))
    print(' votes on WW step by WW step type:', {t: collections.Counter(r['votes_on_ww'] for r in rs if r['ww_type'] == t) for t in set(r['ww_type'] for r in rs)} if sub == 'Hand-Crafted' else '')
write_json(os.path.join(RESULTS, 'who_and_when', 'overlap_rows.json'), {'agentrx': rows, 'mp_bench': mrows})
