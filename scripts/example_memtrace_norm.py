"""Build memtrace_example_norm.json from memtrace_example.json. Usage: python3 -I example_memtrace_norm.py <notes_dir>"""
import json, os, sys

notes = sys.argv[1]
with open(os.path.join(notes, "memtrace_example.json"), encoding="utf-8") as fh:
    e = json.load(fh)
a = e["annotation"]

def val(v, lim=700):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = s.replace("\n", " ")
    return s if len(s) <= lim else s[:lim] + " […]"

steps = []
faulty_idx = None
for i, s in enumerate(e["prediction_backward_slice_steps"], 1):
    lines = [f"Operation: {s['op_name']} [{s['category']}] (op_id {s['op_id']}, session {s['session_id']}, {s['created_at']})"]
    if s.get("comment"):
        lines.append("Description: " + s["comment"].strip())
    seen = set()
    ins = []
    for x in s["inputs"]:
        if x["id"] in seen:
            continue
        seen.add(x["id"])
        if x["category"] == "prompt":
            ins.append(f"  - [{x['category']}] {x['name']} (prompt template, {len(str(x['value']))} chars, omitted)")
        else:
            ins.append(f"  - [{x['category']}] {x['name']}: {val(x['value'])}")
    lines.append("Inputs:\n" + "\n".join(ins))
    outs = []
    seen_out = set()
    for x in s["outputs"]:
        if x["id"] in seen_out or x["id"] in seen and x["category"] in ("prompt",):
            continue
        seen_out.add(x["id"])
        if x["category"] == "prompt":
            outs.append(f"  - [{x['category']}] {x['name']} (prompt, {len(str(x['value']))} chars, omitted)")
        else:
            outs.append(f"  - [{x['category']}] {x['name']}: {val(x['value'])}")
    lines.append("Outputs:\n" + "\n".join(outs))
    content = "\n".join(lines)
    st = dict(idx=i, agent=f"{s['category']} operation ({s['op_name']})", content=content, op_id=s["op_id"])
    if s["op_id"] == a["final_op_id"]:
        faulty_idx = i
    steps.append(st)

norm = dict(
    dataset="memtrace", source_id=f"{e['graph_file']}::{a['query_id']}",
    task=a["query"], ground_truth=a["golden_answers"], final_output=a["prediction"], steps=steps,
    annotation=dict(faulty_agent=next(s["agent"] for s in steps if s["idx"] == faulty_idx) if faulty_idx else None,
                    faulty_step=faulty_idx, category=a["final_error_type"], reason=a["reason"],
                    extra=dict(final_op_id=a["final_op_id"], query_id=a["query_id"], prediction_id=a["prediction_id"], source_evidence=a["source_evidence"],
                               source_evidence_ids=a["source_evidence_ids"], memory_system=e["metadata"].get("memtracebench_system"),
                               source_dataset=e["metadata"].get("memtracebench_dataset_source"), graph_size=e["graph_size"],
                               note="Steps are the operations in the backward (dependency) slice of the prediction node, in chronological order; the full execution graph has many more operations (see graph_size) that do not feed into this prediction.")),
)
out = os.path.join(notes, "memtrace_example_norm.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(norm, fh, indent=1, ensure_ascii=False)
print("faulty idx", faulty_idx, "steps", len(steps), "bytes", os.path.getsize(out))
