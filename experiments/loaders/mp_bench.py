"""Loader for MP-Bench (adobe-research/multi-agent-eval-bench) -> unified trajectory schema.

Annotations: data/mp_bench/adobe_multi-agent-eval-bench/MP-Bench/<annotator 1,2,3>/<manual|automatic>/<n>.json
(867 files = 3 annotators x 289 logs).  Each file: {log_source (GitHub URL), annotation: [{step,
fail_annotation, fail_category, fail_reason, ideal_action}]}.  The source logs were fetched to
data/mp_bench/sources/<sha1(log_source)[:16]>/ (index.json maps key -> {log_source, files, ...}).

Steps are built exactly as the official ``build_annotated_from_log_source.py`` does:
* Who&When JSON sources (57 Hand-Crafted + 120 Algorithm-Generated): one step per ``history`` entry,
  agent = ``name`` or ``role``.
* MAST ``console_log.txt`` sources (112 Magentic-One GAIA runs): drop everything before
  ``SCENARIO.PY STARTING !#!#``, then one step per ``---------- <Agent> ----------`` turn (text up to
  the next delimiter, stripped); question from prompt.txt, answer from expected_answer.txt.
Our ``idx`` == native 0-based position in that list; annotation ``step`` (a 0-based string) maps
to ``idx`` with no offset.  Roles: user/human -> user; Computer_terminal/ComputerTerminal -> tool;
all other names (orchestrator variants, specialists, *_Expert) -> agent.

Labels (set-valued, three annotators):
* ``faulty_steps`` = sorted union of all steps flagged by any annotator (fail_annotation == "1").
* ``faulty_step``  = earliest step flagged by >= 2 annotators, or None when no step has a majority.
* ``faulty_agent`` = agent of ``faulty_step`` with the ``(...)`` suffix removed, or None.
* ``category``     = the fail_category given for ``faulty_step`` by the majority of its voters
  (ties -> lowest annotator id); ``reason`` = the voters' fail_reasons for that step.
* ``extra.votes``  = {step(str): n_votes}; ``extra.voters`` = {step: [annotator ids]};
  ``extra.per_annotator`` = {annotator: [{step, fail_category, fail_reason, ideal_action}]};
  ``extra.out_of_range`` lists flags whose step >= number of steps (dropped from votes).
subset = 'manual' | 'automatic'; id = '<subset>/<n>'.  Flags with a non-integer step are ignored.
"""
import glob
import hashlib
import json
import os
import re
from collections import Counter, defaultdict

SLUG = "mp_bench"
BASE = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/mp_bench"
ANN_ROOT = os.path.join(BASE, "adobe_multi-agent-eval-bench", "MP-Bench")
SRC_DIR = os.path.join(BASE, "sources")
_DELIM = re.compile(r"^-{10} (.+?) -{10}$")


def parse_console_log(content):
    marker = "SCENARIO.PY STARTING !#!#"
    pos = content.find(marker)
    if pos != -1:
        content = content[pos + len(marker):]
    turns, cur, lines = [], None, []
    for line in content.splitlines():
        m = _DELIM.match(line.strip())
        if m:
            if cur is not None:
                turns.append({"role": cur, "content": "\n".join(lines).strip()})
            cur, lines = m.group(1).strip(), []
        elif cur is not None:
            lines.append(line)
    if cur is not None:
        turns.append({"role": cur, "content": "\n".join(lines).strip()})
    return turns


def _base_agent(a):
    return re.sub(r"\s*\(.*\)$", "", a or "").strip()


def _role_of(agent):
    a = agent.lower()
    if a in ("human", "user"):
        return "user"
    if a in ("computerterminal", "computer_terminal"):
        return "tool"
    return "agent"


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _load_source(url):
    """-> dict(question, ground_truth, history[{role,content}], source_kind, system, is_correct, raw_meta)"""
    key = hashlib.sha1(url.encode()).hexdigest()[:16]
    d = os.path.join(SRC_DIR, key)
    if not os.path.isdir(d):
        return None
    if url.endswith(".json"):
        files = [f for f in os.listdir(d) if f.endswith(".json")]
        if not files:
            return None
        raw = json.loads(_read(os.path.join(d, files[0])))
        hist = [{"role": (h.get("name") or h.get("role") or ""), "content": h.get("content") if isinstance(h.get("content"), str) else json.dumps(h.get("content"), ensure_ascii=False),
                 "chat_role": h.get("role") if "name" in h else None} for h in raw.get("history", [])]
        hc = "Hand-Crafted" in url
        return {"question": raw.get("question") or "", "ground_truth": raw.get("ground_truth", raw.get("groundtruth")),
                "history": hist, "source_kind": "Who&When/Hand-Crafted" if hc else "Who&When/Algorithm-Generated",
                "system": "Magentic-One" if hc else "CaptainAgent", "is_correct": raw.get("is_correct", raw.get("is_corrected")),
                "raw_meta": {"question_ID": raw.get("question_ID"), "level": raw.get("level"), "who_and_when_file": files[0],
                             "who_and_when_mistake_step": raw.get("mistake_step"), "who_and_when_mistake_agent": raw.get("mistake_agent")}}
    if not os.path.exists(os.path.join(d, "console_log.txt")):
        return None
    turns = parse_console_log(_read(os.path.join(d, "console_log.txt")))
    q = _read(os.path.join(d, "prompt.txt")).strip() if os.path.exists(os.path.join(d, "prompt.txt")) else ""
    gt = _read(os.path.join(d, "expected_answer.txt")).strip() if os.path.exists(os.path.join(d, "expected_answer.txt")) else ""
    level = "L3" if "level_3" in url else ("L2" if "level_2" in url else "L?")
    task_id = url.split("/")[-3] if "/" in url else None
    return {"question": q, "ground_truth": gt, "history": turns, "source_kind": f"MAST/MagenticOne_GAIA {level}",
            "system": "Magentic-One", "is_correct": None, "raw_meta": {"gaia_task_id": task_id, "level": level}}


