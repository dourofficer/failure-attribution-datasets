"""Analyse MAST-Data (mcemri/MAST-Data). Usage:
python3 -I analyze_mast.py <MAD_full_dataset.json> <MAD_human_labelled_dataset.json> <notes_dir> <scratch_dir>
"""
import sys, os, json, re, ast, collections, itertools
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import *

full_path, human_path, notes_dir, scratch = sys.argv[1:5]
d = json.load(open(full_path))
h = json.load(open(human_path))

MODES = {"1.1": "Disobey task specification", "1.2": "Disobey role specification", "1.3": "Step repetition",
         "1.4": "Loss of conversation history", "1.5": "Unaware of termination conditions",
         "2.1": "Conversation reset", "2.2": "Fail to ask for clarification", "2.3": "Task derailment",
         "2.4": "Information withholding", "2.5": "Ignored other agent's input", "2.6": "Reasoning-action mismatch",
         "3.1": "Premature termination", "3.2": "No or incomplete verification", "3.3": "Incorrect verification"}
CAT = {"1": "FC1 Specification issues", "2": "FC2 Inter-agent misalignment", "3": "FC3 Task verification"}


# ---------------- heuristic step splitting per framework ----------------
def split_ag2(t):
    msgs = ast.literal_eval("[" + re.sub(r"\}\s+\{'content'", "}, {'content'", t) + "]")
    out = []
    for m in msgs:
        c = m.get("content")
        if isinstance(c, list):
            c = "\n".join(str(x) for x in c)
        out.append((m.get("name") or m.get("role"), str(c)))
    return out


def split_metagpt(t):
    out = []
    first = re.search(r"FROM: (\w+) TO: .*?\nACTION: .*?\nCONTENT:\n(.*?)\n-{20,}", t, re.S)
    if first:
        out.append((first.group(1), first.group(2)))
    for blk in re.split(r"\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\] NEW MESSAGES:\n", t)[1:]:
        blk = blk.strip()
        m = re.match(r"([A-Za-z_]+): ?(.*)", blk, re.S)
        if m:
            body = re.split(r"\n-{20,}", m.group(2))[0]
            out.append((m.group(1), body.strip()))
    return out


def split_chatdev(t):
    out = []
    pat = re.compile(r"^\[[^\]]+ INFO\] (?!System|HTTP|flask|\*\*)([^:\n]{2,40}): (.*?)(?=^\[[^\]]+ INFO\]|\Z)", re.M | re.S)
    for m in pat.finditer(t):
        out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def split_magentic(t):
    parts = re.split(r"^---------- (\S+) ----------$", t, flags=re.M)
    out = []
    for i in range(1, len(parts) - 1, 2):
        out.append((parts[i], parts[i + 1].strip()))
    return out


def split_openmanus(t):
    out = []
    for m in re.finditer(r"Executing step (\d+)/\d+\n(.*?)(?=Executing step \d+/\d+\n|\Z)", t, re.S):
        who = re.search(r"✨ (\w+)'s thoughts", m.group(2))
        out.append((who.group(1) if who else "Manus", m.group(2).strip()))
    return out


def split_appworld(t):
    out = []
    for m in re.finditer(r"^\s*Response from (\S+) Agent\n(.*?)(?=^\s*(?:Response from|Message to|Code Execution Output|Entering)|\Z)", t, re.M | re.S):
        out.append((m.group(1), m.group(2).strip()))
    return out


def split_hyperagent(t):
    out = []
    pat = re.compile(r"HyperAgent_\S+ - INFO - ((?:Planner|Navigator|Executor|Editor|Inner-\w+-Assistant)(?:'s Response|->\w+)?):?(.*?)(?=HyperAgent_\S+ - INFO - |\Z)", re.S)
    for m in pat.finditer(t):
        who = m.group(1).split("'")[0].split("->")[0]
        out.append((who, m.group(2).strip()))
    return out


SPLIT = {"AG2": split_ag2, "MetaGPT": split_metagpt, "ChatDev": split_chatdev, "Magentic": split_magentic,
         "OpenManus": split_openmanus, "AppWorld": split_appworld, "HyperAgent": split_hyperagent}

