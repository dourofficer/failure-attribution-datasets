"""Loader for Who&When Pro (HF Leoxx/whowhen_pro) -> unified trajectory schema.

Files: data/who_and_when_pro/data/text.jsonl (6,257 rows, complete) and video.jsonl (916 rows,
complete).  The image / image_gui splits are only partially downloaded (first ~1 GB of each file,
``*.PARTIAL_first1GB.jsonl``, base64 screenshots) and are NOT loaded here.
Row: {id, framework, benchmark, task, trajectory, ground_truth, extras} with the last four JSON-encoded.
subset = framework; category = ground_truth.mode (taxonomy code, name in meta.mode_name).

Steps.  Every native trajectory entry becomes a step (framing entries included, so nothing is
dropped): ``kind == 'user'`` -> role user (native_idx 'user'); ``kind == 'system'`` -> role system
(native_idx 'system'); ``kind == 'final_answer'`` -> role system, agent 'final_answer'
(native_idx 'final_answer'); MathChat's bootstrap user_proxy turn (round 0, position 0) -> role
user (native_idx 'input', not scorable, as in the official renderer).  Scorable steps carry the
official harness's step coordinate (whowhen_eval/render/*.py, score.py) as ``native_idx`` and
``meta.scorable = True``:
  smolagents    cursor over planning/action entries: 0 if the first is a planning entry else 1
                (gt.step identity)
  alfagent      action step_number, 1-based (gt.step identity)
  mathchat      2*round+position (gt.round/position)
  metagpt       stage 0/1/2 (gt.stage)
  macnet        'R.P' from role: author 0.0, critic 1.0, rewriter 1.1, sink 2.0 (gt.round.position)
  magentic-one  'R.P' = round.position of kind=='agent' entries (gt.step is that string)
  debate/dylan  'R.P' (debate: P = index in round.turns; dylan: P = turn.position)
                gt gives round + agents (list)
  dvd / eva     native trajectory index (gt.step is that index; the official renderers show it as
                index-2 for dvd and (index-2)//2 for eva; we keep tool turns as separate steps
                (role tool / agent 'frame_inspect_agent' for dvd's VLM sub-agent) instead of
                folding them -- the official EVA renderer folds the tool turn into the assistant step)
Label mapping: faulty_step = the step whose native_idx equals the gt coordinate; for debate/dylan
faulty_steps = all turns in gt.round whose agent is in gt.agents (faulty_step = the first of them;
the official scorer accepts any turn of the round -> extra.accepted_steps_official).
Leakage: the native flags is_injected / injected / is_replayed / is_live / phase / injection_via
(and the magentic ledger dict) are removed from content and stored in step meta.  ``accepted_predictions``
(MacNet alternates) and the agent roster are kept in annotation.extra / meta.
"""
import json
import os
import re

SLUG = "who_and_when_pro"
DATA_DIR = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/who_and_when_pro"
SPLITS = ["text", "video"]
FLAG_KEYS = ("is_injected", "injected", "is_replayed", "replayed", "is_live", "phase", "injection_via")
SINGLE_AGENT = {"smolagents", "alfagent", "eva", "openai_cua", "agentoccam", "gemini"}
_MACNET_COORD = {"author": "0.0", "critic": "1.0", "rewriter": "1.1", "sink": "2.0"}
_TAX = None


def _taxonomy():
    global _TAX
    if _TAX is None:
        _TAX = {}
        try:
            with open(os.path.join(DATA_DIR, "taxonomy.yaml"), encoding="utf-8") as f:
                for m in re.finditer(r"^([A-Z]+\.\d+):\n\s+name:\s*(.+)$", f.read(), re.M):
                    _TAX[m.group(1)] = m.group(2).strip()
        except OSError:
            pass
    return _TAX


def _J(x):
    return json.loads(x) if isinstance(x, str) else x


def _s(x):
    if x is None:
        return ""
    return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)


def _flags(e):
    return {k: e[k] for k in FLAG_KEYS if k in e}


