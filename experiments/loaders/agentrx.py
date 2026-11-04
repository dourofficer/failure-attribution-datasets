"""Loader for AgentRx (microsoft/AgentRx, public GitHub subset) -> unified trajectory schema.

Files under data/agentrx/github/data/:
* ground_truth/tau_ground_truth.json (29) and ground_truth/magentic_one_ground_truth.json (44):
  [{trajectory_id, failures: [{failure_id, step_number, step_reason, failure_category,
  category_reason, failed_agent}], root_cause: {failure_id, reason_for_root_cause}, failure_summary}]
* tau_retail/tau_dataset_failed.json: tau-bench retail runs {task_id, reward, info{task{instruction,
  outputs, actions, user_id}}, traj: [OpenAI chat messages]}.
* magentic_dataset/<id>.json: Magentic-One logs (Who&When Hand-Crafted format), list of {content, role}.

Steps / index mapping
---------------------
* tau_retail: one step per ``traj`` message, including the system (policy) message.  AgentRx's
  ``step_number`` is the 1-based position in ``traj`` counting the system message, so
  ``idx = step_number - 1``; ``native_idx = idx + 1``.  Roles: system -> system (agent 'System'),
  user (simulated customer) -> user (agent 'User'), assistant -> agent (agent 'Assistant'; tool calls
  rendered as ``[tool_call] name(arguments)``), tool -> tool (agent 'Tool:<name>', content rendered
  as ``[tool_result <name>] ...``).
* magentic_one: one step per list entry; ``step_number`` is the 1-based list index, so
  ``idx = step_number - 1``.  Roles: human -> user; ComputerTerminal -> tool; Orchestrator variants
  and specialists -> agent.

Labels: ``faulty_step`` = step of the failure whose ``failure_id`` equals ``root_cause.failure_id``
(the first *unrecoverable* failure); ``faulty_steps`` = steps of ALL annotated failure events
(including later-recovered ones), sorted; ``faulty_agent`` / ``category`` / reasons from the
root-cause event; ``extra.failures`` is the full event list with our ``idx`` added,
``extra.canonical_category`` normalises the inconsistent category spellings.
Quirks: ``failure_id`` is sometimes a string; agent casing varies (Websurfer/WebSurfer); the
``failed_agent`` can be ``User``; several Magentic-One event steps point at the orchestrator's
instruction to an agent rather than at that agent's reply (see loader report).
"""
import glob
import json
import os
import re

SLUG = "agentrx"
GB = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/agentrx/github/data"
CANON = [("system failure", "System Failure"), ("guardrail", "Guardrails Triggered"), ("not supported", "Intent Not Supported"),
         ("specified", "Under-specified User Intent"), ("misalign", "Intent-Plan Misalignment"), ("misinterpret", "Misinterpretation of Tool Output"),
         ("invalid", "Invalid Invocation"), ("invention", "Invention of New Information"), ("hallucin", "Invention of New Information"),
         ("adherence", "Instruction/Plan Adherence Failure")]


def canon(c):
    cl = str(c or "").lower()
    for k, v in CANON:
        if k in cl:
            return v
    return "OTHER:" + str(c)


def _read_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _tool_call_str(tc):
    fn = tc.get("function") or {}
    return f"{fn.get('name')}({fn.get('arguments')})"


def _tau_steps(t):
    steps = []
    for i, m in enumerate(t["traj"]):
        role = m.get("role")
        c = m.get("content") or ""
        if not isinstance(c, str):
            c = json.dumps(c, ensure_ascii=False)
        meta = {}
        if role == "assistant":
            agent, r = "Assistant", "agent"
            if m.get("tool_calls"):
                calls = "\n".join("[tool_call] " + _tool_call_str(tc) for tc in m["tool_calls"])
                c = (c + "\n" if c else "") + calls
                meta["tool_calls"] = [(tc.get("function") or {}).get("name") for tc in m["tool_calls"]]
        elif role == "tool":
            agent, r = f"Tool:{m.get('name')}", "tool"
            c = f"[tool_result {m.get('name')}]\n{c}"
            meta["tool_name"] = m.get("name")
            meta["tool_call_id"] = m.get("tool_call_id")
        elif role == "user":
            agent, r = "User", "user"
        elif role == "system":
            agent, r = "System", "system"
        else:
            agent, r = str(role), "env"
        steps.append({"idx": i, "native_idx": i + 1, "agent": agent, "role": r, "content": c, "meta": meta})
    return steps


def _mag_role(agent):
    a = agent.lower()
    if a in ("human", "user"):
        return "user"
    if a in ("computerterminal", "computer_terminal"):
        return "tool"
    return "agent"


