# AgentErrorBench (+ AgentDebug-Traj2k) — AgentDebug

## Identity

- **Full title:** *Where LLM Agents Fail and How They can Learn From Failures* (ICML 2026 listing title: *AgentDebug: Where LLM Agents Fail and How They can Learn From Failures*). Dataset names: **AgentErrorBench** (a.k.a. "Agent Error Benchmark", called *AgentDebugBench* by TrajDebug), **AgentErrorTaxonomy**, and (camera-ready only) **AgentDebug-Traj2k** + the **AgentDebugger-4B** model.
- **Authors / affiliation:** Kunlun Zhu, Zijia Liu, Bingxuan Li, Muxin Tian, Yingxuan Yang, Jiaxun Zhang, Pengrui Han, Qipeng Xie, Fuyang Cui, Weijia Zhang, Xiaoteng Ma, Xiaodong Yu, Gowtham Ramesh, Jialian Wu, Zicheng Liu, Pan Lu, James Zou, Jiaxuan You — University of Illinois Urbana-Champaign (U Lab) with Stanford / AMD / other co-authors.
- **Venue:** ICML 2026 (https://icml.cc/virtual/2026/77923, OpenReview id VIO4WbZuVW). arXiv **2509.25370** (v1, 29 Sep 2025; cs.AI). *Note: the arXiv id given in our brief (2509.23071) is a different paper (EviPath, KDD 2026).*
- **Links:** paper https://arxiv.org/abs/2509.25370 · code https://github.com/ulab-uiuc/AgentDebug (MIT) · data: Google Drive folder linked from the README, https://drive.google.com/drive/folders/1bQe6dQA85pktT63YnKIKJDTVaH3O3Vpu · third-party HF mirror `davide221/agenterrorbench` (same 200 trajectories, parquet, train/val/test split added by the uploader) · re-packaged copy in the TrajDebug repo (`THU-KEG/TrajDebug/data/agentdebugbench`, unified schema).
- **License:** code MIT (`LICENSE`, "U Lab @UIUC"); arXiv paper CC BY-NC-SA 4.0; no explicit license file on the Drive data (upstream ALFWorld / WebShop / GAIA terms apply).
- **Availability:** **downloaded** (AgentErrorBench). The Drive folder as fetched via `gdown` contained 196 trajectory files (98 ALFWorld, 48 GAIA, 50 WebShop) + 3 label files; the 4 missing trajectories (`GPT-4o_002_alfworld_task_002`, `GPT-4o_033_alfworld_task_033`, `Llama3.3-70B-Turbo_014_memory_b001_t00_e05-c9015705`, `Qwen3-8B_014_memory_b001_t00_e04-5e8c1dcf`) were filled from the HF mirror, giving all 200. **AgentDebug-Traj2k and AgentDebugger-4B: not released** — they are mentioned only in the ICML camera-ready abstract (not in arXiv v1), and no artefact exists on GitHub, Hugging Face (`hf search` for Traj2k / AgentDebugger returns nothing from the authors) or the Drive folder as of 2026-10-16.
- **On-disk size:** 124 MB total — `gdrive/` 34 MB (official), `hf_davide221/` 18 MB (parquet mirror), `repo_AgentDebug/` 32 MB (code, vendored envs; no data).
- **Local path:** `/dataDisk/home/thanhdo/failure-attribution-datasets/data/agenterrorbench/` (`gdrive/Label/*.json`, `gdrive/Original_Failure_Trajectory/{ALFWorld,GAIA,WebShop}/*.json`, `hf_davide221/data/*.parquet`, `repo_AgentDebug/`).

## Description

- **Purpose.** Benchmark for *critical error detection* in single-agent LLM trajectories: given a failed rollout, predict (i) the step of the first critical (root-cause) error, (ii) the agent module responsible (memory / reflection / planning / action / system) and (iii) the fine-grained error type from the AgentErrorTaxonomy. It is also the test-bed for the AgentDebug framework, which uses the detected critical step to re-roll the agent from that step with corrective feedback.
- **Construction.** The authors ran their own modular ReAct-style agent (prompts with `<memory>`, `<reflection>`, `<plan>`, `<action>` tags; rollout code in `agentdebug/rollout`) with three backbones (GPT-4o, Llama-3.3-70B-Turbo, Qwen3-8B) on ALFWorld (embodied text game), WebShop (e-commerce browsing) and GAIA (tool-using research assistant), collected >500 failed trajectories, derived the taxonomy from them, and curated **200 representative failed trajectories** (100 ALFWorld, 50 WebShop, 50 GAIA). Failures are **natural** (no injection). Max 30 agent steps per episode (step-limit failures are frequent in ALFWorld).
- **Annotation.** Ten expert annotators (graduate students in NLP/agents) labelled every decision step with taxonomy error type(s) and identified the *minimal set of root-cause failures* explaining the cascade; guidelines refined over three pilot rounds, double annotation on a shared subset with collective adjudication. Reported inter-annotator agreement: Cohen's κ = 0.55 across modules. In the released labels every trajectory carries exactly **one** annotated step (`step_annotations` has one entry, equal to `critical_failure_step`) with one module, one failure type and a free-text reasoning.
- **Labels:** `critical_failure_step` (1-based agent step), `critical_failure_module`, per-step `failure_type` + `reasoning` text. No repair text (the AgentDebug *framework* generates feedback, but it is not part of the data). Single-agent only, so there is no agent-level label.
- **Taxonomy (AgentErrorTaxonomy, 5 modules / 17 types; `detector/error_definitions.py` and paper Table 2):**
  - *Memory:* over-simplification / incomplete summary; hallucination (false memory); retrieval failure.
  - *Reflection:* progress misassessment (`progress_misjudge`); outcome misinterpretation; causal misattribution; hallucination.
  - *Planning:* constraint ignorance; impossible action; inefficient planning.
  - *Action:* planning–action disconnect (`misalignment`); format error; parameter error (+ `invalid_action` in code).
  - *System:* step-limit exhaustion; tool execution error; LLM limit; environment error.
- **Task formulation & metrics (paper §4.1):** input = full failed trajectory; output = (step, module, error type). Metrics: **Step** accuracy (exact step), **Step+Module**, **All-Correct** (step + module + type). Baselines: direct prompting, brute-force re-rollout (substitute a corrected action at each step until success), binary search over the trajectory; detector backbone GPT-4.1, temperature 0.
- **Reported results (paper Table 1, GPT-4.1 backbone):**

| Method | ALFWorld S / S+M / ALL | WebShop S / S+M / ALL | GAIA S / S+M / ALL | Avg S / S+M / ALL |
|---|---|---|---|---|
| Direct Prompting | 28 / 14 / 1 | 30 / 6 / 0 | 26 / 10 / 0 | 28.0 / 10.0 / 0.3 |
| Brute Force | 10 / 5 / 0 | 8 / 0 / 0 | 18 / 8 / 0 | 12.0 / 4.3 / 0.0 |
| Binary Search | 20 / 6 / 1 | 14 / 8 / 0 | 22 / 10 / 0 | 18.7 / 8.0 / 0.3 |
| AgentDebug | 35 / 28 / 21 | 42 / 22 / 14 | 58 / 44 / 38 | 45.0 / 31.3 / 24.3 |

  TrajDebug (EMNLP 2026 Findings) reports step accuracy on the same 200 trajectories: direct prompting 9–19 % (ALFWorld), 20–35 % (GAIA), 14–32 % (WebShop); TrajDebug 26.0 / 38.8 / 26.0. Downstream: AgentDebug feedback + up to 5 re-rollouts gives up to 26 % relative task-success improvement (GPT-4o-mini, Qwen3-8B, Qwen3-Next-80B).
- **AgentDebug-Traj2k (camera-ready only):** "an automated data curation pipeline … a large-scale dataset generated via proposer–reviewer collaboration, where multiple models propose debugging analyses and consolidate them into high-quality annotations"; used to train AgentDebugger-4B, which "outperforms GPT-4.1 in error detection". Size (~2k trajectories, from the name), schema and source environments are not documented in any public artefact we could access (the OpenReview PDF is not publicly downloadable).

## Schema

Official Drive release (`gdrive/`):

- `Label/{alfworld,gaia,webshop}_labels.json` — list of label records:
  - `trajectory_id` (str) — file stem of the trajectory, encodes model and episode (e.g. `Qwen3-8B_014_chat_b000_t00_e14-1d03d2d8`).
  - `LLM` (str) — backbone (`GPT-4o`, `Llama3.3-70B-Turbo`, `Qwen3-8B`).
  - `task_type` (str) — `alfworld` / `gaia` / `webshop`.
  - `critical_failure_step` (int) — 1-based index of the agent turn with the root-cause error (k-th assistant message = message index 2k−1).
  - `critical_failure_module` (str) — module of the critical error (raw values mix `plan`/`planning`, `reflect`/`reflection`).
  - `step_annotations` (list) — `[{"step": k, "<module>": {"failure_type": str, "reasoning": str}}]`; exactly one entry per trajectory.
- `Original_Failure_Trajectory/<Env>/<trajectory_id>.json`:
  - `messages` (list of `{role, content}`) — alternating `user` (task prompt + current observation + admissible actions, or tool/web output for GAIA) and `assistant` (structured `<memory>/<reflection>/<plan>/<action>` text; Qwen3 outputs also contain `<think>`). The first user message holds the task.
  - `metadata` — `batch_idx`, `env_id`, `test_idx`, `model`, `steps` (number of agent turns), `won` (always False), `timestamp`, `environment`, `pid`.

HF mirror (`davide221/agenterrorbench`, parquet): one row per trajectory with `trajectory_id, task_type, llm_model, critical_failure_step, critical_failure_module, failure_types[], failure_reasonings[], failure_modules[], num_steps, trajectory_length (chars), full_trajectory (JSON string of the file above), step_annotations (JSON string)`; splits train 139 / validation 31 / test 30 (uploader's split, not official).

## Statistics (computed from the data; 200 trajectories, all failed)

| quantity | n | mean | median | min | max | p10 | p90 |
|---|---|---|---|---|---|---|---|
| agent steps per trajectory (all) | 200 | 25.07 | 30.0 | 1 | 30 | 5 | 30 |
| agent steps (ALFWorld) | 100 | 30 | 30.0 | 30 | 30 | 30 | 30 |
| agent steps (GAIA) | 50 | 14.34 | 10.0 | 1 | 30 | 1 | 30 |
| agent steps (WebShop) | 50 | 25.92 | 30.0 | 4 | 30 | 9 | 30 |
| messages per trajectory (user+assistant) | 200 | 50.13 | 60.0 | 2 | 60 | 10 | 60 |
| critical step index (1-based) | 200 | 7.92 | 5.0 | 1 | 30 | 2 | 22 |
| critical step relative position (step/len) | 199 | 0.38 | 0.2333 | 0.0333 | 1.0 | 0.0667 | 1.0 |
| annotated steps per trajectory | 200 | 1 | 1.0 | 1 | 1 | 1 | 1 |
| characters per trajectory | 200 | 377685.04 | 197568.0 | 4761 | 5818942 | 73844 | 806318 |

Histogram of agent steps per trajectory:

| steps | n | % |
|---|---|---|
| 0-9 | 32 | 16.0 |
| 10-19 | 8 | 4.0 |
| 20-29 | 5 | 2.5 |
| 30-39 | 155 | 77.5 |
| 40-49 | 0 | 0.0 |
| 50-59 | 0 | 0.0 |
| >=60 | 0 | 0.0 |

Histogram of critical-step relative position:

| rel. position | n |
|---|---|
| 0.0-0.2 | 78 |
| 0.2-0.4 | 53 |
| 0.4-0.6 | 19 |
| 0.6-0.8 | 11 |
| 0.8-1.0 | 38 |

Source benchmark × model:

| env | GPT-4o | Llama3.3-70B-Turbo | Qwen3-8B | total |
|---|---|---|---|---|
| alfworld | 50 | 23 | 27 | 100 |
| gaia | 16 | 17 | 17 | 50 |
| webshop | 15 | 17 | 18 | 50 |

Critical-error module (normalised; raw labels use both `plan`/`planning`, `reflect`/`reflection`):

| module | n | % |
|---|---|---|
| planning | 78 | 39.0 |
| reflection | 40 | 20.0 |
| memory | 38 | 19.0 |
| system | 22 | 11.0 |
| action | 22 | 11.0 |

Critical-error type (module.failure_type at the critical step; labels normalised — raw labels mix `plan`/`planning`, `plan_inefficient`/`inefficient_plan`, and 27 labels have an empty failure_type):

| error type | n | % |
|---|---|---|
| planning.inefficient_plan | 46 | 23.0 |
| reflection.progress_misjudge | 20 | 10.0 |
| memory.over_simplification | 20 | 10.0 |
| planning.constraint_ignorance | 13 | 6.5 |
| reflection.outcome_misinterpretation | 12 | 6.0 |
| memory.hallucination | 12 | 6.0 |
| action.unspecified | 10 | 5.0 |
| planning.impossible_action | 10 | 5.0 |
| planning.unspecified | 9 | 4.5 |
| system.step_limit | 8 | 4.0 |
| system.environment_error | 7 | 3.5 |
| action.misalignment | 7 | 3.5 |
| reflection.causal_misattribution | 5 | 2.5 |
| memory.unspecified | 4 | 2.0 |
| system.tool_execution_error | 4 | 2.0 |
| action.parameter_error | 4 | 2.0 |
| system.unspecified | 2 | 1.0 |
| reflection.unspecified | 2 | 1.0 |
| memory.memory_retrieval_failure | 2 | 1.0 |
| action.invalid_action | 1 | 0.5 |
| reflection.hallucination | 1 | 0.5 |
| system.llm_limit | 1 | 0.5 |

Splits in the third-party HF mirror `davide221/agenterrorbench`: {"train": 139, "validation": 31, "test": 30}

Paper-reported figures for comparison: 200 trajectories (100/50/50); κ = 0.55; "most failures cluster in mid-trajectory steps (6–15)"; memory and reflection dominate in the paper's Figure 3 — in the released labels planning is the largest module (39 %), which suggests the figure counts all per-step tags from the annotation study rather than only the released critical-step label.

## Example trajectory

Chosen: `Qwen3-8B_014_chat_b000_t00_e14-1d03d2d8` (webshop, Qwen3-8B), 4 agent steps, 26267 characters; shortest-by-characters failed trajectory with ≤15 steps whose critical error is not a system error. Each step below = environment observation + the agent's response (the dataset stores alternating user/assistant messages; step k = assistant message 2k−1).

**Source id:** `Qwen3-8B_014_chat_b000_t00_e14-1d03d2d8`  
**Task:** 
You are an expert agent operating in the WebShop e-commerce environment.
Your task is: Find me machine wash men's t-shirts with long sleeve with color: mossy oak bottomland, and size: 5x-large big, and price lower than 50.00 dollars
Your current observation is: 'Search'
Your admissible actions of the current situation are: 'search[<your query>]',
'click[search]',.

Please begin by analyzing the situation and planning your approach:

<plan>
Plan the next step:
- Given what I've learned, what should I do next?
- Please explain why this plan is helpful for the next action?
- What do I expect this action to achieve?
</plan>

<action>
Finally, choose ONE admissible action for the current step and choose it within 'search[<your query>]',
'click[search]',.
</action>


**[step 1] assistant (single ReAct-style agent)**

```text
Observation (environment/user message 0):
(task prompt + initial observation; see `task`)

Agent output (assistant message 1):
<think>
Okay, let's tackle this query. The user wants machine wash men's t-shirts with long sleeves, color mossy oak bottomland, size 5x-large, and under $50. First, I need to parse all the details.

The main challenge is the color: "mossy oak bottomland." That's a specifi […] long sleeve t-shirt mossy oak bottomland 5x large under 50 dollars machine wash]
</action>
```

**[step 2] assistant (single ReAct-style agent)**

```text
Observation (environment/user message 2):

You are an expert agent operating in the WebShop e-commerce environment.
Your task is to: Find me machine wash men's t-shirts with long sleeve with color: mossy oak bottomland, and size: 5x-large big, and price lower than 50.00 dollars
Prior to this step, you have already taken 1 step(s). Below is a compact summary of all steps: - SearchQuery: men's long  […] res the user doesn't miss potential matches.
</plan>

<action>
click[b00o30jldk]
</action>
```

**[step 3] assistant (single ReAct-style agent)**

```text
Observation (environment/user message 4):

You are an expert agent operating in the WebShop e-commerce environment.
Your task is to: Find me machine wash men's t-shirts with long sleeve with color: mossy oak bottomland, and size: 5x-large big, and price lower than 50.00 dollars
Prior to this step, you have already taken 2 step(s). Below is a compact summary of all steps: '''
SearchQuery: men's lon […]  including price, color, and size.
</plan>

<action>
click[mossy oak bottomland]
</action>
```

**[step 4] assistant (single ReAct-style agent)  ⟵ ANNOTATED ERROR STEP**

```text
Observation (environment/user message 6):

You are an expert agent operating in the WebShop e-commerce environment.
Your task is to: Find me machine wash men's t-shirts with long sleeve with color: mossy oak bottomland, and size: 5x-large big, and price lower than 50.00 dollars
Prior to this step, you have already taken 3 step(s). Below is a compact summary of all steps: SearchQuery: men's long sl […] pecified product at the correct price and size.
</plan>

<action>
click[buy now]
</action>
```

**Annotation**

- Faulty agent: `assistant (single agent)`
- Faulty step: `4`
- Category: `reflection.progress_misjudge`
- Reason / root cause: The agent didn't check if machine wash is met. The reflection is not able to recognize this correctly. It should check the product details to see if machine wash is met.
- critical_failure_module: reflection
- step_annotations: [{"step": 4, "reflection": {"failure_type": "progress_misjudge", "reasoning": "The agent didn't check if machine wash is met. The reflection is not able to recognize this correctly. It should check the product details to see if machine wash is met."}}]
- step_numbering: 1-based index of assistant turns (message index 2k-1)
- llm: Qwen3-8B
- env: webshop
- won: False
- Produced answer / final output: <think>
Okay, let's tackle this step by step. The user is looking for a machine wash men's long sleeve t-shirt in mossy oak bottomland color, size 5x-large, under $50. From the history, they already did a search and found a product that matches the color and size, and the price range is within the budget. The product is the Legendary Whitetails Men's Non-Typical Long Sleeve T-Shirt, which is priced between $10.52 and $40.5. The attributes match what the user wants: color is mossy oak bottomland, size is 5x-large, and it's a long sleeve t-shirt. The price is definitely under $50.

Now, looking at the current observation, the available actions include clicking on 'buy now' for that product. Si […] roduct at the correct price and size.
</plan>

<action>
click[buy now]
</action>

## Notes for the report

- **Single-agent, step-level + module + type.** No multi-agent attribution; the "who" is always the one agent, the "when" is a 1-based agent turn. ALFWorld trajectories are uniformly 30 steps (the episode cap), so most ALFWorld failures end in step-limit exhaustion even when the root cause is earlier.
- **Label-quality quirks found in the data:** inconsistent module/type spellings (`plan` vs `planning`, `plan_inefficient`, `Parameter_error`, trailing spaces), 27/200 labels with an empty `failure_type`, and one GAIA record (`GPT-4o_003_memory_b000_t00_e03-21a3a421`) whose labelled step (3) exceeds the stored trajectory length (1 agent turn). Each trajectory carries only one annotated step although the paper describes multi-step annotation.
- **Very long observations:** WebShop/GAIA user messages repeat the whole prompt plus page content each step (median 198 k characters per trajectory, max 5.8 M), which matters for context-window budgets of LLM detectors.
- **Overlaps:** the same 200 trajectories are redistributed (unified message schema, critical step converted to a 0-based message index) by TrajDebug/TrajErrBench as `agentdebugbench_*`; the AgentDebug taxonomy is also reused by TrajDebug's detector. Who&When (GAIA/AssistantBench, multi-agent) is the closest sibling benchmark; AgentErrorBench covers embodied (ALFWorld) and web-shopping environments that Who&When does not.
- **Traj2k gap:** the scalable proposer–reviewer dataset and the 4B detector exist only in the ICML camera-ready; cite them as "announced, not released".
