"""Analyse HORIZON (xwang2775/long-horizon-agent-failures). Usage: python3 -I analyze_horizon.py <hf_root> <notes_dir> [example_id]"""
import json, os, sys, re, statistics, collections

root, notes = sys.argv[1], sys.argv[2]
example_id = sys.argv[3] if len(sys.argv) > 3 else None
CATS = ["Environment", "Instruction", "Catastrophic Forgetting", "False Assumption", "Planning Error", "History Error Accumulation", "Memory Limitation"]

def load(r):
    with open(os.path.join(root, r, "classified_results.json"), encoding="utf-8") as fh:
        return json.load(fh)

def n_steps(rec):
    t = rec["trajectory"]
    d = rec["domain"]
    if d == "web":
        return len(re.findall(r"^\[Step \d+\]", t, re.M))
    if d == "os":
        return len(re.findall(r"^\[Agent\]", t, re.M))
    if d == "embodied":
        m = re.search(r"Primitive plan \((\d+) steps?\)", t)
        return int(m.group(1)) if m else len([l for l in t.splitlines() if l.startswith("  ")])
    if d == "database":
        return 1
    return 0

def n_agent_turns_os(t):
    return len(re.findall(r"^\[Agent\]", t, re.M))

def succ(rec):
    return rec["failure_type"] == "Success"

def outcome(rec):
    if rec.get("passed") is not None:
        return bool(rec["passed"])
    if rec.get("score") is not None:
        return rec["score"] >= 1.0
    return None

