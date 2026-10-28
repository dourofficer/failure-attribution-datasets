#!/usr/bin/env python3
"""Statistics + example for Who&When Pro (HF Leoxx/whowhen_pro).
Usage: python3 -I analyze_who_and_when_pro.py <data_dir>   (dir containing data/*.jsonl)

Step conventions follow the official evaluation harness (whowhen_eval/render/*.py, score.py):
  smolagents   : steps = planning + action entries (cursor; 0-based if a planning entry comes first, else 1-based); gt.step identity
  alfagent     : steps = action entries, gt.step == step_number (1-based)
  mathchat     : steps = (round,position) turns except the bootstrap user_proxy turn; flat N = 2*round+position (1-based)
  metagpt      : steps = architect/engineer/reviewer stages (0-based); gt.stage
  macnet       : steps = author/critic/rewriter/sink turns -> coords 0.0,1.0,1.1,2.0; gt.(round,position)
  magentic-one : steps = kind=='agent' entries with coord 'R.P'; gt.step is the 'R.P' string
  debate/dylan : steps = turns inside kind=='round' entries; gt.round only (any turn in that round counts); gt.agents list
  dvd          : steps = trajectory[2:] (assistant/tool entries); gt.step is the native index (subtract 2)
  eva          : steps = assistant+tool pairs folded; gt rendered step = (gt.step-2)//2
  image_gui (coact/openai_cua/agentoccam/gemini): gt.step 1-indexed == step_number
  pixelcraft   : gt.(round,position) default scorer (image split)
Partial files (name contains PARTIAL) are read line-by-line and the (truncated) last line is skipped.
"""
import glob
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fa4_common import (NOTES_DIR, counter_table, describe, fmt_desc, hist_str, md_steps,  # noqa: E402
                        write_json, write_norm_example)

SLUG = "who_and_when_pro"
SINGLE_AGENT = {"smolagents", "alfagent", "eva", "openai_cua", "agentoccam", "gemini"}


def J(x):
    return json.loads(x) if isinstance(x, str) else x


