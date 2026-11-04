#!/usr/bin/env python3
"""TRAIL statistics 2: label-vs-outcome (hindsight), annotation-miss candidates, unlabelled identical mistakes,
primary-error recoverability, earliest->primary distance, evidence-quotes-symptom."""
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, read_json  # noqa: E402
from loaders import load  # noqa: E402

BAD = {'gaia/331aece579d942bb4c345a86c86efb83', 'gaia/c60ad8608dd94271a6c6805eedfa26a8'}


def out_part(c):
    i = c.find('Output (')
    return c[i:] if i >= 0 else c


def main():
    stats = {r['id']: r for r in read_json(os.path.join(RESULTS, 'trail', 'stats.json'))}
    recs = load('trail')
    gaia = [r for r in recs if r['subset'] == 'gaia']
    ok = {r['id']: bool(stats[r['id']]['answer_match']) and r['id'] not in BAD for r in gaia}
    # (a) wrong-ending with no HIGH; correct-ending with HIGH
    noh_wrong = [r['id'] for r in gaia if not ok[r['id']] and stats[r['id']]['n_HIGH'] == 0]
    h_ok = [r['id'] for r in gaia if ok[r['id']] and stats[r['id']]['n_HIGH'] > 0]
    print(f'GAIA wrong-ending traces with NO HIGH error: {len(noh_wrong)}/{sum(1 for r in gaia if not ok[r["id"]])}', noh_wrong)
    print(f'GAIA correct-ending traces with >=1 HIGH error: {len(h_ok)}/{sum(ok.values())}')
    # (b) human score and n_HIGH vs outcome
    def sc(r):
        s = r['labels']['extra'].get('scores')
        if isinstance(s, list) and s:
            s = s[0]
        return s.get('overall') if isinstance(s, dict) else None
    for lab, grp in (('correct', [r for r in gaia if ok[r['id']]]), ('wrong', [r for r in gaia if not ok[r['id']]])):
        scs = [sc(r) for r in grp if sc(r) is not None]
        nh = [stats[r['id']]['n_HIGH'] for r in grp]
        ne = [stats[r['id']]['n_errors'] for r in grp]
        rel = [ (r['labels']['extra']['scores'][0] if isinstance(r['labels']['extra']['scores'], list) else r['labels']['extra']['scores']).get('reliability_score') for r in grp]
        rel = [x for x in rel if x is not None]
        print(f'{lab}: n={len(grp)} human overall score mean={statistics.mean(scs):.2f} median={statistics.median(scs)}; reliability mean={statistics.mean(rel):.2f}; n_HIGH mean={statistics.mean(nh):.2f}; n_errors mean={statistics.mean(ne):.2f}; share with 0 HIGH={sum(1 for x in nh if x==0)/len(nh):.2f}')
    # (c) primary category x outcome; tool-arg formatting primaries and recovery
    pc = defaultdict(Counter)
    for r in gaia:
        for c in stats[r['id']]['primary_cats'][:1]:
            pc[c][ok[r['id']]] += 1
    print(md_table(['primary category', 'correct', 'wrong'], [[c, d[True], d[False]] for c, d in sorted(pc.items(), key=lambda x: -sum(x[1].values()))]))
    # (d) earliest -> primary distance, share of pre-primary errors that are end_plan
    dist = []; pre_end = Counter()
    for r in recs:
        ex = r['labels']['extra']; p = ex['primary_idx']
        if p is None: continue
        errs = [e for e in ex['errors'] if e['idx'] is not None]
        e0 = min(e['idx'] for e in errs)
        if e0 < p:
            dist.append(p - e0)
            for e in errs:
                if e['idx'] < p:
                    pre_end['end_plan' if 'end_plan' in (str(e['description']) + str(e['evidence'])) else 'other'] += 1
    print(f'earliest->primary distance (n={len(dist)}): median {statistics.median(dist)}, mean {statistics.mean(dist):.1f}, max {max(dist)}; pre-primary errors: {dict(pre_end)}')
    # (e) unlabelled identical mistakes
    print_task = []; snippet_only = []
    for r in gaia:
        labelled = set(r['labels']['error_steps'])
        for s in r['steps']:
            if s['role'] != 'agent' or s['agent'] != 'CodeAgent':
                continue
            o = out_part(s['content'])
            m = re.search(r'Code:\s*```py(.*?)```', o, re.S)
            if m and re.search(r'\btask\s*=', m.group(1)) and 'print(task' in m.group(1) and 'search_agent(' not in m.group(1):
                print_task.append((r['id'], s['idx'], s['idx'] in labelled))
        # search_agent final_answer with zero visit_page calls
        sa = [s for s in r['steps'] if s['agent'] == 'ToolCallingAgent']
        if sa:
            visited = any(s['role'] == 'tool' and 'visit_page' in s['content'][:60] for s in sa)
            fa = [s for s in sa if s['role'] == 'agent' and '"name": "final_answer"' in s['content']]
            if fa and not visited:
                snippet_only.append((r['id'], fa[0]['idx'], fa[0]['idx'] in labelled, ok[r['id']]))
    print(f'CodeAgent steps that print the task instead of calling search_agent: {len(print_task)}; labelled: {sum(1 for x in print_task if x[2])}')
    for x in print_task: print('  ', x)
    print(f'search_agent final_answer with no visit_page in its run: {len(snippet_only)}; labelled: {sum(1 for x in snippet_only if x[2])}; correct-ending: {sum(1 for x in snippet_only if x[3])}')
    for x in snippet_only: print('  ', x)
    # (f) SWE primary impact / final-step primaries
    swe = [r for r in recs if r['subset'] == 'swe_bench']
    print('SWE primary impact:', Counter(tuple(stats[r['id']]['primary_impact']) for r in swe), ' primary at last tool span:', sum(1 for r in swe if r['labels']['extra']['primary_idx'] is not None and r['steps'][r['labels']['extra']['primary_idx']]['meta']['span_name'] == 'FinalAnswerTool'))
    print('GAIA primary at FinalAnswerTool / final LLM:', sum(1 for r in gaia if r['labels']['extra']['primary_idx'] is not None and r['labels']['extra']['primary_idx'] >= len(r['steps']) - 3))
    # (g) evidence of primary quotes an execution error (symptom text)
    q = Counter()
    for r in recs:
        p = r['labels']['extra']['primary_idx']
        for e in r['labels']['extra']['errors']:
            if e['idx'] == p:
                ev = str(e['evidence'])
                q['quotes execution error' if re.search(r'Error when executing|TypeError|InterpreterError|Error:|Traceback', ev) else 'other'] += 1
    print('primary-error evidence quotes an execution error message:', dict(q))


if __name__ == '__main__':
    main()
