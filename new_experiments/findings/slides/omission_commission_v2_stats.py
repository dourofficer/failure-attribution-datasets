#!/usr/bin/env python3
"""Numbers for omission_commission_v2.pptx (gap -> carry-on -> fill-in).

Reads results/omission_commission/llm_<slug>.jsonl (the label-blind classifier of inspect/oc_classify.py) and writes
omission_commission_v2_stats.json next to this file.

Vocabulary (v2 slides <- hypotheses.md): gap = omission, carry-on = acceptance, fill-in = commission, chain = pair.
Per dataset, over failed runs the classifier answered with a valid shape:
  chain        runs whose shape is 'pair' (a gap and a later fill-in were both found)
Per dataset, over chain runs only, with the dataset's primary label L:
  near_gap / near_carry / near_fill   |L - step| <= 1 for that step; NOT exclusive (adjacent steps can both match)
  near_any     L within +-1 of at least one of the three steps
  on_any       L exactly equal to one of the three steps
Selection for the slides: natural-failure datasets with chain rate >= 55% AND near_any rate >= 55%.

Usage: python3 findings/slides/omission_commission_v2_stats.py   (from new_experiments/)
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', '..', 'results', 'omission_commission')
SHAPES = {'pair', 'commission_only', 'omission_only', 'other'}
NATURAL = ['who_and_when', 'mp_bench', 'traceelephant', 'trail', 'searchauditbench', 'agentrx', 'symtrace',
           'agenthallu', 'trajerrbench', 'longrca', 'agenterrorbench', 'memtrace', 'horizon']
NAMES = {'who_and_when': 'Who&When', 'mp_bench': 'MP-Bench', 'traceelephant': 'TraceElephant', 'trail': 'TRAIL',
         'searchauditbench': 'SearchAuditBench', 'agentrx': 'AgentRx', 'symtrace': 'SymTrace', 'agenthallu': 'AgentHallu',
         'trajerrbench': 'TrajErrBench', 'longrca': 'LongRCA', 'agenterrorbench': 'AgentErrorBench', 'memtrace': 'MemTrace',
         'horizon': 'HORIZON'}
SAMPLED = {'searchauditbench', 'symtrace', 'agenthallu', 'trajerrbench', 'longrca', 'memtrace', 'horizon'}
THRESH = 0.55
KEYS = ['runs', 'chain', 'near_gap', 'near_carry', 'near_fill', 'near_any', 'on_any']


def dist(label, step):
    try:
        return abs(int(label) - int(step)) if step is not None else None
    except (TypeError, ValueError):
        return None


def one(slug):
    raw = [json.loads(l) for l in open(os.path.join(RES, f'llm_{slug}.jsonl'))]
    rows = [r for r in raw if r.get('parsed') and r['parsed'].get('shape') in SHAPES]
    s = dict.fromkeys(KEYS, 0)
    s['runs'] = len(rows); s['unparsed'] = len(raw) - len(rows)
    for r in rows:
        p = r['parsed']
        if p['shape'] != 'pair':
            continue
        s['chain'] += 1
        d = [dist(r['label'], p.get(k + '_step')) for k in ('omission', 'acceptance', 'commission')]
        near = [x is not None and x <= 1 for x in d]
        s['near_gap'] += near[0]; s['near_carry'] += near[1]; s['near_fill'] += near[2]
        s['near_any'] += any(near)
        s['on_any'] += any(x == 0 for x in d if x is not None)
    s.update(slug=slug, name=NAMES[slug], sampled=slug in SAMPLED,
             chain_rate=s['chain'] / s['runs'], near_any_rate=s['near_any'] / s['chain'] if s['chain'] else 0)
    return s


def total(rows):
    t = {k: sum(r[k] for r in rows) for k in KEYS}
    t['chain_rate'] = t['chain'] / t['runs']; t['near_any_rate'] = t['near_any'] / t['chain']; t['on_any_rate'] = t['on_any'] / t['chain']
    return t


if __name__ == '__main__':
    rows = [one(s) for s in NATURAL]
    sel = [r for r in rows if r['chain_rate'] >= THRESH and r['near_any_rate'] >= THRESH]
    sel.sort(key=lambda r: -r['near_any_rate'])
    out = {'threshold': THRESH, 'selected': sel, 'selected_total': total(sel),
           'not_shown': [r for r in rows if r not in sel], 'all_natural_total': total(rows)}
    json.dump(out, open(os.path.join(HERE, 'omission_commission_v2_stats.json'), 'w'), indent=1)
    for r in rows:
        print(f"{'*' if r in sel else ' '} {r['name']:17s} runs {r['runs']:3d} chain {r['chain']:3d} ({r['chain_rate']:.0%}) "
              f"gap {r['near_gap']:3d} carry {r['near_carry']:3d} fill {r['near_fill']:3d} any {r['near_any']:3d} ({r['near_any_rate']:.0%}) exact {r['on_any']}")
    for k in ('selected_total', 'all_natural_total'):
        t = out[k]
        print(k, t['runs'], t['chain'], f"{t['chain_rate']:.1%}", 'near_any', t['near_any'], f"{t['near_any_rate']:.1%}", 'on_any', t['on_any'], f"{t['on_any_rate']:.1%}",
              'gap/carry/fill', t['near_gap'], t['near_carry'], t['near_fill'])
