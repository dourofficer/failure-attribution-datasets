#!/usr/bin/env python3
"""Build a compact per-record index of SearchAuditBench (loads the 313 MB jsonl once) -> results/searchauditbench/index.jsonl
Per record: id, model, dataset, n_msgs, n_asst, critical_idx, span, root cause, whether critical is the final answer,
where the critical step sits inside its tolerance span, tool-return stats, gold-answer string matches in tool returns
before/after the critical step (strict: only gold strings >= 5 chars or with letters/CJK; numeric golds matched as whole
tokens), answer-origin (first message in which the predicted core answer appears: agent vs tool), doubt-word density in
reasoning, repeated queries, empty/failed tool returns, rationale keyword classes."""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common.util import RESULTS, append_jsonl  # noqa: E402
from loaders import load  # noqa: E402

DOUBT = re.compile(r"\b(not sure|unsure|uncertain|assume|assuming|likely|probably|perhaps|maybe|might be|could be|guess|unclear|cannot (?:find|verify|confirm)|can't (?:find|verify|confirm)|no (?:direct )?evidence|seems)\b|不确定|可能|也许|大概|假设|猜测|似乎|无法(?:确认|找到|验证)", re.I)
EMPTY = re.compile(r"(no results? found|error|failed|timeout|403|404|could not|unable to|empty|inaccessible)", re.I)
RAT_CLASSES = {
    'vintage': re.compile(r'vintage|version|outdated|as of|edition|time[- ]sensitive|current (?:value|data)|later (?:data|version)|date mismatch|mismatched', re.I),
    'recovery': re.compile(r'despite|later (?:re|reconsider)|had (?:already|earlier)|although|even though|nevertheless|instead of', re.I),
    'unsupported': re.compile(r'without any retrieved|no retrieved|unsupported|never (?:opens?|visits?|retriev|search)|from memory|fabricat|invent', re.I),
    'commit': re.compile(r'commits?|finaliz|lock(?:s|ed)? in|prematurely', re.I),
    'evidence_visible': re.compile(r'evidence was (?:visible|available|present)|already (?:surfaced|shown|contained|retrieved|visible)|had (?:already )?(?:surfaced|retrieved|shown|returned)', re.I),
}


def norm(s):
    return re.sub(r'[^0-9a-z一-鿿.%]+', ' ', str(s).lower()).strip()


def is_numeric(v):
    return re.fullmatch(r'[0-9.% ]+', v) is not None


def gold_variants(g):
    g = str(g).strip()
    vs = {norm(g), norm(re.sub(r'\(.*?\)', '', g))}
    for part in re.split(r'\s*(?:/|\bor\b|;)\s*', g):
        if len(norm(part)) >= 3:
            vs.add(norm(part))
    out = set()
    for v in vs:
        if not v:
            continue
        if is_numeric(v):
            out.add(v)  # matched as whole token
        elif len(v) >= 5 or re.search(r'[一-鿿]{2,}', v):
            out.add(v)
    return out


def contains(c, v):
    if is_numeric(v):
        return re.search(r'(?<![0-9.])' + re.escape(v) + r'(?![0-9])', c) is not None
    return v in c


def core_answer(fo):
    m = re.search(r'<answer>(.*?)</answer>', str(fo), re.S)
    a = (m.group(1) if m else str(fo)).strip()
    a = re.sub(r'[*_`#]', '', a).strip()
    return a


