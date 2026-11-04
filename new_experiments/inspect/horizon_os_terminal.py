#!/usr/bin/env python3
"""OS terminal-action analysis: Claude 'finish' instead of 'answer' (task asks for an answer? value already computed?);
GPT drift precursors (turns before first /etc command, empty-output share before drift). Writes results/horizon/os_terminal.md"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, DATA, md_table  # noqa
R = os.path.join(DATA, 'horizon', 'hf')
d2 = json.load(open(os.path.join(R, 'result_2', 'classified_results.json')))
out = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)
def env(x):
    p = x.get('passed')
    if isinstance(p, str): p = {'true': True, 'false': False}.get(p.lower())
    return 'pass' if p else 'fail'
rows = collections.defaultdict(collections.Counter)
drift_rows = []
for x in d2:
    if x['domain'] != 'os': continue
    t = x['trajectory']
    task = re.split(r'^\[Agent\]', t, flags=re.M)[0]
    parts = re.split(r'^\[(Task|Agent|OS response)\]\n', t, flags=re.M)
    turns = []; cur = None
    for i in range(1, len(parts) - 1, 2):
        if parts[i] == 'Agent': cur = {'a': parts[i + 1], 'r': ''}; turns.append(cur)
        elif parts[i] == 'OS response' and cur: cur['r'] = parts[i + 1]
    last = turns[-1]['a'] if turns else ''
    finish = bool(re.search(r'Act:\s*finish', last)); answer = bool(re.search(r'Act:\s*answer\(', last))
    asks_answer = bool(re.search(r'answer|integer|return|output should be|tell me|how many|what is', task, re.I))
    asks_answer_strict = bool(re.search(r'(your answer|provide .{0,30}answer|answer (should|must)|return [\'"]?(yes|no)|single integer|form of an integer|output .{0,20}integer|how many|tell me)', task, re.I))
    num_in_last_think = bool(re.search(r'\b\d+\b', re.sub(r'```.*?```', '', last, flags=re.S)))
    k = (x['model'], env(x)); c = rows[k]; c['n'] += 1
    if finish:
        c['finish'] += 1; c['finish&asks'] += asks_answer_strict; c['finish&asks&num'] += asks_answer_strict and num_in_last_think
    c['asks'] += asks_answer_strict
    # drift precursors (GPT & Claude)
    if '/etc' not in task:
        fi = next((i for i, tr in enumerate(turns) if re.search(r'```(?:bash)?\n[^`]*\/etc', tr['a'])), None)
        if fi is not None:
            before = turns[:fi]
            cmds = [re.search(r'```(?:bash)?\n(.*?)```', tr['a'], re.S).group(1).strip() if re.search(r'```(?:bash)?\n(.*?)```', tr['a'], re.S) else '' for tr in before]
            drift_rows.append({'model': x['model'], 'env': env(x), 'fi': fi, 'n': len(turns), 'empty_before': sum(1 for tr in before if 'output of the OS is empty' in tr['r']),
                               'rep_before': len(cmds) - len(set(cmds)), 'last3_empty': all('output of the OS is empty' in tr['r'] for tr in before[-3:]) if len(before) >= 3 else None,
                               'judge': x['failure_type']})
P('## Terminal action: finish without answer\n')
P(md_table(['model', 'env', 'n', 'ends with finish', 'task asks for an answer (strict regex)', 'finish & task asks answer', 'finish & asks & a number in the final Think'],
           [[k[0], k[1], c['n'], c['finish'], c['asks'], c['finish&asks'], c['finish&asks&num']] for k, c in sorted(rows.items())]))
P('\n## Drift to the /etc one-shot example: precursors\n')
for m in ('gpt', 'claude'):
    v = [d for d in drift_rows if d['model'] == m]
    if not v: continue
    P(f"{m}: n={len(v)}; drift turn index mean {sum(d['fi'] for d in v)/len(v):.1f} of {sum(d['n'] for d in v)/len(v):.1f} turns; turns after drift mean {sum(d['n']-d['fi'] for d in v)/len(v):.1f}; "
      f"empty-output share before drift {100*sum(d['empty_before'] for d in v)/max(1,sum(d['fi'] for d in v)):.0f}%; runs with >=1 repeated command before drift {100*sum(1 for d in v if d['rep_before']>0)/len(v):.0f}%; "
      f"last 3 turns before drift all empty-output {100*sum(1 for d in v if d['last3_empty'])/max(1,sum(1 for d in v if d['last3_empty'] is not None)):.0f}%")
    P('   turns-after-drift distribution:', sorted(collections.Counter(min(d['n'] - d['fi'], 6) for d in v).items()))
# all GPT fails: empty-output share overall for comparison
allg = [x for x in d2 if x['domain'] == 'os' and x['model'] == 'gpt']
tot = 0; emp = 0
for x in allg:
    rs = re.findall(r'^\[OS response\]\n(.*?)(?=^\[Agent\]|\Z)', x['trajectory'], flags=re.M | re.S); tot += len(rs); emp += sum(1 for r in rs if 'output of the OS is empty' in r)
P(f"\nGPT OS: overall empty-output share {100*emp/max(1,tot):.0f}% (all runs)")
with open(os.path.join(RESULTS, 'horizon', 'os_terminal.md'), 'w') as fh: fh.write('\n'.join(out))
