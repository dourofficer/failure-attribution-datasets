#!/usr/bin/env python3
"""LongRCA targeted statistics (beyond length/position).
Writes results/longrca/stats.json and prints tables:
 1. heuristic classification of mistake_reason texts (causal link / no link / redundant work / hand-off / verification)
 2. root step type (hand-off instruction, tool call, final answer, plan, ...) and whether the blamed role speaks again after the root
 3. verifier / judge activity after the root: n messages, verdict words (pass/success vs fail), evaluator 'Run finished' text
 4. visible error signs (tool errors, empty results, repeated identical tool calls, 'retry') before vs after the root, per step
 5. false-success: final DiagnostAgent/planner message claims SUCCESS while the run failed
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, md_table, summarize  # noqa: E402
from common.schema import error_step  # noqa: E402
from loaders import load  # noqa: E402

OUT = os.path.join(RESULTS, 'longrca')

# ---- 1. reason classification (heuristic) ----
RX = {
    'redundant': re.compile(r'redundan|unnecessar|wasted|waste |repeat(ed|s)? (the )?(same|search|call|query)|duplicat|already (been )?(done|verified|confirmed|performed|searched|checked)|re-?(ran|run|search|check|verif)|again|loop|excessive|superfluous|instead of (proceeding|moving on|finish)|should have (finished|stopped|moved on|proceeded)|delay', re.I),
    'handoff': re.compile(r'hand-?off|instruct(ion|ed)|delegat|assign|dispatch|next speaker|told the|asked the', re.I),
    'verification': re.compile(r'verif|judge|validat|check(ed|ing)? (the )?(result|output|plan|answer)|confirm', re.I),
    'causal': re.compile(r'(led|leads|leading) to|result(ed|ing|s) in|caus(ed|es|ing)|therefore|consequen|so that|which (made|meant|prevented|broke)|prevent|fail(ure|ed) (to|because)|because|hence|thus|ultimately|final (answer|plan|output)|wrong (answer|plan|result)|incorrect (final|answer|plan)|propagat|downstream|mis(led|lead)|derail|blocked|unable to|could not|never', re.I),
    'final_answer': re.compile(r'final (answer|plan|output|report)|reported|submitted|concluded|declared', re.I),
}


def classify_reason(t):
    t = t or ''
    tags = {k: bool(rx.search(t)) for k, rx in RX.items()}
    if tags['redundant'] and not tags['causal']:
        c = 'redundant_no_link'
    elif tags['redundant']:
        c = 'redundant_with_link'
    elif tags['causal']:
        c = 'causal_link'
    else:
        c = 'no_link'
    return c, tags


VERIFIER = {'JudgeAgent', 'verifier_agent', 'Verification_Expert', 'DiagnostAgent (-> JudgeAgent)'}
PASS_RX = re.compile(r'\b(STATUS:\s*SUCCESS|all tests? pass|tests? passed|PASS(ED)?\b|verified successfully|is correct|looks correct|no issues|approved|"status":\s*"SUCCESS"|"status": "complete"|complete and correct|satisf(ies|ied))', re.I)
FAIL_RX = re.compile(r'\b(STATUS:\s*FAIL|FAIL(ED|URE)?\b|tests? fail|not (correct|satisf)|incorrect|violat|does not (match|satisfy|meet)|missing|error|mismatch|rejected|"status":\s*"(FAIL|UNKNOWN_ERROR|NOT_FOUND)")', re.I)
TOOL_ERR_RX = re.compile(r'(Traceback|Error:|error:|Exception|not found|No such file|No results|no results|returned no|empty|Invalid|invalid|timed out|Timeout|failed|FAILED|command not found|Permission denied|404|rate limit)', re.I)
RETRY_RX = re.compile(r'\b(retry|retrying|try again|let me try|another approach|alternative|instead)\b', re.I)
TOOLCALL_RX = re.compile(r'^Tool call: (\w+)\nArguments:\n(.*)$', re.S)


def tool_call_key(c):
    m = TOOLCALL_RX.match(c.strip())
    if m:
        return (m.group(1), re.sub(r'\s+', ' ', m.group(2))[:400])
    m = re.search(r'```(bash|python|view|str_replace|create|edit)[^\n]*\n(.*?)```', c, re.S)
    if m:
        return (m.group(1), re.sub(r'\s+', ' ', m.group(2))[:400])
    return None


def main():
    recs = load('longrca')
    rows = []
    for r in recs:
        g = error_step(r)
        steps = r['steps']
        n = len(steps)
        rs = steps[g]
        base = r['labels']['error_agent']
        cls, tags = classify_reason(r['labels']['reason'])
        # root type
        c = rs['content']
        is_handoff = '(->' in rs['agent'] or rs['content'].startswith('Orchestration target') or 'Next speaker' in c[:60]
        is_toolcall = tool_call_key(c) is not None
        is_final = bool(re.search(r'finish\(|Final answer|###STOP###|"days": \[', c)) and g > n * 0.5
        # does the blamed role act again after the root?
        later_same = [s for s in steps[g + 1:] if s['agent'] == rs['agent'] or s['meta'].get('base_agent') == rs['meta'].get('base_agent')]
        # verifier messages after root
        ver_after = [s for s in steps[g + 1:] if s['meta'].get('base_agent') in VERIFIER or s['agent'] in VERIFIER]
        ver_before = [s for s in steps[:g] if s['meta'].get('base_agent') in VERIFIER or s['agent'] in VERIFIER]
        ver_pass = sum(1 for s in ver_after if PASS_RX.search(s['content']) and not FAIL_RX.search(s['content'][:400]))
        ver_fail = sum(1 for s in ver_after if FAIL_RX.search(s['content']))
        # evaluator / run finished
        run_fin = next((s['content'] for s in reversed(steps) if s['content'].startswith('Run finished')), None)
        # final agent message claims success?
        last_agent = next((s for s in reversed(steps) if s['role'] == 'agent'), None)
        claims_success = bool(last_agent and PASS_RX.search(last_agent['content']) and not re.search(r'UNKNOWN_ERROR|budget|FAIL', last_agent['content']))
        # visible error signs before / after root (tool steps)
        def signs(seg):
            tool = [s for s in seg if s['role'] == 'tool']
            ag = [s for s in seg if s['role'] == 'agent']
            te = sum(1 for s in tool if TOOL_ERR_RX.search(s['content'][:2000]))
            rt = sum(1 for s in ag if RETRY_RX.search(s['content']))
            keys = [tool_call_key(s['content']) for s in ag]
            keys = [k for k in keys if k]
            dup = len(keys) - len(set(keys))
            return {'n': len(seg), 'n_tool': len(tool), 'n_agent': len(ag), 'tool_err': te, 'retry': rt, 'dup_calls': dup}
        before, after = signs(steps[:g]), signs(steps[g + 1:])
        # is root itself a visible error? (tool error at g+1)
        nxt = steps[g + 1]['content'] if g + 1 < n else ''
        root_followed_by_tool_err = bool(steps[g + 1]['role'] == 'tool' and TOOL_ERR_RX.search(nxt[:2000])) if g + 1 < n else False
        rows.append({'id': r['id'], 'src': r['subset'], 'n': n, 'g': g, 'rel': g / max(1, n - 1), 'agent': base, 'root_agent': rs['agent'],
                     'reason_cls': cls, 'reason_tags': tags, 'reason': r['labels']['reason'], 'root_len': len(c),
                     'root_is_handoff': is_handoff, 'root_is_toolcall': is_toolcall, 'root_is_final': is_final,
                     'blamed_acts_again': len(later_same), 'ver_after': len(ver_after), 'ver_before': len(ver_before),
                     'ver_pass_after': ver_pass, 'ver_fail_after': ver_fail, 'run_finished': (run_fin or '')[:300],
                     'claims_success': claims_success, 'before': before, 'after': after,
                     'root_followed_by_tool_err': root_followed_by_tool_err, 'mini': r['meta']['mini']})
    json.dump(rows, open(os.path.join(OUT, 'stats.json'), 'w'), ensure_ascii=False, indent=0)
    srcs = sorted(set(x['src'] for x in rows))
    def pct(xs, f):
        xs = list(xs); return f'{100 * sum(1 for x in xs if f(x)) / max(1, len(xs)):.0f}%'
    print('## 1. reason classification (heuristic)')
    tbl = []
    for s in srcs + ['ALL']:
        xs = [x for x in rows if s == 'ALL' or x['src'] == s]
        cnt = collections.Counter(x['reason_cls'] for x in xs)
        tbl.append([s, len(xs)] + [f"{cnt[k]} ({100 * cnt[k] / len(xs):.0f}%)" for k in ('causal_link', 'no_link', 'redundant_with_link', 'redundant_no_link')] +
                   [pct(xs, lambda x: x['reason_tags']['handoff']), pct(xs, lambda x: x['reason_tags']['verification']), pct(xs, lambda x: x['reason_tags']['final_answer'])])
    print(md_table(['source', 'n', 'causal link', 'no link', 'redundant+link', 'redundant, no link', 'mentions hand-off', 'mentions verif.', 'mentions final answer'], tbl))
    print('\n## 2. root step type and blamed role afterwards')
    tbl = []
    for s in srcs + ['ALL']:
        xs = [x for x in rows if s == 'ALL' or x['src'] == s]
        tbl.append([s, len(xs), pct(xs, lambda x: x['root_is_handoff']), pct(xs, lambda x: x['root_is_toolcall']), pct(xs, lambda x: x['root_is_final']),
                    pct(xs, lambda x: x['blamed_acts_again'] > 0), summarize([x['blamed_acts_again'] for x in xs])['median'], pct(xs, lambda x: x['root_followed_by_tool_err'])])
    print(md_table(['source', 'n', 'root = hand-off/orchestration', 'root = tool call', 'root = final output', 'blamed role acts again', 'median #later msgs by blamed', 'root followed by tool error'], tbl))
    print('\n## 3. verifier / judge after the root')
    tbl = []
    for s in srcs + ['ALL']:
        xs = [x for x in rows if s == 'ALL' or x['src'] == s]
        tbl.append([s, len(xs), pct(xs, lambda x: x['ver_after'] > 0), summarize([x['ver_after'] for x in xs])['median'],
                    pct(xs, lambda x: x['ver_pass_after'] > 0), pct(xs, lambda x: x['ver_fail_after'] > 0),
                    pct(xs, lambda x: x['ver_pass_after'] > 0 and x['ver_fail_after'] == 0), pct(xs, lambda x: x['claims_success'])])
    print(md_table(['source', 'n', 'any verifier msg after root', 'median # verifier msgs after', 'verifier says pass after root', 'verifier says fail after root', 'pass only (never fail)', 'last agent msg claims success'], tbl))
    print('\n## 4. visible error signs before vs after root (rates per step)')
    tbl = []
    for s in srcs + ['ALL']:
        xs = [x for x in rows if s == 'ALL' or x['src'] == s]
        def rate(key, part, denom):
            num = sum(x[part][key] for x in xs); den = sum(x[part][denom] for x in xs)
            return f'{100 * num / max(1, den):.1f}%'
        tbl.append([s, rate('tool_err', 'before', 'n_tool'), rate('tool_err', 'after', 'n_tool'), rate('retry', 'before', 'n_agent'), rate('retry', 'after', 'n_agent'),
                    rate('dup_calls', 'before', 'n_agent'), rate('dup_calls', 'after', 'n_agent')])
    print(md_table(['source', 'tool-err before', 'tool-err after', 'retry-lang before', 'retry-lang after', 'dup tool calls before', 'dup after'], tbl))
    print('\n## 5. Run finished texts (first 120 chars) most common per source')
    for s in srcs:
        xs = [x for x in rows if x['src'] == s]
        cnt = collections.Counter(re.sub(r'\d+', '#', x['run_finished'][:60]) for x in xs)
        print(s, cnt.most_common(5))


if __name__ == '__main__':
    main()
