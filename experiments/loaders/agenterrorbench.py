"""AgentErrorBench (AgentDebug, arXiv:2509.25370) loader.

Files (all under data/agenterrorbench/):
  gdrive/Label/{alfworld,gaia,webshop}_labels.json   200 label records (100 / 50 / 50)
  gdrive/Original_Failure_Trajectory/<Env>/<id>.json  196 trajectories {messages, metadata}
  hf_davide221/data/*.parquet                         third-party mirror; `full_trajectory` is the same
                                                      {messages, metadata} object as a JSON string. Used only
                                                      for the 4 ids missing from the Drive folder
                                                      (GPT-4o_002_alfworld_task_002, GPT-4o_033_alfworld_task_033,
                                                      Llama3.3-70B-Turbo_014_memory_b001_t00_e05-c9015705,
                                                      Qwen3-8B_014_memory_b001_t00_e04-5e8c1dcf). Loaded lazily
                                                      (pandas) only when one of them is reached.

Steps
  Every message is one step. `messages` strictly alternate user / assistant starting with user (verified
  on all 200: 2*n_agent_turns messages, no system message). user = task prompt + current observation +
  admissible actions (GAIA: tool output) -> role 'env', agent 'user'; assistant = the tagged
  <memory>/<reflection>/<plan>/<action> blocks (Qwen3 adds <think>) -> role 'agent', agent 'assistant'.
  native_idx = message index (0-based). Assistant steps carry meta['agent_turn'] = k (1-based agent turn).

Index mapping
  Native `critical_failure_step` k is a 1-based agent turn. Agent turn k is message index 2k-1, so
      faulty_step (our idx) = 2k - 1.
  Verified: 199/200 labels land on an assistant message. The GAIA record
  GPT-4o_003_memory_b000_t00_e03-21a3a421 labels step 3 of a 1-turn (2-message) trajectory ->
  faulty_step None, faulty_steps [], annotation.extra['label_out_of_range'] = True (native k kept in extra).

Labels
  category = '<module>.<failure_type>' taken from the step_annotations entry whose `step` == k (module = the
  non-'step' key of that entry; failure_type may be empty -> 'module.' kept verbatim, no normalisation);
  if no such entry, '<critical_failure_module>.' is used. reason = that entry's `reasoning`.
  extra = {critical_failure_module, critical_failure_step (native k), step_annotations (full list), LLM,
           task_type, won, trajectory_source ('gdrive' | 'hf_mirror'), label_out_of_range}.
  outcome = 0 for all (failed-only release; metadata.won is False everywhere).
  task = the "Your task is: ..." (ALFWorld/WebShop) or "Task: ..." (GAIA) line of the first user message,
  falling back to the full first user message. ground_truth None (not released). final_output = last
  assistant message.
  subset = env ('alfworld' | 'gaia' | 'webshop'); system = 'AgentDebug ReAct agent'; meta = {LLM, model
  (metadata.model), env_id, steps (metadata), timestamp, gamefile/pid when present, source_file}.
"""
import json
import os
import re

SLUG = "agenterrorbench"
DATA = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/agenterrorbench"
GD = os.path.join(DATA, "gdrive")
ENVDIR = {"alfworld": "ALFWorld", "gaia": "GAIA", "webshop": "WebShop"}

_hf_cache = None


def _hf_trajectory(tid):
    """Fallback: fetch `full_trajectory` of one id from the HF mirror parquet files (lazy, cached)."""
    global _hf_cache
    if _hf_cache is None:
        import sys
        import glob
        sys.path.append("/dataDisk/home/thanhdo/.local/lib/python3.10/site-packages")
        import pandas as pd
        _hf_cache = {}
        for p in sorted(glob.glob(os.path.join(DATA, "hf_davide221", "data", "*.parquet"))):
            df = pd.read_parquet(p, columns=["trajectory_id", "full_trajectory"])
            for r in df.itertuples(index=False):
                _hf_cache[r.trajectory_id] = r.full_trajectory
    s = _hf_cache.get(tid)
    return json.loads(s) if s is not None else None


