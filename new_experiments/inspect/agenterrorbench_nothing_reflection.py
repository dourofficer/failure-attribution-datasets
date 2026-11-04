#!/usr/bin/env python3
"""How do agents interpret 'Nothing happens' (ALFWorld) and empty result pages (WebShop)?
For every agent turn whose preceding observation is 'Nothing happens', classify the <reflection>/<memory> text:
 aware  = mentions format/quotes/syntax/invalid/admissible/exact
 misread = claims the action succeeded / treats it as 'not found' / 'no X there' / 'empty'
 other.
Also WebShop: count 'next >' clicks on result pages that list no products, and runs that never open a product page.
Writes results/agenterrorbench/nothing_reflection.md"""
import json, os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, read_json, md_table  # noqa
from loaders import load  # noqa

R = os.path.join(RESULTS, 'agenterrorbench')
recs = {r['id']: r for r in load('agenterrorbench')}
turns_all = read_json(os.path.join(R, 'compact_turns.json'))
AWARE = re.compile(r"quot|format|syntax|invalid|admissible|exact(ly)? as|without (the )?quotes|apostroph|parsed|not (a )?valid|unrecognized|typo|wording|phrasing", re.I)
MISREAD = re.compile(r"(nothing|no \w+) (was |is )?(found|there|in|at)|not (found|present|available|located)|doesn't contain|does not contain|did not (reveal|find|yield)|empty|is not (here|in)|already (there|at|open)|successful", re.I)
rows = []
by = defaultdict(Counter)
examples = []
for rid, d in turns_all.items():
    rec = recs[rid]
    if rec['subset'] != 'alfworld':
        continue
    for t in d['turns']:
        if not (t['obs_before'] or '').strip().lower().startswith('nothing happens'):
            continue
        c = rec['steps'][t['idx']]['content']
        refl = ' '.join(re.findall(r'<reflection>(.*?)</reflection>', c, re.S) + re.findall(r'<memory>(.*?)</memory>', c, re.S)) or c
        if AWARE.search(refl):
            k = 'aware(format)'
        elif MISREAD.search(refl):
            k = 'misread(as semantic outcome)'
        else:
            k = 'other/neutral'
        by[rec['meta']['backbone']][k] += 1
        if k != 'aware(format)' and len(examples) < 12 and t['idx'] == d['gold']:
            examples.append((rid, t['idx'], re.sub(r'\s+', ' ', refl)[:300]))
out = ['# How ALFWorld agents interpret "Nothing happens"\n', md_table(['backbone', 'turns after Nothing happens', 'aware(format)', 'misread(as semantic outcome)', 'other'],
      [[b, sum(c.values()), c['aware(format)'], c['misread(as semantic outcome)'], c['other/neutral']] for b, c in by.items()])]
out.append('\nExamples where the GOLD turn follows a "Nothing happens" and the reflection does not mention the format:\n')
for e in examples:
    out.append(f'- {e[0]} idx {e[1]}: {e[2]}')
# WebShop: empty pages and product opens
ws_rows = []
for rid, d in turns_all.items():
    rec = recs[rid]
    if rec['subset'] != 'webshop':
        continue
    empty_next = 0; opened = 0; n_search = 0; n_next = 0
    for t in d['turns']:
        o = t['obs_before'] or ''
        a = t['action'].strip().lower()
        is_results = "'page " in o.lower() and 'total results' in o.lower()
        has_products = bool(re.search(r"'b0[0-9a-z]{8}'", o, re.I))
        if a.startswith('click[next') and is_results and not has_products:
            empty_next += 1
        if re.match(r"click\[b0[0-9a-z]{8}\]", a):
            opened += 1
        n_search += a.startswith('search[')
        n_next += a.startswith('click[next')
    ws_rows.append({'id': rid, 'backbone': rec['meta']['backbone'], 'n_turns': len(d['turns']), 'empty_next': empty_next, 'opened': opened, 'n_search': n_search, 'n_next': n_next, 'cats': d['cats'][-1] if d['cats'] else ''})
out.append('\n\n# WebShop: paging through empty result pages and product opens\n')
out.append(md_table(['backbone', 'runs', "'next' clicks on EMPTY result pages (total)", 'runs with >=1 such click', 'runs that never open a product', 'median searches per run', 'median next-clicks per run'],
    [[b, len(rs), sum(r['empty_next'] for r in rs), sum(1 for r in rs if r['empty_next']), sum(1 for r in rs if r['opened'] == 0), sorted(r['n_search'] for r in rs)[len(rs) // 2], sorted(r['n_next'] for r in rs)[len(rs) // 2]]
     for b, rs in [(b, [r for r in ws_rows if r['backbone'] == b]) for b in ('GPT-4o', 'Llama3.3-70B-Turbo', 'Qwen3-8B')]]))
out.append('\nruns that never open a product: ' + ', '.join(f"{r['id'].split('/')[1][:24]}({r['cats']})" for r in ws_rows if r['opened'] == 0))
with open(os.path.join(R, 'nothing_reflection.md'), 'w') as fh:
    fh.write('\n'.join(out))
print('\n'.join(out))
