#!/usr/bin/env python3
"""Where is the annotator's evidence text? For every located error, test whether the 'evidence' string occurs in
(a) the rendered step content, (b) the span's full attributes (all input messages + output), (c) any other span of the
trace (and which one, relative to the labelled span), (d) nowhere (paraphrase). Also: category fatality = share of each
category's errors that sit in correct-ending vs wrong-ending GAIA traces."""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, read_json  # noqa: E402
from loaders import load  # noqa: E402
from loaders.trail import lj, flatten  # noqa: E402

CORRECT = {  # semantic judgement of final answer vs GAIA true answer (see trail_stats + manual check)
    'bad': {'gaia/331aece579d942bb4c345a86c86efb83', 'gaia/c60ad8608dd94271a6c6805eedfa26a8'}}


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip().lower()


def main():
    stats = {r['id']: r for r in read_json(os.path.join(RESULTS, 'trail', 'stats.json'))}
    recs = load('trail')
    out = Counter(); by_cat = defaultdict(Counter); where = Counter(); offs = []
    rows = []
    for r in recs:
        t, _ = lj(r['meta']['file'])
        fl = []
        for root in t['spans']:
            flatten(root, 0, None, fl)
        full = [norm(json.dumps(x['span'].get('span_attributes') or {}, ensure_ascii=False)) for x in fl]
        for e in r['labels']['extra']['errors']:
            if e['idx'] is None:
                continue
            ev = norm(e.get('evidence'))
            if len(ev) < 15:
                out['evidence too short'] += 1; continue
            frag = ev[:60]
            frag2 = ev[-60:]
            k = e['idx']
            if frag in norm(r['steps'][k]['content']) or frag2 in norm(r['steps'][k]['content']):
                w = 'rendered step'
            elif frag in full[k] or frag2 in full[k]:
                w = 'span attrs (input history)'
            else:
                hits = [j for j, f in enumerate(full) if frag in f or frag2 in f]
                if hits:
                    d = min(hits, key=lambda j: abs(j - k))
                    w = 'other span'
                    offs.append(d - k)
                else:
                    w = 'nowhere (paraphrase)'
            out[w] += 1; by_cat[e['category']][w] += 1; where[(e['kind'], w)] += 1
            rows.append({'id': r['id'], 'idx': k, 'kind': e['kind'], 'cat': e['category'], 'impact': e['impact'], 'where': w})
    print('evidence location:', dict(out))
    print('by span kind:', dict(where))
    print('other-span offsets (other - labelled):', Counter(offs).most_common(12))
    print(md_table(['category', 'rendered', 'span attrs', 'other span', 'nowhere'],
                   [[c] + [d[k] for k in ('rendered step', 'span attrs (input history)', 'other span', 'nowhere (paraphrase)')] for c, d in sorted(by_cat.items(), key=lambda x: -sum(x[1].values()))[:14]]))
    json.dump(rows, open(os.path.join(RESULTS, 'trail', 'evidence_location.json'), 'w'), indent=1)
    # category fatality on GAIA
    fat = defaultdict(Counter); tr = Counter()
    for r in recs:
        if r['subset'] != 'gaia':
            continue
        s = stats[r['id']]
        ok = bool(s['answer_match']) and r['id'] not in CORRECT['bad']
        tr[ok] += 1
        for cat in {(e['category'], e['impact']) for e in r['labels']['extra']['errors']}:
            fat[cat[0]][ok] += 1
        for e in r['labels']['extra']['errors']:
            fat['_impact_' + e['impact']][ok] += 1
    print('\nGAIA traces correct/wrong:', dict(tr))
    print(md_table(['category', 'traces w/ cat: correct', 'wrong', 'P(correct | cat present)'],
                   [[c, d[True], d[False], f'{d[True] / max(1, d[True] + d[False]):.2f}'] for c, d in sorted(fat.items(), key=lambda x: -(x[1][True] + x[1][False])) if d[True] + d[False] >= 4]))


if __name__ == '__main__':
    main()
