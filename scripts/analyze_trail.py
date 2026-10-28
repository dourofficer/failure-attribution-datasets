"""Analyse TRAIL (GitHub mirror of PatronusAI/TRAIL). Usage:
python3 -I analyze_trail.py <benchmarking_dir> <notes_dir> <scratch_dir>
"""
import sys, os, json, re, collections, statistics
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import *

bench, notes_dir, scratch = sys.argv[1:4]

CANON = ["Language-only", "Tool-related", "Poor Information Retrieval", "Incorrect Memory Usage",
         "Tool Output Misinterpretation", "Incorrect Problem Identification", "Tool Selection Errors",
         "Formatting Errors", "Instruction Non-compliance", "Tool Definition Issues",
         "Environment Setup Errors", "Rate Limiting", "Authentication Errors", "Service Errors",
         "Resource Not Found", "Resource Exhaustion", "Timeout Issues", "Context Handling Failures",
         "Resource Abuse", "Goal Deviation", "Task Orchestration"]
GROUP = {"Language-only": "Reasoning/Hallucination", "Tool-related": "Reasoning/Hallucination",
         "Poor Information Retrieval": "Reasoning/Information processing", "Incorrect Memory Usage": "Reasoning/Information processing",
         "Tool Output Misinterpretation": "Reasoning/Information processing",
         "Incorrect Problem Identification": "Reasoning/Decision making", "Tool Selection Errors": "Reasoning/Decision making",
         "Formatting Errors": "Reasoning/Output generation", "Instruction Non-compliance": "Reasoning/Output generation",
         "Tool Definition Issues": "System/Configuration", "Environment Setup Errors": "System/Configuration",
         "Rate Limiting": "System/API", "Authentication Errors": "System/API", "Service Errors": "System/API", "Resource Not Found": "System/API",
         "Resource Exhaustion": "System/Resource management", "Timeout Issues": "System/Resource management",
         "Context Handling Failures": "Planning/Context management", "Resource Abuse": "Planning/Context management",
         "Goal Deviation": "Planning/Task management", "Task Orchestration": "Planning/Task management"}


def canon(cat):
    c = (cat or "").lower().strip().replace("-", " ")
    c = re.sub(r"\s+", " ", c)
    c = re.sub(r"\s*errors?$", "", c) if c not in ("formatting errors", "tool selection errors", "service errors", "environment setup errors", "authentication errors") else c
    for s in CANON:
        sl = s.lower().replace("-", " ")
        if c == sl or c == re.sub(r"\s*errors?$", "", sl) or c.replace(" ", "") == sl.replace(" ", ""):
            return s
    for s in CANON:
        sl = s.lower().replace("-", " ")
        if c.replace(" ", "") in sl.replace(" ", "") or sl.replace(" ", "") in c.replace(" ", ""):
            return s
    if "complien" in c or "compli" in c:
        return "Instruction Non-compliance"
    return cat


def lj(path):
    s = open(path, encoding="utf-8").read()
    try:
        return json.loads(s), False
    except json.JSONDecodeError:
        return json.loads(re.sub(r",(\s*[}\]])", r"\1", s)), True


def flatten(span, depth, agent, out):
    at = span.get("span_attributes", {}) or {}
    kind = at.get("openinference.span.kind")
    if kind == "AGENT":
        agent = span["span_name"].replace(".run", "")
        # managed agent name if present
    out.append({"depth": depth, "agent": agent, "span": span})
    for c in span.get("child_spans", []) or []:
        flatten(c, depth + 1, agent, out)


