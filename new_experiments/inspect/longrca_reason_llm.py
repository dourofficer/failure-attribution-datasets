#!/usr/bin/env python3
"""Classify every LongRCA mistake_reason with the LLM (no thinking, short JSON). Writes results/longrca/reason_llm.jsonl."""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table  # noqa: E402
from common.llm import chat_json_many  # noqa: E402
from loaders import load  # noqa: E402

SYS = 'You classify short annotator rationales from a failure-attribution benchmark. Answer with JSON only.'
P = ('An annotator marked one step of a failed agent trajectory as the root cause and wrote this rationale:\n"""{reason}"""\n'
     'Classify it. Fields:\n'
     '"causal_link": does the rationale state HOW this mistake led to the final task failure (an explicit consequence for the outcome)? true/false\n'
     '"kind": one of "wrong_action" (a substantively wrong decision/fact/action), "redundant_work" (the main complaint is repeated, unnecessary or wasted work / inefficiency), '
     '"handoff_instruction" (a wrong or incomplete instruction/delegation to another agent), "verification" (a verifier/judge/checker accepted or mis-checked something), '
     '"premature_stop_or_answer" (stopped, answered or declared completion too early / without required info), "ignored_evidence" (ignored available tool output, constraint or user request), "other"\n'
     '"mentions_outcome": does it mention the final answer/plan/result being wrong, incomplete or the task failing? true/false\n'
     'Answer: {{"causal_link": bool, "kind": "...", "mentions_outcome": bool}}')


def main():
    recs = load('longrca')
    per = int(sys.argv[1]) if len(sys.argv) > 1 else None  # records per source (stratified, in file order)
    if per:
        seen = collections.Counter()
        keep = []
        for r in recs:
            if seen[r['subset']] < per:
                keep.append(r); seen[r['subset']] += 1
        recs = keep
    msgs = [[{'role': 'system', 'content': SYS}, {'role': 'user', 'content': P.format(reason=(r['labels']['reason'] or '')[:3000])}] for r in recs]
    outs = chat_json_many(msgs, workers=2, max_tokens=200, think=False, tag='longrca_reason')
    path = os.path.join(RESULTS, 'longrca', 'reason_llm.jsonl')
    with open(path, 'w') as fh:
        for r, (p, o) in zip(recs, outs):
            p = p or {}
            fh.write(json.dumps({'id': r['id'], 'src': r['subset'], 'reason': r['labels']['reason'], 'causal_link': p.get('causal_link'),
                                 'kind': p.get('kind'), 'mentions_outcome': p.get('mentions_outcome'), 'parsed': bool(p)}, ensure_ascii=False) + '\n')
    rows = [json.loads(l) for l in open(path)]
    srcs = sorted(set(x['src'] for x in rows))
    kinds = ['wrong_action', 'redundant_work', 'handoff_instruction', 'verification', 'premature_stop_or_answer', 'ignored_evidence', 'other']
    tbl = []
    for s in srcs + ['ALL']:
        xs = [x for x in rows if s == 'ALL' or x['src'] == s]
        n = len(xs)
        c = collections.Counter(x['kind'] for x in xs)
        tbl.append([s, n, f"{100 * sum(1 for x in xs if x['causal_link']) / n:.0f}%", f"{100 * sum(1 for x in xs if x['mentions_outcome']) / n:.0f}%"] + [f'{100 * c[k] / n:.0f}%' for k in kinds])
    print(md_table(['source', 'n', 'causal link', 'mentions outcome'] + kinds, tbl))
    print('unparsed', sum(1 for x in rows if not x['parsed']))


if __name__ == '__main__':
    main()
