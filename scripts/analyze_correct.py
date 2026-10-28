"""Analyse CORRECT-Error (yifanyu/CORRECT-Error). Usage:
python3 -I analyze_correct.py <parquet> <notes_dir> <scratch_dir>
"""
import sys, os, site, json, collections, re
sys.path.append(site.getusersitepackages())
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from common import *

parquet, notes_dir, scratch = sys.argv[1:4]
df = pd.read_parquet(parquet)
n = len(df)


def norm_agent(a):
    a = (a or "").strip()
    a = a.strip("[]").strip()
    return a


steps = [len(h) for h in df.history]
agents = [len({m["role"] for m in h if m["role"] != "user"}) for h in df.history]
agents_incl_user = [len({m["role"] for m in h}) for h in df.history]
chars = [sum(len(m["content"]) for m in h) for h in df.history]
rel = [(int(s) / (L - 1)) if L > 1 else 0.0 for s, L in zip(df.mistake_step, steps)]
faulty = collections.Counter(norm_agent(a) for a in df.mistake_agent)
faulty_raw = collections.Counter(df.mistake_agent)
bench = collections.Counter(df.dataset)
gen = collections.Counter(df.generator_model)
bench_gen = collections.Counter(zip(df.dataset, df.generator_model))
role_msgs = collections.Counter(m["role"] for h in df.history for m in h)

# alignment of mistake_step with history index (0-based incl. user msg at idx 0)
align0 = sum(1 for s, h, a in zip(df.mistake_step, df.history, df.mistake_agent)
             if s < len(h) and norm_agent(h[s]["role"]) == norm_agent(a))
unknown0 = sum(1 for s, a in zip(df.mistake_step, df.mistake_agent) if s == 0)
step0_agents = collections.Counter(norm_agent(a) for s, a in zip(df.mistake_step, df.mistake_agent) if s == 0)
reason_nonempty = int((df.mistake_reason.fillna("") != "").sum())
gt_nonempty = int((df.groundtruth.fillna("") != "").sum())
qid_dups = int(df.duplicated(subset=["dataset", "question_id"]).sum())
# base question id (before _k suffix) -> how many injected variants per source question
base = df.question_id.str.replace(r"_\d+$", "", regex=True)
variants = collections.Counter(zip(df.dataset, df.generator_model, base))
var_desc = describe(list(variants.values()))

# per-benchmark step stats
per_bench = {}
for b in sorted(bench):
    sub = df[df.dataset == b]
    L = [len(h) for h in sub.history]
    per_bench[b] = {"n": len(sub), "steps": describe(L),
                    "chars": describe([sum(len(m["content"]) for m in h) for h in sub.history]),
                    "rel_pos_mean": round(sum((s / (l - 1)) if l > 1 else 0 for s, l in zip(sub.mistake_step, L)) / len(sub), 3),
                    "faulty": dict(collections.Counter(norm_agent(a) for a in sub.mistake_agent).most_common(4))}
per_gen = {}
for g in sorted(gen):
    sub = df[df.generator_model == g]
    per_gen[g] = {"n": len(sub), "steps": describe([len(h) for h in sub.history]),
                  "mistake_step": describe([int(x) for x in sub.mistake_step])}

