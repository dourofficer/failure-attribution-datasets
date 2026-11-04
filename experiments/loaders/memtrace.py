"""Loader for MemTraceBench (Deng et al. 2026, arXiv 2605.28732; HF zjunlp/MemTraceBench, MIT).

Source: data/memtrace/{rag,mem0,evermemos,long_context}/<source>_<conversation>.json — 103 serialised `smartcomment`
execution graphs (6 MB .. 532 MB each; 6 GB in total).  Each file = one (memory system, conversation) run and holds
data.nodes (variables: messages, memory units, prompts, llm responses, retrieval results, prediction ...),
data.operations (op_id, op_name, category, comment, session_id, created_at, metadata), data.edges
(op_id, source_full_node_id -> target_full_node_id), data.sessions and data.annotations (query, golden_answers,
prediction(_id), source_evidence(_ids), final_error_type, final_op_id, reason).

One trajectory per annotation.  The 160 memory-system failures (final_error_type in ExtractionError / UpdateError /
DeletionError / RetrievalError / ResponseError; 40 per system) get subset = memory system (rag / mem0 / evermemos /
long_context) and outcome = 0.  The 75 AnnotationError + 3 LLMAsAJudgeError cases are kept with subset = 'excluded'
and outcome = None (their memory system is in meta.memory_system); they have no final_op_id.

Steps = the backward dependency slice of the prediction node: every operation that owns an edge on a path into
`prediction_id` (the same materialisation as scripts/analyze_memtrace.py), ordered chronologically by the operation's
created_at (the graph is a DAG built in execution order, so this is a topological order).  One operation = one step;
native_idx = op_id; agent = op_name; role = 'agent' for LLM-backed operations (fact/memory extraction, update
decisions, boundary detection, agentic retrieval rounds with LLM sufficiency check / query refinement,
question-answering, llm-judge: any op whose metadata names an llm_model, plus question-answering/llm-judge) and
'tool' for everything else (vector / hybrid search, reranking, message-buffer bookkeeping, memory_update by token
window, add/finalize of memory units).  content = op_name/category/session + the op's description + its input and
output variable values (source / target nodes of its edges).

CONTENT IS TRIMMED — the one dataset where full content is impractical: slices run up to 3,661 operations and the raw
node values of one slice sum to up to 346 M chars (message buffers and prompts are repeated on every operation).  Each
individual variable value longer than head+tail chars is cut to its first `head` (default 4000) and last `tail`
(default 500) chars with an explicit '…[trimmed N chars]…' marker; the step gets meta.trimmed = True and the
trajectory meta.trimmed = True if any step was trimmed.  Pass head/tail to load() to change the budget (head=None
disables trimming).  Nothing else is dropped: every operation of the slice is a step and every input/output node
of that operation is listed.

Label mapping: faulty_step = idx of the step whose op_id == final_op_id when that operation is inside the slice;
otherwise None with annotation.extra['op_outside_slice'] = True (20 of 160 cases: mostly Mem0 extraction errors
where the missed fact never produced a memory unit, so no edge connects the faulty operation to the prediction).
faulty_agent = op_name of final_op_id (also when outside the slice); category = final_error_type; reason = reason.
extra: query_id, prediction_id, golden_answers_id, source_evidence(_ids), final_op_id/name/category, the global
position of the faulty op among all operations of the graph, slice size.

Memory: files are loaded one at a time with json.load and released before the next one (the EverMemOS / RealMem
graphs need several GB while parsed).  `limit` stops without opening further files.  Order: split order
rag, mem0, evermemos, long_context; files sorted by name; annotations in file order.  subset may be a system name or
'excluded'.
"""
import ast
import collections
import gc
import glob
import json
import os

SLUG = "memtrace"
ROOT = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/memtrace"
SPLITS = ["rag", "mem0", "evermemos", "long_context"]
SYSTEM_NAMES = {"rag": "Naive RAG", "mem0": "Mem0", "evermemos": "EverMemOS", "long_context": "Long-Context"}
MEMORY_ERRORS = {"ExtractionError", "UpdateError", "DeletionError", "RetrievalError", "ResponseError"}
LLM_OP_NAMES = {"question-answering", "llm-judge", "memory_system.extract_facts", "memory_system.update_memory_decision",
                "memory_system.extract_memory", "evermemos.boundary_detection",
                "memory_system.agentic_round1_bundle", "memory_system.agentic_round2_bundle"}


