#!/usr/bin/env python3
"""Targeted statistics on AgentHallu beyond length/position (G3). Prints markdown tables; writes results/agenthallu/stats.md
Usage: python3 -I inspect/agenthallu_stats.py
"""
import json, os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table  # noqa
from common.schema import error_step  # noqa
from loaders import load  # noqa

ERR = re.compile(r'(\berror\b|\bfailed\b|exception|timeout|timed out|no such|not found|cannot |could not|unable to|403|404|traceback|invalid)', re.I)
EMPTY = re.compile(r'(no results?|\[\]|"matches": \[\]|empty|nothing found)', re.I)
OUT = []


def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.append(s)


def tool_resp(s):
    i = s['content'].find('Tool responses:')
    return s['content'][i:] if i >= 0 else ''


def has_call(s):
    return 'Tool calls:' in s['content']


def is_ask_human(s):
    return bool(re.search(r'ask_human|ask_user|human_via_console', s['content'].split('Tool responses:')[0]))


def is_final(s):
    c = s['content']
    return 'final_answer' in c or '"failed": false' in c or '"failed":false' in c


def err_step(s):
    tr = tool_resp(s)
    return bool(tr) and bool(ERR.search(tr))


def norm(x):
    x = str(x).strip().lower(); x = x.replace('$', '').replace('\\boxed{', '').replace('}', '').replace(',', '')
    return re.sub(r'[\s\.]+$', '', x).strip()


