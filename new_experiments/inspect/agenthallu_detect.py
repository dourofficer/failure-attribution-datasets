#!/usr/bin/env python3
"""Hallucination DETECTION probe on AgentHallu without ground truth: show question + trajectory + final answer, ask
whether the final answer is hallucinated and which step is responsible. 40 clean + 40 hallucinated, stratified by
framework (fixed seed). Writes results/agenthallu/detect.jsonl and prints AUROC / accuracy / step agreement.
Usage: python3 -I inspect/agenthallu_detect.py [--n-per-class 40] [--workers 2] [--seed 0]
"""
import argparse, os, random, sys
from collections import defaultdict, Counter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, append_jsonl, md_table  # noqa
from common.llm import chat_json_many  # noqa
from common.render import render_steps  # noqa
from common.schema import error_step  # noqa
from loaders import load  # noqa

SYSTEM = ('You are auditing an LLM agent system. You see the user question, the full trajectory and the final answer. '
          'You do NOT know the reference answer. Decide whether the final answer is hallucinated (factually wrong, '
          'unsupported by the evidence gathered, or based on a wrong tool call / wrong reasoning step).')
PROMPT = ('QUESTION:\n{q}\n\nTRAJECTORY:\n\n{traj}\n\nFINAL ANSWER:\n{ans}\n\n'
          'Answer with one JSON object only: {{"hallucinated": true|false, "confidence": <0.0-1.0 that it IS hallucinated>, '
          '"why": "<one or two sentences>", "suspect_step": <integer step index of the step most responsible, or -1 if none>}}')


def auroc(pos, neg):
    import itertools
    n = 0; s = 0.0
    for p in pos:
        for q in neg:
            n += 1; s += 1.0 if p > q else (0.5 if p == q else 0.0)
    return s / max(1, n)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--n-per-class', type=int, default=40); ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--seed', type=int, default=0); ap.add_argument('--tag', default='')
    a = ap.parse_args()
    recs = load('agenthallu')
    rng = random.Random(a.seed)
    by = defaultdict(list)
    for r in recs:
        by[(r['outcome'], r['subset'])].append(r)
    chosen = []
    for oc in ('success', 'fail'):
        fws = sorted(k[1] for k in by if k[0] == oc)
        quota = {fw: 0 for fw in fws}
        pools = {fw: rng.sample(by[(oc, fw)], len(by[(oc, fw)])) for fw in fws}
        k = 0
        while k < a.n_per_class:
            for fw in fws:
                if pools[fw] and k < a.n_per_class:
                    chosen.append(pools[fw].pop()); quota[fw] += 1; k += 1
        print(oc, quota, file=sys.stderr)
    msgs = []
    for r in chosen:
        traj, _ = render_steps(r, total_cap_tokens=60000)
        msgs.append([{'role': 'system', 'content': SYSTEM},
                     {'role': 'user', 'content': PROMPT.format(q=r['task'][:6000], traj=traj, ans=str(r['final_output'])[:4000])}])
    outs = chat_json_many(msgs, workers=a.workers, max_tokens=8192, think=True, tag='ah_detect')
    path = os.path.join(RESULTS, 'agenthallu', 'detect' + (f'_{a.tag}' if a.tag else '') + '.jsonl')
    if os.path.exists(path): os.remove(path)
    rows = []
    for r, (p, o) in zip(chosen, outs):
        p = p or {}
        try: conf = float(p.get('confidence', 0.5))
        except Exception: conf = 0.5
        try: sus = int(p.get('suspect_step', -1))
        except Exception: sus = -1
        g = error_step(r)
        row = {'id': r['id'], 'subset': r['subset'], 'domain': r['meta']['domain'], 'outcome': r['outcome'], 'n_steps': len(r['steps']),
               'gold': g, 'cats': r['labels']['categories'], 'pred_halluc': bool(p.get('hallucinated')), 'conf': conf, 'why': p.get('why'),
               'suspect': sus, 'step_exact': (g is not None and sus == g), 'step_within1': (g is not None and abs(sus - g) <= 1),
               'parsed': bool(p), 'finish': o.get('finish_reason'), 'fallback': o.get('fallback'),
               'reasoning_tail': (o.get('reasoning') or '')[-1500:], 'gt': str(r['ground_truth'])[:300], 'final': str(r['final_output'])[:300]}
        rows.append(row); append_jsonl(path, row)
    pos = [x['conf'] for x in rows if x['outcome'] == 'fail']; neg = [x['conf'] for x in rows if x['outcome'] == 'success']
    tp = sum(1 for x in rows if x['outcome'] == 'fail' and x['pred_halluc']); fn = len(pos) - tp
    fp = sum(1 for x in rows if x['outcome'] == 'success' and x['pred_halluc']); tn = len(neg) - fp
    print(md_table(['metric', 'value'], [
        ['n (halluc / clean)', f'{len(pos)} / {len(neg)}'], ['AUROC (conf)', f'{auroc(pos, neg):.3f}'],
        ['accuracy (pred_halluc)', f'{(tp + tn) / len(rows):.3f}'], ['recall on hallucinated', f'{tp}/{len(pos)}'], ['false alarms on clean', f'{fp}/{len(neg)}'],
        ['step exact | hallucinated', f"{sum(1 for x in rows if x['outcome']=='fail' and x['step_exact'])}/{len(pos)}"],
        ['step exact | hallucinated & detected', f"{sum(1 for x in rows if x['outcome']=='fail' and x['pred_halluc'] and x['step_exact'])}/{tp}"],
        ['step exact | hallucinated & missed', f"{sum(1 for x in rows if x['outcome']=='fail' and not x['pred_halluc'] and x['step_exact'])}/{fn}"],
        ['step within 1 | hallucinated', f"{sum(1 for x in rows if x['outcome']=='fail' and x['step_within1'])}/{len(pos)}"],
    ]))
    print('\nby framework (halluc: detected/n, step exact; clean: false alarms/n)')
    for fw in sorted(set(x['subset'] for x in rows)):
        h = [x for x in rows if x['subset'] == fw and x['outcome'] == 'fail']; c = [x for x in rows if x['subset'] == fw and x['outcome'] == 'success']
        print(f"  {fw}: halluc {sum(x['pred_halluc'] for x in h)}/{len(h)} det, {sum(x['step_exact'] for x in h)} exact; clean FA {sum(x['pred_halluc'] for x in c)}/{len(c)}")
    print('\nby category (halluc only): detected/n, exact')
    for cat in sorted(set(x['cats'][0] for x in rows if x['cats'])):
        h = [x for x in rows if x['outcome'] == 'fail' and x['cats'][:1] == [cat]]
        print(f"  {cat}: {sum(x['pred_halluc'] for x in h)}/{len(h)} det, {sum(x['step_exact'] for x in h)} exact, mean conf {sum(x['conf'] for x in h)/max(1,len(h)):.2f}")
    print('\nconf bins (halluc): exact-step rate'); 
    for lo, hi in ((0, 0.5), (0.5, 0.8), (0.8, 1.01)):
        h = [x for x in rows if x['outcome'] == 'fail' and lo <= x['conf'] < hi]
        print(f'  [{lo},{hi}): n={len(h)} exact={sum(x["step_exact"] for x in h)}')
    print('wrote', path)


if __name__ == '__main__':
    main()
