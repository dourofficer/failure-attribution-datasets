# CORRECT-Error (CORRECT: Condensed Error Recognition via Knowledge Transfer in Multi-agent Systems)

## Identity

| Field | Value |
|---|---|
| Full title | **CORRECT: COndensed eRror RECognition via knowledge Transfer in multi-agent systems** |
| Authors / affiliation | Yifan Yu (UIUC), Moyan Li (Amazon), Shaoyuan Xu (Amazon), Jinmiao Fu (Amazon), Xinhai Hou (U. Michigan), Fan Lai (UIUC), Bryan Wang (Amazon) |
| Venue | ICML 2026 (poster; PMLR 306). Listed on Amazon Science. |
| arXiv | [2509.24088](https://arxiv.org/abs/2509.24088) (v1, 28 Sep 2025, cs.MA) |
| Links | Paper PDF: https://arxiv.org/pdf/2509.24088 · Amazon Science page: https://www.amazon.science/publications/correct-condensed-error-recognition-via-knowledge-transfer-in-multi-agent-systems · Code: https://github.com/UIUC-MLSys/CORRECT · Data: https://huggingface.co/datasets/yifanyu/CORRECT-Error |
| License | Apache-2.0 (dataset card and GitHub LICENSE) |
| Availability | **Public, downloaded** (not gated). HF dataset last modified 2026-06-10. Single `test` split, 2,226 rows, one parquet file. GitHub repo also cloned (code + pre-extracted error schemata + similarity maps; it does *not* contain the trajectories, which it downloads from HF). |
| On-disk size | HF data: 1 parquet file (`data/test-00000-of-00001.parquet`), ~20 MB; GitHub clone ~20 MB (schemata/similarities JSON); total `data/correct_error/` = 40 MB |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/correct_error/CORRECT-Error/data/test-00000-of-00001.parquet` (data); `/dataDisk/home/thanhdo/failure-attribution-datasets/data/correct_error/CORRECT_github/` (code) |

## Description

**Purpose.** CORRECT-Error is a benchmark for *step-level decisive-error attribution* in LLM multi-agent systems: given a failed MAS trajectory, predict the agent (`mistake_agent`) and the step index (`mistake_step`) of the **decisive error** — defined as the earliest step whose correction would have flipped the trajectory from failure to success (same formulation as Who&When, Zhang et al. ICML 2025). It was released as the evaluation set for the CORRECT framework (a training-free method that caches distilled "error schemata" from past failures and retrieves them to guide an LLM detector).

**Source MAS / tasks.** All trajectories are produced by a **Magentic-One variant** (Fourney et al. 2024) running inside AutoGen with *selector-group-chat* workflow control. The agent roles seen in the data are `Planner` (the orchestrator-like role that decomposes the task, analyses the previous result and decides the next action), `WebSurfer`, `Coder`, `CodeExecutor`, `FileSurfer`; every trajectory begins with a `user` message that states the task and the available capabilities. Seven task suites: GAIA (Level-1 for the gpt-5-nano subset), HotpotQA, MuSiQue, 2WikiMultihopQA ("wikimqa"), ARC, MATH-500, MMLU-Pro. Two trajectory-generator LLMs: `gpt-4o-mini` (318 trajectories) and `gpt-5-nano` (1,908).

**How failures were obtained — injected, not natural.** Three-stage bootstrap pipeline (paper §4):
1. *Diverse trajectory collection*: generate a large pool of **successful** trajectories across the seven tasks, plus a small set of human-annotated real failure trajectories as exemplars (the Who&When hand-crafted set).
2. *Semantic error-schema matching*: each successful trajectory is paired (by semantic similarity) with its closest human-labelled failure; GPT-5 devises an injection strategy (where to inject, how to adapt the error pattern).
3. *Contextual error injection*: the generator model rewrites one step into an erroneous action at the designated point, so the injected step is the decisive error by construction. The paper states that the injected distribution "closely matches natural error distributions derived from human annotations", and that synthesis cost >3 B tokens.

**Human validation (paper §4 / §5).** Three expert labelers (>120 h total) saw a blind, balanced mix of synthetic and real (human-labelled) failure trajectories: 47.1% of synthetic trajectories were judged human-labelled, 42.3% of genuine ones were correctly identified; 94.4% of synthetic trajectories were judged genuine by ≥2 of 3 labelers, 52.9% unanimously. No per-record human check of the step label is reported; there is no inter-annotator κ on the labels themselves. Labels (agent + step) come from the injection pipeline (LLM-generated).

**Label types.** Per trajectory: `mistake_agent` (string), `mistake_step` (int, 0-based index into `history`, where index 0 is the user task message), `mistake_reason` (free text — **empty for all 2,226 records in the release**), `is_corrected` (always `false`), `groundtruth` (**empty for all records**), `question`. No failure-category / taxonomy label. Every trajectory is a failure (there are no success trajectories in the release).

**Task formulation & metrics.** Step-level accuracy with tolerance: Acc@k = prediction counted correct if |pred − gt| ≤ k (paper reports Acc@0 for Who&When and Acc@1/3/5 for CORRECT-Error, averaged over 5 runs). Agent-level accuracy is not reported for CORRECT-Error. The released evaluator (`src/evaluate.py`, strict exact match, `--tolerance`) uses the parquet labels as ground truth.

**Reported baselines on CORRECT-Error (paper Table 2; detector = Qwen-2.5-7B according to the text, accuracy %):**

| Subset | Method | GAIA | HotpotQA | MuSiQue | WikiMQA | ARC | Math500 | MMLU-Pro |
|---|---|---|---|---|---|---|---|---|
| gpt-4o-mini, Acc@1/@3/@5 | LLM-as-a-Judge | 28.6/42.9/50.0 | 34.8/59.4/63.8 | 27.8/77.8/77.8 | 14.7/55.9/64.7 | 64.0/75.0/78.0 | 10.2/23.4/35.6 | 58.3/62.5/66.7 |
| gpt-4o-mini, Acc@1/@3/@5 | CORRECT | 28.6/50.0/64.3 | 60.9/94.2/95.7 | 38.9/88.9/88.9 | 44.1/88.2/94.1 | 80.4/88.2/91.2 | 57.1/87.8/95.9 | 69.1/88.2/94.1 |
| gpt-5-nano, Acc@1/@3/@5 | LLM-as-a-Judge | 16.7/27.8/38.9 | 14.7/48.9/65.8 | 11.9/43.9/58.8 | 6.4/35.6/56.1 | 62.8/69.6/71.1 | 41.8/57.1/64.3 | 50.0/64.7/70.6 |
| gpt-5-nano, Acc@1/@3/@5 | CORRECT | 30.6/44.4/52.8 | 35.8/72.7/84.3 | 32.7/61.2/77.2 | 16.9/49.9/69.0 | 80.4/88.2/91.2 | 57.1/87.8/95.9 | 69.1/88.2/94.1 |

(Average gains reported: +20.1/+27.6/+28.7 points on the gpt-4o-mini subset, +16.8/+20.1/+18.9 on gpt-5-nano. On Who&When hand-crafted, CORRECT lifts Acc@0 from 3.5→12.1 (Qwen-2.5-7B) and 8.6→17.2 (GPT-5).)

## Schema

Single parquet, one row per trajectory (HF `datasets` features):

| Field | Type | Meaning |
|---|---|---|
| `trajectory_id` | str | `{generator_model}_{dataset}_{question_id}` (e.g. `gpt-5-nano_gaia_level1_task22_1`), unique |
| `dataset` | str | task suite: `arc`, `hotpot`, `musique`, `wikimqa`, `math500`, `mmlu_pro`, `gaia` |
| `generator_model` | str | LLM that generated (and corrupted) the trajectory: `gpt-4o-mini` or `gpt-5-nano` |
| `gaia_level` | float/null | `1.0` for the 36 GAIA gpt-5-nano rows, null elsewhere |
| `question` | str | task posed to the MAS |
| `groundtruth` | str | reference answer — empty string in all rows |
| `question_id` | str | source task id, e.g. `task12_2`; the `_k` suffix indexes injected variants of the same source question |
| `history` | list[{role, content}] | the full trajectory; `role` ∈ {user, Planner, WebSurfer, Coder, CodeExecutor, FileSurfer}; `history[0]` is always the `user` task message |
| `mistake_agent` | str | agent blamed for the decisive error (LLM-written; includes variants like `[Planner]`, `Unknown`) |
| `mistake_step` | int | 0-based index into `history` of the decisive error |
| `mistake_reason` | str | explanation — empty in all rows |
| `is_corrected` | bool | always `false` |
| `level` | int | source-side metadata, always 0 |

GitHub repo: `src/` (inference, schema generation, `evaluate.py`), `data/schemata_correct_error_{gpt4omini,gpt5nano}/<task>/` (error schemata used by CORRECT), `data/similarities*/` (trajectory-similarity maps), `scripts/` (shell entry points). None of this was executed.

## Statistics (computed from the parquet; see `correct_error_stats.json`)

| Statistic | Value |
|---|---|
| Trajectories | **2,226** (single `test` split); all are failures with exactly one labelled decisive error |
| By task suite | wikimqa 733 · hotpot 578 · musique 312 · arc 304 · math500 157 · mmlu_pro 92 · gaia 50 |
| By generator | gpt-5-nano 1,908 · gpt-4o-mini 318 |
| Distinct source questions | 1,440 (1.55 injected variants per source question on average, max 5) |
| Steps per trajectory (`len(history)`, incl. user msg) | mean 11.8 · median 10 · min 2 · max 22 |
| Steps histogram | 2–4: 610 · 5–8: 483 · 9–12: 214 · 13–16: 72 · 17–20: 38 · 21–22: 809 |
| Steps by task (median) | arc 2 · mmlu_pro 2 · math500 5 · gaia 10 · hotpot 10 · wikimqa 14 · musique 21 |
| Distinct agents per trajectory (excl. `user`) | mean 1.87 · median 2 · min 1 · max 5 (incl. user: mean 2.87, max 6) |
| Messages per role (all trajectories) | Planner 13,129 · WebSurfer 10,637 · user 2,226 · CodeExecutor 175 · Coder 126 · FileSurfer 18 |
| Characters per trajectory | mean 27.7 k · median 18.8 k · min 806 · max 183.8 k |
| `mistake_step` | mean 5.2 · median 5 · min 0 · max 19 |
| Relative error position (step/(len−1)) | mean 0.69 · median 0.95; buckets 0–.2: 346 · .2–.4: 367 · .4–.6: 163 · .6–.8: 185 · .8–1: 1,165 |
| Faulty agent (normalised) | Planner 1,639 (73.6%) · WebSurfer 467 (21.0%) · Unknown 42 · Coder 23 · CodeExecutor 22 · Orchestrator 17 · ComputerTerminal 5 · other 11 |
| Label consistency | `history[mistake_step].role == mistake_agent` for 2,040/2,226 (91.6%); 43 rows have `mistake_step = 0` (42 of them with agent `Unknown`), i.e. they point at the user message |
| `mistake_reason` non-empty | 0 / 2,226 |
| `groundtruth` non-empty | 0 / 2,226 |
| Failure category labels | none |
| Success trajectories | none (the successful "parents" are not released) |

Note on positions: 610 trajectories have ≤4 steps (e.g. user→Planner→answer for ARC/MMLU-Pro), where the only possible error step is the last one, which inflates the 0.8–1.0 bucket; 809 trajectories have 21–22 steps, which looks like a round cap of the generating MAS.

## Example trajectory

Chosen: `gpt-5-nano_gaia_level1_task22_1` (GAIA L1, 8 steps, 3 roles, decisive error at step 6 by WebSurfer). Raw record: `correct_error_example.json`; normalised: `correct_error_example_norm.json`. Content truncated at ~500 chars per step here.

**Source id:** `gpt-5-nano_gaia_level1_task22_1`  
**Task:** In Series 9, Episode 11 of Doctor Who, the Doctor is trapped inside an ever-shifting maze. What is this location called in the official script for the episode? Give the setting exactly as it appears in the first scene heading.  
**Ground truth:** —  
**Final output:** **Analysis of Previous Result:**
The BBC PDF view shows the first scene heading line as "INT. CASTLE - DAY" at the top of the page, indicating the location name and time.

**Updated Understanding:**
The first scene heading in the official script (Series 9, Episode 11, Heaven Sent) is exactly:
INT. CASTLE - DAY

**Decis […] ww.bbc.co.uk/writers/documents/doctor-who-s9-ep11-heaven-sent-steven-moffat.pdf)

**Step 0 — user**
> You have been given the following task:
> 
> In Series 9, Episode 11 of Doctor Who, the Doctor is trapped inside an ever-shifting maze. What is this location called in the official script for the episode? Give the setting exactly as it appears in the first scene heading.
> 
> Available capabilities:
> - WebSurfer: Can perform REAL internet searches and browse websites
> - FileSurfer: Can read and analyze file […] teps
> 2. Gather information systematically
> 3. Build upon previous results
> 
> What is your first action?

**Step 1 — Planner**
> **Analysis of Previous Result:**
> No prior results to build on. We’re at the information-gathering step to locate the first scene heading from the official Doctor Who script for Series 9, Episode 11.
> 
> **Updated Understanding:**
> Task is to identify the exact first scene heading as it appears in the official script for Doctor Who Series 9, Episode 11 (the Doctor is in an ever-shifting maze). We must  […] 
> First action: Initiate WebSurfer to locate the official script and extract the first scene heading.

**Step 2 — WebSurfer**
> I typed 'Heaven Sent Doctor Who shooting script first scene heading' into the browser search bar.
> 
> The web browser is open to the page [Heaven Sent Doctor Who shooting script first scene heading at DuckDuckGo](https://duckduckgo.com/?q=Heaven+Sent+Doctor+Who+shooting+script+first+scene+heading&ia=web).
> The viewport shows 41% of the webpage, and is positioned at the top of the page
> The following te […] ly": "true",
>         "apple-mobile-web-app-capable": "no"
>     }
> }
> 
> Here is a screenshot of the page.

**Step 3 — Planner**
> **Analysis of Previous Result:**
> The DuckDuckGo/BBC results page is visible and shows a BBC PDF link for the official script (DW9 - EP 11 Heaven Sent) along with other transcript sources. The first scene heading has not yet been extracted.
> 
> **Updated Understanding:**
> To answer precisely, we need to open the official BBC script (DW9 - EP 11 Heaven Sent) and read the first scene heading on the first […] n: Use WebSurfer to open the BBC official script URL and extract the exact first scene heading text.

**Step 4 — WebSurfer**
> I typed 'https://www.bbc.co.uk/writers/documents/doctor-who-s9-ep11-heaven-sent-steven-moffat.pdf' into the browser address bar.
> 
> The web browser is open to the page [](https://www.bbc.co.uk/writers/documents/doctor-who-s9-ep11-heaven-sent-steven-moffat.pdf).
> The viewport shows 100% of the webpage, and is positioned at the top of the page
> The following text is visible in the viewport:
> 
> The following metadata was extracted from the webpage:
> 
> {}
> 
> Here is a screenshot of the page.

**Step 5 — Planner**
> **Analysis of Previous Result:**
> The BBC official script PDF is open, but the first scene heading (the line that starts with INT. or EXT.) has not been extracted yet. We currently only have the title page visible.
> 
> **Updated Understanding:**
> We need the exact first scene heading text from the BBC official script for Doctor Who Series 9, Episode 11 (Heaven Sent), including formatting and punctuatio […] t action: Use WebSurfer to locate and extract the exact first scene heading from the BBC script PDF.

**Step 6 — WebSurfer**  ⟵ ANNOTATED ERROR
> I typed 'https://www.bbc.co.uk/writers/documents/doctor-who-s9-ep11-heaven-sent-steven-moffat.pdf' into the browser address bar.
> 
> The web browser is open to the page (https://www.bbc.co.uk/writers/documents/doctor-who-s9-ep11-heaven-sent-steven-moffat.pdf).
> The viewport shows 100% of the webpage, and is positioned at the top of the page
> The following text is visible in the viewport:
> INT. CASTLE - DAY
> The following metadata was extracted from the webpage:
> 
> {}
> 
> Here is a screenshot of the page.

**Step 7 — Planner**
> **Analysis of Previous Result:**
> The BBC PDF view shows the first scene heading line as "INT. CASTLE - DAY" at the top of the page, indicating the location name and time.
> 
> **Updated Understanding:**
> The first scene heading in the official script (Series 9, Episode 11, Heaven Sent) is exactly:
> INT. CASTLE - DAY
> 
> **Decision:**
> - TASK_COMPLETE
> - Final Answer: INT. CASTLE - DAY
> 
> Source: BBC official script PDF (https://www.bbc.co.uk/writers/documents/doctor-who-s9-ep11-heaven-sent-steven-moffat.pdf)

**Annotation**

- faulty agent: `WebSurfer`
- faulty step: `6`
- category: `None`
- reason: (none provided)
- dataset: gaia
- generator_model: gpt-5-nano
- question_id: task22_1
- is_corrected: false
- level: 0
- step_indexing: 0-based index into `history`, where index 0 is the user task message

Caveat for this example: because the release has no `groundtruth` and no `mistake_reason`, the nature of the injected error at step 6 cannot be verified from the record alone; by construction it is the step rewritten by the injection pipeline (here the WebSurfer "reads" a scene heading from the PDF viewport that the previous visit of the same URL did not show).

## Notes for the report

- **Largest step-labelled attribution set** in this survey (2,226 vs. 184 for Who&When; the paper calls it 12.3×), but it is **single-framework** (one Magentic-One-style MAS, 2 generator LLMs) and **synthetic**: every failure is an LLM-injected corruption of a successful run, matched to a real human-annotated failure as a template. 
- Labels are **step + agent only**; no error taxonomy, no textual reason, no ground-truth answer, no success/failure flag (all failed), and the successful parent trajectories are not released — so the benchmark cannot be used for failure *detection*, only localisation.
- Label noise indicators: `mistake_agent` contains free-form strings (`[Planner]`, `Unknown`, "Refusal to target any agent; providing prevention guidance instead", `Orchestrator`/`Solver`/`Economist` which are not roles that appear in `history`), 43 rows point at step 0 (the user message), and 8.4% of rows have an agent label that does not match the role at the labelled step.
- Heavy **role imbalance** (Planner = 74% of faults) and **length bimodality** (many 2-step and many 21–22-step trajectories); a trivial "blame the Planner at the last step" prior is strong for short traces.
- Overlap: the pipeline is seeded with Who&When hand-crafted failures and the GAIA tasks overlap with Who&When / TRAIL / MAST-Data (all include GAIA); task suites otherwise differ (multi-hop QA, ARC, MATH-500, MMLU-Pro).
- Indexing convention: `mistake_step` is a 0-based index into `history` including the user message at index 0 (verified: 91.6% role agreement under this convention vs. 4.3% under a 1-based reading).
