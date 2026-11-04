"""TrajErrBench (TrajDebug, THU-KEG) loader — unified TrajDebug schema files.

Root: data/trajerrbench/repo_TrajDebug/data/
  trajerrbench/en/tau2bench/*.json   400   subset 'tau2bench'      (native, English edition)
  trajerrbench/en/swebenchpro/*.json  86   subset 'swebenchpro'    (native, English edition)
  whoandwhen/{handcrafted,algorithm_generated}/*.json   58 + 126   subset 'conv_whoandwhen'
  agentdebugbench/{alfworld,gaia,webshop}/*.json       100+50+50   subset 'conv_agentdebugbench'
The zh edition is not loaded (labels and message counts are identical to en). The converted copies are
TrajDebug's re-packaging of Who&When and AgentErrorBench into the same message schema; they are loaded as
separate subsets so their indices can be cross-checked against the native loaders.
load(subset=None) yields all four subsets (486 + 184 + 200 = 870); pass a subset name to restrict.

Steps
  One `messages` entry = one step. `step` is 0-based and equals the array index in every file (verified),
  so native_idx = step = our idx. role mapping: system -> 'system', user -> 'user', assistant -> 'agent',
  tool -> 'tool'. agent = `name` when present (native subsets: name == role; conv_whoandwhen: the Who&When
  speaker, e.g. 'Orchestrator (thought)', 'WebSurfer', 'Excel_Expert', user turns are named 'human'),
  else the role (conv_agentdebugbench has no `name` key). Step meta = {judgable, compress_role}.

Index mapping
  faulty_step = metadata.annotation.critical_error_step (0-based message index) when it is an int inside the
  trajectory; None otherwise (one conv_agentdebugbench record, GPT-4o_003_memory_b000_t00_e03-21a3a421,
  has critical_error_step null because the native label k=3 is beyond its 1-turn trajectory).
  Cross-checks (verified): conv_agentdebugbench critical_error_step == 2*k-1 for the native 1-based agent
  turn k in extra.label_entry (199/199 non-null); conv_whoandwhen critical_error_step == int(mistake_step_native).
  faulty_agent = steps[faulty_step].agent.

Labels
  category = critical_error_type ('<module>.<SubType>', null for 17 native records and for all converted
  copies); reason = None (no rationale released) for native subsets; for conv_whoandwhen the Who&When
  mistake_reason; for conv_agentdebugbench the native step_annotations reasoning at step k.
  extra = everything in metadata.extra except agent_framework_description (that goes to meta), plus
  critical_error_step (native) and, for converted copies, the native label fields.
  outcome = 1 if metadata.reward == 1 else 0 (all released records have reward 0).
  task = metadata.task_description; ground_truth = extra.groundtruth for conv_whoandwhen, else None;
  final_output = last assistant message.
  model: tau2bench task_id '<domain>_failed_<model>::<uuid>' -> model, domain; swebenchpro task_id
  '<model>_instance_<repo>-<commit>-v<hash>' -> model; conv_agentdebugbench: label_entry.LLM;
  conv_whoandwhen: unknown ('').
  meta = {source_benchmark, model, domain, pair_id, language, judgable (list of bool per step), reward,
          agent_framework_description, source_file}.
  id = '<subset>/<task_id>' (native, conv_agentdebugbench) or '<subset>/<folder>/<file stem>' (conv_whoandwhen).
"""
import glob
import json
import os

SLUG = "trajerrbench"
ROOT = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/trajerrbench/repo_TrajDebug/data"
ROLE = {"system": "system", "user": "user", "assistant": "agent", "tool": "tool"}
SUBSETS = {
    "tau2bench": ["trajerrbench/en/tau2bench"],
    "swebenchpro": ["trajerrbench/en/swebenchpro"],
    "conv_whoandwhen": ["whoandwhen/handcrafted", "whoandwhen/algorithm_generated"],
    "conv_agentdebugbench": ["agentdebugbench/alfworld", "agentdebugbench/gaia", "agentdebugbench/webshop"],
}


def _model_domain(subset, md):
    tid = md.get("task_id") or ""
    if subset == "tau2bench" and "_failed_" in tid:
        dom, rest = tid.split("_failed_", 1)
        return rest.split("::")[0], dom
    if subset == "swebenchpro" and "_instance_" in tid:
        return tid.split("_instance_", 1)[0], "swe"
    if subset == "conv_agentdebugbench":
        le = (md.get("extra") or {}).get("label_entry") or {}
        return le.get("LLM") or "", le.get("task_type") or ""
    return "", (md.get("extra") or {}).get("source_benchmark") or ""