def main():
    out = os.path.join(RESULTS, 'searchauditbench', 'index.jsonl')
    if os.path.exists(out):
        os.remove(out)
    recs = load('searchauditbench')
    for r in recs:
        ex = r['labels']['extra']
        k = ex['critical_idx']
        steps = r['steps']
        asst = [s['idx'] for s in steps if s['role'] == 'agent']
        tools = [s for s in steps if s['role'] == 'tool']
        last_asst = asst[-1]
        gv = gold_variants(r['ground_truth'])
        ca = core_answer(r['final_output'])
        ca_n = norm(ca)
        first_gold_tool = None
        n_gold_before = n_gold_after = 0
        gold_tool_idxs = []
        for s in tools:
            c = norm(s['content'])
            if any(contains(c, v) for v in gv):
                gold_tool_idxs.append(s['idx'])
                if first_gold_tool is None:
                    first_gold_tool = s['idx']
                if s['idx'] < k:
                    n_gold_before += 1
                else:
                    n_gold_after += 1
        # answer origin: first step (any role) whose normalised content contains the core answer (only if core answer short)
        origin_idx = origin_role = None
        if 3 <= len(ca_n) <= 60:
            for s in steps[2:]:
                c = norm(s['content'])
                if s['idx'] == last_asst:
                    break
                if contains(c, ca_n) if is_numeric(ca_n) else ca_n in c:
                    origin_idx, origin_role = s['idx'], s['role']
                    break
        doubt = {}
        for s in steps:
            if s['role'] == 'agent':
                doubt[s['idx']] = 1000.0 * len(DOUBT.findall(s['content'])) / max(1, len(s['content']))
        queries = []
        for s in steps:
            if s['role'] == 'agent':
                m = re.search(r'Tool calls: (\[.*\])\s*$', s['content'], re.S)
                if m:
                    try:
                        for tc in json.loads(m.group(1)):
                            args = tc.get('tool_arguments')
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except Exception:
                                    pass
                            queries.append((s['idx'], tc.get('tool_name'), json.dumps(args, ensure_ascii=False)[:300]))
                    except Exception:
                        pass
        qc = Counter(q[2] for q in queries)
        n_repeat = sum(c - 1 for c in qc.values() if c > 1)
        empty_tools = [s['idx'] for s in tools if EMPTY.search(s['content'][:400]) and len(s['content']) < 700]
        span = ex['span_idxs']
        span_roles = [steps[j]['role'] for j in span]
        agent_in_span = [j for j in span if steps[j]['role'] == 'agent']
        pos_in_span = 'only' if len(agent_in_span) == 1 else ('first' if agent_in_span[0] == k else ('last' if agent_in_span[-1] == k else 'middle'))
        prev_tool = next((s for s in reversed(steps[:k]) if s['role'] == 'tool'), None)
        prev_tool_kind = prev_tool['agent'] if prev_tool else None
        rat = r['labels']['reason'] or ''
        row = {'id': r['id'], 'model': r['meta']['backbone'], 'dataset': r['subset'], 'n_msgs': len(steps), 'n_asst': len(asst),
               'critical_idx': k, 'span_start': ex['span_start'], 'span_end': ex['span_end'], 'span_len': len(span),
               'span_n_agent': span_roles.count('agent'), 'span_n_tool': span_roles.count('tool'), 'span_ends_at_last': ex['span_end'] == steps[-1]['idx'],
               'span_starts_with_tool': bool(span) and steps[span[0]]['role'] == 'tool', 'pos_in_span': pos_in_span,
               'rc': r['labels']['categories'][0], 'critical_is_final': k == last_asst, 'last_asst': last_asst,
               'rel_pos': k / max(1, last_asst), 'asst_rank_of_critical': asst.index(k) if k in asst else None,
               'n_tools': len(tools), 'n_search': sum(1 for q in queries if q[1] == 'search'), 'n_visit': sum(1 for q in queries if q[1] == 'visit'),
               'n_repeat_queries': n_repeat, 'empty_tools': empty_tools, 'n_empty_tools': len(empty_tools),
               'gold': str(r['ground_truth'])[:200], 'pred': str(r['final_output'])[:300], 'core_answer': ca[:120], 'gold_in_pred': any(contains(norm(ca), v) for v in gv),
               'first_gold_tool': first_gold_tool, 'gold_tool_idxs': gold_tool_idxs[:30], 'n_gold_tool_before': n_gold_before, 'n_gold_tool_after': n_gold_after,
               'first_asst_after_gold': next((a for a in asst if first_gold_tool is not None and a > first_gold_tool), None),
               'origin_idx': origin_idx, 'origin_role': origin_role, 'origin_checked': 3 <= len(ca_n) <= 60,
               'doubt_at': doubt.get(k, 0), 'doubt_before_mean': (sum(v for i, v in doubt.items() if i < k) / max(1, sum(1 for i in doubt if i < k))),
               'doubt_after_mean': (sum(v for i, v in doubt.items() if i > k) / max(1, sum(1 for i in doubt if i > k))),
               'doubt_final': doubt.get(last_asst, 0), 'doubt_argmax': max(doubt, key=doubt.get) if doubt else None,
               'critical_chars': len(steps[k]['content']), 'critical_has_tool_call': 'Tool calls:' in steps[k]['content'],
               'critical_tool': next((q[1] for q in queries if q[0] == k), None), 'prev_tool_kind': prev_tool_kind,
               'rat_classes': [c for c, rx in RAT_CLASSES.items() if rx.search(rat)],
               'reason': rat[:700], 'repair': (ex.get('repair_directive') or '')[:400]}
        append_jsonl(out, row)
    print('wrote', out, len(recs))


if __name__ == '__main__':
    main()
