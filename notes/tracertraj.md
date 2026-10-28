# TracerTraj (AgenTracer data release)

## Identity

| Field | Value |
|---|---|
| Full title | **AgenTracer: Who Is Inducing Failure in the LLM Agentic Systems?** (dataset: *TracerTraj* / "TracerTraj-2.5K"; model: AgenTracer-8B) |
| Authors | Guibin Zhang, Junhao Wang, Junjie Chen, Wangchunshu Zhou (OPPO), Kun Wang, Shuicheng Yan; affiliations listed on the paper: OPPO, NUS, CUHK, NTU (contact guibinz@outlook.com) |
| Venue | **ICLR 2026** (poster) |
| arXiv | 2509.03312 (cs.CL, cs.MA) — v1 3 Sep 2025, v2 4 Sep 2025 — https://arxiv.org/abs/2509.03312 |
| Project page | https://bingreeky.github.io/atracer/ |
| Code | https://github.com/bingreeky/AgenTracer (data-curation pipeline, MetaGPT working example; 106 stars) |
| Data | GitHub release **`data-v1.0.0`** (27 Aug 2026): `agentracer-data-v1.0.0.zip`, 24.0 MB, SHA-256 `a4615b2d…826d` (verified). **No Hugging Face release** found (searched "AgenTracer", "TracerTraj"). **Model weights (AgenTracer-8B) are not released** ("internal considerations"). |
| License | Not stated in the release archive or README; the repository carries no explicit data license (treat as research-use; cite the paper) |
| Availability status | **Downloaded in full** (expanded release: 3,208 train + 790 test = 3,998 trajectories; the README warns it is *not identical* to the paper's TracerTraj-2.5K and contains additional samples) |
| On-disk size | 158 MB (24 MB zip + 135 MB extracted JSONL) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/tracertraj/extracted/agentracer-data-v1.0.0/{agentic,coding,math}/{train,test}.jsonl` |

## Description

**Purpose.** Large-scale *training* resource (plus held-out test splits) for failure attribution in LLM agentic systems: given a failed multi-agent trajectory, output the failure-responsible agent i\* and the decisive error step t\* (earliest step whose correction would turn failure into success — the Who&When definition). Used to RL-train AgenTracer-8B (Qwen3-8B, GRPO with a multi-granular reward: format gate × [0.5·Gaussian step reward + 0.5·agent-match]).

**How it was built (fully automatic, no human annotation).**
1. *Collection*: run six multi-agent systems — MetaGPT, AutoGen, Smolagents (hand-crafted), AgentPrune (partially automated), AFlow and OWL-Workforce (fully automated) — on six/seven benchmarks: coding (MBPP+, KodCode, Blackjack), maths (MATH, GSM8K), general agentic (GAIA, HotpotQA). Split raw runs into successful and failed corpora.
2. *Counterfactual replay* (failed runs): an analyzer agent (DeepSeek-R1) with access to the trajectory, environment feedback and the ground-truth solution proposes a minimally corrected action at each step t; the trajectory is re-simulated from t; the earliest t whose correction yields success is labelled the decisive error (agent = the one acting at t).
3. *Programmatic fault injection* (successful runs): a perturbation operator (DeepSeek-R1) corrupts the action at a sampled step; if the re-simulated run fails, that step/agent is the decisive error by construction.
Paper composition (Table 3): curated trajectories 2,170 (coding) / 1,185 (math) / 1,300 (agentic); annotated TracerTraj-2.5K = 1,288 / 630 / 558; test 147 / 63 / 56 (9:1 held-out). The released v1.0.0 archive is larger (coding 1,141+127, math 567+63, agentic 1,500+600) and curated from a different data version; e-mail addresses and credential-like strings were replaced by placeholders (690 e-mail and 88 credential occurrences redacted, per MANIFEST).

**Label types.** Agent-level (`mistake_agent`), step-level (`mistake_step`), free-text `mistake_reason` and reference `ground_truth` (coding/math only); `error_source` ∈ {Injection Error, Diagnosis Error} (agentic only — "Injection Error" = fault-injected sample, "Diagnosis Error" = counterfactually diagnosed natural failure). No failure-mode taxonomy.

**Task formulation & metrics.** All-at-once attribution; outputs `<agentID> | <stepID>`; **agent-level accuracy** and **step-level accuracy**, each reported *with* (w/ G) and *without* (w/o G) access to the task ground truth. Evaluation on Who&When (hand-crafted / automated) and on the TracerTraj test splits.

**Reported baselines (paper Table 2, TracerTraj test splits; cells = w/ G / w/o G, accuracy %).**

| Model | Code agent | Code step | Math agent | Math step | Agentic agent | Agentic step |
|---|---|---|---|---|---|---|
| Qwen3-8B | 45.35/32.99 | 2.36/1.15 | 31.74/33.58 | 9.52/12.96 | 27.93/30.16 | 13.49/15.31 |
| Qwen3-32B | 62.99/63.78 | 2.36/1.75 | 17.46/17.46 | 4.76/7.93 | 30.55/30.55 | 18.60/15.31 |
| GPT-4.1 | 59.84/53.54 | 12.59/11.02 | 39.55/35.18 | 35.81/26.63 | 43.61/40.67 | 24.99/25.69 |
| DeepSeek-R1 | 11.81/11.81 | 10.23/10.23 | 42.68/38.58 | 29.52/18.51 | 45.12/46.19 | 27.13/21.80 |
| Gemini-2.5-Pro | 70.07/66.92 | 11.02/6.29 | 58.79/58.79 | 32.22/27.40 | 37.16/32.18 | 18.60/17.04 |
| Claude-Sonnet-4 | 65.98/63.78 | 15.51/11.02 | 46.03/50.79 | 38.10/46.03 | 55.20/49.13 | 30.33/29.80 |
| AgenTracer-8B | **72.95/72.21** | **18.85/18.85** | **59.32/66.10** | **57.63/57.63** | 53.28/50.61 | **36.17/35.55** |

On Who&When (Table 1, w/ G / w/o G): AgenTracer-8B 69.10/63.82 agent and 20.68/20.68 step (hand-crafted), 69.62/63.73 agent and 42.86/37.30 step (automated); Claude-Sonnet-4 56.90/50.00, 17.24/18.97, 57.93/51.11, 40.65/38.83; DeepSeek-R1 56.90/53.44, 13.29/6.90, 66.67/65.08, 31.32/29.52.

## Schema

```
agentracer-data-v1.0.0/
  README.md, MANIFEST.json            # row counts, SHA-256 per file, field lists, redaction counts
  agentic/{train,test}.jsonl          # 1,500 / 600 rows
  coding/{train,test}.jsonl           # 1,141 / 127 rows
  math/{train,test}.jsonl             # 567 / 63 rows
```

| Field | Domains | Meaning |
|---|---|---|
| `question_ID` | all | task id (e.g. KodCode `Filter_5086_I`, GAIA-style uuid, `<hash>_<n>` for math) — **not unique**: 118 math ids occur in several rows (different injected variants of the same task), 21 ids appear in both train and test (histories differ) |
| `question` | all | task statement given to the system |
| `history` | all | list of steps; `step` (int; **1-based in agentic, 0-based in coding/math**), `content` (str), `role` (chat role), `name` (agent name; **absent in agentic**, where `role` is always the generic `assistant`) |
| `mistake_agent` | all | responsible agent name (coding: MetaGPT roles Engineer/Product Manager/Team Leader/Architect/Data Analyst; math: AFlow operator names such as `Custom`, `reasoning expert`; agentic: always `assistant`) |
| `mistake_step` | all | decisive error step, stored as a **string** (e.g. `"6"`), refers to `history[].step` (always found) |
| `mistake_reason` | coding, math | free-text explanation produced by the annotation pipeline |
| `ground_truth` | coding, math | reference solution / answer |
| `error_source` | agentic | `Injection Error` (fault injection) or `Diagnosis Error` (counterfactual diagnosis of a natural failure) |

## Statistics

Computed from the released archive with `scripts/analyze_tracertraj.py` (machine-readable: `notes/tracertraj_stats.json`). Relative error position = index of the error step within the history / (T−1).

#### Split table

| Domain/split | N | steps mean/median/min/max | chars mean | agents mean | rel. error pos mean | error_source | sender@root==agent | generic 'assistant' only |
|---|---|---|---|---|---|---|---|---|
| agentic/train | 1500 | 9.36/7.0/4/42 | 35973.75 | 1 | 0.55 | {'Injection Error': 1306, 'Diagnosis Error': 194} | 1.0 | 1.0 |
| agentic/test | 600 | 9.33/7.0/4/39 | 35335.68 | 1 | 0.57 | {'Injection Error': 516, 'Diagnosis Error': 84} | 1.0 | 1.0 |
| coding/train | 1141 | 20.87/14/1/304 | 35578.51 | 2.33 | 0.46 | {None: 1141} | 1.0 | 0.0 |
| coding/test | 127 | 20.8/13/2/151 | 35228.13 | 2.3 | 0.42 | {None: 127} | 1.0 | 0.0 |
| math/train | 567 | 6.25/7/3/11 | 8475.26 | 2.66 | 0.54 | {None: 567} | 1.0 | 0.0 |
| math/test | 63 | 6.38/7/3/11 | 8565.16 | 2.78 | 0.52 | {None: 63} | 1.0 | 0.0 |
| ALL | 3998 | 12.52/10.0/1/304 | 31409.75 | 1.69 | 0.52 | {'Injection Error': 1822, 'Diagnosis Error': 278, None: 1898} | 1.0 | 0.5253 |

#### Steps histogram (all / test)

| bin | all | test |
|---|---|---|
| [0,5) | 525 | 109 |
| [5,10) | 1383 | 320 |
| [10,15) | 1209 | 215 |
| [15,20) | 282 | 65 |
| [20,30) | 339 | 57 |
| [30,40) | 171 | 16 |
| [40,60) | 57 | 5 |
| [60,100) | 19 | 0 |
| >=100 | 13 | 3 |

#### Relative error position histogram (all)

| bin | count |
|---|---|
| [0,0.1) | 182 |
| [0.1,0.2) | 309 |
| [0.2,0.3) | 449 |
| [0.3,0.4) | 590 |
| [0.4,0.5) | 427 |
| [0.5,0.6) | 495 |
| [0.6,0.7) | 334 |
| [0.7,0.8) | 303 |
| [0.8,0.9) | 335 |
| [0.9,1.0) | 104 |
| >=1.0 | 470 |

#### Faulty agent top per domain

- **agentic**: assistant (2100)
- **coding**: Engineer (935), Product Manager (155), Team Leader (125), Architect (46), Data Analyst (7)
- **math**: Custom (400), reasoning expert (171), BestMAS_GSM8K (55), AnswerGenerate (2), QualityDiversity (1), IterativeGeometrySolver (1)

## Example trajectory

Chosen example: `coding/test/Filter_5086_I` (MetaGPT team, 8 steps, 16.7 k characters; faulty agent **Product Manager** at step 6). Raw record: `notes/tracertraj_example.json`; normalised: `notes/tracertraj_example_norm.json`.


Question: Please solve the programming task below in Python. 

Given a non-empty list of integers, write a Python function that returns a new list containing the elements that appear twice in the original list. The function should handle duplicate entries and empty lists.

Note that the function declaration is def find_duplicates(nums):. 

**[0] Team Leader (role=assistant)**

```
Team Leader thinking: 
# Past Experience
<experience>

# Tool State


# Current Plan
[GOAL] [Message] from User to Mike: Please solve the programming task below in Python. 

Given a non-empty list of integers, write a Python function that returns a new list containing the elements that appear twice in the original list. The function should handle duplicate entries and empty lists.

Note that the function declaration is def find_duplicates(nums):. I wish you finish the task with a multi-agent coo […]
```

**[1] Team Leader (role=assistant)**

```
Team Leader thinking: To address the user's request, I will create a plan that involves multiple team members. The task requires writing a Python function to find duplicates in a list, which can be handled efficiently by the Engineer. However, since the user requested multi-agent cooperation, I will also involve the Product Manager to create a Product Requirement Document (PRD) for clarity and documentation purposes.

Here’s the plan:
1. Alice (Product Manager) will create a PRD based on the use […]
```

**[2] Team Leader (role=assistant)**

```
Team Leader sends to Alice: Create a Product Requirement Document (PRD) for the task: Given a non-empty list of integers, write a Python function that returns a new list containing the elements that appear twice in the original list. The function should handle duplicate entries and empty lists. The function declaration is def find_duplicates(nums):. The solution file name must be 'solution.py'.
```

**[3] Product Manager (role=assistant)**

```
Product Manager thinking: 
# Past Experience
<experience>

# Tool State


# Current Plan
[GOAL] [Message] from Mike to Alice: Create a Product Requirement Document (PRD) for the task: Given a non-empty list of integers, write a Python function that returns a new list containing the elements that appear twice in the original list. The function should handle duplicate entries and empty lists. The function declaration is def find_duplicates(nums):. The solution file name must be 'solution.py'.
No P […]
```

**[4] Product Manager (role=assistant)**

```
Product Manager thinking: To create a Product Requirement Document (PRD) for the task of writing a Python function that identifies duplicate integers in a list, I will first outline the necessary sections of the PRD. This will include the language and project info, product definition, technical specifications, and any open questions. 

I will start by creating a new file named 'solution.py' to hold the function implementation. After that, I will insert the PRD content into the file. 

Here’s the […]
```

**[5] Product Manager (role=assistant)**

```
Product Manager thinking: 
# Past Experience
<experience>

# Tool State


# Current Plan
[GOAL] [Message] from Mike to Alice: Create a Product Requirement Document (PRD) for the task: Given a non-empty list of integers, write a Python function that returns a new list containing the elements that appear twice in the original list. The function should handle duplicate entries and empty lists. The function declaration is def find_duplicates(nums):. The solution file name must be 'solution.py'.
No P […]
```

**[6] Product Manager (role=assistant)  ⟵ ANNOTATED ERROR STEP**

```
Product Manager thinking: I will now insert the PRD content into the 'solution.py' file. The PRD will include the language and project info, product definition, technical specifications, and open questions. This will provide a comprehensive overview of the task requirements.

Here’s the content I will insert:

```markdown
# Product Requirement Document (PRD)

## 1. Language & Project Info
- **Language**: Python
- **Project Name**: find_duplicates_function

## 2. Product Definition
### Product Go […]
```

**[7] Product Manager (role=assistant)**

```
Product Manager thinking: 
# Past Experience
<experience>

# Tool State


# Current Plan
[GOAL] [Message] from Mike to Alice: Create a Product Requirement Document (PRD) for the task: Given a non-empty list of integers, write a Python function that returns a new list containing the elements that appear twice in the original list. The function should handle duplicate entries and empty lists. The function declaration is def find_duplicates(nums):. The solution file name must be 'solution.py'.
No P […]
```

**Annotation**: mistake_agent=`Product Manager`, mistake_step=`6`, error_source=`None`

mistake_reason: The Product Manager created a PRD and inserted it into the solution.py file, but did not implement the actual function 'find_duplicates(nums)'. The task requires a functional implementation, not just documentation.

ground_truth: def find_duplicates(nums):
    """
    Given a list of integers, return a new list containing the elements that appear twice in the original list.
    
    Arguments:
    nums -- list of integers
    
    Returns:
    list of integers
    """
    from collections import Counter
    count = Counter(nums)
    return [num for num, cnt in count.items() if cnt == 2]

## Notes for the report

- **Synthetic/automatic labels, no human review.** Labels come from counterfactual replay (analyzer = DeepSeek-R1) and fault injection; the paper reports no inter-annotator or human-validation numbers for TracerTraj. The release is explicitly "not identical" to the paper's TracerTraj-2.5K.
- **The agentic domain is effectively single-agent for attribution purposes**: all 2,100 agentic rows label every step `assistant` (no `name` field) and `mistake_agent` is always `assistant`, so agent-level accuracy is trivially 100 % there; only the step matters. In coding (MetaGPT) 2.3 named roles per trajectory on average (Engineer is blamed in 935/1,268 rows); in math (AFlow workflows) the "agents" are workflow operators (`Custom`, `reasoning expert`, `QualityDiversity`, …).
- **Short trajectories**: mean 12.5 steps (median 10; agentic median 7, math 3–11, coding up to 304) but long steps (mean 31 k characters per trajectory, ≈8 k tokens; agentic steps embed large web/tool outputs, partly in Chinese).
- **Error position skews late**: 470 of 3,998 rows have the decisive error at the *last* step (relative position 1.0) and 1,212 rows have it in the last 30 %; coding errors sit earlier (mean 0.46).
- **Indexing inconsistencies**: `mistake_step` is a string; agentic steps are 1-based while coding/math are 0-based; the agentic `error_source` field has no counterpart in coding/math (the paper's injected-vs-diagnosed split is not recoverable there).
- **Duplicates / leakage**: 118 math `question_ID`s appear multiple times and 21 appear in both train and test (same task, different injected variant/histories) — avoid per-task leakage when training.
- **Overlap with other datasets**: shares frameworks/benchmarks with MAST (MetaGPT, AutoGen, GAIA, MATH, GSM8K) and with AEGIS (Smolagents, GAIA, MATH, GSM8K) but the trajectories are the authors' own runs; evaluation uses Who&When as the external benchmark. Authors overlap with AEGIS (Guibin Zhang).
- Redaction: e-mails and credential-like strings replaced by placeholders (325 unique e-mails, 48 unique credentials) — expect `<EMAIL>`-style tokens in content.
