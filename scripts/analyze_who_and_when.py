#!/usr/bin/env python3
"""Compute statistics + pick an example for Who&When (Kevin355/Who_and_When).
Usage: python3 -I analyze_who_and_when.py <data_dir>
Writes notes/who_and_when_stats.json, _example.json, _example_norm.json and prints a
markdown block (stats tables + example) to stdout for inclusion in the notes.
"""
import glob
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fa4_common import (NOTES_DIR, counter_table, describe, fmt_desc, hist_str, md_steps,  # noqa: E402
                    write_json, write_norm_example)

SLUG = "who_and_when"


def agent_of(h):
    """Agent name of a history entry. Hand-crafted: role string (e.g. 'Orchestrator (thought)');
    algorithm-generated: 'name' field."""
    return h.get("name") or h.get("role")


def base_agent(a):
    # collapse 'Orchestrator (thought)', 'Orchestrator (-> WebSurfer)' -> 'Orchestrator'
    return re.sub(r"\s*\(.*\)$", "", a)


def main():
    data_dir = sys.argv[1]
    recs = []
    for sub in ["Hand-Crafted", "Algorithm-Generated"]:
        for f in sorted(glob.glob(os.path.join(data_dir, "Who&When", sub, "*.json")),
                        key=lambda p: int(os.path.basename(p).split(".")[0])):
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
            d["_subset"] = sub
            d["_file"] = os.path.relpath(f, data_dir)
            recs.append(d)

    stats = {"n_trajectories": len(recs), "steps_per_traj": [], "error_step_rel_pos": [],
             "agents_per_traj": [], "faulty_agent_counts": {}, "category_counts": {},
             "source_benchmark_counts": {}, "splits": {}, "per_subset": {}}
    faulty = Counter(); faulty_base = Counter(); bench = Counter(); splits = Counter()
    chars = []; is_correct = Counter(); levels = Counter(); mtype = Counter()
    per_sub = {}
    rows_for_example = []
    for d in recs:
        sub = d["_subset"]
        hist = d["history"]
        n = len(hist)
        ms = int(str(d["mistake_step"]).strip("'\""))
        ma = str(d["mistake_agent"]).strip("'\"")
        agents = {agent_of(h) for h in hist if agent_of(h) not in (None, "human")}
        agents_base = {base_agent(a) for a in agents}
        # benchmark: GAIA question_IDs are UUIDs; AssistantBench ones are 64-hex sha
        qid = str(d["question_ID"]).strip("'\"")
        src = "AssistantBench" if re.fullmatch(r"[0-9a-f]{64}", qid) else ("GAIA" if re.fullmatch(r"[0-9a-f-]{36}", qid) else "unknown")
        total_chars = sum(len(h.get("content") or "") for h in hist)
        ic = d.get("is_corrected", d.get("is_correct"))
        is_correct[str(ic)] += 1
        if d.get("level") is not None:
            levels[(sub, str(d["level"]).strip("'\""))] += 1
        if d.get("mistake_type"):
            mtype[str(d["mistake_type"])] += 1
        stats["steps_per_traj"].append(n)
        rel = (ms + 1) / n  # steps are 0-based indices into history
        stats["error_step_rel_pos"].append(round(rel, 4))
        stats["agents_per_traj"].append(len(agents_base))
        faulty[ma] += 1; faulty_base[base_agent(ma)] += 1; bench[src] += 1; splits[sub] += 1
        chars.append(total_chars)
        ps = per_sub.setdefault(sub, {"steps": [], "rel": [], "agents": [], "chars": [], "bench": Counter(), "faulty": Counter(), "ms_abs": []})
        ps["steps"].append(n); ps["rel"].append(rel); ps["agents"].append(len(agents_base)); ps["chars"].append(total_chars)
        ps["bench"][src] += 1; ps["faulty"][base_agent(ma)] += 1; ps["ms_abs"].append(ms)
        rows_for_example.append((d, n, ms, src, total_chars))
        if ms >= n:
            print(f"WARNING: mistake_step {ms} >= len(history) {n} in {d['_file']}", file=sys.stderr)

    stats["faulty_agent_counts"] = dict(faulty.most_common())
    stats["faulty_agent_counts_collapsed"] = dict(faulty_base.most_common())
    stats["category_counts"] = dict(mtype.most_common())
    stats["source_benchmark_counts"] = dict(bench)
    stats["splits"] = dict(splits)
    stats["is_correct_counts"] = dict(is_correct)
    stats["level_counts"] = {f"{s}/level{l}": c for (s, l), c in sorted(levels.items())}
    stats["chars_per_traj"] = chars
    for sub, ps in per_sub.items():
        stats["per_subset"][sub] = {
            "n": len(ps["steps"]), "steps": describe(ps["steps"]), "error_step_rel_pos": describe(ps["rel"]),
            "error_step_abs": describe(ps["ms_abs"]), "agents": describe(ps["agents"]), "chars": describe(ps["chars"]),
            "source_benchmark_counts": dict(ps["bench"]), "faulty_agent_counts": dict(ps["faulty"].most_common()),
        }
    stats["summary"] = {"steps": describe(stats["steps_per_traj"]), "error_step_rel_pos": describe(stats["error_step_rel_pos"]),
                        "agents": describe(stats["agents_per_traj"]), "chars": describe(chars)}
    write_json(os.path.join(NOTES_DIR, f"{SLUG}_stats.json"), stats)

    # ---- markdown
    out = []
    out.append("| Statistic | Overall | Hand-Crafted | Algorithm-Generated |")
    out.append("|---|---|---|---|")
    hc, ag = per_sub["Hand-Crafted"], per_sub["Algorithm-Generated"]
    out.append(f"| # trajectories (all failed) | {len(recs)} | {len(hc['steps'])} | {len(ag['steps'])} |")
    out.append(f"| source benchmark | {dict(bench)} | {dict(hc['bench'])} | {dict(ag['bench'])} |")
    out.append(f"| steps per trajectory | {fmt_desc(describe(stats['steps_per_traj']))} | {fmt_desc(describe(hc['steps']))} | {fmt_desc(describe(ag['steps']))} |")
    out.append(f"| steps histogram | {hist_str(stats['steps_per_traj'], [0,5,10,20,30,50,100,1000])} | {hist_str(hc['steps'], [0,5,10,20,30,50,100,1000])} | {hist_str(ag['steps'], [0,5,10,20,30,50,100,1000])} |")
    out.append(f"| distinct agents per trajectory (collapsed Orchestrator variants) | {fmt_desc(describe(stats['agents_per_traj']))} | {fmt_desc(describe(hc['agents']))} | {fmt_desc(describe(ag['agents']))} |")
    out.append(f"| annotated error step (0-based index) | {fmt_desc(describe([int(round(r*n))-1 for r,n in zip(stats['error_step_rel_pos'],stats['steps_per_traj'])]))} | {fmt_desc(describe(hc['ms_abs']))} | {fmt_desc(describe(ag['ms_abs']))} |")
    out.append(f"| relative position of error step ((step+1)/len) | {fmt_desc(describe(stats['error_step_rel_pos']))} | {fmt_desc(describe(hc['rel']))} | {fmt_desc(describe(ag['rel']))} |")
    out.append(f"| characters per trajectory (sum of history contents) | {fmt_desc(describe(chars))} | {fmt_desc(describe(hc['chars']))} | {fmt_desc(describe(ag['chars']))} |")
    out.append(f"| approx tokens per trajectory (chars/4) | {int(describe(chars)['mean']/4)} mean | {int(describe(hc['chars'])['mean']/4)} mean | {int(describe(ag['chars'])['mean']/4)} mean |")
    out.append(f"| is_correct(ed) values | {dict(is_correct)} | | |")
    out.append(f"| GAIA level (where given) | {stats['level_counts']} | | |")
    out.append(f"| mistake_type (only 4 HC records have it) | {dict(mtype)} | | |")
    out.append("")
    out.append("**Faulty agent distribution (Hand-Crafted, Orchestrator variants collapsed):**\n")
    out.append(counter_table(hc["faulty"], "mistake_agent", "count"))
    out.append("\n**Faulty agent distribution (Algorithm-Generated, top 15 of %d distinct names):**\n" % len(ag["faulty"]))
    out.append(counter_table(ag["faulty"], "mistake_agent", "count", top=15))
    out.append("\n**Raw mistake_agent strings (top 12):**\n")
    out.append(counter_table(faulty, "mistake_agent (raw)", "count", top=12))

    # ---- example: shortest failed Hand-Crafted trajectory with <=15 steps if possible, else shortest overall
    cands = sorted(rows_for_example, key=lambda t: (t[1], t[4]))
    def n_agents(t):
        return len({base_agent(agent_of(h)) for h in t[0]["history"] if agent_of(h) != "human"})
    short = [t for t in cands if t[1] <= 15 and t[4] / t[1] <= 2500 and n_agents(t) >= 2]
    # prefer a multi-agent Hand-Crafted trace (orchestrator + specialist) with <=15 steps; else multi-agent Alg.-Generated
    pick = next((t for t in short if t[0]["_subset"] == "Hand-Crafted"), None) or (short[0] if short else cands[0])
    d, n, ms, src, tc = pick
    write_json(os.path.join(NOTES_DIR, f"{SLUG}_example.json"), {k: v for k, v in d.items() if not k.startswith("_")} | {"_file": d["_file"], "_subset": d["_subset"]})
    steps = [{"idx": i, "agent": agent_of(h), "content": h.get("content") or ""} for i, h in enumerate(d["history"])]
    ma = str(d["mistake_agent"]).strip("'\"")
    gt = d.get("groundtruth", d.get("ground_truth"))
    reason = str(d["mistake_reason"]).strip("'\"")
    ann = {"faulty_agent": ma, "faulty_step": ms, "category": d.get("mistake_type"), "reason": reason,
           "extra": {"subset": d["_subset"], "question_ID": str(d["question_ID"]).strip("'\""), "level": d.get("level"),
                     "is_correct": d.get("is_corrected", d.get("is_correct")), "source_benchmark": src,
                     "step_indexing": "0-based index into history (history[0] is the user question in Hand-Crafted)"}}
    final = None
    for h in reversed(d["history"]):
        if "FINAL ANSWER" in (h.get("content") or "") or "final answer" in (h.get("content") or "").lower():
            final = h.get("content"); break
    path, size = write_norm_example(SLUG, f"{d['_subset']}/{os.path.basename(d['_file'])}", d["question"], gt, final, steps, ann)
    out.append(f"\n\n## Example trajectory\n\nFile `{d['_file']}` ({d['_subset']}, source {src}), {n} steps, {tc} characters, "
               f"{len({base_agent(agent_of(h)) for h in d['history'] if agent_of(h)!='human'})} distinct agents.\n")
    out.append(f"**Task:** {d['question']}\n\n**Ground-truth answer:** {gt}\n")
    out.append(md_steps(steps, ms))
    out.append(f"\n**Annotation:** mistake_agent = `{ma}`, mistake_step = `{ms}` (0-based index into history), "
               f"mistake_reason = \"{reason}\"; is_correct = {d.get('is_corrected', d.get('is_correct'))}; "
               f"question_ID = {str(d['question_ID']).strip(chr(39))}; level = {d.get('level')}.\n")
    out.append(f"\n(normalised example written to {path}, {size/1024:.1f} KB)\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
