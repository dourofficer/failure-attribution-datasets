"""Loader for LongRCA Bench (CLoud5-real/longrca-bench) -> unified trajectory schema.

Files: data/longrca/data/full/<source>/<source>__NNN.json (1,140 records, the full test set);
data/longrca/data/mini/ holds identical copies of the 200 Mini records (only used to set
``meta.in_mini``).

Steps / index mapping
---------------------
* One step per ``history`` entry; ``history[].step`` is a contiguous 0-based index, so our
  ``idx == native_idx == step``.  ``mistake_step`` is 0-based -> ``faulty_step = mistake_step``.
* Roles: native ``role == 'assistant'`` -> ``agent``; native ``role == 'user'`` entries are
  terminal / tool / evaluator / orchestration-bookkeeping records (``name == 'Computer_terminal'``)
  -> ``tool``, except the task instruction records (``name == 'human'``) -> ``user``.
* ``agent`` = ``history[].name`` as recorded (composite hand-off names such as
  ``DiagnostAgent (-> ActionAgent)`` are kept verbatim because they are themselves reference roles).
* subset = source prefix of ``question_ID`` (swe_bench_pro, terminal_bench_2, travelplanner,
  vitabench, webarena_verified).  task = first ``human`` record (else first record).  No reference
  answer; final_output = last agent record.  No taxonomy -> category None.
"""
import glob
import json
import os

SLUG = "longrca"
DATA_DIR = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/longrca/data"
SYSTEMS = {"swe_bench_pro": "DiagnostAgent-ActionAgent-JudgeAgent (custom)",
           "terminal_bench_2": "DiagnostAgent-ActionAgent-JudgeAgent (custom)",
           "travelplanner": "AutoGen MagenticOneGroupChat (manager/stay/transport/food_attr/verifier)",
           "vitabench": "Action_Expert + Computer_terminal (AG2)",
           "webarena_verified": "AutoGen Planner-WebSurfer-Critic (Task_Planner/Action_Expert/Verification_Expert)"}
SOURCES = list(SYSTEMS)


def _mini_ids():
    return {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(DATA_DIR, "mini", "*", "*.json"))}


def _role_of(h):
    name = (h.get("name") or "").strip()
    if h.get("role") == "assistant":
        return "agent"
    if name.lower() == "human":
        return "user"
    return "tool"


def _convert(path, source, mini):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    hist = d.get("history") or []
    steps = []
    for i, h in enumerate(hist):
        content = h.get("content")
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False) if content is not None else ""
        steps.append({"idx": i, "native_idx": h.get("step", i), "agent": (h.get("name") or h.get("role") or "").strip(),
                      "role": _role_of(h), "content": content, "meta": {"chat_role": h.get("role")}})
    ms = d.get("mistake_step")
    try:
        ms = int(ms)
    except (TypeError, ValueError):
        ms = None
    if ms is not None and not (0 <= ms < len(steps)):
        ms = None
    task = next((s["content"] for s in steps if s["role"] == "user"), steps[0]["content"] if steps else "")
    final = next((s["content"] for s in reversed(steps) if s["role"] == "agent"), None)
    qid = d.get("question_ID")
    return {
        "dataset": SLUG, "id": qid, "subset": source, "system": SYSTEMS.get(source, ""),
        "task": task, "ground_truth": None, "final_output": final, "outcome": 0, "steps": steps,
        "annotation": {"faulty_step": ms, "faulty_steps": [ms] if ms is not None else [],
                       "faulty_agent": d.get("mistake_agent"), "category": None, "reason": d.get("mistake_reason"),
                       "extra": {"mistake_step_raw": d.get("mistake_step"),
                                 "labelled_step_agent": steps[ms]["agent"] if ms is not None else None,
                                 "labelled_step_native_role": hist[ms].get("role") if ms is not None else None}},
        "meta": {"file": os.path.relpath(path, DATA_DIR), "in_mini": qid in mini, "source_benchmark": source,
                 "steps_contiguous": [h.get("step") for h in hist] == list(range(len(hist)))},
    }


def load(limit=None, subset=None):
    sources = [subset] if subset else SOURCES
    mini = _mini_ids()
    n = 0
    for src in sources:
        for path in sorted(glob.glob(os.path.join(DATA_DIR, "full", src, "*.json"))):
            if limit is not None and n >= limit:
                return
            yield _convert(path, src, mini)
            n += 1
