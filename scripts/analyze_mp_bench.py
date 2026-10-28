#!/usr/bin/env python3
"""Statistics + example for MP-Bench (adobe-research/multi-agent-eval-bench).
Usage: python3 -I analyze_mp_bench.py <raw_repo_dir> <sources_dir>
  raw_repo_dir: clone of adobe-research/multi-agent-eval-bench (contains MP-Bench/<annotator>/<split>/<n>.json)
  sources_dir : output of mp_bench_fetch_sources.py (index.json + fetched logs)
Re-implements (without executing) the step segmentation of the official
build_annotated_from_log_source.py: Who&When JSON logs -> history entries (0-based);
MAST console_log.txt -> turns split on '---------- AGENT ----------' delimiters after
'SCENARIO.PY STARTING !#!#' (0-based).
"""
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fa4_common import (NOTES_DIR, counter_table, describe, fmt_desc, hist_str, md_steps,  # noqa: E402
                        write_json, write_norm_example)

SLUG = "mp_bench"
_DELIM = re.compile(r"^-{10} (.+?) -{10}$")


def parse_console_log(content):
    marker = "SCENARIO.PY STARTING !#!#"
    pos = content.find(marker)
    if pos != -1:
        content = content[pos + len(marker):]
    turns, cur, lines = [], None, []
    for line in content.splitlines():
        m = _DELIM.match(line.strip())
        if m:
            if cur is not None:
                turns.append({"role": cur, "content": "\n".join(lines).strip()})
            cur, lines = m.group(1).strip(), []
        elif cur is not None:
            lines.append(line)
    if cur is not None:
        turns.append({"role": cur, "content": "\n".join(lines).strip()})
    return turns


def base_agent(a):
    return re.sub(r"\s*\(.*\)$", "", a or "")


def load_source(entry, src_dir):
    """Return (question, ground_truth, history[list of {role,content}], source_kind, is_correct)."""
    key = hashlib.sha1(entry["log_source"].encode()).hexdigest()[:16]
    d = os.path.join(src_dir, key)
    url = entry["log_source"]
    if url.endswith(".json"):
        fname = [f for f in os.listdir(d) if f.endswith(".json")][0]
        with open(os.path.join(d, fname), encoding="utf-8") as f:
            raw = json.load(f)
        hist = [{"role": h.get("name") or h.get("role"), "content": h.get("content", "")} for h in raw.get("history", [])]
        sub = "Who&When/Hand-Crafted" if "Hand-Crafted" in url else "Who&When/Algorithm-Generated"
        return raw.get("question"), raw.get("ground_truth", raw.get("groundtruth")), hist, sub, raw.get("is_correct", raw.get("is_corrected")), raw
    with open(os.path.join(d, "console_log.txt"), encoding="utf-8", errors="replace") as f:
        turns = parse_console_log(f.read())
    q = gt = ""
    for name, var in (("prompt.txt", "q"), ("expected_answer.txt", "gt")):
        p = os.path.join(d, name)
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                if var == "q":
                    q = f.read().strip()
                else:
                    gt = f.read().strip()
    level = "L3" if "level_3" in url else ("L2" if "level_2" in url else "L?")
    return q, gt, turns, f"MAST/MagenticOne_GAIA {level}", None, None