steps, agents, chars, parse_fail = [], [], [], collections.Counter()
per_mas_steps = collections.defaultdict(list)
per_mas_agents = collections.defaultdict(list)
agent_names = collections.defaultdict(collections.Counter)
parsed = {}
for r in d:
    t = r["trace"]["trajectory"]
    chars.append(len(t))
    try:
        msgs = SPLIT[r["mas_name"]](t)
    except Exception as e:
        parse_fail[r["mas_name"]] += 1
        msgs = []
    parsed[id(r)] = msgs
    n = len(msgs)
    a = {m[0] for m in msgs}
    steps.append(n)
    agents.append(len(a))
    per_mas_steps[r["mas_name"]].append(n)
    per_mas_agents[r["mas_name"]].append(len(a))
    for nm in a:
        agent_names[r["mas_name"]][nm] += 1

mode_counts = collections.Counter()
cat_counts = collections.Counter()
modes_per_trace = []
any_fail = 0
null_traces = 0
per_mas_modes = collections.defaultdict(collections.Counter)
per_mas_n = collections.Counter()
per_mas_anyfail = collections.Counter()
combo = collections.Counter()
for r in d:
    a = r["mast_annotation"]
    per_mas_n[r["mas_name"]] += 1
    if all(v is None for v in a.values()):
        null_traces += 1
        modes_per_trace.append(None)
        continue
    flagged = [k for k, v in a.items() if v == 1]
    modes_per_trace.append(len(flagged))
    for k in flagged:
        mode_counts[k] += 1
        per_mas_modes[r["mas_name"]][k] += 1
    for c in {k.split(".")[0] for k in flagged}:
        cat_counts[CAT[c]] += 1
    if flagged:
        any_fail += 1
        per_mas_anyfail[r["mas_name"]] += 1
    combo[tuple(sorted(flagged))] += 1

total_flags = sum(mode_counts.values())
mode_share = {k: round(100 * v / total_flags, 1) for k, v in mode_counts.items()}

mas = collections.Counter(r["mas_name"] for r in d)
llm = collections.Counter(r["llm_name"] for r in d)
bench = collections.Counter(r["benchmark_name"] for r in d)
triple = collections.Counter((r["mas_name"], r["benchmark_name"], r["llm_name"]) for r in d)

# ---------------- human-labelled set: agreement ----------------
human = {"n_traces": len(h), "rounds": {}}
for rnd, grp in itertools.groupby(sorted(h, key=lambda r: r["round"]), key=lambda r: r["round"]):
    grp = list(grp)
    n_modes = len(grp[0]["annotations"])
    # pairwise Cohen's kappa over trace x mode cells
    pairs = {}
    for a1, a2 in [("annotator_1", "annotator_2"), ("annotator_1", "annotator_3"), ("annotator_2", "annotator_3")]:
        x = [(ann[a1], ann[a2]) for r in grp for ann in r["annotations"] if a1 in ann and a2 in ann]
        n = len(x)
        po = sum(1 for p, q in x if p == q) / n
        p1 = sum(1 for p, _ in x if p) / n
        p2 = sum(1 for _, q in x if q) / n
        pe = p1 * p2 + (1 - p1) * (1 - p2)
        kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
        pairs[f"{a1}-{a2}"] = {"n_cells": n, "agreement": round(po, 3), "kappa": round(kappa, 3)}
    unanimous = sum(1 for r in grp for ann in r["annotations"] if len({ann.get(k) for k in ("annotator_1", "annotator_2", "annotator_3") if k in ann}) == 1)
    cells = sum(len(r["annotations"]) for r in grp)
    pos_rate = round(sum(1 for r in grp for ann in r["annotations"] for k in ("annotator_1", "annotator_2", "annotator_3") if ann.get(k)) / (3 * cells), 3)
    human["rounds"][rnd] = {"n_traces": len(grp), "n_modes_in_taxonomy": n_modes,
                            "traces": [(r["mas_name"], r["benchmark_name"], len(r["trace"])) for r in grp],
                            "pairwise": pairs, "unanimous_cells_frac": round(unanimous / cells, 3),
                            "positive_rate": pos_rate,
                            "mode_names": [ann["failure mode"].split("\n")[0] for ann in grp[0]["annotations"]]}

