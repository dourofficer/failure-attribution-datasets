# MP-Bench — dataset notes

## Identity

| Field | Value |
|---|---|
| Full title | *Rethinking Failure Attribution in Multi-Agent Systems: A Multi-Perspective Benchmark and Evaluation* |
| Authors / affiliation | Yeonjun In (KAIST; work done at Adobe Research), Mehrab Tanjim, Jayakumar Subramanian, Sungchul Kim, Uttaran Bhattacharya, Somdeb Sarkhel (Adobe Research), Wonjoong Kim, Sangwu Park, Chanyoung Park (KAIST) |
| Venue | ICML 2026 (arXiv comment "Under review") |
| arXiv | [2603.25001](https://arxiv.org/abs/2603.25001) (26 Mar 2026); paper CC BY 4.0 |
| Paper HTML | https://arxiv.org/html/2603.25001 |
| Code | https://github.com/yeonjun-in/MP-Bench (evaluation pipeline, leaderboard, `build_annotated_from_log_source.py`) — leaderboard page https://yeonjun-in.github.io/MP-Bench/ |
| Data | https://github.com/adobe-research/multi-agent-eval-bench (`MP-Bench/<annotator 1,2,3>/<manual|automatic>/<n>.json`); HF mirror `Yeonjun/MP-Bench` contains only README + LICENSE (no data). |
| License | **Adobe Research License v1.2** — non-commercial research/teaching only, derivatives must stay non-commercial. The annotations point to third-party logs (Who&When: no explicit license; MAST traces: MIT-licensed repo). |
| Availability | Ungated; **downloaded in full**. The release ships *only annotation pointers*: each file has a `log_source` URL into the Who&When GitHub repo or the MAST repo plus step-level annotations. All 289 distinct source logs were fetched from GitHub with our own script (no repo code executed) so the full trajectories are available locally. |
| On-disk size | 6.0 MB (annotation repo) + 0.5 MB (eval repo) + fetched source logs (see Statistics) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/mp_bench/adobe_multi-agent-eval-bench/MP-Bench/` (raw annotations), `data/mp_bench/yeonjun_MP-Bench/` (eval code, leaderboard.json), `data/mp_bench/sources/<sha1(url)[:16]>/` (fetched logs + `index.json` mapping) |

## Description

**Purpose.** Argues that MAS failure attribution is *non-deterministic*: a failed trace often admits several plausible root causes, so a benchmark should store a *set* of annotator perspectives rather than one gold (agent, step). MP-Bench re-annotates existing failure logs with three independent expert annotators and evaluates attribution as a *ranking* against the annotators' consensus.

**Construction.**
- 289 execution logs from 121 MAS configurations: 169 *manual* (hand-crafted MAS) and 120 *automatic* (algorithm-generated MAS). Sources (from the `log_source` URLs): 120 Who&When Algorithm-Generated (CaptainAgent on GAIA/AssistantBench), 57 Who&When Hand-Crafted (Magentic-One), and 112 **MAST** Magentic-One GAIA-validation console logs (86 level-2, 26 level-3; from the MAST failure-taxonomy repo `multi-agent-systems-failure-taxonomy/MAST`). All are *natural* failures. (The paper itself says the logs were "collected by running MAS" and only cites Who&When as design precedent; the README states the MAST + Who&When provenance.)
- **Annotators.** Three experts recruited on Upwork after a two-stage screening (technical interview, then test annotations reviewed for correctness/consistency). Each annotator labelled *every* log independently with no guiding perspective: for each step a binary failure-inducing flag, a free-text `fail_reason`, a free-text `ideal_action`, and (in the released files) a `fail_category`. ~31 min per manual log, ~14 min per automatic log, ≈ 346 expert-hours total.
- **Agreement.** Of the steps flagged by anyone, 16.2 % were flagged by all three, 27.8 % by two, 56.1 % by one only; pairwise disagreement up to ~60 % — the empirical motivation for the multi-perspective formulation. Steps get a *consensus rate* (fraction of annotators flagging them); GPT-5.1 summarises the annotators' reasons/ideal actions per step.
- **Categories** present in the files: Planning Error, Verification Error, Reasoning Error, Contextual Understanding Error, Tool Usage Error, Tool/Agent Invocation Error, Reasoning-Action Mismatch, Resource Access Error, System Error (the paper does not define this taxonomy; it appears to be the annotation-interface's category list).

**Task formulation & metrics.** The attribution system outputs a ranked list of failure steps (with reasons); repeated runs over 3 seeds are consolidated. *Attribution*: nDCG@5 / nDCG@all (exponential or linear gain) of the predicted ranking against the human consensus ranking; a random baseline is given. *Reasoning*: LLM-as-judge (GPT-5.1, temp 0) scores 1–10 for fail-reason, ideal-action and overall agreement with the consolidated annotator reasoning. The paper's conclusion: under multi-perspective evaluation LLMs are far from random (contrary to the "near-random" picture from Who&When's single-label step accuracy).

**Baselines (paper Table 2; nDCG@5 exp. gain, and judge average).**

| Model (All-at-Once with taxonomy) | Hand-crafted nDCG@5 | Automatic nDCG@5 | Hand-crafted judge | Automatic judge |
|---|---|---|---|---|
| Random | 0.128 | 0.315 | – | – |
| GPT-4.1 | 0.431 | 0.676 | 7.63 | 7.78 |
| GPT-5.1 | 0.375 | 0.784 | 7.62 | 8.25 |
| o3-mini | 0.437 | 0.394 | 7.48 | 7.37 |
| Claude Sonnet 4.5 | 0.440 | 0.789 | 7.95 | 8.23 |
| Qwen3-8B | 0.294 | 0.668 | 6.11 | 6.54 |
| GPT-oss-120B | 0.425 | 0.703 | 7.51 | 7.92 |

(`leaderboard.json` in the eval repo lists the same models with manual_num_scored = 157, automatic_num_scored = 120.)

## Schema

Raw annotation file `MP-Bench/<annotator>/<split>/<n>.json` (867 files = 3 × 289):

| Field | Meaning |
|---|---|
| `log_source` | GitHub URL of the source log: `…/Agents_Failure_Attribution/tree/main/Who&When/{Hand-Crafted,Algorithm-Generated}/<k>.json` or `…/MAST/tree/main/traces/MagenticOne_GAIA/gaia_validation_level_{2,3}__MagenticOne/<task-uuid>/0/console_log.txt`. |
| `annotation` | List (possibly empty) of flagged steps, each `{step, fail_annotation ("1"), fail_category, fail_reason, ideal_action}`. `step` is a **0-based index** into the step list defined below (string). |

Normalised format produced by the official `build_annotated_from_log_source.py` (re-implemented in our `analyze_mp_bench.py`): `{question, ground_truth, is_correct, system_prompt, history:[{content, role, step, fail_annotation, fail_category, fail_reason, ideal_action}]}` where for Who&When JSON logs the steps are the `history` entries (role = agent `name` or `role`), and for MAST console logs the steps are the turns delimited by `---------- <AgentName> ----------` lines after the `SCENARIO.PY STARTING` marker (question from `prompt.txt`, answer from `expected_answer.txt` in the same folder).

Our fetched copy: `data/mp_bench/sources/index.json` maps a 16-hex key → `{log_source, raw_url, refs (annotation files), files}`; each key directory holds the source JSON or `console_log.txt` + `prompt.txt` + `expected_answer.txt`.

## Statistics (computed from the data)

| Statistic | Overall | manual (hand-crafted MAS) | automatic (algorithm-generated MAS) |
|---|---|---|---|
| # execution logs (instances; all failed runs) | 289 (39 missing source) | 130 | 120 |
| # annotation files (3 annotators x instances) | 867 | | |
| source of logs | {'Who&When/Algorithm-Generated': 120, 'MAST/MagenticOne_GAIA L2': 73, 'Who&When/Hand-Crafted': 57} | {'MAST/MagenticOne_GAIA L2': 73, 'Who&When/Hand-Crafted': 57} | {'Who&When/Algorithm-Generated': 120} |
| steps per log | mean 23.29, median 10.0, min 5, max 130 | mean 36.76, median 31.5, min 5, max 130 | mean 8.7, median 10.0, min 5, max 10 |
| steps histogram | 0-4: 0, 5-9: 73, 10-19: 95, 20-29: 16, 30-49: 44, 50-99: 13, >=100: 9 | 0-4: 0, 5-9: 19, 10-19: 29, 20-29: 16, 30-49: 44, 50-99: 13, >=100: 9 | 0-4: 0, 5-9: 54, 10-19: 66, 20-29: 0, 30-49: 0, 50-99: 0, >=100: 0 |
| distinct agents per log | mean 3.44, median 4.0, min 1, max 6 | mean 3.25, median 3.0, min 1, max 6 | mean 3.64, median 4.0, min 1, max 4 |
| characters per log | mean 32096.39, median 15585.5, min 2851, max 168851 | mean 50983.37, median 34990.5, min 3833, max 168851 | mean 11635.49, median 8081.5, min 2851, max 112210 |
| flagged steps per annotation file (one annotator, one log) | mean 4.96, median 3.0, min 0, max 59 | | |
| distinct flagged steps per log (union over 3 annotators) | mean 9.15, median 6.0, min 0, max 78 | mean 12.71, median 8.5, min 0, max 78 | mean 5.3, median 5.0, min 1, max 10 |
| flagged (step) consensus: #steps flagged by 1/2/3 annotators | {'flagged_by_1_annotators': 1242, 'flagged_by_2_annotators': 659, 'flagged_by_3_annotators': 387} | {'by_1': 934, 'by_2': 473, 'by_3': 245} | {'by_1': 308, 'by_2': 186, 'by_3': 142} |
| rel. position of earliest majority-flagged step ((idx+1)/len) | mean 0.4, median 0.3333, min 0.0155, max 1.0 | mean 0.45, median 0.3726, min 0.0155, max 1.0 | mean 0.36, median 0.3, min 0.1, max 1.0 |
| rel. position of all flagged steps | mean 0.6, median 0.6046511627906976, min 0.015503875968992248, max 1.0 | | |

**Failure-category distribution (over all annotator step flags):**

| fail_category | flags | % |
|---|---|---|
| Planning Error | 765 | 20.6 |
| Verification Error | 657 | 17.7 |
| Reasoning Error | 500 | 13.4 |
| Contextual Understanding Error | 474 | 12.7 |
| Tool/Agent Invocation Error | 366 | 9.8 |
| Tool Usage Error | 355 | 9.5 |
| Reasoning-Action Mismatch | 318 | 8.5 |
| Resource Access Error | 161 | 4.3 |
| System Error | 124 | 3.3 |
|  | 1 | 0.0 |

**Agent blamed (agent at flagged step; Orchestrator sub-roles collapsed), top 15:**

| agent | flags | % |
|---|---|---|
| Orchestrator | 880 | 23.6 |
| WebSurfer | 820 | 22.0 |
| MagenticOneOrchestrator | 700 | 18.8 |
| Verification_Expert | 189 | 5.1 |
| Computer_terminal | 102 | 2.7 |
| FileSurfer | 95 | 2.6 |
| Assistant | 80 | 2.1 |
| Validation_Expert | 68 | 1.8 |
| DataVerification_Expert | 50 | 1.3 |
| ComputerTerminal | 40 | 1.1 |
| WebServing_Expert | 38 | 1.0 |
| DataAnalysis_Expert | 37 | 1.0 |
| PythonDebugging_Expert | 34 | 0.9 |
| VerificationExpert | 17 | 0.5 |
| VideoContentAnalysis_Expert | 17 | 0.5 |

**Agent blamed by split (top 8 each):**

*manual*

| agent | flags | % |
|---|---|---|
| Orchestrator | 880 | 33.7 |
| WebSurfer | 820 | 31.4 |
| MagenticOneOrchestrator | 700 | 26.8 |
| FileSurfer | 95 | 3.6 |
| Assistant | 80 | 3.1 |
| ComputerTerminal | 40 | 1.5 |

*automatic*

| agent | flags | % |
|---|---|---|
| Verification_Expert | 189 | 17.1 |
| Computer_terminal | 102 | 9.2 |
| Validation_Expert | 68 | 6.1 |
| DataVerification_Expert | 50 | 4.5 |
| WebServing_Expert | 38 | 3.4 |
| DataAnalysis_Expert | 37 | 3.3 |
| PythonDebugging_Expert | 34 | 3.1 |
| VerificationExpert | 17 | 1.5 |



## Example trajectory

Instance `manual/18.json` (source: MAST/MagenticOne_GAIA L2; log_source = https://github.com/multi-agent-systems-failure-taxonomy/MAST/tree/main/traces/MagenticOne_GAIA/gaia_validation_level_2__MagenticOne/0ff53813-3367-4f43-bcbd-3fd725c1bf4b/0/console_log.txt), 9 steps, 13726 characters, 3 distinct agents, 3 annotators.

**Task:** What two-word type of model did Manash Pratim Kashyap's and PS Fader's studies in customer retention studies published during 2018-2019 have in common (no punctuation)?

**Ground-truth answer:** beta geometric

**Step 0 — user**

> What two-word type of model did Manash Pratim Kashyap's and PS Fader's studies in customer retention studies published during 2018-2019 have in common (no punctuation)?

**Step 1 — MagenticOneOrchestrator**

> We are working to address the following user request:
> 
> What two-word type of model did Manash Pratim Kashyap's and PS Fader's studies in customer retention studies published during 2018-2019 have in common (no punctuation)?
> 
> 
> To answer this request we have assembled the following team:
> 
> Assistant: A helpful and general-purpose AI assistant that has strong language skills, Python skills, and Linux command line skills.
> ComputerTerminal: A computer terminal that performs no other action than runnin […]

**Step 2 — MagenticOneOrchestrator**

> Please conduct a search for academic publications or articles by Manash Pratim Kashyap and PS Fader on customer retention from 2018-2019. Focus on identifying the type of models used in these studies and look for a two-word model that is common to both.

**Step 3 — WebSurfer**  **⟵ ANNOTATED ERROR STEP**

> I typed 'Manash Pratim Kashyap PS Fader customer retention model 2018-2019' into the browser search bar.
> 
> The web browser is open to the page [Manash Pratim Kashyap PS Fader customer retention model 2018-2019 - Cerca](https://www.bing.com/search?q=Manash+Pratim+Kashyap+PS+Fader+customer+retention+model+2018-2019&FORM=QBLH).
> The viewport shows 39% of the webpage, and is positioned at the top of the page
> The following text is visible in the viewport:
> 
> Microsoft e i suoi fornitori di terze parti ut […]

**Step 4 — MagenticOneOrchestrator**

> Please check the search results for any documents or mentions that specify the model type used by both Manash Pratim Kashyap and PS Fader in their customer retention studies from 2018-2019.

**Step 5 — WebSurfer**  **⟵ ANNOTATED ERROR STEP**

> I clicked 'A Simple Model for Analyzing the Customer Retention Comparing Rural and Urban Store'.
> 
> The web browser is open to the page [Manash Pratim Kashyap PS Fader customer retention model 2018-2019 - Cerca](https://www.bing.com/search?q=Manash+Pratim+Kashyap+PS+Fader+customer+retention+model+2018-2019&FORM=QBLH).
> The viewport shows 39% of the webpage, and is positioned at the top of the page
> The following text is visible in the viewport:
> 
> Microsoft e i suoi fornitori di terze parti utilizzano […]

**Step 6 — MagenticOneOrchestrator**  **⟵ ANNOTATED ERROR STEP**

> Please extract more detailed information from the identified webpage, focusing on the specific type of model mentioned in the studies, and verify if it matches a two-word model type used by both authors.

**Step 7 — WebSurfer**  **⟵ ANNOTATED ERROR STEP**

> The studies by Manash Pratim Kashyap and others, including PS Fader, during 2018-2019, primarily mention customer retention models that include the use of Reinartz and Kumar’s model from 2000, as well as a modified version by Fader, Hardie, and Lee in 2005. These models focus on assessing customer retention by evaluating customer switching behaviors and often employ migration or Markov models to estimate the probabilities of customers transitioning between states. The models emphasize analyzing  […]

**Step 8 — MagenticOneOrchestrator**  **⟵ ANNOTATED ERROR STEP**

> FINAL ANSWER: Markov Model
> SCENARIO.PY COMPLETE !#!#
> SCENARIO.PY RUNTIME: 494 !#!#
> RUN.SH COMPLETE !#!#


**Annotations (per annotator):**

- Annotator 1, step 5 (WebSurfer), category *Tool Usage Error*: WebSurfer attempted to click on the Academia.edu link 'A Simple Model for Analyzing the Customer Retention Comparing Rural and Urban Store' but the navigation failed. The browser remained on the Bing search results page instead of navigating to the actual article. This prevented WebSurfer from accessing the detailed content of Kashyap's paper which would have provided more specific model information.  
  Ideal action: WebSurfer should have reported that the click failed to navigate and tried a different approach like typing the URL directly.
- Annotator 1, step 7 (WebSurfer), category *Contextual Understanding Error*: The search results from step 3 clearly mentioned beta-geometric (BG) distribution as a simple probability model for projecting customer retention. This was the direct answer to the question. WebSurfer's summary focused on 'Markov models' mentioned elsewhere in the snippets but completely missed the 'beta-geometric' reference that was prominently visible and directly relevant to the question about Fader's work.  
  Ideal action: WebSurfer should have recognized the 'beta-geometric' mention in the search results.  It should have verified if Kashyap's 2018-2019 study also uses the beta-geometric model by clicking on his paper or searching for more details.'
- Annotator 1, step 8 (MagenticOneOrchestrator), category *Contextual Understanding Error*: The Orchestrator failed to recognize that the answer 'beta geometric' was clearly visible in the search results  
  Ideal action: The Orchestrator should have noticed the 'beta-geometric' reference in search results,and asked WebSurfer to click on Kashyap's paper to verify if it also uses the beta-geometric model. The correct answer 'beta geometric' was visible but not recognized.
- Annotator 2, step 5 (WebSurfer), category *Reasoning-Action Mismatch*: The agent says it clicked a paper, but the page content did not change and no paper was opened.  
  Ideal action: The WebSurfer should have actually opened the linked paper and shown its contents.
- Annotator 2, step 6 (MagenticOneOrchestrator), category *Verification Error*: The Orchestrator did not verify whether the WebSurfer had actually opened a paper or extracted real data before asking for detailed analysis.  
  Ideal action: The Orchestrator should have checked whether a real article page was opened and asked the WebSurfer to open the correct source if not before asking for detailed analysis.
- Annotator 2, step 7 (WebSurfer), category *Reasoning Error*: The WebSurfer drew conclusions without confirming the exact model used in both studies from actual source documents.  
  Ideal action: The WebSurfer should have opened the original studies and confirmed the shared model before summarizing.
- Annotator 2, step 8 (MagenticOneOrchestrator), category *Verification Error*: The Orchestrator finalized the answer without verifying whether the information from earlier steps was correct or supported by real sources.  
  Ideal action: The Orchestrator should have verified the shared model from the original studies before giving the final answer.
- Annotator 3, step 3 (WebSurfer), category *Tool/Agent Invocation Error*: Found search results containing 'beta-geometric (BG) distribution' reference but failed to highlight or extract this key information for the task  
  Ideal action: Should have identified and extracted the 'beta-geometric' model reference visible in the search results, particularly from the Fader and Hardie (2007) citation
- Annotator 3, step 5 (WebSurfer), category *Tool/Agent Invocation Error*: Failed to navigate to the academic paper, clicking did not successfully access the detailed content needed for analysis  
  Ideal action: Should have tried alternative navigation methods or accessed the ResearchGate link that was also available in search results
- Annotator 3, step 7 (WebSurfer), category *Tool/Agent Invocation Error*: Provided general summary without identifying the specific 'beta geometric' model that was mentioned in the search results, focusing on Markov models instead  
  Ideal action: Should have specifically identified and reported the 'beta-geometric' model mentioned in the Fader and Hardie research visible in search results
- Annotator 3, step 8 (MagenticOneOrchestrator), category *Reasoning Error*: Concluded with 'Markov Model' instead of 'beta geometric' despite evidence in search results pointing to beta-geometric distribution  
  Ideal action: Should have analyzed the search results more carefully and identified 'beta geometric' as the common model type based on the Fader and Hardie (2007) reference

Step votes: {'3': ['3'], '5': ['1', '2', '3'], '6': ['2'], '7': ['1', '2', '3'], '8': ['1', '2', '3']}. Earliest majority-flagged step: 5.


(normalised example written to /dataDisk/home/thanhdo/failure-attribution-datasets/notes/mp_bench_example_norm.json, 22.1 KB)


Source-log coverage at analysis time: 250 of 289 logs (120 automatic + 130 manual); the remaining 39 manual MAST level-2/level-3 console logs were still being fetched from GitHub when the statistics were computed (fetch log: `data/mp_bench_fetch.log`; re-run `scripts/analyze_mp_bench.py` to refresh). Annotation-file statistics (category, consensus, flags per file) are computed over the annotations of the covered logs only.

## Notes for the report

- **No single gold label.** Each log has three independent annotation sets; a step is flagged by 1, 2 or 3 annotators (54 % / 29 % / 17 % of flagged steps in our data; paper: 56.1 / 27.8 / 16.2 %). Annotators flag *several* steps per log (mean 5 per annotator-log, union mean 9, max 78), so the benchmark is a *ranking/set* task, not "find the one decisive step". For comparability with the other datasets we report the position of the *earliest majority-flagged* step (mean 0.40 of the log), but this is our derived quantity, not an official label.
- **Categories are per-flag, per-annotator.** `fail_category` comes from a 9-class list (Planning, Verification, Reasoning, Contextual Understanding, Tool Usage, Tool/Agent Invocation, Reasoning-Action Mismatch, Resource Access, System Error) that the paper does not define; different annotators often give the same step different categories (see example: step 5 = Tool Usage / Reasoning-Action Mismatch / Tool/Agent Invocation). `ideal_action` (counterfactual fix) is unique to this dataset among the four.
- **Pointer-only release.** The repo contains annotations only; trajectories must be fetched from the Who&When GitHub repo (JSON) and the MAST repo (`console_log.txt`, parsed on `---------- Agent ----------` delimiters). Step indices are 0-based positions in those reconstructions, so they depend on the parser; we re-implemented the official parser rather than executing it. In MAST logs the orchestrator is named `MagenticOneOrchestrator` and the first step is the raw `user` prompt; in Who&When HC logs it is `Orchestrator (thought)` / `Orchestrator (-> X)` — the blame tables above therefore list both spellings.
- **Overlap.** 177 of the 289 logs are the Who&When logs (120 AG + 57 HC) re-annotated — a direct test of label reliability: MP-Bench's three annotators frequently disagree with each other and with Who&When's single decisive step. The other 112 logs are Magentic-One GAIA runs from the MAST failure-taxonomy corpus (level 2/3 validation tasks), also output-only console logs.
- **Counts differ across sources.** README: 289 logs / 121 MAS; eval README: 169 manual + 126 automatic; released files: 169 manual + 120 automatic per annotator; leaderboard scores 157 manual + 120 automatic. Treat 289 (169/120) as canonical.
- **Metrics.** nDCG@5 against the consensus ranking plus an LLM-judge (GPT-5.1) score of the reasoning; the leaderboard (`yeonjun_MP-Bench/leaderboard.json`) uses nDCG@5 only. Automatic (short, 5–10 steps) logs are much easier (nDCG ≈ 0.7–0.8) than hand-crafted ones (≈ 0.4; random 0.13).
- **License.** Adobe Research License v1.2 (non-commercial) for the annotations; the pointed-to logs carry their own terms. Evaluation requires paid API models for the consolidation/judge steps.
