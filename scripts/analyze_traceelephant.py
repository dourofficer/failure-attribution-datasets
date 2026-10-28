#!/usr/bin/env python3
"""Statistics + example for TraceElephant (HF TraceElephant/TraceElephant, data.zip extracted).
Usage: python3 -I analyze_traceelephant.py <extracted_data_dir>   (dir containing magentic-runs-gaia/ etc.)
"""
import glob
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fa4_common import (NOTES_DIR, counter_table, describe, fmt_desc, hist_str, md_steps,  # noqa: E402
                        write_json, write_norm_example)

SLUG = "traceelephant"
SYSTEM_OF_DIR = {"magentic-runs-gaia": ("magentic-one", "GAIA"), "magentic-runs-assistant-bench": ("magentic-one", "AssistantBench"),
                 "captain-runs-gaia": ("captain-agent", "GAIA"), "captain-runs-assistantbench": ("captain-agent", "AssistantBench"),
                 "swe-agent-runs-swe-bench": ("swe-agent", "SWE-Bench Verified")}


def msg_text(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict):
                if p.get("type") == "text":
                    parts.append(p.get("text", ""))
                elif p.get("type") == "image_url":
                    parts.append("[image]")
                else:
                    parts.append(json.dumps(p)[:200])
            else:
                parts.append(str(p))
        return "\n".join(parts)
    return json.dumps(content)


def step_output(st):
    """Assistant output text (+ tool calls) of one step record."""
    try:
        msg = st["output"]["choices"][0]["message"]
    except Exception:  # noqa
        return "", []
    text = msg_text(msg.get("content"))
    calls = msg.get("tool_calls") or []
    return text, calls


def step_observation(st, next_st):
    """Tool results that come back are only visible as the last 'tool' message(s) in the NEXT step's input."""
    if next_st is None:
        return ""
    msgs = next_st["input"]["messages"]
    obs = []
    for m in reversed(msgs):
        if m.get("role") == "tool":
            obs.append(msg_text(m.get("content")))
        else:
            break
    return "\n".join(reversed(obs))


def parse_step(v):
    """'9' -> 9, 'Step 36' -> 36, 'none' -> None"""
    s = str(v).strip()
    digits = "".join(ch for ch in s if ch.isdigit())
    return int(digits) if digits else None


