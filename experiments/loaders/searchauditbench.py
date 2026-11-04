"""SearchAuditBench (SearchAuditor, arXiv:2608.05212) loader.

File: data/searchauditbench/extracted/benchmark_data_1243.jsonl (313 MB, one failed run per line). The file is
streamed line by line; `limit` stops early, `subset` (= the `dataset` tag) filters while streaming.

Steps
  One trajectory message = one step, in file order. `message_index` is 0-based and equals the list position
  in all 1,243 records (verified), so native_idx = message_index = our idx.
  role mapping: system -> 'system', user -> 'user', assistant -> 'agent', tool -> 'tool'.
  agent = the role name ('assistant'), or 'tool:<name>' for tool returns.
  content rendering (nothing truncated):
      assistant:  "[reasoning]\n<reasoning_content>\n\n[content]\n<content>\n\n[tool_call] <tool_name>(<json tool_arguments>)  (id=<tool_call_id>)" (sections omitted when empty)
      tool:       "[tool_result <name>] (call_id=<tool_call_id>)\n<content>"
      system/user: "<content>"
  Scalar bookkeeping fields on a message (finish_reason, model_family, text_tool_call_fallback,
  finalize_force/finalize_repair/heuristic_answer_wrap, answer_block_normalized, tool_call_id, name) go to
  step meta; tool_calls also go to meta['tool_calls'] verbatim.

Index mapping
  faulty_step = critical_step.message_index (always an assistant message; verified 1243/1243).
  faulty_steps = [faulty_step]. The tolerance span is NOT folded into faulty_steps; it is kept as
  extra['tolerance_span'] = {'start': span_start_message_index, 'end': span_end_message_index} (inclusive,
  same idx space; verified start <= k <= end < n_messages for all records).

Labels
  category = root_cause_primary (6 classes); reason = rationale.failure_rationale;
  extra = {tolerance_span, root_cause_primary, failure_rationale, repair_directive, repair_rubrics,
           predicted_answer}.
  ground_truth = gold_answer. NOTE: in the official auditing task the gold answer is hidden from the auditor
  (QC only); it is kept here for evaluation, so an auditor prompt must not include it.
  final_output = predicted_answer; outcome = 0 (failed-only); task = query.
  subset = `dataset` tag (BrowseComp, BrowseComp English, BrowseComp-ZH, DeepSearchQA, SEALQA,
  XBench-DeepSearch); system = 'SearchAuditor scaffold (search/visit)'; meta = {model, index, n_messages,
  n_assistant, source_file}. id = str(index) (0..1242, unique).
"""
import json
import os

SLUG = "searchauditbench"
FILE = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/searchauditbench/extracted/benchmark_data_1243.jsonl"
ROLE = {"system": "system", "user": "user", "assistant": "agent", "tool": "tool"}
_CORE = {"role", "content", "reasoning_content", "tool_calls", "message_index"}


def _render(m):
    role = m.get("role")
    content = m.get("content")
    if role == "assistant":
        parts = []
        if m.get("reasoning_content"):
            parts.append("[reasoning]\n" + m["reasoning_content"])
        if content:
            parts.append("[content]\n" + content)
        for c in m.get("tool_calls") or []:
            args = c.get("tool_arguments")
            args_s = json.dumps(args, ensure_ascii=False) if not isinstance(args, str) else args
            cid = c.get("tool_call_id")
            parts.append(f"[tool_call] {c.get('tool_name')}({args_s})" + (f"  (id={cid})" if cid else ""))
        return "\n\n".join(parts)
    if role == "tool":
        head = f"[tool_result {m.get('name') or ''}]".replace(" ]", "]")
        if m.get("tool_call_id"):
            head += f" (call_id={m['tool_call_id']})"
        return head + "\n" + (content or "")
    return content or ""


def _convert(d):
    steps = []
    for i, m in enumerate(d["trajectory"]):
        meta = {k: v for k, v in m.items() if k not in _CORE}
        if m.get("tool_calls"):
            meta["tool_calls"] = m["tool_calls"]
        role = m.get("role")
        agent = role if role != "tool" else f"tool:{m.get('name') or ''}"
        steps.append({"idx": i, "native_idx": m.get("message_index", i), "agent": agent,
                      "role": ROLE.get(role, "system"), "content": _render(m), "meta": meta})
    cs = d["critical_step"]
    k = cs["message_index"]
    ok = isinstance(k, int) and 0 <= k < len(steps)
    return {
        "dataset": SLUG,
        "id": str(d["index"]),
        "subset": d.get("dataset") or "",
        "system": "SearchAuditor scaffold (search/visit)",
        "task": d.get("query") or "",
        "ground_truth": d.get("gold_answer"),
        "final_output": d.get("predicted_answer"),
        "outcome": 0,
        "steps": steps,
        "annotation": {
            "faulty_step": k if ok else None,
            "faulty_steps": [k] if ok else [],
            "faulty_agent": steps[k]["agent"] if ok else None,
            "category": d.get("root_cause_primary"),
            "reason": (d.get("rationale") or {}).get("failure_rationale"),
            "extra": {
                "tolerance_span": {"start": cs.get("span_start_message_index"), "end": cs.get("span_end_message_index")},
                "root_cause_primary": d.get("root_cause_primary"),
                "failure_rationale": (d.get("rationale") or {}).get("failure_rationale"),
                "repair_directive": d.get("repair_directive"),
                "repair_rubrics": d.get("repair_rubrics"),
                "predicted_answer": d.get("predicted_answer"),
            },
        },
        "meta": {
            "model": d.get("model"),
            "index": d.get("index"),
            "n_messages": len(steps),
            "n_assistant": sum(1 for s in steps if s["role"] == "agent"),
            "source_file": "extracted/benchmark_data_1243.jsonl",
            "gold_answer_note": "gold_answer is hidden from auditors in the official task; kept in ground_truth for scoring only",
        },
    }


def load(limit=None, subset=None):
    n = 0
    with open(FILE, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            d = json.loads(line)
            if subset is not None and d.get("dataset") != subset:
                continue
            yield _convert(d)
            n += 1
            if limit is not None and n >= limit:
                return
