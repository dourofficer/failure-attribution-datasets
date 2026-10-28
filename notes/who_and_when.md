# Who&When — dataset notes

## Identity

| Field | Value |
|---|---|
| Full title | *Which Agent Causes Task Failures and When? On Automated Failure Attribution of LLM Multi-Agent Systems* |
| Authors / affiliation | Shaokun Zhang, Ming Yin, Jieyu Zhang, Jiale Liu, Zhiguang Han, Jingyang Zhang, Beibin Li, Chi Wang, Huazheng Wang, Yiran Chen, Qingyun Wu — Penn State University, Duke University, University of Washington, Nanyang Technological University, Meta, Google DeepMind, Oregon State University, AG2AI Inc. |
| Venue | ICML 2025 (spotlight) |
| arXiv | [2505.00212](https://arxiv.org/abs/2505.00212) (v3, June 2025) |
| Paper HTML | https://arxiv.org/html/2505.00212 |
| Code | https://github.com/mingyin1/Agents_Failure_Attribution (mirror: ag2ai/Agents_Failure_Attribution) |
| Data | https://huggingface.co/datasets/Kevin355/Who_and_When (also as JSON files inside the GitHub repo) |
| License | No explicit license on the HF dataset card or the GitHub repo (no LICENSE file); the arXiv paper is CC BY 4.0. Underlying queries come from GAIA (Apache-2.0-style terms via HF gated access) and AssistantBench. Treat as research-use. |
| Availability | **Downloaded in full**, ungated. |
| On-disk size | 9.5 MB (two parquet files + 184 JSON files + HF cache) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/who_and_when/` — JSON logs in `Who&When/Hand-Crafted/{1..58}.json` and `Who&When/Algorithm-Generated/{1..126}.json`; identical content in `Hand-Crafted.parquet` (58 rows) and `Algorithm-Generated.parquet` (126 rows). |

## Description

**Purpose.** First benchmark for *automated failure attribution* in LLM multi-agent systems (MAS): given the log of a MAS run that failed a task, identify the *failure-responsible agent* ("who") and the *decisive error step* ("when") — the earliest step whose correction would have turned the failed trajectory into a success — plus a natural-language explanation.

**Construction.**
- *Algorithm-Generated* subset (126 logs): MAS automatically assembled by the **CaptainAgent** algorithm (AG2 library, GPT-4o backbone) for queries from the GAIA and AssistantBench validation sets. CaptainAgent builds a per-task team of "_Expert" agents (e.g. `Verification_Expert`, `WebServing_Expert`) plus a `Computer_terminal`; 82 distinct expert names appear as the blamed agent across the 126 logs. Only runs that failed the query were kept.
- *Hand-Crafted* subset (58 logs): **Magentic-One** (Orchestrator + WebSurfer, FileSurfer, Coder/Assistant, ComputerTerminal) run on the AssistantBench validation set (28 logs) and 30 random GAIA instances.
- Failures are **natural** (observed in real runs; no injection). Overall 184 failure logs from 127 distinct MAS configurations.
- **Annotation protocol.** Three human experts, three rounds: (1) independent annotation with uncertainty flags (15–30 % of cases flagged), (2) consensus discussion on flagged cases, (3) cross-validation of each other's labels. Effort 30.9 / 30.2 / 23.2 hours per annotator. No formal inter-annotator agreement coefficient is reported.
- **Labels.** `mistake_agent` (agent-level), `mistake_step` (step-level, 0-based index into `history`), `mistake_reason` (free text). No failure-category taxonomy (4 hand-crafted records carry an ad-hoc `mistake_type`).

**Task formulation & metrics.** Agent-level accuracy (predicted agent == `mistake_agent`) and step-level accuracy (predicted step == `mistake_step`; a tolerance-window variant is also discussed). Three LLM attribution methods: *All-at-Once* (whole log in one prompt), *Step-by-Step* (sequential judgement until the first error), *Binary Search*. Evaluated with and without providing the ground-truth answer of the task.

**Baselines reported in the paper (GPT-4o, Table 1; agent-level / step-level accuracy %).**

| Method | Alg.-Generated, with GT | Hand-Crafted, with GT | Alg.-Generated, w/o GT | Hand-Crafted, w/o GT |
|---|---|---|---|---|
| Random | 29.10 / 19.06 | 12.00 / 4.16 | 29.10 / 19.06 | 12.00 / 4.16 |
| All-at-Once | 54.33 / 12.50 | 55.17 / 5.26 | 51.12 / 13.53 | 53.44 / 3.51 |
| Step-by-Step | 35.20 / 25.51 | 34.48 / 7.02 | 26.02 / 15.31 | 32.75 / 8.77 |
| Binary Search | 44.13 / 23.98 | 51.72 / 6.90 | 30.11 / 16.59 | 36.21 / 6.90 |

Reasoning models on Hand-Crafted (Table 4, agent / step): All-at-Once — GPT-4o 54.31 / 4.39, o1 41.38 / 10.34, DeepSeek-R1 56.90 / 3.45; Step-by-Step — GPT-4o 33.62 / 7.90, o1 36.21 / 13.79, DeepSeek-R1 32.76 / 6.90. Headline: best method 53.5 % agent-level and 14.2 % step-level.

## Schema

Each log is one JSON object (one row in parquet). Field sets differ slightly between subsets.

| Field | Subset | Meaning |
|---|---|---|
| `question` | both | The user task (GAIA / AssistantBench query). |
| `question_ID` | both | Source task id (GAIA: UUID; AssistantBench: 64-hex sha). |
| `groundtruth` (HC) / `ground_truth` (AG) | both | Expected final answer. |
| `is_corrected` (HC) / `is_correct` (AG) | both | Whether the run succeeded — always `False` here. |
| `level` | AG (all), HC (30 GAIA) | GAIA difficulty level 1/2/3 or AssistantBench `Medium`/`Hard`. |
| `history` | both | Ordered list of turns. HC: `{role, content}` with `role` in {`human`, `Orchestrator (thought)`, `Orchestrator (-> WebSurfer)`, `WebSurfer`, `FileSurfer`, `Assistant`, `ComputerTerminal`, `Orchestrator (termination condition)`}. AG: `{role (user/assistant), name (agent name), content}`. |
| `system_prompt` | AG | Dict agent-name → system prompt of each generated expert. |
| `mistake_agent` | both | Label: responsible agent name (string; note case inconsistency `WebSurfer` vs `Websurfer`). |
| `mistake_step` | both | Label: **0-based index into `history`** of the decisive error step (stored as a string). In HC, `history[0]` is the human question, so the first agent step is index 1. |
| `mistake_reason` | both | Label: free-text explanation. |
| `mistake_type` | 4 HC records only | Ad-hoc category (`wrong_reasoning`, `Tool failure`, `Processing Error`). |
| `labels` | 1 AG record | Stray extra field. |

Note: in the AG JSON files most scalar values are wrapped in literal quotes (e.g. `"mistake_step": "'0'"`), so strip quotes when parsing.

## Statistics (computed from the data)

| Statistic | Overall | Hand-Crafted | Algorithm-Generated |
|---|---|---|---|
| # trajectories (all failed) | 184 | 58 | 126 |
| source benchmark | {'AssistantBench': 56, 'GAIA': 128} | {'AssistantBench': 28, 'GAIA': 30} | {'GAIA': 98, 'AssistantBench': 28} |
| steps per trajectory | mean 22.24, median 10.0, min 5, max 130 | mean 51.6, median 32.5, min 5, max 130 | mean 8.72, median 10.0, min 5, max 10 |
| steps histogram | 0-4: 0, 5-9: 61, 10-19: 78, 20-29: 11, 30-49: 11, 50-99: 13, 100-999: 10 | 0-4: 0, 5-9: 5, 10-19: 8, 20-29: 11, 30-49: 11, 50-99: 13, 100-999: 10 | 0-4: 0, 5-9: 56, 10-19: 70, 20-29: 0, 30-49: 0, 50-99: 0, 100-999: 0 |
| distinct agents per trajectory (collapsed Orchestrator variants) | mean 3.3, median 4.0, min 1, max 5 | mean 2.57, median 2.0, min 1, max 5 | mean 3.63, median 4.0, min 1, max 4 |
| annotated error step (0-based index) | mean 6.83, median 4.0, min 0, max 82 | mean 15.16, median 12.0, min 1, max 82 | mean 3, median 2.0, min 0, max 9 |
| relative position of error step ((step+1)/len) | mean 0.46, median 0.4, min 0.0388, max 1.0 | mean 0.47, median 0.38, min 0.03875968992248062, max 1.0 | mean 0.45, median 0.4, min 0.1, max 1.0 |
| characters per trajectory (sum of history contents) | mean 28121.86, median 11296.0, min 2851, max 305187 | mean 64003.24, median 42064.0, min 6221, max 305187 | mean 11605.04, median 8132.0, min 2851, max 112210 |
| approx tokens per trajectory (chars/4) | 7030 mean | 16000 mean | 2901 mean |
| is_correct(ed) values | {'False': 184} | | |
| GAIA level (where given) | {'Algorithm-Generated/level1': 36, 'Algorithm-Generated/level2': 58, 'Algorithm-Generated/level3': 4, 'Algorithm-Generated/levelHard': 18, 'Algorithm-Generated/levelMedium': 10, 'Hand-Crafted/level1': 10, 'Hand-Crafted/level2': 16, 'Hand-Crafted/level3': 4} | | |
| mistake_type (only 4 HC records have it) | {'Tool failure': 1, 'wrong_reasoning': 2, 'Processing Error': 1} | | |

**Faulty agent distribution (Hand-Crafted, Orchestrator variants collapsed):**

| mistake_agent | count | % |
|---|---|---|
| WebSurfer | 31 | 53.4 |
| Orchestrator | 18 | 31.0 |
| Assistant | 4 | 6.9 |
| FileSurfer | 3 | 5.2 |
| Websurfer | 2 | 3.4 |

**Faulty agent distribution (Algorithm-Generated, top 15 of 82 distinct names):**

| mistake_agent | count | % |
|---|---|---|
| Verification_Expert | 18 | 14.3 |
| PythonDebugging_Expert | 7 | 5.6 |
| DataAnalysis_Expert | 6 | 4.8 |
| DataVerification_Expert | 5 | 4.0 |
| Validation_Expert | 5 | 4.0 |
| WebServing_Expert | 4 | 3.2 |
| Statistics_Expert | 2 | 1.6 |
| Geometry_Expert | 2 | 1.6 |
| DataExtraction_Expert | 2 | 1.6 |
| Research_Expert | 2 | 1.6 |
| VideoContentAnalysis_Expert | 2 | 1.6 |
| Excel_Expert | 1 | 0.8 |
| HawaiiRealEstate_Expert | 1 | 0.8 |
| Literary_Analysis_Expert | 1 | 0.8 |
| ScientificPaperAnalysis_Expert | 1 | 0.8 |

**Raw mistake_agent strings (top 12):**

| mistake_agent (raw) | count | % |
|---|---|---|
| WebSurfer | 31 | 16.8 |
| Orchestrator | 18 | 9.8 |
| Verification_Expert | 18 | 9.8 |
| PythonDebugging_Expert | 7 | 3.8 |
| DataAnalysis_Expert | 6 | 3.3 |
| DataVerification_Expert | 5 | 2.7 |
| Validation_Expert | 5 | 2.7 |
| Assistant | 4 | 2.2 |
| WebServing_Expert | 4 | 2.2 |
| FileSurfer | 3 | 1.6 |
| Websurfer | 2 | 1.1 |
| Statistics_Expert | 2 | 1.1 |


## Example trajectory

File `Who&When/Hand-Crafted/48.json` (Hand-Crafted, source AssistantBench), 5 steps, 11977 characters, 2 distinct agents.

**Task:** Based on recent years (2020-2023), how likely am I to hit a rainy day (at least 0.5mm of precipitation) if I travel to Seattle during the first week of September? (provide the answer in percentage)

**Ground-truth answer:** 14.2

**Step 0 — human**

> Based on recent years (2020-2023), how likely am I to hit a rainy day (at least 0.5mm of precipitation) if I travel to Seattle during the first week of September? (provide the answer in percentage)
> 

**Step 1 — Orchestrator (thought)**

> Initial plan:
> 
> We are working to address the following user request:
> 
> Based on recent years (2020-2023), how likely am I to hit a rainy day (at least 0.5mm of precipitation) if I travel to Seattle during the first week of September? (provide the answer in percentage)
> 
> 
> To answer this request we have assembled the following team:
> 
> Assistant: A helpful and general-purpose AI assistant that has strong language skills, Python skills, and Linux command line skills.
> ComputerTerminal: A computer termin […]

**Step 2 — Orchestrator (thought)**

> Updated Ledger:
> {
>   "is_request_satisfied": {
>     "reason": "The request has not yet been satisfied as we still need to gather and process the historical weather data for Seattle for the first week of September from 2020 to 2023.",
>     "answer": false
>   },
>   "is_in_loop": {
>     "reason": "We are not in a loop as we have just defined the plan and steps to proceed.",
>     "answer": false
>   },
>   "is_progress_being_made": {
>     "reason": "We have outlined a clear plan and have just begun by initiatin […]

**Step 3 — Orchestrator (-> WebSurfer)**

> Please search for historical weather data for Seattle for the first week of September from 2020 to 2023 and find the number of rainy days (with at least 0.5mm of precipitation) during that period each year.

**Step 4 — WebSurfer**  **⟵ ANNOTATED ERROR STEP**

> I typed 'Seattle historical weather data September 2020-2023' into '0 characters out of 2000'.
> 
> Here is a screenshot of [Seattle historical weather data September 2020-2023 - Search](https://www.bing.com/search?q=Seattle+historical+weather+data+September+2020-2023&form=QBLH&sp=-1&lq=0&pq=&sc=0-0&qs=n&sk=&cvid=273959149E7F422CB8DC7E6C09666674&ghsh=0&ghacc=0&ghpl=). The viewport shows 31% of the webpage, and is positioned at the top of the page.
> The following metadata was extracted from the webpag […]


**Annotation:** mistake_agent = `WebSurfer`, mistake_step = `4` (0-based index into history), mistake_reason = "The agent didn't find enough information to answer the question but directly gave the answer."; is_correct = False; question_ID = 2aa5dd83fbcd0dce9a3dd4592106e5b5edf738008d932e357d477bba80e59ccf; level = None.


(normalised example written to /dataDisk/home/thanhdo/failure-attribution-datasets/notes/who_and_when_example_norm.json, 16.8 KB)


## Notes for the report

- **Step indexing.** `mistake_step` is a 0-based index into `history`. In Hand-Crafted logs `history[0]` is the user's question, so an annotated step `k` is the `k`-th *message* (not the `k`-th agent action); the orchestrator's internal "thought"/ledger updates, its instructions to a specialist (`Orchestrator (-> WebSurfer)`) and the specialist's replies are each separate steps. In Algorithm-Generated logs there is no human turn in `history` (the question is only in `question`); the first entry is the first expert's message, and `Computer_terminal` execution results count as steps too.
- **Two very different regimes.** Algorithm-Generated logs are short (5–10 steps, mean 8.7, ~2.9k tokens) with 1–4 agents; Hand-Crafted logs are long (5–130 steps, mean 51.6, ~16k tokens; 34 of 58 have ≥ 30 steps) — this is why step-level accuracy in the paper collapses to 3–10 % on Hand-Crafted. The blamed agent is `WebSurfer` in 57 % and `Orchestrator` in 31 % of Hand-Crafted logs; in Algorithm-Generated logs the blame is spread over 82 distinct expert names (top: `Verification_Expert` 14 %).
- **Error position.** The decisive error sits on average at 46 % of the trajectory (median 40 %); 8 logs have the error in the last step and 20 at index 0 (all AG, i.e. the very first expert message).
- **Label quirks.** Agent names are inconsistent in case (`WebSurfer` vs `Websurfer`, `Verification_Expert` vs `VerificationExpert`); AG values are double-quoted strings; `is_corrected`/`is_correct` and `groundtruth`/`ground_truth` differ in name between subsets; `level` is missing for 28 HC AssistantBench logs; only 4 records have a `mistake_type`. No failure taxonomy, no severity, one label per log (single decisive step assumed) — exactly the assumption MP-Bench later challenges.
- **Overlaps.** The same 184 logs are the "manual"/"automatic" seeds re-annotated by three experts in **MP-Bench** (177 of its 289 logs: 120 of the 126 AG logs + 57 of the 58 HC logs, via GitHub `log_source` pointers to `mingyin1/Agents_Failure_Attribution`). **TraceElephant** re-runs the same two MAS (CaptainAgent, Magentic-One) on the same benchmarks but records full traces; **Who&When Pro** is the same group's scaled-up successor with injected rather than natural failures.
- **Output-only logs.** Only agent outputs are stored — no system prompts (except AG `system_prompt`), no tool inputs, no screenshots (WebSurfer steps contain the textual page summary only). This is the "partial observation" setting that TraceElephant criticises.
- **Evaluation caveat.** In the Hand-Crafted subset several logs end with the orchestrator giving up or a time-out; annotators still assign a decisive step. The paper evaluates with/without the ground-truth answer because, without it, the attribution model must first decide *that* the run failed.
