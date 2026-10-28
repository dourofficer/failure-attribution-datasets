"""Render a <slug>_example_norm.json as a Markdown 'Example trajectory' section.
Usage: python3 -I render_example.py <norm.json> <out.md> [max_chars=500]"""
import json, sys

src, out = sys.argv[1], sys.argv[2]
lim = int(sys.argv[3]) if len(sys.argv) > 3 else 500
with open(src, encoding="utf-8") as fh:
    n = json.load(fh)

def tr(s, lim=lim):
    s = str(s).replace("\r", "")
    if len(s) <= lim:
        return s
    head = s[: int(lim * 0.8)]
    tail = s[-int(lim * 0.2):]
    return head + " […] " + tail

ann = n["annotation"]
fs = ann.get("faulty_step")
fs_set = set(fs) if isinstance(fs, list) else ({fs} if fs is not None else set())
lines = []
lines.append(f"**Source id:** `{n.get('source_id')}`  ")
lines.append(f"**Task:** {tr(n.get('task') or '', 1200)}  ")
if n.get("ground_truth") is not None:
    lines.append(f"**Ground truth:** {tr(n.get('ground_truth'), 400)}  ")
if n.get("final_output") is not None:
    lines.append(f"**Final output of the system:** {tr(n.get('final_output'), 600)}  ")
lines.append("")
lines.append(f"Steps ({len(n['steps'])} total):")
lines.append("")
for s in n["steps"]:
    mark = "  ⟵ ANNOTATED ERROR STEP" if s["idx"] in fs_set else ""
    body = tr(s["content"]).strip()
    lines.append(f"- **Step {s['idx']} — {s.get('agent')}**{mark}")
    lines.append("")
    lines.append("  > " + body.replace("\n", "\n  > "))
    lines.append("")
lines.append("**Annotation:**")
lines.append("")
lines.append(f"- Faulty agent/component: `{ann.get('faulty_agent')}`")
lines.append(f"- Faulty step: `{ann.get('faulty_step')}`")
lines.append(f"- Category: `{ann.get('category')}`")
lines.append(f"- Reason / root cause: {tr(ann.get('reason') or '', 1500)}")
for k, v in (ann.get("extra") or {}).items():
    if k in ("reference_explanation",):
        continue
    lines.append(f"- {k}: {tr(v, 300)}")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("wrote", out, len("\n".join(lines)), "chars")