def steps_of(framework, traj):
    """Return list of (coord_str, agent, content) in trajectory order, plus final answer."""
    steps = []
    final = None
    if framework in ("smolagents",):
        nonframing = [e for e in traj if e.get("kind") not in ("user", "final_answer")]
        cursor = 0 if nonframing and nonframing[0].get("kind") == "planning" else 1
        for e in nonframing:
            if e.get("kind") == "planning":
                steps.append((str(cursor), "agent", "Plan: " + (e.get("plan") or "")))
            else:
                c = "Thought/Code: " + (e.get("reasoning") or "")
                if e.get("code"):
                    c += "\nCode: " + str(e.get("code"))
                c += "\nObservation: " + str(e.get("observation") or "")
                if e.get("error"):
                    c += "\nError: " + str(e.get("error"))
                steps.append((str(cursor), "agent", c))
                if e.get("is_final_answer"):
                    final = str(e.get("observation") or "")[:2000]
            cursor += 1
    elif framework == "alfagent":
        for e in traj:
            if e.get("kind") == "action":
                steps.append((str(e["step_number"]), "agent", f"Thought: {e.get('reasoning','')}\nAction: {e.get('action','')}\nObservation: {e.get('observation','')}"))
    elif framework == "mathchat":
        for e in traj:
            if e.get("round") is None:
                if e.get("kind") == "final_answer":
                    final = e.get("content")
                continue
            if e["round"] == 0 and e["position"] == 0 and e["agent_id"] == "user_proxy":
                steps.append(("input", "user_proxy (framing prompt, not a scorable step)", e.get("output") or ""))
                continue
            steps.append((str(2 * e["round"] + e["position"]), e["agent_id"], e.get("output") or ""))
    elif framework == "metagpt":
        for e in traj:
            if e.get("kind") == "final_answer":
                final = e.get("content"); continue
            if "stage" in e:
                steps.append((str(e["stage"]), e["agent_id"], e.get("output") or ""))
    elif framework == "macnet":
        layer = {"author": (0, 0), "critic": (1, 0), "rewriter": (1, 1), "sink": (2, 0)}
        for e in traj:
            if e.get("kind") == "final_answer":
                final = e.get("content"); continue
            if "role" in e and e["role"] in layer:
                r, p = layer[e["role"]]
                steps.append((f"{r}.{p}", f"{e['agent_id']} ({e['role']})", e.get("output") or ""))
    elif framework == "magentic-one":
        for e in traj:
            if e.get("kind") != "agent":
                continue
            c = e.get("output") or ""
            if e.get("tool_actions"):
                c += "\nAction: " + json.dumps(e["tool_actions"], ensure_ascii=False)
            steps.append((f"{e['round']}.{e['position']}", e["agent"], c))
            if isinstance(e.get("phase"), list) and "final_answer" in e["phase"]:
                final = e.get("output")
    elif framework in ("debate", "dylan"):
        for e in traj:
            if e.get("kind") == "final_answer":
                final = e.get("content"); continue
            if e.get("kind") == "round":
                for pos, t in enumerate(e.get("turns") or []):
                    p = t.get("position", pos)
                    steps.append((f"{e['round']}.{p}", t["agent_id"] + (f" ({t['role']})" if t.get("role") else ""), t.get("output") or ""))
    elif framework == "dvd":
        for i, e in enumerate(traj):
            if i < 2:
                continue
            k = e.get("kind")
            agent = "orchestrator" if k == "assistant" else f"tool:{e.get('tool_name')}"
            c = e.get("content") or ""
            if e.get("tool_calls"):
                c += "\nAction: " + json.dumps(e["tool_calls"], ensure_ascii=False)
            steps.append((str(i - 2), agent, c))
            if k == "assistant" and not e.get("tool_calls"):
                final = e.get("content")
    elif framework == "eva":
        body = traj[2:]
        n = 0
        i = 0
        while i < len(body):
            e = body[i]
            c = e.get("content") or ""
            if e.get("tool_calls"):
                c += "\nAction: " + json.dumps(e["tool_calls"], ensure_ascii=False)
            if i + 1 < len(body) and body[i + 1].get("kind") == "tool":
                c += "\nObservation: " + str(body[i + 1].get("content") or "")
                i += 1
            steps.append((str(n), "agent", c))
            if e.get("kind") == "assistant" and not e.get("tool_calls"):
                final = e.get("content")
            n += 1
            i += 1
    else:  # image split frameworks (pixelcraft, coact, openai_cua, agentoccam, gemini) — generic handling
        n = 0
        for e in traj:
            if e.get("kind") in ("user", "system"):
                continue
            if e.get("kind") == "final_answer":
                final = e.get("content"); continue
            if e.get("kind") == "round":
                for pos, t in enumerate(e.get("turns") or []):
                    steps.append((f"{e['round']}.{t.get('position', pos)}", t.get("agent_id", "?"), t.get("output") or ""))
                continue
            coord = e.get("step_number") if e.get("step_number") is not None else (
                f"{e['round']}.{e['position']}" if e.get("round") is not None and e.get("position") is not None else n + 1)
            agent = e.get("agent") or e.get("agent_id") or e.get("role") or e.get("kind") or "agent"
            c = e.get("output") or e.get("content") or e.get("reasoning") or ""
            if isinstance(c, list):
                c = "\n".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in c)
            for k in ("action", "code", "observation"):
                if e.get(k):
                    c += f"\n{k.capitalize()}: {str(e[k])[:3000]}"
            steps.append((str(coord), str(agent), c))
            n += 1
    return steps, final


