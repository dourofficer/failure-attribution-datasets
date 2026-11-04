"""AgentHallu (arXiv:2601.06818) loader.

Files: data/agenthallu/repo/AgentHallu/<framework>/NNN.json, 693 files in 7 framework folders
(BFCL 164, Camel 93, Magentic_One 94, Octotools 47, OpenDeepSearch 100, OpenManus 104, SmolAgents 91).
Both hallucinated (443, is_hallucination == "true") and clean (250) runs are loaded; clean runs get
outcome 1 and an empty annotation.

Steps
  One `history` entry = one step, in array order. native_idx = the entry's own `step` number (1-based in
  the dataset; NOT always contiguous: BFCL/043 repeats step 2, BFCL/083 skips 6, BFCL/142 starts at 2,
  OpenManus/014 skips 12). agent = `role` when present (agent name, e.g. 'MagenticOneOrchestrator',
  'WebSurfer', 'Coder', 'ComputerTerminal', 'Search Agent', 'Developer Agent', 'Planner', 'Coordinator',
  'assistant'); when absent (single-agent SmolAgents / OpenDeepSearch / Octotools and 7 Camel steps) the
  record's `agent_type` is used. role = 'agent' for every entry (the dataset has no user/tool turns:
  tool returns live inside the step; ComputerTerminal / Computer_terminal-style executors are also kept as
  'agent' because the dataset names them as speakers and their output is the step content).
  content rendering: `content` followed, for each aligned (tool_calls[i], tool_responses[i]) pair, by
      "[tool_call] <name>(<arguments>)" and "[tool_result] <response>"
  (arguments rendered as JSON when a dict, verbatim when a string, e.g. CodeAct code; responses rendered as
  JSON when not a string). Nothing is truncated. Step meta = {tool_calls, tool_responses} verbatim.

Index mapping
  `hallucination_step` is a string holding a 1-based step number that matches history[i].step, so
      faulty_step = the array position i of the FIRST history entry with entry['step'] == int(hallucination_step)
  (match by value, not by position, because of the gaps above; all 443 labels match exactly one entry).
  faulty_agent = that step's agent.

Labels
  category = '<hallucination_category> / <hallucination_subcategory>'; reason = hallucination_reason;
  extra = {hallucination_category, hallucination_subcategory, hallucination_step (native str), explanation
           (reference solution shown to annotators), agent_answer, is_hallucination (raw string)}.
  outcome = 0 if is_hallucination == 'true' else 1. task = question; ground_truth = true_answer;
  final_output = agent_answer (BFCL stores these as per-turn lists -> rendered '[turn k] ...' lines; numeric
  answers -> JSON text; `explanation` may be a dict and is kept verbatim in extra). subset = framework folder name; system = agent_type (e.g. 'OWL' for Camel);
  meta = {model_id, question_source, question_domain, agent_type, source_file}.
  Note: Human-Interaction labels land on agent steps (the simulated user's wrong fact arrives inside the
  agent's step, e.g. via an ask-user tool), since no user turns exist in `history`.
"""
import glob
import json
import os

SLUG = "agenthallu"
ROOT = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/agenthallu/repo/AgentHallu"
FRAMEWORKS = ["BFCL", "Camel", "Magentic_One", "Octotools", "OpenDeepSearch", "OpenManus", "SmolAgents"]


def _j(v):
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def _text(v):
    """BFCL stores question / true_answer / agent_answer as lists (one entry per user turn); other frameworks
    occasionally store numeric answers. Render non-strings to text: a list of per-turn entries becomes
    '[turn 1] ...\n[turn 2] ...', anything else is JSON."""
    if v is None or isinstance(v, str):
        return v
    if isinstance(v, list):
        return "\n".join(f"[turn {i + 1}] " + (" ".join(map(str, x)) if isinstance(x, list) else _j(x)) for i, x in enumerate(v))
    return _j(v)


def _render(s):
    parts = []
    if s.get("content"):
        parts.append(s["content"])
    calls = s.get("tool_calls") or []
    resps = s.get("tool_responses") or []
    for i in range(max(len(calls), len(resps))):
        if i < len(calls):
            c = calls[i] or {}
            parts.append(f"[tool_call] {c.get('name')}({_j(c.get('arguments')) if c.get('arguments') is not None else ''})")
        if i < len(resps):
            parts.append("[tool_result] " + _j(resps[i]))
    return "\n".join(parts)


def _convert(path, fw, d):
    steps = []
    for i, s in enumerate(d.get("history") or []):
        steps.append({"idx": i, "native_idx": s.get("step", i + 1), "agent": (s.get("role") or d.get("agent_type") or "").strip(),
                      "role": "agent", "content": _render(s),
                      "meta": {"tool_calls": s.get("tool_calls"), "tool_responses": s.get("tool_responses")}})
    hall = str(d.get("is_hallucination")).lower() == "true"
    fs = None
    if hall and d.get("hallucination_step") is not None:
        try:
            k = int(d["hallucination_step"])
            fs = next((i for i, s in enumerate(d["history"]) if s.get("step") == k), None)
        except (TypeError, ValueError):
            fs = None
    cat = d.get("hallucination_category")
    sub = d.get("hallucination_subcategory")
    return {
        "dataset": SLUG,
        "id": f"{fw}/{os.path.splitext(os.path.basename(path))[0]}",
        "subset": fw,
        "system": d.get("agent_type") or "",
        "task": _text(d.get("question")) or "",
        "ground_truth": _text(d.get("true_answer")),
        "final_output": _text(d.get("agent_answer")),
        "outcome": 0 if hall else 1,
        "steps": steps,
        "annotation": {
            "faulty_step": fs,
            "faulty_steps": [fs] if fs is not None else [],
            "faulty_agent": steps[fs]["agent"] if fs is not None else None,
            "category": (f"{cat} / {sub}" if sub else cat) if hall else None,
            "reason": d.get("hallucination_reason") if hall else None,
            "extra": ({"hallucination_category": cat, "hallucination_subcategory": sub,
                       "hallucination_step": d.get("hallucination_step"), "explanation": d.get("explanation"),
                       "agent_answer": d.get("agent_answer"), "is_hallucination": d.get("is_hallucination")}
                      if hall else {"explanation": d.get("explanation"), "agent_answer": d.get("agent_answer"),
                                    "is_hallucination": d.get("is_hallucination")}),
        },
        "meta": {"model_id": d.get("model_id"), "question_source": d.get("question_source"),
                 "question_domain": d.get("question_domain"), "agent_type": d.get("agent_type"),
                 "source_file": os.path.relpath(path, ROOT), "label_note": "human labels (step + category + cause)"},
    }


def load(limit=None, subset=None):
    n = 0
    for fw in FRAMEWORKS:
        if subset is not None and fw != subset:
            continue
        for p in sorted(glob.glob(os.path.join(ROOT, fw, "*.json"))):
            with open(p, encoding="utf-8") as fh:
                d = json.load(fh)
            yield _convert(p, fw, d)
            n += 1
            if limit is not None and n >= limit:
                return
