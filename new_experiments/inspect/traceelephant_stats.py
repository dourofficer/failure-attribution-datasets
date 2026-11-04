#!/usr/bin/env python3
"""TraceElephant targeted statistics beyond length/position:
 (c) Captain-Agent: is the gold step the first specialist step, and does the run contain any tool/code execution before it?
 (d) repetition (near-duplicate steps) before vs after the gold step, per subset;
 (e) SWE-Agent: first source edit vs gold; did the reproduction script ever reproduce before the first fix;
 (g) final answer == ground truth despite 'failed' label.
Writes results/traceelephant/stats.json."""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, write_json, md_table, summarize  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402


def norm(t):
    return re.sub(r'\s+', ' ', re.sub(r'call_[A-Za-z0-9]+|step_\d+_image_\d+', '', t)).strip().lower()[:2000]


def jacc(a, b):
    A, B = set(a.split()), set(b.split())
    return len(A & B) / max(1, len(A | B))


def main():
    recs = load('traceelephant')
    out = {}
    # (c) captain
    cap = [r for r in recs if r['subset'] == 'captain-agent' and r['labels']['error_steps']]
    c = Counter()
    for r in cap:
        g = error_step(r)
        first_spec = next((s['idx'] for s in r['steps'] if s['agent'] != 'Orchestrator'), None)
        has_code_before = any('```python' in s['content'] or '```sh' in s['content'] or 'Action:' in s['content'] for s in r['steps'][:g])
        has_code_at = '```python' in r['steps'][g]['content'] or 'Action:' in r['steps'][g]['content']
        any_code = any('```python' in s['content'] or 'Action:' in s['content'] for s in r['steps'])
        c['gold_is_first_specialist'] += g == first_spec
        c['code_before_gold'] += has_code_before
        c['code_at_gold'] += has_code_at
        c['no_code_anywhere'] += not any_code
        c['gold_is_orchestrator'] += r['steps'][g]['agent'] == 'Orchestrator'
        c['n'] += 1
    out['captain'] = dict(c)
    print('captain:', dict(c))
    # (d) repetition before/after gold
    rep = {}
    for sub in ('magentic-one', 'captain-agent', 'swe-agent'):
        rs = [r for r in recs if r['subset'] == sub and r['labels']['error_steps']]
        before = after = nb = na = 0
        per = []
        for r in rs:
            g = error_step(r)
            seen = []
            dup = []
            for s in r['steps']:
                t = norm(s['content'])
                is_dup = any(jacc(t, p) > 0.9 for p in seen[-12:]) if t else False
                dup.append(is_dup)
                seen.append(t)
            b = [d for i, d in enumerate(dup) if i < g]
            a = [d for i, d in enumerate(dup) if i > g]
            before += sum(b); nb += len(b); after += sum(a); na += len(a)
            per.append({'id': r['id'], 'dup_before': sum(b), 'n_before': len(b), 'dup_after': sum(a), 'n_after': len(a)})
        rep[sub] = {'dup_rate_before': before / max(1, nb), 'dup_rate_after': after / max(1, na), 'n_before': nb, 'n_after': na,
                    'records_with_dup_after_but_not_before': sum(1 for p in per if p['dup_after'] > 0 and p['dup_before'] == 0),
                    'records_with_dup_before': sum(1 for p in per if p['dup_before'] > 0), 'n': len(rs)}
        print(sub, rep[sub])
    out['repetition'] = rep
    # (e) swe
    swe = [r for r in recs if r['subset'] == 'swe-agent']
    c = Counter(); offs = []
    for r in swe:
        g = error_step(r)
        first_src_edit = None
        first_edit = None
        repro_ok_before_fix = False
        for s in r['steps']:
            m = re.search(r'\\"command\\":\\"(str_replace|create|insert)\\",\\"path\\":\\"([^\\"]+)', s['content'])
            if m:
                path = m.group(2)
                if first_edit is None:
                    first_edit = s['idx']
                if first_src_edit is None and '/testbed/' in path and not re.search(r'reproduce|test_|/tests/|repro', path):
                    first_src_edit = s['idx']
        c['n'] += 1
        c['gold==first_src_edit'] += g == first_src_edit
        c['gold==first_edit'] += g == first_edit
        c['gold<first_src_edit'] += first_src_edit is not None and g < first_src_edit
        c['gold>first_src_edit'] += first_src_edit is not None and g > first_src_edit
        c['no_src_edit'] += first_src_edit is None
        if first_src_edit is not None:
            offs.append(g - first_src_edit)
        # gold step type: edit of source / edit of repro / bash / text
        s = r['steps'][g]['content']
        m = re.search(r'\\"command\\":\\"(str_replace|create|insert|view)\\",\\"path\\":\\"([^\\"]+)', s)
        if m:
            kind = ('view' if m.group(1) == 'view' else 'edit') + (':repro/test' if re.search(r'reproduce|test_|/tests/|repro', m.group(2)) else ':src')
        elif '"name": "bash"' in s or '"name":"bash"' in s:
            kind = 'bash'
        elif 'submit' in s[:300]:
            kind = 'submit'
        else:
            kind = 'text'
        c['gold_kind:' + kind] += 1
    out['swe'] = {'counts': dict(c), 'gold_minus_first_src_edit': summarize(offs)}
    print('swe:', dict(c), summarize(offs))
    # (g) final answer vs gt
    c = Counter()
    for r in recs:
        if r['subset'] == 'swe-agent' or not r.get('ground_truth'):
            continue
        fo = r.get('final_output') or ''
        m = re.search(r'## ANSWER\s*\n(.*?)(?:\n## REASON|\Z)', fo, re.S)
        ans = (m.group(1) if m else fo).strip().strip('"').lower()
        gt = str(r['ground_truth']).strip().lower()
        c['n'] += 1
        c['no_final'] += not fo
        c['gt_in_answer'] += bool(ans) and gt in ans
        c['gt_in_any_step'] += any(gt in s['content'].lower() for s in r['steps']) and len(gt) > 3
    out['final_vs_gt'] = dict(c)
    print('final vs gt:', dict(c))
    write_json(os.path.join(RESULTS, 'traceelephant', 'stats.json'), out)


if __name__ == '__main__':
    main()
