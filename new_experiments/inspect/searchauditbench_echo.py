#!/usr/bin/env python3
"""Query-echo pollution and empty-return fatigue around the critical step.
(1) 'echo' pages: search results whose URL is an instagram.com/popular/ tag page or whose title overlaps the query heavily
    (SEO pages that mirror the question). Count per trajectory, in the tool return right before the critical step, and
    whether the final answer's core string co-occurs with such a page.
(2) empty / failed tool returns: density in the 6 tool returns before k vs all tool returns.
(3) rationale message references: numbers 'message N' in the rationale other than k: earlier (evidence) or later.
(4) distance (in assistant steps) between the first assistant step after the first gold-bearing tool return and k.
Writes results/searchauditbench/echo.jsonl and prints tables."""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, append_jsonl, md_table, summarize  # noqa: E402
from loaders import load  # noqa: E402

ECHO_URL = re.compile(r'instagram\.com/popular/|facebook\.com/fb-answers/|/popular/[a-z0-9%\-]{20,}', re.I)
EMPTY = re.compile(r"^(no results? found|\[visit\]|the useful information .{0,400}?(403|404|forbidden|inaccessible|error|not accessible|could not|unable to|login|captcha|no (?:relevant )?(?:information|data|content))|a google search for .{0,300}? found 0 results)", re.I | re.S)


def tokens(s):
    return set(re.findall(r'[a-z0-9]{3,}|[一-鿿]{2}', str(s).lower()))


def main():
    idx = {json.loads(l)['id']: json.loads(l) for l in open(os.path.join(RESULTS, 'searchauditbench', 'index.jsonl'))}
    out = os.path.join(RESULTS, 'searchauditbench', 'echo.jsonl')
    if os.path.exists(out):
        os.remove(out)
    rows = []
    for r in load('searchauditbench'):
        ex = r['labels']['extra']
        k = ex['critical_idx']
        steps = r['steps']
        qt = tokens(r['task'])
        tools = [s for s in steps if s['role'] == 'tool']
        asst = [s['idx'] for s in steps if s['role'] == 'agent']
        echo_steps, echo_titles = [], 0
        empty_steps = []
        for s in tools:
            c = s['content']
            n_echo = len(ECHO_URL.findall(c))
            # titles with >= 70% of query tokens (for queries with >= 6 tokens)
            t_echo = 0
            if len(qt) >= 6:
                for m in re.finditer(r'\[([^\]]{10,200})\]\(http', c):
                    tt = tokens(m.group(1))
                    if len(tt) >= 4 and len(tt & qt) / len(tt) >= 0.7:
                        t_echo += 1
            if n_echo or t_echo:
                echo_steps.append(s['idx'])
                echo_titles += n_echo + t_echo
            if EMPTY.search(c.strip()[:600]) or len(c.strip()) < 80:
                empty_steps.append(s['idx'])
        prev_tools = [s['idx'] for s in tools if s['idx'] < k][-6:]
        prev_tools_all = [s['idx'] for s in tools if s['idx'] < k]
        rat = r['labels']['reason'] or ''
        refs = sorted({int(x) for x in re.findall(r'[Mm]essage (\d+)', rat)} - {k})
        row = {'id': r['id'], 'rc': r['labels']['categories'][0], 'k': k, 'n_tools': len(tools),
               'n_echo_steps': len(echo_steps), 'echo_steps': echo_steps[:40], 'echo_before_k': sum(1 for e in echo_steps if e < k),
               'echo_right_before_k': bool(prev_tools) and prev_tools[-1] in echo_steps,
               'n_empty': len(empty_steps), 'empty_rate_all': len(empty_steps) / max(1, len(tools)),
               'empty_rate_prev6': (sum(1 for e in prev_tools if e in empty_steps) / len(prev_tools)) if prev_tools else None,
               'empty_rate_before_k': (sum(1 for e in prev_tools_all if e in empty_steps) / len(prev_tools_all)) if prev_tools_all else None,
               'empty_rate_after_k': (sum(1 for s in tools if s['idx'] > k and s['idx'] in empty_steps) / max(1, sum(1 for s in tools if s['idx'] > k))) if any(s['idx'] > k for s in tools) else None,
               'rat_refs': refs, 'rat_refs_earlier': [x for x in refs if x < k], 'rat_refs_later': [x for x in refs if x > k]}
        i = idx[r['id']]
        if i['first_asst_after_gold'] is not None and i['first_asst_after_gold'] <= k:
            row['asst_gap_gold_to_k'] = asst.index(k) - asst.index(i['first_asst_after_gold'])
        else:
            row['asst_gap_gold_to_k'] = None
        rows.append(row)
        append_jsonl(out, row)
    n = len(rows)
    print('echo pages present in >=1 tool return:', sum(1 for x in rows if x['n_echo_steps']), f'/{n}')
    print('echo page in the tool return right before k:', sum(1 for x in rows if x['echo_right_before_k']), f'/{n}')
    print('by dataset:', {d: f"{sum(1 for x in rows if x['n_echo_steps'] and idx[x['id']]['dataset'] == d)}/{sum(1 for x in rows if idx[x['id']]['dataset'] == d)}" for d in sorted({idx[x['id']]['dataset'] for x in rows})})
    print('by rc echo-right-before-k:', {rc: f"{sum(1 for x in rows if x['echo_right_before_k'] and x['rc'] == rc)}/{sum(1 for x in rows if x['rc'] == rc)}" for rc in sorted({x['rc'] for x in rows})})
    e_all = [x['empty_rate_all'] for x in rows]; e6 = [x['empty_rate_prev6'] for x in rows if x['empty_rate_prev6'] is not None]
    eb = [x['empty_rate_before_k'] for x in rows if x['empty_rate_before_k'] is not None]; ea = [x['empty_rate_after_k'] for x in rows if x['empty_rate_after_k'] is not None]
    print('empty-return rate: all', summarize(e_all)['mean'], 'prev6', summarize(e6)['mean'], 'before k', summarize(eb)['mean'], 'after k', summarize(ea)['mean'])
    print('records with empty rate in prev6 > overall:', sum(1 for x in rows if x['empty_rate_prev6'] is not None and x['empty_rate_prev6'] > x['empty_rate_all']), 'lower:', sum(1 for x in rows if x['empty_rate_prev6'] is not None and x['empty_rate_prev6'] < x['empty_rate_all']))
    print('rationale refs: any', sum(1 for x in rows if x['rat_refs']), 'earlier only', sum(1 for x in rows if x['rat_refs_earlier'] and not x['rat_refs_later']), 'later only', sum(1 for x in rows if x['rat_refs_later'] and not x['rat_refs_earlier']), 'both', sum(1 for x in rows if x['rat_refs_later'] and x['rat_refs_earlier']))
    gaps = [x['asst_gap_gold_to_k'] for x in rows if x['asst_gap_gold_to_k'] is not None]
    print('assistant-step gap from first chance after gold-bearing return to k:', summarize(gaps), Counter(min(g, 10) for g in gaps))


if __name__ == '__main__':
    main()
