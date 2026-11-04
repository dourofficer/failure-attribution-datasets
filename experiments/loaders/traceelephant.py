"""Loader for TraceElephant (HF TraceElephant/TraceElephant) -> unified trajectory schema.

Files: data/traceelephant/extracted/data/<system-benchmark dir>/<run_id>/{trace_metadata.json,
step_records.json, images/}.  Dirs: captain-runs-gaia, captain-runs-assistantbench,
magentic-runs-gaia, magentic-runs-assistant-bench, swe-agent-runs-swe-bench (220 failed runs).

Steps / index mapping
---------------------
* One step per record of ``step_records.json`` = one LLM call.  ``step_id`` is 1-based and
  contiguous, so ``idx = step_id - 1`` and ``native_idx = step_id``.  Every step has role
  ``agent`` (an LLM decision); ``agent`` = ``agent_name`` (for SWE-Agent that is the tool the
  single agent chose: str_replace_editor / bash / submit).
* ``mistake_step`` is the 1-based ``step_id`` stored as a string; ``faulty_step = int - 1``.
  Irregular values: ``'none'`` (assistant_bench_task_26: no decisive step -> faulty_step None,
  faulty_steps []) and ``'Step 36'`` (digits are extracted -> 36).

Content rendering (each call's ``input.messages`` repeats the whole context, so the input is
NOT dumped):
  ``[input <role|name>]`` blocks: the messages of this step's input that have not been seen in any
  earlier step's input or output (text compared after normalising image placeholders) -- i.e. the
  NEW tool results / observations / peer messages / framework prompts that reached the model at
  this step (the system prompt and task appear once, in the first step where they occur; a later
  message whose text exactly repeats an earlier one is therefore not rendered again);
  ``[output]``: the assistant text of this call; ``[tool_call] name(arguments)``: its tool calls
  (from ``output.tool_calls``, else ``tool_logs``).  Image parts are rendered as
  ``[image <file>]``; the PNGs live in ``<run>/images/`` (listed in step meta).
Step meta: agent_id, n_input_messages, n_new_input_messages, usage (tokens), images.
subset = the system-benchmark directory name; system = ``system_name``;
ground_truth = metadata ``ground_truth`` (absent for SWE-Bench: ``tests_status`` in meta).
"""
import glob
import json
import os
import re

SLUG = "traceelephant"
ROOT = "/dataDisk/home/thanhdo/failure-attribution-datasets/data/traceelephant/extracted/data"
SUBSETS = ["captain-runs-assistantbench", "captain-runs-gaia", "magentic-runs-assistant-bench", "magentic-runs-gaia", "swe-agent-runs-swe-bench"]
BENCH = {"captain-runs-assistantbench": "AssistantBench", "captain-runs-gaia": "GAIA", "magentic-runs-assistant-bench": "AssistantBench",
         "magentic-runs-gaia": "GAIA", "swe-agent-runs-swe-bench": "SWE-Bench Verified"}
_IMG_RE = re.compile(r"\{'type': 'image', 'image_file': '[^']*'\}|<image>|\[image[^\]]*\]")
_WS_RE = re.compile(r"\s+")


def _msg_text(content):
    """Readable text of a message content (str or list of parts)."""
    if content is None:
        return "", []
    if isinstance(content, str):
        return content, []
    if isinstance(content, list):
        parts, imgs = [], []
        for p in content:
            if isinstance(p, dict):
                t = p.get("type")
                if t == "text":
                    parts.append(p.get("text") or "")
                elif t == "image":
                    f = p.get("image_file") or p.get("path") or ""
                    imgs.append(f)
                    parts.append(f"[image {f}]" if f else "[image]")
                elif t == "image_url":
                    imgs.append("inline")
                    parts.append("[image]")
                else:
                    parts.append(json.dumps(p, ensure_ascii=False))
            else:
                parts.append(str(p))
        return "\n".join(parts), imgs
    return json.dumps(content, ensure_ascii=False), []


def _key(text):
    return _WS_RE.sub(" ", _IMG_RE.sub("<image>", text)).strip()


def _tool_call_str(tc):
    fn = tc.get("function") or {}
    name = fn.get("name") or tc.get("name")
    args = fn.get("arguments") if "function" in tc else tc.get("arguments")
    if not isinstance(args, str):
        args = json.dumps(args, ensure_ascii=False)
    return f"[tool_call] {name}({args})"


