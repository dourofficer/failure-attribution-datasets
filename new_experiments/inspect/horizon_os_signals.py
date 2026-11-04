#!/usr/bin/env python3
"""OS-domain signal analysis for HORIZON: empty-output rate, repeated commands, answer-format mismatch, by env verdict
and judge label; AUROC of cheap trajectory features for env pass vs fail (P6 'normal flow' test). Writes results/horizon/os_signals.md"""
import json, os, re, sys, collections, itertools
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
    if p is not None: return 'pass' if p else 'fail'
    try: return 'pass' if float(x.get('score')) >= 1 else 'fail'
    except (TypeError, ValueError): return None
def cf(x):
    m = re.search(r'aug-cf(\d+)-', x['id']); return int(m.group(1)) if m else None
SHOULD_OUTPUT = re.compile(r'^\s*(pwd|ls\b|cat\b|echo\b|wc\b|head\b|tail\b|find\b|grep\b|date\b|whoami|id\b|df\b|du\b|stat\b|printenv|env\b|which\b)')
feats = []
for x in d2:
    if x['domain'] != 'os': continue
    t = x['trajectory']
    parts = re.split(r'^\[(Task|Agent|OS response)\]\n', t, flags=re.M)
    task = ''; turns = []
    cur = None
    for i in range(1, len(parts) - 1, 2):
        k, body = parts[i], parts[i + 1].strip()
        if k == 'Task': task = body
        elif k == 'Agent': cur = {'agent': body, 'resp': None}; turns.append(cur)
        elif k == 'OS response' and cur is not None: cur['resp'] = body
    cmds = []
    for tr in turns:
        m = re.search(r'```(?:bash)?\n(.*?)```', tr['agent'], re.S)
        tr['cmd'] = m.group(1).strip() if m else None
        tr['empty'] = tr['resp'] is not None and 'output of the OS is empty' in tr['resp']
        tr['err'] = tr['resp'] is not None and bool(re.search(r'(Permission denied|command not found|No such file|syntax error|cannot |not found|Error|error:|Operation not permitted|Invalid)', tr['resp'], re.I))
        tr['trunc'] = tr['resp'] is not None and 'truncated' in tr['resp']
    cmds = [tr['cmd'] for tr in turns if tr['cmd']]
    n = len(turns)
    n_empty_should = sum(1 for tr in turns if tr['cmd'] and SHOULD_OUTPUT.match(tr['cmd']) and tr['empty'])
    n_should = sum(1 for tr in turns if tr['cmd'] and SHOULD_OUTPUT.match(tr['cmd']))
    pwd_empty = sum(1 for tr in turns if tr['cmd'] and tr['cmd'].strip() == 'pwd' and tr['empty'])
    pwd_n = sum(1 for tr in turns if tr['cmd'] and tr['cmd'].strip() == 'pwd')
    rep = len(cmds) - len(set(cmds))
    maxrep = max(collections.Counter(cmds).values()) if cmds else 0
    consec = sum(1 for a, b in zip(cmds, cmds[1:]) if a == b)
    last = turns[-1]['agent'] if turns else ''
    ans = re.search(r'answer\((.*)\)\s*$', last, re.S)
    finish = bool(re.search(r'Act:\s*finish', last))
    ans_txt = ans.group(1).strip() if ans else None
    # expected format from the (original) question
    q = task
    wants_yesno = bool(re.search(r"'yes'|'no'|yes or no|yes/no", q, re.I))
    wants_int = bool(re.search(r'integer|a single number|as a number|numeric', q, re.I))
    fmt_mismatch = None
    if ans_txt is not None:
        if wants_yesno: fmt_mismatch = ans_txt.strip().strip("'\"").lower() not in ('yes', 'no')
        elif wants_int: fmt_mismatch = not re.fullmatch(r'-?\d+', ans_txt.strip().strip("'\""))
    feats.append({'id': x['id'], 'model': x['model'], 'cf': cf(x), 'env': env(x), 'judge': x['failure_type'], 'n': n, 'n_err': sum(tr['err'] for tr in turns),
                  'n_empty': sum(tr['empty'] for tr in turns), 'n_empty_should': n_empty_should, 'n_should': n_should, 'pwd_empty': pwd_empty, 'pwd_n': pwd_n,
                  'rep': rep, 'maxrep': maxrep, 'consec': consec, 'has_answer': ans is not None, 'finish': finish, 'fmt_mismatch': fmt_mismatch,
                  'n_trunc': sum(tr['trunc'] for tr in turns), 'ans': (ans_txt or '')[:60]})
