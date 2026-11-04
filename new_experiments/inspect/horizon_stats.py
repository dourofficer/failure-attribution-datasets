#!/usr/bin/env python3
"""HORIZON targeted statistics (G3): env-vs-judge disagreement, judge self-consistency (result_2 vs result_3),
where the judge's failure_step_number sits (last step / last-5 / loop start / judge window), OS error signs.
Writes results/horizon/stats.md and results/horizon/disagreements.jsonl."""
import json, os, re, sys, collections, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, DATA, md_table, append_jsonl  # noqa
from loaders import load  # noqa

R = os.path.join(DATA, 'horizon', 'hf')
d2 = json.load(open(os.path.join(R, 'result_2', 'classified_results.json')))
d3 = {x['id']: x for x in json.load(open(os.path.join(R, 'result_3', 'classified_results.json')))}
d5 = {x['id']: x for x in json.load(open(os.path.join(R, 'result_5', 'classified_results.json')))}
out = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)

def env(x):
    p = x.get('passed'); s = x.get('score')
    if isinstance(p, str): p = {'true': True, 'false': False}.get(p.lower())
    if p is not None: return 'pass' if p else 'fail'
    try: return 'pass' if float(s) >= 1 else 'fail'
    except (TypeError, ValueError): return None
def judge(x): return 'pass' if x.get('failure_type') == 'Success' else 'fail'
def level(x):
    r = str(x.get('run', ''))
    m = re.search(r'step_(\d+)', r) or re.search(r'(\d+)', r.split('/')[-1])
    return m.group(1) if m else r
def nsteps(x):
    t = x.get('trajectory') or ''
    if x['domain'] == 'web': return len(re.findall(r'^\[Step \d+\]', t, re.M))
    if x['domain'] == 'os': return len(re.findall(r'^\[Agent\]', t, re.M))
    return 1

# ---- 1. env vs judge
P('## 1. Environment verdict vs judge (result_2)\n')
rows = []
for key in ['domain', 'model']:
    c = collections.defaultdict(collections.Counter)
    for x in d2:
        e = env(x)
        if e is None: continue
        c[x[key]][(e, judge(x))] += 1
    for k, cc in sorted(c.items()):
        n = sum(cc.values()); dis = cc[('pass', 'fail')] + cc[('fail', 'pass')]
        rows.append([f'{key}={k}', n, cc[('pass','pass')], cc[('fail','fail')], cc[('pass','fail')], cc[('fail','pass')], f'{100*dis/n:.1f}'])
P(md_table(['group', 'n', 'both pass', 'both fail', 'env pass / judge FAIL', 'env fail / judge SUCCESS', 'disagree %'], rows))
# by os level
P('\nOS by level (env pass/judge fail = EPJF, env fail/judge success = EFJS):')
c = collections.defaultdict(collections.Counter)
for x in d2:
    if x['domain'] != 'os': continue
    c[level(x)][(env(x), judge(x))] += 1
rows = [[lv, sum(cc.values()), cc[('pass','fail')], cc[('fail','pass')], f"{100*(cc[('pass','fail')]+cc[('fail','pass')])/sum(cc.values()):.1f}"] for lv, cc in sorted(c.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 99)]
P(md_table(['level', 'n', 'EPJF', 'EFJS', 'disagree %'], rows))
# judge label on env-pass runs
P('\nJudge failure_type given to env-PASS runs (web+os+db):')
cc = collections.Counter(x['failure_type'] for x in d2 if env(x) == 'pass' and judge(x) == 'fail')
P(dict(cc))
# dump disagreements
dp = os.path.join(RESULTS, 'horizon', 'disagreements.jsonl')
if os.path.exists(dp): os.remove(dp)
for x in d2:
    e = env(x)
    if e and e != judge(x):
        append_jsonl(dp, {'id': x['id'], 'domain': x['domain'], 'model': x['model'], 'env': e, 'judge': x['failure_type'], 'reason': x['reason'],
                          'r3': d3[x['id']]['failure_type'], 'r3_reason': d3[x['id']]['reason'], 'n_steps': nsteps(x), 'level': level(x)})