_TASK_RE = re.compile(r"^(?:Your task is(?: to)?:|Task:)\s*(.+?)\s*$", re.M)


def _task_of(first_user_msg):
    m = _TASK_RE.search(first_user_msg or "")
    return m.group(1) if m else (first_user_msg or "")


def _critical_annotation(label, k):
    for a in label.get("step_annotations") or []:
        if a.get("step") == k:
            for mod, v in a.items():
                if mod != "step" and isinstance(v, dict):
                    return mod, v.get("failure_type"), v.get("reasoning")
    return None, None, None


def _convert(label, env, tj, source):
    msgs = tj["messages"]
    meta = tj.get("metadata") or {}
    steps = []
    turn = 0
    for j, m in enumerate(msgs):
        if m["role"] == "assistant":
            turn += 1
            steps.append({"idx": j, "native_idx": j, "agent": "assistant", "role": "agent",
                          "content": m.get("content") or "", "meta": {"agent_turn": turn}})
        else:
            steps.append({"idx": j, "native_idx": j, "agent": m["role"], "role": "env" if m["role"] == "user" else "system",
                          "content": m.get("content") or "", "meta": {}})
    k = label["critical_failure_step"]
    fs = 2 * k - 1
    out_of_range = not (0 <= fs < len(steps) and steps[fs]["role"] == "agent")
    mod, ftype, reasoning = _critical_annotation(label, k)
    if mod is None:
        mod = label.get("critical_failure_module")
    category = f"{mod}.{ftype or ''}" if mod is not None else None
    final = next((s["content"] for s in reversed(steps) if s["role"] == "agent"), None)
    return {
        "dataset": SLUG,
        "id": label["trajectory_id"],
        "subset": env,
        "system": "AgentDebug ReAct agent",
        "task": _task_of(msgs[0]["content"] if msgs and msgs[0]["role"] == "user" else ""),
        "ground_truth": None,
        "final_output": final,
        "outcome": 0,
        "steps": steps,
        "annotation": {
            "faulty_step": None if out_of_range else fs,
            "faulty_steps": [] if out_of_range else [fs],
            "faulty_agent": "assistant",
            "category": category,
            "reason": reasoning,
            "extra": {
                "critical_failure_module": label.get("critical_failure_module"),
                "critical_failure_step": k,
                "step_annotations": label.get("step_annotations"),
                "LLM": label.get("LLM"),
                "task_type": label.get("task_type"),
                "won": meta.get("won"),
                "trajectory_source": source,
                "label_out_of_range": out_of_range,
            },
        },
        "meta": {
            "LLM": label.get("LLM"),
            "model": meta.get("model"),
            "env": env,
            "env_id": meta.get("env_id"),
            "metadata_steps": meta.get("steps"),
            "timestamp": meta.get("timestamp"),
            "gamefile": meta.get("gamefile"),
            "pid": meta.get("pid"),
            "n_agent_turns": turn,
            "source_file": (f"gdrive/Original_Failure_Trajectory/{ENVDIR[env]}/{label['trajectory_id']}.json"
                            if source == "gdrive" else "hf_davide221/data/*.parquet"),
            "label_note": "human labels; single annotated step per trajectory",
        },
    }


def load(limit=None, subset=None):
    n = 0
    for env in ("alfworld", "gaia", "webshop"):
        if subset is not None and env != subset:
            continue
        with open(os.path.join(GD, "Label", f"{env}_labels.json"), encoding="utf-8") as fh:
            labels = json.load(fh)
        for label in labels:
            tid = label["trajectory_id"]
            p = os.path.join(GD, "Original_Failure_Trajectory", ENVDIR[env], tid + ".json")
            if os.path.exists(p):
                with open(p, encoding="utf-8") as fh:
                    tj = json.load(fh)
                source = "gdrive"
            else:
                tj = _hf_trajectory(tid)
                source = "hf_mirror"
                if tj is None:
                    continue
            yield _convert(label, env, tj, source)
            n += 1
            if limit is not None and n >= limit:
                return