def _tool_call_str(tc):
    name = tc.get("name") or (tc.get("function") or {}).get("name")
    args = tc.get("arguments") if "arguments" in tc else (tc.get("function") or {}).get("arguments")
    if isinstance(args, dict):
        args = {k: v for k, v in args.items() if k != "database"}
        args = json.dumps(args, ensure_ascii=False)
    elif isinstance(args, str) and '"database"' in args:
        try:
            d = json.loads(args)
            args = json.dumps({k: v for k, v in d.items() if k != "database"}, ensure_ascii=False)
        except ValueError:
            pass
    return f"[tool_call] {name}({args})"


def _step(native_idx, agent, role, content, meta=None, scorable=True):
    m = {"scorable": scorable}
    if meta:
        m.update(meta)
    return {"native_idx": native_idx, "agent": agent, "role": role, "content": content, "meta": m}


def _framing(e):
    k = e.get("kind")
    if k == "user":
        return _step("user", "user", "user", _s(e.get("content")), scorable=False)
    if k == "system":
        return _step("system", "system", "system", _s(e.get("content")), scorable=False)
    if k == "final_answer":
        return _step("final_answer", "final_answer", "system", _s(e.get("content")), scorable=False)
    return None


def _steps_of(fw, traj):
    steps = []
    if fw == "smolagents":
        cursor = None
        for e in traj:
            fr = _framing(e)
            if fr:
                steps.append(fr); continue
            k = e.get("kind")
            if cursor is None:
                cursor = 0 if k == "planning" else 1
            if k == "planning":
                steps.append(_step(cursor, "agent", "agent", f"[plan]\n{_s(e.get('plan')).strip()}\n[/plan]", {"kind": "planning"}))
            else:
                reasoning = _s(e.get("reasoning")).strip()
                parts = []
                if reasoning:
                    parts.append(f"[output]\n{reasoning}\n[/output]")
                code = _s(e.get("code")).strip()
                if code and code not in reasoning:
                    parts.append(f"[code]\n{code}\n[/code]")
                obs = _s(e.get("observation")).strip()
                if obs:
                    parts.append(f"[observation]\n{obs}\n[/observation]")
                err = _s(e.get("error")).strip()
                if err and err not in obs:
                    parts.append(f"[error]\n{err}\n[/error]")
                steps.append(_step(cursor, "agent", "agent", "\n".join(parts) if parts else "(empty step)",
                                   {"kind": k, "step_number": e.get("step_number"), "is_final_answer": e.get("is_final_answer"),
                                    "n_observation_images": len(e.get("observation_images") or []), **_flags(e)}))
            cursor += 1
    elif fw == "alfagent":
        for e in traj:
            fr = _framing(e)
            if fr:
                steps.append(fr); continue
            parts = []
            for tag, key in (("think", "reasoning"), ("action", "action"), ("observation", "observation")):
                v = _s(e.get(key)).strip()
                if v:
                    parts.append(f"[{tag}]\n{v}\n[/{tag}]")
            steps.append(_step(e.get("step_number"), "agent", "agent", "\n".join(parts) if parts else "(empty step)",
                               {"kind": e.get("kind"), "is_final_answer": e.get("is_final_answer"), **_flags(e)}))
    elif fw == "mathchat":
        for e in traj:
            fr = _framing(e)
            if fr:
                steps.append(fr); continue
            r, p = e.get("round"), e.get("position")
            agent = str(e.get("agent_id") or "unknown")
            out = _s(e.get("output"))
            meta = {"round": r, "position": p, "native_role": e.get("role"), **_flags(e)}
            if r == 0 and p == 0 and agent == "user_proxy":
                steps.append(_step("input", agent, "user", out, meta, scorable=False))
            else:
                steps.append(_step(2 * int(r) + int(p), agent, "agent" if agent != "user_proxy" else "tool", out, meta))
    elif fw == "metagpt":
        for e in traj:
            fr = _framing(e)
            if fr:
                steps.append(fr); continue
            steps.append(_step(int(e.get("stage")), str(e.get("agent_id") or "unknown"), "agent", _s(e.get("output")),
                               {"native_role": e.get("role"), **_flags(e)}))
    elif fw == "macnet":
        n_inner = 0
        for e in traj:
            fr = _framing(e)
            if fr:
                steps.append(fr); continue
            role = str(e.get("role"))
            coord = _MACNET_COORD.get(role)
            if coord is None:
                coord = f"1.{n_inner}"
            if coord.startswith("1."):
                n_inner += 1
            steps.append(_step(coord, str(e.get("agent_id") or "unknown"), "agent", _s(e.get("output")),
                               {"native_role": role, "stage": e.get("stage"), **_flags(e)}))
    elif fw in ("magentic-one", "magentic"):
        for e in traj:
            fr = _framing(e)
            if fr:
                steps.append(fr); continue
            if e.get("kind") != "agent":
                continue
            coord = f"{e.get('round')}.{e.get('position')}"
            out = _s(e.get("output")).strip()
            parts = [f"[output]\n{out}\n[/output]"] if out else []
            if e.get("tool_actions"):
                parts.append("[tool_actions]\n" + json.dumps(e["tool_actions"], ensure_ascii=False, indent=2) + "\n[/tool_actions]")
            meta = {"native_role": e.get("role"), "round": e.get("round"), "position": e.get("position"), **_flags(e)}
            if "ledger" in e:
                meta["ledger"] = e.get("ledger")
            steps.append(_step(coord, str(e.get("agent") or "unknown"), "agent", "\n".join(parts) if parts else "(empty turn)", meta))
    elif fw in ("debate", "dylan"):
        for e in traj:
            fr = _framing(e)
            if fr:
                steps.append(fr); continue
            if e.get("kind") != "round":
                continue
            r = int(e.get("round", 0))
            for pos, t in enumerate(e.get("turns") or []):
                p = int(t.get("position", pos)) if fw == "dylan" else pos
                steps.append(_step(f"{r}.{p}", str(t.get("agent_id") or "unknown"), "agent", _s(t.get("output")),
                                   {"round": r, "position": p, "native_role": t.get("role"), **_flags(t)}))
    elif fw in ("dvd", "eva"):
        for i, e in enumerate(traj):
            k = e.get("kind")
            fr = _framing(e)
            if fr:
                steps.append(fr); continue
            if k == "assistant":
                c = _s(e.get("content")).strip()
                parts = [f"[output]\n{c}\n[/output]"] if c else []
                for tc in e.get("tool_calls") or []:
                    parts.append(_tool_call_str(tc))
                steps.append(_step(i, "orchestrator" if fw == "dvd" else "agent", "agent", "\n".join(parts) if parts else "(empty assistant turn)",
                                   {"kind": k, **_flags(e)}))
            elif k == "tool":
                name = e.get("tool_name") or "?"
                c = _s(e.get("content")).strip()
                frames = e.get("frames") or []
                meta = {"kind": k, "tool_name": name, "tool_call_id": e.get("tool_call_id"), "n_frames": len(frames),
                        "frames": [{"index": f.get("index"), "time_s": f.get("time_s"), "path": f.get("path")} for f in frames] or None, **_flags(e)}
                if fw == "dvd" and name == "frame_inspect_tool":
                    steps.append(_step(i, "frame_inspect_agent", "agent", f"[output]\n{c}\n[/output]", meta))
                else:
                    steps.append(_step(i, f"tool:{name}", "tool", f"[tool_result tool={name}]\n{c}\n[/tool_result]", meta))
            else:
                steps.append(_step(i, str(k), "env", _s(e.get("content")), {"kind": k, **_flags(e)}))
    else:
        raise ValueError(f"unsupported framework {fw!r} (image / image_gui frameworks are not loaded)")
    for i, s in enumerate(steps):
        s["idx"] = i
    return steps


