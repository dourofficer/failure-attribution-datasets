#!/usr/bin/env python3
"""Join the all-at-once baseline predictions and the prefix probe with the per-run symptom statistics.
Questions: when the judge misses, does it pick the first mechanical symptom (first malformed / Nothing / repeated / error turn)?
Is the gold step locally detectable per env and per label module? Writes results/agenterrorbench/baseline_vs_symptoms.md"""
import json, os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_jsonl, md_table  # noqa

R = os.path.join(RESULTS, 'agenterrorbench')
per = {r['id']: r for r in read_jsonl(os.path.join(R, 'stats_per_run.jsonl'))}
base = read_jsonl(os.path.join(R, 'all_at_once_std.jsonl'))
probe = read_jsonl(os.path.join(R, 'prefix_probe.jsonl'))
turn = lambda idx: (idx + 1) // 2 if idx is not None else None
out = ['# Baseline and prefix probe vs symptom turns\n']
rows = []
cat = Counter()
for b in base:
    p = per[b['id']]
    pt, gt = turn(b['pred_step']), turn(b['gold_step'])
    if pt is None:
        continue
    sym = {'first malformed': p['first_malformed_turn'], 'first inadmissible': p['first_inadmissible_turn'], 'first Nothing': p['first_nothing_turn']}
    hit = [k for k, v in sym.items() if v == pt]
    rows.append([b['id'].split('/')[1][:26], p['env'], gt, pt, pt - gt, p['cats'][-1] if p['cats'] else '', ','.join(hit) or '-', p['n_nothing'], p['n_malformed']])
    if pt != gt:
        cat['miss'] += 1
        cat['miss & pred == first malformed/inadmissible/Nothing turn'] += bool(hit)
        cat['miss & pred earlier than gold'] += pt < gt
        cat['miss & pred earlier & run has >=5 Nothing turns'] += (pt < gt and p['n_nothing'] >= 5)
    else:
        cat['exact'] += 1
        cat['exact & gold == first malformed/inadmissible/Nothing turn'] += bool(hit)
out.append('## All-at-once (n=%d)\n' % len(rows))
out.append(md_table(['count', 'n'], [[k, v] for k, v in cat.items()]))
# by env: direction of misses
by = defaultdict(Counter)
for r in rows:
    by[r[1]]['n'] += 1; by[r[1]]['exact'] += r[4] == 0; by[r[1]]['earlier'] += r[4] < 0; by[r[1]]['later'] += r[4] > 0
    by[r[1]]['|d|<=1'] += abs(r[4]) <= 1
out.append('\n' + md_table(['env', 'n', 'exact', 'pred earlier (turns)', 'pred later', 'within ±1 turn'], [[e, c['n'], c['exact'], c['earlier'], c['later'], c['|d|<=1']] for e, c in by.items()]))
out.append('\n' + md_table(['id', 'env', 'gold turn', 'pred turn', 'pred-gold', 'label type', 'pred == symptom turn', '#Nothing', '#malformed'], sorted(rows, key=lambda r: (r[1], r[4]))))
# signed offset median by env
import statistics
out.append('\nmedian signed offset (turns) per env: ' + str({e: statistics.median([r[4] for r in rows if r[1] == e]) for e in by}))
# prefix probe per env / module
out.append('\n## Prefix probe (window ±6 idx around gold, n=%d records)\n' % len(probe))
pb = defaultdict(lambda: Counter())
for x in probe:
    p = per[x['id']]
    for key in (p['env'], 'module=' + (p['module'] or '?')):
        c = pb[key]
        c['n'] += 1; c['gold flagged'] += x['gold_flagged']; c['earliest flagged == gold'] += x['earliest_flagged'] == x['gold']
        c['flag before'] += x['n_flagged_before']; c['probed before'] += x['n_probed_before']; c['flag after'] += x['n_flagged_after']; c['probed after'] += x['n_probed_after']
        c['gold is Nothing/malformed turn'] += bool(p['gold_is_nothing'] or p['gold_is_malformed'])
out.append(md_table(['group', 'records', 'gold flagged', 'earliest flagged == gold', 'flag rate before gold', 'flag rate after gold', 'gold turn is a null-obs/malformed turn'],
    [[k, c['n'], c['gold flagged'], c['earliest flagged == gold'], f"{c['flag before']}/{c['probed before']}", f"{c['flag after']}/{c['probed after']}", c['gold is Nothing/malformed turn']] for k, c in pb.items()]))
# gold flagged vs gold-is-symptom
sym_f = Counter()
for x in probe:
    p = per[x['id']]
    k = 'gold is null-obs/malformed' if (p['gold_is_nothing'] or p['gold_is_malformed'] or p['gold_obs_before_nothing']) else 'gold is a semantic decision'
    sym_f[(k, x['gold_flagged'])] += 1
out.append('\n' + md_table(['gold-turn kind', 'flagged', 'not flagged'], [[k, sym_f[(k, True)], sym_f[(k, False)]] for k in ('gold is null-obs/malformed', 'gold is a semantic decision')]))
out.append('\nper-record probe: ' + '; '.join(f"{x['id'].split('/')[1][:22]} gold {turn(x['gold'])} flagged={x['gold_flagged']} earliest={turn(x['earliest_flagged']) if x['earliest_flagged'] is not None else None} what={ (x['scores'].get(str(x['gold'])) or {}).get('what','')[:80]!r}" for x in probe))
open(os.path.join(R, 'baseline_vs_symptoms.md'), 'w').write('\n'.join(out))
print('\n'.join(out))
