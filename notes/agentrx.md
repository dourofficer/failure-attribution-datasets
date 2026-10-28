# AgentRx Benchmark

## Identity

| Field | Value |
|---|---|
| Full title | **AgentRx: Diagnosing AI Agent Failures from Execution Trajectories** |
| Authors | Shraddha Barke (Microsoft Research), Arnav Goyal (Microsoft; intern), Alind Khare (Microsoft), Avaljot Singh (UIUC; intern), Suman Nath (Microsoft), Chetan Bansal (Microsoft) |
| Venue | **EMNLP 2026 Findings** (per arXiv comments); arXiv v1 2 Feb 2026, v2 31 Aug 2026 |
| arXiv | 2602.02475 (cs.AI) — https://arxiv.org/abs/2602.02475 |
| Blog | https://microsoft.com/en-us/research/blog/systematic-debugging-for-ai-agents-introducing-the-agentrx-framework |
| Data (HF) | `microsoft/AgentRx` — **gated** ("auto" approval mode; `hf download` returns *Access denied. This repository requires approval*). Only `README.md` could be fetched. Card license: **CC-BY-4.0**. Files: `tau_retail.jsonl`, `magentic_one.jsonl` (annotations, config `default`), `tau_retail_dataset.jsonl`, `magentic_dataset.jsonl` (raw trajectories, config `trajectories`). |
| Code + public data subset (GitHub) | https://github.com/microsoft/AgentRx — **MIT**, pushed 2026-09-14. Its `data/` folder ships raw trajectories and ground truth for τ-bench retail (29) and Magentic-One (44 with ground truth, 58 trajectory files), plus domain policies and tool schemas. Flash (internal Microsoft incident-management traces) and the RelWork subset are **not** included. |
| Availability status | HF: gated / access denied. GitHub subset: **downloaded** (shallow clone). Paper v2 describes 170 annotated trajectories (39 τ-bench, 42 Flash, 44 Magentic-One, 45 RelWork); the blog/earlier version describes 115 trajectories from τ-bench, Flash and Magentic-One. The public GitHub subset covers 73 of them. |
| On-disk size | 14 MB (GitHub clone, of which `data/` ≈ 7 MB; HF README 2.5 kB) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/agentrx/github/data/` (ground truth in `ground_truth/`, trajectories in `tau_retail/tau_dataset_failed.json` and `magentic_dataset/*.json`); HF card at `data/agentrx/README.md` |

## Description

**Purpose.** Locate the **critical failure step** — defined as the *first unrecoverable failure by any agent* in a failed execution — and assign it a **root-cause category** from a cross-domain taxonomy. The dataset is the evaluation benchmark for the AgentRx framework (constraint synthesis → step-wise checking → validation log → LLM judge).

**Sources (natural failures, no injection).**
- *τ-bench retail* (single tool-calling agent + LLM-simulated user, domain policy): 115 retail tasks run with gpt-4o, one trial; 39 failed trajectories analysed (29 in the public GitHub subset). Median length 36 steps (range 20–62).
- *Flash* (Microsoft multi-agent incident-management workflow agent): 42 trajectories with at least one agent failure; median 3 steps (each expanding to ≈8 sub-steps). Not released.
- *Magentic-One* (orchestrator + WebSurfer/FileSurfer/Coder/ComputerTerminal on open-ended web/file tasks): 44 failed trajectories **randomly sampled from the Who&When dataset** (hand-crafted subset, GAIA-style queries). Median 33 steps (range 5–130).
- *RelWork* (paper v2 only): 45 trajectories, five from each of nine task settings of MAST (7 domains) and Who&When (algorithm-generated and hand-crafted); annotated under the frozen taxonomy as a held-out check. Not released.

**Annotation protocol.** Grounded-theory open coding by **three annotators**, two phases: (1) *exhaustive failure marking* — every step where the agent fails to make progress is recorded with step index, open code and reason (even later-recovered ones); (2) *critical failure identification* — the earliest failure in the causal chain from which the agent never recovers; its category is the trajectory's root-cause label. Codes were merged iteratively until saturation, then frozen (closed coding for remaining/earlier trajectories). **Inter-annotator agreement:** on 30 trajectories (τ-bench, Flash, Magentic-One) annotated by all three, pairwise Cohen's κ = 0.93 / 0.87 / 0.90, **mean κ = 0.89**. Cost: 20 min (τ-bench), 22 min (Flash, RelWork), 24 min (Magentic) per trajectory; 62.5 human hours for 170 trajectories.

**Taxonomy (9 root-cause categories; the code adds a 10th "Inconclusive").** 1 Instruction/Plan Adherence Failure; 2 Invention of New Information; 3 Invalid Invocation; 4 Misinterpretation of Tool Output; 5 Intent–Plan Misalignment; 6 Under-specified User Intent; 7 Intent Not Supported; 8 Guardrails Triggered; 9 System Failure. Exactly one label at the critical step; a yes/no checklist disambiguates (e.g. plan wrong → Intent–Plan Misalignment vs plan right but not followed → Adherence).

**Label types.** Step-level (`step_number` of each failure event and of the root cause), agent-level (`failed_agent`), category (`failure_category`), free-text reasons (`step_reason`, `category_reason`, `reason_for_root_cause`, `failure_summary`). A trajectory may carry many failure events (Magentic-One: 295 failures over 44 trajectories, 68 % with ≥2); the root cause is one of them by `failure_id`.

**Paper Table 1 — distribution of critical-failure labels (% of failed trajectories per domain).**

| Category | τ-bench (39) | Flash (42) | Magentic (44) | RelWork (45) |
|---|---|---|---|---|
| Instr./Plan Adherence | 20.5 | 23.8 | 18.2 | 33.3 |
| Invention of Information | 2.6 | 9.5 | 9.1 | 17.8 |
| Invalid Invocation | 0 | 0 | 0 | 2.2 |
| Misinterpretation of Output | 20.5 | 33.3 | 34.1 | 33.3 |
| Intent–Plan Misalignment | 15.4 | 0 | 9.1 | 6.7 |
| Under-specified Intent | 33.3 | 19.0 | 0 | 0 |
| Intent Not Supported | 5.1 | 0 | 6.8 | 2.2 |
| Guardrails Triggered | 0 | 0 | 20.5 | 2.2 |
| System Failure | 2.6 | 14.3 | 2.3 | 0 |

**Size (paper Table 6):** avg tokens/step 133 (τ), 169 (Flash), 330 (Magentic), 393 (RelWork); avg tokens/trajectory 4,889 / 6,415 / 16,484 / 5,837.

**Task formulation & metrics.** Input: failed trajectory (normalised IR), tool schema, optional domain policy. Output: critical step ŝ, category ŷ (and failed agent). Metrics: exact step accuracy, Acc@±1/±3/±5, average step distance; category accuracy vs the critical failure ("critical"), vs any annotated failure, vs the earliest and vs the terminal failure; failed-agent accuracy. Runs n = 3, gpt-5 judge by default.

**Reported baselines (paper Table 3, gpt-5; mean ± std over 3 runs; W&W\* = Who&When all-at-once prompt adapted to the first-unrecoverable-failure definition).**

| Dataset | Method | Agent Acc | Step Acc | Category Acc |
|---|---|---|---|---|
| τ-bench | W&W\* | 65 ± 1.5 | 18.8 ± 5.3 | – |
| τ-bench | AgentRx | 66.7 | 42.7 ± 1.5 | 47 ± 1.5 |
| Magentic | W&W\* | 61.4 ± 6.8 | 22.7 ± 3.9 | – |
| Magentic | AgentRx | 71.2 ± 1.1 | 36.4 | 46.2 ± 1.3 |
| Flash | W&W\* | 16.1 ± 1.2 | 64.3 ± 3.9 | – |
| Flash | AgentRx | 82.5 ± 1.4 | 82.5 ± 1.4 | 65.9 ± 5 |
| RelWork | W&W\* | 57 ± 6.8 | 32.6 ± 1.3 | – |
| RelWork | AgentRx | 65.9 ± 5 | 61.5 ± 4.2 | 59.3 ± 2.1 |

Judge-only baseline (no constraint evidence, Table 7): step acc 29.9 (τ), 80.2 (Flash), 32.6 (Magentic), 51.9 (RelWork); Acc@±5 68.4 / 100 / 52.3 / 88.9. o3 and DeepSeek-V3.2 results are in the paper's Tables 8–9.

## Schema

**HF card (gated) — annotation rows** (`tau_retail.jsonl`, `magentic_one.jsonl`): `trajectory_id` (str), `failure_summary` (str), `failures` (list of {`failure_id`, `step_number` (int), `step_reason`, `failure_category`, `category_reason`, `failed_agent`}), `root_cause` ({`failure_id`, `reason_for_root_cause`}), `root_cause_failure_id`, `root_cause_reason`, `num_failures` (int). Raw trajectories are in the `trajectories` config (`tau_retail_dataset.jsonl`, `magentic_dataset.jsonl`).

**GitHub public subset** (`data/`):

```
ground_truth/tau_ground_truth.json          # list of 29 annotation dicts (same fields as above, minus num_failures/root_cause_* copies)
ground_truth/tau_retail.json                # older 24-record version of the same
ground_truth/magentic_one_ground_truth.json # 44 annotation dicts
tau_retail/tau_dataset_failed.json          # 29 τ-bench runs: {task_id, reward, info{task{user_id, actions, instruction, outputs}, reward_info}, traj[], trial, records}
magentic_dataset/<id>.json                  # 58 Magentic-One logs: list of {content, role}; steps_by_id.json = step counts
magentic_dataset_whowhen/<id>.json          # 16 of the same logs (Who&When-format copies)
policies/{retail_policy.txt, magentic_policy.txt}; tool_schemas/
```

- τ-bench `traj[]` items are OpenAI chat messages: `role` ∈ {system (retail policy), user (simulated customer), assistant (optionally with `tool_calls`), tool (with `name`, `tool_call_id`)}. **`step_number` is the 1-based position in `traj` including the system message** (verified: task 2, step 7 = assistant "11 available T-shirt options").
- Magentic-One items: `role` ∈ {`human`, `Orchestrator (thought)`, `Orchestrator (-> WebSurfer)`, `WebSurfer`, `FileSurfer`, `Coder`, `Assistant`, `Orchestrator (termination condition)`, …}; `step_number` is the 1-based list index (verified: trajectory 5f982798, step 33 = FileSurfer "Error 404 File not found").

## Statistics

Computed **from the public GitHub subset (73 trajectories with ground truth: 29 τ-bench retail + 44 Magentic-One)** with `scripts/analyze_agentrx.py`; machine-readable in `notes/agentrx_stats.json`. Flash and RelWork are not public; paper-level numbers are in the Description above. The Magentic-One root-cause category distribution recomputed here matches paper Table 1 exactly (15/44 = 34.1 % Misinterpretation, 9/44 = 20.5 % Guardrails, 8/44 = 18.2 % Adherence, …); the τ-bench subset (29 of 39) differs slightly from the paper's 39-trajectory column. Note: agent-level labels on τ-bench are just `Assistant` vs `User` (single-agent setting). Relative position uses (step−1)/(T−1) with T the number of messages.

#### Stats table

| Quantity | tau_retail | magentic_one | all public |
|---|---|---|---|
| Steps per trajectory | mean 36.69, median 36, min 20, max 62, p10 26, p90 48 | mean 50.02, median 31.5, min 5, max 130, p10 9, p90 124 | mean 44.73, median 33, min 5, max 130, p10 16, p90 113 |
| Distinct agents per trajectory | mean 3, median 3, min 3, max 3, p10 3, p90 3 | mean 3.41, median 3.0, min 2, max 5, p10 3, p90 4 | mean 3.25, median 3, min 2, max 5, p10 3, p90 4 |
| Annotated failure events per trajectory | mean 1.34, median 1, min 1, max 4, p10 1, p90 2 | mean 6.7, median 3.0, min 1, max 55, p10 1, p90 19 | mean 4.58, median 2, min 1, max 55, p10 1, p90 9 |
| Root-cause step (1-based) | mean 24.69, median 21, min 7, max 57, p10 11, p90 37 | mean 14.36, median 10.5, min 2, max 56, p10 4, p90 31 | mean 18.47, median 17, min 2, max 57, p10 5, p90 34 |
| Root-cause relative position (step-1)/(T-1) | mean 0.67, median 0.72, min 0.18181818181818182, max 1.0, p10 0.24390243902439024, p90 0.972972972972973 | mean 0.47, median 0.3169642857142857, min 0.02459016393442623, max 1.0, p10 0.05172413793103448, p90 1.0 | mean 0.55, median 0.5625, min 0.02459016393442623, max 1.0, p10 0.1, p90 1.0 |
| Characters per trajectory | mean 18656.38, median 16648, min 10946, max 39508, p10 12769, p90 23791 | mean 64032.27, median 34990.5, min 6221, max 305187, p10 13937, p90 153622 | mean 46006.23, median 23084, min 6221, max 305187, p10 13853, p90 122244 |
| Trajectories | 29 | 44 | 73 |
| Root cause == first annotated failure | 0.931 | 0.5909 | 0.726 |
| Trajectories with >=2 failure events | 0.2414 | 0.6818 | 0.5068 |
| Root-cause step within range | 1.0 | 1.0 | 1.0 |

#### Root-cause category (canonicalised) per domain

| category | tau_retail | magentic_one | all |
|---|---|---|---|
| Guardrails Triggered | 0 | 9 | 9 |
| Instruction/Plan Adherence Failure | 3 | 8 | 11 |
| Intent Not Supported | 2 | 3 | 5 |
| Intent-Plan Misalignment | 7 | 4 | 11 |
| Invalid Invocation | 1 | 0 | 1 |
| Invention of New Information | 0 | 4 | 4 |
| Misinterpretation of Tool Output | 7 | 15 | 22 |
| System Failure | 1 | 1 | 2 |
| Under-specified User Intent | 8 | 0 | 8 |

#### Raw category labels found in ground truth (root cause)

- Misinterpretation of Tool Output: 22
- Intent Plan Misalignment: 11
- Guardrails Triggered: 9
- Underspecified User Intent: 8
- Instruction/Plan Adherence Failure: 8
- Invention of new information: 4
- Instruction Adherence Failure: 3
- Intent not supported: 3
- Intent Not Supported: 2
- System Failure: 2
- Invalid Invocation: 1

#### All annotated failure events (not only root cause), canonicalised

- Instruction/Plan Adherence Failure: 203
- Misinterpretation of Tool Output: 31
- Intent-Plan Misalignment: 27
- Intent Not Supported: 24
- Guardrails Triggered: 24
- Under-specified User Intent: 10
- Invention of New Information: 8
- Invalid Invocation: 5
- System Failure: 2

#### Root-cause failed agent

- **tau_retail**: Assistant (21), User (8)
- **magentic_one**: Orchestrator (23), WebSurfer (16), Websurfer (2), Assistant (2), FileSurfer (1)

#### Steps histogram
| bin | count |
|---|---|
| [0,10) | 5 |
| [10,20) | 6 |
| [20,30) | 19 |
| [30,40) | 14 |
| [40,60) | 15 |
| [60,80) | 2 |
| [80,100) | 4 |
| [100,130) | 6 |
| >=130 | 2 |

#### Relative root-cause position histogram
| bin | count |
|---|---|
| [0,0.1) | 7 |
| [0.1,0.2) | 7 |
| [0.2,0.3) | 10 |
| [0.3,0.4) | 5 |
| [0.4,0.5) | 2 |
| [0.5,0.6) | 8 |
| [0.6,0.7) | 5 |
| [0.7,0.8) | 8 |
| [0.8,0.9) | 7 |
| [0.9,1.0) | 4 |
| >=1.0 | 10 |

## Example trajectory

Chosen example: Magentic-One trajectory `e6bc98089608217e45b6956a46518fe3cce64a799b3ac43c6974c449ae14c408` (8 steps, 9.2 k characters, two annotated failures of which the second is the root cause — it illustrates the "first *unrecoverable* failure" convention). Raw record (ground truth + trajectory): `notes/agentrx_example.json`; normalised: `notes/agentrx_example_norm.json`.


Task: What's the highest price a high-rise apartment was sold for in Mission Bay, San Francisco, in 2021?


**[1] human**

```
What's the highest price a high-rise apartment was sold for in Mission Bay, San Francisco, in 2021?

```

**[2] Orchestrator (thought)**

```
Initial plan:

We are working to address the following user request:

What's the highest price a high-rise apartment was sold for in Mission Bay, San Francisco, in 2021?


To answer this request we have assembled the following team:

Assistant: A helpful and general-purpose AI assistant that has strong language skills, Python skills, and Linux command line skills.
ComputerTerminal: A computer terminal that performs no other action than running Python scripts (provided to it quoted in ```python c […]
```

**[3] Orchestrator (thought)**

```
Updated Ledger:
{
  "is_request_satisfied": {
    "reason": "The request has not been satisfied as we have not yet identified the highest selling price for a high-rise apartment in Mission Bay, San Francisco, in 2021.",
    "answer": false
  },
  "is_in_loop": {
    "reason": "The tasks and questions are progressing towards finding the information, and there's no indication of repeating actions yet.",
    "answer": false
  },
  "is_progress_being_made": {
    "reason": "We are making progress by […]
```

**[4] Orchestrator (-> WebSurfer)**

```
Please search for the highest price a high-rise apartment was sold for in Mission Bay, San Francisco, in 2021. Check websites like Zillow, Redfin, Realtor.com, or local news outlets like the San Francisco Chronicle. Report back the highest selling price you find.
```

**[5] WebSurfer  ⟵ other annotated failure**

```
I typed 'highest price high-rise apartment sold Mission Bay San Francisco 2021' into '0 characters out of 2000'.

Here is a screenshot of [highest price high-rise apartment sold Mission Bay San Francisco 2021 - Search](https://www.bing.com/search?q=highest+price+high-rise+apartment+sold+Mission+Bay+San+Francisco+2021&form=QBLH&sp=-1&lq=0&pq=&sc=0-0&qs=n&sk=&cvid=A0A2F14E955F4D08B290B29A975075DF&ghsh=0&ghacc=0&ghpl=). The viewport shows 35% of the webpage, and is positioned at the top of the page […]
```

**[6] Orchestrator (thought)**

```
Updated Ledger:
{
  "is_request_satisfied": {
    "reason": "The highest price found for a high-rise apartment sold in Mission Bay, San Francisco, in 2021, is $1.08 billion for 1800 Owens Street.",
    "answer": true
  },
  "is_in_loop": {
    "reason": "The request has been successfully addressed with the required information.",
    "answer": false
  },
  "is_progress_being_made": {
    "reason": "The request has been resolved with the discovery of the highest selling price.",
    "answer": tru […]
```

**[7] Orchestrator (thought)  ⟵ ANNOTATED ERROR STEP (root cause)**

```
Request satisfied.
```

**[8] Orchestrator (termination condition)**

```
No agent selected.
/workspace/scenario.py:94: UserWarning: Resolved model mismatch: gpt-4o-2024-08-06 != gpt-4o-2024-05-13. Model mapping may be incorrect.
  response = await client.create(messages)
FINAL ANSWER: 1080000000
SCENARIO.PY COMPLETE !#!#
RUN.SH COMPLETE !#!#
```

**Annotation**: failures = [{"failure_id": 1, "step_number": 5, "step_reason": "Webusurfer worked on 35% of the webpage", "failure_category": "Instruction/Plan Adherence Failure", "category_reason": "Websurfer worked on 35% of the webpage despite orchestrator asking for complete information", "failed_agent": "Websurfer"}, {"failure_id": 2, "step_number": 7, "step_reason": "Orchestrator said request satisfied on incomplete information", "failure_category": "Misinterpretation of Tool Output", "category_reason": "Orchestrator said request satisfied without on incomplete information even though websurfer had worked on partial webpage", "failed_agent": "Orchestrator"}]

root_cause = {"failure_id": 2, "reason_for_root_cause": "The orchestrator failed to ensure that the websurfer had gathered complete information before concluding that the request was satisfied."}

failure_summary = The orchestrator prematurely concluded that the user's request was satisfied based on incomplete data provided by the websurfer agent.

## Notes for the report

- **Gated on HF** (CC-BY-4.0, approval required) but the **GitHub repo (MIT) ships a usable 73-trajectory subset** with identical annotation schema; the proprietary Flash traces (42) and the RelWork subset (45) are not public, and HF only lists τ-retail and Magentic-One splits anyway.
- **Definition differs from Who&When.** The target is the first *unrecoverable* failure, not the first failure: in 27 % of the public trajectories (41 % of Magentic-One) the root cause is *not* the first annotated failure event, because the orchestrator recovered from earlier ones (paper App. C, trajectory 5f982798: Who&When marks step 3, AgentRx marks step 33).
- **Overlap with Who&When.** All 44 Magentic-One trajectories are sampled from Who&When's hand-crafted subset (file names are GAIA task ids / Who&When hashes; 16 copies are even stored in Who&When format). Evaluations on both benchmarks are therefore not independent.
- **Multi-failure timelines.** Every failure event is annotated (mean 6.7 events per Magentic-One trajectory, up to 55), which supports "any-failure", "earliest" and "terminal" category metrics beyond root-cause accuracy.
- **Label hygiene.** Category strings are inconsistent across records (`Instruction Adherence Failure` vs `Instruction/Plan Adherence Failure`, `Intent Plan Misalignment` vs `Intent-Plan Misalignment`, `Underspecified`/`Under-specified`, `Websurfer`/`WebSurfer`); one record stores `failure_id` as a string. Canonicalise before scoring. `failed_agent` can be `User` (under-specified intent) — i.e. blame may fall on the simulated user, not an agent.
- **Mostly single- or few-agent.** τ-bench is single-agent (Assistant/User/tools); Magentic-One has 2–5 roles. Agent-level accuracy is thus easy; the interesting target is the step + category.
- **Step granularity**: one message = one step (tool results are separate steps); τ-bench steps include the system prompt at index 1. Trajectories are short-to-medium (public set: median 33 messages, max 130; ≈5–16 k tokens per paper Table 6).
- Related artefacts: the AgentRx pipeline (IR normaliser, invariant generator, checker, judge) is in the same repo and was also run on all 1,022 MAST trajectories (no gold labels there).
