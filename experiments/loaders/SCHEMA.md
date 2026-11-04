# Unified trajectory schema for the experiments

Every loader in `experiments/loaders/<slug>.py` exposes

```python
SLUG = "<slug>"
def load(limit=None, subset=None):  # -> iterator of Trajectory dicts, deterministic order
```

and yields dicts of this shape (validated by `loaders/schema.py: validate(traj)`):

```python
{
  "dataset": "<slug>",
  "id": "<unique within the dataset; use the dataset's own id/filename>",
  "subset": "<split/source/system the dataset itself distinguishes, e.g. 'hand_crafted', 'tau2bench', 'webarena_verified'; '' if none>",
  "system": "<agent framework, e.g. 'Magentic-One', 'CaptainAgent', 'SWE-Agent'; '' if unknown>",
  "task": "<the task / question text>",
  "ground_truth": "<reference answer or None>",
  "final_output": "<the system's final answer / output or None>",
  "outcome": 0 | 1 | None,          # 1 = task succeeded, 0 = failed, None = unknown. Failed-only datasets: 0.
  "steps": [
    {
      "idx": 0,                      # OUR index: position in this list, 0-based, contiguous
      "native_idx": <int|str>,       # the dataset's own index/coordinate for this step (whatever the label refers to)
      "agent": "<agent/role name as the dataset gives it; normalised only for casing/whitespace>",
      "role": "agent" | "tool" | "user" | "system" | "env",   # agent = an LLM-backed decision; tool/env = tool return or environment observation; user = human/simulated user; system = system prompt or framework bookkeeping
      "content": "<full text of the step (do NOT truncate); for structured steps (tool calls + args + result) render them in a readable text form>",
      "meta": {}                     # optional: tool name, phase, span kind, token counts, etc.
    }, ...
  ],
  "annotation": {
    "faulty_step": <idx or None>,    # the single primary label the dataset defines (earliest decisive / critical / responsible step), expressed in OUR idx
    "faulty_steps": [idx, ...],      # all labelled steps when the label is a set (MP-Bench union, AgentRx events, TRAIL spans, SymFail node); [faulty_step] if single; [] if none
    "faulty_agent": "<as given or derived from steps[faulty_step].agent; None if not applicable>",
    "category": "<failure-mode / taxonomy label, None if none>",
    "reason": "<free-text rationale, None if none>",
    "extra": {}                      # everything else the dataset gives: per-annotator votes, event lists with categories, t_lock/t_obs, tolerance spans, impact, ideal_action, consensus rates, injected flags, ...
  },
  "meta": {}                         # model backbone, benchmark, level, file path, licence notes, ...
}
```

Rules
- `annotation.faulty_step` MUST be a valid `steps[].idx` (or None). Document in the module docstring exactly how the native label was mapped (0/1-based, which entries count as steps, composite coordinates such as Who&When Pro "R.P").
- Keep every entry of the native trajectory as a step (orchestrator thoughts, tool returns, user turns) so that nothing the annotator saw is lost; mark the kind with `role`. Do not merge or drop steps unless the dataset's official evaluation does so (then say so in the docstring).
- `content` must be complete. Rendering of structured steps: e.g. `"[tool_call] search({...})\n[tool_result] ..."`.
- Loaders must be stdlib-only where possible (pandas/pyarrow allowed via `sys.path.append('/dataDisk/home/thanhdo/.local/lib/python3.10/site-packages')` for parquet). Run with `python3 -I`.
- Paths are absolute under `/dataDisk/home/thanhdo/failure-attribution-datasets/data/`. The report sections `report/<group>/<slug>/<slug>.tex` and the notes `notes/<slug>.md` describe each dataset's files and schema; the scripts `scripts/analyze_<slug>.py` already parse them and can be copied from.
- If a dataset has successful trajectories too (AgentHallu clean runs, HORIZON successes, TRAIL unselected), load them as well with `outcome=1` and empty annotation.
- Big files: load lazily; `limit` must stop early without reading everything.
