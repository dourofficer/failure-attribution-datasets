"""HORIZON (xwang2775/long-horizon-agent-failures) loader.  ALL LABELS ARE LLM-JUDGE LABELS, not human.

Files (data/horizon/hf/):
  result_2/classified_results.json  3,782 judge-labelled records: id, domain (web/os/database/embodied),
                                    model (gpt = GPT-5-mini, claude = Claude-4-Sonnet), run (level), passed or
                                    score (environment verdict; absent for the 270 embodied records),
                                    trajectory (domain-specific text), failure_type, reason.  <- main set
  result_5/classified_results.json  371 web / GPT-5-mini records with failure_step_number (int or null) and
                                    `steps` (judge window over the last <=5 steps). 147 ids are also in
                                    result_2 (identical trajectory text; 22 of them get a different judge
                                    failure_type); the other 224 (levels 5_mini_step_{2..5}.{1,2}) are NOT in
                                    result_2.
load(subset=None) yields the 3,782 result_2 records (subset = domain). The 224 result_5-only records are
available with load(subset='web_r5only') (subset field 'web_r5only', ids unique w.r.t. result_2) and are
excluded from the default so that the default count equals the report's 3,782.

Steps (split from the trajectory text; nothing dropped, headers go to task/ground_truth)
  web:      header 'Task: ... / Expected answer: ... / Score: ?' then '[Step n]' blocks (n = 1..N contiguous,
            verified). One block = one step, role 'agent', agent 'web agent', native_idx = n; the block text
            (Page: / Agent: / Action:) is the content verbatim.
  os:       '[Task]' block -> step 0, role 'user', native_idx 'Task' (also used as `task`); then alternating
            '[Agent]' -> role 'agent' (native_idx 'Agent k', k = 1-based agent turn) and '[OS response]' ->
            role 'env' (native_idx 'OS response k'). 13 trajectories end on an [OS response]; kept as is.
  database: a single block (Question / Evidence / Agent SQL / Gold SQL / Correct / Notes) -> one step,
            role 'agent', native_idx 0. task = Question (+ Evidence); ground_truth = Gold SQL;
            final_output = Agent SQL.
  embodied: 'Task: ...' then 'Primitive plan (k steps):' followed by one indented primitive per line ->
            one step per line, role 'agent', native_idx = 1-based line number (count matches k, verified).
            3 claude records have 'Primitive plan (0 steps)' and therefore 0 steps (kept, not dropped).

Index mapping
  Only result_5 records have a step label. failure_step_number is the 1-based n of the '[Step n]' block the
  judge blames -> faulty_step = n - 1 (verified 1 <= n <= N for all 294 int labels). It is attached to a
  result_2 record only when result_2 also calls the run a failure (failure_type != 'Success'); when the two
  passes disagree the result_5 step is still exposed in extra['result_5'] but faulty_step stays None.
  All other records: faulty_step None, faulty_steps [].

Labels / outcome
  category = result_2 failure_type (None when 'Success'); reason = result_2 judge reason (None on Success).
  outcome = passed (bool) or score >= 1.0 when present (3,512 records), else judge failure_type == 'Success'
  (embodied only). meta['judge_env_disagree'] = True when an env verdict exists and disagrees with the
  judge's Success/failure call (None when there is no env verdict).
  extra = {failure_type, reason, env_verdict ('passed'|'score' value or None), result_5: {failure_type,
           reason, failure_step_number, steps} when present}.
  meta = {domain, model, model_name, run, task_id, label_source ('LLM judge, result_2' / 'result_5'),
          judge_env_disagree, outcome_source, n_native_steps, source_file}.
"""
import json
import os
import re

SLUG = "horizon"
ROOT = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/horizon/hf"
MODEL_NAME = {"gpt": "gpt-5-mini", "claude": "claude-sonnet-4"}

_WEB_STEP = re.compile(r"^\[Step (\d+)\]\n", re.M)
_OS_BLOCK = re.compile(r"^\[(Task|Agent|OS response)\]\n", re.M)


def _web(t):
    parts = _WEB_STEP.split(t)
    head = parts[0]
    task = re.search(r"^Task:\s*(.*)$", head, re.M)
    exp = re.search(r"^Expected answer:\s*(.*)$", head, re.M)
    steps = []
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        body = parts[i + 1].strip("\n")
        steps.append({"idx": len(steps), "native_idx": n, "agent": "web agent", "role": "agent", "content": body, "meta": {}})
    final = None
    m = re.findall(r"^Action:\s*stop \[(.*?)\]\s*$", t, re.M)
    if m:
        final = m[-1]
    gt = exp.group(1).strip() if exp else None
    return (task.group(1).strip() if task else head.strip()), gt, final, steps, head


def _os(t):
    parts = _OS_BLOCK.split(t)
    steps, task, final = [], "", None
    k_agent = k_env = 0
    pre = parts[0].strip()
    if pre:  # text before the first block tag (not expected)
        steps.append({"idx": 0, "native_idx": "preamble", "agent": "env", "role": "env", "content": pre, "meta": {}})
    for i in range(1, len(parts), 2):
        tag, body = parts[i], parts[i + 1].strip("\n")
        if tag == "Task":
            task = body
            steps.append({"idx": len(steps), "native_idx": "Task", "agent": "user", "role": "user", "content": body, "meta": {}})
        elif tag == "Agent":
            k_agent += 1
            steps.append({"idx": len(steps), "native_idx": f"Agent {k_agent}", "agent": "os agent", "role": "agent", "content": body, "meta": {"agent_turn": k_agent}})
            m = re.search(r"^Act:\s*(answer\(.*\)|finish.*)\s*$", body, re.M | re.S)
            if m:
                final = m.group(1).strip()
        else:
            k_env += 1
            steps.append({"idx": len(steps), "native_idx": f"OS response {k_env}", "agent": "OS", "role": "env", "content": body, "meta": {}})
    return task, None, final, steps


