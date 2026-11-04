#!/usr/bin/env python3
"""Web label signatures with id-stripped (but element-text-preserving) action normalisation; loop features for pass vs fail;
early-stop types. Writes results/horizon/web_labels.md"""
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
    blocks = re.split(r'^\[Step (\d+)\]\n', t, flags=re.M); steps = []
    for i in range(1, len(blocks), 2):
        b = blocks[i + 1]; a = re.search(r'^Action:\s*(.*)$', b, re.M); pg = re.search(r'^Page\s*:\s*(.*)$', b, re.M)
        steps.append({'n': int(blocks[i]), 'action': a.group(1).strip() if a else '', 'page': pg.group(1).strip() if pg else ''})
    return steps
def norm(a):
    a = re.sub(r'\[\d+\]', '', a); return re.sub(r'\s+', ' ', a).strip()[:120]
def auroc(pos, neg):
    return sum(1 if p > q else 0.5 if p == q else 0 for p in pos for q in neg) / (len(pos) * len(neg))
recs = []
for x in d2:
    if x['domain'] != 'web': continue
    s = parse(x['trajectory']); acts = [norm(t['action']) for t in s]
    try: sc = float(x.get('score'))
    except (TypeError, ValueError): continue
    stop = s[-1]['action'] if s else ''
    recs.append({'model': x['model'], 'fail': sc < 1, 'n': len(s), 'consec': sum(1 for a, b in zip(acts, acts[1:]) if a == b and a not in ('', 'none')),
                 'maxrep': max((v for k, v in collections.Counter(acts).items() if k not in ('', 'none')), default=0),
                 'none': sum(1 for a in acts if a in ('', 'none')), 'page_rep': max(collections.Counter(t['page'] for t in s).values()) if s else 0,
                 'stop_type': 'parse-early-stop' if 'parse' in stop else 'max-steps-early-stop' if 'Early stop' in stop else 'stop[answer]' if stop.startswith('stop') else 'other'})
P('## Web pass vs fail (score), id-stripped actions\n')
rows = []
for m in ('gpt', 'claude', 'all'):
    v = [r for r in recs if m == 'all' or r['model'] == m]; pos = [r for r in v if r['fail']]; neg = [r for r in v if not r['fail']]
    rows.append([m, len(pos), len(neg), f"{100*sum(1 for r in pos if r['consec']>0)/len(pos):.0f} / {100*sum(1 for r in neg if r['consec']>0)/len(neg):.0f}",
                 f"{100*sum(1 for r in pos if r['maxrep']>=3)/len(pos):.0f} / {100*sum(1 for r in neg if r['maxrep']>=3)/len(neg):.0f}",
                 f"{100*sum(1 for r in pos if r['none']>0)/len(pos):.0f} / {100*sum(1 for r in neg if r['none']>0)/len(neg):.0f}",
                 f"{auroc([r['n'] for r in pos],[r['n'] for r in neg]):.3f}", f"{auroc([r['consec'] for r in pos],[r['consec'] for r in neg]):.3f}", f"{auroc([r['maxrep'] for r in pos],[r['maxrep'] for r in neg]):.3f}", f"{auroc([r['none'] for r in pos],[r['none'] for r in neg]):.3f}"])
