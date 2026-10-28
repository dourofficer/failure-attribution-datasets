# TrajErrBench — TrajDebug

## Identity

- **Full title:** *TRAJDEBUG: Tracing Error Lifecycle to Identify Critical Failures in Long-Horizon Agent Trajectories*. Dataset: **TrajErrBench**.
- **Authors / affiliation:** Yunjia Qi, Zehua Yin, Xintong Shi, Hao Peng, Songyuanyi Lu, Yixian Liu, Richeng Xuan, Yuhong Liu, Zhichao Hu, Xiaozhi Wang, Lei Hou, Bin Xu, Juanzi Li — Tsinghua University (THU-KEG), with co-authors from industry.
- **Venue:** Findings of EMNLP 2026 (accepted 2026-08-20 per the repo). arXiv **2608.06346** (v1, 6 Aug 2026, cs.AI).
- **Links:** paper https://arxiv.org/abs/2608.06346 · code + data https://github.com/THU-KEG/TrajDebug (`data/trajerrbench/`; English edition released 2026-09-07) · the repo also redistributes Who&When (184) and AgentErrorBench (200) in the same unified schema.
- **License:** MIT for the TrajDebug code and original annotations (`LICENSE`, `CITATION.cff`); task text / trajectories remain under τ²-Bench and SWE-Bench Pro terms (see `data/README.md`).
- **Availability:** **downloaded** (git clone, 486 zh + 486 en files, complete).
- **On-disk size:** 215 MB for the clone — `data/trajerrbench/` 63 MB (en 32 MB + zh 31 MB), `data/agentdebugbench/` 78 MB, `data/whoandwhen/` 7.5 MB, `main.pdf`, code, outputs.
- **Local path:** `/dataDisk/home/thanhdo/failure-attribution-datasets/data/trajerrbench/repo_TrajDebug/` (`data/trajerrbench/{en,zh}/{tau2bench,swebenchpro}/*.json`, `data/trajerrbench/manifest.jsonl`).

## Description

- **Purpose.** Benchmark for **critical error (step) detection** in long-horizon single-agent trajectories: the critical error step is the *earliest decisive error* — a step whose action, if replaced by a correct one (all earlier steps fixed, later steps unfolding correctly), would have turned the failure into a success (counterfactual definition from Who&When). Detection is done from the failed trajectory alone (no task ground truth).
- **Construction (natural failures).** Two domains: **400 τ²-Bench** rollouts (airline + retail customer-service tool-use tasks with a simulated user) produced by DeepSeek-Reasoner, GPT-5 and Qwen3-Max; **86 SWE-Bench Pro** rollouts (repository-level issue fixing in the OpenHands scaffold) produced by Claude-Opus-4.6, Kimi-K2.6-Coding, Gemini-3.1-Pro and Grok-4.20-Beta (GPT-5.4 is listed in the paper but does not appear among the released ids). Failed runs are those with reward 0 under the original benchmark evaluation. Averages: 29.3 and 119.7 steps.
- **Annotation protocol.** Follows Who&When's decisive-error practice. Model-assisted pre-annotation by GPT-5.4, Gemini-3.1-Pro and Claude-Opus-4.6 (given the trajectory *plus* the benchmark's failure details — unmet DB constraints for τ²-Bench, failing tests for SWE-Bench Pro) is shown to annotators as reference; a pool of **20 trained annotators**, **3 per trajectory**, majority vote (≥2/3) defines the label. Guideline: (1) the step must contain an explicit, evidence-supported mistake; (2) it must be failure-responsible (locally repaired mistakes excluded); (3) if several, pick the earliest. SWE-Bench Pro started with 110 trajectories; 24 with no 2-way agreement were dropped. Each annotator wrote a short explanation, but these are **not shipped**.
- **Inter-annotator agreement (Table 5):** critical step Fleiss' κ = 0.91 (pairwise 91.2 %) on τ²-Bench, 0.67 (66.7 %) on SWE-Bench Pro; execution phase κ = 0.73 / 0.42; reference category κ = 0.41 / 0.38. Pre-annotation exact-match with final labels: Claude 64.5 %, Gemini 76.8 %, GPT-5.4 53.2 % (τ²); 48.8 / 31.4 / 55.8 % (SWE-Pro).
- **Labels:** `critical_error_step` (0-based unified message index; always an assistant message except one tool message in the release), `critical_error_type` = `<module>.<subtype>` from the TrajDebug taxonomy (None when not mappable: 17 cases). The paper additionally annotates an *execution phase* (planning / reasoning / action / observation / verification) and a *contradiction reference category* (Task Conflict / History Conflict / Intra-Step Conflict); the phase is recoverable from the type prefix, the reference category is not in the release.
- **Taxonomy (`detector/utils/taxonomy.md`, 5 modules / 20 subtypes):** PLAN: BadDecomposition, WrongOrder, UnrealisticPlan, GoalDrift, OverExplore · REASON: WrongChoice (evidence visible but ignored/misquoted), InvalidInference (evidence cited correctly but over-reaching conclusion), MissingAssumptionCheck (claim with no supporting evidence) · ACT: WrongTool, ToolSchemaMismatch, WrongActionSequence, UnsafeOrForbiddenAction · OBS: MisreadOutput, IgnoreOutput, TimingIssue, GroundingFail · VERIFY: NoVerification, WrongVerification, PrematureTermination, InfiniteRetry.
- **Task & metrics:** exact-step accuracy (`detector/score_steps.py`), plus a relaxed window [GT−3, GT] in Appendix E; the paper evaluates on the **zh edition**. Baselines: direct prompting with 7 LLMs, AgentDebugger (AgentDebug), CHIEF, AgentRx. TrajDebug = multi-granularity compression → error trigger detection → error state classification (resolved vs. terminal impact) → candidate-set-guided causal attribution.
- **Reported results (Table 1, step accuracy %):**