def _gt_coord(fw, gt):
    if fw == "mathchat":
        return 2 * int(gt["round"]) + int(gt["position"])
    if fw == "metagpt":
        return int(gt["stage"])
    if fw == "macnet":
        return f"{gt['round']}.{gt['position']}"
    if fw in ("smolagents", "alfagent", "dvd", "eva"):
        return int(gt["step"]) if gt.get("step") is not None else None
    if fw in ("magentic-one", "magentic"):
        return str(gt.get("step"))
    return None


def _convert(split, r):
    fw = r["framework"]
    gt = _J(r["ground_truth"]) or {}
    traj = _J(r["trajectory"]) or []
    ex = _J(r["extras"]) or {}
    task = _J(r["task"]) or {}
    steps = _steps_of(fw, traj)
    accepted_official = None
    if fw in ("debate", "dylan"):
        rd = int(gt["round"])
        agents = {str(a).lower() for a in (gt.get("agents") or ([gt["agent"]] if gt.get("agent") else []))}
        in_round = [s["idx"] for s in steps if s["meta"].get("scorable") and s["meta"].get("round") == rd]
        fsteps = [i for i in in_round if steps[i]["agent"].lower() in agents] or in_round
        fs = fsteps[0] if fsteps else None
        accepted_official = in_round
    else:
        coord = _gt_coord(fw, gt)
        fs = next((s["idx"] for s in steps if s["meta"].get("scorable") and s["native_idx"] == coord), None)
        fsteps = [fs] if fs is not None else []
    fa = gt.get("agent") or (",".join(gt["agents"]) if gt.get("agents") else None)
    if fa is None and fs is not None:
        fa = steps[fs]["agent"]
    mode = gt.get("mode")
    final = ex.get("final_answer") if isinstance(ex, dict) else None
    if final is None:
        final = next((s["content"] for s in steps if s["native_idx"] == "final_answer"), None)
    if final is None and fw in ("magentic-one", "magentic"):
        final = next((s["content"] for s in reversed(steps) if isinstance(s["meta"].get("phase"), list) and "final_answer" in s["meta"]["phase"]), None)
    if final is None and fw in ("dvd", "eva"):
        final = next((s["content"] for s in reversed(steps) if s["role"] == "agent"), None)
    roster = ex.get("agents") if isinstance(ex, dict) else None
    return {
        "dataset": SLUG, "id": r["id"], "subset": fw, "system": fw,
        "task": _s(task.get("query")) + (("\nOptions: " + _s(task.get("options"))) if task.get("options") else ""),
        "ground_truth": _s(task.get("answer")) if task.get("answer") is not None else None,
        "final_output": _s(final) if final is not None else None, "outcome": 0, "steps": steps,
        "annotation": {"faulty_step": fs, "faulty_steps": fsteps, "faulty_agent": fa, "category": mode, "reason": None,
                       "extra": {"ground_truth_raw": gt, "mode_name": _taxonomy().get(mode), "accepted_predictions": gt.get("accepted_predictions"),
                                 "accepted_predictions_note": gt.get("accepted_predictions_note"), "accepted_steps_official": accepted_official,
                                 "injected_steps": [s["idx"] for s in steps if s["meta"].get("is_injected") or s["meta"].get("injected")
                                                    or (isinstance(s["meta"].get("phase"), list) and "injected" in s["meta"]["phase"])],
                                 "labelled_step_agent": steps[fs]["agent"] if fs is not None else None}},
        "meta": {"split": split, "framework": fw, "benchmark": r.get("benchmark"), "single_agent": fw in SINGLE_AGENT,
                 "agents": roster, "n_scorable_steps": sum(1 for s in steps if s["meta"].get("scorable")),
                 "extras": {k: v for k, v in ex.items() if k != "agents"} if isinstance(ex, dict) else ex,
                 "task_images": len(task.get("images") or [])},
    }


def load(limit=None, subset=None):
    n = 0
    for split in SPLITS:
        path = os.path.join(DATA_DIR, "data", f"{split}.jsonl")
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if subset and r.get("framework") != subset:
                    continue
                if limit is not None and n >= limit:
                    return
                yield _convert(split, r)
                n += 1
