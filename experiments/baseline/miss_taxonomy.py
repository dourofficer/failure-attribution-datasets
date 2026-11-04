"""Why did the all-at-once pick differ from the gold?  For every exact miss, show the model the gold step (+ human
rationale), its own pick (+ its reason) and a sketch of the steps between, and ask it to classify the relation.
python3 -I baseline/miss_taxonomy.py <slug> [...]   -> baseline/out/misses__<slug>.jsonl + a summary table."""
import json, os, sys, re, importlib, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'loaders'))
from common.llm import LLM

PROMPT = """A failed run of an LLM agent system was annotated by humans with a DECISIVE ERROR STEP (the earliest step that, if done correctly, would have let the run succeed). An automatic attributor that read the whole run picked a DIFFERENT step. You are shown the task, the two steps with their justifications, and a sketch of the steps around and between them. Decide how the attributor's pick relates to the human label.

TASK: {task}
FINAL OUTPUT OF THE RUN: {final}

HUMAN LABEL: step {g} by {gagent}
HUMAN RATIONALE: {greason}
CONTENT OF STEP {g}:
{gcontent}

ATTRIBUTOR PICK: step {p} by {pagent}
ATTRIBUTOR REASON: {preason}
CONTENT OF STEP {p}:
{pcontent}

SKETCH OF THE STEPS FROM {lo} TO {hi} (each truncated):
{sketch}

Classify with ONE of these codes:
A same_error_other_step: both point at the same underlying mistake or episode; they differ only in which step of it is labelled (the instruction vs the execution, the producer of bad information vs the consumer who accepted it, the first vs a later repeat, the decision vs the commit).
B pick_is_upstream_cause: the pick is an EARLIER mistake that plausibly caused the error at the human step.
C pick_is_downstream_symptom: the pick is a LATER consequence of the error at the human step.
D pick_was_recovered: the pick was a mistake but the system corrected it or routed around it before the human step, so it did not cause the failure.
E pick_is_other_mistake: the pick is a different, independent mistake that also contributed or might have.
F human_label_questionable: the human step is not a mistake, or is environment-caused, or was itself recovered from; the pick is at least as defensible.
G pick_not_a_mistake: the picked step is actually fine.

Then say who is right. Answer with one JSON object only:
{{"code": "A|B|C|D|E|F|G", "who_is_right": "human|attributor|both_defensible|neither", "note": "<=25 words"}}"""


def sk(s, n=220):
    c = re.sub(r"\s+", " ", s['content']).strip()
    return f"[{s['idx']}] {s['agent']}: {c[:n]}"


def run(slug):
    mod = importlib.import_module(slug); llm = LLM()
    preds = {}
    for l in open(os.path.join(HERE, 'out', f'{slug}__std.jsonl')):
        r = json.loads(l)
        if r['pred']: preds[r['id']] = r
    items = []
    for t in mod.load():
        r = preds.get(t['id']); g = t['annotation']['faulty_step']
        if not r or g is None: continue
        try: p = int(r['pred'].get('faulty_step'))
        except Exception: continue
        if p == g or not (0 <= p < len(t['steps'])): continue
        steps = t['steps']; lo, hi = min(p, g), max(p, g)
        window = steps[max(0, lo - 2): hi + 3]
        if len(window) > 16:
            window = window[:7] + [None] + window[-7:]
        sketch = "\n".join(sk(s) if s else "   [...]" for s in window)
        msg = PROMPT.format(task=str(t['task'])[:700], final=str(t.get('final_output') or '')[:400], g=g, gagent=steps[g]['agent'], greason=(t['annotation']['reason'] or 'not released')[:700],
                            gcontent=steps[g]['content'][:1500], p=p, pagent=steps[p]['agent'], preason=(r['pred'].get('reason') or '')[:500], pcontent=steps[p]['content'][:1500],
                            lo=window[0]['idx'], hi=window[-1]['idx'], sketch=sketch)
        items.append((t['id'], g, p, t['subset'], msg))
    outs = llm.chat_many([[{"role": "user", "content": m}] for *_, m in items], workers=12, max_tokens=250, thinking=False, temperature=0.0, tag='miss_tax_v1')
    C = collections.Counter(); W = collections.Counter(); n = 0
    with open(os.path.join(HERE, 'out', f'misses__{slug}.jsonl'), 'w') as f:
        for (i, g, p, sub, _), o in zip(items, outs):
            m = re.search(r'\{.*\}', o.get('text') or '', re.S); tag = None
            if m:
                try: tag = json.loads(m.group(0))
                except Exception: pass
            f.write(json.dumps({'id': i, 'gold': g, 'pred': p, 'subset': sub, 'tag': tag}) + '\n')
            if tag: n += 1; C[str(tag.get('code'))[:1]] += 1; W[str(tag.get('who_is_right'))] += 1
    print(f"{slug}: {len(items)} misses, {n} classified | " + " ".join(f"{k}:{100*v/max(n,1):.0f}%" for k, v in sorted(C.items())) + " | who_is_right " + " ".join(f"{k}:{100*v/max(n,1):.0f}%" for k, v in W.most_common()))


if __name__ == '__main__':
    for s in sys.argv[1:]: run(s)
