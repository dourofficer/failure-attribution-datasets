"""Loader for Who&When (Kevin355/Who_and_When) -> unified trajectory schema (see SCHEMA.md).

Files: data/who_and_when/Who&When/{Hand-Crafted,Algorithm-Generated}/<n>.json (58 + 126 = 184 logs).

Steps / index mapping
---------------------
* One step per ``history`` entry, in order; our ``idx`` == position in ``history`` == native index.
* ``mistake_step`` is a 0-based index into ``history`` (stored as a string, sometimes wrapped in
  literal quotes like ``"'4'"``), so ``faulty_step = int(mistake_step)`` with no offset.
* Hand-Crafted: ``history[0]`` is the human question (role ``human``); orchestrator thoughts,
  orchestrator instructions (``Orchestrator (-> X)``), specialist replies and
  ``Orchestrator (termination condition)`` are separate steps.  Agent name = ``role`` string.
* Algorithm-Generated: no human turn in ``history`` (question only in ``question``); agent name =
  ``name`` field (``role`` there is the AG2 chat role user/assistant and is kept in step meta).

Roles: ``human`` -> user; ``ComputerTerminal`` / ``Computer_terminal`` -> tool; everything else
(all Orchestrator variants, specialists, *_Expert) -> agent.

Label fields (mistake_agent / mistake_step / mistake_reason / question_ID / level) have their
surrounding quotes stripped.  benchmark = GAIA (UUID question_ID) or AssistantBench (64-hex sha).
Quirks: agent-name casing is inconsistent (WebSurfer/Websurfer); in a few logs the blamed agent is
not the agent of the labelled step (see loader report).
"""
import glob
import json
import os
import re

SLUG = "who_and_when"
DATA_DIR = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/who_and_when/Who&When"
SUBSETS = {"hand_crafted": ("Hand-Crafted", "Magentic-One"), "algorithm_generated": ("Algorithm-Generated", "CaptainAgent")}


def _strip(v):
    if v is None:
        return None
    return str(v).strip().strip("'\"").strip()


def _agent_of(h):
    return (h.get("name") or h.get("role") or "").strip()


def _role_of(agent, raw_role):
    a = agent.lower()
    if a in ("human", "user"):
        return "user"
    if a in ("computerterminal", "computer_terminal"):
        return "tool"
    return "agent"


def _benchmark(qid):
    if re.fullmatch(r"[0-9a-f]{64}", qid or ""):
        return "AssistantBench"
    if re.fullmatch(r"[0-9a-f-]{36}", qid or ""):
        return "GAIA"
    return "unknown"


def _files(subset_key):
    sub_dir = SUBSETS[subset_key][0]
    return sorted(glob.glob(os.path.join(DATA_DIR, sub_dir, "*.json")),
                  key=lambda p: int(os.path.basename(p).split(".")[0]))


def _convert(path, subset_key):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    sub_dir, system = SUBSETS[subset_key]
    hist = d.get("history") or []
    steps = []
    for i, h in enumerate(hist):
        agent = _agent_of(h)
        meta = {}
        if "name" in h and "role" in h:
            meta["chat_role"] = h.get("role")
        steps.append({"idx": i, "native_idx": i, "agent": agent, "role": _role_of(agent, h.get("role")),
                      "content": h.get("content") if isinstance(h.get("content"), str) else json.dumps(h.get("content"), ensure_ascii=False),
                      "meta": meta})
    ms_raw = d.get("mistake_step")
    try:
        ms = int(_strip(ms_raw))
    except (TypeError, ValueError):
        ms = None
    if ms is not None and not (0 <= ms < len(steps)):
        ms = None
    ma = _strip(d.get("mistake_agent"))
    qid = _strip(d.get("question_ID"))
    final = None
    for s in reversed(steps):
        if "FINAL ANSWER" in s["content"]:
            final = s["content"]
            break
    gt = d.get("groundtruth", d.get("ground_truth"))
    return {
        "dataset": SLUG,
        "id": f"{subset_key}/{os.path.basename(path)[:-5]}",
        "subset": subset_key,
        "system": system,
        "task": d.get("question") or "",
        "ground_truth": _strip(gt) if gt is not None else None,
        "final_output": final,
        "outcome": 0,
        "steps": steps,
        "annotation": {
            "faulty_step": ms,
            "faulty_steps": [ms] if ms is not None else [],
            "faulty_agent": ma,
            "category": _strip(d.get("mistake_type")) if d.get("mistake_type") else None,
            "reason": _strip(d.get("mistake_reason")),
            "extra": {"mistake_step_raw": ms_raw, "mistake_agent_raw": d.get("mistake_agent"),
                      "labelled_step_agent": steps[ms]["agent"] if ms is not None else None,
                      "labels": d.get("labels")},
        },
        "meta": {"file": os.path.relpath(path, os.path.dirname(DATA_DIR)), "question_ID": qid,
                 "benchmark": _benchmark(qid), "level": _strip(d.get("level")) if d.get("level") is not None else None,
                 "is_correct": d.get("is_corrected", d.get("is_correct")),
                 "system_prompt": d.get("system_prompt")},
    }


def load(limit=None, subset=None):
    keys = [subset] if subset else list(SUBSETS)
    n = 0
    for key in keys:
        for path in _files(key):
            if limit is not None and n >= limit:
                return
            yield _convert(path, key)
            n += 1