json.dump(feats, open(os.path.join(RESULTS, 'horizon', 'os_features.json'), 'w'))
N = len(feats)
P('## OS environment quirk: commands that should print something return "output is empty"\n')
P(f"pwd calls: {sum(f['pwd_n'] for f in feats)}, of which empty: {sum(f['pwd_empty'] for f in feats)} ({100*sum(f['pwd_empty'] for f in feats)/max(1,sum(f['pwd_n'] for f in feats)):.0f}%)")
P(f"commands matching ls/cat/echo/wc/find/grep/...: {sum(f['n_should'] for f in feats)}, empty: {sum(f['n_empty_should'] for f in feats)} ({100*sum(f['n_empty_should'] for f in feats)/max(1,sum(f['n_should'] for f in feats)):.0f}%)")
P(f"runs with >=1 such swallowed output: {sum(1 for f in feats if f['n_empty_should']>0)} / {N}")
P('\n## Signals by env verdict x judge label (OS)\n')
g = collections.defaultdict(list)
for f in feats: g[(f['env'], f['judge'])].append(f)
rows = []
for k, v in sorted(g.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
    n = len(v)
    rows.append([k[0], k[1], n, f"{sum(f['n'] for f in v)/n:.1f}", f"{100*sum(1 for f in v if f['maxrep']>=3)/n:.0f}", f"{100*sum(1 for f in v if f['consec']>0)/n:.0f}",
                 f"{100*sum(1 for f in v if f['n_empty_should']>0)/n:.0f}", f"{100*sum(1 for f in v if f['n_err']>0)/n:.0f}", f"{100*sum(1 for f in v if f['finish'])/n:.0f}",
                 f"{100*sum(1 for f in v if f['has_answer'])/n:.0f}", f"{100*sum(1 for f in v if f['fmt_mismatch'])/max(1,sum(1 for f in v if f['fmt_mismatch'] is not None)):.0f}", f"{100*sum(1 for f in v if f['n_trunc']>0)/n:.0f}"])
P(md_table(['env', 'judge', 'n', 'turns', 'same cmd >=3x %', 'consecutive repeat %', 'swallowed output %', 'error resp %', 'ends finish %', 'ends answer %', 'answer format mismatch % (of checkable)', 'truncated output %'], rows))
P('\n## By model: env pass vs fail\n')
rows = []
for m in ('gpt', 'claude'):
    for e in ('pass', 'fail'):
        v = [f for f in feats if f['model'] == m and f['env'] == e]; n = len(v)
        rows.append([m, e, n, f"{sum(f['n'] for f in v)/n:.1f}", f"{100*sum(1 for f in v if f['maxrep']>=3)/n:.0f}", f"{100*sum(1 for f in v if f['consec']>0)/n:.0f}", f"{100*sum(1 for f in v if f['n_empty_should']>0)/n:.0f}",
                     f"{100*sum(1 for f in v if f['n_err']>0)/n:.0f}", f"{100*sum(1 for f in v if f['finish'])/n:.0f}", f"{100*sum(1 for f in v if f['fmt_mismatch'])/max(1,sum(1 for f in v if f['fmt_mismatch'] is not None)):.0f}"])
P(md_table(['model', 'env', 'n', 'turns', 'same cmd >=3x %', 'consec repeat %', 'swallowed %', 'error %', 'ends finish %', 'fmt mismatch %'], rows))
# AUROC of cheap features for env fail (P6)
def auroc(pos, neg):
    if not pos or not neg: return None
    s = 0
    for p in pos:
        for q in neg:
            s += 1 if p > q else 0.5 if p == q else 0
    return s / (len(pos) * len(neg))
P('\n## AUROC of cheap whole-trajectory features for env FAIL (P6: do failures deviate from a normal flow?)\n')
rows = []
for m in ('gpt', 'claude', 'all'):
    v = [f for f in feats if (m == 'all' or f['model'] == m) and f['env'] in ('pass', 'fail')]
    pos = [f for f in v if f['env'] == 'fail']; neg = [f for f in v if f['env'] == 'pass']
    r = [m, len(pos), len(neg)]
    for key in ('n', 'maxrep', 'consec', 'n_err', 'n_empty', 'cf'):
        r.append(f"{auroc([f[key] for f in pos], [f[key] for f in neg]):.3f}")
    r.append(f"{auroc([int(f['finish']) for f in pos], [int(f['finish']) for f in neg]):.3f}")
    r.append(f"{auroc([int(bool(f['fmt_mismatch'])) for f in pos], [int(bool(f['fmt_mismatch'])) for f in neg]):.3f}")
    rows.append(r)
P(md_table(['model', 'n fail', 'n pass', 'AUROC n_turns', 'max repeat', 'consec repeat', 'n error resp', 'n empty resp', 'cf level', 'ends finish', 'fmt mismatch'], rows))
# judge label vs model: CF reason mentions
P('\n## What the judge calls Catastrophic Forgetting on GPT vs Claude (env-fail runs): feature means\n')
rows = []
for m in ('gpt', 'claude'):
    for lab in ('Catastrophic Forgetting', 'Planning Error', 'Instruction'):
        v = [f for f in feats if f['model'] == m and f['env'] == 'fail' and f['judge'] == lab]; n = len(v)
        if not n: continue
        rows.append([m, lab, n, f"{sum(f['n'] for f in v)/n:.1f}", f"{100*sum(1 for f in v if f['maxrep']>=3)/n:.0f}", f"{100*sum(1 for f in v if f['has_answer'])/n:.0f}", f"{100*sum(1 for f in v if f['finish'])/n:.0f}", f"{100*sum(1 for f in v if f['fmt_mismatch'])/max(1,sum(1 for f in v if f['fmt_mismatch'] is not None)):.0f}", f"{sum(f['cf'] for f in v)/n:.1f}"])
P(md_table(['model', 'judge label', 'n', 'turns', 'same cmd>=3x %', 'ends answer %', 'ends finish %', 'fmt mismatch %', 'mean cf level'], rows))
with open(os.path.join(RESULTS, 'horizon', 'os_signals.md'), 'w') as fh: fh.write('\n'.join(out))