def _native_reason(subset, md, k_native):
    ex = md.get("extra") or {}
    if subset == "conv_whoandwhen":
        return ex.get("mistake_reason")
    if subset == "conv_agentdebugbench":
        le = ex.get("label_entry") or {}
        for a in le.get("step_annotations") or []:
            if a.get("step") == le.get("critical_failure_step"):
                for mod, v in a.items():
                    if mod != "step" and isinstance(v, dict):
                        return v.get("reasoning")
    return None


def _id_of(path, subset, md):
    """id = '<subset>/<task_id>' for the native and conv_agentdebugbench subsets (task ids are unique there);
    conv_whoandwhen uses '<subset>/<handcrafted|algorithm_generated>/<file stem>' because Who&When question
    IDs repeat across its two folders."""
    if subset == "conv_whoandwhen":
        return f"{subset}/{os.path.basename(os.path.dirname(path))}/{os.path.splitext(os.path.basename(path))[0]}"
    return f"{subset}/{md.get('task_id')}"


def _convert(path, subset, d):
    md = d["metadata"]
    ann = md.get("annotation") or {}
    ex = md.get("extra") or {}
    steps = []
    for i, m in enumerate(d["messages"]):
        role = m.get("role")
        name = (m.get("name") or role or "").strip()
        steps.append({"idx": i, "native_idx": m.get("step", i), "agent": name, "role": ROLE.get(role, "system"),
                      "content": m.get("content") or "", "meta": {"judgable": m.get("judgable"), "compress_role": m.get("compress_role")}})
    k = ann.get("critical_error_step")
    ok = isinstance(k, int) and 0 <= k < len(steps)
    model, domain = _model_domain(subset, md)
    extra = {kk: v for kk, v in ex.items() if kk != "agent_framework_description"}
    extra["critical_error_step"] = k
    extra["critical_error_type"] = ann.get("critical_error_type")
    if subset == "conv_agentdebugbench":
        extra["critical_failure_step_native_1based_turn"] = (ex.get("label_entry") or {}).get("critical_failure_step")
    reward = md.get("reward")
    category = ann.get("critical_error_type")
    if category is None and subset == "conv_agentdebugbench":
        le = ex.get("label_entry") or {}
        for a in le.get("step_annotations") or []:
            if a.get("step") == le.get("critical_failure_step"):
                for mod, v in a.items():
                    if mod != "step" and isinstance(v, dict):
                        category = f"{mod}.{v.get('failure_type') or ''}"
    return {
        "dataset": SLUG,
        "id": _id_of(path, subset, md),
        "subset": subset,
        "system": {"tau2bench": "tau2-bench tool-calling agent", "swebenchpro": "SWE-Bench Pro coding agent",
                   "conv_whoandwhen": "Who&When multi-agent system (converted)",
                   "conv_agentdebugbench": "AgentDebug ReAct agent (converted)"}[subset],
        "task": md.get("task_description") or "",
        "ground_truth": ex.get("groundtruth") if subset == "conv_whoandwhen" else None,
        "final_output": next((s["content"] for s in reversed(steps) if s["role"] == "agent"), None),
        "outcome": 1 if reward == 1 else 0,
        "steps": steps,
        "annotation": {
            "faulty_step": k if ok else None,
            "faulty_steps": [k] if ok else [],
            "faulty_agent": steps[k]["agent"] if ok else (ex.get("mistake_agent") if subset == "conv_whoandwhen" else None),
            "category": category,
            "reason": _native_reason(subset, md, k),
            "extra": extra,
        },
        "meta": {
            "source_benchmark": ex.get("source_benchmark"),
            "model": model,
            "domain": domain,
            "pair_id": ex.get("pair_id"),
            "language": ex.get("language"),
            "judgable": [s["meta"]["judgable"] for s in steps],
            "reward": reward,
            "agent_framework_description": ex.get("agent_framework_description"),
            "source_file": os.path.relpath(path, ROOT),
            "label_note": "native subsets: human 3-way majority label, no rationale; converted subsets carry the source dataset's labels",
        },
    }


def load(limit=None, subset=None):
    n = 0
    for name, dirs in SUBSETS.items():
        if subset is not None and name != subset:
            continue
        for dd in dirs:
            for p in sorted(glob.glob(os.path.join(ROOT, dd, "*.json"))):
                with open(p, encoding="utf-8") as fh:
                    d = json.load(fh)
                yield _convert(p, name, d)
                n += 1
                if limit is not None and n >= limit:
                    return
