#!/usr/bin/env python3
"""Label-blind LLM classification of the failure shape: omission -> (acceptance) -> commission.

The model sees task, ground truth (if released), final output and the whole trajectory, but NOT the dataset's label.
It must name (a) the missing required item and the step where it should have entered the agent's state (omission),
(b) the step that declared it obtained anyway (acceptance), (c) the step that first asserts an unsupported claim or acts
on one (commission), and the overall shape. Results: results/omission_commission/llm_<slug>.jsonl (resumable).

Usage: python3 inspect/oc_classify.py <slug> [--n 150] [--seed 0] [--ids a,b] [--workers 48] [--all]
"""
import argparse, collections, json, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, append_jsonl, read_jsonl
from common.llm import chat_json_many
from common.render import render_steps, render_task
from common.schema import error_step
from loaders import load

OUT = os.path.join(RESULTS, 'omission_commission')
SYSTEM = ('You are auditing a failed run of an LLM agent system. You will see the task, the reference answer when one '
          'exists, the system\'s final output, and the complete step-indexed trajectory. Read the whole trajectory '
          'before answering. Be precise about step indices: cite the [step N] tags exactly as shown.')
PROMPT = '''{task}

TRAJECTORY:

{traj}

Classify HOW this run failed using the following definitions.

A REQUIRED ITEM is any piece of evidence or requirement the task needs for a correct result: a fact, number, name, page content, file content, tool result, user-stated constraint, or plan requirement.

OMISSION STEP: the earliest step at which a required item should have entered the agent's working state but did not. Kinds: never_sought (no attempt to obtain it; the agent answers from memory or skips it), attempt_failed (a tool call / page load / install failed or returned nothing and was not successfully retried), delegated_not_done (an agent asked another agent or the user to obtain it and it never happened), visible_not_extracted (the item was present in an observation but the agent did not pick it up), obtained_then_dropped (the item was held earlier and later lost or contradicted without new evidence). If the agent never tried, the omission step is the step where the attempt should have been made (e.g. the planning step or the step that instead answered from memory).

ACCEPTANCE STEP: a later step, if any, at which some agent asserts or acts as if the missing item had been obtained or verified (e.g. an orchestrator ledger saying the information was gathered, a "verified" claim, a plan proceeding as if the step succeeded). null if none.

COMMISSION STEP: the earliest step at which an agent asserts a concrete claim, value, identifier, result or source that NO observation in the trajectory supports, or takes a consequential action on such a basis. Kinds: fabricated_fact, unjustified_assumption (explicitly assumes a value), hallucinated_tool_result (claims a tool/search returned something it did not), misread_evidence (the evidence was there but was read or transcribed wrongly), wrong_binding (a real fact attached to the wrong entity/time), action_without_basis (a consequential action, e.g. a purchase, write, or final answer, taken without the required evidence).

SHAPE:
- "pair": there is an omission AND a later commission whose content fills exactly the gap the omission left (the fabricated or assumed item is the missing item).
- "commission_only": an unsupported claim or action occurs but no required item was missing (e.g. the right evidence was obtained and then misread, or a wrong binding of obtained facts).
- "omission_only": a required item was missing and the run failed because of it, but no agent ever asserted an unsupported claim about it (e.g. the agent gave up, looped, answered "unknown", or produced a correct-form answer that simply lacks the item).
- "other": the failure is not about a missing or fabricated item: policy/format violation, environment outage with no claim made, budget exhaustion with no decisive step, a wrong answer that is fully supported by (wrong) evidence, or the run is actually not a failure.

Answer with ONE JSON object and nothing after it:
{{"missing_item": "<what was required and not properly obtained, or null>",
 "omission_step": <int or null>, "omission_kind": "<kind or null>",
 "acceptance_step": <int or null>,
 "commission_step": <int or null>, "commission_kind": "<kind or null>", "commission_what": "<the unsupported claim/action in one line, or null>",
 "shape": "pair" | "commission_only" | "omission_only" | "other", "other_kind": "<policy_or_format | environment | budget_exhaustion | wrong_but_evidenced | not_a_failure | reasoning_slip | null>",
 "decisive_step": <int: the single step you would blame if forced to choose one>,
 "confidence": <0.0-1.0>}}'''


def build(rec):
    traj, _ = render_steps(rec, per_step_cap=6000, total_cap_tokens=100000)
    task = render_task(rec, with_gt=True)
    return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': PROMPT.format(task=task, traj=traj)}]


def pick(recs, n, seed):
    """Stratified by subset, proportional, deterministic."""
    if n is None or len(recs) <= n:
        return recs
    rnd = random.Random(seed)
    by = collections.defaultdict(list)
    for r in recs:
        by[r['subset']].append(r)
    out = []
    for k in sorted(by, key=str):
        rs = by[k]; rnd.shuffle(rs)
        out.extend(rs[:max(1, round(n * len(rs) / len(recs)))])
    rnd.shuffle(out)
    return out[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug'); ap.add_argument('--n', type=int, default=150); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--ids', default=None); ap.add_argument('--workers', type=int, default=48); ap.add_argument('--all', action='store_true')
    ap.add_argument('--load-kw', default='{}')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'llm_{a.slug}.jsonl')
    done = {r['id'] for r in read_jsonl(path)} if os.path.exists(path) else set()
    recs = [r for r in load(a.slug, **json.loads(a.load_kw)) if r['steps'] and r['outcome'] != 'success']
    if a.ids:
        want = set(a.ids.split(',')); recs = [r for r in recs if r['id'] in want]
    else:
        labelled = [r for r in recs if r['labels']['error_steps']]
        recs = pick(labelled if labelled else recs, None if a.all else a.n, a.seed)
    recs = [r for r in recs if r['id'] not in done]
    print(f'{a.slug}: {len(recs)} records to classify ({len(done)} already done)', flush=True)
    B = 100000  # one pool for the whole dataset; every call is cached individually, so nothing is lost on a crash
    for i in range(0, len(recs), B):
        chunk = recs[i:i + B]
        outs = chat_json_many([build(r) for r in chunk], workers=a.workers, max_tokens=12000, think=True, tag='oc_classify_v1')
        for r, (parsed, out) in zip(chunk, outs):
            row = {'dataset': a.slug, 'id': r['id'], 'subset': r['subset'], 'label': error_step(r), 'error_steps': r['labels']['error_steps'],
                   'extra_keys': {k: r['labels']['extra'].get(k) for k in ('root_cause_idx', 'primary_idx', 'critical_idx', 'earliest_majority_step', 'span_start', 'span_end') if k in r['labels']['extra']},
                   'categories': r['labels']['categories'], 'n_steps': len(r['steps']), 'parsed': parsed,
                   'finish': out.get('finish_reason'), 'fallback': out.get('fallback'), 'error': out.get('error'),
                   'usage': out.get('usage'), 'content': out.get('content', '')[-1500:]}
            append_jsonl(path, row)
        print(f'  {min(i + B, len(recs))}/{len(recs)} done', flush=True)


if __name__ == '__main__':
    main()
