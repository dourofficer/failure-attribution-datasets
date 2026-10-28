"""Shared helpers for the who_and_when / traceelephant / mp_bench / who_and_when_pro analysis
scripts (stdlib only; run with python3 -I from scripts/). Named fa4_* to avoid clashing with
other agents' helper modules in this directory."""
import json
import math
import os
import statistics
from collections import Counter

NOTES_DIR = "/dataDisk/home/thanhdo/failure-attribution-datasets/notes"


def describe(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return {"n": 0}
    xs_sorted = sorted(xs)
    return {
        "n": len(xs),
        "mean": round(statistics.mean(xs), 2),
        "median": statistics.median(xs),
        "min": xs_sorted[0],
        "max": xs_sorted[-1],
        "p10": xs_sorted[int(0.10 * (len(xs) - 1))],
        "p90": xs_sorted[int(0.90 * (len(xs) - 1))],
    }


def hist(xs, edges):
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        c = sum(1 for x in xs if lo <= x < hi)
        label = f"{lo}-{hi - 1}" if hi != math.inf and hi < 10**6 else f">={lo}"
        out.append((label, c))
    return out


def hist_str(xs, edges):
    return ", ".join(f"{l}: {c}" for l, c in hist(xs, edges))


def fmt_desc(d, unit=""):
    if d.get("n", 0) == 0:
        return "n/a"
    return f"mean {d['mean']}{unit}, median {d['median']}{unit}, min {d['min']}{unit}, max {d['max']}{unit}"


def counter_table(c, title_key="value", title_val="count", top=None, total=None):
    rows = c.most_common(top)
    total = total or sum(c.values())
    lines = [f"| {title_key} | {title_val} | % |", "|---|---|---|"]
    for k, v in rows:
        lines.append(f"| {k} | {v} | {100 * v / total:.1f} |")
    return "\n".join(lines)


def trim_text(s, head=3000, tail=500, limit=4000):
    if s is None:
        return None, False
    if len(s) <= limit:
        return s, False
    return s[:head] + " […] " + s[-tail:], True


def truncate_for_md(s, limit=500):
    if s is None:
        return ""
    s = str(s)
    if len(s) <= limit:
        return s
    return s[:limit] + " […]"


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=str)


def write_norm_example(slug, source_id, task, ground_truth, final_output, steps, annotation):
    out_steps = []
    for s in steps:
        content, trimmed = trim_text(s["content"])
        d = {"idx": s["idx"], "agent": s["agent"], "content": content}
        if trimmed:
            d["trimmed"] = True
        for k, v in s.items():
            if k not in ("idx", "agent", "content"):
                d[k] = v
        out_steps.append(d)
    obj = {"dataset": slug, "source_id": source_id, "task": task, "ground_truth": ground_truth,
           "final_output": final_output, "steps": out_steps, "annotation": annotation}
    path = os.path.join(NOTES_DIR, f"{slug}_example_norm.json")
    write_json(path, obj)
    return path, os.path.getsize(path)


def md_steps(steps, faulty_idx, limit=500):
    fset = set(faulty_idx) if isinstance(faulty_idx, (list, set, tuple)) else {faulty_idx}
    lines = []
    for s in steps:
        mark = "  **⟵ ANNOTATED ERROR STEP**" if s["idx"] in fset else ""
        content = truncate_for_md(s["content"], limit).replace("\n", "\n> ")
        lines.append(f"**Step {s['idx']} — {s['agent']}**{mark}\n\n> {content}\n")
    return "\n".join(lines)
