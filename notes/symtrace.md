# SymFail — SymTrace

## Identity

- **Full title:** *Repair or Resample? Rethinking Failure Debugging in LLM Multi-Agent Systems*. Framework: **SymTrace** (Symptomatic Trace); dataset: **SymFail**.
- **Authors / affiliation:** Zhongwen Luan, Xiaoyu Zhang, Ming Hu, Yue Yang, Jiongchi Yu, Xiaohong Chen — East China Normal University (Shanghai), Nanyang Technological University, Xi'an University of Architecture and Technology.
- **Venue:** arXiv preprint **2608.25920** (v1 26 Aug 2026, v2 29 Aug 2026; cs.AI, cs.SE). No venue.
- **Links:** paper https://arxiv.org/abs/2608.25920 · code + data: anonymous review repository https://anonymous.4open.science/r/SymTrace-7234 (`SymTrace/` code, `SymFail/` data). No Hugging Face dataset, no GitHub repository, no project page found (searched 2026-10-26).
- **License:** SymFail author-created annotations, localized failure records, trace graphs, derived metadata and documentation: **CC BY 4.0** (`SymFail/DATA_LICENSE.md`). WebArena-Verified / AssistantBench tasks, websites, framework code and model outputs keep their own terms. No licence file for the SymTrace code.
- **Availability:** **downloaded in full** (anonymous-GitHub zip export, 53 MB; 354 MB extracted). Two frozen snapshots are shipped: the paper's **536-case package** (`human_annotations_536.jsonl` + `initial_failure_logs_536/`, 2,144 files) and a newer **437-case package** (`human_annotations_437.jsonl` + `initial_failure_logs_437/`, 3,453 files; reviewed 2026-09-03) that the paper does not describe.
- **Local path:** `/dataDisk/home/thanhdo/failure-attribution-datasets/data/symtrace/extracted/SymFail/` (zip kept in `data/symtrace/SymTrace-7234.zip`).

## Description

- **Purpose.** SymTrace is a controlled evaluation framework for MAS failure *debugging and repair*. It asks whether rerun-based repair methods fix failures causally or only by resampling. It records an execution as an **event-dependency graph** (boundary logging of every model and tool call, no change to the framework scheduler), picks an **intervention anchor** node, replays the prefix from the recorded boundary results under strict matching ("selective replay") and lets everything after the anchor run live. SymFail is the frozen set of source failures the study intervenes on. It is not an attribution leaderboard: the labelled failure node is used to evaluate *repair*, and the categories are described as "trace-localized intervention signals rather than task-level failure verdicts".
- **Construction (natural failures).** Candidate pool: all 258 WebArena-Verified Hard tasks and the 33 eligible AssistantBench dev tasks (task, reference answer and gold URL available); retained all 33 AssistantBench tasks and the first 167 WebArena-Verified Hard tasks in published order → **200 tasks** (33 Web-QA, 70 mutation, 25 navigation, 72 retrieval). Each task is run once with **AG2**, **CrewAI** and **Magentic-One** through SymTrace's instrumented adapters, backbone **deepseek-v4-flash** at temperature 0 (an API alias; no model snapshot recorded), giving 600 executions. The native evaluators (WebArena-Verified evaluator; reference-answer match for AssistantBench) mark **536 failures** (462 of 501 WebArena executions, 74 of 99 AssistantBench executions): 171 AG2, 184 CrewAI, 181 Magentic-One. The 64 accepted runs are not released. Separately, 54 successful executions were rerun three times for an instability analysis: 39 failed at least once.
- **Annotation protocol.** Four annotators with software-engineering backgrounds, calibrated on reference-labelled examples. Three annotate independently: all applicable categories C1–C4 (multi-label), one primary category, and the **earliest trace-supported actionable node** (node id + node kind) with evidence and a rationale. A fourth annotator reviews task, full trace, event graph and the three annotations and produces the **final** annotation with authority to revise anything (no majority vote, no label union). The final category set differs from the three-annotator union in 113 / 536 cases (21.1 %). All 536 × 4 = 2,144 node selections exist in their event graphs and match the recorded node kinds.
- **Agreement (three independent annotators, paper App. B):** Fleiss' κ = **0.62** primary category, **0.574** exact category set, **0.81** failure-node type; per-category presence κ: C1 0.696, C2 0.374, C3 0.718, C4 0.688. Exact failure node: **73.88 %** unanimous, **95.90 %** at least two of three; strict tuple (categories + node) unanimous in 39.18 %. From the released flags: node unanimous 396 / 536, node supported by ≥2 annotators 470, primary label unanimous 459, label set unanimous 280, strict unanimous 210; final confidence "high" in all 536 cases (individual annotations: 1,467 high, 141 medium).
- **Taxonomy (C1–C4, consolidated from the MAST failure taxonomy of Cemri et al.):**
  - **C1 Task-constraint violation** (from FM-1.1): behaviour conflicts with an explicit task constraint or output requirement (placeholder/skipped actions, unresolved requests).
  - **C2 Repeated or stalled progress** (FM-1.3 + FM-1.5): history repeats while the objective is unfinished (repeated action fingerprints / URLs without new parameters or evidence).
  - **C3 Unresolved runtime condition** (FM-2.2 + FM-2.3, extended to execution/context failures): the node contains or continues from an unresolved execution, access or upstream condition (recorded errors, timeouts, failed tool results).
  - **C4 Plan–action–outcome inconsistency** (FM-2.6): an explicit plan or claim conflicts with the executed action or observed outcome (completion claimed after an unsuccessful action).