stats = {
    "n_trajectories": n,
    "steps_per_traj": steps,
    "error_step_rel_pos": [round(x, 4) for x in rel],
    "agents_per_traj": agents,
    "faulty_agent_counts": dict(faulty.most_common()),
    "faulty_agent_counts_raw": dict(faulty_raw.most_common()),
    "category_counts": {},
    "source_benchmark_counts": dict(bench.most_common()),
    "framework_counts": {"Magentic-One variant (AutoGen selector-group-chat; agents Planner/WebSurfer/Coder/CodeExecutor/FileSurfer)": n},
    "generator_model_counts": dict(gen.most_common()),
    "splits": {"test": n, **{f"test/{b}/{g}": c for (b, g), c in sorted(bench_gen.items())}},
    "all_failed": True,
    "steps_desc": describe(steps),
    "steps_hist": histogram(steps, [(2, 4), (5, 8), (9, 12), (13, 16), (17, 20), (21, 22)]),
    "agents_desc_excl_user": describe(agents),
    "agents_desc_incl_user": describe(agents_incl_user),
    "chars_desc": describe(chars),
    "mistake_step_desc": describe([int(x) for x in df.mistake_step]),
    "rel_pos_desc": describe(rel),
    "rel_pos_hist": histogram(rel, [(0.0, 0.2), (0.2001, 0.4), (0.4001, 0.6), (0.6001, 0.8), (0.8001, 1.0)]),
    "messages_per_role": dict(role_msgs.most_common()),
    "mistake_step_matches_history_role_0based": align0,
    "mistake_step_eq_0": unknown0,
    "mistake_step_eq_0_agents": dict(step0_agents),
    "mistake_reason_nonempty": reason_nonempty,
    "groundtruth_nonempty": gt_nonempty,
    "dup_dataset_question_id": qid_dups,
    "injected_variants_per_source_question": var_desc,
    "n_source_questions": len(variants),
    "per_benchmark": per_bench,
    "per_generator": per_gen,
}
dump(stats, os.path.join(notes_dir, "correct_error_stats.json"))

# ---- choose example: short, multi-agent, non-Planner fault in the middle, GAIA preferred
cand = df.copy()
cand["L"] = steps
cand["avg"] = [c / l for c, l in zip(chars, steps)]
cand["fa"] = [norm_agent(a) for a in cand.mistake_agent]
sel = cand[(cand.L.between(6, 10)) & (cand.fa == "WebSurfer") & (cand.mistake_step >= 2)
           & (cand.mistake_step <= cand.L - 2) & (cand.avg <= 2500)]
sel = sel.sort_values(["dataset", "avg"], key=lambda s: s.map({"gaia": 0}).fillna(1) if s.name == "dataset" else s)
print("candidates", len(sel))
print(sel[["trajectory_id", "L", "avg", "mistake_step"]].head(10).to_string())
ex = sel.iloc[0]
raw = {k: (ex[k] if k not in ("L", "avg", "fa") else None) for k in df.columns}
raw["history"] = [dict(m) for m in ex.history]
raw["gaia_level"] = None if pd.isna(raw["gaia_level"]) else raw["gaia_level"]
dump(raw, os.path.join(notes_dir, "correct_error_example.json"))

nsteps = []
for i, m in enumerate(ex.history):
    txt, trimmed = trim_long(m["content"])
    st = {"idx": i, "agent": m["role"], "content": txt}
    if trimmed:
        st["trimmed"] = True
    nsteps.append(st)
norm = {
    "dataset": "correct_error",
    "source_id": ex.trajectory_id,
    "task": ex.question,
    "ground_truth": ex.groundtruth if ex.groundtruth else None,
    "final_output": ex.history[-1]["content"],
    "steps": nsteps,
    "annotation": {
        "faulty_agent": ex.mistake_agent,
        "faulty_step": int(ex.mistake_step),
        "category": None,
        "reason": ex.mistake_reason if ex.mistake_reason else None,
        "extra": {"dataset": ex.dataset, "generator_model": ex.generator_model,
                  "question_id": ex.question_id, "is_corrected": bool(ex.is_corrected), "level": int(ex.level),
                  "step_indexing": "0-based index into `history`, where index 0 is the user task message"},
    },
}
dump(norm, os.path.join(notes_dir, "correct_error_example_norm.json"))
with open(os.path.join(scratch, "correct_error_example.md"), "w") as f:
    f.write(render_example_md(norm))
print(json.dumps({k: v for k, v in stats.items() if not isinstance(v, list)}, indent=1, default=str))