def _instances():
    inst = defaultdict(dict)
    for fpath in glob.glob(os.path.join(ANN_ROOT, "*", "*", "*.json")):
        ann_id, split, fn = fpath.split(os.sep)[-3:]
        inst[(split, fn)][ann_id] = fpath
    return sorted(inst.items(), key=lambda kv: (kv[0][0], int(kv[0][1].split(".")[0])))


def _convert(split, fn, ann_paths):
    anns = {}
    for aid, p in sorted(ann_paths.items()):
        anns[aid] = json.loads(_read(p))
    urls = {a["log_source"] for a in anns.values()}
    url = next(iter(anns.values()))["log_source"]
    src = _load_source(url)
    if src is None:
        return None
    hist = src["history"]
    steps = []
    for i, h in enumerate(hist):
        agent = h["role"].strip()
        meta = {}
        if h.get("chat_role"):
            meta["chat_role"] = h["chat_role"]
        steps.append({"idx": i, "native_idx": i, "agent": agent, "role": _role_of(agent), "content": h["content"] or "", "meta": meta})
    n = len(steps)
    voters = defaultdict(list)
    per_ann = {}
    flags_at = defaultdict(list)
    oor = []
    for aid, d in anns.items():
        lst = []
        for a in d.get("annotation") or []:
            rec = {"step": a.get("step"), "fail_category": a.get("fail_category"), "fail_reason": a.get("fail_reason"), "ideal_action": a.get("ideal_action")}
            lst.append(rec)
            try:
                s = int(str(a.get("step")).strip())
            except (TypeError, ValueError):
                continue
            if str(a.get("fail_annotation", "1")) != "1":
                continue
            if not (0 <= s < n):
                oor.append({"annotator": aid, "step": s})
                continue
            if aid not in voters[s]:
                voters[s].append(aid)
            flags_at[s].append((aid, rec))
        per_ann[aid] = lst
    flagged = sorted(voters)
    maj = [s for s in flagged if len(voters[s]) >= 2]
    fs = maj[0] if maj else None
    category = reason = None
    if fs is not None:
        cats = Counter(r["fail_category"] for _, r in flags_at[fs] if r.get("fail_category"))
        category = cats.most_common(1)[0][0] if cats else None
        reason = "\n".join(f"[annotator {aid}; {r.get('fail_category')}] {r.get('fail_reason')}" for aid, r in flags_at[fs])
    final = next((s["content"] for s in reversed(steps) if "FINAL ANSWER" in s["content"]), None)
    return {
        "dataset": SLUG, "id": f"{split}/{fn[:-5]}", "subset": split, "system": src["system"],
        "task": src["question"], "ground_truth": src["ground_truth"] if src["ground_truth"] not in ("", None) else None,
        "final_output": final, "outcome": 0, "steps": steps,
        "annotation": {"faulty_step": fs, "faulty_steps": flagged,
                       "faulty_agent": _base_agent(steps[fs]["agent"]) if fs is not None else None,
                       "category": category, "reason": reason,
                       "extra": {"votes": {str(s): len(v) for s, v in sorted(voters.items())},
                                 "voters": {str(s): v for s, v in sorted(voters.items())},
                                 "majority_steps": maj, "per_annotator": per_ann, "n_annotators": len(anns),
                                 "out_of_range": oor, "log_source_mismatch_across_annotators": len(urls) != 1}},
        "meta": {"log_source": url, "source_kind": src["source_kind"], "is_correct": src["is_correct"],
                 "annotation_files": {aid: os.path.relpath(p, BASE) for aid, p in ann_paths.items()}, **src["raw_meta"]},
    }


def load(limit=None, subset=None):
    n = 0
    for (split, fn), ann_paths in _instances():
        if subset and split != subset:
            continue
        if limit is not None and n >= limit:
            return
        t = _convert(split, fn, ann_paths)
        if t is None:
            continue
        yield t
        n += 1