def span_content(span):
    """Human-readable content of a span for the normalised example."""
    at = span.get("span_attributes", {}) or {}
    kind = at.get("openinference.span.kind")
    parts = []
    if kind == "LLM":
        # last input message + output
        idx = sorted({int(m.group(1)) for k in at for m in [re.match(r"llm\.input_messages\.(\d+)\.message\.content", k)] if m})
        if idx:
            i = idx[-1]
            parts.append(f"Input (last of {len(idx)} msgs, role={at.get(f'llm.input_messages.{i}.message.role')}): {at.get(f'llm.input_messages.{i}.message.content')}")
        out = at.get("llm.output_messages.0.message.content") or at.get("output.value")
        parts.append(f"Output ({at.get('llm.model_name')}): {out}")
    elif kind == "TOOL":
        parts.append(f"Tool: {at.get('tool.name')} | Input: {at.get('input.value')}")
        if at.get("output.value") is not None:
            parts.append(f"Observation: {at.get('output.value')}")
    else:
        if at.get("input.value") is not None:
            parts.append(f"Input: {at.get('input.value')}")
        if at.get("output.value") is not None:
            parts.append(f"Output: {at.get('output.value')}")
        if not parts:
            logs = span.get("logs") or []
            if logs:
                body = logs[0].get("body", {})
                parts.append("Function call: " + json.dumps({k: body.get(k) for k in ("function.name", "function.arguments")}, default=str))
            else:
                parts.append("(no content)")
    return "\n".join(str(p) for p in parts)


SPLITS = [("gaia", "data/GAIA", "processed_annotations_gaia"), ("swe_bench", "data/SWE Bench", "processed_annotations_swe_bench")]
traces = []
fixed_files = []
for split, sub, ann in SPLITS:
    for fn in sorted(os.listdir(os.path.join(bench, sub))):
        t, f1 = lj(os.path.join(bench, sub, fn))
        a, f2 = lj(os.path.join(bench, ann, fn))
        if f1 or f2:
            fixed_files.append(fn)
        fl = []
        for root in t["spans"]:
            flatten(root, 0, None, fl)
        ids = [x["span"]["span_id"] for x in fl]
        raw_chars = os.path.getsize(os.path.join(bench, sub, fn))
        content_chars = sum(len(str(v)) for x in fl for k, v in (x["span"].get("span_attributes") or {}).items()
                            if k.startswith(("input.value", "output.value", "llm.", "tool.")))
        errs = []
        for e in a.get("errors", []):
            loc = e.get("location")
            idx = ids.index(loc) if loc in ids else None
            errs.append({"category_raw": e.get("category"), "category": canon(e.get("category")), "location": loc, "idx": idx,
                         "impact": (e.get("impact") or "").upper(), "evidence": e.get("evidence"), "description": e.get("description"),
                         "kind": (fl[idx]["span"].get("span_attributes") or {}).get("openinference.span.kind") if idx is not None else None,
                         "agent": fl[idx]["agent"] if idx is not None else None})
        scores = (a.get("scores") or [{}])[0]
        agents = sorted({x["agent"] for x in fl if x["agent"]})
        kinds = collections.Counter((x["span"].get("span_attributes") or {}).get("openinference.span.kind") for x in fl)
        traces.append({"split": split, "file": fn, "trace_id": t.get("trace_id"), "n_spans": len(fl), "spans": fl, "errors": errs,
                       "scores": scores, "agents": agents, "raw_chars": raw_chars, "content_chars": content_chars, "kinds": kinds,
                       "task": None})

# ---- stats
n = len(traces)
steps = [t["n_spans"] for t in traces]
agents = [len(t["agents"]) for t in traces]
rel = [e["idx"] / (t["n_spans"] - 1) for t in traces for e in t["errors"] if e["idx"] is not None and t["n_spans"] > 1]
cat = collections.Counter(e["category"] for t in traces for e in t["errors"])
cat_split = {s: collections.Counter(e["category"] for t in traces if t["split"] == s for e in t["errors"]) for s, _, _ in SPLITS}
grp = collections.Counter(GROUP.get(e["category"], "UNMAPPED:" + str(e["category"])) for t in traces for e in t["errors"])
top = collections.Counter(GROUP.get(e["category"], "UNMAPPED").split("/")[0] for t in traces for e in t["errors"])
imp = collections.Counter(e["impact"] for t in traces for e in t["errors"])
imp_by_group = collections.defaultdict(collections.Counter)
for t in traces:
    for e in t["errors"]:
        imp_by_group[GROUP.get(e["category"], "UNMAPPED").split("/")[0]][e["impact"]] += 1
