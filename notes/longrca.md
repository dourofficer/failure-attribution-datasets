# LongRCA Bench

## Identity

| Field | Value |
|---|---|
| Full title | **LongRCA Bench: Root-Cause Localization in Long-Horizon Agent Trajectories** (earlier arXiv versions were titled "LongRCA Bench: Diagnosing Responsible Roles and Root Causes in Long-Horizon Agent Failures") |
| Authors | Yunfei Zhang\*, Boyu Feng\*, Changhua Pei (corresponding), Zexin Wang, Zhihuang Peng, Xinlong Liu, Hengyue Jiang, Difeng Ma, Jiayi Zhang, Yongzhou Yao, Yanan Zhao, Fei Sun, Yintong Huo, Zhaoyang Liu, Jingjing Li, Gaogang Xie, Dan Pei |
| Affiliations | Computer Network Information Center, CAS; Hangzhou Institute for Advanced Study, UCAS; Chongqing University; Institute of Computing Technology, CAS; Singapore Management University; Tongyi Lab (Alibaba); Tsinghua University |
| Venue | arXiv preprint (no venue stated; 34 pages, 11 figures). v1 15 Aug 2026, v4 (current) 21 Sep 2026 |
| arXiv | 2608.15242 (cs.AI, cs.SE) — https://arxiv.org/abs/2608.15242 |
| Project page / leaderboard | https://longrca-bench.github.io/ |
| Data | Hugging Face `CLoud5-real/longrca-bench` (public, **not gated**), last modified 2026-09-02 |
| Code | No separate code repository found (paper mentions release scripts for Mini sampling/calibration; not in the HF repo) |
| License | Not stated on the HF dataset card (no `license` field); paper under arXiv perpetual non-exclusive license |
| Availability status | **Downloaded in full** (1,140 full + 200 mini JSON files + 2 Parquet files) |
| On-disk size | 351 MB (`longrca-full.parquet` 60.9 MB, `longrca-mini.parquet` 12.3 MB, 1,340 JSON files) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/longrca/` (JSON under `data/full/<source>/` and `data/mini/<source>/`) |

## Description

**Purpose.** Retrospective failure attribution over *complete, long* failed agent executions: given a failed trajectory (`question_ID` + `history`), predict (a) the **responsible workflow role** and (b) the **earliest decisive root-cause step** (0-based). The two targets are predicted and scored independently. The paper's focus is the "long-horizon" regime: reference roots precede trajectory completion by a median of 48 steps and 28.4 % of trajectories have >100 steps after the root.

**Sources and agent frameworks (all natural failures, no injection).** Evaluator-confirmed failed task attempts from five sources (Appendix E of the paper):

| Source | N | Task domain | Agent organisation (workflow) | Trajectory generator LLM |
|---|---|---|---|---|
| SWE-bench Pro | 128 | software repair | custom DiagnostAgent–ActionAgent–JudgeAgent team (diagnosis–execution–verification) | MiniMax-M2.5 (128) |
| Terminal-Bench 2 | 42 | terminal tasks | same custom team | MiniMax-M2.5 (42) |
| TravelPlanner | 685 | travel planning | AutoGen MagenticOneGroupChat with specialist roles (manager, stay, transport, food_attr, verifier agents) | MiniMax-M2.5 (265), Kimi-K2.5 (260), Qwen3.5-Plus (160) |
| VitaBench | 108 | service-oriented tool use (Chinese-language) | Action_Expert–Computer_terminal workflow | M2.5 (69), K2.5 (16), Q3.5+ (23) |
| WebArena Verified | 177 | web interaction | AutoGen Planner–WebSurfer–Critic controller (Task_Planner, Action_Expert, Verification_Expert) | MiniMax-M2.5 (177) |

Infrastructure/smoke-test/debug runs were excluded. Normalisation keeps original content, roles and temporal order with stable 0-based indices; no synthetic intermediate steps and no artificial subdivision of source events (so event granularity differs across sources).

**Annotation protocol.** 22 master's/doctoral CS students. Calibration on 100 trajectories, then full-scale annotation with the same pool. Annotators saw the task, the complete step-indexed history and the source evaluator outcome, and submitted a responsible role, a root step and an evidence-grounded rationale; DeepSeek V4 Flash Preview produced factual *navigation summaries* (no root-cause judgement). 1,343 valid submissions over 1,041 trajectories (747 single, 286 double, 8 triple). Pairwise agreement on the 294 multiply-annotated trajectories (310 pairs): **role agreement 66.1 %, exact-step agreement 40.3 %, step ±5 agreement 50.3 %**; 38.1 % of pairs differ by >20 steps (median gap 5, IQR 0–46). Exact matches were kept as consensus; two experts resolved disagreements; final QC removed 60 of 1,200 reviewed trajectories → **1,140**. Typical annotation time 30–40 min per trajectory.

**Root definition (decision rules, App. G).** The root is the earliest recorded step that introduces a decisive, failure-relevant error that remains unrepaired at completion. If a handoff instruction already contains the error and the recipient executes it faithfully, the *instruction* step is the root; a recipient step qualifies only if it introduces a new deviation. Repaired errors and later steps that merely propagate/expose the error are excluded; missed verifications are explanatory context, not the root.

**Label types.** Agent-level (`mistake_agent`, a recorded role name), step-level (`mistake_step`, 0-based), free-text rationale (`mistake_reason`). **No failure-category taxonomy** and no success trajectories.

**LongRCA-Mini.** Fixed 200-trajectory subset, 40 per source, sampled without replacement with seed 20260821 (n = 200 is the smallest size passing the calibration criteria of max median error ≤ 2 pp and max p95 error ≤ 6 pp over 10,000 draws). Mini is scored Macro-5 (equal source weight). Fidelity: mean |Δ| 1.665 pp, max 3.771 pp over 18 method–metric pairs.

**Metrics.** Agent Acc (explicit role output vs reference), Step Acc (exact 0-based match), Step ±5, Joint Exact / Joint ±5, Step MAE (valid outputs); invalid outputs count as errors. Full benchmark weights trajectories equally (source proportions retained); Mini uses Macro-5.

**Reported baselines (paper Table 2; full benchmark, backbone DeepSeek-V4-Flash, accuracies in %).**

| Method | Agent Acc | Step Acc | Step ±5 | Step Acc SWE | TB2 | TP | Vita | WA |
|---|---|---|---|---|---|---|---|---|
| All-at-once | 26.2 | 7.6 | 19.9 | 1.6 | 7.1 | 4.5 | 19.4 | 16.9 |
| Step-by-step | 22.2 | 5.3 | 16.9 | 0.8 | 4.8 | 3.5 | 12.0 | 11.3 |
| Binary search | 23.0 | 3.4 | 13.3 | 0.8 | 4.8 | 2.0 | 12.0 | 5.1 |
| ECHO | 27.5 | 13.2 | 24.7 | 7.8 | 21.4 | 8.9 | 22.2 | 26.0 |
| FALAT | 19.0 | 2.8 | 12.5 | 2.3 | 2.4 | 2.9 | 3.7 | 2.3 |
| RCTA (paper's method) | **51.1** | **24.1** | **37.4** | 38.3 | 26.2 | 18.8 | 25.0 | 33.3 |

Always predicting each source's most frequent reference role gives 40.3 % Agent Acc (role prior). On LongRCA-Mini (Table 3, Macro-5 Agent/Step Acc): RCTA 60.5/27.0 (V4-Flash), 61.0/28.0 (V4-Pro), 64.5/30.0 (GPT-5.6 Sol), 61.5/31.5 (Kimi K3), 48.5/13.5 (Qwen3.5-35B-A3B); All-at-once 42.5/7.5 … 51.0/3.5; ECHO 45.0/13.0 … 48.5/10.0. For comparison, the same six methods score 30.4–41.8 % Step Acc on Who&When (median length 10 steps) vs 2.8–24.1 % on LongRCA (median 145).

## Schema

File layout on HF / local:

```
longrca-full.parquet                 # 1,140 rows (config "default", split "test")
longrca-mini.parquet                 # 200 rows   (config "mini",    split "test")
data/full/{swe_bench_pro,terminal_bench_2,travelplanner,vitabench,webarena_verified}/<source>__NNN.json   # one trajectory per file
data/mini/<source>/<source>__NNN.json   # identical copies of the 200 Mini trajectories
README.md
```

Each JSON record (identical columns in Parquet):

| Field | Type | Meaning |
|---|---|---|
| `question_ID` | str | source-prefixed trajectory id, e.g. `travelplanner__021` |
| `history` | list[dict] | ordered trajectory records (includes the task instruction, agent messages, tool calls, observations, evaluator feedback) |
| `history[].step` | int | stable 0-based index (verified contiguous 0..T-1 for all 1,140 records) |
| `history[].name` | str | recorded workflow role / agent name; handoff records use names like `DiagnostAgent (-> ActionAgent)` |
| `history[].role` | str | chat role of the record (`assistant` for agent outputs; `user` for terminal/tool/environment records) |
| `history[].content` | str | original text of the record |
| `mistake_agent` | str | reference responsible role (always one of the recorded `name` values; verified) |
| `mistake_step` | int | reference 0-based root-cause step |
| `mistake_reason` | str | human rationale grounded in the trajectory (withheld at prediction time, not scored) |

Methods receive only `question_ID` and `history`; the three `mistake_*` fields are withheld.

## Statistics

All numbers below are **computed from the downloaded data** (script `scripts/analyze_longrca.py`; machine-readable version in `notes/longrca_stats.json`). Verification: Mini ⊂ Full and Mini records are byte-identical to the Full copies; Parquet row counts 1,140 / 200 match the JSON files. Paper-reported values for comparison: mean length 156.3, median 145, total recorded steps 178,137, total history characters 207,731,218, median root-to-end 48, 28.4 % with >100 steps after root, Macro-5 mean normalised root position 0.420.

#### Stats table

| Quantity | Value |
|---|---|
| Trajectories (all failed, natural) | 1140 full / 200 mini |
| Steps per trajectory | mean 156.04, median 145.0, min 10, max 728, p10 53, p90 270 |
| Distinct agents (name) per trajectory | mean 5.42, median 6.0, min 2, max 7, p10 3, p90 7 |
| Root-cause step (0-based) | mean 78.26, median 55.5, min 1, max 521, p10 11, p90 179 |
| Relative root position step/(T-1) | mean 0.53, median 0.516491482421167, min 0.004366812227074236, max 1.0, p10 0.11374407582938388, p90 0.9742489270386266 |
| Root-to-end distance T-1-r* | mean 76.77, median 47.5, min 0, max 605, p10 3, p90 183 |
| Frac. with >50 / >100 / >200 steps after root | 0.486 / 0.2825 / 0.0763 |
| Characters per trajectory | mean 182402.73, median 147555.5, min 1231, max 1224895, p10 37793, p90 325140 |
| Total steps / characters | 177884 / 207939112 |
| Sender of root step == responsible role | 0.9921 |
| Trajectories with explicit handoff markers ('->' in name) | 0.1491 |

#### Per source

| Source | N | N mini | steps mean/median/min/max | chars mean | rel. root pos mean | root-to-end median | agents mean | agent names |
|---|---|---|---|---|---|---|---|---|
| swe_bench_pro | 128 | 40 | 284.98/257.5/80/728 | 451829.27 | 0.25 | 184.0 | 7 | ActionAgent, Computer_terminal, DiagnostAgent, DiagnostAgent (-> ActionAgent), DiagnostAgent (-> JudgeAgent), JudgeAgent, human |
| terminal_bench_2 | 42 | 40 | 272.12/213.5/44/546 | 297244.17 | 0.29 | 152.0 | 7 | ActionAgent, Computer_terminal, DiagnostAgent, DiagnostAgent (-> ActionAgent), DiagnostAgent (-> JudgeAgent), JudgeAgent, human |
| travelplanner | 685 | 40 | 165.94/165/16/524 | 163337.49 | 0.6 | 55 | 5.94 | Computer_terminal, Task_Planner, food_attr_agent, manager_agent, stay_agent, transport_agent, verifier_agent |
| vitabench | 108 | 40 | 54.61/51.0/10/130 | 23186.21 | 0.45 | 24.0 | 2 | Action_Expert, Computer_terminal |
| webarena_verified | 177 | 40 | 58.82/63/13/63 | 131245.3 | 0.56 | 26 | 4 | Action_Expert, Computer_terminal, Task_Planner, Verification_Expert |

#### Steps histogram

| bin | count |
|---|---|
| [0,25) | 13 |
| [25,50) | 88 |
| [50,100) | 288 |
| [100,150) | 204 |
| [150,200) | 261 |
| [200,300) | 198 |
| [300,400) | 46 |
| [400,600) | 35 |
| >=600 | 7 |

#### Relative root position histogram

| bin | count |
|---|---|
| [0,0.1) | 101 |
| [0.1,0.2) | 112 |
| [0.2,0.3) | 143 |
| [0.3,0.4) | 99 |
| [0.4,0.5) | 105 |
| [0.5,0.6) | 113 |
| [0.6,0.7) | 69 |
| [0.7,0.8) | 83 |
| [0.8,0.9) | 67 |
| [0.9,1.0) | 243 |
| >=1.0 | 5 |

#### Faulty agent (responsible role) distribution, overall top 20

| role | count |
|---|---|
| Action_Expert | 189 |
| stay_agent | 175 |
| manager_agent | 163 |
| Task_Planner | 147 |
| DiagnostAgent (-> ActionAgent) | 91 |
| transport_agent | 85 |
| verifier_agent | 68 |
| ActionAgent | 60 |
| food_attr_agent | 57 |
| Computer_terminal | 55 |
| Verification_Expert | 33 |
| DiagnostAgent | 10 |
| JudgeAgent | 7 |

#### Faulty role by source

- **swe_bench_pro**: DiagnostAgent (-> ActionAgent) (75), ActionAgent (42), DiagnostAgent (6), JudgeAgent (4), Computer_terminal (1)
- **terminal_bench_2**: ActionAgent (18), DiagnostAgent (-> ActionAgent) (16), DiagnostAgent (4), JudgeAgent (3), Computer_terminal (1)
- **travelplanner**: stay_agent (175), manager_agent (163), Task_Planner (103), transport_agent (85), verifier_agent (68), food_attr_agent (57), Computer_terminal (34)
- **vitabench**: Action_Expert (89), Computer_terminal (19)
- **webarena_verified**: Action_Expert (100), Task_Planner (44), Verification_Expert (33)

## Example trajectory

Chosen example: `webarena_verified__099` (13 steps, 4 roles, 28.7 k characters) — the shortest English-language trajectory; the overall shortest is `vitabench__089` (10 steps, Chinese-language VitaBench dialogue). Raw record: `notes/longrca_example.json`; normalised: `notes/longrca_example_norm.json`.


**[0] Computer_terminal (role=user)**

```
Get name(s) of reviewer(s) who mention price being unfair for the product on the current page
```

**[1] Computer_terminal (role=user)**

```
Orchestration (progress_packet):
cycle=1
```

**[2] Task_Planner (role=assistant)**

```
Orchestration target: Planner
This run uses an explicit progress packet handoff. Plan only the next browse step.