def _db(t):
    def f(key):
        m = re.search(rf"^{key}\s*:\s*(.*)$", t, re.M)
        return m.group(1).strip() if m else None
    q, ev = f("Question"), f("Evidence")
    task = q or t
    if ev:
        task += "\nEvidence: " + ev
    steps = [{"idx": 0, "native_idx": 0, "agent": "sql agent", "role": "agent", "content": t.strip("\n"), "meta": {}}]
    return task, f("Gold  SQL") or f("Gold SQL"), f("Agent SQL"), steps


def _embodied(t):
    m = re.search(r"^Task:\s*(.*)$", t, re.M)
    task = m.group(1).strip() if m else ""
    lines = t.splitlines()
    steps = []
    for ln in lines:
        if ln.startswith("  "):
            steps.append({"idx": len(steps), "native_idx": len(steps) + 1, "agent": "embodied planner", "role": "agent", "content": ln.strip(), "meta": {}})
    return task, None, None, steps


def _split(domain, t):
    if domain == "web":
        task, gt, final, steps, _ = _web(t)
        return task, gt, final, steps
    if domain == "os":
        return _os(t)
    if domain == "database":
        return _db(t)
    if domain == "embodied":
        return _embodied(t)
    return t, None, None, [{"idx": 0, "native_idx": 0, "agent": "agent", "role": "agent", "content": t, "meta": {}}]


def _env_outcome(x):
    if "passed" in x and x["passed"] is not None:
        return bool(x["passed"]), "passed"
    if x.get("score") is not None:
        return x["score"] >= 1.0, "score"
    return None, None


def _convert(x, r5=None, subset=None, source="result_2"):
    domain = x["domain"]
    task, gt, final, steps = _split(domain, x["trajectory"])
    judge_success = x.get("failure_type") == "Success"
    env_ok, src = _env_outcome(x)
    if env_ok is not None:
        outcome = 1 if env_ok else 0
        disagree = (env_ok != judge_success)
    else:
        outcome, disagree, src = (1 if judge_success else 0), None, "judge"
    fs = None
    r5_extra = None
    if r5 is not None:
        n = r5.get("failure_step_number")
        r5_extra = {"failure_type": r5.get("failure_type"), "reason": r5.get("reason"), "failure_step_number": n, "steps": r5.get("steps")}
        if isinstance(n, int) and 1 <= n <= len(steps) and not judge_success:
            fs = n - 1
    extra = {"failure_type": x.get("failure_type"), "reason": x.get("reason"),
             "env_verdict": x.get("passed") if "passed" in x else x.get("score")}
    if r5_extra is not None:
        extra["result_5"] = r5_extra
    if "existing_category" in x:
        extra["existing_category"] = x["existing_category"]
    return {
        "dataset": SLUG,
        "id": x["id"],
        "subset": subset or domain,
        "system": {"web": "WebArena browsing agent", "os": "AgentBench OS agent", "database": "text-to-SQL agent (BIRD)",
                   "embodied": "bimanual primitive planner"}.get(domain, domain),
        "task": task,
        "ground_truth": gt,
        "final_output": final,
        "outcome": outcome,
        "steps": steps,
        "annotation": {
            "faulty_step": fs,
            "faulty_steps": [fs] if fs is not None else [],
            "faulty_agent": steps[fs]["agent"] if fs is not None else None,
            "category": None if judge_success else x.get("failure_type"),
            "reason": None if judge_success else x.get("reason"),
            "extra": extra,
        },
        "meta": {
            "domain": domain, "model": x.get("model"), "model_name": MODEL_NAME.get(x.get("model")),
            "run": x.get("run"), "task_id": x.get("task_id"),
            "label_source": f"LLM judge ({source})" + (" + result_5 step label" if r5 is not None else ""),
            "judge_env_disagree": disagree, "outcome_source": src,
            "n_native_steps": len(steps), "source_file": f"{source}/classified_results.json",
            "label_note": "all failure_type / reason / failure_step_number labels are LLM-judge outputs, not human",
        },
    }


def _load_json(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def load(limit=None, subset=None):
    r5 = {x["id"]: x for x in _load_json("result_5/classified_results.json")}
    n = 0
    if subset == "web_r5only":
        r2_ids = {x["id"] for x in _load_json("result_2/classified_results.json")}
        for x in r5.values():
            if x["id"] in r2_ids:
                continue
            yield _convert(x, r5=x, subset="web_r5only", source="result_5")
            n += 1
            if limit is not None and n >= limit:
                return
        return
    for x in _load_json("result_2/classified_results.json"):
        if subset is not None and x["domain"] != subset:
            continue
        yield _convert(x, r5=r5.get(x["id"]))
        n += 1
        if limit is not None and n >= limit:
            return
