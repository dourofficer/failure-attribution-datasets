"""Write agenthallu_example.json and agenthallu_example_norm.json. Usage: python3 -I example_agenthallu.py <record.json> <notes_dir>"""
import json, sys, os

src, notes = sys.argv[1], sys.argv[2]
with open(src, encoding="utf-8") as fh:
    d = json.load(fh)
with open(os.path.join(notes, "agenthallu_example.json"), "w", encoding="utf-8") as fh:
    json.dump(d, fh, indent=1, ensure_ascii=False)

def trim(s, lim=4000):
    if len(s) > lim:
        return s[:3000] + " […] " + s[-500:], True
    return s, False

steps = []
for s in d["history"]:
    parts = []
    if s.get("content") not in (None, "", "None"):
        parts.append(str(s["content"]))
    if s.get("tool_calls"):
        for tc in s["tool_calls"]:
            parts.append("Action: " + json.dumps(tc, ensure_ascii=False))
    if s.get("tool_responses"):
        for tr in s["tool_responses"]:
            parts.append("Observation: " + (tr if isinstance(tr, str) else json.dumps(tr, ensure_ascii=False)))
    content, trimmed = trim("\n".join(parts))
    st = {"idx": s.get("step"), "agent": s.get("role") or d.get("agent_type"), "content": content}
    if trimmed:
        st["trimmed"] = True
    steps.append(st)

fs = int(d["hallucination_step"])
faulty_agent = next((s.get("role") for s in d["history"] if s.get("step") == fs), None) or d.get("agent_type")
norm = {
    "dataset": "agenthallu",
    "source_id": os.path.join(*src.split(os.sep)[-2:]),
    "task": d["question"],
    "ground_truth": d.get("true_answer"),
    "final_output": d.get("agent_answer"),
    "steps": steps,
    "annotation": {
        "faulty_agent": faulty_agent,
        "faulty_step": fs,
        "category": f'{d.get("hallucination_category")} / {d.get("hallucination_subcategory")}',
        "reason": d.get("hallucination_reason"),
        "extra": {
            "is_hallucination": d.get("is_hallucination"),
            "hallucination_category": d.get("hallucination_category"),
            "hallucination_subcategory": d.get("hallucination_subcategory"),
            "model_id": d.get("model_id"),
            "agent_type": d.get("agent_type"),
            "question_source": d.get("question_source"),
            "question_domain": d.get("question_domain"),
            "reference_explanation": d.get("explanation"),
        },
    },
}
with open(os.path.join(notes, "agenthallu_example_norm.json"), "w", encoding="utf-8") as fh:
    json.dump(norm, fh, indent=1, ensure_ascii=False)
print("steps", len(steps), "size", os.path.getsize(os.path.join(notes, "agenthallu_example_norm.json")))