Task prompt:
You are an autonomous web agent operating in E-commerce Store. Begin from the provided start URLs and work within the current session to complete the task objective.

## Site Context

- Platform: E-commerce Store
- Description: An online shopping platform where customers can browse products, add items to cart, and make purchases.
- Authentication: You are already logged  […]
```

**[3] Task_Planner (role=assistant)**

```
Let me analyze the task:

1. **Task Objective**: Get name(s) of reviewer(s) who mention price being unfair for the product on the current page
2. **Start URL**: http://localhost:7770/haflinger-men-s-wool-felt-open-back-slippers-beige-550-peat-us-7.html
3. **Task Type**: RETRIEVE (we're getting data about reviewers)

The task is asking me to find reviewers who mentioned that the price is unfair for this product. This requires:
1. First, navigate to the product page
2. Find the reviews section
3.  […]
```

**[4] Task_Planner (role=assistant)**

```
{"status": "act", "reason": "Starting task to find reviewer names who mention price being unfair. Need to load the product page first.", "current_subgoal": "Load product page and find reviews section", "instruction_for_web_surfer": "Navigate to http://localhost:7770/haflinger-men-s-wool-felt-open-back-slippers-beige-550-peat-us-7.html. Once loaded, look for the product reviews section. Identify if there is a Reviews tab, link, or section on the page. Report back the location of the reviews secti […]
```

**[5] Task_Planner (role=assistant)**

```
Orchestration target: WebSurfer
This is an explicit progress packet handoff from Planner to WebSurfer.
Do not ask for the task again. Use the packet below and take the minimum number of browser actions needed.

Task prompt:
You are an autonomous web agent operating in E-commerce Store. Begin from the provided start URLs and work within the current session to complete the task objective.

## Site Context

- Platform: E-commerce Store
- Description: An online shopping platform where customers can  […]
```

**[6] Action_Expert (role=assistant)**

```
I clicked '2  Reviews'.

The web browser is open to the page [HAFLINGER Men's Wool Felt Open Back Slippers, Beige 550 Peat, US:7](http://localhost:7770/haflinger-men-s-wool-felt-open-back-slippers-beige-550-peat-us-7.html).
The viewport shows 34% of the webpage, and is positioned 48% down from the top of the page
The following text is visible in the viewport:

Skip to the beginning of the images gallery  Details 
 Reviews 
2Customer Reviews Wonderful! 
Rating 100% 
 Nothing.....everyday use. 
 R […]
```

**[7] Task_Planner (role=assistant)**

```
Orchestration target: Critic
This run uses an explicit progress packet handoff. Decide whether the task is complete, needs one more step, or should fail fast.

Task prompt:
You are an autonomous web agent operating in E-commerce Store. Begin from the provided start URLs and work within the current session to complete the task objective.

## Site Context

- Platform: E-commerce Store
- Description: An online shopping platform where customers can browse products, add items to cart, and make purcha […]
```

**[8] Verification_Expert (role=assistant)**

```
Let me analyze the current state of the task:

1. **Task Objective**: Get name(s) of reviewer(s) who mention price being unfair for the product on the current page

2. **Current Progress**: 
   - The product page is loaded
   - Reviews section is visible (2 customer reviews)
   - The reviews visible are:
     - Review 1: "Wonderful!" by Jay - "Nothing.....everyday use."
     - Review 2: "Joe" by Josef Bürger - "Die Haflinger sind wie beschrieben und erwartet sehr gut"

3. **Analysis**: 
   - Loo […]
```

**[9] Verification_Expert (role=assistant)  ⟵ ANNOTATED ERROR STEP**

```
{"status":"complete","reason":"The task asks for reviewer(s) who mention price being unfair. The page shows exactly 2 reviews (visible in both viewport and metadata). Review 1 is by Jay with text 'Nothing.....everyday use.' and Review 2 is by Josef Bürger with text 'Die Haflinger sind wie beschrieben und erwartet sehr gut' (German for 'The Haflingers are as described and expected very good'). Neither review mentions price or indicates the price is unfair. The metadata confirms only these 2 revie […]
```

**[10] Task_Planner (role=assistant)**

```
Orchestration (coordinator_decision):
cycle=1
```

**[11] Verification_Expert (role=assistant)**

```
Final answer:
{"task_type": "RETRIEVE", "status": "SUCCESS", "retrieved_data": [], "error_details": null}
```

**[12] Computer_terminal (role=user)**

```
Run finished: The task asks for reviewer(s) who mention price being unfair. The page shows exactly 2 reviews (visible in both viewport and metadata). Review 1 is by Jay with text 'Nothing.....everyday use.' and Review 2 is by Josef Bürger with text 'Die Haflinger sind wie beschrieben und erwartet sehr gut' (German for 'The Haflingers are as described and expected very good'). Neither review mentions price or indicates the price is unfair. The metadata confirms only these 2 reviews exist for this […]
```

**Annotation**: mistake_agent = `Verification_Expert`, mistake_step = `9`

mistake_reason: Verification_Expert already correctly determined at #9 that the page has only 2 comments, and neither Jay nor Josef Bürger mentioned "price unfair". However, it outputs the following in its final_response:

status: "SUCCESS"
retrieved_data: []
error_details: null

This violates the WebArena RETRIEVE task specification. For retrieval tasks such as "find the reviewer name", if no matching entity exists on the page, the correct return should be NOT_FOUND_ERROR, rather than SUCCESS with an empty list. Therefore, the error is not the failure to find the reviewer, but the incorrect labeling of the "not found" scenario as successful completion.

## Notes for the report

- **Natural failures only, long horizons.** No error injection; all 1,140 trajectories are evaluator-confirmed failures. Median 145 steps, mean 156, max 728; mean 182 k characters (≈45 k tokens) per trajectory — an order of magnitude longer than Who&When (median 10 steps). Our recomputed statistics match the paper to within rounding (e.g. 28.25 % vs 28.4 % with >100 steps after the root; total steps 177,884 vs 178,137 reported).
- **Source imbalance.** TravelPlanner is 60.1 % of the full set (685/1,140); SWE-bench Pro and Terminal-Bench 2 trajectories are 4–5× longer (median 257.5 / 213.5 steps, up to 450 k characters) than VitaBench/WebArena (median 51 / 63). Mini equalises sources (40 each) and is scored Macro-5; the paper insists headline numbers use the full set.
- **Root position is bimodal.** 243/1,140 roots lie in the last 10 % of the trajectory (many TravelPlanner/WebArena cases where a verifier or planner commits the decisive error late), while SWE/TB2 roots sit early (mean relative position 0.25–0.29) followed by hundreds of steps. Five trajectories have the root at the very last step.
- **Role naming quirks.** Handoff records carry composite names such as `DiagnostAgent (-> ActionAgent)`; these appear as reference roles (91 cases), so role matching must follow the paper's normalisation (Appendix L.1). `Computer_terminal` (an environment/relay record) is the responsible role in 55 cases — the paper notes the outer sender of a log event does not mechanically determine responsibility (e.g. `swe_bench_pro__047`, step 133 relays ActionAgent's completion report). In 99.2 % of records the sender of the root step equals the responsible role.
- **Agent count is small (2–7 roles).** Agent-level accuracy is therefore partly a prior problem (40.3 % with the per-source majority role); VitaBench has only two roles.
- **No category labels**, only free-text rationales; no successful trajectories; evaluator feedback (e.g. "Run finished: …") is already inside `history`.
- **Language.** VitaBench trajectories are in Chinese; the rest are English (with some Chinese fragments in TravelPlanner/WebArena tool output).
- **Inter-annotator agreement is low in absolute terms** (exact step 40.3 %, ±5 50.3 %), i.e. the ceiling for exact-step accuracy is itself limited; the paper reports label-sensitivity analyses (RCTA remains rank-1 in 100 % of 10,000 label draws).
- **Relation to other datasets.** Trajectories were freshly generated by the authors (2026 models: MiniMax-M2.5, Kimi-K2.5, Qwen3.5-Plus); no overlap with Who&When/MAST logs. The paper benchmarks the same methods on Who&When for cross-dataset comparison and cites AgentRx (first-unrecoverable-failure definition) and TraceElephant.
- **License is unspecified** on the HF card; check with the authors before redistribution.
