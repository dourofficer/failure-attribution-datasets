"""Analyse AgentHallu (arXiv 2601.06818). Usage: python3 -I analyze_agenthallu.py <data_root> <notes_dir>"""
import json, os, sys, glob, statistics, collections

root, notes = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(root, "*", "*.json")))
recs = []
for f in files:
    with open(f, encoding="utf-8") as fh:
        d = json.load(fh)
    d["_file"] = os.path.relpath(f, root)
    d["_framework_dir"] = f.split(os.sep)[-2]
    recs.append(d)

def steps_of(d):
    return d.get("history", [])

def step_chars(s):
    n = len(str(s.get("content", "")))
    for k in ("tool_calls", "tool_responses"):
        v = s.get(k)
        if v:
            n += len(json.dumps(v, ensure_ascii=False))
    return n

def is_hall(d):
    v = d.get("is_hallucination")
    return str(v).lower() == "true"

n = len(recs)
hall = [d for d in recs if is_hall(d)]
nonhall = [d for d in recs if not is_hall(d)]
steps_per = [len(steps_of(d)) for d in recs]
chars_per = [sum(step_chars(s) for s in steps_of(d)) for d in recs]
roles = collections.Counter()
roles_per_traj = []
for d in recs:
    rs = set(s.get("role", "?") for s in steps_of(d))
    roles_per_traj.append(len(rs))
    roles.update(rs)

# error step relative position (hallucinated only)
rel, abs_pos = [], []
bad_step_fmt = 0
for d in hall:
    hs = d.get("hallucination_step")
    L = len(steps_of(d))
    try:
        hs_i = int(hs)
    except Exception:
        bad_step_fmt += 1
        continue
    if L > 0:
        rel.append(hs_i / L)
        abs_pos.append(hs_i)

cat = collections.Counter(d.get("hallucination_category") for d in hall)
subcat = collections.Counter((d.get("hallucination_category"), d.get("hallucination_subcategory")) for d in hall)
fw = collections.Counter(d["_framework_dir"] for d in recs)
fw_hall = collections.Counter(d["_framework_dir"] for d in hall)
agent_type = collections.Counter(d.get("agent_type") for d in recs)
model = collections.Counter(d.get("model_id") for d in recs)
src = collections.Counter(d.get("question_source") for d in recs)
dom = collections.Counter(d.get("question_domain") for d in recs)
src_hall = collections.Counter(d.get("question_source") for d in hall)
faulty_role = collections.Counter()
for d in hall:
    try:
        hs_i = int(d.get("hallucination_step"))
    except Exception:
        continue
    for s in steps_of(d):
        if s.get("step") == hs_i:
            faulty_role[s.get("role", "?")] += 1
            break

def hist(xs, edges):
    out = collections.OrderedDict()
    for lo, hi in zip(edges[:-1], edges[1:]):
        out[f"{lo}-{hi-1}"] = sum(1 for x in xs if lo <= x < hi)
    out[f">={edges[-1]}"] = sum(1 for x in xs if x >= edges[-1])
    return out

def q(xs):
    xs = sorted(xs)
    return dict(mean=round(statistics.mean(xs), 2), median=statistics.median(xs), min=xs[0], max=xs[-1])

# keys of a record
keys = collections.Counter()
step_keys = collections.Counter()
for d in recs:
    keys.update(k for k in d if not k.startswith("_"))
    for s in steps_of(d):
        step_keys.update(s.keys())

summary = {
    "n_trajectories": n,
    "n_hallucinated": len(hall),
    "n_non_hallucinated": len(nonhall),
    "steps_stats_all": q(steps_per),
    "steps_stats_hall": q([len(steps_of(d)) for d in hall]),
    "steps_hist": hist(steps_per, [1, 3, 6, 11, 16, 21, 31]),
    "chars_stats": q(chars_per),
    "error_step_abs_stats": q(abs_pos),
    "error_step_rel_stats": q(rel),
    "error_step_rel_hist": hist([int(r * 10) for r in rel], list(range(0, 11))),
    "bad_step_format": bad_step_fmt,
    "roles_per_traj": q(roles_per_traj),
    "role_counts": dict(roles.most_common()),
    "faulty_role_counts": dict(faulty_role.most_common()),
    "category_counts": dict(cat.most_common()),
    "subcategory_counts": {f"{c} / {s}": v for (c, s), v in subcat.most_common()},
    "framework_counts": dict(fw.most_common()),
    "framework_hall_counts": dict(fw_hall.most_common()),
    "agent_type_counts": dict(agent_type.most_common()),
    "model_counts": dict(model.most_common()),
    "source_counts": dict(src.most_common()),
    "source_hall_counts": dict(src_hall.most_common()),
    "domain_counts": dict(dom.most_common()),
    "record_keys": dict(keys),
    "step_keys": dict(step_keys),
}
print(json.dumps(summary, indent=1, ensure_ascii=False))

stats = {
    "n_trajectories": n,
    "steps_per_traj": steps_per,
    "error_step_rel_pos": rel,
    "agents_per_traj": roles_per_traj,
    "faulty_agent_counts": dict(faulty_role),
    "category_counts": dict(cat),
    "subcategory_counts": {f"{c} / {s}": v for (c, s), v in subcat.items()},
    "source_benchmark_counts": dict(src),
    "framework_counts": dict(fw),
    "model_counts": dict(model),
    "splits": {"all": n, "hallucinated": len(hall), "non_hallucinated": len(nonhall), **{f"framework/{k}": v for k, v in fw.items()}},
    "chars_per_traj": chars_per,
    "summary": summary,
}
with open(os.path.join(notes, "agenthallu_stats.json"), "w") as fh:
    json.dump(stats, fh, indent=1, ensure_ascii=False)

# ---- choose example: hallucinated, multi-role if possible, <=15 steps, avg chars <= 2500, prefer tool use & mid-trajectory error
cands = []
for d in hall:
    L = len(steps_of(d))
    if L < 4 or L > 12:
        continue
    avg = sum(step_chars(s) for s in steps_of(d)) / L
    if avg > 1800:
        continue
    try:
        hs_i = int(d.get("hallucination_step"))
    except Exception:
        continue
    nroles = len(set(s.get("role") for s in steps_of(d)))
    score = (nroles >= 2, 1 < hs_i < L, -abs(avg - 700))
    cands.append((score, d))
cands.sort(key=lambda t: t[0], reverse=True)
print("\nTOP CANDIDATES:")
for sc, d in cands[:15]:
    print(sc, d["_file"], d["_framework_dir"], len(steps_of(d)), d.get("hallucination_step"), d.get("hallucination_category"), d.get("question_source"))