err_kind = collections.Counter(e["kind"] for t in traces for e in t["errors"])
err_agent = collections.Counter(str(e["agent"]) for t in traces for e in t["errors"])
errs_per = [len(t["errors"]) for t in traces]
unmatched = sum(1 for t in traces for e in t["errors"] if e["idx"] is None)
raw_cats = collections.Counter(e["category_raw"] for t in traces for e in t["errors"])
unmapped = {k: v for k, v in cat.items() if k not in CANON}
spans_with_err = sum(len({e["idx"] for e in t["errors"] if e["idx"] is not None}) for t in traces)
overall = [t["scores"].get("overall") for t in traces if isinstance(t["scores"].get("overall"), (int, float))]
kinds_total = collections.Counter()
for t in traces:
    kinds_total.update(t["kinds"])
per_split = {}
for s, _, _ in SPLITS:
    ts = [t for t in traces if t["split"] == s]
    per_split[s] = {"n_traces": len(ts), "spans_total": sum(t["n_spans"] for t in ts),
                    "spans_desc": describe([t["n_spans"] for t in ts]), "errors_total": sum(len(t["errors"]) for t in ts),
                    "errors_per_trace_desc": describe([len(t["errors"]) for t in ts]),
                    "traces_with_zero_errors": sum(1 for t in ts if not t["errors"]),
                    "agents_desc": describe([len(t["agents"]) for t in ts]),
                    "agent_names": dict(collections.Counter(a for t in ts for a in t["agents"])),
                    "raw_json_chars_desc": describe([t["raw_chars"] for t in ts]),
                    "content_chars_desc": describe([t["content_chars"] for t in ts]),
                    "impact": dict(collections.Counter(e["impact"] for t in ts for e in t["errors"])),
                    "overall_score_mean": round(statistics.mean([t["scores"].get("overall") for t in ts if isinstance(t["scores"].get("overall"), (int, float))]), 2),
                    "category_counts": dict(cat_split[s].most_common())}
stats = {
    "n_trajectories": n,
    "steps_per_traj": steps,
    "steps_note": "steps = OpenTelemetry spans flattened in DFS (document) order = chronological order; includes framework spans (main, Step N, agent run, LLM call, tool call)",
    "error_step_rel_pos": [round(x, 4) for x in rel],
    "agents_per_traj": agents,
    "faulty_agent_counts": dict(err_agent.most_common()),
    "category_counts": dict(cat.most_common()),
    "category_group_counts": dict(grp.most_common()),
    "top_level_category_counts": dict(top.most_common()),
    "impact_counts": dict(imp.most_common()),
    "impact_by_top_level": {k: dict(v) for k, v in imp_by_group.items()},
    "error_span_kind_counts": dict(err_kind.most_common()),
    "source_benchmark_counts": {"GAIA": per_split["gaia"]["n_traces"], "SWE-Bench Lite": per_split["swe_bench"]["n_traces"]},
    "framework_counts": {"smolagents OpenDeepResearch (CodeAgent manager + ToolCallingAgent search_agent), o3-mini": per_split["gaia"]["n_traces"],
                         "smolagents CodeAgent (single agent, gitingest + python), claude-3-7-sonnet": per_split["swe_bench"]["n_traces"]},
    "splits": {"gaia": per_split["gaia"]["n_traces"], "swe_bench": per_split["swe_bench"]["n_traces"]},
    "errors_total": sum(errs_per),
    "errors_per_trace_desc": describe(errs_per),
    "errors_per_trace_hist": histogram(errs_per, [(0, 0), (1, 2), (3, 5), (6, 10), (11, 20)]),
    "traces_with_zero_errors": sum(1 for e in errs_per if e == 0),
    "distinct_spans_with_errors": spans_with_err,
    "error_locations_not_matching_any_span": unmatched,
    "steps_desc": describe(steps),
    "steps_hist": histogram(steps, [(11, 15), (16, 25), (26, 40), (41, 60), (61, 100), (101, 200)]),
    "rel_pos_desc": describe(rel),
    "rel_pos_hist": histogram(rel, [(0.0, 0.2), (0.2001, 0.4), (0.4001, 0.6), (0.6001, 0.8), (0.8001, 1.0)]),
    "agents_desc": describe(agents),
    "span_kind_counts": dict(kinds_total),
    "raw_json_chars_desc": describe([t["raw_chars"] for t in traces]),
    "content_chars_desc": describe([t["content_chars"] for t in traces]),
    "overall_score_desc": describe(overall),
    "raw_category_spellings": len(raw_cats),
    "unmapped_categories": unmapped,
    "files_needing_trailing_comma_fix": fixed_files,
    "per_split": per_split,
    "has_success_label": False,
}
dump(stats, os.path.join(notes_dir, "trail_stats.json"))

