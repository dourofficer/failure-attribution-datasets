# AgentHallu

## Identity

| Field | Value |
|---|---|
| Full title | **AgentHallu: Benchmarking Automated Hallucination Attribution of LLM-based Agents** |
| Authors | Xuannan Liu, Xiao Yang, Zekun Li, Peipei Li, Ran He (BUPT / CASIA group of Ran He; affiliations not listed on the arXiv abstract page) |
| Venue | arXiv preprint (v1 11 Jan 2026); no peer-reviewed venue listed as of 2026-10-16 |
| arXiv id | 2601.06818 |
| Paper | https://arxiv.org/abs/2601.06818 (HTML: https://arxiv.org/html/2601.06818v1) |
| Project page | https://liuxuannan.github.io/AgentHallu.github.io/ |
| Code + data | https://github.com/liuxuannan/AgentHallu (data is shipped inside the repo under `AgentHallu/<framework>/NNN.json`; no HF dataset exists — `hf search AgentHallu` returns nothing) |
| License | Repo `LICENSE` file: CC BY 4.0. Paper text (Appendix) says CC BY-NC-SA 4.0 for dataset and code — the two statements conflict; treat as CC-BY-family, cite the repo. Source queries: SimpleQA/GPQA/MATH-500/AIME/HLE (MIT), BFCL v3 (Apache-2.0), GAIA (no explicit license). |
| Availability | **Released, downloaded in full** (git clone, depth 1). Not gated. |
| On-disk size | 36 MB (693 JSON files; the trajectories themselves ≈ 16 MB of text) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/agenthallu/repo/AgentHallu/` |

## Description

**Purpose.** AgentHallu defines the task of *automated hallucination attribution of LLM-based agents*: given a user query and the full multi-step trajectory of an agent (or multi-agent) system, (1) judge whether the final answer is hallucinated (binary), (2) localise the single step that is *responsible* for the hallucination, and (3) produce a free-text causal explanation. It is the hallucination-flavoured sibling of Who&When-style failure attribution: the label is a step index plus a category plus a reason, and "hallucination" is operationalised as *final answer ≠ ground truth*.

**How it was built.**
- *Agent frameworks (7):* SmolAgents (ReAct and CodeAct variants), OpenDeepSearch (ReAct / CodeAct), OpenManus, OctoTools, Magentic-One (multi-agent: Orchestrator / Coder / WebSurfer / ComputerTerminal / FileSurfer), OWL (CAMEL-AI; multi-agent: Coordinator / Planner / Search Agent / Developer Agent / Multi-Modal Processing Agent; stored in the `Camel/` folder), and a plain Function-calling Agent used only for BFCL v3 (stored in `BFCL/`).
- *Backbone LLMs:* the six general frameworks were run with GPT-4.1, GPT-4o, GPT-5, Claude-3.7-Sonnet and Qwen2.5-Coder-32B; the function-calling agent with GPT-4.1, Qwen3-32B and Llama-3.3-70B. (Observed `model_id` distribution below.)
- *Source benchmarks / domains (5 domains, 8 datasets):* World Knowledge (SimpleQA), Science (GPQA), Math (MATH-500 levels 3–5, AIME 2024, AIME 2025), General Assistant (GAIA validation), Tool Use (BFCL v3 multi-turn), plus a small HLE supplement.
- *Failures are natural, not injected.* Agents were run on the queries; runs with no final answer and trajectories with ≤2 valid steps were discarded; "trivial" cases on which four LLM judges all agreed were removed so that the retained set is hard. The 693 retained trajectories contain 443 hallucinated and 250 non-hallucinated runs.
- *Annotation protocol.* Ten graduate-level annotators with AI expertise. Pipeline: GPT-5-Thinking and Gemini-2.5-Pro first draft an oracle-guided reasoning path from (question, ground truth, dataset solution); annotators then (i) give the binary judgment, (ii) for hallucinated runs label the category/sub-category, the responsible step and a causal explanation; LLM-drafted attribution references are verified by annotators, disagreements are resolved by discussion and agreed cases are peer cross-checked. The responsible step is defined counterfactually: *a step is responsible if correcting it and re-rolling the remaining steps yields the correct answer; if several qualify, the earliest is the root cause.*
- *Inter-annotator agreement (initial, before adjudication):* judgment 98.9 %, category 81.9 %, step 77.9 % (lowest for Science 72.5 % and General Assistant 69.2 %).
- *Taxonomy construction:* grounded theory (open coding + constant comparison) on a 140-trajectory pilot set.

**Label types.** Trajectory-level binary label (`is_hallucination`), step-level index (`hallucination_step`, 1-based, a single step), category + sub-category from the taxonomy, free-text reason (`hallucination_reason`), plus the dataset's reference solution (`explanation`), ground-truth answer and the agent's final answer. There is *no explicit agent-level label*, but every step carries a `role` (agent name) in the multi-agent frameworks, so the faulty agent is derivable (we do this below).

**Error taxonomy (5 categories, 14 sub-categories; counts over the 443 hallucinated trajectories, computed from the data):**

| Category | Sub-category | Definition (paper) | n |
|---|---|---|---|
| Planning (67) | Fact Derive | plan introduces non-existent / misleading facts | 37 |
| | Task Decompose | sub-goals do not match the task | 30 |
| Retrieval (82) | Query Misalign | inaccurate retrieval query | 18 |
| | Context Misalign | retrieves factually wrong context | 18 |
| | Summarize Misalign | misrepresents retrieved context when summarising | 46 |
| Reasoning (118) | Factual Reasoning | wrong factual inference over context | 18 |
| | Math Reasoning | wrong mathematical inference / computation | 45 |
| | Science Reasoning | wrong scientific inference / computation | 37 |
| | General Reasoning | wrong reasoning on general tasks | 18 |
| Human-Interaction (73) | (single) | incorrect information propagated from the *user* turn (multi-turn settings; the agent trusts a wrong user message) | 73 |
| Tool-Use (103) | Missing Required Call | omits a required tool call | 32 |
| | Incorrect Tool Arguments | mis-specified arguments | 36 |
| | Parallel Call Conflict | conflicting parallel tool calls | 12 |
| | Unnecessary Tool Call | irrelevant / wrong tool invoked | 23 |

**Task formulation and metrics.** Input = query + full trajectory (standard "all-at-once" prompting) or incremental step-by-step prompting that stops at the first detected hallucination. Outputs: binary judgment (macro-F1 / macro-recall / accuracy), *step-localisation accuracy* (exact match of the responsible step index, computed on hallucinated samples only), and explanation quality via G-EVAL (1–5, GPT-5 as judge, graded against the human explanation).

**Baseline numbers (paper Table 4, standard prompting; random baseline: judgment F1 48.5, attribution acc 8.7):**

| Model | Judgment F1 | Step-attribution acc (%) | G-EVAL |
|---|---|---|---|
| GPT-5 | 70.2 | 32.7 | 2.0 |
| GPT-5-mini | 65.0 | 35.0 | 2.0 |
| Gemini-2.5-Pro | 64.6 | **41.1** | 2.4 |
| Gemini-2.5-Flash | 65.3 | 36.3 | 2.1 |
| Claude-4.5-Sonnet | 63.6 | 33.4 | 2.0 |
| DeepSeek-V3.1 | 52.1 | 19.0 | 1.5 |
| Qwen3-32B | 51.8 | 21.2 | 1.3 |
| Qwen3-8B | 49.5 | 15.1 | 0.9 |
| Qwen2.5-72B | 44.3 | 7.7 | 0.6 |
| Qwen2.5-32B | 49.3 | 8.6 | 0.8 |
| Qwen2.5-7B | 43.9 | 6.6 | 0.5 |
| Llama-3.3-70B | 40.4 | 7.2 | 0.4 |
| Llama-3.1-8B | 35.1 | 1.6 | 0.2 |

Tool-use hallucinations are the hardest to localise (best model 14.6 %, GPT-5 4.9 %; the abstract quotes 11.6 % as the best per-category tool-use figure). Step-by-step prompting raises GPT-5 from 32.7 % to 42.7 % at ~3.4× the token cost (7.4k → 25.5k tokens).

## Schema

File layout: `AgentHallu/{BFCL,Camel,Magentic_One,Octotools,OpenDeepSearch,OpenManus,SmolAgents}/NNN.json` — one JSON object per trajectory (164/93/94/47/100/104/91 files). Evaluation code: `inference.py`, `evaluate_metric.py`, `evaluate_geval*.py` (not executed by us).

Top-level fields (present in all 693 records unless noted):

| Field | Meaning |
|---|---|
| `model_id` | backbone LLM id (e.g. `gpt-4.1-2025-04-14`) |
| `agent_type` | framework / variant (`SmolAgents-ReAct`, `SmolAgents-CodeAct`, `OpenDeepSearch-ReAct|CodeAct`, `OpenManus`, `Octotools`, `Magentic-One`, `OWL`, `Function-calling Agent`) |
| `question` | user query |
| `true_answer` | gold answer from the source benchmark |
| `question_source` | source benchmark (`SimpleQA`, `GPQA`, `MATH-500`, `AIME2024`, `AIME2025`, `GAIA`, `HLE`, `BFCL_v3_multi_turn_base`) |
| `question_domain` | one of World Knowledge / Science / Math / General Assistant / Tool Use |
| `explanation` | reference solution / rationale from the source dataset (used by annotators) |
| `history` | list of steps (see below) |
| `agent_answer` | final answer produced by the agent system |
| `is_hallucination` | `"true"` / `"false"` (string) |
| `hallucination_step` | (hallucinated only, 443) integer index of the responsible step, matching `history[i].step` (1-based) |
| `hallucination_category` | (443) one of the 5 categories, e.g. `Tool-Use Hallucination` |
| `hallucination_subcategory` | (443) one of the 14 sub-categories (Human-Interaction repeats the category name) |
| `hallucination_reason` | (443) human-written causal explanation |

Step object in `history`: `step` (int, 1-based), `role` (agent name; present in 4,048 of 5,269 steps — missing for single-agent frameworks such as SmolAgents/OpenDeepSearch where the only actor is the assistant; BFCL steps use `assistant`), `content` (text: thought/plan/message or final answer), `tool_calls` (list of `{name, arguments}`; present in 3,238 steps), `tool_responses` (list of strings, aligned with `tool_calls`). Multi-agent frameworks encode hand-offs as orchestrator steps whose content is e.g. `Call Next Speaker: Coder with arguments: (...)`.

## Statistics

All numbers below are computed from the downloaded data (`scripts/analyze_agenthallu.py`), unless marked *(paper)*.

| Statistic | Value |
|---|---|
| Trajectories | **693** (443 hallucinated = "failed", 250 non-hallucinated = "successful") |
| Per framework (all / hallucinated) | BFCL fn-calling 164/103, OpenManus 104/84, OpenDeepSearch 100/58, Magentic-One 94/54, OWL (Camel) 93/57, SmolAgents 91/57, OctoTools 47/30 |
| Per backbone model | gpt-4.1 316, gpt-4o 124, Qwen3-32B 60, gpt-5 55, Qwen2.5-Coder-32B 55, Llama-3.3-70B 44, claude-3.7-sonnet 39 |
| Per source benchmark (all / hallucinated) | SimpleQA 183/106, BFCL-v3 164/103, GPQA 137/100, MATH-500 76/43, GAIA 68/36, HLE 25/23, AIME2025 24/19, AIME2024 16/13 |
| Per domain | World Knowledge 184, Tool Use 164, Science 147, Math 127, General Assistant 71 |
| Steps per trajectory (all) | mean 7.60, median 6, min 3, max 43; p25 4, p75 10, p90 13 |
| Steps per trajectory (hallucinated) | mean 7.48, median 6, min 3, max 43 |
| Steps histogram | 3–5: 278 · 6–10: 274 · 11–15: 106 · 16–20: 23 · 21–30: 6 · ≥31: 6 |
| Distinct roles per trajectory | mean 1.5, median 1, max 5 (OWL and Magentic-One trajectories have 2–5 roles; the rest have a single actor) |
| Labelled error step (absolute, 1-based) | mean 3.91, median 3, min 1, max 26 |
| Labelled error step, relative position step/len | mean 0.53, median 0.56, min 0.02, max 1.0 |
| Relative-position histogram (deciles 0.0–0.1 … 0.9–1.0, plus =1.0) | 8 · 45 · 55 · 56 · 23 · 48 · 54 · 68 · 48 · 15 · (exactly 1.0: 23) |
| Faulty role (derived from `history[step].role`) | assistant 187, *(no role; single-agent)* 145, Search Agent 31, MagenticOneOrchestrator 25, Developer Agent 19, WebSurfer 15, Coder 14, Planner 5, Multi-Modal Processing Agent 1, null 1 |
| Category distribution | Reasoning 118 · Tool-Use 103 · Retrieval 82 · Human-Interaction 73 · Planning 67 |
| Characters per trajectory (content + tool calls/responses) | mean 23,254, median 4,632, p25 2,429, p75 11,258, p90 31,028, min 520, max 1,113,213 (a few OpenManus/OWL trajectories embed very large tool outputs) |

Machine-readable version: `notes/agenthallu_stats.json`.

## Example trajectory

Chosen record: `Magentic_One/087.json` (Magentic-One, GPT-4.1 backbone, MATH-500, 10 steps, 3 roles, Planning / Fact Derive, responsible step 3). Raw record: `notes/agenthallu_example.json`; normalised: `notes/agenthallu_example_norm.json`.

**Source id:** `Magentic_One/087.json`  
**Task:** Find the number of quadratic equations of the form $x^2 + ax + b = 0,$ such that whenever $c$ is a root of the equation, $c^2 - 2$ is also a root of the equation.  
**Ground truth:** 6  
**Final output of the system:** After following the process, we find that there are **3 distinct quadratic equations** of the form \(x^2 + ax + b = 0\) such that whenever \(c\) is a root, \(c^2-2\) is also a root.  

Steps (10 total):

- **Step 1 — MagenticOneOrchestrator**

  > Here is an initial fact sheet to consider:
  > 
  > 1. GIVEN OR VERIFIED FACTS
  > 
  > - The quadratic equation has the form \( x^2 + a x + b = 0 \).
  > - For every root \( c \) of the equation, \( c^2 - 2 \) is also a root of the same equation.
  > - The request is to find the total number of such equations.
  > 
  > 2. FACTS TO LOOK UP
  > 
  > - None are directly referenced for lookup in the problem statement. There are no external […] braic investigation; the analysis and solution can be handled with Coder's mathematical reasoning.)

- **Step 2 — MagenticOneOrchestrator**

  > Call Next Speaker: Coder with arguments: ("instruction_or_question": Output the first step ('fact_survey') analyzing the condition: If c is a root of x^2 + a x + b = 0, then c^2 - 2 is also a root, and state any immediate relationships between a, b and the roots.).

- **Step 3 — Coder**  ⟵ ANNOTATED ERROR STEP

  > fact_survey
  > 
  > If \( c \) is a root of \( x^2 + a x + b = 0 \), then by Vieta's formulas, the sum of the roots is \(-a\), and the product is \(b\). Denote the two roots by \( c \) and \( d \). The problem specifies that, for every root \( c \), \( c^2-2 \) is also a root of the same equation. This means \( d = c^2-2 \) and \( c = d^2-2 \).
  > 
  > From this, we get two key relationships:
  > 
  > 1. The sum of the […]  \( b \) as above. The number of such \( c \) gives the number of corresponding quadratic equations.

- **Step 4 — MagenticOneOrchestrator**

  > Call Next Speaker: Coder with arguments: ("instruction_or_question": Proceed to make_plan: Develop a multi-step strategy to find all distinct values of c that satisfy the equation c = (c^2 - 2)^2 - 2, and for each such c, compute the corresponding a and b for the quadratic equation x^2 + ax + b = 0. Be sure to enumerate and count the number of qualifying quadratic equations, carrying forward any necessary relationships.).

- **Step 5 — Coder**

  > make_plan
  > 
  > Here is a confident multi-step strategy to solve the problem:
  > 
  > 1. **Rewrite the key equation for \( c \):** Start from the relationship \( c = (c^2 - 2)^2 - 2 \). Expand and simplify it to obtain a quartic polynomial in \( c \), as this will reveal all possible algebraic solutions for \( c \).
  > 
  > 2. **Factor and Solve the Quartic:** Factor the quartic equation wherever possible to find al […] arly always yield four suitable solutions, the answer will be confidently based on this enumeration.

- **Step 6 — MagenticOneOrchestrator**

  > Call Next Speaker: Coder with arguments: ("instruction_or_question": Solve the quartic equation c = (c^2 - 2)^2 - 2 fully (expand to c^4 - 4c^2 + 2c + 2 = 0), enumerate and clearly list all roots (real or complex), and for each root, compute the corresponding values of a and b according to the plan. Finally, count and report the number of distinct quadratic equations of the form x^2 + ax + b = 0 that arise from these roots.).

- **Step 7 — Coder**

  > Plan:
  > 
  > 1. Expand the quartic: \( c = (c^2 - 2)^2 - 2 \rightarrow c^4 - 4c^2 + 2c + 2 = 0 \).
  > 2. Find all roots (\( c \)) of \( c^4 - 4c^2 + 2c + 2 = 0 \).
  > 3. For each \( c \), calculate \( a = -(c^2 + c - 2) \) and \( b = c^3 - 2c \).
  > 4. Output all roots with their (a, b).
  > 5. Count the number of distinct quadratic equations.
  > 
  > Let's implement this.
  > 
  > ```python
  > import sympy as sp
  > 
  > # Define symbol
  > c = […] ads = set(quadratics)
  > print(f"\nNumber of distinct quadratic equations: {len(distinct_quads)}")
  > ```

- **Step 8 — MagenticOneOrchestrator**

  > Call Next Speaker: ComputerTerminal with arguments: ("instruction_or_question": Run the given Python code to solve c^4 - 4c^2 + 2c + 2 = 0, then enumerate all roots and corresponding (a, b), and finally count and report the number of distinct quadratic equations as per instructions.).

- **Step 9 — ComputerTerminal**

  > Action: {"name": "PythonInterpreterTool", "arguments": "import sympy as sp\n\n# Define symbol\nc = sp.symbols('c')\n\n# Quartic equation\neq = c**4 - 4*c**2 + 2*c + 2\n\n# Solve for roots\nroots = sp.solve(eq, c)\n\n# Store quadratic equations (ax, b)\nquadratics = []\n\nfor root in roots:\n    # Compute a and b for each root\n    a = -(root**2 + root - 2)\n    b = root**3 - 2*root\n    # Express  […] 1603781133*I, b = -0.79502225594763 + 1.03262310636755*I
  > 
  > Number of distinct quadratic equations: 4

- **Step 10 — MagenticOneOrchestrator**

  > After following the process, we find that there are **3 distinct quadratic equations** of the form \(x^2 + ax + b = 0\) such that whenever \(c\) is a root, \(c^2-2\) is also a root.

**Annotation:**

- Faulty agent/component: `Coder`
- Faulty step: `3`
- Category: `Planning Hallucination / Fact Derive`
- Reason / root cause: The critical error occurred in Step 3 where the Coder adopted a flawed strategy: reducing the problem solely to solving the quartic equation $c = (c^2-2)^2-2$ and incorrectly assuming a one-to-one correspondence between its roots and the number of quadratic equations, thereby neglecting the necessary case distinctions outlined in the explanation.
- is_hallucination: true
- hallucination_category: Planning Hallucination
- hallucination_subcategory: Fact Derive
- model_id: gpt-4.1-2025-04-14
- agent_type: Magentic-One
- question_source: MATH-500
- question_domain: Math

## Notes for the report

- **What is unique.** The only failure-attribution dataset in this survey whose unit of blame is a *hallucination-responsible step* defined counterfactually (fix the step, re-roll, answer becomes correct), with a *three-level* annotation (binary / step / free-text cause) and a hallucination-specific taxonomy that includes a *Human-Interaction* category (the user turn is the source of the wrong information — 73 cases, all in the OWL/Camel subset in our data) and a *Tool-Use* category with four sub-types. It also contains 250 non-hallucinated trajectories, so it supports the detection (judgment) task, unlike Who&When-style failure-only sets.
- **Mixed single-/multi-agent.** Only Magentic-One (94) and OWL (93) trajectories are multi-agent with explicit `role` names; the other five frameworks are single-agent (role absent or `assistant`). Agent-level attribution is therefore only meaningful on ~27 % of the data; step-level attribution is meaningful everywhere.
- **Short trajectories.** Median 6 steps, 80 % have ≤ 10 steps; the labelled step sits in the middle on average (relative position 0.53), i.e. there is no strong "first step" or "last step" prior to exploit, unlike some injected-error datasets.
- **Natural failures, hard subset.** Failures arise from real runs and trivial cases (all four LLM judges agree) were filtered out — hence low baseline numbers (best 41.1 % step accuracy) even for frontier models.
- **Quirks.** `is_hallucination` is a string, not a boolean. `role` is absent for 1,221 steps. The `Camel` folder is the OWL framework. The license statement differs between the repo (CC BY 4.0) and the paper (CC BY-NC-SA 4.0). The paper's sub-category percentages contain at least one typo (Summarize Misalign listed as 4.6 % vs 46/693 = 6.6 %). Data lives in a GitHub repo, not on HF — reproducibility depends on the repo staying up.
- **Overlaps.** Shares source benchmarks with Who&When / TraceElephant (GAIA), Aegis (GAIA, MATH), AgentRx (BFCL-style tool calling / τ-bench) and MAST (Magentic-One, OpenManus-like frameworks), but the trajectories are new runs; no trajectory-level overlap with other sets is expected.