def _role(op):
    md = op.get("metadata") or {}
    if isinstance(md, dict) and md.get("llm_model"):
        return "agent"
    return "agent" if op.get("op_name") in LLM_OP_NAMES else "tool"


def _lit(s):
    """Annotation fields are Python reprs ("'text'", "['a']"); return the parsed object or the raw string."""
    if not isinstance(s, str):
        return s
    try:
        return ast.literal_eval(s)
    except Exception:
        return s


def _as_text(v):
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)


def _trim(v, head, tail):
    s = _as_text(v)
    if head is None or len(s) <= head + tail:
        return s, False
    return s[:head] + f"\n…[trimmed {len(s) - head - tail} chars]…\n" + s[-tail:], True


def backward_slice(pred_full_id, edges_by_target):
    """Return the set of op_ids (and node ids) that are ancestors of the prediction node."""
    seen, ops = set(), set()
    stack = [pred_full_id]
    while stack:
        nid = stack.pop()
        if nid in seen:
            continue
        seen.add(nid)
        for op_id, src in edges_by_target.get(nid, ()):
            ops.add(op_id)
            if src not in seen:
                stack.append(src)
    return ops, seen


def _render_step(op, ins, outs, node_by_id, head, tail):
    lines = [f"Operation: {op.get('op_name')} [{op.get('category')}] (op_id {op.get('op_id')}, session {op.get('session_id')}, {op.get('created_at')})"]
    md = op.get("metadata") or {}
    if md:
        lines.append("Parameters: " + json.dumps(md, ensure_ascii=False, default=str))
    if op.get("comment"):
        lines.append("Description: " + str(op["comment"]).strip())
    trimmed = False
    for label, ids in (("Inputs", ins), ("Outputs", outs)):
        lines.append(f"{label}:" if ids else f"{label}: (none)")
        for nid in ids:
            n = node_by_id.get(nid)
            if n is None:
                lines.append(f"  - {nid}: <node missing>")
                continue
            val, t = _trim(n.get("value", ""), head, tail)
            trimmed = trimmed or t
            lines.append(f"  - [{n.get('category')}] {nid}: {val}")
    return "\n".join(lines), trimmed