- **Labels in the release:** `failure_node_id`, `failure_node_kind` (agent_action / tool_call / tool_result / final_result), `primary_failure_label`, `failure_labels` (1–4 of c1–c4), `confidence`, per-annotator records and unanimity / support flags. **Rationales and evidence excerpts are withheld** (`annotation_prose_in_public_export: false`) although the paper says the release includes them. No faulty-agent label (the node's `agent_id` is the only agent information), no root cause, no repair outcome per node.
- **Method under test (SymTrace Suspicious-Node Intervention).** Each completed node is scored by deterministic rules (repetition deadlocks, unresolved execution failures, browser errors, completion claims without tool evidence) and an LLM judge; fused score c_mix = 0.55·LLM + 0.45·rules (+0.04 if several symptoms), confirmation gate θ = 0.50 (manually set). The highest-scoring node becomes the anchor; the prefix is reconstructed from recorded boundary results and the node is re-generated with a C1–C4-conditioned repair instruction, one attempt.
- **Metrics.** rep@k (failure reproduced in attempt k) and pass@k (native evaluator accepts the repaired run), per MAS and in total; Holm-corrected paired tests.
- **Reported results.**

| Reproduction (%) | rep@1 | rep@3 |
|---|---|---|
| Unguided full rerun | 67.97 | 41.42 |
| SymTrace selective replay | 80.78 | 52.43 |

| Repair (pass rate, %) | attempts | AG2 | CrewAI | Magentic-One | Total |
|---|---|---|---|---|---|
| Last-Node intervention | 1 | 0.58 | 1.63 | 1.66 | 1.31 |
| Random-Node intervention | 1 | 2.34 | 4.89 | 3.87 | 3.73 |
| Critic-Agent | 3 | 4.09 | 2.72 | 4.42 | 3.73 |
| Self-Reflection | 3 | 4.68 | 2.17 | 6.08 | 4.29 |
| Unguided Full Rerun | 3 | 8.19 | 3.80 | 8.84 | 6.90 |
| **Suspicious-Node (SymTrace)** | 1 | **16.37** | **25.00** | **18.78** | **20.15** |

By primary category (rerun / self-reflection / critic pass@3): C1 9.60 / 4.80 / 2.40; C2 4.35 / 2.90 / 5.80; C3 5.42 / 3.45 / 1.97; C4 7.91 / 5.76 / 6.47. Suspicious-Node efficiency: 10–15 API calls per repair. Raising θ to 0.95 keeps 78 cases with 24.36 % conditional repair.

## Schema

- `SymFail/human_annotations_536.jsonl` — one object per case: `annotation_id`, `case_id`, `benchmark_case_id`, `task_id` (`webarena_verified_hard_<n>` or `assistantbench_dev_<hash>`), `mas` (`ag2` / `crewai` / `magnetic_one`), `failure_node_id` (`<task_id>:attempt_000:snapshot:<trace-hash>:<node>`, e.g. `…:agent_action_0001`, `…:final`, `…:crewai_message_kickoff_0002`, `…:magnetic_message_0002_0000`), `failure_node_kind`, `primary_failure_label`, `failure_labels`, `confidence`, `inter_annotator_agreement` {unanimity flags, support counts}, `individual_annotations` (3 × the same fields), review metadata.
- `SymFail/initial_failure_logs_536/<mas>/<task_id>/attempt_000/` — one bundle per failure:
  - `graph.json` (`schema_version: masd.graph.v1`): `nodes` [{`node_id`, `kind` ∈ {sys_prompt, user_input, agent_action, tool_call, tool_result, final_result, error}, `agent_id`, `step_id`, `sequence_index`, `topological_timestamp`, `parent_node_ids`, `child_node_ids`, `action`, `observation`, `thought`, `tool_call`, `tool_result`, `final_answer`, `error`, `api_messages` / `api_response` (full LLM request and raw response, on LLM-backed agent_action nodes), `metadata`}], `edges` [{`parent_id`, `child_id`, `reason` (e.g. `adapter_dependency`), `confidence`}], `topological_order`, `trace_id`, `metadata.capture_summary` (`llm_call_count`, `tool_result_count`, `tool_failure_count`, instrumentation level).
  - `trajectory.json`: the same nodes with run metadata plus `result` and `task` (benchmark task, `reference_answer` or WebArena evaluator spec, `task_type`, `difficulty_tag`, `start_urls`).
  - `result_record.json`: `final_answer`, `evaluator_evidence` (`method`, `missing_reference_items` / `missing_retrieved_data`, `has_real_tool_event`), `latency`, `model`, `temperature`, `api_call_count`, `token_usage` (empty in all 536 records).
  - `api_records.jsonl`: one line per LLM call — `request` (messages), `response`, `usage`, `latency`, `adapter`.
- **Step unit used here:** one graph node in `topological_order` (0-based; node 0 is `sys_prompt`, node 1 the `user_input`). The failure node index is its position in that order.
- `SymFail/initial_failure_logs_437/<mas>/<benchmark>--<mas>--<model>/<task_id>/attempt_000/` (newer package): adds `graph_manifest.json`, `evaluation.json`, `stdout.log`, and framework stdout/stderr for ChatDev / MetaGPT / OpenManus; `human_annotations_437.jsonl` has a flatter schema (`primary_label`, `reason`, `evidence_excerpt`, `failure_node_id` = `node_final` for all 437, `reviewer_id` = `trajectory_deep`, `task_input`, `reference_answer_for_review`).

## Statistics (computed from the downloaded 536-case package; all trajectories failed)

| quantity | n | mean | median | min | max | p10 | p90 |
|---|---|---|---|---|---|---|---|
| graph nodes (= steps) per trajectory, all | 536 | 10.35 | 7.0 | 5 | 21 | 5 | 19 |
| graph nodes per trajectory, AG2 | 171 | 10.36 | 13 | 5 | 15 | 5 | 15 |
| graph nodes per trajectory, CrewAI | 184 | 7.72 | 5.0 | 5 | 15 | 5 | 15 |
| graph nodes per trajectory, Magentic-One | 181 | 13.02 | 7 | 7 | 21 | 7 | 21 |
| decision nodes (agent_action + tool_call + final_result) | 536 | 7.22 | 5.0 | 3 | 16 | 3 | 15 |
| agent_action nodes per trajectory | 536 | 5.09 | 4.0 | 2 | 12 | 2 | 12 |
| LLM calls per trajectory (capture_summary) | 536 | 1.9 | 1.0 | 1 | 3 | 1 | 3 |
| tool results per trajectory | 536 | 1.13 | 0.0 | 0 | 3 | 0 | 3 |
| tool failures per trajectory | 536 | 0.7 | 0.0 | 0 | 3 | 0 | 2 |
| distinct agent_id per trajectory | 536 | 3.14 | 3.0 | 2 | 4 | 2 | 4 |
| failure node index (0-based, topological order) | 536 | 3.83 | 3.0 | 2 | 14 | 2 | 8 |
| failure node relative position (idx / last idx) | 536 | 0.49 | 0.5 | 0.1 | 1.0 | 0.15 | 1.0 |
| characters per trajectory (all node texts) | 536 | 5510.8 | 3571.0 | 517 | 33408 | 1005 | 12933 |
| tokens per trajectory (result.token_usage) | 0 | - | - | - | - | - | - |
| wall-clock latency per trajectory (s) | 536 | 17.47 | 15.1 | 3.4 | 63.7 | 8.0 | 30.1 |

Histogram of graph nodes per trajectory:

| nodes | n | % |
|---|---|---|
| 0-4 | 0 | 0.0 |
| 5-9 | 304 | 56.7 |
| 10-14 | 75 | 14.0 |
| 15-19 | 110 | 20.5 |
| 20-24 | 47 | 8.8 |
| 25-29 | 0 | 0.0 |
| >=30 | 0 | 0.0 |

Histogram of failure-node relative position:

| rel. position | n | % |
|---|---|---|
| 0.0-0.2 | 93 | 17.4 |
| 0.2-0.4 | 144 | 26.9 |
| 0.4-0.6 | 179 | 33.4 |
| 0.6-0.8 | 17 | 3.2 |
| 0.8-1.0 | 103 | 19.2 |

Framework × benchmark:

| MAS / benchmark | n | % |
|---|---|---|
| CrewAI / WebArena-Verified Hard | 161 | 30.0 |
| Magentic-One / WebArena-Verified Hard | 155 | 28.9 |
| AG2 / WebArena-Verified Hard | 146 | 27.2 |
| Magentic-One / AssistantBench | 26 | 4.9 |
| AG2 / AssistantBench | 25 | 4.7 |
| CrewAI / AssistantBench | 23 | 4.3 |

Primary symptom category:

| primary label | n | % |
|---|---|---|
| C3 Unresolved runtime condition | 203 | 37.9 |
| C4 Plan-action-outcome inconsistency | 139 | 25.9 |
| C1 Task-constraint violation | 125 | 23.3 |
| C2 Repeated / stalled progress | 69 | 12.9 |

Multi-label marginals (a case carries 1–4 labels):

| label | n | % |
|---|---|---|
| C4 Plan-action-outcome inconsistency | 466 | 86.9 |
| C1 Task-constraint violation | 439 | 81.9 |
| C3 Unresolved runtime condition | 289 | 53.9 |
| C2 Repeated / stalled progress | 288 | 53.7 |

Label-set size: {"3": 260, "2": 153, "1": 32, "4": 91}; most common sets: {"c1+c2+c4": 119, "c1+c3+c4": 102, "c1+c2+c3+c4": 91, "c1+c4": 68, "c2+c3+c4": 29, "c2+c4": 27, "c3+c4": 26, "c1+c3": 23}

Primary category by MAS:

| MAS | C1 | C2 | C3 | C4 |
|---|---|---|---|---|
| AG2 | 37 | 2 | 72 | 60 |
| CrewAI | 49 | 21 | 36 | 78 |
| Magentic-One | 39 | 46 | 95 | 1 |

Failure node kind / agent_id of the failure node:

| failure_node_kind | n | % |
|---|---|---|
| agent_action | 433 | 80.8 |
| final_result | 98 | 18.3 |
| tool_result | 4 | 0.7 |
| tool_call | 1 | 0.2 |
| agent_id of failure node | n | % |
|---|---|---|
| crewai (CrewAI) | 184 | 34.3 |
| ag2 (AG2) | 166 | 31.0 |
| user (Magentic-One) | 102 | 19.0 |
| masd_magnetic_one_assistant (Magentic-One) | 77 | 14.4 |
| browser_tool (AG2) | 4 | 0.7 |
| magnetic_one (Magentic-One) | 2 | 0.4 |
| masd_ag2_multistep_assistant (AG2) | 1 | 0.2 |

Node kinds over all trajectories: {"sys_prompt": 536, "user_input": 536, "agent_action": 2726, "tool_call": 607, "tool_result": 607, "final_result": 536}; agent_id totals: {"ag2": 971, "user": 883, "masd_ag2_multistep_assistant": 371, "browser_tool": 607, "magnetic_one": 922, "masd_magnetic_one_assistant": 694, "crewai": 1100}

Task types / difficulty tags (from trajectory.json task): {"assistant_web_qa": 74, "navigate": 64, "retrieve": 203, "mutate": 195} / {"medium": 29, "hard": 507}

Backbone model / temperature recorded in result: {"deepseek-v4-flash": 536} / {"0.0": 536}

Agreement (536 cases, 3 annotators + 1 adjudicator): {"failure_node_unanimous": 396, "failure_node_support_ge2": 470, "failure_node_kind_unanimous": 488, "primary_label_unanimous": 459, "label_set_unanimous": 280, "strict_unanimous": 210, "confidence": {"high": 536}, "individual_confidence": {"high": 1467, "medium": 141}, "final_label_set_differs_from_all_three": 87}

Failure node is the last node in 98 cases; it is the first agent_action node in 246 cases.

Environment / adapter signals: {"llm_calls_distribution": {"3": 220, "1": 276, "2": 40}, "trajectories_without_tool_call": 276, "trajectories_with_failed_tool_result": 196, "trajectories_all_tool_results_failed": 163, "trajectories_with_placeholder_url_error": 173, "webarena_trajectories_with_placeholder_url_error": 173, "webarena_trajectories_with_any_successful_tool_result": 23, "assistantbench_trajectories_with_any_successful_tool_result": 74, "evaluator_has_real_tool_event_false": 447, "evaluator_has_real_tool_event_true": 15, "evaluator_methods": {"reference_answer_match": 74, "webarena_verified_evaluator": 462}, "magentic_failure_node_agent_user_kind": {"agent_action": 102}, "final_answer_contains_unable_or_cannot": 148, "distinct_tasks": 194, "tasks_failed_by_all_three_mas": 155}

### The newer 437-case package

{
 "n": 437,
 "bundles_found": 437,
 "per_mas": {
  "ag2": 80,
  "crewai": 80,
  "magnetic_one": 80,
  "chatdev": 80,
  "metagpt": 54,
  "openmanus": 63
 },
 "per_model": {
  "gemini": 160,
  "gpt": 160,
  "claude": 117
 },
 "per_benchmark": {
  "assistantbench+webarena_verified": 240,
  "programdev": 197
 },
 "per_cell": {
  "assistantbench+webarena_verified--ag2--gemini": 40,
  "assistantbench+webarena_verified--ag2--gpt": 40,
  "assistantbench+webarena_verified--crewai--claude": 40,
  "assistantbench+webarena_verified--crewai--gpt": 40,
  "assistantbench+webarena_verified--magnetic_one--claude": 40,
  "assistantbench+webarena_verified--magnetic_one--gemini": 40,
  "programdev--chatdev--gemini": 40,
  "programdev--chatdev--gpt": 40,
  "programdev--metagpt--claude": 14,
  "programdev--metagpt--gpt": 40,
  "programdev--openmanus--claude": 23,
  "programdev--openmanus--gemini": 40
 },
 "task_family": {
  "assistantbench": 198,
  "webarena": 42,
  "programdev": 197
 },
 "primary_label": {
  "C3 Unresolved runtime condition": 319,
  "C4 Plan-action-outcome inconsistency": 69,
  "C1 Task-constraint violation": 43,
  "C2 Repeated / stalled progress": 6
 },
 "failure_node_id": {
  "node_final": 437
 },
 "reason": {
  "Incomplete execution - no final action": 319,
  "Reasoning-action mismatch - failed to find correct answer": 58,
  "Task constraint violation - missing required content or violating explicit requirements": 43,
  "Loop or deadlock - agent stuck in repetitive actions without progress": 6,
  "Reasoning and action mismatch": 11
 },
 "reviewer_id": {
  "trajectory_deep": 437
 },
 "reviewed_at_range": [
  "2026-09-03T14:46:03.041132",
  "2026-09-03T14:46:05.690327"
 ]
}

| quantity | n | mean | median | min | max | p10 | p90 |
|---|---|---|---|---|---|---|---|
| graph nodes per trajectory (437 package) | 437 | 17.11 | 15 | 5 | 90 | 6 | 24 |
| LLM calls per trajectory (437 package) | 240 | 2.67 | 3.0 | 1 | 3 | 1 | 3 |
| graph nodes per trajectory, ag2 | 80 | 13.04 | 15.0 | 5 | 15 | 9 | 15 |
| graph nodes per trajectory, chatdev | 80 | 9.54 | 6.0 | 6 | 31 | 6 | 19 |
| graph nodes per trajectory, crewai | 80 | 12.25 | 13.0 | 5 | 15 | 5 | 15 |
| graph nodes per trajectory, magnetic_one | 80 | 16.29 | 18.0 | 6 | 20 | 6 | 19 |
| graph nodes per trajectory, metagpt | 54 | 13.15 | 11.0 | 8 | 24 | 11 | 24 |
| graph nodes per trajectory, openmanus | 63 | 42.54 | 28 | 12 | 90 | 12 | 86 |

## Example trajectory

Chosen: `initial_failure_logs_536/ag2/webarena_verified_hard_96` (AG2, WebArena-Verified Hard, 13 graph nodes, 2553 characters): the shortest trajectory with at least one tool call whose unanimous failure node is an agent_action that is not the final node. Step index = position in `topological_order`.

**Source id:** `initial_failure_logs_536/ag2/webarena_verified_hard_96`  
**Task:** Get the status of my latest order and when will it arrive. Return a list of objects with keys "status" and "arrival_date" (YYYY-MM-DD format or null if not available), without any additional details.

**[step 0] ag2 [sys_prompt]**

```text
MASD controlled experiment prompt and adapter constraints.
```

**[step 1] user [user_input]**

```text
Mode: snapshot
Task id: webarena_verified_hard_96
Benchmark: webarena_verified / hard
Task: Get the status of my latest order and when will it arrive. Return a list of objects with keys "status" and "arrival_date" (YYYY-MM-DD format or null if not available), without any additional details.
Start URLs or tools: ['__SHOPPING__']
Return only the final answer and a short note about what evidence would be needed.
```

**[step 2] masd_ag2_multistep_assistant [agent_action]**

```text
[ag2_process_message_before_send] {"action":"browse","url":"__SHOPPING__","reason":"Start at the shopping site to access account and view latest order status."}
```

**[step 3] ag2 [agent_action]**

```text
[ag2_agent_step] {"action":"browse","url":"__SHOPPING__","reason":"Start at the shopping site to access account and view latest order status."}
```

**[step 4] ag2 [tool_call]**

```text
{"reason": "Start at the shopping site to access account and view latest order status.", "type": "browser_http_get", "url": "__SHOPPING__"}
```

**[step 5] browser_tool [tool_result]**

```text
{'type': 'browser_http_get', 'status': 'failed', 'url': '__SHOPPING__', 'latency': 0.0015594959259033203, 'error': {'type': 'MissingSchema', 'message': "Invalid URL '__SHOPPING__': No scheme supplied. Perhaps you meant https://__SHOPPING__"}}
```

**[step 6] masd_ag2_multistep_assistant [agent_action]**

```text
[ag2_process_message_before_send] {"action":"browse","url":"https://__SHOPPING__","reason":"Need to access the shopping site. The placeholder needs a scheme."}
```

**[step 7] ag2 [agent_action]  ⟵ ANNOTATED ERROR STEP**

```text
[ag2_agent_step] {"action":"browse","url":"https://__SHOPPING__","reason":"Need to access the shopping site. The placeholder needs a scheme."}
```

**[step 8] ag2 [tool_call]**

```text
{"reason": "Need to access the shopping site. The placeholder needs a scheme.", "type": "browser_http_get", "url": "https://__SHOPPING__"}
```

**[step 9] browser_tool [tool_result]**

```text
{'type': 'browser_http_get', 'status': 'failed', 'url': 'https://__SHOPPING__', 'latency': 7.287393808364868, 'error': {'type': 'ConnectionError', 'message': 'HTTPSConnectionPool(host=\'__shopping__\', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host=\'__shopping__\', port=443): Failed to resolve \'__shopping__\' ([Errno 11001] getaddrinfo failed)"))'}}
```

**[step 10] masd_ag2_multistep_assistant [agent_action]**

```text
[ag2_process_message_before_send] {"final":"[\n  {\"status\": \"unknown\", \"arrival_date\": null}\n]\n\nNote: Evidence needed would be the user's order history page on the shopping site after authentication."}
```

**[step 11] ag2 [agent_action]**

```text
[ag2_agent_step] {"final":"[\n  {\"status\": \"unknown\", \"arrival_date\": null}\n]\n\nNote: Evidence needed would be the user's order history page on the shopping site after authentication."}
```

**[step 12] ag2 [final_result]**

```text
[
  {"status": "unknown", "arrival_date": null}
]

Note: Evidence needed would be the user's order history page on the shopping site after authentication.
```

**Annotation**

- Faulty agent: `ag2`
- Faulty step: `7`
- Category: `C3 Unresolved runtime condition (primary); label set {C1, C2, C3, C4}`
- Reason / root cause: (annotation rationales and evidence excerpts are withheld from the public export: annotation_prose_in_public_export = false; the label is the earliest trace-supported actionable node carrying the symptom)
- mas: AG2
- source_benchmark: WebArena-Verified Hard
- task_type: retrieve
- difficulty: hard
- failure_node_id: agent_action_0001
- failure_node_kind: agent_action
- confidence: high
- inter_annotator_agreement: {"annotation_count": 3, "primary_failure_label_unanimous": true, "failure_label_set_unanimous": false, "failure_node_unanimous": true, "failure_node_kind_unanimous": true, "strict_annotation_unanimous": false, "final_primary_failure_label_support_count": 0, "final_failure_label_set_support_count": 1, "final_failure_node_support_count": 3, "final_strict_annotation_support_count": 0}
- evaluator_evidence: {"evaluator_names": ["AgentResponseEvaluator"], "expected_retrieved_data": [{"arrival_date": null, "status": "canceled"}], "has_real_tool_event": false, "method": "webarena_verified_evaluator", "missing_retrieved_data": [{"expected": {"arrival_date": null, "status": "canceled"}, "missing_values": ["None", "canceled"]}], "observed_answer_excerpt": "[\n  {\"status\": \"unknown\", \"arrival_date\": null}\n]\n\nNote: Evidence needed would be the user's order history page on the shopping site after authentication.", "observed_tool_result": {"error": {"message": "HTTPSConnectionPool(host='__shopping__', port=443): Max retries exceeded with url: / (Caused by NameResolutionError(\"HTTPSConnection(host='__shopping__', port=443): Failed to resolve '__shopping__' ([Errno 11001] getaddrinfo failed)\"))", "type": "ConnectionError"}, "latency": 7.287393808364868, "status": "failed", "type": "browser_http_get", "url": "https://__SHOPPING__"}, "requires_environment_event": false, "task_types": ["RETRIEVE"]}
- llm_call_count: 3
- tool_failure_count: 2
- step_indexing: 0-based position of the node in graph.json topological_order (sys_prompt = 0, user_input = 1)
- Ground truth: [{'evaluator': 'AgentResponseEvaluator', 'expected': {'error_details': None, 'retrieved_data': [{'arrival_date': None, 'status': 'canceled'}], 'status': 'SUCCESS', 'task_type': 'RETRIEVE'}, 'ordered': False, 'results_schema': {'items': {'properties': {'arrival_date': {'format': 'date', 'type': 'string'}, 'status': {'type': 'string'}}, 'type': 'object'}, 'type': 'array'}}]
- Produced answer / final output: [
  {"status": "unknown", "arrival_date": null}
]

Note: Evidence needed would be the user's order history page on the shopping site after authentication.

## Notes for the report

1. **Replayable by design.** Every bundle carries the full event graph with per-call LLM requests/responses and tool boundary results, which is exactly what SymTrace's selective replay (and Proposal 1's `Roll`) consumes; the code to replay is in the same repository. This is the closest released analogue to TraceElephant's "dynamic" setting, with CrewAI as a framework seen nowhere else in the survey.
2. **The MAS are thin adapters, and the budget is tiny.** Agents are SymTrace's `masd_*` adapters (one assistant + a `browser_http_get` tool), `llm_call_count` is at most 3 and is 1 in 276 of 536 trajectories (no tool call at all); graph sizes are nearly constant per framework (AG2 15, CrewAI 5–15, Magentic-One 7–21 nodes). "Agent-level" attribution is meaningless here: the failure node's `agent_id` is the framework name, `user` (Magentic-One echoes the task as an `agent_action` by `user`, blamed 102 times) or the assistant.
3. **Most WebArena runs never reached the environment.** The WebArena site placeholders (`__SHOPPING__`, …) were not substituted in the released runs: 173 WebArena trajectories end in `MissingSchema` / `NameResolutionError` tool failures on the literal placeholder, only 23 of 462 WebArena trajectories contain a single successful tool result, and the evaluator records `has_real_tool_event: false` for 447 of them. Many "failures" are therefore the agent answering (or declaring inability, 148 final answers) without any page content, which is what C3 (38 %) and C4 capture. The AssistantBench runs did reach the live web (74 / 74 with a successful fetch), though several sites returned "temporarily unavailable" pages.
4. **Labels are symptoms, not root causes.** C1–C4 are MAST modes collapsed to four and are explicitly intervention signals; label sets are large (mean 2.77 labels, C4 present in 87 % of cases, 91 cases carry all four), so the informative targets are the primary label (κ 0.62) and the node (73.9 % unanimous). The failure node is the first `agent_action` in 246 cases and the final node in 98.
5. **Public export is incomplete.** Rationales and evidence are withheld; `token_usage` is empty; the 64 successful runs are not released; the repository is an anonymous review link, so persistence is uncertain. The 437-case package (6 frameworks incl. ChatDev / MetaGPT / OpenManus on ProgramDev, 3 backbones) is a different study with a single reviewer, a template reason string and `node_final` as the failure node for every case — not a step-labelled resource.
6. **Overlaps.** Magentic-One and AssistantBench shared with Who&When / TraceElephant / AgentRx (new runs, different backbone); WebArena with LongRCA and HORIZON; the taxonomy maps onto MAST. SymTrace is cited in the report's Proposal 1 as the operational form of counterfactual replay.