| Method | ALFWorld | GAIA | WebShop | W&W Hand | W&W Algo | τ²-Bench | SWE-Bench Pro | AVG |
|---|---|---|---|---|---|---|---|---|
| Direct Prompting (best of 7: Gemini-3.1-Pro) | 19.0 | 30.6 | 32.0 | 20.7 | 46.8 | 52.5 | 17.4 | 31.3 |
| Direct Prompting GPT-5.4 | 11.0 | 20.4 | 14.0 | 13.8 | 28.6 | 41.5 | 10.5 | 20.0 |
| AgentDebugger | 21.0 | 36.0 | 20.0 | 12.1 | 40.5 | 26.0 | 10.5 | 23.7 |
| CHIEF | 6.0 | 26.0 | 10.0 | 19.0 | 41.3 | 26.8 | 2.3 | 18.8 |
| AgentRx | 8.0 | 26.5 | 18.0 | 25.9 | 41.3 | 36.3 | 5.8 | 23.1 |
| TrajDebug | 26.0 | 38.8 | 26.0 | 22.4 | 48.4 | 52.8 | 24.4 | 34.1 |

## Schema

One JSON file per trajectory (unified TrajDebug schema, `data_processing/schema.py`):

- `messages` (list) — `step` (int, 0-based, equals array index), `role` (`system`/`user`/`assistant`/`tool`), `name` (original speaker label; here equal to the role), `content` (str; assistant tool calls are rendered as `[tool_calls]\n- fn({json})`), `judgable` (bool, whether the step can be the critical step), `compress_role` (`preserve`/… hint for the detector's compression).
- `metadata.dataset` = `trajerrbench`; `metadata.task_id` (τ²: `<domain>_failed_<model>::<uuid>`; SWE-Pro: `<model>_instance_<repo>-<commit>-v<hash>`); `metadata.task_description` (the user's first request / issue text); `metadata.reward` (0 for all); `metadata.annotation.critical_error_step` (int), `metadata.annotation.critical_error_type` (str or null); `metadata.extra` — `agent_framework_description` (long natural-language description of the environment and annotation conventions used by the detector prompt), `language` (`en`/`zh`), `source_benchmark`, `pair_id`.
- `manifest.jsonl` — 486 lines `{pair_id, source_benchmark, task_id, zh_path, en_path}` pairing the two editions (labels and message counts are identical: 0 mismatches found).

## Statistics (computed from the English edition; 486 trajectories, all failed)

| quantity | n | mean | median | min | max | p10 | p90 |
|---|---|---|---|---|---|---|---|
| messages per trajectory (all, en) | 486 | 45.18 | 29.0 | 7 | 202 | 21 | 112 |
| messages per trajectory (τ²-Bench) | 400 | 29.27 | 27.0 | 7 | 202 | 19 | 41 |
| messages per trajectory (SWE-Bench Pro) | 86 | 119.17 | 117.0 | 58 | 180 | 82 | 160 |
| assistant steps per trajectory (all) | 486 | 21.54 | 14.0 | 3 | 101 | 9 | 55 |
| tool messages per trajectory (all) | 486 | 17.3 | 9.0 | 1 | 89 | 5 | 54 |
| critical step index (0-based message idx) | 486 | 26.95 | 19.0 | 2 | 160 | 9 | 60 |
| critical rel. position (idx / last idx), all | 486 | 0.63 | 0.6538 | 0.0225 | 0.9888 | 0.3146 | 0.8828 |
| critical rel. position, τ²-Bench | 400 | 0.64 | 0.65705 | 0.0882 | 0.9773 | 0.325 | 0.881 |
| critical rel. position, SWE-Bench Pro | 86 | 0.59 | 0.62415 | 0.0225 | 0.9888 | 0.2887 | 0.8828 |
| characters per trajectory (all) | 486 | 52559.87 | 20895.0 | 8123 | 448410 | 14550 | 165920 |
| characters per trajectory (τ²-Bench) | 400 | 20620.95 | 19655.0 | 8123 | 57590 | 14321 | 28518 |
| characters per trajectory (SWE-Bench Pro) | 86 | 201113.02 | 181666.5 | 81574 | 448410 | 107378 | 324548 |

Histogram of messages per trajectory (en):

| messages | n | % |
|---|---|---|
| 0-9 | 2 | 0.4 |
| 10-19 | 42 | 8.6 |
| 20-29 | 213 | 43.8 |
| 30-39 | 97 | 20.0 |
| 40-59 | 38 | 7.8 |
| 60-79 | 14 | 2.9 |
| 80-119 | 39 | 8.0 |
| 120-199 | 40 | 8.2 |
| >=200 | 1 | 0.2 |

Histogram of critical-step relative position:

| rel. position | n | % |
|---|---|---|
| 0.0-0.2 | 26 | 5.3 |
| 0.2-0.4 | 40 | 8.2 |
| 0.4-0.6 | 120 | 24.7 |
| 0.6-0.8 | 204 | 42.0 |
| 0.8-1.0 | 96 | 19.8 |

Subset / domain / generating model:

| subset / domain / model | n | % |
|---|---|---|
| tau2bench / retail / deepseek-reasoner | 103 | 21.2 |
| tau2bench / airline / qwen3-max | 80 | 16.5 |
| tau2bench / retail / gpt-5 | 76 | 15.6 |
| tau2bench / airline / deepseek-reasoner | 71 | 14.6 |
| tau2bench / airline / gpt-5 | 70 | 14.4 |
| swebenchpro / swe / gemini-3.1-pro-preview | 28 | 5.8 |
| swebenchpro / swe / claude-opus-4-6 | 21 | 4.3 |
| swebenchpro / swe / grok-4.20-beta-0309-reasoning-passthrough | 21 | 4.3 |
| swebenchpro / swe / moonshot_kimi-k2.6-coding-litellm | 16 | 3.3 |

Critical-error type (module.subtype) — all en trajectories:

| critical_error_type | n | % |
|---|---|---|
| reason.WrongChoice | 124 | 25.5 |
| reason.InvalidInference | 94 | 19.3 |
| reason.MissingAssumptionCheck | 64 | 13.2 |
| plan.BadDecomposition | 44 | 9.1 |
| obs.IgnoreOutput | 26 | 5.3 |
| obs.MisreadOutput | 21 | 4.3 |
| plan.WrongOrder | 17 | 3.5 |
| None | 17 | 3.5 |
| verify.NoVerification | 16 | 3.3 |
| act.WrongActionSequence | 13 | 2.7 |
| verify.PrematureTermination | 12 | 2.5 |
| act.WrongTool | 9 | 1.9 |
| act.ToolSchemaMismatch | 8 | 1.6 |
| plan.UnrealisticPlan | 6 | 1.2 |
| obs.GroundingFail | 6 | 1.2 |
| act.UnsafeOrForbiddenAction | 4 | 0.8 |
| plan.OverExplore | 2 | 0.4 |
| verify.WrongVerification | 2 | 0.4 |
| plan.GoalDrift | 1 | 0.2 |

Critical-error module (prefix of the type label):

| module | n | % |
|---|---|---|
| reason | 282 | 58.0 |
| plan | 70 | 14.4 |
| obs | 53 | 10.9 |
| act | 34 | 7.0 |
| verify | 30 | 6.2 |
| None | 17 | 3.5 |

Critical-error type by subset:

| type | τ²-Bench | SWE-Bench Pro |
|---|---|---|
| None | 8 | 9 |
| act.ToolSchemaMismatch | 4 | 4 |
| act.UnsafeOrForbiddenAction | 2 | 2 |
| act.WrongActionSequence | 10 | 3 |
| act.WrongTool | 8 | 1 |
| obs.GroundingFail | 6 | 0 |
| obs.IgnoreOutput | 26 | 0 |
| obs.MisreadOutput | 21 | 0 |
| plan.BadDecomposition | 32 | 12 |
| plan.GoalDrift | 1 | 0 |
| plan.OverExplore | 2 | 0 |
| plan.UnrealisticPlan | 6 | 0 |
| plan.WrongOrder | 17 | 0 |
| reason.InvalidInference | 91 | 3 |
| reason.MissingAssumptionCheck | 58 | 6 |
| reason.WrongChoice | 89 | 35 |
| verify.NoVerification | 8 | 8 |
| verify.PrematureTermination | 11 | 1 |
| verify.WrongVerification | 0 | 2 |

Role of the annotated critical message: {'assistant (assistant)': 485, 'tool (tool)': 1}. Reward values: {0: 486}.

Paper-reported for comparison: 400 + 86 trajectories averaging 29.3 and 119.7 steps; τ²-Bench reasoning-phase 60.7 %, task conflict 52.4 % / history conflict 46.3 %; SWE-Bench Pro reasoning 57.1 %, task conflict 73.4 %; top subtypes reason.InvalidInference 22.8 %, reason.WrongChoice 22.2 %, reason.MissingAssumptionCheck 14.5 % (τ²) and reason.WrongChoice 40.7 %, plan.BadDecomposition 14.0 %, verify.NoVerification 9.3 % (SWE-Pro) — matching our counts.

## Example trajectory

Chosen: `airline_failed_qwen3-max::0250f877-f44b-4ceb-990a-f284cc9c6433` (en edition, tau2bench, airline domain, model qwen3-max), 7 messages, 8123 characters; the shortest τ²-Bench trajectory. Step index = unified `step` (0-based message index; step 0 is the system policy prompt).

**Source id:** `airline_failed_qwen3-max::0250f877-f44b-4ceb-990a-f284cc9c6433`  
**Task:** Hi, I’d like to check the balances on my gift cards and certificates, please. Could you let me know the total amounts I have for each?

**[step 0] system**

```text
# Airline Agent Policy

The current time is 2024-05-15 15:00:00 EST.

As an airline agent, you can help users **book**, **modify**, or **cancel** flight reservations. You also handle **refunds and compensation**.

Before taking any actions that update the booking database (booking, modifying flights, editing baggage, changing cabin class, or updating passenger information), you must list the actio […] of passengers.

Do not offer compensation for any other reason than the ones listed above.
```

**[step 1] assistant**

```text
Hi! How can I help you today?
```

**[step 2] user**

```text
Hi, I’d like to check the balances on my gift cards and certificates, please. Could you let me know the total amounts I have for each?
```

**[step 3] assistant  ⟵ ANNOTATED ERROR STEP**

```text
[tool_calls]
- transfer_to_human_agents({"summary": "User is requesting to check the balances on their gift cards and certificates, which is outside the scope of available tools and policy."})
```

**[step 4] tool**

```text
Transfer successful
```

**[step 5] assistant**

```text
YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON.
```

**[step 6] user**

```text
###TRANSFER###
```

**Annotation**

- Faulty agent: `assistant`
- Faulty step: `3`
- Category: `act.WrongTool`
- Reason / root cause: (no free-text rationale is shipped in the release; label = earliest failure-responsible step under the Who&When decisive-error protocol)
- reward: 0
- source_benchmark: tau2bench
- language: en
- pair_id: tau2bench:airline_failed_qwen3-max::0250f877-f44b-4ceb-990a-f284cc9c6433
- agent_framework_description: A user interacts with a single `assistant` that must follow the scene policy shown in the leading `system` message while executing the user's request. `tool` messages are tool-call return values. Critical errors can only be attributed to an `assistant` step; `user` and `tool` steps are never the critical step. The assistant should try to fulfil the user's request as much as possible, but the user may make unreasonable or out-of-policy requests; whenever the user's request conflicts with the `system` policy, the `system` policy takes precedence and the assistant must refuse or redirect rather than comply.

DATASET NOTES (tau²-bench). The leading `system` message lists binding procedural rules using "必须" / "must" / "before X you must Y" / "only ... if" / "never". These rules are hard constraints on every assistant step that touches the database (booking, modifying, cancelling, refunding, returning) — typical examples include verifying user identity (email lookup, name+zip) before any account-data operation. When the user refers to a target object indirectly ("my recent order", "the ite […]  may be unworkable, and the user may rely on the option as if it were available.
- Produced answer / final output: YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON.

## Notes for the report

- **Closest to Who&When's protocol** (decisive/earliest error, 3-way majority), but single-agent and long-horizon; it is the only dataset here with both a *customer-service tool-use* domain (τ²-Bench, with a simulated user whose messages are never the critical step) and a *coding* domain (SWE-Bench Pro, ~120 messages / 200 k characters each).
- **Critical errors are mid-to-late** (median relative position 0.65; only 13.5 % in the first 40 %), because agents first gather information (user dialogue / repo exploration) before the decisive decision — the opposite of the early-error pattern in *Failure as a Process*.
- **Two language editions:** the paper's numbers are on the Chinese (zh) edition; the English edition was built from aligned source trajectories and inherits the zh labels. Use `en` for English-language reports; cite that results are on `zh`.
- **What is missing:** annotator rationales, execution-phase and reference-category labels (only in the paper's aggregate figures), the 24 dropped ambiguous SWE-Pro trajectories, and 17 trajectories with `critical_error_type = null`.
- **Pre-annotation anchoring risk:** annotators saw three LLM proposals *and* the benchmark's failure diagnostics; evaluated detectors see only the trajectory — the authors quantify the anchoring (Table 4) but it should be mentioned.
- **Overlaps:** the repo ships converted copies of Who&When (58 + 126) and AgentErrorBench (100 + 50 + 50) — convenient for a unified evaluation harness; the taxonomy is a re-organisation of AgentDebug's modules (plan/reason/act/obs/verify instead of memory/reflection/planning/action/system).
