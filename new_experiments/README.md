# new_experiments — dataset inspection and hypothesis formation (Nov 2026)

Goal: inspect the downloaded failure-attribution datasets (`../data/`), read the literature, and form
hypotheses about *systematic phenomena* that make step-level failure attribution hard. Findings go to
`findings/`; literature notes to `lit/`; code here. `../experiments/` is deprecated and must not be read.

Layout
```
common/    schema.py (unified record), llm.py (cached client for the local vLLM server), render.py (prompt rendering), util.py
loaders/   one module per dataset slug exposing load() -> list[record]; registry in loaders/__init__.py
baseline/  all_at_once.py — generic prompting baseline on any loader; writes results/<slug>/*.jsonl
inspect/   per-dataset / cross-dataset analysis scripts (statistics beyond length and position)
results/   baseline predictions (jsonl) and metric summaries
findings/  datasets/<slug>.md (per-dataset notes), hypotheses.md (synthesis), worklog.md
lit/       literature notes with verified arXiv ids
cache/     llm_cache.sqlite (prompt-keyed cache; delete to re-run)
```

Conventions
- Run everything with `python3 -I <script>` from this directory (`-I` because the data are downloaded archives). `-I` drops the
  script dir and cwd from sys.path, so every entry-point script starts with
  `sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))` before importing `common`/`loaders`.
  `common/util.py` adds the user site-packages (pandas / pyarrow) to `sys.path` explicitly.
- LLM: Qwen3.8-27B served by vLLM at `http://localhost:8210/v1`, model name `qwen3.8-27b`, 200k context,
  thinking on by default (`reasoning_content`). `common/llm.py` caches every call in `cache/llm_cache.sqlite`.
- Step indices in records are 0-based positions in `steps`; `labels.error_steps` uses the same indices.
  Each step keeps the dataset's native index in `native_step` so numbers can be mapped back to the paper's convention.
- Never write into `../report/` or `../experiments/`.

Shared tooling (do not modify; add new scripts under inspect/ instead)
- `baseline/all_at_once.py <slug> [--variant std|inventory] [--n N | --ids a,b] [--no-gt] [--mask-last K] [--budget-tokens T]`
  all-at-once attribution; results/<slug>/all_at_once_<variant>.jsonl with pred, raw, reasoning, per-record scores.
- `inspect/analyze_baseline.py <slug> [name]` categorises misattributions (later/earlier/agent/parse) and dumps reasoning
  excerpts to results/<slug>/<name>_analysis.md.
- `inspect/prefix_probe.py <slug> [--n N | --ids] [--max-steps M] [--window W]` prefix-only monitor: asks "is the latest step a
  mistake?" for every agent step with only steps 0..k visible (no outcome, no ground truth). Measures local detectability
  of the labelled step, false-flag rates before/after the label, earliest-flagged vs label. ~1 call per probed step.
- `common/llm.py: chat_json()/chat_json_many()` return (parsed_json, out); they retry without thinking when the thinking
  overruns max_tokens (field out['fallback']). Thinking is on by default; cache key includes the think flag.

Status (2026-11-01)
- Deliverable: `findings/hypotheses.md` (cross-dataset synthesis: phenomena X1–X12, hypotheses H1–H13, P1–P8 verdicts,
  experiment programme). Group syntheses: `findings/groups/g1..g4`. Per-dataset: `findings/datasets/<slug>.md`.
- Literature: `lit/known_phenomena.md`. Baseline/probe tables: `python3 -I inspect/summarize_baselines.py`,
  `python3 -I inspect/summarize_probes.py`. All LLM calls are cached in `cache/llm_cache.sqlite`.
- Two vLLM servers were used (:8210 on GPU 5, :8211 on GPU 3, `vllm/serve_second.sh`); `common/llm.py` picks the less loaded one.