# ---- 2. result_2 vs result_3
P('\n## 2. Judge self-consistency: result_2 vs result_3\n')
rows = []
groups = collections.defaultdict(list)
for x in d2:
    y = d3[x['id']]
    same = x['failure_type'] == y['failure_type']
    samebin = judge(x) == judge(y)
    e = env(x)
    agree_env2 = (e == judge(x)) if e else None
    n = nsteps(x)
    lb = '1-5' if n <= 5 else '6-15' if n <= 15 else '16-30' if n <= 30 else '>30'
    for g in [('domain', x['domain']), ('model', x['model']), ('env', e), ('len', lb), ('level', x['domain'] + ':' + level(x))]:
        groups[g].append((same, samebin, agree_env2, e))
for g, v in sorted(groups.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
    n = len(v)
    rows.append([f'{g[0]}={g[1]}', n, f'{100*sum(a for a,_,_,_ in v)/n:.1f}', f'{100*sum(b for _,b,_,_ in v)/n:.1f}'])
P(md_table(['group', 'n', 'exact label agree %', 'pass/fail agree %'], rows))
# confusion matrix of labels r2 x r3
conf = collections.Counter((x['failure_type'], d3[x['id']]['failure_type']) for x in d2 if x['failure_type'] != d3[x['id']]['failure_type'])
P('\nTop label confusions (r2 -> r3):'); P(conf.most_common(12))
# when r2 and r3 disagree on pass/fail, who agrees with env?
agree = collections.Counter()
for x in d2:
    y = d3[x['id']]; e = env(x)
    if e and judge(x) != judge(y):
        agree['r2 matches env' if judge(x) == e else 'r3 matches env'] += 1
P('\nr2/r3 pass-fail splits, who matches env:', dict(agree))
# env disagreement: is it stable across passes? (both passes disagree with env)
both = sum(1 for x in d2 if env(x) and env(x) != judge(x) and env(x) != judge(d3[x['id']]))
one = sum(1 for x in d2 if env(x) and env(x) != judge(x))
P(f'r2 disagrees with env: {one}; of these r3 ALSO disagrees with env: {both} ({100*both/max(1,one):.1f}%) -> stable judge-vs-env disagreement')
# r1 as third pass
d1 = {x['id']: x for x in json.load(open(os.path.join(R, 'result_1', 'classified_results.json')))}
common = [x for x in d2 if x['id'] in d1]
P(f'result_1 overlaps result_2 on {len(common)} ids; exact agree r1-r2 {100*sum(1 for x in common if x["failure_type"]==d1[x["id"]]["failure_type"])/max(1,len(common)):.1f}%, pass/fail agree {100*sum(1 for x in common if judge(x)==judge(d1[x["id"]]))/max(1,len(common)):.1f}%')
# r5 vs r2 on shared web ids
sh = [x for x in d2 if x['id'] in d5]
P(f'result_5 overlaps result_2 on {len(sh)} ids; exact agree {100*sum(1 for x in sh if x["failure_type"]==d5[x["id"]]["failure_type"])/max(1,len(sh)):.1f}%, pass/fail {100*sum(1 for x in sh if judge(x)==judge(d5[x["id"]]))/max(1,len(sh)):.1f}%')

# ---- 3. step labels (result_5)
P('\n## 3. Where the judge puts failure_step_number (result_5, web/GPT)\n')
rows5 = []
for x in d5.values():
    fs = x.get('failure_step_number')
    if fs is None: continue
    try: fs = int(fs)
    except (TypeError, ValueError): continue
    t = x['trajectory']
    blocks = re.split(r'^\[Step (\d+)\]\n', t, flags=re.M)
    steps = {int(blocks[i]): blocks[i+1] for i in range(1, len(blocks), 2)}
    n = len(steps); last = max(steps) if steps else 0
    actions = {k: (re.search(r'^Action:\s*(.*)$', v, re.M).group(1).strip() if re.search(r'^Action:\s*(.*)$', v, re.M) else '') for k, v in steps.items()}
    # loop: first step k such that actions[k]==actions[k-1] (identical consecutive)
    loop_first = next((k for k in sorted(steps) if k > 1 and actions.get(k) and actions[k] == actions.get(k-1)), None)
    # first repeat of any earlier action
    seen = {}; rep_first = None
    for k in sorted(steps):
        a = actions[k]
        if a and a in seen and rep_first is None: rep_first = k
        seen.setdefault(a, k)
    none_first = next((k for k in sorted(steps) if actions[k] in ('none', '') ), None)
    stop_step = next((k for k in sorted(steps) if actions[k].startswith('stop')), None)
    win = x.get('steps') or []
    winlabels = [w.get('label') for w in win]
    win_raw_steps = []
    for w in win:
        m = re.search(r'\[Step (\d+)\]', w.get('raw') or '')
        win_raw_steps.append(int(m.group(1)) if m else None)
    fail_pos_in_win = next((i for i, l in enumerate(winlabels) if 'FAILURE' in (l or '')), None)
    rows5.append(dict(id=x['id'], fs=fs, n=n, last=last, score=x.get('score'), ft=x['failure_type'], loop_first=loop_first, rep_first=rep_first,
                      none_first=none_first, stop_step=stop_step, win=win_raw_steps, win_fail_pos=fail_pos_in_win, nwin=len(win), action=actions.get(fs, '')[:80],
                      in_range=fs in steps))
N = len(rows5)
P(f'labelled records: {N}; in-range: {sum(r["in_range"] for r in rows5)}')
P(md_table(['statistic', 'n', '%'], [
    ['label == last step', sum(r['fs'] == r['last'] for r in rows5), f'{100*sum(r["fs"]==r["last"] for r in rows5)/N:.1f}'],
    ['label within last 5 steps', sum(r['fs'] >= r['last'] - 4 for r in rows5), f'{100*sum(r["fs"]>=r["last"]-4 for r in rows5)/N:.1f}'],
    ['label in first 5 steps', sum(r['fs'] <= 5 for r in rows5), f'{100*sum(r["fs"]<=5 for r in rows5)/N:.1f}'],
    ['label == 1', sum(r['fs'] == 1 for r in rows5), f'{100*sum(r["fs"]==1 for r in rows5)/N:.1f}'],
    ['run has a consecutive identical-action loop', sum(r['loop_first'] is not None for r in rows5), f'{100*sum(r["loop_first"] is not None for r in rows5)/N:.1f}'],
    ['  label == first loop step (2nd identical action)', sum(r['loop_first'] == r['fs'] for r in rows5), ''],
    ['  label == loop step - 1 (first of the pair)', sum(r['loop_first'] is not None and r['loop_first'] - 1 == r['fs'] for r in rows5), ''],
    ['  label before loop start-1', sum(r['loop_first'] is not None and r['fs'] < r['loop_first'] - 1 for r in rows5), ''],
    ['  label after loop start', sum(r['loop_first'] is not None and r['fs'] > r['loop_first'] for r in rows5), ''],
    ['run has any repeated action', sum(r['rep_first'] is not None for r in rows5), ''],
    ['  label <= first repeat', sum(r['rep_first'] is not None and r['fs'] <= r['rep_first'] for r in rows5), ''],
    ['run has an empty/none action', sum(r['none_first'] is not None for r in rows5), ''],
    ['  label == first none action', sum(r['none_first'] == r['fs'] for r in rows5), ''],
    ['run ends with stop[...]', sum(r['stop_step'] is not None for r in rows5), ''],
    ['  label == stop step', sum(r['stop_step'] == r['fs'] for r in rows5), ''],
    ['judge window (steps field) non-empty', sum(r['nwin'] > 0 for r in rows5), ''],
    ['  window = 5 steps', sum(r['nwin'] == 5 for r in rows5), ''],
    ['  window ends at last step', sum(bool(r['win']) and r['win'][-1] == r['last'] for r in rows5), ''],
    ['  window centred on label (fail at pos 3 of 5)', sum(r['win_fail_pos'] == 2 for r in rows5), ''],
    ['  window first step == label (fail at pos 1)', sum(r['win_fail_pos'] == 0 for r in rows5), ''],
]))
P('\nfail position inside window:', collections.Counter(r['win_fail_pos'] for r in rows5))
P('rel position (fs/last) deciles:', collections.Counter(min(9, int(10 * r['fs'] / max(1, r['last']))) for r in rows5))
P('label step action type:', collections.Counter(re.split(r'[ \[]', r['action'])[0] for r in rows5).most_common(10))
P('failure_type x (label==last):', collections.Counter((r['ft'], r['fs'] == r['last']) for r in rows5))
P('score of labelled records:', collections.Counter(str(r['score']) for r in rows5))
json.dump(rows5, open(os.path.join(RESULTS, 'horizon', 'step_labels.json'), 'w'), indent=1)

# ---- 4. OS error signs
P('\n## 4. OS runs: visible error signs vs judge label\n')
pat = re.compile(r'(Permission denied|command not found|No such file|syntax error|cannot |not found|Error|error:|Operation not permitted|Invalid)', re.I)
rows = collections.defaultdict(lambda: collections.Counter())
for x in d2:
    if x['domain'] != 'os': continue
    t = x['trajectory']
    parts = re.split(r'^\[(Task|Agent|OS response)\]\n', t, flags=re.M)
    agents = []; resps = []
    for i in range(1, len(parts) - 1, 2):
        if parts[i] == 'Agent': agents.append(parts[i+1].strip())
        elif parts[i] == 'OS response': resps.append(parts[i+1].strip())
    err_resp = sum(1 for r in resps if pat.search(r))
    cmds = [re.search(r'```(?:bash)?\n(.*?)```', a, re.S).group(1).strip() if re.search(r'```(?:bash)?\n(.*?)```', a, re.S) else a[:100] for a in agents]
    rep = len(cmds) - len(set(cmds))
    has_answer = any('answer(' in a for a in agents)
    has_finish = any('finish' in a.lower()[-200:] for a in agents)
    key = (env(x), x['failure_type'])
    c = rows[key]; c['n'] += 1; c['err_resp>0'] += err_resp > 0; c['repeat>0'] += rep > 0; c['has_answer'] += has_answer; c['n_agent_sum'] += len(agents); c['err_sum'] += err_resp
P(md_table(['env', 'judge', 'n', 'runs with >=1 error-looking OS response %', 'runs with repeated command %', 'runs with answer() %', 'mean agent turns', 'mean error responses'],
    [[k[0], k[1], c['n'], f'{100*c["err_resp>0"]/c["n"]:.0f}', f'{100*c["repeat>0"]/c["n"]:.0f}', f'{100*c["has_answer"]/c["n"]:.0f}', f'{c["n_agent_sum"]/c["n"]:.1f}', f'{c["err_sum"]/c["n"]:.1f}'] for k, c in sorted(rows.items(), key=lambda kv: (str(kv[0][0]), kv[0][1]))]))
# CF label vs length and level
P('\nCatastrophic Forgetting rate by OS level and by length bin (judge r2, failed-by-judge runs only):')
c = collections.defaultdict(collections.Counter)
for x in d2:
    if x['domain'] != 'os' or judge(x) == 'pass': continue
    n = nsteps(x); lb = '1-5' if n <= 5 else '6-10' if n <= 10 else '11-20' if n <= 20 else '>20'
    c['len=' + lb][x['failure_type'] == 'Catastrophic Forgetting'] += 1
    c['level=' + level(x).zfill(2)][x['failure_type'] == 'Catastrophic Forgetting'] += 1
    c['model=' + x['model']][x['failure_type'] == 'Catastrophic Forgetting'] += 1
P(md_table(['group', 'n judged-fail', 'CF %'], [[k, sum(v.values()), f'{100*v[True]/sum(v.values()):.1f}'] for k, v in sorted(c.items())]))
# length of judge reason mentioning words
P('\nJudge reason keyword rates for CF labels (os):')
cfr = [x['reason'] for x in d2 if x['domain'] == 'os' and x['failure_type'] == 'Catastrophic Forgetting']
for kw in ['forgot', 'forget', 'ignored', 'never', 'did not', 'skipped', 'loop', 'repeat', 'answer']:
    P(f'  {kw}: {100*sum(1 for r in cfr if kw in r.lower())/max(1,len(cfr)):.0f}%')
with open(os.path.join(RESULTS, 'horizon', 'stats.md'), 'w') as fh: fh.write('\n'.join(out))
