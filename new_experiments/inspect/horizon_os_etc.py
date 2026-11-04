#!/usr/bin/env python3
"""OS one-shot-example contamination: does the final answer / late commands talk about /etc or 'files in /etc' when the task
does not mention /etc? By model, env verdict and judge label. Writes results/horizon/os_etc.md"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, DATA, md_table  # noqa
R = os.path.join(DATA, 'horizon', 'hf')
d2 = json.load(open(os.path.join(R, 'result_2', 'classified_results.json')))
d3 = {x['id']: x for x in json.load(open(os.path.join(R, 'result_3', 'classified_results.json')))}
out = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)
def env(x):
    p = x.get('passed')
    if isinstance(p, str): p = {'true': True, 'false': False}.get(p.lower())
    return 'pass' if p else 'fail'
# find the one-shot example text in a raw run
ex = None
for f in [os.path.join(R, 'os', 'run_0', 'gpt-5-mini', 'os-std-aug-clear-filtered-1', 'runs.jsonl')]:
    if os.path.exists(f):
        d = json.loads(open(f).readline()); h = d['output']['history']
        sysmsg = h[0]['content']
        m = re.search(r'(example|Example)[\s\S]{0,1500}', sysmsg)
        ex = sysmsg
P('System prompt excerpt around the one-shot example:')
i = ex.find('/etc') if ex else -1
P((ex[max(0, i - 900): i + 600] if i >= 0 else 'no /etc in system prompt').replace('\n', ' | '))
rows = collections.defaultdict(collections.Counter)
drift = []
for x in d2:
    if x['domain'] != 'os': continue
    t = x['trajectory']
    task = re.split(r'^\[Agent\]', t, flags=re.M)[0]
    task_etc = '/etc' in task
    agents = re.findall(r'^\[Agent\]\n(.*?)(?=^\[OS response\]|\Z)', t, flags=re.M | re.S)
    last = agents[-1] if agents else ''
    ans = re.search(r'answer\((.*)\)\s*$', last, re.S)
    ans_txt = ans.group(1) if ans else ''
    ans_etc = '/etc' in ans_txt or 'files in /etc' in last
    cmd_etc = sum(1 for a in agents if re.search(r'```(?:bash)?\n[^`]*\/etc', a))
    key = (x['model'], env(x))
    c = rows[key]; c['n'] += 1
    if not task_etc:
        c['task_no_etc'] += 1; c['ans_etc'] += ans_etc; c['cmd_etc'] += cmd_etc > 0
        if ans_etc or cmd_etc:
            drift.append({'id': x['id'], 'model': x['model'], 'env': env(x), 'judge': x['failure_type'], 'r3': d3[x['id']]['failure_type'], 'ans': ans_txt[:80], 'n_cmd_etc': cmd_etc,
                          'first_etc_turn': next((i + 1 for i, a in enumerate(agents) if re.search(r'```(?:bash)?\n[^`]*\/etc', a)), None), 'n_turns': len(agents)})
P('\n## /etc drift in runs whose task does not mention /etc\n')
P(md_table(['model', 'env', 'n', 'task w/o /etc', 'final answer mentions /etc', '%', 'any /etc command', '%'],
           [[k[0], k[1], c['n'], c['task_no_etc'], c['ans_etc'], f"{100*c['ans_etc']/max(1,c['task_no_etc']):.1f}", c['cmd_etc'], f"{100*c['cmd_etc']/max(1,c['task_no_etc']):.1f}"] for k, c in sorted(rows.items())]))
P('\nJudge label (r2) of drifted runs (answer mentions /etc, task does not):')
P(collections.Counter((d['model'], d['judge']) for d in drift if '/etc' in d['ans']).most_common(10))
P('r3 label of the same runs:', collections.Counter((d['model'], d['r3']) for d in drift if '/etc' in d['ans']).most_common(6))
P('\nWhen does the first /etc command appear (relative position in run) for drifted runs:')
rel = [d['first_etc_turn'] / d['n_turns'] for d in drift if d['first_etc_turn']]
P(f"n={len(rel)}, mean rel {sum(rel)/max(1,len(rel)):.2f}, share in last third {100*sum(1 for r in rel if r > 0.66)/max(1,len(rel)):.0f}%, share at turn 1 {100*sum(1 for d in drift if d['first_etc_turn']==1)/max(1,len(rel)):.0f}%")
P('\nShare of all GPT env-fail runs explained by /etc drift (answer mentions /etc while task does not):',
  f"{sum(1 for d in drift if d['model']=='gpt' and d['env']=='fail' and '/etc' in d['ans'])} / {sum(c['n'] for k, c in rows.items() if k==('gpt','fail'))}")
P('Share of GPT Catastrophic-Forgetting labels that are /etc drift:',
  f"{sum(1 for d in drift if d['model']=='gpt' and d['judge']=='Catastrophic Forgetting' and '/etc' in d['ans'])} / {sum(1 for x in d2 if x['domain']=='os' and x['model']=='gpt' and x['failure_type']=='Catastrophic Forgetting')}")
json.dump(drift, open(os.path.join(RESULTS, 'horizon', 'os_etc_drift.json'), 'w'), indent=1)
with open(os.path.join(RESULTS, 'horizon', 'os_etc.md'), 'w') as fh: fh.write('\n'.join(out))