def main():
    rs = load('agenthallu')
    fails = [r for r in rs if r['outcome'] == 'fail']; cleans = [r for r in rs if r['outcome'] == 'success']
    cat = lambda r: r['labels']['categories'][0].replace(' Hallucination', '') if r['labels']['categories'] else '-'
    sub = lambda r: r['labels']['categories'][1] if len(r['labels']['categories']) > 1 else '-'

    # ---------- T1 gold-step composition ----------
    P('\n## T1. What kind of step is the gold step? (hallucinated runs, by category)')
    rows = []
    for c in sorted(set(cat(r) for r in fails)):
        rr = [r for r in fails if cat(r) == c]; g = [r['steps'][error_step(r)] for r in rr]
        n = len(rr)
        rows.append([c, n, f"{100*sum(has_call(s) for s in g)/n:.0f}%", f"{100*sum(err_step(s) for s in g)/n:.0f}%", f"{100*sum(is_ask_human(s) for s in g)/n:.0f}%",
                     f"{100*sum(1 for r in rr if error_step(r)==len(r['steps'])-1)/n:.0f}%", f"{100*sum(1 for r in rr if error_step(r)==0)/n:.0f}%",
                     f"{100*sum(1 for s in g if 'Call Next Speaker' in s['content'])/n:.0f}%",
                     f"{100*sum(1 for s in g if is_final(s))/n:.0f}%"])
    P(md_table(['category', 'n', 'has tool call', 'tool error in its response', 'is ask_human', 'is last step', 'is step 0', 'is handoff', 'is final-answer step'], rows))

    # ---------- T2 visible symptoms (tool errors) relative to gold; clean runs ----------
    P('\n## T2. Tool-error steps (regex on tool responses) relative to the gold step; clean runs as control')
    rows = []
    for name, rr in (('hallucinated', fails), ('clean', cleans)):
        for fw in sorted(set(r['subset'] for r in rr)):
            x = [r for r in rr if r['subset'] == fw]
            runs_with_err = sum(1 for r in x if any(err_step(s) for s in r['steps']))
            tot_steps = sum(len(r['steps']) for r in x); err_steps = sum(sum(err_step(s) for s in r['steps']) for r in x)
            if name == 'hallucinated':
                before = sum(1 for r in x if any(err_step(s) for s in r['steps'][:error_step(r)]))
                at = sum(1 for r in x if err_step(r['steps'][error_step(r)]))
                after = sum(1 for r in x if any(err_step(s) for s in r['steps'][error_step(r)+1:]))
                rel = f'{100*before/len(x):.0f}% / {100*at/len(x):.0f}% / {100*after/len(x):.0f}%'
            else:
                rel = '-'
            rows.append([name, fw, len(x), f'{100*runs_with_err/len(x):.0f}%', f'{100*err_steps/max(1,tot_steps):.1f}%', rel])
    P(md_table(['class', 'framework', 'n', 'runs with >=1 tool-error step', 'tool-error steps / all steps', 'err before / at / after gold (hallucinated)'], rows))
    # recovered error proxy in clean runs: error then later non-error call
    rec = sum(1 for r in cleans if any(err_step(s) for s in r['steps']))
    P(f'\nclean runs with >=1 tool-error step (recovered-error proxy): {rec}/{len(cleans)} = {100*rec/len(cleans):.1f}%; '
      f'hallucinated: {sum(1 for r in fails if any(err_step(s) for s in r["steps"]))}/{len(fails)}')

    # ---------- T3 ground-truth visible in the trajectory ----------
    P('\n## T3. Is the correct answer visible in the trajectory of hallucinated runs? (exact normalised GT string, GT <= 40 chars, non-BFCL)')
    rows = []; cnt = Counter(); ids = defaultdict(list)
    for r in fails:
        if r['subset'] == 'BFCL': continue
        g = norm(r['ground_truth'])
        if not g or len(g) > 40 or len(g) < 2 or (g.replace('.', '').isdigit() and len(g) <= 2): continue
        k = next((s['idx'] for s in r['steps'] if g in norm(s['content'])), None)
        gs = error_step(r)
        key = 'never' if k is None else ('before gold' if k < gs else ('at gold' if k == gs else 'after gold'))
        cnt[(cat(r), key)] += 1; cnt[('ALL', key)] += 1; ids[key].append(r['id'])
    for c in sorted(set(k[0] for k in cnt)):
        n = sum(v for k, v in cnt.items() if k[0] == c)
        rows.append([c, n] + [f"{cnt[(c, key)]} ({100*cnt[(c, key)]/n:.0f}%)" for key in ('before gold', 'at gold', 'after gold', 'never')])
    P(md_table(['category', 'n evaluable', 'GT visible before gold', 'at gold', 'after gold', 'never'], rows))
    P('ids GT visible before gold:', ', '.join(ids['before gold'][:40]))
    P('ids GT visible at gold:', ', '.join(ids['at gold'][:40]))
    # same on clean runs
    k2 = Counter()
    for r in cleans:
        if r['subset'] == 'BFCL': continue
        g = norm(r['ground_truth'])
        if not g or len(g) > 40 or len(g) < 2 or (g.replace('.', '').isdigit() and len(g) <= 2): continue
        k2['visible' if any(g in norm(s['content']) for s in r['steps']) else 'never'] += 1
    P('clean runs (same filter): GT visible in trajectory', dict(k2))

    # ---------- T4 Human-interaction ----------
    P('\n## T4. ask_human steps: where they occur and whether the gold step is one')
    rows = []
    for name, rr in (('HI (hallucinated)', [r for r in fails if cat(r) == 'Human-Interaction']), ('other hallucinated', [r for r in fails if cat(r) != 'Human-Interaction']), ('clean', cleans)):
        n = len(rr); with_ah = [r for r in rr if any(is_ask_human(s) for s in r['steps'])]
        n_ah = sum(sum(is_ask_human(s) for s in r['steps']) for r in with_ah)
        gold_is_ah = sum(1 for r in rr if r['labels']['error_steps'] and is_ask_human(r['steps'][error_step(r)]))
        gold_is_first_ah = sum(1 for r in rr if r['labels']['error_steps'] and is_ask_human(r['steps'][error_step(r)]) and not any(is_ask_human(s) for s in r['steps'][:error_step(r)]))
        rows.append([name, n, len(with_ah), f'{n_ah/max(1,len(with_ah)):.2f}', gold_is_ah, gold_is_first_ah, Counter(r['subset'] for r in with_ah).most_common(4)])
    P(md_table(['class', 'n', 'runs with ask_human', 'ask_human per such run', 'gold is ask_human step', 'gold is FIRST ask_human', 'frameworks'], rows))
    P('non-HI hallucinated runs containing ask_human:', [r['id'] for r in fails if cat(r) != 'Human-Interaction' and any(is_ask_human(s) for s in r['steps'])][:30])
    P('clean runs containing ask_human:', [r['id'] for r in cleans if any(is_ask_human(s) for s in r['steps'])][:40])
    # HI: step after gold adopts? count HI runs where the human's answer string appears in the final answer
    adopt = 0; hi = [r for r in fails if cat(r) == 'Human-Interaction']
    for r in hi:
        s = r['steps'][error_step(r)]; tr = tool_resp(s)
        m = re.findall(r'\d[\d\.,]*', tr)
        if m and any(x in str(r['final_output']) for x in m if len(x) >= 3): adopt += 1
    P(f'HI runs where a number from the human reply reappears in the final answer: {adopt}/{len(hi)}')

    # ---------- T5 BFCL ----------
    P('\n## T5. BFCL (Tool-Use): turn structure, gold step type, silent tool responses')
    bf = [r for r in fails if r['subset'] == 'BFCL']; bc = [r for r in cleans if r['subset'] == 'BFCL']
    def turns(r):
        # a turn ends at a step without tool calls (the assistant reply)
        t = []; cur = []
        for s in r['steps']:
            cur.append(s['idx'])
            if not has_call(s):
                t.append(cur); cur = []
        if cur: t.append(cur)
        return t
    rows = []
    for sc in sorted(set(sub(r) for r in bf)):
        x = [r for r in bf if sub(r) == sc]; n = len(x)
        gcall = sum(1 for r in x if has_call(r['steps'][error_step(r)]))
        gerr = sum(1 for r in x if err_step(r['steps'][error_step(r)]))
        silent = sum(1 for r in x if '"None"' in tool_resp(r['steps'][error_step(r)]) or "'None'" in tool_resp(r['steps'][error_step(r)]))
        tpos = []
        for r in x:
            t = turns(r); g = error_step(r)
            ti = next((i for i, tt in enumerate(t) if g in tt), None)
            tpos.append((ti, len(t)))
        first_turn = sum(1 for ti, nt in tpos if ti == 0); last_turn = sum(1 for ti, nt in tpos if ti == nt - 1)
        try: nq = [len(json.loads(r['task'])) for r in x]
        except Exception: nq = []
        rows.append([sc, n, f'{100*gcall/n:.0f}%', f'{100*gerr/n:.0f}%', f'{100*silent/n:.0f}%', f'{100*first_turn/n:.0f}% / {100*last_turn/n:.0f}%', f'{sum(nq)/max(1,len(nq)):.1f}', f'{sum(nt for _, nt in tpos)/n:.1f}'])
    P(md_table(['subcategory', 'n', 'gold is a tool-call step', 'gold response has error', 'gold response silent (None)', 'gold in first / last turn', 'user turns (task)', 'detected turns'], rows))
    # tool error rate in BFCL hallucinated vs clean
    for name, x in (('BFCL hallucinated', bf), ('BFCL clean', bc)):
        ts = sum(len(r['steps']) for r in x); es = sum(sum(err_step(s) for s in r['steps']) for r in x)
        P(f'{name}: tool-error steps {es}/{ts} = {100*es/ts:.1f}%; runs with >=1 error {sum(1 for r in x if any(err_step(s) for s in r["steps"]))}/{len(x)}')

    # ---------- T6 reason text vs label ----------
    P('\n## T6. Step number quoted in hallucination_reason vs hallucination_step label (1-based)')
    mism = []; ok = 0; none = 0
    for r in fails:
        m = re.search(r'[Ss]tep\s*(\d+)', r['labels']['reason'] or '')
        raw = r['labels']['extra'].get('hallucination_step_raw')
        if not m: none += 1; continue
        if int(m.group(1)) == int(raw): ok += 1
        else: mism.append((r['id'], int(m.group(1)), int(raw), len(r['steps'])))
    P(f'reason quotes a step: {ok + len(mism)}/{len(fails)}; agrees with label: {ok}; disagrees: {len(mism)}; no step quoted: {none}')
    P('disagreements (id, reason step, label step, n_steps):', mism)

    # ---------- T7 gold==0 ----------
    P('\n## T7. gold == step 0 (112 runs): who is step 0 and what category')
    z = [r for r in fails if error_step(r) == 0]
    P(md_table(['framework', 'agent at step 0', 'category', 'n'], [[k[0], k[1], k[2], v] for k, v in sorted(Counter((r['subset'], r['steps'][0]['agent'], cat(r)) for r in z).items(), key=lambda kv: -kv[1])]))
    P('gold==0 share by framework:', {fw: f"{sum(1 for r in z if r['subset']==fw)}/{sum(1 for r in fails if r['subset']==fw)}" for fw in sorted(set(r['subset'] for r in fails))})

    # ---------- T8 gold at the handoff vs content ----------
    P('\n## T8. Multi-agent frameworks: is the gold step a WebSurfer/Search fetch step whose RESPONSE carries the wrong fact (fetch) vs an agent assertion (adopt)?')
    rows = []
    for fw in ('Magentic_One', 'Camel'):
        x = [r for r in fails if r['subset'] == fw]
        fetch = sum(1 for r in x if has_call(r['steps'][error_step(r)]) and r['steps'][error_step(r)]['agent'] in ('WebSurfer', 'Search Agent'))
        orch = sum(1 for r in x if r['steps'][error_step(r)]['agent'] in ('MagenticOneOrchestrator', 'Planner', 'Coordinator'))
        rows.append([fw, len(x), fetch, orch, dict(Counter(r['steps'][error_step(r)]['agent'] for r in x))])
    P(md_table(['framework', 'n', 'gold = search/browse tool-call step', 'gold = orchestrator/planner step', 'agent at gold'], rows))

    with open(os.path.join(RESULTS, 'agenthallu', 'stats.md'), 'w') as fh:
        fh.write('\n'.join(OUT))


if __name__ == '__main__':
    main()
