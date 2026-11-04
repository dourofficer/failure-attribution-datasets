"""Tag the MODEL's own reasons (std outputs) for evidence quality and relate to correctness: does a reason that cites a
concrete contradiction / observation predict a correct step?  python3 -I baseline/tag_pred_reasons.py slug..."""
import json, os, sys, re, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
from common.llm import LLM
P = """An automatic attributor read the log of a failed LLM-agent run and justified its choice of the decisive error step with the reason below. Judge the reason itself (not whether it is right).

Reason: \"\"\"{reason}\"\"\"

Answer yes/no:
A cites_specific_evidence: it names a concrete fact from the log (a specific wrong value, URL, click, command, claim, tool result) rather than a generic judgement.
B states_contradiction: it points to a contradiction between what the agent did/claimed and what the observation or task required.
C mentions_downstream_effect: it explains how the error propagated to the final failure.
D hedged: it uses hedging ("likely", "possibly", "may have", "appears").
E blames_strategy: the error it names is a strategy/plan choice ("should have used X instead", "inefficient") rather than a wrong fact or action.
F mentions_loop_or_repetition: it mentions repetition, looping, stalling or wasted steps.
Answer with one JSON object: {{"A": true/false, "B": ..., "C": ..., "D": ..., "E": ..., "F": ...}}"""
llm = LLM()
for slug in sys.argv[1:]:
    rows = [json.loads(l) for l in open(os.path.join(HERE, 'out', f'{slug}__std.jsonl'))]
    rows = [r for r in rows if r['pred'] and r['pred'].get('reason') and r['gold'].get('faulty_step') is not None]
    outs = llm.chat_many([[{"role": "user", "content": P.format(reason=str(r['pred']['reason'])[:1500])}] for r in rows], workers=10, max_tokens=120, thinking=False, temperature=0.0, tag='predreason_v1')
    S = collections.defaultdict(lambda: [0, 0, 0, 0]); n = 0
    with open(os.path.join(HERE, 'out', f'predtags__{slug}.jsonl'), 'w') as f:
        for r, o in zip(rows, outs):
            m = re.search(r'\{.*\}', o.get('text') or '', re.S)
            if not m: continue
            try: tg = json.loads(m.group(0))
            except Exception: continue
            try: ok = int(r['pred']['faulty_step']) == r['gold']['faulty_step']; pm3 = abs(int(r['pred']['faulty_step']) - r['gold']['faulty_step']) <= 3
            except Exception: continue
            n += 1; f.write(json.dumps({'id': r['id'], 'ok': ok, 'tags': tg}) + '\n')
            for k in 'ABCDEF':
                v = bool(tg.get(k)); S[(k, v)][0] += 1; S[(k, v)][1] += ok; S[(k, v)][2] += pm3
    print(f"\n{slug} (n={n}): exact accuracy when the model's reason has / lacks each property")
    names = {'A': 'cites_specific_evidence', 'B': 'states_contradiction', 'C': 'mentions_downstream_effect', 'D': 'hedged', 'E': 'blames_strategy', 'F': 'mentions_loop'}
    for k in 'ABCDEF':
        a = S[(k, True)]; b = S[(k, False)]
        print(f"  {names[k]:<27} yes: n={a[0]:>4} exact {100*a[1]/max(a[0],1):5.1f}% ±3 {100*a[2]/max(a[0],1):5.1f}% | no: n={b[0]:>4} exact {100*b[1]/max(b[0],1):5.1f}% ±3 {100*b[2]/max(b[0],1):5.1f}%")
