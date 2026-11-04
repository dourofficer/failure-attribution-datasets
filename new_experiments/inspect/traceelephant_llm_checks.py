#!/usr/bin/env python3
"""Two small LLM classifications for TraceElephant (think off, cached):
 1. mistake_reason type: commission (a wrong action/claim at the step) / omission (should have done X) / outcome-only;
    plus whether the reason refers to a consequence visible later.
 2. Who&When same-task pairs: same failure mechanism? (0 = different, 1 = similar, 2 = same)
Writes results/traceelephant/reason_types.json and ww_mechanism.json."""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, write_json, read_json  # noqa: E402
from common.llm import chat_json_many  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402

P1 = ('You classify a one-sentence human annotation that explains why an AI agent system failed a task, written for a specific '
      'labelled step.\n\nAnnotation: "{reason}"\n\nClassify:\n'
      '"type": one of "commission" (the step did something concretely wrong: wrong fact, wrong value, wrong tool, fabricated content), '
      '"omission" (the step should have done something it did not do: not verifying, not checking, not using a tool, relying on X instead of Y), '
      '"outcome" (describes only the final result or a general failure without a specific act), "mixed".\n'
      '"verification_related": true if the annotation says something was not verified/confirmed/checked/validated.\n'
      '"names_consequence": true if it describes the downstream consequence (loop, wrong final answer, repeated attempts).\n'
      'Answer with one JSON object only: {{"type": "...", "verification_related": true|false, "names_consequence": true|false}}')

P2 = ('Two independent runs of two different multi-agent systems attempted the same task and both failed. Here are the human '
      'explanations of the decisive mistake in each run.\nTASK: {task}\nRun A: {a}\nRun B: {b}\n\nIs the failure MECHANISM the same '
      '(e.g. both fabricate without using tools; both misidentify the same entity; both cannot access the same source)?\n'
      'Answer one JSON object: {{"same_mechanism": 0|1|2, "note": "<one line>"}} where 0 = different mechanisms, 1 = related '
      '(same sub-problem fails but differently), 2 = same mechanism.')


def main():
    recs = load('traceelephant')
    msgs = [[{'role': 'user', 'content': P1.format(reason=(r['labels']['reason'] or '').replace('"', "'"))}] for r in recs]
    outs = chat_json_many(msgs, workers=4, max_tokens=300, think=False, tag='te_reason_type')
    rows = []
    for r, (p, o) in zip(recs, outs):
        p = p or {}
        rows.append({'id': r['id'], 'subset': r['subset'], 'reason': r['labels']['reason'], **{k: p.get(k) for k in ('type', 'verification_related', 'names_consequence')}})
    write_json(os.path.join(RESULTS, 'traceelephant', 'reason_types.json'), rows)
    for sub in ('magentic-one', 'captain-agent', 'swe-agent', None):
        rs = [x for x in rows if sub is None or x['subset'] == sub]
        print(sub or 'ALL', len(rs), 'type:', dict(Counter(x['type'] for x in rs)), 'verif:', sum(1 for x in rs if x['verification_related']),
              'conseq:', sum(1 for x in rs if x['names_consequence']))
    pairs = read_json(os.path.join(RESULTS, 'traceelephant', 'ww_overlap.json'))
    same = [x for x in pairs if (x['te_subset'], x['ww_subset']) in (('magentic-one', 'Hand-Crafted'), ('captain-agent', 'Algorithm-Generated'))]
    by = {r['id']: r for r in recs}
    msgs = [[{'role': 'user', 'content': P2.format(task=by[x['te_id']]['task'][:600], a=x['te_reason'], b=x['ww_reason'])}] for x in same]
    outs = chat_json_many(msgs, workers=4, max_tokens=300, think=False, tag='te_ww_mech')
    for x, (p, o) in zip(same, outs):
        p = p or {}
        x['same_mechanism'] = p.get('same_mechanism')
        x['note'] = p.get('note')
    write_json(os.path.join(RESULTS, 'traceelephant', 'ww_mechanism.json'), same)
    print('WW same-system pairs:', len(same), Counter(x['same_mechanism'] for x in same))
    print('by TE subset:', Counter((x['te_subset'], x['same_mechanism']) for x in same))
    print('agent agreement given mechanism:', Counter((x['same_mechanism'], x['agent_eq']) for x in same))


if __name__ == '__main__':
    main()
