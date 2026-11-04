# experiments/

Inspection of the 19 downloadable failure-attribution datasets with a local judge model, to form hypotheses about
what makes step-level attribution hard. Findings live in `findings/` (`hypotheses.md` = the deliverable, `worklog.md`
= raw observations in order of discovery).

Layout
- `vllm/serve.sh` — Qwen3.8-27B on one H200 (GPU 5, port 8210, 200k context). `vllm/pyshim/` is a private copy of
  mpmath with one module renamed because this sandbox hides files named `libhyper*` from directory listings.
- `common/llm.py` — OpenAI-compatible client with an sqlite cache (`cache/llm_cache.sqlite`); `common/render.py` —
  trajectory → prompt text with a character budget (per-step head/tail trimming, step numbers preserved).
- `loaders/` — one module per dataset producing the unified schema in `loaders/SCHEMA.md` (validated by
  `schema.py`, smoke-tested by `check_loader.py <slug>`); `REGISTRY.py` lists the slugs. Index-mapping rules and the
  label quirks found while parsing are in each module docstring.
- `baseline/all_at_once.py` — the Who&When all-at-once prompt (`--variant std`), an error-inventory prompt that tags
  every mistake recovered/fatal (`inventory`), an outcome-blind inventory for successful runs too (`inventory_blind`);
  `--anonymise` renames agents; `--ids` restricts to a list. Outputs in `baseline/out/<slug>__<variant>.jsonl`.
  `score.py` (exact/±k/agent/in-set/earlier-later), `slice.py` (accuracy by category, position, repeat block, rationale
  tag, vote count), `analyze_inventory.py` (joins std + inventory for the recovered-error question).
  `run_queue_*.sh` are the batch scripts that were run; `watch.sh` the progress filter.
- `inspect/` — annotation-only analyses: `tag_reasons.py` (LLM tags on every rationale), `repeat_blocks.py`,
  `obs_signals.py`, `priors.py`, `wwpro_length_shortcut.py`; outputs in `inspect/out/`.

Run everything with `python3 -I` from this directory.
