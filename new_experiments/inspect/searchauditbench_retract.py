#!/usr/bin/env python3
"""LLM probe: after the labelled critical step k, does the agent itself later question / retract the decision made at k
(recovered-then-relapsed), and was the mechanism named in the rationale already present in an EARLIER assistant message?
Input per record: query, the critical step (full), the official rationale, and the reasoning of all later assistant
messages (truncated), plus the earlier assistant messages (truncated). Two JSON answers per record.
Usage: python3 -I inspect/searchauditbench_retract.py [--n 40] [--seed 0] [--workers 2]"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, append_jsonl  # noqa: E402
from common.llm import chat_json_many  # noqa: E402
from common.render import truncate  # noqa: E402
from loaders import load  # noqa: E402

SYS = 'You are auditing an annotation of a failed web-research agent trajectory. Answer strictly from the text given.'
P_LATER = ('QUERY: {q}\n\nAN ANNOTATOR LABELLED MESSAGE {k} AS THE CRITICAL ERROR, WITH THIS RATIONALE:\n{rat}\n\n'
           'MESSAGE {k} (the labelled step):\n{crit}\n\nLATER ASSISTANT MESSAGES (reasoning, truncated):\n{later}\n\n'
           'Questions: (a) Does the agent, in any LATER message, explicitly question, doubt, or retract the specific decision/'
           'assumption that the rationale blames message {k} for (e.g. "wait, this does not match", "I need to re-check X")? '
           '(b) If yes, does it then act on the doubt (re-search / verify) before finally re-committing to the same wrong line? '
           'Answer JSON only: {{"questions_later": true|false, "first_questioning_message": <int or null>, '
           '"acts_on_doubt": true|false, "recommits_anyway": true|false, "evidence": "<one quoted line>"}}')
P_EARLIER = ('QUERY: {q}\n\nAN ANNOTATOR LABELLED MESSAGE {k} AS THE EARLIEST CRITICAL ERROR, WITH THIS RATIONALE:\n{rat}\n\n'
             'MESSAGE {k} (the labelled step):\n{crit}\n\nEARLIER ASSISTANT MESSAGES (reasoning, truncated):\n{earlier}\n\n'
             'Question: is the SAME mistake mechanism the rationale describes (same wrong assumption, same narrowed scope, same '
             'unverified acceptance, same ignored constraint) already present in an EARLIER assistant message? If so, give the '
             'earliest such message. Answer JSON only: {{"present_earlier": true|false, "earliest_message": <int or null>, '
             '"evidence": "<one quoted line>"}}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=40)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    recs = load('searchauditbench')
    random.Random(a.seed).shuffle(recs)
    recs = recs[:a.n]
    msgs_l, msgs_e, meta = [], [], []
    for r in recs:
        k = r['labels']['extra']['critical_idx']
        rat = r['labels']['reason'] or ''
        asst = [s for s in r['steps'] if s['role'] == 'agent']
        later = [s for s in asst if s['idx'] > k]
        earlier = [s for s in asst if s['idx'] < k]
        crit = truncate(r['steps'][k]['content'], 6000)
        fl = '\n\n'.join(f"[message {s['idx']}]\n{truncate(s['content'], 2500)}" for s in later) or '(none: the labelled message is the final answer)'
        fe = '\n\n'.join(f"[message {s['idx']}]\n{truncate(s['content'], 2500)}" for s in earlier) or '(none: the labelled message is the first decision)'
        q = r['task']
        msgs_l.append([{'role': 'system', 'content': SYS}, {'role': 'user', 'content': P_LATER.format(q=q, k=k, rat=rat, crit=crit, later=fl)}])
        msgs_e.append([{'role': 'system', 'content': SYS}, {'role': 'user', 'content': P_EARLIER.format(q=q, k=k, rat=rat, crit=crit, earlier=fe)}])
        meta.append({'id': r['id'], 'rc': r['labels']['categories'][0], 'k': k, 'n_later': len(later), 'n_earlier': len(earlier), 'is_final': not later})
    outs_l = chat_json_many(msgs_l, workers=a.workers, max_tokens=6000, think=True, tag='sab_retract_later')
    outs_e = chat_json_many(msgs_e, workers=a.workers, max_tokens=6000, think=True, tag='sab_retract_earlier')
    path = os.path.join(RESULTS, 'searchauditbench', 'retract.jsonl')
    if os.path.exists(path):
        os.remove(path)
    for m, (pl, _), (pe, _) in zip(meta, outs_l, outs_e):
        row = {**m, 'later': pl or {}, 'earlier': pe or {}}
        append_jsonl(path, row)
    rows = [json.loads(l) for l in open(path)]
    nl = [x for x in rows if not x['is_final']]
    print('n', len(rows), 'with later messages', len(nl))
    print('questions_later', sum(1 for x in nl if x['later'].get('questions_later')), 'acts_on_doubt', sum(1 for x in nl if x['later'].get('acts_on_doubt')), 'recommits', sum(1 for x in nl if x['later'].get('recommits_anyway')))
    ne = [x for x in rows if x['n_earlier']]
    print('present_earlier', sum(1 for x in ne if x['earlier'].get('present_earlier')), '/', len(ne))
    for x in rows:
        print(x['id'], x['rc'], 'k', x['k'], '| later:', x['later'].get('questions_later'), x['later'].get('first_questioning_message'), x['later'].get('recommits_anyway'), '| earlier:', x['earlier'].get('present_earlier'), x['earlier'].get('earliest_message'))


if __name__ == '__main__':
    main()