def gt_coord(framework, gt):
    if framework == "mathchat":
        return str(2 * gt["round"] + gt["position"])
    if framework == "metagpt":
        return str(gt["stage"])
    if framework in ("debate", "dylan"):
        return f"round {gt['round']}"
    if framework == "dvd":
        return str(gt["step"] - 2)
    if framework == "eva":
        return str((gt["step"] - 2) // 2)
    if gt.get("step") is not None:
        return str(gt["step"])
    if gt.get("round") is not None:
        return f"{gt['round']}.{gt['position']}" if gt.get("position") is not None else str(gt["round"])
    return None


def gt_index(framework, gt, steps):
    """0-based index of the labelled step among the scorable steps (debate/dylan: first turn of the round)."""
    coords = [c for c, _, _ in steps if c != "input"]
    g = gt_coord(framework, gt)
    if g is None:
        return None
    if framework in ("debate", "dylan"):
        r = str(gt["round"])
        for i, c in enumerate(coords):
            if c.split(".")[0] == r:
                return i
        return None
    try:
        return coords.index(g)
    except ValueError:
        return None


def main():
    data_dir = sys.argv[1]
    files = sorted(glob.glob(os.path.join(data_dir, "data", "*.jsonl")))
    tax = {}
    try:
        import re
        with open(os.path.join(data_dir, "taxonomy.yaml")) as f:
            for m in re.finditer(r"^([A-Z]+\.\d+):\n\s+name:\s*(.+)$", f.read(), re.M):
                tax[m.group(1)] = m.group(2).strip()
    except Exception as e:  # noqa
        print("taxonomy parse failed", e, file=sys.stderr)

    stats = {"n_trajectories": 0, "steps_per_traj": [], "error_step_rel_pos": [], "agents_per_traj": [],
             "faulty_agent_counts": {}, "category_counts": {}, "source_benchmark_counts": {}, "splits": {},
             "per_split": {}, "per_framework": {}, "notes": "image/image_gui splits: only a ~1 GB byte-range sample of the 6.8/11.2 GB files was downloaded"}
    split_c = Counter(); fw_c = Counter(); bench_c = Counter(); mode_c = Counter(); mode_fam = Counter(); faulty = Counter()
    faulty_role = Counter(); single_multi = Counter(); unmatched = Counter(); per_split = {}; per_fw = {}
    chars_all = []; examples = []
    for path in files:
        split = os.path.basename(path).split(".")[0]
        partial = "PARTIAL" in path
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
        if partial:
            lines = lines[:-1]  # drop truncated tail line
        for line in lines:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            fw = r["framework"]; bm = r["benchmark"]
            gt = J(r["ground_truth"]); traj = J(r["trajectory"]); ex = J(r["extras"]); task = J(r["task"])
            steps, final = steps_of(fw, traj)
            scorable = [s for s in steps if s[0] != "input"]
            n = len(scorable)
            gi = gt_index(fw, gt, steps)
            if gi is None:
                unmatched[fw] += 1
            roster = ex.get("agents") if isinstance(ex, dict) else None
            n_agents = len(roster) if roster else len({a for _, a, _ in scorable})
            total_chars = sum(len(c) for _, _, c in steps)
            fa = gt.get("agent") or (",".join(gt["agents"]) if gt.get("agents") else None) or "(single-agent)"
            mode = gt.get("mode")
            stats["n_trajectories"] += 1
            stats["steps_per_traj"].append(n)
            stats["agents_per_traj"].append(n_agents)
            if gi is not None and n:
                stats["error_step_rel_pos"].append(round((gi + 1) / n, 4))
            split_c[split] += 1; fw_c[fw] += 1; bench_c[bm] += 1; mode_c[mode] += 1; mode_fam[(mode or "?").split(".")[0]] += 1
            faulty[(fw, fa)] += 1
            faulty_role[fa if fw not in SINGLE_AGENT else "(single-agent)"] += 1
            single_multi["single" if fw in SINGLE_AGENT or n_agents <= 1 else "multi"] += 1
            chars_all.append(total_chars)
            ps = per_split.setdefault(split, {"n": 0, "steps": [], "rel": [], "chars": [], "fw": Counter(), "bench": Counter(), "modes": Counter()})
            ps["n"] += 1; ps["steps"].append(n); ps["chars"].append(total_chars); ps["fw"][fw] += 1; ps["bench"][bm] += 1; ps["modes"][mode] += 1
            if gi is not None and n:
                ps["rel"].append((gi + 1) / n)
            pf = per_fw.setdefault(fw, {"n": 0, "steps": [], "rel": [], "agents": [], "chars": [], "bench": Counter(), "modes": Counter(), "faulty": Counter()})
            pf["n"] += 1; pf["steps"].append(n); pf["agents"].append(n_agents); pf["chars"].append(total_chars); pf["bench"][bm] += 1; pf["modes"][mode] += 1; pf["faulty"][fa] += 1
            if gi is not None and n:
                pf["rel"].append((gi + 1) / n)
            if split in ("text", "video") and fw not in SINGLE_AGENT and n <= 15 and total_chars / max(n, 1) <= 2500 and gi is not None:
                examples.append((n, total_chars, r, steps, final, gi, gt, ex, task, fw, bm))

    stats["faulty_agent_counts"] = {f"{k[0]}/{k[1]}": v for k, v in faulty.most_common()}
    stats["faulty_agent_counts_collapsed"] = dict(faulty_role.most_common())
    stats["category_counts"] = {f"{k} {tax.get(k, '')}".strip(): v for k, v in mode_c.most_common()}
    stats["category_family_counts"] = dict(mode_fam.most_common())
    stats["source_benchmark_counts"] = dict(bench_c.most_common()); stats["framework_counts"] = dict(fw_c.most_common())
    stats["splits"] = dict(split_c); stats["single_vs_multi_agent"] = dict(single_multi); stats["gt_step_unmatched_by_framework"] = dict(unmatched)
    stats["chars_per_traj"] = chars_all
    for k, p in per_split.items():
        stats["per_split"][k] = {"n": p["n"], "steps": describe(p["steps"]), "error_step_rel_pos": describe(p["rel"]), "chars": describe(p["chars"]),
                                 "framework_counts": dict(p["fw"].most_common()), "benchmark_counts": dict(p["bench"].most_common()), "mode_counts": dict(p["modes"].most_common())}
    for k, p in per_fw.items():
        stats["per_framework"][k] = {"n": p["n"], "steps": describe(p["steps"]), "error_step_rel_pos": describe(p["rel"]), "agents": describe(p["agents"]),
                                     "chars": describe(p["chars"]), "benchmark_counts": dict(p["bench"]), "mode_counts": dict(p["modes"].most_common()), "faulty_agent_counts": dict(p["faulty"].most_common())}
    stats["summary"] = {"steps": describe(stats["steps_per_traj"]), "error_step_rel_pos": describe(stats["error_step_rel_pos"]),
                        "agents": describe(stats["agents_per_traj"]), "chars": describe(chars_all)}
    write_json(os.path.join(NOTES_DIR, f"{SLUG}_stats.json"), stats)

    out = []
    out.append(f"Rows analysed: {stats['n_trajectories']} (text {split_c.get('text',0)} + video {split_c.get('video',0)} complete; "
               f"image {split_c.get('image',0)} + image_gui {split_c.get('image_gui',0)} from ~1 GB samples of each file). Paper total: 12,326.\n")
    out.append("| Statistic | All analysed rows | text | video | image (sample) | image_gui (sample) |")
    out.append("|---|---|---|---|---|---|")
    sp = ["text", "video", "image", "image_gui"]
    def col(fn):
        return " | ".join(fn(per_split[s]) if s in per_split else "n/a" for s in sp)
    out.append(f"| # trajectories (all failed by construction) | {stats['n_trajectories']} | " + col(lambda p: str(p['n'])) + " |")
    out.append(f"| scorable steps per trajectory | {fmt_desc(describe(stats['steps_per_traj']))} | " + col(lambda p: fmt_desc(describe(p['steps']))) + " |")
    E = [0, 3, 5, 10, 20, 30, 50, 10**9]
    out.append(f"| steps histogram | {hist_str(stats['steps_per_traj'], E)} | " + col(lambda p: hist_str(p['steps'], E)) + " |")
    out.append(f"| relative position of injected step ((idx+1)/len) | {fmt_desc(describe(stats['error_step_rel_pos']))} | " + col(lambda p: fmt_desc(describe(p['rel']))) + " |")
    out.append(f"| characters per trajectory (step contents, images excluded) | {fmt_desc(describe(chars_all))} | " + col(lambda p: fmt_desc(describe(p['chars']))) + " |")
    out.append(f"| agents per trajectory (roster size; 1 for single-agent) | {fmt_desc(describe(stats['agents_per_traj']))} | | | | |")
    out.append(f"| single- vs multi-agent rows | {dict(single_multi)} | | | | |")
    out.append(f"| rows whose GT step could not be matched to a rendered step | {dict(unmatched) or 0} | | | | |")
    out.append("\n**Rows per framework (with benchmark, steps, agents, error position):**\n")
    out.append("| framework | n | benchmarks | steps (mean/med/min/max) | agents | err. rel. pos. mean | top faulty agent |")
    out.append("|---|---|---|---|---|---|---|")
    for fw, p in sorted(per_fw.items(), key=lambda kv: -kv[1]["n"]):
        d = describe(p["steps"]); a = describe(p["agents"]); rp = describe(p["rel"])
        out.append(f"| {fw} | {p['n']} | {', '.join(f'{b}:{c}' for b, c in p['bench'].most_common())} | {d['mean']}/{d['median']}/{d['min']}/{d['max']} | {a['mean']} | {rp.get('mean','n/a')} | {p['faulty'].most_common(1)[0][0]} ({p['faulty'].most_common(1)[0][1]}) |")
    out.append("\n**Error-mode distribution (ground_truth.mode):**\n")
    out.append(counter_table(Counter(stats["category_counts"]), "mode", "count"))
    out.append("\n**Error-mode family:**\n")
    out.append(counter_table(mode_fam, "family", "count"))
    out.append("\n**Source benchmark distribution:**\n")
    out.append(counter_table(bench_c, "benchmark", "count"))
    out.append("\n**Faulty agent (multi-agent frameworks only; framework/agent):**\n")
    out.append(counter_table(Counter({k: v for k, v in stats["faulty_agent_counts"].items() if not k.endswith("(single-agent)")}), "framework/agent", "count", top=25))

    # example: prefer magentic-one (orchestrator MAS, GAIA) short trace, else any multi-agent
    examples.sort(key=lambda t: (t[0], t[1]))
    # prefer a magentic-one trace with 6-12 scorable steps that contains tool actions and is not the very first/last step
    def good(t):
        return t[9] == "magentic-one" and 6 <= t[0] <= 12 and 0 < t[5] < t[0] - 1 and any("Action:" in c for _, _, c in t[3])
    pick = next((t for t in examples if good(t)), None) or next((t for t in examples if t[9] == "magentic-one" and t[0] >= 4), None) \
        or next((t for t in examples if t[0] >= 4), None) or examples[0]
    n, tc, r, steps, final, gi, gt, ex, task, fw, bm = pick
    raw = dict(r);
    for k in ("task", "trajectory", "ground_truth", "extras"):
        raw[k] = J(raw[k])
    write_json(os.path.join(NOTES_DIR, f"{SLUG}_example.json"), raw)
    norm_steps = [{"idx": c, "agent": a, "content": t} for c, a, t in steps]
    scor = [s for s in steps if s[0] != "input"]
    faulty_coord = scor[gi][0]
    fa = gt.get("agent") or (gt.get("agents") if gt.get("agents") else None)
    ann = {"faulty_agent": fa if not isinstance(fa, list) else ",".join(fa), "faulty_step": faulty_coord,
           "category": f"{gt.get('mode')} ({tax.get(gt.get('mode'), '')})", "reason": None,
           "extra": {"ground_truth_raw": gt, "framework": fw, "benchmark": bm, "extras": ex,
                     "step_indexing": "framework-specific coordinate as rendered by the official harness (see script docstring)",
                     "injected_entries": [i for i, e in enumerate(J(r["trajectory"])) if isinstance(e, dict) and (e.get("is_injected") or e.get("injected") or ("injected" in (e.get("phase") or []) if isinstance(e.get("phase"), list) else False))]}}
    gt_answer = task.get("answer")
    final_out = (ex.get("final_answer") if isinstance(ex, dict) else None) or final
    path, size = write_norm_example(SLUG, r["id"], task.get("query"), gt_answer, final_out, norm_steps, ann)
    out.append(f"\n\n## Example trajectory\n\nRow id `{r['id']}` (framework {fw}, benchmark {bm}, split text), {n} scorable steps, {tc} characters, agents: {[a['id'] for a in ex.get('agents', [])] if isinstance(ex, dict) and ex.get('agents') else 'n/a'}.\n")
    out.append(f"**Task:** {str(task.get('query'))[:1500]}\n\n**Ground-truth answer:** {gt_answer}\n\n**System's final answer:** {str(final_out)[:500]}\n")
    out.append(md_steps(norm_steps, faulty_coord))
    out.append(f"\n**Annotation (ground_truth):** `{json.dumps(gt)}` → faulty agent = `{ann['faulty_agent']}`, faulty step coordinate = `{faulty_coord}`, "
               f"error mode = `{gt.get('mode')}` ({tax.get(gt.get('mode'), '')}). No free-text reason is provided (labels are by construction). "
               f"Trajectory entries flagged as injected: {ann['extra']['injected_entries']}.\n")
    out.append(f"\n(normalised example written to {path}, {size/1024:.1f} KB)\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