# ---- example: shortest GAIA trace with >=2 errors
cands = sorted([t for t in traces if t["split"] == "gaia" and len(t["errors"]) >= 2], key=lambda t: (t["n_spans"], t["content_chars"]))
ex = cands[0]
print("example", ex["file"], ex["n_spans"], len(ex["errors"]), ex["content_chars"])
raw_trace, _ = lj(os.path.join(bench, "data/GAIA", ex["file"]))
raw_ann, _ = lj(os.path.join(bench, "processed_annotations_gaia", ex["file"]))
dump({"trace": raw_trace, "labels": raw_ann}, os.path.join(notes_dir, "trail_example.json"))

# task statement: from answer_single_question function args if present
task = None
gt = None
for x in ex["spans"]:
    for lg in x["span"].get("logs") or []:
        args = (lg.get("body") or {}).get("function.arguments") or {}
        exm = args.get("example") if isinstance(args, dict) else None
        if isinstance(exm, dict) and exm.get("question"):
            task = exm.get("question")
            gt = exm.get("true_answer") or exm.get("Final answer") or exm.get("answer")
final = None
for x in reversed(ex["spans"]):
    at = x["span"].get("span_attributes") or {}
    if x["span"]["span_name"] == "FinalAnswerTool":
        final = at.get("input.value")
        break
nsteps = []
for i, x in enumerate(ex["spans"]):
    txt, tr = trim_long(span_content(x["span"]))
    at = x["span"].get("span_attributes") or {}
    st = {"idx": i, "agent": f"{x['agent'] or 'framework'} / {x['span']['span_name']} [{at.get('openinference.span.kind') or 'INTERNAL'}]",
          "span_id": x["span"]["span_id"], "depth": x["depth"], "content": txt}
    if tr:
        st["trimmed"] = True
    nsteps.append(st)
errs_norm = [{"location_idx": e["idx"], "span_id": e["location"], "category": e["category"], "group": GROUP.get(e["category"]),
              "impact": e["impact"], "evidence": e["evidence"], "description": e["description"]} for e in ex["errors"]]
norm = {
    "dataset": "trail",
    "source_id": ex["trace_id"],
    "task": task,
    "ground_truth": gt,
    "final_output": final,
    "steps": nsteps,
    "annotation": {
        "faulty_agent": None,
        "faulty_step": sorted({e["idx"] for e in ex["errors"] if e["idx"] is not None}),
        "category": [f"idx {e['idx']} ({e['location']}): {e['category']} [{e['impact']}]" for e in ex["errors"]],
        "reason": " || ".join(f"[{e['category']}] {e['description']}" for e in ex["errors"]),
        "extra": {"errors": errs_norm, "scores": ex["scores"], "split": "gaia",
                  "step_indexing": "0-based index over spans flattened in DFS order (idx) — the dataset itself addresses errors by span_id, not by index"},
    },
}
dump(norm, os.path.join(notes_dir, "trail_example_norm.json"))
with open(os.path.join(scratch, "trail_example.md"), "w") as f:
    f.write(render_example_md(norm))
print(json.dumps({k: v for k, v in stats.items() if not isinstance(v, list)}, indent=1, default=str))
