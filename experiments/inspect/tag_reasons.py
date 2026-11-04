"""Tag every annotator rationale (LongRCA, Who&When, TraceElephant, AgentHallu, AgentRx root reasons) with an LLM for
lifecycle language and label-quality signals. Output: experiments/inspect/out/reason_tags.jsonl
Run: python3 -I inspect/tag_reasons.py"""
import json, glob, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
from common.llm import LLM
D = '/dataDisk/home/thanhdo/failure-attribution-datasets/data'

items = []
for sub in ['Hand-Crafted', 'Algorithm-Generated']:
    for f in sorted(glob.glob(f'{D}/who_and_when/Who&When/{sub}/*.json')):
        d = json.load(open(f)); items.append(dict(dataset='who_and_when', subset=sub, id=os.path.basename(f), step=str(d['mistake_step']), agent=str(d['mistake_agent']), reason=d.get('mistake_reason') or ''))
for f in sorted(glob.glob(f'{D}/traceelephant/extracted/**/trace_metadata.json', recursive=True)):
    d = json.load(open(f)); items.append(dict(dataset='traceelephant', subset=d.get('system_name'), id=d.get('run_id'), step=str(d.get('mistake_step')), agent=d.get('mistake_agent'), reason=d.get('mistake_reason') or ''))
for f in sorted(glob.glob(f'{D}/longrca/data/full/*/*.json')):
    d = json.load(open(f)); items.append(dict(dataset='longrca', subset=d['question_ID'].split('__')[0], id=d['question_ID'], step=str(d['mistake_step']), agent=d['mistake_agent'], reason=d.get('mistake_reason') or ''))
for f in sorted(glob.glob(f'{D}/agenthallu/repo/AgentHallu/*/*.json')):
    d = json.load(open(f))
    if str(d.get('is_hallucination')).lower() == 'true':
        items.append(dict(dataset='agenthallu', subset=f.split('/')[-2], id=f.split('/')[-2] + '/' + os.path.basename(f), step=str(d.get('hallucination_step')), agent=None, reason=d.get('hallucination_reason') or ''))
for name in ['tau_ground_truth.json', 'magentic_one_ground_truth.json']:
    for g in json.load(open(f'{D}/agentrx/github/data/ground_truth/{name}')):
        root = g['root_cause']; rf = [x for x in g['failures'] if str(x['failure_id']) == str(root['failure_id'])]
        items.append(dict(dataset='agentrx', subset=name.split('_')[0], id=str(g['trajectory_id']), step=str(rf[0]['step_number']) if rf else None, agent=rf[0]['failed_agent'] if rf else None,
                          reason=(rf[0]['step_reason'] + ' || ROOT: ' + root['reason_for_root_cause']) if rf else root['reason_for_root_cause']))
items = [it for it in items if it['reason'].strip()]
print('items', len(items), {k: sum(1 for i in items if i['dataset'] == k) for k in set(i['dataset'] for i in items)})

PROMPT = """Below is the rationale an annotator wrote to justify which step of a failed LLM-agent run is the root-cause / decisive error step. Classify the rationale on the following yes/no questions. Judge ONLY from the text of the rationale.

Rationale: \"\"\"{reason}\"\"\"

Questions:
A. earlier_error_recovered: Does it mention an earlier mistake or problem that the system later corrected, worked around, or recovered from (before the decisive error)?
B. later_repair_failed: Does it mention that after the decisive error the system tried to fix/repair/retry and those attempts failed?
C. propagation_stated: Does it explicitly state a causal chain from the blamed step to the final failure (e.g. "leading to", "causing", "so the final answer was")?
D. symptom_only: Does it describe only the final wrong answer / final state (what was wrong at the end) without naming a specific earlier decision or action that caused it?
E. uses_ground_truth: Does it rely on knowledge of the correct answer / reference solution / test results that an attributor reading only the log would not have (e.g. "the correct answer is X", "should have been Y according to the ground truth")?
F. blames_environment: Does it attribute the failure to a tool failure, access restriction, timeout, missing file, or other environment/infrastructure problem rather than a wrong decision?
G. counterfactual_stated: Does it say what the step should have done instead?
H. multiple_candidates: Does it mention more than one wrong step/decision as contributing (ambiguity about which is the root)?
I. generic: Is the rationale generic / template-like, giving no run-specific evidence (e.g. "the agent provided wrong information")?

Answer with one JSON object: {{"A": true/false, "B": ..., "C": ..., "D": ..., "E": ..., "F": ..., "G": ..., "H": ..., "I": ..., "note": "<=15 words"}}"""

llm = LLM()
os.makedirs(f'{HERE}/out', exist_ok=True)
msgs = [[{"role": "user", "content": PROMPT.format(reason=it['reason'][:6000])}] for it in items]
outs = llm.chat_many(msgs, workers=12, max_tokens=300, thinking=False, temperature=0.0, tag='reason_tags_v1')
ok = 0
with open(f'{HERE}/out/reason_tags.jsonl', 'w') as f:
    for it, o in zip(items, outs):
        m = re.search(r'\{.*\}', o.get('text') or '', re.S)
        tags = None
        if m:
            try: tags = json.loads(m.group(0)); ok += 1
            except Exception: pass
        f.write(json.dumps({**it, 'tags': tags}, ensure_ascii=False) + '\n')
print('parsed', ok, '/', len(items))
