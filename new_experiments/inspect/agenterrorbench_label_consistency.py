#!/usr/bin/env python3
"""Label-text consistency for AgentErrorBench: does the annotator's reasoning text refer to objects / tools / products
that never occur in the trajectory (a sign that the label was written for another run)? Also module spelling variants.
Writes results/agenterrorbench/label_consistency.md"""
import os, re, sys
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table  # noqa
from loaders import load  # noqa

STOP = set('the a an and or of to in on at for with by from as is was were be been it its this that which not no yes agent model step steps task goal action actions observation plan planning memory reflection module failure error result results page search query product products item items user tool tools environment '
           'next back click search did does do should could would after before then than instead while because but so if when where which who what how all any some more most one two first last same other only also into out up down over under again still already correct wrong invalid valid proper improper correctly incorrectly misinterpreted misinterpret misread'.split())
rows = []
for r in load('agenterrorbench'):
    reason = r['labels']['reason'] or ''
    if not reason.strip():
        continue
    traj = ' '.join(s['content'] for s in r['steps']).lower()
    words = [w for w in re.findall(r"[a-z][a-z0-9_\-']{3,}", reason.lower()) if w not in STOP]
    # keep only concrete-looking tokens: nouns of ALFWorld objects / product ids / tool names
    missing = sorted({w for w in words if w not in traj and w.rstrip('s') not in traj and (w + 's') not in traj})
    rows.append({'id': r['id'], 'env': r['subset'], 'n_words': len(set(words)), 'missing': missing, 'reason': reason[:200]})
sus = [x for x in rows if x['n_words'] and len(x['missing']) / x['n_words'] >= 0.25 and len(x['missing']) >= 2]
out = ['# Label-text consistency\n', f'records with reason text: {len(rows)}; records whose reason contains >=2 content words absent from the whole trajectory and >=25% of its content words absent: {len(sus)}\n']
out.append(md_table(['id', 'env', 'missing words', 'reason (head)'], [[x['id'], x['env'], ', '.join(x['missing'][:8]), x['reason'][:120].replace('|', '/')] for x in sus]))
# spelling variants
recs = load('agenterrorbench')
c = Counter((r['labels']['extra']['critical_failure_module'], (r['labels']['categories'][1].split('.', 1)[1] if len(r['labels']['categories']) > 1 else '')) for r in recs)
out.append('\n## module / failure_type spellings as shipped\n' + md_table(['module (raw)', 'failure_type', 'n'], [[m, f, n] for (m, f), n in sorted(c.items())]))
with open(os.path.join(RESULTS, 'agenterrorbench', 'label_consistency.md'), 'w') as fh:
    fh.write('\n'.join(out))
print('\n'.join(out))