def parse_step(v):
    s = "".join(ch for ch in str(v) if ch.isdigit())
    return int(s) if s else None


def _convert(sub, run_dir):
    with open(os.path.join(run_dir, "trace_metadata.json"), encoding="utf-8") as f:
        meta = json.load(f)
    with open(os.path.join(run_dir, "step_records.json"), encoding="utf-8") as f:
        recs = json.load(f)
    seen = set()
    steps = []
    for i, st in enumerate(recs):
        msgs = (st.get("input") or {}).get("messages") or []
        new_blocks, images = [], []
        n_new = 0
        for m in msgs:
            text, imgs = _msg_text(m.get("content"))
            k = _key(text)
            if k and k in seen:
                continue
            if k:
                seen.add(k)
            n_new += 1
            label = m.get("name") or m.get("role") or "message"
            if m.get("name") and m.get("role") and m["role"] not in ("user", "assistant"):
                label = f"{m['role']}/{m['name']}"
            extra = ""
            if m.get("tool_calls"):
                extra = "\n" + "\n".join(_tool_call_str(tc) for tc in m["tool_calls"])
            new_blocks.append(f"[input {label}]\n{text}{extra}")
            images.extend(imgs)
        try:
            out_msg = st["output"]["choices"][0]["message"]
        except (KeyError, IndexError, TypeError):
            out_msg = {}
        out_text, _ = _msg_text(out_msg.get("content"))
        if out_text.strip() in ("null", "None"):
            out_text = ""
        calls = out_msg.get("tool_calls") or st.get("tool_logs") or []
        if out_text:
            seen.add(_key(out_text))
        parts = list(new_blocks)
        if out_text:
            parts.append(f"[output]\n{out_text}")
        for tc in calls:
            if isinstance(tc, dict):
                parts.append(_tool_call_str(tc))
        usage = (st.get("output") or {}).get("usage") or {}
        steps.append({"idx": i, "native_idx": st.get("step_id", i + 1), "agent": str(st.get("agent_name") or ""), "role": "agent",
                      "content": "\n".join(parts),
                      "meta": {"agent_id": st.get("agent_id"), "n_input_messages": len(msgs), "n_new_input_messages": n_new,
                               "usage": usage if usage else None, "images": images or None, "finish_reason": (st.get("output") or {}).get("choices", [{}])[0].get("finish_reason") if (st.get("output") or {}).get("choices") else None}})
    ms_raw = meta.get("mistake_step")
    k = parse_step(ms_raw)
    fs = k - 1 if k is not None and 1 <= k <= len(steps) else None
    final = None
    for s in reversed(steps):
        if "FINAL ANSWER" in s["content"]:
            final = s["content"].split("[output]", 1)[-1] if "[output]" in s["content"] else s["content"]
            break
    if final is None and steps:
        last = steps[-1]["content"]
        final = last.split("[output]", 1)[-1] if "[output]" in last else None
    return {
        "dataset": SLUG, "id": f"{sub}/{os.path.basename(run_dir)}", "subset": sub, "system": meta.get("system_name") or "",
        "task": meta.get("task_instruction") or "", "ground_truth": meta.get("ground_truth"), "final_output": final, "outcome": 0, "steps": steps,
        "annotation": {"faulty_step": fs, "faulty_steps": [fs] if fs is not None else [], "faulty_agent": meta.get("mistake_agent"),
                       "category": None, "reason": meta.get("mistake_reason"),
                       "extra": {"mistake_step_raw": ms_raw, "labelled_step_agent": steps[fs]["agent"] if fs is not None else None}},
        "meta": {"task_id": meta.get("task_id"), "run_id": meta.get("run_id"), "benchmark": BENCH.get(sub), "dir": os.path.relpath(run_dir, ROOT),
                 "tests_status": meta.get("tests_status"), "agent_configuration": meta.get("agent_configuration"),
                 "agent_system_intro": meta.get("agent_system_intro"), "n_images": len(glob.glob(os.path.join(run_dir, "images", "*.png")))},
    }


def load(limit=None, subset=None):
    subs = [subset] if subset else SUBSETS
    n = 0
    for sub in subs:
        for run_dir in sorted(glob.glob(os.path.join(ROOT, sub, "*"))):
            if not os.path.isdir(run_dir):
                continue
            if limit is not None and n >= limit:
                return
            yield _convert(sub, run_dir)
            n += 1