def q(xs):
    xs = sorted(xs)
    if not xs:
        return {}
    return dict(mean=round(statistics.mean(xs), 2), median=statistics.median(xs), min=xs[0], max=xs[-1],
                p25=xs[len(xs) // 4], p75=xs[3 * len(xs) // 4], p90=xs[int(len(xs) * 0.9)])

def hist(xs, edges):
    out = collections.OrderedDict()
    for lo, hi in zip(edges[:-1], edges[1:]):
        out[f"{lo}-{hi-1}"] = sum(1 for x in xs if lo <= x < hi)
    out[f">={edges[-1]}"] = sum(1 for x in xs if x >= edges[-1])
    return out

R = {r: load(r) for r in ["result_1", "result_2", "result_3", "result_5"]}
main = R["result_2"]
by_id3 = {x["id"]: x for x in R["result_3"]}
summary = {}
summary["files"] = {r: dict(n=len(v), keys=sorted(set(k for x in v for k in x))) for r, v in R.items()}
summary["main_file"] = "result_2/classified_results.json"
summary["n_trajectories"] = len(main)
summary["domain_model_counts"] = {f"{d}/{m}": c for (d, m), c in sorted(collections.Counter((x["domain"], x["model"]) for x in main).items())}
summary["domain_counts"] = dict(collections.Counter(x["domain"] for x in main))
summary["model_counts"] = dict(collections.Counter(x["model"] for x in main))
summary["run_counts"] = dict(collections.Counter(str(x.get("run")) for x in main))
summary["judge_success_vs_failure"] = dict(collections.Counter("Success" if succ(x) else "Failure" for x in main))
summary["judge_success_vs_failure_by_domain"] = {d: dict(collections.Counter("Success" if succ(x) else "Failure" for x in main if x["domain"] == d)) for d in sorted(set(x["domain"] for x in main))}
summary["judge_success_vs_failure_by_model"] = {m: dict(collections.Counter("Success" if succ(x) else "Failure" for x in main if x["model"] == m)) for m in ["gpt", "claude"]}
oc = collections.Counter()
mismatch = collections.Counter()
for x in main:
    o = outcome(x)
    oc[str(o)] += 1
    if o is not None:
        mismatch[(o, succ(x))] += 1
summary["env_outcome_counts(passed/score)"] = dict(oc)
summary["env_outcome_vs_judge_label"] = {f"env_pass={a},judge_success={b}": c for (a, b), c in mismatch.items()}
fails = [x for x in main if not succ(x)]
summary["failure_type_counts"] = dict(collections.Counter(x["failure_type"] for x in fails))
summary["failure_type_by_domain"] = {d: dict(collections.Counter(x["failure_type"] for x in fails if x["domain"] == d)) for d in sorted(set(x["domain"] for x in fails))}
summary["failure_type_by_model"] = {m: dict(collections.Counter(x["failure_type"] for x in fails if x["model"] == m)) for m in ["gpt", "claude"]}
steps = {x["id"]: n_steps(x) for x in main}
summary["steps_per_traj_all"] = q(list(steps.values()))
summary["steps_per_traj_by_domain"] = {d: q([steps[x["id"]] for x in main if x["domain"] == d]) for d in sorted(set(x["domain"] for x in main))}
summary["steps_hist_all"] = hist(list(steps.values()), [0, 1, 3, 6, 11, 16, 21, 31, 51])
summary["steps_hist_by_domain"] = {d: hist([steps[x["id"]] for x in main if x["domain"] == d], [0, 1, 3, 6, 11, 16, 21, 31, 51]) for d in sorted(set(x["domain"] for x in main))}
chars = {x["id"]: len(x["trajectory"]) for x in main}
summary["chars_per_traj_all"] = q(list(chars.values()))
summary["chars_per_traj_by_domain"] = {d: q([chars[x["id"]] for x in main if x["domain"] == d]) for d in sorted(set(x["domain"] for x in main))}
summary["reason_len"] = q([len(x["reason"]) for x in fails])
# agreement result_2 vs result_3 (two judge passes over the same 3782 ids)
agree = sum(1 for x in main if by_id3[x["id"]]["failure_type"] == x["failure_type"])
agree_bin = sum(1 for x in main if succ(by_id3[x["id"]]) == succ(x))
both_fail = [x for x in main if not succ(x) and not succ(by_id3[x["id"]])]
agree_cat = sum(1 for x in both_fail if by_id3[x["id"]]["failure_type"] == x["failure_type"])
summary["judge_consistency_result2_vs_result3"] = dict(n=len(main), exact_label_agreement=round(agree / len(main), 4), success_failure_agreement=round(agree_bin / len(main), 4),
                                                       category_agreement_given_both_failed=round(agree_cat / max(1, len(both_fail)), 4), n_both_failed=len(both_fail))
conf = collections.Counter((x["failure_type"], by_id3[x["id"]]["failure_type"]) for x in main)
summary["confusion_result2_vs_result3_top"] = [dict(r2=a, r3=b, n=c) for (a, b), c in conf.most_common(15)]
# result_5: step-level labels for web/gpt
r5 = R["result_5"]
r5f = [x for x in r5 if not succ(x)]
r5_steps = {x["id"]: n_steps(x) for x in r5}
rel = []
for x in r5f:
    fs = x.get("failure_step_number")
    n = r5_steps[x["id"]]
    if isinstance(fs, int) and n > 0:
        rel.append(min(fs, n) / n)
summary["result_5_step_level"] = dict(n=len(r5), n_failed=len(r5f), n_with_failure_step=sum(1 for x in r5f if isinstance(x.get("failure_step_number"), int)),
                                      failure_type_counts=dict(collections.Counter(x["failure_type"] for x in r5f)),
                                      score_counts=dict(collections.Counter(x["score"] for x in r5)),
                                      steps_per_traj=q(list(r5_steps.values())), failure_step_abs=q([x["failure_step_number"] for x in r5f if isinstance(x.get("failure_step_number"), int)]),
                                      failure_step_rel=q(rel), failure_step_rel_hist=hist([int(r * 10) for r in rel], list(range(0, 11))),
                                      n_failure_step_gt_nsteps=sum(1 for x in r5f if isinstance(x.get("failure_step_number"), int) and x["failure_step_number"] > r5_steps[x["id"]]),
                                      judge_failure_but_score1=sum(1 for x in r5f if x["score"] == 1.0))
# result_1
r1 = R["result_1"]
summary["result_1"] = dict(n=len(r1), domain_model=dict(collections.Counter(f'{x["domain"]}/{x["model"]}' for x in r1)), failure_type_counts=dict(collections.Counter(x["failure_type"] for x in r1)),
                           existing_category=dict(collections.Counter(str(x.get("existing_category")) for x in r1)))
print(json.dumps(summary, indent=1, ensure_ascii=False))

stats = dict(
    n_trajectories=len(main), n_failed=len(fails),
    steps_per_traj=[steps[x["id"]] for x in main],
    steps_per_traj_failed=[steps[x["id"]] for x in fails],
    error_step_rel_pos=rel,
    agents_per_traj=[1] * len(main),
    faulty_agent_counts={"single agent": len(fails)},
    category_counts=dict(collections.Counter(x["failure_type"] for x in fails)),
    source_benchmark_counts={"web (WebArena)": summary["domain_counts"].get("web", 0), "os (AgentBench OS)": summary["domain_counts"].get("os", 0),
                             "database (MAC-SQL / BIRD)": summary["domain_counts"].get("database", 0), "embodied (IsaacSim bimanual)": summary["domain_counts"].get("embodied", 0)},
    model_counts=summary["model_counts"],
    splits={**{f"result_2/{k}": v for k, v in summary["domain_model_counts"].items()}, "result_5 (web/gpt, step-level)": len(r5), "result_1 (older subset)": len(r1), "result_3 (2nd judge pass)": len(R["result_3"])},
    chars_per_traj=[chars[x["id"]] for x in main],
    summary=summary,
)
with open(os.path.join(notes, "horizon_stats.json"), "w") as fh:
    json.dump(stats, fh, indent=1, ensure_ascii=False)

# ---- example from result_5 (web, step-level label)
if example_id:
    x = next(r for r in r5 if r["id"] == example_id)
    with open(os.path.join(notes, "horizon_example.json"), "w", encoding="utf-8") as fh:
        json.dump(x, fh, indent=1, ensure_ascii=False)
    t = x["trajectory"]
    head, *parts = re.split(r"^\[Step (\d+)\]\n", t, flags=re.M)
    task = re.search(r"^Task: (.*)$", head, re.M).group(1)
    exp = re.search(r"^Expected answer: (.*)$", head, re.M)
    steps_n = []
    for i in range(0, len(parts), 2):
        idx = int(parts[i]); body = parts[i + 1].strip()
        page = re.search(r"^Page\s*:\s*(.*)$", body, re.M)
        agent = re.search(r"^Agent:\s*(.*?)(?=^Action:|\Z)", body, re.M | re.S)
        action = re.search(r"^Action:\s*(.*)$", body, re.M | re.S)
        content = ""
        if page: content += "Observation: " + page.group(1).strip() + "\n"
        if agent: content += "Thought: " + agent.group(1).strip() + "\n"
        if action: content += "Action: " + action.group(1).strip()
        steps_n.append(dict(idx=idx, agent=f"web agent ({'gpt-5-mini' if x['model']=='gpt' else 'claude-4-sonnet'})", content=content.strip() or body))
    final = None
    m = re.search(r"stop \[(.*?)\]", t)
    if m: final = m.group(1)
    norm = dict(dataset="horizon", source_id=x["id"], task=task, ground_truth=exp.group(1) if exp else None, final_output=final, steps=steps_n,
                annotation=dict(faulty_agent="web agent (single-agent)", faulty_step=x.get("failure_step_number"), category=x["failure_type"], reason=x["reason"],
                                extra=dict(domain=x["domain"], model=x["model"], run=x["run"], task_id=x["task_id"], score=x["score"], judge="LLM-as-a-Judge (trajectory-grounded), not human",
                                           judge_step_window_summaries=x.get("steps"))))
    with open(os.path.join(notes, "horizon_example_norm.json"), "w", encoding="utf-8") as fh:
        json.dump(norm, fh, indent=1, ensure_ascii=False)
    print("example written", example_id, "steps", len(steps_n))
else:
    print("\nCANDIDATES (result_5, failed, score 0, 6-15 steps):")
    c = [x for x in r5f if x["score"] == 0.0 and isinstance(x.get("failure_step_number"), int) and 6 <= r5_steps[x["id"]] <= 15 and x["failure_step_number"] <= r5_steps[x["id"]]]
    c.sort(key=lambda x: (x["failure_type"] == "Planning Error", abs(r5_steps[x["id"]] - 10)))
    for x in c[:20]:
        print(x["id"], x["failure_type"], "nsteps", r5_steps[x["id"]], "fail_step", x["failure_step_number"], "chars", len(x["trajectory"]), "|", x["trajectory"][:90].replace("\n", " "))