def _mag_steps(d):
    steps = []
    for i, m in enumerate(d):
        agent = (m.get("role") or "").strip()
        c = m.get("content") or ""
        if not isinstance(c, str):
            c = json.dumps(c, ensure_ascii=False)
        steps.append({"idx": i, "native_idx": i + 1, "agent": agent, "role": _mag_role(agent), "content": c, "meta": {}})
    return steps


def _annotation(g, n):
    failures = []
    for f in g.get("failures") or []:
        s = f.get("step_number")
        idx = s - 1 if isinstance(s, int) and 1 <= s <= n else None
        failures.append({**f, "idx": idx, "canonical_category": canon(f.get("failure_category"))})
    rc_id = str((g.get("root_cause") or {}).get("failure_id"))
    rc = next((f for f in failures if str(f.get("failure_id")) == rc_id), None)
    fs = rc["idx"] if rc else None
    all_idx = sorted({f["idx"] for f in failures if f["idx"] is not None})
    if fs is not None and fs not in all_idx:
        all_idx = sorted(all_idx + [fs])
    first_id = min((f["failure_id"] for f in failures if isinstance(f.get("failure_id"), int)), default=None)
    reason = None
    if rc:
        reason = (f"step_reason: {rc.get('step_reason')} | category_reason: {rc.get('category_reason')} | "
                  f"root_cause: {(g.get('root_cause') or {}).get('reason_for_root_cause')}")
    return {"faulty_step": fs, "faulty_steps": all_idx,
            "faulty_agent": rc.get("failed_agent") if rc else None,
            "category": rc.get("failure_category") if rc else None, "reason": reason,
            "extra": {"failures": failures, "root_cause": g.get("root_cause"), "failure_summary": g.get("failure_summary"),
                      "canonical_category": rc["canonical_category"] if rc else None,
                      "n_failures": len(failures), "root_cause_is_first_failure": (rc is not None and first_id is not None and str(first_id) == rc_id),
                      "failure_steps_out_of_range": [f.get("step_number") for f in failures if f["idx"] is None]}}


def _load_tau(limit_state):
    traj = {t["task_id"]: t for t in _read_json(os.path.join(GB, "tau_retail", "tau_dataset_failed.json"))}
    for g in _read_json(os.path.join(GB, "ground_truth", "tau_ground_truth.json")):
        t = traj[g["trajectory_id"]]
        steps = _tau_steps(t)
        task_info = (t.get("info") or {}).get("task") or {}
        final = next((s["content"] for s in reversed(steps) if s["role"] == "agent" and s["content"].strip()), None)
        yield {"dataset": SLUG, "id": f"tau_retail/{g['trajectory_id']}", "subset": "tau_retail",
               "system": "tau-bench retail tool-calling agent (gpt-4o) + simulated user",
               "task": task_info.get("instruction") or "",
               "ground_truth": json.dumps({"outputs": task_info.get("outputs"), "actions": task_info.get("actions")}, ensure_ascii=False),
               "final_output": final, "outcome": 0 if not t.get("reward") else 1, "steps": steps,
               "annotation": _annotation(g, len(steps)),
               "meta": {"trajectory_id": g["trajectory_id"], "reward": t.get("reward"), "user_id": task_info.get("user_id"),
                        "trial": t.get("trial"), "source": (t.get("info") or {}).get("source"),
                        "step_indexing": "step_number = 1-based position in traj incl. system message"}}


def _load_magentic():
    ww = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(GB, "magentic_dataset_whowhen", "*.json"))}
    for g in _read_json(os.path.join(GB, "ground_truth", "magentic_one_ground_truth.json")):
        tid = g["trajectory_id"]
        d = _read_json(os.path.join(GB, "magentic_dataset", f"{tid}.json"))
        steps = _mag_steps(d)
        task = next((s["content"] for s in steps if s["role"] == "user"), steps[0]["content"] if steps else "")
        final = next((s["content"] for s in reversed(steps) if "FINAL ANSWER" in s["content"]), None)
        yield {"dataset": SLUG, "id": f"magentic_one/{tid}", "subset": "magentic_one", "system": "Magentic-One",
               "task": task, "ground_truth": None, "final_output": final, "outcome": 0, "steps": steps,
               "annotation": _annotation(g, len(steps)),
               "meta": {"trajectory_id": tid, "has_whowhen_format_copy": tid in ww, "origin": "Who&When Hand-Crafted subset",
                        "step_indexing": "step_number = 1-based list index"}}


def load(limit=None, subset=None):
    gens = []
    if subset in (None, "tau_retail"):
        gens.append(_load_tau(None))
    if subset in (None, "magentic_one"):
        gens.append(_load_magentic())
    n = 0
    for gen in gens:
        for t in gen:
            if limit is not None and n >= limit:
                return
            yield t
            n += 1