def _file_trajectories(path, split, subset, head, tail):
    with open(path, encoding="utf-8") as fh:
        g = json.load(fh)
    D = g["data"]
    md = g.get("metadata") or {}
    ops = D["operations"]
    ops_sorted = sorted(range(len(ops)), key=lambda i: (ops[i].get("created_at") or "", i))
    op_order = {ops[i]["op_id"]: k for k, i in enumerate(ops_sorted)}
    op_by_id = {o["op_id"]: o for o in ops}
    node_by_id = {n["full_node_id"]: n for n in D["nodes"]}
    edges_by_target = collections.defaultdict(list)
    edges_by_op = collections.defaultdict(list)
    for e in D["edges"]:
        edges_by_target[e["target_full_node_id"]].append((e["op_id"], e["source_full_node_id"]))
        edges_by_op[e["op_id"]].append((e["source_full_node_id"], e["target_full_node_id"]))
    graph_size = {"nodes": len(D["nodes"]), "edges": len(D["edges"]), "operations": len(ops), "sessions": len(D.get("sessions", []))}
    fname = os.path.basename(path)
    source = md.get("memtracebench_dataset_source") or fname.split("_")[0]
    seen_ids = collections.Counter()
    for a in D.get("annotations", []):
        et = a.get("final_error_type")
        tsubset = split if et in MEMORY_ERRORS else "excluded"
        if subset is not None and tsubset != subset:
            continue
        slice_ops, slice_nodes = backward_slice(a.get("prediction_id"), edges_by_target)
        ordered = sorted(slice_ops, key=lambda x: op_order.get(x, -1))
        steps, any_trim, faulty = [], False, None
        for k, oid in enumerate(ordered):
            op = op_by_id[oid]
            ins, outs, si, so = [], [], set(), set()
            for s, t in edges_by_op[oid]:
                if s not in si:
                    si.add(s); ins.append(s)
                if t not in so:
                    so.add(t); outs.append(t)
            content, trimmed = _render_step(op, ins, outs, node_by_id, head, tail)
            any_trim = any_trim or trimmed
            opmd = op.get("metadata") or {}
            if oid == a.get("final_op_id"):
                faulty = k
            steps.append({"idx": k, "native_idx": oid, "agent": str(op.get("op_name") or "").strip(), "role": _role(op),
                          "content": content,
                          "meta": {"op_name": op.get("op_name"), "category": op.get("category"), "session_id": op.get("session_id"),
                                   "created_at": op.get("created_at"), "global_op_index": op_order.get(oid),
                                   "llm_model": opmd.get("llm_model") if isinstance(opmd, dict) else None,
                                   "n_inputs": len(ins), "n_outputs": len(outs), "trimmed": trimmed}})
        fo = a.get("final_op_id")
        fop = op_by_id.get(fo) if fo else None
        qid = a.get("query_id")
        tid = f"{split}/{fname}::{qid}"
        seen_ids[tid] += 1
        if seen_ids[tid] > 1:
            tid += f"#{seen_ids[tid]}"
        q = _lit(a.get("query"))
        pred = _lit(a.get("prediction"))
        yield {
            "dataset": SLUG,
            "id": tid,
            "subset": tsubset,
            "system": SYSTEM_NAMES.get(split, split),
            "task": q if isinstance(q, str) else _as_text(q),
            "ground_truth": a.get("golden_answers"),
            "final_output": pred if isinstance(pred, str) else _as_text(pred) if pred is not None else None,
            "outcome": 0 if tsubset != "excluded" else None,
            "steps": steps,
            "annotation": {"faulty_step": faulty, "faulty_steps": [faulty] if faulty is not None else [],
                           "faulty_agent": (fop or {}).get("op_name") if fop else None,
                           "category": et, "reason": a.get("reason"),
                           "extra": {"query_id": qid, "prediction_id": a.get("prediction_id"), "golden_answers_id": a.get("golden_answers_id"),
                                     "golden_answers_parsed": _lit(a.get("golden_answers")),
                                     "source_evidence": a.get("source_evidence"), "source_evidence_ids": a.get("source_evidence_ids"),
                                     "final_op_id": fo, "final_op_name": (fop or {}).get("op_name"), "final_op_category": (fop or {}).get("category"),
                                     "final_op_global_index": op_order.get(fo) if fo else None,
                                     "op_outside_slice": bool(fo) and faulty is None,
                                     "slice_ops": len(ordered), "slice_nodes": len(slice_nodes)}},
            "meta": {"dataset_source": source, "conversation_id": g.get("user_id"), "memory_system": split,
                     "memory_system_name": SYSTEM_NAMES.get(split, split), "graph_id": g.get("graph_id"), "project_id": g.get("project_id"),
                     "file": path, "slice_length": len(ordered), "graph_size": graph_size,
                     "n_annotations_in_file": len(D.get("annotations", [])), "trimmed": any_trim,
                     "value_head": head, "value_tail": tail,
                     "backbone": "GPT-4.1-mini (memory construction + answering); Claude Opus 4.5 judge", "licence": "MIT"},
        }
    del g, D, ops, op_by_id, node_by_id, edges_by_target, edges_by_op
    gc.collect()


def files(subset=None):
    out = []
    for sp in SPLITS:
        if subset is not None and subset != "excluded" and subset != sp:
            continue
        out += [(sp, f) for f in sorted(glob.glob(os.path.join(ROOT, sp, "*.json")))]
    return out


def load(limit=None, subset=None, head=4000, tail=500):
    n = 0
    for sp, f in files(subset):
        for t in _file_trajectories(f, sp, subset, head, tail):
            yield t
            n += 1
            if limit is not None and n >= limit:
                return
