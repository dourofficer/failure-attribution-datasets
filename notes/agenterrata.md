# AgentErrata (from "Diagnosing with Insights: Structured Analysis of Agent Failures via Behavioral Abstractions")

## Identity

| Field | Value |
|---|---|
| Full title | **Diagnosing with Insights: Structured Analysis of Agent Failures via Behavioral Abstractions** (introduces the AGENTSCOPE diagnosis method and the **AgentErrata** dataset) |
| Authors / affiliation | Jiayi Bi (Tsinghua Univ.; MSR intern), Yanjie Gao (Microsoft Research), Yuanmin Xie (Tsinghua Univ.; Microsoft intern), Liqun Li (Microsoft), Tianyin Xu (UIUC), Fan Yang (Microsoft Research), Mao Yang (Microsoft Research) |
| Venue | arXiv preprint only (as of 2026-10-16); no venue stated |
| arXiv | [2609.02371](https://arxiv.org/abs/2609.02371) (v1, 2 Sep 2026, cs.*; paper licence CC BY 4.0) |
| Links | Paper: https://arxiv.org/abs/2609.02371 · HTML: https://arxiv.org/html/2609.02371v1 · Code/data: **none given** in the paper (no footnote URL, no availability statement, no acknowledgements) |
| License | Not stated (no release) |
| Availability | **NOT RELEASED.** Searched HF datasets API (`AgentErrata`, `errata`, `agentscope`), GitHub repository search (`AgentErrata`: 0 repos) and the web on 2026-10-16 — no public artefact. The paper calls it "the current release of AgentErrata" but gives no location. Note the name clash: the method "AgentScope" is unrelated to the `agentscope-ai` framework on GitHub/HF. |
| On-disk size | 0 (nothing to download). `data/agenterrata/` only holds the 103 KB Who&When case file that the paper's Appendix C analyses (`whoandwhen_handcrafted_2.json`, fetched from https://github.com/ag2ai/Agents_Failure_Attribution/blob/main/Who%26When/Hand-Crafted/2.json). |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/agenterrata/` (case file only) |

## Description (all from the paper)

**Purpose.** AgentErrata is the authors' evaluation set for *joint* fault localisation (which step) and failure attribution (which failure mode), built because Who&When marks the failure step but has no failure-type labels, and because — the authors argue (Appendix C) — Who&When's annotated step is often the *earliest detectable* issue rather than the *decisive* one.

**Construction — injected, taxonomy-guided.**
- Agent frameworks: **OpenManus** (tool-augmented general-purpose workflow), **OWL** (reasoning-centric autonomous agents), **Mini SWE Agent** (software engineering). Benchmarks: **BrowseComp**, **SWE-Bench Lite**, **WebArena**. The paper does not say how many trajectories come from each, nor whether they are single- or multi-agent (AGENTSCOPE claims to handle both; OpenManus/Mini-SWE-Agent are essentially single-agent loops, OWL is a two-agent user/assistant society).
- Only **successfully completed** runs are kept; then "failure-taxonomy-guided fault injection" is applied: an LLM first judges whether a trajectory is suitable for a given failure category; single-step failures are injected by **instrumented replay** at a designated step; failures with cross-step semantic/textual dependencies get additional post-processing to align the trajectory text. Every injected failure is a **decisive error** (it makes the task fail).
- **All injected trajectories are manually verified**; invalid/unreasonable ones discarded. No number of annotators, no agreement statistic, no annotation time is reported.
- Size: **303 trajectories**. Steps/length statistics: not reported (only a runtime illustration mentions traces of 4 steps/7 calls up to 120 steps/242 calls, drawn from AgentErrata + Who&When).

**Labels.** Per trajectory: the injected (decisive) failing step, and its failure mode (one of 10) / category (one of 3). Whether an agent/role label exists is not stated.

**Taxonomy (AGENTSCOPE, Table 1): 10 modes in 3 categories**, with AgentErrata shares (Fig. 7 / Appendix B):

| Category | Mode | Share | One-line definition |
|---|---|---|---|
| Reasoning (36.0%) | WC Wrong Context | 8.3% | uses irrelevant/invalid/misleading context |
| | IU Instruction Unfollowing | 9.9% | output departs from given instructions/specs |
| | IC Insufficient Context | 9.6% | needed information missing from the input |
| | CM Context Miss | 5.3% | overlooks relevant earlier history |
| Control-flow (31.0%) | TM Termination Miss | 9.6% | keeps acting after the task is complete |
| | PT Premature Termination | 12.5% | stops before the task is finished |
| | SL Step Loop | 8.9% | repeats earlier steps without justification |
| Action (36.0%) | AM Action Mismatch | 13.2% | action contradicts the preceding reasoning |
| | II Invocation Issue | 7.9% | tool/API called incorrectly |
| | EF Execution Failure | 14.9% | tool/API/action fails at runtime |

(The category percentages in Fig. 6 sum to 103% and the four Reasoning modes sum to 33.1%, not 36.0% — an inconsistency in the paper. The authors describe the distribution as "roughly uniform" with biases introduced by the LLM suitability check.)

**Task formulation & metrics.** Fault localisation: step-level accuracy SLA and tolerance variants SLAT (T±0, T±1, T±3). Attribution: classification accuracy CA (predicted failure mode = ground truth). Reported both "w/ solution" and "w/o solution" (i.e. with/without the reference answer given to the diagnoser).

**Baselines on AgentErrata (paper Tables 2–4, %):**

| Backbone | Method | SLA T±0 / ±1 / ±3 (w/ sol.) | SLA T±0 / ±1 / ±3 (w/o sol.) | CA (w/o sol.) |
|---|---|---|---|---|
| GPT-4o | Who&When All-at-once | 2.14 / 6.05 / 21.00 | 2.09 / 4.18 / 23.69 | 20.63 (LLM-as-judge) |
| GPT-4o | Who&When Step-by-step | 10.56 / 14.52 / 25.74 | 8.91 / 13.20 / 25.74 | — |
| GPT-4o | AgentScope | 28.38 / 34.98 / 48.51 | 30.03 / 35.64 / 49.83 | 43.56 |
| GPT-5.1 | Who&When All-at-once | 2.64 / 5.61 / 18.81 | 3.30 / 4.62 / 18.81 | 18.15 (LLM-as-judge) |
| GPT-5.1 | Who&When Step-by-step | 1.65 / 4.62 / 12.21 | 1.32 / 4.29 / 13.20 | — |
| GPT-5.1 | AgentScope | 29.70 / 34.65 / 50.50 | 31.35 / 36.63 / 54.13 | 45.87 |
| DeepSeek-V3.2 | All-at-once / Step-by-step / AgentScope (SLA w/o sol.) | 0.66 / 17.82 / 34.98 | — | AgentScope CA 45.21 |

## Schema

Not available (no release). The paper's internal representation is a **ReAG** (Reasoning-Action Graph): a DAG whose vertices are ⟨id, role, content, ISR⟩ with ISR = {Intent & Context, Reasoning & Action, Signal & Validation}; node types: reasoning, action (tool call/output), user input, output, claim, tool response; edges = control/data dependencies. Expected released fields (by analogy with Who&When, which the paper benchmarks alongside): trajectory steps with role/content, `mistake_step`, failure-mode label.

## Statistics

Nothing could be computed. Paper-reported numbers only (`agenterrata_stats.json`):

| Statistic | Value (paper) |
|---|---|
| Trajectories | 303, all failed (one injected decisive error each) |
| Frameworks | OpenManus, OWL, Mini SWE Agent (per-framework counts not given) |
| Benchmarks | BrowseComp, SWE-Bench Lite, WebArena (counts not given) |
| Category distribution | Reasoning 36.0% · Control-flow 31.0% · Action 36.0% |
| Mode distribution | IC 9.6 · WC 8.3 · IU 9.9 · CM 5.3 · TM 9.6 · PT 12.5 · SL 8.9 · AM 13.2 · II 7.9 · EF 14.9 (%); ≈ 29 / 25 / 30 / 16 / 29 / 38 / 27 / 40 / 24 / 45 trajectories if scaled to 303 |
| Steps / agents per trajectory | not reported |
| Error position | not reported |
| Faulty agent distribution | not reported |
| Annotation | LLM suitability check + injection, then manual verification (no IAA) |

## Example trajectory (from the paper — not an AgentErrata record)

The paper shows **no AgentErrata trajectory**. Its only worked example (Appendix C) is a **Who&When Hand-Crafted** trace (Magentic-One on a GAIA-style question; 86 steps, Orchestrator + WebSurfer), used to argue that the human-annotated step 4 is the first detectable issue while the decisive failure is the later stagnation loop. The full file was fetched and stored as `agenterrata_example.json` (raw) and `agenterrata_example_norm.json` (`from_paper: true`). Because it is long (86 steps), only the task, the annotated step, and the steps the paper discusses are shown here; the normalised file has all steps.

- **Task:** "What is the worst rated series (according to Rotten Tomatoes) with more than 1 season that Ted Danson has starred in and is available on Amazon Prime Video (US)?" — ground truth `CSI: Cyber`.
- **Agents:** `human` (step 0), `Orchestrator (thought)`, `Orchestrator (-> WebSurfer)`, `WebSurfer`.
- **Step 3 — Orchestrator (-> WebSurfer):** "Please search for a list of series that Ted Danson has starred in, and confirm which of those series have more than one season…"
- **Step 4 — WebSurfer ⟵ ANNOTATED ERROR (Who&When label):** "I typed 'Ted Danson TV series list' into '0 characters out of 2000'. Here is a screenshot of [Ted Danson TV series list – Search]…" (only a search-results page; nothing extracted). Who&When reason: "The information obtained by WebSurfer is neither reliable nor satisfies the requirements of the Orchestrator."
- **Steps 5–10 — Orchestrator:** ledger updates ("request not yet satisfied…"), re-issues the same instruction; "Next speaker WebSurfer".
- **Step 11 — WebSurfer:** "I clicked 'Credits'. Here is a screenshot of [Ted Danson List of Movies and TV Shows – TV Guide]…"
- **Step 15 — WebSurfer:** "I clicked 'Credits'…" (identical viewport) → **stagnation loop** (`is_in_loop: true` per the paper); steps 19–85 continue the scroll/click loop through TV Guide and IMDb with two "Stalled… Replanning" events at steps 37 and 64.
- **Step 85 — WebSurfer (last):** another scroll; the run then ends ("FINAL ANSWER: CSI Cyber" appears in the tail of the final message, followed by the content-filter error described in the paper).
- **Paper's reading:** the annotated step 4 is an intermediate information-gap, the later loop (SL) and the execution failure (EF) are what actually determine the outcome.

## Notes for the report

- **Unavailable**: no data, no code, no licence; everything above is from arXiv 2609.02371v1. Treat all numbers as paper-reported. If it is released later, expect ~303 JSON trajectories with step index + one of 10 mode labels.
- Closest relatives: Who&When (same step-level formulation, paper benchmarks on both; 184 trajectories, no mode labels), CORRECT-Error (injected decisive errors, no mode labels), MAST (mode labels but no step), TRAIL (span + category labels, natural errors). AgentErrata is the only one of the four that combines **injected decisive step** + **failure-mode label** + **manual verification**, and the only one whose frameworks are mostly *single-agent* tool loops (OpenManus, Mini SWE Agent) plus OWL.
- Taxonomy overlap with MAST: SL ≈ FM-1.3 step repetition, PT ≈ FM-3.1 premature termination, TM ≈ FM-1.5 unaware of termination, AM ≈ FM-2.6 reasoning-action mismatch, IU ≈ FM-1.1 disobey task specification; the Action category (II, EF) corresponds to TRAIL's System-Execution errors.
- Reported inconsistencies: category percentages sum to 103%; the Reasoning modes sum to 33.1% vs. 36.0% stated.
- Appendix C's point (annotated step = earliest vs. decisive) is a useful caveat for *all* human-labelled step datasets; note that in the cited Who&When file the trace actually ends with "FINAL ANSWER: CSI Cyber", which matches the ground truth, yet it is labelled a failure (`is_corrected: false`) — an example of label ambiguity in Who&When itself.
