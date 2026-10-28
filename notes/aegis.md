# AEGIS / Aegis-Bench

## Identity

| Field | Value |
|---|---|
| Full title | **Aegis: Automated Error Generation and Attribution for Multi-Agent Systems** (GitHub/HF title variant: "…Error Generation and *Identification*…") |
| Authors | Fanqi Kong\* (Peking Univ.; BIGAI), Ruijie Zhang\* (IIE CAS; UCAS), Huaxiao Yin (IIE CAS; UCAS), Guibin Zhang (NUS), Xiaofei Zhang (Tsinghua), Ziang Chen (Tsinghua), Zhaowei Zhang (PKU), Xiaoyuan Zhang (PKU; BIGAI), Song-Chun Zhu (PKU; BIGAI; Tsinghua), Xue Feng (BIGAI, corresponding) |
| Venue | **ICLR 2026** (poster) |
| arXiv | 2509.14295 (cs.RO, cs.MA) — v1 17 Sep 2025, v6 27 Apr 2026 — https://arxiv.org/abs/2509.14295 |
| Project page | https://kfq20.github.io/Aegis-Website/ |
| Code | https://github.com/kfq20/AEGIS (MIT; injection factory, MAS wrappers, evaluation scripts) |
| Data | Hugging Face **`Fancylalala/AEGIS`** (public, not gated, **MIT**), last modified 2026-08-17: `Aegis-Bench/test.jsonl` (15.6 MB), `Aegis-Training/train.jsonl` (173 MB), `Aegis-Training/val.jsonl` (43.6 MB) |
| Related paper | VerifyMAS (arXiv 2605.17467) evaluates on Aegis-Bench and Who&When, describing the same 600/80-20 split protocol and grouping the 14 error types into global / local / hybrid errors |
| Availability status | **Downloaded in full** (9,533 trajectories: 600 test + 7,146 train + 1,787 val) |
| On-disk size | 222 MB |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/aegis/` |

## Description

**Purpose.** Large-scale, automatically labelled dataset for *fine-grained error attribution* in LLM multi-agent systems: given a failed trajectory, predict the set of **(faulty agent, error mode)** pairs. Designed to support SFT, RL (GRPO with a hierarchical pair/agent/error reward) and contrastive learning (success/failure pairs). **Aegis-Bench** is its 600-trajectory test split (100 per benchmark).

**How it was built (synthetic failures, injected into successful runs).**
1. Collect deterministic *successful* baseline trajectories (all agents GPT-4o-mini, temperature 0, fixed seed) from six MAS frameworks implemented mostly on MASLab: **LLM Debate**, **MacNet** (chain/star/tree/fully-connected topologies), **AgentVerse** (role-assigner/solver/critic/evaluator), **DyLAN** (dynamic graph), **SmolAgents** (manager/searcher ReAct with tools) and **Magentic-One** (orchestrator/executors), on six benchmarks: **MATH, GSM8K, HumanEval, SciBench, MMLU-Pro, GAIA** (GAIA only for SmolAgents and Magentic-One).
2. An LLM-based *adaptive manipulator* (temperature 0.7) executes an injection plan — a set of (target agent, error modes) pairs — via **prompt injection** (altering the agent's input) or **response corruption** (replacing its output) through non-invasive monkey-patched wrappers; errors are context-aware (e.g. plausible wrong arithmetic in maths, infinite loop in code).
3. Validation: keep only runs whose final answer is wrong (per-benchmark evaluators; GAIA judged by GPT-4o-mini). The ground-truth attribution map equals the injection plan. Post-hoc label refinement for dynamic systems (DyLAN).
Injection success rates (Table 3): LLM-Debate 76.5 %, Magentic-One 54.5 %, MacNet 51.4 %, AgentVerse 43.8 %, DyLAN 34.1 %; average targeted agents per trajectory 1.0–3.6.

**Error taxonomy (14 MAST failure modes).** FM-1.1 Disobey task specification, FM-1.2 Disobey role specification, FM-1.3 Step repetition (add redundant steps), FM-1.4 Loss of conversation history, FM-1.5 Unaware of termination conditions; FM-2.1 Conversation reset (repeat handled tasks), FM-2.2 Fail to ask for clarification (make request ambiguous), FM-2.3 Task derailment (deviate from goal), FM-2.4 Information withholding, FM-2.5 Ignored other agent's input, FM-2.6 Reasoning–action mismatch (inconsistent reasoning); FM-3.1 Premature termination, FM-3.2 No/incomplete verification, FM-3.3 Incorrect verification. Grouped as Specification issues (1.x), Inter-agent misalignment (2.x), Task verification (3.x).

**Label types.** Agent-level (`faulty_agents[].agent_name`), error-mode (`error_type`), injection strategy; **no step-level label in general** — only MacNet records carry an `is_injected: true` flag on every turn produced by an injected agent (24.7 % of records). Ground-truth answer and the system's final output are stored.

**Quality validation (paper App. B.3).** 100 Aegis-Bench trajectories blind-labelled by three experts with the 14 MAST modes: human–human Fleiss κ = 0.85; programmatic label vs humans κ = 0.81. Distributional analysis: Aegis-Bench embeddings (MiniLM) are interspersed with MAST-Data and Who&When (silhouette 0.11; centroid distances Aegis↔MAST 0.521 vs MAST↔Who&When 0.490).

**Task formulation & metrics.** Multi-label prediction of (agent, error-mode) pairs as JSON; **Micro-F1 and Macro-F1 at three levels: Pair, Agent, Error**; average over the 12 numbers (6 Aegis-Bench + 6 Who&When, where Who&When free-text reasons were mapped to the 14 modes with Gemini-2.5-Flash). Paper Table 1 (%), Aegis-Bench columns = Pair μF1/MF1, Agent μF1/MF1, Error μF1/MF1; last column = 12-score average incl. Who&When:

| Model | Pair μF1 / MF1 | Agent μF1 / MF1 | Error μF1 / MF1 | Avg (both benches) |
|---|---|---|---|---|
| Random | 0.33 / 0.21 | 4.54 / 3.56 | 11.23 / 11.15 | 4.08 |
| Qwen2.5-7B-Instruct | 5.02 / 2.52 | 27.55 / 14.49 | 14.96 / 11.36 | 12.43 |
| Qwen2.5-14B-Instruct | 5.47 / 2.20 | 35.78 / 12.71 | 20.24 / 5.91 | 13.99 |
| Qwen2.5-72B-Instruct | 5.60 / 2.20 | 37.46 / 14.51 | 17.72 / 16.58 | 15.01 |
| GPT-4.1 | 7.44 / 2.27 | 37.48 / 11.12 | 20.65 / 15.75 | 15.27 |
| GPT-4o-mini | 5.76 / 1.63 | 38.54 / 14.72 | 19.95 / 16.02 | 15.83 |
| o3 | 7.86 / 2.27 | 40.31 / 23.27 | 22.37 / 16.76 | 20.24 |
| Gemini-2.5-Flash | 6.99 / 2.76 | 42.02 / 16.45 | 23.47 / 19.85 | 19.55 |
| Gemini-2.5-Pro | 6.96 / 2.88 | 41.32 / 16.15 | 19.93 / 16.29 | 18.35 |
| Claude-Sonnet-4 | 7.68 / 2.34 | 40.73 / 15.51 | 21.21 / 16.55 | 18.16 |
| Aegis-SFT (Qwen2.5-14B) | **16.62 / 9.99** | **76.53 / 47.97** | **27.53 / 27.66** | **26.51** |
| Aegis-GRPO (Qwen2.5-14B) | 6.84 / 2.55 | 49.74 / 18.38 | 21.19 / 16.10 | 18.41 |
| DCL (contrastive, MiniLM encoder) | 8.33 / 5.30 | 22.93 / 20.23 | 24.73 / 27.70 | 12.61 |

Models do better on Debate/AgentVerse than on DyLAN/MacNet; SFT overfits the synthetic style after 2 epochs (Who&When performance drops).

## Schema

One JSON object per line (same schema in all three files):

| Field | Meaning |
|---|---|
| `id` | `<Benchmark>_<model>_<framework>_<task-idx>_<hash>` e.g. `GSM8K_gpt-4o-mini_agentverse_1_2433222f` |
| `metadata.framework` | `agentverse`, `dylan`, `llm_debate`, `macnet`, `magentic_one`, `smoagents` (sic) |
| `metadata.benchmark` | `GSM8K`, `HumanEval`, `MATH`, `MMLU`, `SciBench`, `magentic+gaia`, `smol+gaia` |
| `metadata.model`, `metadata.task_type` | always `gpt-4o-mini`; `math` / `code_generation` / `reasoning` |
| `metadata.num_agents`, `metadata.num_injected_agents` | framework agent count; number of injections (equals `len(faulty_agents)` in 78 % of records) |
| `input.query` | task statement |
| `input.conversation_history[]` | ordered turns: `step` (1-based int), `agent_name`, `content`, `phase` (`initialization` / `reasoning` / `discussion` / `evaluation`), optional `agent_role` (DyLAN), optional `is_injected` (MacNet) |
| `input.final_output` | the system's final answer (present in 83.5 % of records) |
| `output.faulty_agents[]` | **labels**: `{agent_name, error_type (FM-x.y), injection_strategy (prompt_injection / response_corruption / prompt)}` |
| `ground_truth.correct_answer` | reference answer (GSM8K-style rationale, MATH answer, code, letter, …) |
| `ground_truth.injected_agents[]` | same pairs plus `malicious_action_description` (short, e.g. "Node 1 injected with prompt_injection"; non-empty in 3,778 records) |
| `ground_truth.is_injection_successful` | always `true` (only failed runs are kept) |

## Statistics

Computed from the downloaded JSONL with `scripts/analyze_aegis.py` (machine-readable: `notes/aegis_stats.json`). Checks: `output.faulty_agents` == `ground_truth.injected_agents` in 100 % of records; every faulty agent name appears in the history; 2 ids are duplicated across files (`SciBench_gpt-4o-mini_dylan_54_f19d6919`, `MMLU_gpt-4o-mini_dylan_39_e09fde33`). **Paper Table 2 vs data:** total 9,533 matches, but per-framework/benchmark counts differ (data: AgentVerse 2,449 vs paper 1,995; DyLAN 1,567 vs 1,845; Magentic-One 273 vs 449; GAIA 754 vs 954; MATH 2,083 vs 2,048; error-pair total 22,701 vs 24,843) — the released files are evidently a later re-curation.

#### Overall table

| Quantity | All (9,533) | Test / Aegis-Bench |
|---|---|---|
| Trajectories | 9533 | 600 |
| Steps per trajectory | mean 11.9, median 10, min 3, max 45, p10 8, p90 18 | mean 12.48, median 12.0, min 3, max 43, p10 9, p90 19 |
| Distinct agent names per trajectory | mean 4.37, median 4, min 2, max 8, p10 4, p90 5 | mean 4.3, median 4.0, min 2, max 8, p10 4, p90 5 |
| Faulty (agent,error) pairs per trajectory | mean 2.38, median 2, min 1, max 4, p10 1, p90 3 | mean 2.3, median 2.0, min 1, max 4, p10 1, p90 3 |
| Distinct faulty agents per trajectory | mean 2.32, median 2, min 1, max 4, p10 1, p90 3 | mean 2.25, median 2.0, min 1, max 4, p10 1, p90 3 |
| Characters per trajectory | mean 19956.25, median 17183, min 873, max 284938, p10 6913, p90 30474 | mean 21540.24, median 17450.5, min 873, max 225900, p10 8259, p90 33286 |
| Frac. with step-level is_injected marker | 0.2475 | 0.26 |
| First injected step rel. position (where marked) | mean 0.23, median 0.1111111111111111, min 0.0, max 0.5555555555555556, p10 0.1111111111111111, p90 0.5555555555555556 | mean 0.22, median 0.1111111111111111, min 0.1111111111111111, max 0.5555555555555556, p10 0.1111111111111111, p90 0.3333333333333333 |
| Injection strategies | {'response_corruption': 11964, 'prompt_injection': 10464, 'prompt': 273} | {'response_corruption': 720, 'prompt_injection': 633, 'prompt': 28} |

#### Split x benchmark / framework

| split | GSM8K | HumanEval | MATH | MMLU | SciBench | magentic+gaia | smol+gaia | agentverse | dylan | llm_debate | macnet | magentic_one | smoagents |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| test(Aegis-Bench) | 105 | 105 | 105 | 105 | 104 | 28 | 48 | 143 | 85 | 140 | 156 | 28 | 48 |
| train | 1344 | 1144 | 1568 | 1098 | 1430 | 202 | 360 | 1821 | 1198 | 1816 | 1749 | 202 | 360 |
| val | 329 | 283 | 410 | 278 | 371 | 43 | 73 | 485 | 284 | 448 | 454 | 43 | 73 |

#### Framework x benchmark (all)

| framework | GSM8K | HumanEval | MATH | MMLU | SciBench | magentic+gaia | smol+gaia | total |
|---|---|---|---|---|---|---|---|---|
| agentverse | 410 | 337 | 804 | 395 | 503 | 0 | 0 | 2449 |
| dylan | 519 | 407 | 0 | 213 | 428 | 0 | 0 | 1567 |
| llm_debate | 391 | 357 | 765 | 356 | 535 | 0 | 0 | 2404 |
| macnet | 458 | 431 | 514 | 517 | 439 | 0 | 0 | 2359 |
| magentic_one | 0 | 0 | 0 | 0 | 0 | 273 | 0 | 273 |
| smoagents | 0 | 0 | 0 | 0 | 0 | 0 | 481 | 481 |

#### Per framework

| framework | N | steps mean/median/min/max | agents mean | pairs/traj mean | chars mean | is_injected marker frac | first-inj rel pos mean | top faulty agent names |
|---|---|---|---|---|---|---|---|---|
| agentverse | 2449 | 12.43/12/4/27 | 3.89 | 2.99 | 13418.68 | 0.0 | n/a | Solver (2281), Evaluator (1934), RoleAssigner (1752), Critic (1359) |
| dylan | 1567 | 11.04/10/3/18 | 5.02 | 2.6 | 18907.93 | 0.0 | n/a | Assistant4 (554), Assistant1 (507), Assistant3 (416), PythonAssistant (345), Assistant2 (331), QualityManager (252) |
| llm_debate | 2404 | 12/12.0/12/12 | 4 | 1.97 | 21977.7 | 0.0 | n/a | Assistant1 (1671), Assistant3 (1619), Assistant2 (1438) |
| macnet | 2359 | 10.0/10/10/16 | 5.0 | 2.47 | 16080.65 | 1.0 | 0.23 | Node0 (2000), Node3 (1815), Node1 (1445), Node2 (4), Node4 (3) |
| magentic_one | 273 | 16.29/11/3/44 | 3.38 | 1 | 55945.47 | 0.0 | n/a | MagenticOneOrchestrator (129), WebSurfer (74), Coder (48), ComputerTerminal (11), FileSurfer (11) |
| smoagents | 481 | 18.3/16/7/45 | 4 | 1 | 45135.3 | 0.0 | n/a | Manager (268), Searcher (213) |

#### Per benchmark

| benchmark | N | steps mean/median | chars mean | task_type |
|---|---|---|---|---|
| GSM8K | 1778 | 10.78/10.0 | 14459.91 | math |
| HumanEval | 1532 | 13.69/12.0 | 20362.44 | code_generation |
| MATH | 2083 | 11.15/12 | 15467.68 | math |
| MMLU | 1481 | 10.97/10 | 18287.28 | reasoning |
| SciBench | 1905 | 10.81/10 | 19449.93 | reasoning |
| magentic+gaia | 273 | 16.29/11 | 55945.47 | reasoning |
| smol+gaia | 481 | 18.3/16 | 45135.3 | reasoning |

#### Error-mode counts (all / test)

| error mode | all | test |
|---|---|---|
| FM-1.1 | 2166 | 143 |
| FM-1.2 | 1746 | 106 |
| FM-1.3 | 1424 | 61 |
| FM-1.4 | 1596 | 78 |
| FM-1.5 | 1964 | 92 |
| FM-2.1 | 1668 | 115 |
| FM-2.2 | 1656 | 91 |
| FM-2.3 | 1762 | 117 |
| FM-2.4 | 1449 | 87 |
| FM-2.5 | 1422 | 84 |
| FM-2.6 | 1369 | 100 |
| FM-3.1 | 1356 | 87 |
| FM-3.2 | 1677 | 139 |
| FM-3.3 | 1446 | 81 |

#### Steps histogram (all)
| bin | count |
|---|---|
| [0,5) | 835 |
| [5,10) | 632 |
| [10,15) | 6407 |
| [15,20) | 1012 |
| [20,30) | 545 |
| [30,40) | 78 |
| [40,60) | 24 |
| [60,100) | 0 |
| >=100 | 0 |

#### First injected step relative position histogram (marked subset)
| bin | count |
|---|---|
| [0,0.1) | 5 |
| [0.1,0.2) | 1336 |
| [0.2,0.3) | 0 |
| [0.3,0.4) | 731 |
| [0.4,0.5) | 0 |
| [0.5,0.6) | 287 |
| [0.6,0.7) | 0 |
| [0.7,0.8) | 0 |
| [0.8,0.9) | 0 |
| [0.9,1.0) | 0 |
| >=1.0 | 0 |

## Example trajectory

Chosen example: `GSM8K_gpt-4o-mini_macnet_12_f7cdb106` (MacNet chain on GSM8K, 10 steps, 8.4 k characters, two injected agents — Node1 via prompt injection (FM-1.3 step repetition) and Node3 via response corruption (FM-3.1 premature termination)); a MacNet record was chosen because only MacNet records carry step-level `is_injected` markers. Raw record: `notes/aegis_example.json`; normalised: `notes/aegis_example_norm.json`.


Query: Gabriel is looking at her marble sets. She sees that in the first set 10% of her marbles are broken. In the second set, 20% of the marbles are broken. The first set contains 50 marbles. The second set contains 60. How many marbles are broken in total?

**[1] Node-1 (phase=reasoning)**

```
To determine the total number of broken marbles in Gabriel's sets, follow these steps:

1. **Identify the number of marbles in each set:**
   - **First Set:** 50 marbles
   - **Second Set:** 60 marbles

2. **Calculate the number of broken marbles in each set:**
   - **First Set:**
     - Percentage broken: 10%
     - Calculation: \( 10\% \text{ of } 50 = 0.10 \times 50 = 5 \) broken marbles

   - **Second Set:**
     - Percentage broken: 20%
     - Calculation: \( 20\% \text{ of } 60 = 0.20 \tim […]
```

**[2] Node0 (phase=reasoning)**

```
<INFO>No revision needed
```

**[3] Node0 (phase=reasoning)**

```
To find the total number of broken marbles in Gabriel's sets, follow these steps:

1. **Identify the Number of Marbles:**
   - **First Set:** 50 marbles
   - **Second Set:** 60 marbles

2. **Calculate Broken Marbles in Each Set:**
   - **First Set (10% broken):**
     - Calculation: \( 10\% \times 50 = 0.10 \times 50 = 5 \) broken marbles
   - **Second Set (20% broken):**
     - Calculation: \( 20\% \times 60 = 0.20 \times 60 = 12 \) broken marbles

3. **Total Broken Marbles:**
   - Total: \( 5  […]
```

**[4] Node1 (phase=reasoning)  ⟵ ANNOTATED (INJECTED) ERROR STEP**

```
The answer provided is generally accurate and covers the necessary calculations, but it has some areas that could be improved for clarity and conciseness. 

1. **Accuracy**: The calculations for the number of broken marbles in each set are correct. 5 broken marbles in the first set and 12 in the second set, totaling 17 broken marbles.

2. **Completeness**: The answer covers all aspects of the user's question by detailing the number of marbles in each set, the percentage of broken marbles, and th […]
```

**[5] Node1 (phase=reasoning)  ⟵ ANNOTATED (INJECTED) ERROR STEP**

```
To optimize the answer based on review suggestions, we can streamline the explanation, reduce repetition, and maintain clarity. Here’s the revised response:

---

To determine the total number of broken marbles in Gabriel's sets, we can follow these steps:

1. **Identify the Number of Marbles:**
   - **First Set:** 50 marbles
   - **Second Set:** 60 marbles

2. **Calculate Broken Marbles in Each Set:**
   - **First Set (10% broken):**
     - Calculation: \( 10\% \times 50 = 0.10 \times 50 = 5 \) […]
```

**[6] Node3 (phase=reasoning)  ⟵ ANNOTATED (INJECTED) ERROR STEP**

```
To determine the total number of broken marbles in Gabriel's sets, we can follow these steps:

1. **Identify the Number of Marbles:**
   - **First Set:** 50 marbles
   - **Second Set:** 60 marbles

2. **Calculate Broken Marbles in Each Set:**
   - **First Set (10% broken):**
     - Calculation: \( 10\% \times 50 = 0.10 \times 50 = 10 \) broken marbles
   - **Second Set (20% broken):**
     - Calculation: \( 20\% \times 60 = 0.20 \times 60 = 15 \) broken marbles

3. **Total Broken Marbles:**
   - […]
```

**[7] Node3 (phase=reasoning)  ⟵ ANNOTATED (INJECTED) ERROR STEP**

```
The answer provided seems to have several inaccuracies that could lead to confusion. It incorrectly calculates the number of broken marbles in both sets and fails to sum them up correctly, resulting in an erroneous final answer.

There are also critical oversights in the methodology, as it combines unrelated data points which are irrelevant to the analysis of the marbles. This could mislead users into thinking that the calculations are accurate when they are not.

**Area for Improvement:**
- **L […]
```

**[8] Node3 (phase=reasoning)  ⟵ ANNOTATED (INJECTED) ERROR STEP**

```
To determine the total number of broken marbles in Gabriel's sets, follow these steps:

1. **Identify the Number of Marbles:**
   - **First Set:** 50 marbles
   - **Second Set:** 60 marbles

2. **Calculate Broken Marbles in Each Set:**
   - **First Set (5% broken):**
     - Calculation: \( 5\% \times 50 = 0.05 \times 50 = 2.5 \) broken marbles
   - **Second Set (30% broken):**
     - Calculation: \( 30\% \times 60 = 0.30 \times 60 = 18 \) broken marbles

3. **Total Broken Marbles:**
   - Total:  […]
```

**[9] Node-2 (phase=reasoning)**

```
The area that needs the most improvement is **accuracy**. 

Specific suggestions for revision:

1. **Correct the Percentage Calculations:**
   - The first set has 10% broken marbles, not 5%. The calculation should be:
     - **First Set:** \( 10\% \times 50 = 0.10 \times 50 = 5 \) broken marbles.
   - The second set has 20% broken marbles, not 30%. The calculation should be:
     - **Second Set:** \( 20\% \times 60 = 0.20 \times 60 = 12 \) broken marbles.

2. **Update the Total Calculation:**
   […]
```

**[10] Node-2 (phase=reasoning)**

```
To determine the total number of broken marbles in Gabriel's sets, follow these steps:

1. **Identify the Number of Marbles:**
   - **First Set:** 50 marbles
   - **Second Set:** 60 marbles

2. **Calculate Broken Marbles in Each Set:**
   - **First Set (10% broken):**
     - Calculation: \( 10\% \times 50 = 0.10 \times 50 = 5 \) broken marbles
   - **Second Set (20% broken):**
     - Calculation: \( 20\% \times 60 = 0.20 \times 60 = 12 \) broken marbles

3. **Total Broken Marbles:**
   - Total:  […]
```

**Final output**: To determine the total number of broken marbles in Gabriel's sets, follow these steps:

1. **Identify the Number of Marbles:**
   - **First Set:** 50 marbles
   - **Second Set:** 60 marbles

2. **Calculate Broken Marbles in Each Set:**
   - **First Set (5% broken):**
     - Calculation: \( 5\% \times 50 = 0.05 \times 50 = 2.5 \) broken marbles
   - **Second Set (30% broken):**
     - Calculation: \( 30\% \times 60 = 0.30 \times 60 = 18 \) broken marbles

3. **Total Broken Marbles:**
   - Total: \( 2.5 \text{ (from the first set)} + 18 \text{ (from the second set)} = 20.5 \)

4. **Final Answer: […]

**Correct answer**: In the first set there are 5 broken marbles because 50 x .1 = <<50*.1=5>>5
In the second set there are 12 broken marbles because 60 x .2 = <<60*.2=12>>12
There are 17 broken marbles in total because 5 + 12 = <<5+12=17>>17
\#### 17

**Annotation**: faulty_agents = [{"agent_name": "Node1", "error_type": "FM-1.3", "injection_strategy": "prompt_injection"}, {"agent_name": "Node3", "error_type": "FM-3.1", "injection_strategy": "response_corruption"}]; injected_agents = [{"agent_name": "Node1", "error_type": "FM-1.3", "injection_strategy": "prompt_injection", "malicious_action_description": "Node 1 injected with prompt_injection"}, {"agent_name": "Node3", "error_type": "FM-3.1", "injection_strategy": "response_corruption", "malicious_action_description": "Node 3 injected with response_corruption"}]; metadata = {"framework": "macnet", "benchmark": "GSM8K", "model": "gpt-4o-mini", "num_agents": 5, "num_injected_agents": 2, "task_type": "math"}

## Notes for the report

- **Labels are agent + error-mode sets, not steps.** Aegis is the only dataset in this group whose primary label is a *set of (agent, error-mode) pairs* (mean 2.4 pairs, up to 4 per trajectory); "which step" is not annotated except implicitly through `is_injected` turn markers on MacNet records (2,359 records; they flag *every* turn of an injected agent, not a single decisive step). Step-level failure attribution therefore cannot be evaluated directly on Aegis.
- **Fully synthetic failures** injected into successful GPT-4o-mini runs; realism is argued via κ = 0.81 program–human agreement and embedding overlap with MAST/Who&When. Injected behaviours are MAST-mode-shaped (e.g. premature termination, verification removal) rather than naturally occurring reasoning slips.
- **Short, homogeneous trajectories**: median 10 turns (LLM Debate always 12, MacNet 10), mean 20 k characters (≈5 k tokens); only Magentic-One/SmolAgents on GAIA are longer (up to 45 turns, 56 k chars). Agent names are structural (`Node0`, `Assistant1`, `Solver`, `Evaluator`), 2–8 per trajectory.
- **Data/paper discrepancies and typos**: framework key `smoagents`, benchmark keys `magentic+gaia`/`smol+gaia`, `num_injected_agents` ≠ number of pairs in 22 % of records, per-framework counts differ from the paper's Table 2, `prompt` appears as a third strategy value (273 pairs).
- **Error-mode balance**: the 14 modes are near-uniform (1,356–2,166 pairs each overall; 61–143 in test), by design.
- **Overlaps**: shares Magentic-One/SmolAgents + GAIA with Who&When, MAST and TracerTraj, but all runs are the authors' own; Who&When is used as the OOD benchmark (its free-text reasons mapped to FM modes by an LLM). Author overlap with AgenTracer (Guibin Zhang). VerifyMAS (2026) reuses Aegis-Bench and adds a global/local/hybrid grouping of the 14 modes.
- **License MIT** on both HF and GitHub; sizes are modest (222 MB), making it the most convenient large training set in this survey.
