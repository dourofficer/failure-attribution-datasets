# HORIZON

## Identity

| Field | Value |
|---|---|
| Full title | **The Long-Horizon Task Mirage? Diagnosing Where and Why Agentic Systems Break** (benchmark: HORIZON) |
| Authors | Xinyu Jessica Wang, Haoyue Bai, Yiyou Sun, Haorui Wang, Shuibai Zhang, Wenjie Hu, Mya Schroder, Bilge Mutlu, Dawn Song, Robert D. Nowak — UW–Madison and UC Berkeley (inferred from author list; affiliations not on the abstract page) |
| Venue | arXiv preprint (v1 13 Apr 2026); the ethics statement mentions "COLM 2026 policy", so it was submitted to COLM 2026 |
| arXiv id | 2604.11978 |
| Paper | https://arxiv.org/abs/2604.11978 (HTML: https://arxiv.org/html/2604.11978) |
| Project / leaderboard | https://xwang2775.github.io/horizon-leaderboard/ (source: https://github.com/xwang2775/horizon-leaderboard — HTML + one CSV only, no code) |
| Data | (a) **https://huggingface.co/datasets/xwang2775/long-horizon-agent-failures** — raw runs + LLM-judge failure attributions, 19.5 GB, **not gated**, no dataset card, no license; (b) https://huggingface.co/datasets/xwang2775/horizon-tasks — the task definitions / plans (786 rows, parquet), **gated (manual approval; our access request was denied/pending: "Access denied. This repository requires approval")** |
| License | none stated on either HF repo or in the paper |
| Availability | **Released (a) / gated (b). Representative subset of (a) downloaded** (see below); (b) not obtained. |
| On-disk size | **187 MB** downloaded of 19.5 GB: all four judge-output bundles `result_{1,2,3,5}/` (≈140 MB), all `database/` and `embodied/` raw files, all `os/` run files (40 MB), and the web metadata (`config.json`, `failure_analysis.json`, `steps_*.txt`, logs; 4.8 MB). **Skipped:** the web Playwright traces (`web/*/*/traces/*.zip`, ≈ 10–15 GB) and the per-step HTML page renders (`render_*.html`, several GB), which are not needed for attribution analysis. |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/horizon/hf/` |

## Description

**Purpose.** HORIZON is a *diagnostic* benchmark for long-horizon agent tasks: it constructs tasks of controllable horizon (compositional depth *s*) in four domains, runs agents on them, and attributes every failure to one of seven failure modes with a trajectory-grounded LLM-as-a-Judge. The attribution labels are therefore **judge-generated at scale (3,782 trajectories in the release; "3,100+" in the paper) and human-validated only on a 40-trajectory pilot** (inter-annotator κ = 0.61, human–judge κ = 0.84). It is a *failure taxonomy* dataset in the MAST family, with step-level localisation available only for one subset (web/GPT-5-mini).

**How it was built.**
- *Domains and base benchmarks (4):* Web navigation (WebArena; shopping-admin / Postmill / GitLab sites), Operating System (AgentBench OS, bash in Ubuntu), Database (MAC-SQL on BIRD-style text-to-SQL), Embodied manipulation (bimanual IsaacSim 5.0, primitive-action plans).
- *Horizon construction:* tasks are nested by level *s*. **Depth extension** (OS, Database — fixed initial state) inserts intermediate required steps (≈1–2 permission checks per OS level, ≈2–3 filtering operations per DB level; OS levels s = 1…10, DB s = 1…8). **Breadth extension** (Web, Embodied — variable initial state) composes *k* independent base tasks into one workflow joined by "AND" (web s = 1…5 with .1/.2 sub-variants, embodied s = 1…5 actions). "700+ tasks" in total.
- *Agents:* single-agent prompt-based agents (WebArena CoT agent with accessibility-tree observations, AgentBench OS ReAct agent, MAC-SQL, a primitive-plan planner) backed by **GPT-5-mini** and **Claude-4-Sonnet** (the appendix figure captions also mention GPT-4o-mini / Claude-3.5-Sonnet — an inconsistency in the paper); three independent runs per OS task set.
- *Failures are natural* (no injection). The environment's own verifier gives pass/fail (`passed` / `score`); the judge additionally decides "Success" vs a failure mode from the trajectory text, so the two disagree on ~12 % of runs (see statistics).
- *Judge pipeline:* an LLM judge reads the serialised trajectory (task, expected answer, per-step page/thought/action for web; `[Agent]`/`[OS response]` blocks for OS; the predicted vs gold SQL plus execution result for DB; the primitive plan for embodied) and outputs `failure_type` + one-sentence `reason` (+ `failure_step_number` and a 5-step window summary in the web subset). Judge model is not named in the released files; the paper says GPT-class judge. Two full judge passes are released (`result_2`, `result_3`, identical inputs) — they agree on Success-vs-Failure 94.3 % of the time and on the exact failure category 73.3 % of the time given both say "failure".
- *Human validation:* two expert annotators labelled a shared set of 40 failure trajectories (κ = 0.61); one annotator vs the judge on 40 traces (κ = 0.84). No human labels are included in the release.

**Label types.** Trajectory-level: `failure_type` (7 categories or `Success`), `reason` (one sentence, ~200 chars). Step-level: `failure_step_number` only in `result_5` (web / GPT-5-mini, 371 runs; 294 failed runs carry a step index). No agent-level label (all agents are single-agent). Environment outcome (`passed` bool for OS/DB/embodied, `score` ∈ {0,1} for web) is also present.

**Error taxonomy (7 modes; Table 1 / Appendix B; [L] = predominantly long-horizon, [S] = present at all horizons but amplified):**

| Failure mode | Definition (paraphrased) | Level |
|---|---|---|
| Environment (Disturbance / Unable to Detect Environment Change) | acts on stale state: does not notice a page change, failed command, schema change; two sub-types | S |
| Instruction (Ill-defined / Partially Understood) | misreads or fills gaps in an ambiguous/unsatisfiable instruction; two sub-types | S |
| False Assumption | acts on unverified beliefs (ownership, column existence, placeholder data) | S |
| Planning Error (sub-plan & action) | wrong sub-goal order, wrong action plan or action sequence | S |
| Catastrophic Forgetting | a constraint still in context no longer governs later actions | L |
| History Error Accumulation | early mistakes are carried forward and compounded | L |
| Memory Limitation | needed information lost to truncation / summarisation / incomplete retrieval | L |

The paper additionally groups these into process-level (PFMEA, 72.5 % of failures) vs design-level (DFMEA, 27.5 %).

**Task formulation and metrics (paper).** Primary: success rate vs extension level *s*, per domain and model, with a "break level" (first level where success collapses). Secondary: distribution of failure modes per domain/model as produced by the judge; κ-based validation of the judge. The dataset was *not* used to benchmark attribution models — there is no attribution leaderboard; the judge itself is the attribution method.

**Reported findings (paper; no numeric success table in the text).** Web collapses at very small *s*; OS and DB degrade gradually until later levels; Embodied degrades steeply with any increase in *s*. Failure-mode mix (paper, from 3,100+ trajectories): Embodied — Planning 94.9 %; Database — Planning 79.3 %; Web — Planning 74.9 %, Environment 11.3 %, Memory Limitation 6.2 %; OS — Planning 36.7 %, Instruction 25.9 %, Environment 17.3 %, Memory Limitation 15.1 %. By model: GPT failures 64.9 % Planning / 18.3 % Memory Limitation; Claude failures 32.5 % Environment / 16.5 % Instruction. (The released `result_2/failure_stats.json` gives a somewhat different mix — see Statistics — e.g. 0 % Memory Limitation and 29.6 % Catastrophic Forgetting overall, so the paper's figures come from a different judge pass than the released one.)

## Schema

Layout of `xwang2775/long-horizon-agent-failures` (HF, 19.5 GB; `*` = downloaded):

| Path | Content |
|---|---|
| `result_2/classified_results.json` * | **main judge output**: list of 3,782 records, one per trajectory, fields below |
| `result_3/classified_results.json` * | second judge pass over the same 3,782 ids (same fields) |
| `result_1/classified_results.json` * | earlier pass over a 1,499-trajectory subset (os 920, embodied 270, database 180, web 129); extra field `existing_category` (older code such as `A.5`) |
| `result_5/classified_results.json` * | web / GPT-5-mini only, 371 records, **adds `failure_step_number` (int or null) and `steps` (judge's summaries of the last ≤5 steps, each with `label`, `summary`, `raw`)** |
| `result_*/judge_cache.json` * | same records keyed by id (cache of the judge) |
| `result_*/failure_stats.json` * | aggregated failure-mode proportions overall / by model / by domain / by domain×model |
| `database/analyzed_results_final_{gpt,claude}.json` * | 90 BIRD-style questions each: `question_id, db_id, question, evidence, difficulty, pred, gold, res (0/1), failure_category, failure_reason` |
| `embodied/{gpt-5-mini,claude-4-sonnet}/<ULID>.json` * | 135 each: `id, revision_of, task_prompt, primitive_plan[{name, parameters, core_primitives}]` |
| `os/run_{0,1,2}/{gpt-5-mini,claude-sonnet-4}/os-std-aug-clear-filtered-<level>/runs.jsonl` * | 46 AgentBench-style run records per level (`index, error, info, output{status, result{result: bool}, history[{role: user|agent, content}]}`), plus `overall.json` / `error.jsonl`; `os/gpt5mini-runs_pass.jsonl`; accuracy tables (`accuracy_*.md`, in Chinese) |
| `web/{chatgpt-5-mini,claude-sonnet-4}/5_mini_step_<s>[.k]/` | per-level WebArena run dirs: `config.json` *, `steps_<task>.txt` * (step log), `failure_analysis.json` * (an earlier per-task judge output with `failure_category`, `failure_subcategory`, `confidence`, `justification`), `render_<task>.html` (page renders, not downloaded), `traces/<task>.zip` (Playwright traces, not downloaded) |

Fields of a `classified_results.json` record:

| Field | Meaning |
|---|---|
| `id` | unique id, e.g. `web_gpt_5_mini_step_4_6`, `os_gpt_run_0_aug-cf3-007-bootstrap-00021`, `db_gpt_39`, `embodied_claude_<ULID>` |
| `domain` | `web` / `os` / `database` / `embodied` |
| `model` | `gpt` (GPT-5-mini) or `claude` (Claude-4-Sonnet) |
| `run` | run / level id (`run_0..2` for OS, `5_mini_step_<s>[.k]` for web; absent for DB/embodied) |
| `task_id` | task index within the run (web/result_5 only) |
| `passed` / `score` | environment verdict (OS/DB/embodied bool; web 0.0/1.0); one of the two is present for 3,512 records |
| `trajectory` | serialised trajectory text; format is domain-specific: web `Task/Expected answer` header + `[Step n]` blocks (`Page :`, `Agent:`, `Action:`); OS `[Task]` + alternating `[Agent]` / `[OS response]`; DB a single block (`Question/Evidence/Agent SQL/Gold SQL/Correct/Notes`); embodied `Task` + `Primitive plan (k steps)` list |
| `failure_type` | judge label: `Success` or one of the 7 modes |
| `reason` | judge's one-sentence explanation |
| `failure_step_number` | (result_5 only) 1-based index of the `[Step n]` the judge blames |
| `steps` | (result_5 only) judge window: list of `{label, summary, raw}` for the last ≤5 steps |
| `existing_category` | (result_1 / 180 web records) earlier category code (`A.2`, `A.4`, `A.5`, `A.5.1`, `Success`) |

## Statistics

Computed from `result_2/classified_results.json` (main judge pass) and `result_5` (step-level subset) with `scripts/analyze_horizon.py`; machine-readable `notes/horizon_stats.json`. Paper-only numbers are marked.

| Statistic | Value |
|---|---|
| Trajectories (release) | **3,782** = os 2,735 (gpt 1,366 / claude 1,369) · web 597 (gpt 149 / claude 448) · embodied 270 (135/135) · database 180 (90/90); by model: claude 2,042, gpt 1,740. *(paper: 3,132 = web 767, os 2,146, db 84, embodied 135; 1,995 failures / 1,137 successes)* |
| Runs / levels | OS `run_0/1/2` (918/914/903 records; 10 levels × 46 tasks × 2 models each); web `5_mini_step_1..5` and `.1/.2` sub-levels (21–66 records each) |
| Judge Success vs Failure | **1,284 Success / 2,498 Failure** (66 % failure); by domain: os 924/1,811, web 170/427, embodied 123/147, database 67/113; by model: gpt 579/1,161, claude 705/1,337 |
| Environment verdict vs judge | env pass & judge Success 909 · env pass & judge failure 200 · env fail & judge failure 2,151 · env fail & judge Success 252 · no env verdict 270 (embodied) → 12.9 % disagreement where both exist |
| Failure-mode distribution (2,498 failures) | Planning Error 1,125 (45.0 %) · Catastrophic Forgetting 739 (29.6 %) · Instruction 523 (20.9 %) · Environment 61 (2.4 %) · False Assumption 49 (2.0 %) · History Error Accumulation 1 · Memory Limitation 0 |
| By domain | os: CF 717, Planning 545, Instruction 503, Env 34, FA 11, HEA 1 · web: Planning 351, Env 27, FA 25, CF 22, Instr 2 · embodied: Planning 139, Instr 5, FA 3 · database: Planning 90, Instr 13, FA 10 |
| By model | gpt: CF 644, Planning 436, Instr 39, Env 26, FA 15 · claude: Planning 689, Instr 484, CF 95, Env 35, FA 34 |
| result_5 (web/gpt, step-level) | 371 runs, 299 judged failed, 294 with `failure_step_number`; modes: Planning 252, Environment 17, History Error Accumulation 10, Instruction 8, False Assumption 7, **Memory Limitation 5**; 12 runs have env score 1.0 but a judge failure label |
| Steps per trajectory (all, parsed from text) | mean 13.7, median 11, p25 8, p75 14, p90 22, max 151 (database counted as 1 step) |
| Steps by domain | os mean 12.7 / median 11 / max 50 (agent turns) · web mean 23.5 / median 10 / p90 69 / max 151 · embodied mean 9.8 / median 9 / max 34 (primitive actions) · database 1 |
| Steps histogram (all) | 1–2: 207 · 3–5: 373 · 6–10: 1,259 · 11–15: 1,131 · 16–20: 354 · 21–30: 253 · 31–50: 116 · ≥51: 86 (3 embodied with empty plan) |
| Labelled error step (result_5, 294 runs) | absolute: mean 9.5, median 6, p90 21, max 61; **relative position mean 0.44, median 0.42**, p25 0.16, p75 0.67; decile histogram 0.0–0.1: 49 · 35 · 26 · 24 · 24 · 36 · 33 · 25 · 27 · 0.9–1.0: 7 · =1.0: 8 |
| Characters per trajectory | mean 6,741, median 5,399, p90 10,470, max 102,763 (web p90 39 k; os median 5.6 k; embodied median 0.6 k; db median 1.2 k) |
| Reason length | mean 206 chars |
| Judge consistency (result_2 vs result_3) | exact label 77.5 %; Success/Failure 94.3 %; category given both failed 73.3 % (n = 2,392); biggest confusions: CF↔Planning (204 + 98), Instruction↔Planning (109 + 104) |
| Human validation *(paper)* | 40 trajectories: κ(human,human) = 0.61, κ(human,judge) = 0.84 |

Source benchmark counts: WebArena 597, AgentBench-OS 2,735, MAC-SQL/BIRD 180, IsaacSim embodied 270.

## Example trajectory

Chosen record: `web_gpt_5_mini_step_4_6` from `result_5` (WebArena shopping-admin, GPT-5-mini, breadth level s = 4: four tasks joined by AND; 14 steps; env score 0.0; judge label **Memory Limitation** with `failure_step_number = 9`). Raw record (incl. the judge's 5-step window summaries): `notes/horizon_example.json`; normalised: `notes/horizon_example_norm.json`. Note that the label and reason come from the LLM judge, not from a human.

**Source id:** `web_gpt_5_mini_step_4_6`  
**Task:** Cancel order 299 AND What is the top-1 best-selling product in 2022 AND Show all customers AND Get the billing name of the oldest complete order  
**Ground truth:** Canceled  
**Final output of the system:** Early stop: Same typing action for 3 times  

Steps (14 total):

- **Step 1 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Dashboard / Magento Admin
  > Thought: Let's think step-by-step. I will open the order row for order 299 to cancel it.
  > 
  > In summary, the next action I will perform is ```click [975]```
  > Action: click [975] where [975] is [975] row 'http://localhost:7780/admin/sales/order/view/order_id/299/'

- **Step 2 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): #000000299 / Orders / Operations / Sales / Magento Admin
  > Thought: Let's think step-by-step.
  > 
  > The order view shows Order Status = "Canceled", so order 299 is already canceled. Next I need the top-1 best-selling product in 2022, show all customers, and get the billing name of the oldest "Complete" order. I'll navigate to the Reports section to find sales/bestsellers.
  > 
  > I […] will perform is ```click [1322]```
  > Action: click [1322] where [1322] is [1322] link '\ue60a REPORTS'

- **Step 3 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): #000000299 / Orders / Operations / Sales / Magento Admin
  > Thought: Let's think step-by-step. The order view shows Order 299's status is already "Canceled", so no further action is needed to cancel it. Next, I'll open the Bestsellers report to find the top-selling product for 2022.
  > 
  > In summary, the next action I will perform is ```click [2280]```
  > Action: click [2280] where [2280] is [2280] link 'Bestsellers'

- **Step 4 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Bestsellers Report / Products / Reports / Magento Admin
  > Thought: I will set the report's date range to 2022. In summary, the next action I will perform is ```type [4573] [01/01/2022] [0]```
  > Action: type [4573] [01/01/2022] where [4573] is [4573] textbox 'From *' required: True

- **Step 5 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Bestsellers Report / Products / Reports / Magento Admin
  > Thought: Let's think step-by-step. I will enter the end date for the report so I can run the 2022 bestsellers report.
  > 
  > In summary, the next action I will perform is ```type [4576] [12/31/2022] [1]```
  > Action: type [4576] [12/31/2022 ] where [4576] is [4576] textbox 'To *' required: True

- **Step 6 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Bestsellers Report / Products / Reports / Magento Admin
  > Thought: Let's think step-by-step. First I will generate the bestsellers report for 2022 to find the top-1 product. 
  > 
  > In summary, the next action I will perform is ```click [4782]```
  > Action: click [4782] where [4782] is [4782] button 'Show Report'

- **Step 7 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Bestsellers Report / Products / Reports / Magento Admin
  > Thought: Let's think step-by-step. The best-sellers report results need to be displayed to identify the top product for 2022. I'll (re)run the report by clicking the "Show Report" button.
  > 
  > In summary, the next action I will perform is ```click [6091]```
  > Action: click [6091] where [6091] is [6091] button 'Show Report'

- **Step 8 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Bestsellers Report / Products / Reports / Magento Admin
  > Thought: In summary, the next action I will perform is ```click [9442]```
  > Action: click [9442] where [9442] is [9442] link '\ue60b SALES'

- **Step 9 — web agent (gpt-5-mini)**  ⟵ ANNOTATED ERROR STEP

  > Observation: Tab 0 (current): Bestsellers Report / Products / Reports / Magento Admin
  > Thought: Let's think step-by-step. To cancel order #299 I need to open the Orders list under Sales. The Orders link is available in the Sales menu.
  > 
  > In summary, the next action I will perform is ```click [9650]```
  > Action: click [9650] where [9650] is [9650] link 'Orders'

- **Step 10 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Orders / Operations / Sales / Magento Admin
  > Thought: Let's think step-by-step. To cancel order #299 I should locate it in the Orders list — the page has a "Search by keyword" box. I'll search for "299" to load that order.
  > 
  > In summary, the next action I will perform is ```type [12939] [299] [1]```
  > Action: type [12939] [299 ] where [12939] is [12939] textbox 'Search by keyword' required: False

- **Step 11 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Orders / Operations / Sales / Magento Admin
  > Thought: Let's think step-by-step. I will first run the search for the order so I can cancel it.
  > 
  > In summary, the next action I will perform is ```click [12940]```
  > Action: click [12940] where [12940] is [12940] button 'Search'

- **Step 12 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Orders / Operations / Sales / Magento Admin
  > Thought: In summary, the next action I will perform is ```type [12939] [299] [1]```
  > Action: type [12939] [299 ] where [12939] is [12939] textbox 'Search by keyword' required: False

- **Step 13 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Orders / Operations / Sales / Magento Admin
  > Thought: Let's think step-by-step. I will replace the current search keyword with the order ID "299" and submit the search to locate the order. 
  > 
  > In summary, the next action I will perform is ```type [12939] [299] [1]```
  > Action: type [12939] [299 ] where [12939] is [12939] textbox 'Search by keyword' focused: True required: False

- **Step 14 — web agent (gpt-5-mini)**

  > Observation: Tab 0 (current): Orders / Operations / Sales / Magento Admin
  > Thought: 
  > Action: stop [Early stop: Same typing action for 3 times]

**Annotation:**

- Faulty agent/component: `web agent (single-agent)`
- Faulty step: `9`
- Category: `Memory Limitation`
- Reason / root cause: After noting in Step 2 that order 299 was already canceled, the agent later forgot this and attempted to cancel it again (Step 9), repeating search actions instead of proceeding with the remaining tasks.
- domain: web
- model: gpt
- run: 5_mini_step_4
- task_id: 6
- score: 0.0
- judge: LLM-as-a-Judge (trajectory-grounded), not human
- judge_step_window_summaries: [{'label': 'establishment step', 'summary': 'Agent observes order 299 is already canceled and plans to work on other tasks.', 'raw': '[Step 2]\nPage : Tab 0 (current): #000000299 / Orders / Operations / Sales / Magento Admin\nAgent: Let\'s  […] n: click [12940] where [12940] is [12940] button 'Search'"}]

## Notes for the report

- **What is unique.** The only dataset here with *controllable horizon*: the same base task appears at increasing compositional depth/breadth, so failure modes can be plotted against horizon length; four heterogeneous domains including embodied manipulation and text-to-SQL; two full judge passes released, which lets one quantify judge self-consistency (77.5 % exact agreement).
- **Labels are LLM-generated.** Treat HORIZON as a judge-labelled taxonomy dataset (like MAST-Data), not a human-annotated attribution benchmark. Only 40 trajectories were human-checked and those labels are not released. Step-level labels exist only for 294 web/GPT runs (`result_5`) and are judge outputs.
- **Granularity varies by domain.** Database "trajectories" are a single predicted SQL vs gold SQL (one step), embodied ones are a plan of primitives without observations, OS ones are ReAct transcripts, web ones are accessibility-tree agent logs. Step-level attribution is therefore only meaningful for web and OS.
- **Inconsistencies to flag.** Release counts (3,782) ≠ paper counts (3,132); released failure mix has 0 Memory Limitation and 29.6 % Catastrophic Forgetting while the paper reports 15 % Memory Limitation on OS; judge Success label disagrees with the environment verdict on ~13 % of runs (200 env-passes labelled as failures, 252 env-fails labelled Success); model names in appendix figures (GPT-4o-mini, Claude-3.5-Sonnet) differ from the main text (GPT-5-mini, Claude-4-Sonnet); no license on the HF repo or in the paper; HF dataset has no card and its viewer fails (UnicodeDecodeError).
- **Size caveat.** 19.5 GB on HF but >95 % of it is Playwright trace zips and HTML renders of web pages; the attribution-relevant JSON is ~140 MB (downloaded). The gated `horizon-tasks` repo holds the task/plan definitions (786 rows: web 145, OS 506, DB 90, embodied 45) with `history_gpt` / `history_claude` JSON strings; we could not obtain it.
- **Overlaps.** Base tasks come from WebArena, AgentBench-OS, BIRD/MAC-SQL — shared with TRAIL (GAIA/SWE-bench: none), AgentDebug/AgentErrorBench (WebShop/ALFWorld: none), and Who&When (GAIA: none); so essentially no task overlap with the MAS attribution datasets, but conceptual overlap with MAST's failure-taxonomy approach.
