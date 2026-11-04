"""Loader for *Failure as a Process* (Zhao et al. 2026, arXiv 2607.09510; repo cli_trajectory_analysis).

Source files (all under data/failure_as_process/repo_cli_trajectory_analysis/data/):
  traj_data_v2_all89tasks.json  1,794 annotation records (1,184 FAIL, 610 PASS); case_id = <task>__<scaffold>__<model>
  merged_tasks.json             89 Terminal-Bench tasks: category, difficulty, task_type, core_requirements_summary, refs
  pass_obs_input.json           433 PASS runs: a 2-3 step "context" excerpt (command + output) around the first error step
  pass_error_observability.json 433 PASS runs: LLM label observable/silent for that first error

The release ships NO raw trajectories.  One trajectory is yielded per annotation record with steps = [] except for the
433 PASS runs that have an excerpt in pass_obs_input.json.  There the excerpt is parsed into native steps
("  step N  $ <command>\n            <output>"); each native step (one agent turn = command + output) becomes TWO
schema steps sharing native_idx = N (the dataset's 1-based turn number): role 'agent' = the command, role 'env' = the
output.  Commands/outputs that the release itself truncated (trailing '…') get meta.trimmed = True.  Steps outside the
excerpt are NOT materialised, so for those trajectories len(steps) != 2*m; the full length is annotation.extra['m'].

Label mapping
  outcome      1 for PASS (no t_commit field), 0 for FAIL (has t_commit).
  faulty_step  always None (no steps to point at).  The native decisive-error step t_err (1-based turn) is kept in
               annotation.extra['t_err'] together with t_commit (= t_lock), t_surface (= t_obs; None = silent failure),
               their evidence quotes, timepoint_confidence, trigger_mechanism(_other) + explanation, primary/contributing
               failure layer/category/subtype, root_cause_label, one_sentence_failure_summary, forewarning_*, awareness,
               first_awareness_step, num_recovery_attempts, tail_dominant_behavior, fabrication_*, verification_*,
               action_segments ([start, end, code] runs, codes E/P/W/X/V/C/R/O), m, long_traj, uncertain_fields.
  category     FAIL: trigger_mechanism (9-way controlled vocabulary; 'other' -> extra['trigger_mechanism_other']).  PASS: None.
  reason       FAIL: trigger_explanation.  PASS: None (one_sentence_strategy_summary is in extra).
  faulty_agent None (single-agent CLI coding runs; the agent is always the one coding agent).
  PASS extra   num_error_events, first_error_step/_evidence, num_recoveries, max_detour_length, near_miss(+description,
               evidence), verification_before_claim, first_relevant_verification_step, verification_evidence,
               suspicious_pass(+type, evidence), solution_directness, one_sentence_strategy_summary, confidence,
               action_segments, m, long_traj, uncertain_fields; plus first_error_observability (observable/silent) and
               excerpt_steps for the 433 runs with an excerpt.
  subset       scaffold (miniswe / openhands / terminus2).  system = scaffold's full name; model in meta.
  task         Terminal-Bench task id + category/difficulty + core_requirements_summary (task.yaml is not redistributed).
  ground_truth solution_ref URL (hidden test suite; Terminal-Bench tests decide PASS/FAIL).
Order: file order of traj_data_v2_all89tasks.json (sorted by case_id in the release).
"""
import json
import os
import re

SLUG = "failure_as_process"
ROOT = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/failure_as_process/repo_cli_trajectory_analysis/data"
SCAFFOLD_NAMES = {"miniswe": "mini-SWE-agent", "openhands": "OpenHands", "terminus2": "Terminus 2"}
MODEL_NAMES = {"claude": "Claude Sonnet 4", "gpt5": "GPT-5", "gemini": "Gemini 2.5 Pro", "qwen": "Qwen3-Coder-480B",
               "deepseek-v3.2": "DeepSeek-V3.2", "kimi": "Kimi-K2-Instruct", "devstral": "Devstral 2"}
ACTION_CODES = {"E": "explore/read", "P": "planning", "W": "write/edit", "X": "execute/run", "V": "verify/test",
                "C": "completion claim", "R": "recover/retry", "O": "other"}
_STEP_RE = re.compile(r"^  step (\d+)  \$ ", re.M)
_OUT_INDENT = "            "


def _parse_excerpt(ctx):
    """'  step N  $ cmd\\n            output...' -> [(N, cmd, output)]."""
    ms = list(_STEP_RE.finditer(ctx))
    out = []
    for i, m in enumerate(ms):
        seg = ctx[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(ctx)]
        cmd, _, rest = seg.partition("\n")
        if rest.startswith(_OUT_INDENT):
            rest = rest[len(_OUT_INDENT):]
        out.append((int(m.group(1)), cmd.rstrip("\n"), rest.rstrip("\n")))
    return out