def main():
    root = sys.argv[1]
    recs = []
    for d in sorted(glob.glob(os.path.join(root, "*", "*"))):
        if not os.path.isdir(d):
            continue
        with open(os.path.join(d, "trace_metadata.json"), encoding="utf-8") as f:
            meta = json.load(f)
        with open(os.path.join(d, "step_records.json"), encoding="utf-8") as f:
            steps = json.load(f)
        n_img = len(glob.glob(os.path.join(d, "images", "*.png")))
        recs.append((os.path.relpath(d, root), meta, steps, n_img))

    stats = {"n_trajectories": len(recs), "steps_per_traj": [], "error_step_rel_pos": [], "agents_per_traj": [],
             "faulty_agent_counts": {}, "category_counts": {}, "source_benchmark_counts": {}, "splits": {}, "per_system": {}}
    faulty = Counter(); bench = Counter(); splits = Counter(); sysc = Counter(); faulty_by_sys = {}
    chars = []; toks = []; imgs = []; ms_abs = []; per = {}
    examples = []
    no_step = []
    for rel, meta, steps, n_img in recs:
        sysn, bname = SYSTEM_OF_DIR[rel.split("/")[0]]
        n = len(steps)
        ms = parse_step(meta["mistake_step"])
        ids = [s["step_id"] for s in steps]
        if ids != list(range(1, n + 1)):
            print(f"WARNING non-contiguous step ids in {rel}: {ids[:5]}...", file=sys.stderr)
        if ms is None:
            no_step.append(rel)
        elif not (1 <= ms <= n):
            print(f"WARNING mistake_step {ms} outside 1..{n} in {rel}", file=sys.stderr)
        agents = {s["agent_name"] for s in steps}
        tot_chars = sum(len(step_output(s)[0]) + sum(len(json.dumps(c)) for c in step_output(s)[1]) for s in steps)
        tot_tokens = sum((s.get("output", {}).get("usage") or {}).get("total_tokens", 0) or 0 for s in steps)
        stats["steps_per_traj"].append(n); stats["agents_per_traj"].append(len(agents))
        if ms is not None:
            stats["error_step_rel_pos"].append(round(ms / n, 4))
        faulty[meta["mistake_agent"]] += 1; bench[bname] += 1; splits[rel.split("/")[0]] += 1; sysc[sysn] += 1
        faulty_by_sys.setdefault(sysn, Counter())[meta["mistake_agent"]] += 1
        chars.append(tot_chars); toks.append(tot_tokens); imgs.append(n_img)
        if ms is not None:
            ms_abs.append(ms)
        p = per.setdefault(sysn, {"steps": [], "rel": [], "agents": [], "chars": [], "toks": [], "imgs": [], "ms": [], "bench": Counter()})
        p["steps"].append(n); p["agents"].append(len(agents)); p["chars"].append(tot_chars); p["toks"].append(tot_tokens)
        p["imgs"].append(n_img); p["bench"][bname] += 1
        if ms is not None:
            p["rel"].append(ms / n); p["ms"].append(ms)
        examples.append((rel, meta, steps, n, ms, tot_chars, sysn, bname, len(agents)))

    stats["faulty_agent_counts"] = dict(faulty.most_common()); stats["source_benchmark_counts"] = dict(bench); stats["splits"] = dict(splits)
    stats["system_counts"] = dict(sysc); stats["traces_without_numeric_mistake_step"] = no_step; stats["chars_per_traj"] = chars; stats["llm_tokens_per_traj"] = toks; stats["images_per_traj"] = imgs
    stats["faulty_agent_counts_by_system"] = {k: dict(v.most_common()) for k, v in faulty_by_sys.items()}
    for k, p in per.items():
        stats["per_system"][k] = {"n": len(p["steps"]), "steps": describe(p["steps"]), "error_step_rel_pos": describe(p["rel"]),
                                  "error_step_abs": describe(p["ms"]), "agents": describe(p["agents"]), "chars": describe(p["chars"]),
                                  "llm_tokens": describe(p["toks"]), "images": describe(p["imgs"]), "source_benchmark_counts": dict(p["bench"])}
    stats["summary"] = {"steps": describe(stats["steps_per_traj"]), "error_step_rel_pos": describe(stats["error_step_rel_pos"]),
                        "agents": describe(stats["agents_per_traj"]), "chars": describe(chars), "llm_tokens": describe(toks)}
    write_json(os.path.join(NOTES_DIR, f"{SLUG}_stats.json"), stats)

    out = []
    cols = ["captain-agent", "magentic-one", "swe-agent"]
    out.append("| Statistic | Overall | " + " | ".join(cols) + " |")
    out.append("|---|---|" + "---|" * len(cols))
    out.append(f"| # released trajectories (all failed) | {len(recs)} | " + " | ".join(str(len(per[c]['steps'])) for c in cols) + " |")
    out.append(f"| source benchmark | {dict(bench)} | " + " | ".join(str(dict(per[c]['bench'])) for c in cols) + " |")
    out.append(f"| steps (LLM calls) per trajectory | {fmt_desc(describe(stats['steps_per_traj']))} | " + " | ".join(fmt_desc(describe(per[c]['steps'])) for c in cols) + " |")
    E = [0, 5, 10, 20, 30, 50, 100, 10**9]
    out.append(f"| steps histogram | {hist_str(stats['steps_per_traj'], E)} | " + " | ".join(hist_str(per[c]['steps'], E) for c in cols) + " |")
    out.append(f"| distinct agent names per trajectory | {fmt_desc(describe(stats['agents_per_traj']))} | " + " | ".join(fmt_desc(describe(per[c]['agents'])) for c in cols) + " |")
    out.append(f"| annotated error step (1-based step_id) | {fmt_desc(describe(ms_abs))} | " + " | ".join(fmt_desc(describe(per[c]['ms'])) for c in cols) + " |")
    out.append(f"| relative position (step/len) | {fmt_desc(describe(stats['error_step_rel_pos']))} | " + " | ".join(fmt_desc(describe(per[c]['rel'])) for c in cols) + " |")
    out.append(f"| output characters per trajectory (agent outputs + tool calls only) | {fmt_desc(describe(chars))} | " + " | ".join(fmt_desc(describe(per[c]['chars'])) for c in cols) + " |")
    out.append(f"| total LLM tokens per trajectory (sum of usage.total_tokens; 0 where not logged) | {fmt_desc(describe(toks))} | " + " | ".join(fmt_desc(describe(per[c]['toks'])) for c in cols) + " |")
    out.append(f"| traces with non-numeric mistake_step ('none' / 'Step N') | {len(no_step)} ({', '.join(no_step)}) | | | |")
    out.append(f"| screenshots (png) per trajectory | {fmt_desc(describe(imgs))} | " + " | ".join(fmt_desc(describe(per[c]['imgs'])) for c in cols) + " |")
    out.append("\n**Faulty agent distribution by system:**\n")
    for c in cols:
        out.append(f"*{c}*\n\n" + counter_table(faulty_by_sys[c], "mistake_agent", "count", top=12) + "\n")

    # example: shortest multi-agent trace with <=15 steps (prefer magentic-one / captain-agent, i.e. true MAS)
    examples = [t for t in examples if t[4] is not None]
    cands = sorted(examples, key=lambda t: (t[3], t[5]))
    pick = next((t for t in cands if t[3] <= 15 and t[8] >= 2 and t[5] / t[3] <= 2500 and t[6] != "swe-agent"), None) \
        or next((t for t in cands if t[8] >= 2), None) or cands[0]
    rel, meta, steps, n, ms, tc, sysn, bname, na = pick
    raw = {"dir": rel, "trace_metadata": meta, "step_records": steps}
    write_json(os.path.join(NOTES_DIR, f"{SLUG}_example.json"), raw)
    norm_steps = []
    for i, st in enumerate(steps):
        text, calls = step_output(st)
        obs = step_observation(st, steps[i + 1] if i + 1 < n else None)
        content = text
        if calls:
            content += ("\n" if content else "") + "Action: " + json.dumps(calls, ensure_ascii=False)
        if st.get("tool_logs"):
            content += "\nTool logs: " + json.dumps(st["tool_logs"], ensure_ascii=False)[:2000]
        if obs:
            content += "\nObservation: " + obs
        norm_steps.append({"idx": st["step_id"], "agent": st["agent_name"], "content": content,
                           "prompt_tokens": (st.get("output", {}).get("usage") or {}).get("prompt_tokens"),
                           "n_input_messages": len(st["input"]["messages"])})
    final = None
    for st in reversed(steps):
        t, _ = step_output(st)
        if "FINAL ANSWER" in t or "final answer" in t.lower():
            final = t; break
    ann = {"faulty_agent": meta["mistake_agent"], "faulty_step": ms, "category": None, "reason": meta["mistake_reason"],
           "extra": {"system_name": meta["system_name"], "task_id": meta["task_id"], "run_id": meta["run_id"], "source_benchmark": bname,
                     "agent_configuration": meta.get("agent_configuration"), "tests_status": meta.get("tests_status"),
                     "step_indexing": "1-based step_id = one LLM invocation (input context + output)"}}
    path, size = write_norm_example(SLUG, rel, meta["task_instruction"], meta.get("ground_truth"), final, norm_steps, ann)
    out.append(f"\n\n## Example trajectory\n\nRun `{rel}` (system {sysn}, source {bname}), {n} steps (LLM calls), {na} distinct agents, {tc} output characters.\n")
    out.append(f"**Task:** {meta['task_instruction'][:1500]}\n\n**Ground-truth answer:** {meta.get('ground_truth')}\n")
    out.append("Each step below shows the agent's *output* (plus tool calls) and, where present, the tool *observation* that was fed into the next step's input. The full per-step input context (system prompt + all prior messages) is in the raw record.\n")
    out.append(md_steps(norm_steps, ms))
    out.append(f"\n**Annotation:** mistake_agent = `{meta['mistake_agent']}`, mistake_step = `{ms}` (1-based step_id), mistake_reason = \"{meta['mistake_reason']}\".\n")
    out.append(f"\n(normalised example written to {path}, {size/1024:.1f} KB)\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