stats = {
    "n_trajectories": len(d),
    "steps_per_traj": steps,
    "steps_note": "HEURISTIC: traces are single log strings; steps = framework-specific regex split (messages/turns). 0 = parse failure.",
    "error_step_rel_pos": [],
    "agents_per_traj": agents,
    "faulty_agent_counts": {},
    "category_counts": {CAT[k.split(".")[0]] + " / FM-" + k + " " + MODES[k]: v for k, v in sorted(mode_counts.items())},
    "mode_counts": dict(sorted(mode_counts.items())),
    "mode_share_pct_of_all_flags": dict(sorted(mode_share.items())),
    "fc_counts_traces_with_any_mode_in_category": dict(cat_counts),
    "source_benchmark_counts": dict(bench.most_common()),
    "framework_counts": dict(mas.most_common()),
    "llm_counts": dict(llm.most_common()),
    "framework_benchmark_llm_counts": {" / ".join(k): v for k, v in sorted(triple.items())},
    "splits": {"train (MAD_full_dataset.json)": len(d), "human_labelled (MAD_human_labelled_dataset.json)": len(h)},
    "traces_with_any_failure_mode": any_fail,
    "traces_with_no_failure_mode": len(d) - any_fail - null_traces,
    "traces_with_null_annotation": null_traces,
    "modes_per_trace_desc": describe([m for m in modes_per_trace if m is not None]),
    "modes_per_trace_hist": dict(sorted(collections.Counter(m for m in modes_per_trace if m is not None).items())),
    "top_mode_combinations": {"+".join(k) if k else "(none)": v for k, v in combo.most_common(12)},
    "per_framework": {m: {"n": per_mas_n[m], "any_failure": per_mas_anyfail[m],
                          "any_failure_pct": round(100 * per_mas_anyfail[m] / per_mas_n[m], 1),
                          "mode_counts": dict(sorted(per_mas_modes[m].items())),
                          "steps_desc(heuristic)": describe([s for s in per_mas_steps[m] if s > 0]),
                          "agents_desc(heuristic)": describe([s for s in per_mas_agents[m] if s > 0]),
                          "agent_names": dict(agent_names[m].most_common(12)),
                          "parse_failures": parse_fail[m]} for m in mas},
    "chars_desc": describe(chars),
    "chars_hist": histogram(chars, [(0, 5000), (5001, 20000), (20001, 50000), (50001, 200000), (200001, 500000), (500001, None)]),
    "steps_desc(heuristic)": describe([s for s in steps if s > 0]),
    "steps_hist(heuristic)": histogram(steps, [(1, 5), (6, 10), (11, 20), (21, 40), (41, 80), (81, None)]),
    "agents_desc(heuristic)": describe([s for s in agents if s > 0]),
    "has_success_label": False,
    "human_labelled": human,
}
dump(stats, os.path.join(notes_dir, "mast_data_stats.json"))

# ---------------- example: short AG2 trace with 1-3 modes ----------------
cands = []
for r in d:
    if r["mas_name"] != "AG2":
        continue
    msgs = parsed[id(r)]
    flagged = [k for k, v in r["mast_annotation"].items() if v == 1]
    if not msgs or not (6 <= len(msgs) <= 15) or not (1 <= len(flagged) <= 3):
        continue
    cands.append((len(r["trace"]["trajectory"]), r, msgs, flagged))
cands.sort(key=lambda x: x[0])
# prefer GSM (math word problem) traces among the shortest
pick = next((c for c in cands if c[1]["benchmark_name"] == "GSM" and c[0] > 3000), cands[0])
L, ex, msgs, flagged = pick
print("example", ex["mas_name"], ex["benchmark_name"], ex["llm_name"], ex["trace_id"], L, len(msgs), flagged)
dump(ex, os.path.join(notes_dir, "mast_data_example.json"))
nsteps = []
for i, (who, c) in enumerate(msgs):
    txt, tr = trim_long(c)
    st = {"idx": i, "agent": who, "content": txt}
    if tr:
        st["trimmed"] = True
    nsteps.append(st)
task = msgs[0][1]
norm = {
    "dataset": "mast_data",
    "source_id": f"{ex['trace']['key']}#{ex['trace']['index']} (trace_id={ex['trace_id']})",
    "task": task,
    "ground_truth": None,
    "final_output": msgs[-1][1],
    "steps": nsteps,
    "annotation": {
        "faulty_agent": None,
        "faulty_step": None,
        "category": [f"FM-{k} {MODES[k]} ({CAT[k.split('.')[0]]})" for k in flagged],
        "reason": None,
        "extra": {"mast_annotation": ex["mast_annotation"], "mas_name": ex["mas_name"], "llm_name": ex["llm_name"],
                  "benchmark_name": ex["benchmark_name"], "annotator": "LLM judge (OpenAI o1, few-shot) — trace-level binary labels only",
                  "step_split": "heuristic: AG2 message list parsed with ast.literal_eval; agent = message `name`"},
    },
}
dump(norm, os.path.join(notes_dir, "mast_data_example_norm.json"))
with open(os.path.join(scratch, "mast_data_example.md"), "w") as f:
    f.write(render_example_md(norm))
print(json.dumps({k: v for k, v in stats.items() if not isinstance(v, list)}, indent=1, default=str))