def _excerpt_steps(ctx, scaffold):
    steps = []
    for n, cmd, outp in _parse_excerpt(ctx):
        steps.append({"idx": len(steps), "native_idx": n, "agent": "coding agent", "role": "agent",
                      "content": "$ " + cmd,
                      "meta": {"kind": "command", "excerpt": True, "trimmed": cmd.endswith("…"), "scaffold": scaffold}})
        steps.append({"idx": len(steps), "native_idx": n, "agent": "terminal", "role": "env",
                      "content": outp,
                      "meta": {"kind": "output", "excerpt": True, "trimmed": outp.endswith("…"), "scaffold": scaffold}})
    return steps


def _task_text(task_id, t):
    if not t:
        return f"Terminal-Bench task `{task_id}`"
    head = f"Terminal-Bench task `{task_id}` ({t.get('category')}, {t.get('difficulty')}"
    if t.get("task_type"):
        head += f", {t['task_type']}"
    head += ")"
    reqs = t.get("core_requirements_summary") or []
    return head + (": " + "; ".join(reqs) if reqs else "")


def load(limit=None, subset=None):
    recs = json.load(open(os.path.join(ROOT, "traj_data_v2_all89tasks.json"), encoding="utf-8"))
    tasks = {t["task_id"]: t for t in json.load(open(os.path.join(ROOT, "merged_tasks.json"), encoding="utf-8"))}
    excerpts = {p["case_id"]: p for p in json.load(open(os.path.join(ROOT, "pass_obs_input.json"), encoding="utf-8"))}
    observ = json.load(open(os.path.join(ROOT, "pass_error_observability.json"), encoding="utf-8"))
    n = 0
    for r in recs:
        task_id, scaffold, model = r["case_id"].split("__")
        if subset is not None and scaffold != subset:
            continue
        t = tasks.get(task_id, {})
        is_fail = "t_commit" in r
        extra = {k: v for k, v in r.items() if k not in ("case_id", "schema_version")}
        extra["step_indexing"] = "1-based agent turns (thought + command + output); m = total turns"
        extra["action_code_legend"] = ACTION_CODES
        steps = []
        if is_fail:
            extra["t_lock"] = r["t_commit"]
            extra["t_obs"] = r.get("t_surface")
            extra["silent_failure"] = r.get("t_surface") is None
            extra["fix_window"] = r["t_commit"] - r["t_err"]
            if r.get("t_surface") is not None:
                extra["observability_lag"] = r["t_surface"] - r["t_commit"]
            category = r.get("trigger_mechanism")
            reason = r.get("trigger_explanation")
        else:
            category = None
            reason = None
            ex = excerpts.get(r["case_id"])
            if ex is not None:
                steps = _excerpt_steps(ex["context"], scaffold)
                extra["excerpt_steps"] = sorted({s["native_idx"] for s in steps})
                extra["excerpt_first_error_step"] = ex.get("first_error_step")
                lab = observ.get(r["case_id"]) or {}
                extra["first_error_observability"] = lab.get("label")
                extra["first_error_observability_why"] = lab.get("why")
        yield {
            "dataset": SLUG,
            "id": r["case_id"],
            "subset": scaffold,
            "system": SCAFFOLD_NAMES.get(scaffold, scaffold),
            "task": _task_text(task_id, t),
            "ground_truth": t.get("solution_ref"),
            "final_output": None,
            "outcome": 0 if is_fail else 1,
            "steps": steps,
            "annotation": {"faulty_step": None, "faulty_steps": [], "faulty_agent": None,
                           "category": category, "reason": reason, "extra": extra},
            "meta": {"task": task_id, "scaffold": scaffold, "model": model, "model_name": MODEL_NAMES.get(model, model),
                     "difficulty": t.get("difficulty"), "task_category": t.get("category"), "task_type": t.get("task_type"),
                     "core_requirements_summary": t.get("core_requirements_summary"),
                     "raw_task_ref": t.get("raw_task_ref"), "solution_ref": t.get("solution_ref"),
                     "m": r.get("m"), "schema_version": r.get("schema_version"), "has_excerpt": bool(steps),
                     "raw_trajectory_released": False, "benchmark": "Terminal-Bench",
                     "source_file": os.path.join(ROOT, "traj_data_v2_all89tasks.json")},
        }
        n += 1
        if limit is not None and n >= limit:
            return
