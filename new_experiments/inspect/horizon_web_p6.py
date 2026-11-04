#!/usr/bin/env python3
"""Web domain: (1) pass-vs-fail AUROC of cheap trajectory features (P6), (2) shared action prefix between a passing run
of the same task_id at a lower level and a failing run at a higher level (do failures follow the success flow up to the break?),
(3) label-step text signatures (Action: none, identical-action loop start). Writes results/horizon/web_p6.md"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, DATA, md_table  # noqa
R = os.path.join(DATA, 'horizon', 'hf')
d2 = json.load(open(os.path.join(R, 'result_2', 'classified_results.json')))
d5 = {x['id']: x for x in json.load(open(os.path.join(R, 'result_5', 'classified_results.json')))}
out = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)
def parse(t):
    blocks = re.split(r'^\[Step (\d+)\]\n', t, flags=re.M)
    steps = []
    for i in range(1, len(blocks), 2):
        b = blocks[i + 1]
        a = re.search(r'^Action:\s*(.*)$', b, re.M); pg = re.search(r'^Page\s*:\s*(.*)$', b, re.M)
        steps.append({'n': int(blocks[i]), 'action': a.group(1).strip() if a else '', 'page': pg.group(1).strip() if pg else ''})
    return steps
def norm(a):  # action without element ids
    a = re.sub(r'\[\d+\]', '[id]', a); a = re.sub(r'where \[id\].*$', '', a); return a.strip()[:80]
recs = []
for x in d2:
    if x['domain'] != 'web': continue
    s = parse(x['trajectory'])
    acts = [st['action'] for st in s]
    nacts = [norm(a) for a in acts]
    try: sc = float(x.get('score'))
    except (TypeError, ValueError): sc = None
    recs.append({'id': x['id'], 'model': x['model'], 'run': x['run'], 'task': x['task_id'], 'score': sc, 'judge': x['failure_type'], 'n': len(s),
                 'none': sum(1 for a in acts if a in ('', 'none')), 'early_stop': any('Early stop' in a for a in acts),
                 'maxrep': max(collections.Counter(nacts).values()) if nacts else 0, 'consec': sum(1 for a, b in zip(nacts, nacts[1:]) if a == b and a),
                 'page_rep': max(collections.Counter(st['page'] for st in s).values()) if s else 0, 'acts': nacts, 'stop': acts[-1] if acts else '',
                 'level': re.search(r'step_([\d.]+)', x['run']).group(1) if re.search(r'step_([\d.]+)', x['run']) else None})
def auroc(pos, neg):
    s = sum(1 if p > q else 0.5 if p == q else 0 for p in pos for q in neg); return s / (len(pos) * len(neg))
P('## Web: pass vs fail cheap features (env score)\n')
rows = []
for m in ('gpt', 'claude', 'all'):
    v = [r for r in recs if (m == 'all' or r['model'] == m) and r['score'] is not None]
    pos = [r for r in v if r['score'] < 1]; neg = [r for r in v if r['score'] >= 1]
    rows.append([m, len(pos), len(neg), f"{sum(r['n'] for r in pos)/len(pos):.1f} / {sum(r['n'] for r in neg)/len(neg):.1f}",
                 f"{100*sum(1 for r in pos if r['none']>0)/len(pos):.0f} / {100*sum(1 for r in neg if r['none']>0)/len(neg):.0f}",
                 f"{100*sum(1 for r in pos if r['early_stop'])/len(pos):.0f} / {100*sum(1 for r in neg if r['early_stop'])/len(neg):.0f}",
                 f"{100*sum(1 for r in pos if r['consec']>0)/len(pos):.0f} / {100*sum(1 for r in neg if r['consec']>0)/len(neg):.0f}",
                 f"{auroc([r['n'] for r in pos],[r['n'] for r in neg]):.3f}", f"{auroc([r['none'] for r in pos],[r['none'] for r in neg]):.3f}",
                 f"{auroc([r['consec'] for r in pos],[r['consec'] for r in neg]):.3f}", f"{auroc([r['maxrep'] for r in pos],[r['maxrep'] for r in neg]):.3f}"])
P(md_table(['model', 'n fail', 'n pass', 'steps fail/pass', 'has none-action % f/p', 'early stop % f/p', 'consecutive repeat % f/p', 'AUROC n', 'AUROC none', 'AUROC consec', 'AUROC maxrep'], rows))
# early stop reasons
P('\nEarly-stop / stop strings in failed web runs:', collections.Counter(re.sub(r'\[.*', '', r['stop'])[:40] + ('[Early stop]' if 'Early stop' in r['stop'] else '') for r in recs if r['score'] is not None and r['score'] < 1).most_common(6))
P('Fail runs by (early-stop-by-parse, loop):', collections.Counter(('parse-early-stop' if 'parse' in r['stop'] else 'other-stop', 'consec-loop' if r['consec'] > 0 else 'no-loop') for r in recs if r['score'] is not None and r['score'] < 1))
# shared prefix: same model, same task, lower level pass vs higher level fail
P('\n## Shared action prefix: passing run at a lower level vs failing run at a higher level (same model, same task_id)\n')
by = collections.defaultdict(list)
for r in recs:
    if r['score'] is not None and r['level']: by[(r['model'], r['task'])].append(r)
pairs = []
for k, v in by.items():
    for a in v:
        for b in v:
            if a['score'] >= 1 and b['score'] < 1 and float(a['level']) < float(b['level']):
                lcp = 0
                for p, q in zip(a['acts'], b['acts']):
                    if p == q: lcp += 1
                    else: break
                pairs.append({'pass_id': a['id'], 'fail_id': b['id'], 'pass_n': a['n'], 'fail_n': b['n'], 'lcp': lcp, 'pass_level': a['level'], 'fail_level': b['level'],
                              'fail_label': d5.get(b['id'], {}).get('failure_step_number')})
P(f'pairs: {len(pairs)}')
if pairs:
    P(f"mean LCP {sum(p['lcp'] for p in pairs)/len(pairs):.2f}; LCP >= pass_n-1 (fail run reproduces the whole passing run): {sum(1 for p in pairs if p['lcp'] >= p['pass_n']-1)} ({100*sum(1 for p in pairs if p['lcp'] >= p['pass_n']-1)/len(pairs):.0f}%); LCP==0: {sum(1 for p in pairs if p['lcp']==0)}")
    lab = [p for p in pairs if p['fail_label'] is not None]
    P(f"pairs with a judge step label on the failing run: {len(lab)}; label <= LCP (judge blames a step the passing run also took): {sum(1 for p in lab if int(p['fail_label']) <= p['lcp'])}; label == LCP+1 (first divergent step): {sum(1 for p in lab if int(p['fail_label']) == p['lcp']+1)}; label > LCP+1: {sum(1 for p in lab if int(p['fail_label']) > p['lcp']+1)}")
    P('LCP distribution:', sorted(collections.Counter(p['lcp'] for p in pairs).items()))
json.dump(pairs, open(os.path.join(RESULTS, 'horizon', 'web_prefix_pairs.json'), 'w'), indent=1)
# label-step text signatures
P('\n## Label-step signatures (result_5)\n')
lab = []
for x in d5.values():
    fs = x.get('failure_step_number')
    if fs is None: continue
    s = parse(x['trajectory']); fs = int(fs)
    st = next((t for t in s if t['n'] == fs), None)
    if not st: continue
    acts = [norm(t['action']) for t in s]; i = next(i for i, t in enumerate(s) if t['n'] == fs)
    lab.append({'none': st['action'] in ('', 'none'), 'loop_start': i + 1 < len(acts) and acts[i] == acts[i + 1] and acts[i] not in ('', 'none'),
                'repeat_of_earlier': acts[i] in acts[:i] and acts[i] not in ('', 'none'), 'stop': st['action'].startswith('stop'), 'ft': x['failure_type']})
N = len(lab)
P(md_table(['signature of the labelled step', 'n', '%'], [
    ['Action: none (parse failure) at the label', sum(l['none'] for l in lab), f"{100*sum(l['none'] for l in lab)/N:.1f}"],
    ['label is first of an identical-action pair (loop start)', sum(l['loop_start'] for l in lab), f"{100*sum(l['loop_start'] for l in lab)/N:.1f}"],
    ['label repeats an earlier action', sum(l['repeat_of_earlier'] for l in lab), f"{100*sum(l['repeat_of_earlier'] for l in lab)/N:.1f}"],
    ['label is the stop action', sum(l['stop'] for l in lab), f"{100*sum(l['stop'] for l in lab)/N:.1f}"],
    ['none of the above (needs semantics)', sum(1 for l in lab if not (l['none'] or l['loop_start'] or l['repeat_of_earlier'] or l['stop'])), f"{100*sum(1 for l in lab if not (l['none'] or l['loop_start'] or l['repeat_of_earlier'] or l['stop']))/N:.1f}"]]))
with open(os.path.join(RESULTS, 'horizon', 'web_p6.md'), 'w') as fh: fh.write('\n'.join(out))