def main():
    raw_dir, src_dir = sys.argv[1], sys.argv[2]
    # index.json is only written when the fetcher finishes; otherwise rebuild the mapping from the raw files
    ipath = os.path.join(src_dir, "index.json")
    if os.path.exists(ipath):
        with open(ipath) as f:
            index = json.load(f)
        by_url = {v["log_source"]: v for v in index.values()}
    else:
        by_url = {}
        for fpath in glob.glob(os.path.join(raw_dir, "MP-Bench", "*", "*", "*.json")):
            with open(fpath, encoding="utf-8") as f:
                url = json.load(f)["log_source"]
            key = hashlib.sha1(url.encode()).hexdigest()[:16]
            d = os.path.join(src_dir, key)
            main_name = "console_log.txt" if url.endswith(".txt") else "x.json"
            ok = os.path.isdir(d) and any(fn.endswith(".json") or fn == "console_log.txt" for fn in os.listdir(d)) and \
                 (not url.endswith(".txt") or os.path.exists(os.path.join(d, "console_log.txt")))
            by_url[url] = {"log_source": url, "files": {main_name: "ok" if ok else "missing"}}
    # group annotation files by (split, instance number) across annotators
    inst = defaultdict(dict)
    for fpath in sorted(glob.glob(os.path.join(raw_dir, "MP-Bench", "*", "*", "*.json"))):
        ann_id, split, fn = fpath.split(os.sep)[-3:]
        with open(fpath, encoding="utf-8") as f:
            d = json.load(f)
        inst[(split, fn)][ann_id] = d
    # sanity: same log_source across annotators
    mism = 0
    for k, v in inst.items():
        srcs = {d["log_source"] for d in v.values()}
        if len(srcs) != 1:
            mism += 1
            print("WARNING differing log_source across annotators", k, srcs, file=sys.stderr)

    stats = {"n_trajectories": len(inst), "steps_per_traj": [], "error_step_rel_pos": [], "agents_per_traj": [],
             "faulty_agent_counts": {}, "category_counts": {}, "source_benchmark_counts": {}, "splits": {},
             "per_split": {}, "n_annotation_files": sum(len(v) for v in inst.values()), "log_source_mismatch_instances": mism}
    cat = Counter(); cat_by_split = {}; faulty = Counter(); faulty_split = {}; src_c = Counter(); split_c = Counter()
    n_flag_per_file = []; consensus = Counter(); consensus_split = {}; per_split = {}; chars_all = []
    ann_steps_per_inst = []; earliest_rel = []; all_rel = []
    examples = []; missing = 0
    for (split, fn), anns in sorted(inst.items(), key=lambda kv: (kv[0][0], int(kv[0][1].split(".")[0]))):
        url = next(iter(anns.values()))["log_source"]
        entry = by_url.get(url)
        if not entry or not any(v in ("ok", "cached") for v in entry["files"].values()):
            missing += 1; continue
        q, gt, hist, src_kind, is_corr, raw = load_source(entry, src_dir)
        n = len(hist)
        agents = {base_agent(h["role"]) for h in hist if h["role"] not in (None, "human")}
        tot_chars = sum(len(h["content"] or "") for h in hist)
        # per-step votes
        votes = defaultdict(set); per_step_ann = defaultdict(list)
        for aid, d in anns.items():
            n_flag_per_file.append(len(d["annotation"]))
            for a in d["annotation"]:
                try:
                    s = int(a["step"])
                except ValueError:
                    continue
                if str(a.get("fail_annotation", "1")) != "1":
                    continue
                if s >= n:
                    print(f"WARNING step {s} >= n {n} in {split}/{fn} annotator {aid}", file=sys.stderr)
                votes[s].add(aid)
                per_step_ann[s].append({"annotator": aid, **a})
                cat[a.get("fail_category") or ""] += 1
                cat_by_split.setdefault(split, Counter())[a.get("fail_category") or ""] += 1
                ag = base_agent(hist[s]["role"]) if s < n else "?"
                faulty[ag] += 1; faulty_split.setdefault(split, Counter())[ag] += 1
                all_rel.append((s + 1) / n)
        for s, who in votes.items():
            consensus[len(who)] += 1; consensus_split.setdefault(split, Counter())[len(who)] += 1
        flagged = sorted(votes)
        ann_steps_per_inst.append(len(flagged))
        stats["steps_per_traj"].append(n); stats["agents_per_traj"].append(len(agents))
        if flagged:
            # "error step" for the position statistic = earliest step flagged by a majority (>=2), else earliest flagged
            maj = [s for s in flagged if len(votes[s]) >= 2]
            e = maj[0] if maj else flagged[0]
            stats["error_step_rel_pos"].append(round((e + 1) / n, 4)); earliest_rel.append((e + 1) / n)
        src_c[src_kind] += 1; split_c[split] += 1; chars_all.append(tot_chars)
        ps = per_split.setdefault(split, {"n": 0, "steps": [], "agents": [], "chars": [], "nflag": [], "rel": [], "src": Counter(), "n_ann": Counter()})
        ps["n"] += 1; ps["steps"].append(n); ps["agents"].append(len(agents)); ps["chars"].append(tot_chars); ps["nflag"].append(len(flagged)); ps["src"][src_kind] += 1
        ps["n_ann"][len(anns)] += 1
        if flagged:
            ps["rel"].append(stats["error_step_rel_pos"][-1])
        if 5 <= n <= 15 and tot_chars / n <= 2500 and len(agents) >= 2 and flagged:
            examples.append((n, tot_chars, split, fn, url, q, gt, hist, src_kind, is_corr, anns, votes, per_step_ann, raw))

    stats["category_counts"] = dict(cat.most_common()); stats["category_counts_by_split"] = {k: dict(v.most_common()) for k, v in cat_by_split.items()}
    stats["faulty_agent_counts"] = dict(faulty.most_common()); stats["faulty_agent_counts_by_split"] = {k: dict(v.most_common()) for k, v in faulty_split.items()}
    stats["source_benchmark_counts"] = dict(src_c); stats["splits"] = dict(split_c); stats["chars_per_traj"] = chars_all
    stats["flagged_steps_per_annotation_file"] = describe(n_flag_per_file); stats["distinct_flagged_steps_per_instance"] = describe(ann_steps_per_inst)
    stats["consensus_counts"] = {f"flagged_by_{k}_annotators": v for k, v in sorted(consensus.items())}
    stats["consensus_counts_by_split"] = {s: {f"by_{k}": v for k, v in sorted(c.items())} for s, c in consensus_split.items()}
    stats["all_flagged_step_rel_pos"] = describe(all_rel); stats["instances_missing_source"] = missing
    for k, p in per_split.items():
        stats["per_split"][k] = {"n": p["n"], "steps": describe(p["steps"]), "agents": describe(p["agents"]), "chars": describe(p["chars"]),
                                 "distinct_flagged_steps": describe(p["nflag"]), "error_step_rel_pos": describe(p["rel"]), "source_counts": dict(p["src"]),
                                 "annotators_per_instance": dict(p["n_ann"])}
    stats["summary"] = {"steps": describe(stats["steps_per_traj"]), "error_step_rel_pos": describe(stats["error_step_rel_pos"]), "agents": describe(stats["agents_per_traj"]), "chars": describe(chars_all)}
    write_json(os.path.join(NOTES_DIR, f"{SLUG}_stats.json"), stats)

    out = []
    out.append("| Statistic | Overall | manual (hand-crafted MAS) | automatic (algorithm-generated MAS) |")
    out.append("|---|---|---|---|")
    m, a = per_split["manual"], per_split["automatic"]
    out.append(f"| # execution logs (instances; all failed runs) | {len(inst)} ({missing} missing source) | {m['n']} | {a['n']} |")
    out.append(f"| # annotation files (3 annotators x instances) | {stats['n_annotation_files']} | | |")
    out.append(f"| source of logs | {dict(src_c)} | {dict(m['src'])} | {dict(a['src'])} |")
    out.append(f"| steps per log | {fmt_desc(describe(stats['steps_per_traj']))} | {fmt_desc(describe(m['steps']))} | {fmt_desc(describe(a['steps']))} |")
    E = [0, 5, 10, 20, 30, 50, 100, 10**9]
    out.append(f"| steps histogram | {hist_str(stats['steps_per_traj'], E)} | {hist_str(m['steps'], E)} | {hist_str(a['steps'], E)} |")
    out.append(f"| distinct agents per log | {fmt_desc(describe(stats['agents_per_traj']))} | {fmt_desc(describe(m['agents']))} | {fmt_desc(describe(a['agents']))} |")
    out.append(f"| characters per log | {fmt_desc(describe(chars_all))} | {fmt_desc(describe(m['chars']))} | {fmt_desc(describe(a['chars']))} |")
    out.append(f"| flagged steps per annotation file (one annotator, one log) | {fmt_desc(stats['flagged_steps_per_annotation_file'])} | | |")
    out.append(f"| distinct flagged steps per log (union over 3 annotators) | {fmt_desc(stats['distinct_flagged_steps_per_instance'])} | {fmt_desc(describe(m['nflag']))} | {fmt_desc(describe(a['nflag']))} |")
    out.append(f"| flagged (step) consensus: #steps flagged by 1/2/3 annotators | {stats['consensus_counts']} | {stats['consensus_counts_by_split'].get('manual')} | {stats['consensus_counts_by_split'].get('automatic')} |")
    out.append(f"| rel. position of earliest majority-flagged step ((idx+1)/len) | {fmt_desc(describe(stats['error_step_rel_pos']))} | {fmt_desc(describe(m['rel']))} | {fmt_desc(describe(a['rel']))} |")
    out.append(f"| rel. position of all flagged steps | {fmt_desc(stats['all_flagged_step_rel_pos'])} | | |")
    out.append("\n**Failure-category distribution (over all annotator step flags):**\n")
    out.append(counter_table(cat, "fail_category", "flags"))
    out.append("\n**Agent blamed (agent at flagged step; Orchestrator sub-roles collapsed), top 15:**\n")
    out.append(counter_table(faulty, "agent", "flags", top=15))
    out.append("\n**Agent blamed by split (top 8 each):**\n")
    for s in ("manual", "automatic"):
        out.append(f"*{s}*\n\n" + counter_table(faulty_split[s], "agent", "flags", top=8) + "\n")

    # ---- example: shortest manual log with 5-15 steps, >=2 agents, preferring one with >=2 flagged steps and some disagreement
    examples.sort(key=lambda t: (t[2] != "manual", -len(t[11]), t[0], t[1]))
    pick = next((t for t in examples if t[2] == "manual" and len(t[11]) >= 2), None) or examples[0]
    n, tc, split, fn, url, q, gt, hist, src_kind, is_corr, anns, votes, per_step_ann, raw = pick
    raw_rec = {"split": split, "instance_file": fn, "log_source": url, "annotations_by_annotator": anns,
               "reconstructed_history": hist, "question": q, "ground_truth": gt, "source_kind": src_kind, "source_raw_record": raw}
    write_json(os.path.join(NOTES_DIR, f"{SLUG}_example.json"), raw_rec)
    steps = [{"idx": i, "agent": h["role"], "content": h["content"] or ""} for i, h in enumerate(hist)]
    flagged = sorted(votes)
    maj = [s for s in flagged if len(votes[s]) >= 2]
    per_ann = {aid: [{k: v for k, v in x.items()} for x in d["annotation"]] for aid, d in anns.items()}
    primary = maj[0] if maj else flagged[0]
    reasons = "; ".join(f"[step {s}, annotator {x['annotator']}, {x.get('fail_category')}] {x.get('fail_reason')}" for s in flagged for x in per_step_ann[s])
    ann_norm = {"faulty_agent": base_agent(hist[primary]["role"]), "faulty_step": flagged,
                "category": sorted({x.get("fail_category") for s in flagged for x in per_step_ann[s]}),
                "reason": reasons,
                "extra": {"per_annotator": per_ann, "votes_per_step": {str(s): sorted(v) for s, v in votes.items()},
                          "earliest_majority_step": primary, "source_kind": src_kind, "log_source": url, "is_correct": is_corr,
                          "step_indexing": "0-based index into reconstructed history (Who&When JSON history / MAST console-log turns)"}}
    final = None
    for h in reversed(hist):
        if "FINAL ANSWER" in (h["content"] or ""):
            final = h["content"]; break
    path, size = write_norm_example(SLUG, f"{split}/{fn}", q, gt, final, steps, ann_norm)
    out.append(f"\n\n## Example trajectory\n\nInstance `{split}/{fn}` (source: {src_kind}; log_source = {url}), {n} steps, {tc} characters, "
               f"{len({base_agent(h['role']) for h in hist if h['role']!='human'})} distinct agents, {len(anns)} annotators.\n")
    out.append(f"**Task:** {q}\n\n**Ground-truth answer:** {gt}\n")
    out.append(md_steps(steps, flagged))
    out.append("\n**Annotations (per annotator):**\n")
    for aid in sorted(anns):
        d = anns[aid]
        if not d["annotation"]:
            out.append(f"- Annotator {aid}: flagged no step.")
        for x in d["annotation"]:
            s = x["step"]
            out.append(f"- Annotator {aid}, step {s} ({base_agent(hist[int(s)]['role']) if str(s).isdigit() and int(s) < n else '?'}), category *{x.get('fail_category')}*: {x.get('fail_reason')}  \n  Ideal action: {x.get('ideal_action')}")
    out.append(f"\nStep votes: { {str(s): sorted(v) for s, v in sorted(votes.items())} }. Earliest majority-flagged step: {primary}.\n")
    out.append(f"\n(normalised example written to {path}, {size/1024:.1f} KB)\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