P(md_table(['model', 'n fail', 'n pass', 'consecutive identical action % f/p', 'same action >=3x % f/p', 'has none % f/p', 'AUROC n_steps', 'AUROC consec', 'AUROC maxrep', 'AUROC none'], rows))
P('\nstop type x outcome:'); P(collections.Counter((r['stop_type'], 'fail' if r['fail'] else 'pass') for r in recs))
P('\n## Label-step signatures (result_5, 294 labels), id-stripped actions\n')
lab = []
for x in d5.values():
    fs = x.get('failure_step_number')
    if fs is None: continue
    s = parse(x['trajectory']); fs = int(fs); acts = [norm(t['action']) for t in s]
    i = next((i for i, t in enumerate(s) if t['n'] == fs), None)
    if i is None: continue
    a = acts[i]
    none = a in ('', 'none')
    loop_start = (not none) and i + 1 < len(acts) and acts[i + 1] == a
    rep_earlier = (not none) and a in acts[:i]
    first_rep3 = next((j for j in range(len(acts)) if acts[j] not in ('', 'none') and acts[:j + 1].count(acts[j]) == 3), None)
    first_consec = next((j for j in range(1, len(acts)) if acts[j] == acts[j - 1] and acts[j] not in ('', 'none')), None)
    first_none = next((j for j in range(len(acts)) if acts[j] in ('', 'none')), None)
    # first "anomaly" = earliest of (first consecutive repeat start, first none)
    cands = [c for c in (first_consec - 1 if first_consec is not None else None, first_none) if c is not None]
    first_anom = min(cands) if cands else None
    lab.append({'ft': x['failure_type'], 'none': none, 'loop_start': loop_start, 'rep_earlier': rep_earlier, 'stop': s[i]['action'].startswith('stop'),
                'i': i, 'n': len(s), 'first_anom': first_anom, 'd_anom': (i - first_anom) if first_anom is not None else None,
                'first_consec_start': first_consec - 1 if first_consec is not None else None, 'first_none': first_none})
N = len(lab)
def pct(k): return f"{100*k/N:.1f}"
P(md_table(['signature of the labelled step', 'n', '%'], [
    ['Action: none (unparseable action)', sum(l['none'] for l in lab), pct(sum(l['none'] for l in lab))],
    ['first of two identical consecutive actions (loop start)', sum(l['loop_start'] for l in lab), pct(sum(l['loop_start'] for l in lab))],
    ['repeats an action taken earlier (non-consecutive)', sum(l['rep_earlier'] and not l['loop_start'] for l in lab), pct(sum(l['rep_earlier'] and not l['loop_start'] for l in lab))],
    ['is the stop action', sum(l['stop'] for l in lab), pct(sum(l['stop'] for l in lab))],
    ['none of these (needs semantics)', sum(1 for l in lab if not (l['none'] or l['loop_start'] or l['rep_earlier'] or l['stop'])), pct(sum(1 for l in lab if not (l['none'] or l['loop_start'] or l['rep_earlier'] or l['stop'])))]]))
P('\nLabel vs first syntactic anomaly (earliest of: start of first identical-consecutive pair, first none):')
P(md_table(['relation', 'n', '%'], [
    ['no syntactic anomaly in run', sum(1 for l in lab if l['first_anom'] is None), pct(sum(1 for l in lab if l['first_anom'] is None))],
    ['label == first anomaly', sum(1 for l in lab if l['d_anom'] == 0), pct(sum(1 for l in lab if l['d_anom'] == 0))],
    ['label BEFORE first anomaly (judge earlier than syntax)', sum(1 for l in lab if l['d_anom'] is not None and l['d_anom'] < 0), pct(sum(1 for l in lab if l['d_anom'] is not None and l['d_anom'] < 0))],
    ['label 1-3 after first anomaly', sum(1 for l in lab if l['d_anom'] is not None and 1 <= l['d_anom'] <= 3), pct(sum(1 for l in lab if l['d_anom'] is not None and 1 <= l['d_anom'] <= 3))],
    ['label >3 after first anomaly', sum(1 for l in lab if l['d_anom'] is not None and l['d_anom'] > 3), pct(sum(1 for l in lab if l['d_anom'] is not None and l['d_anom'] > 3))]]))
P('d_anom distribution (label - first anomaly):', sorted(collections.Counter(l['d_anom'] for l in lab).items(), key=lambda kv: (kv[0] is None, kv[0])))
P('by failure_type: label==first anomaly:', {ft: f"{sum(1 for l in lab if l['ft']==ft and l['d_anom']==0)}/{sum(1 for l in lab if l['ft']==ft)}" for ft in set(l['ft'] for l in lab)})
with open(os.path.join(RESULTS, 'horizon', 'web_labels.md'), 'w') as fh: fh.write('\n'.join(out))
