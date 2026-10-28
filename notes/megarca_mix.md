# MegaRCA-Mix

## Identity

| Field | Value |
|---|---|
| Full title | **Root-Cause Attribution Is a Search Problem: Continual Search for Long-Horizon Agent Failures** (introduces the MegaRCA-Mix test set) |
| Authors | Harsh Raj, David Lee, Anas Mahmoud, Renxiong Wang, Razvan-Gabriel Dumitru, Chenguang Wang, Tong Zhao, Yunzhong He, Darvin Yi, Vipul Gupta — Scale AI |
| Venue | arXiv preprint (v1 11 Sep 2026, v2 28 Sep 2026); no venue listed |
| arXiv id | 2609.13463 |
| Paper | https://arxiv.org/abs/2609.13463 · https://huggingface.co/papers/2609.13463 · HTML https://arxiv.org/html/2609.13463v2 |
| Companion taxonomy paper | "Model or Harness? An Interaction-Centric Taxonomy for Localizing Agent Failures", Raj et al., arXiv 2607.28802 (Scale AI) |
| Source trials | Harbor Index (Shi et al. 2026, arXiv 2609.04298; https://hub.harborframework.com/datasets/harbor-index) run with Claude Code under the Harbor framework |
| Code / data links | **None.** No GitHub, HF dataset, project page or "will release" statement in v1/v2 of the paper, on the HF papers page, in GitHub search (`MegaRCA`) or HF dataset search (`MegaRCA`, `rca-mix`) as of 2026-10-16. |
| License | not stated |
| Availability | **NOT RELEASED** (as of 2026-10-16). Nothing downloaded; everything below is from the paper. |
| On-disk size | 0 (directory `data/megarca_mix/` is empty) |
| Local path | `/dataDisk/home/thanhdo/failure-attribution-datasets/data/megarca_mix/` (empty) |

## Description

**Purpose.** MegaRCA-Mix is a small, deliberately hard root-cause-attribution (RCA) test set for *very long* agent executions: 50 failed trials whose logs have a **median of 286 K tokens (1.05 MiB)** and that come with the complete evidence bundle a human debugger would have — raw trajectory, trial configuration, agent-side logs, verifier output and sandbox artifacts. It was built because the four existing RCA benchmarks the paper evaluates on (TRAIL, TELBench, AgentRx, Who&When algorithm-generated subset) have much shorter traces and only a single trajectory file, so a judge never has to *search* for evidence. The paper's method, **Continual Search**, prompts an LLM judge over up to four turns to keep opening unread evidence before committing to a diagnosis.

**How it was built.**
- *Source:* failed trials from **Harbor Index**, a curated meta-benchmark of 82 agentic tasks distilled from 29 benchmarks across seven domains (software engineering, scientific research, mathematics, data analytics, security, …). Table 1 of the paper names GAIA, SWE-Bench, HLE, OpenRCA "+ 15 additional benchmarks" (so 19 benchmarks are represented in the 50 trials; the "29" refers to Harbor Index as a whole).
- *Agent:* **Claude Code** harness with **Opus-4.8** and **GPT-5.5** backbones, run under the Harbor evaluation framework (sandboxed, with verifiers).
- *Failures are natural* (real failed evaluation trials, nothing injected).
- *Annotation:* each trial is **human-annotated with its "first consequential error"** under the interaction-centric taxonomy of Raj et al. (2026): a triple (**edge** between the model and another component, **fault side** ∈ {model, harness, environment, grader}, **failure mode** out of 41) plus a quoted first-divergence citation. Gold labels are stored as one or more *acceptable gold cluster sets* per trial (several taxonomy triples may be acceptable). The paper does not say how many annotators, who they were, or report inter-annotator agreement.
- *Per-benchmark / per-model / per-domain composition* of the 50 trials: not reported. Step counts: not reported (only token/MiB sizes).

**Label types.** Trial-level root-cause triple (edge, fault side, failure mode) + first-divergence citation + evidence quote. This is *component-level* ("which side is at fault") and *mode-level* attribution; there is no agent-role label (Claude Code is single-agent with sub-agents) and the "step" is a cited divergence point rather than an index.

**Error taxonomy** (Raj et al. 2026, 41 modes; the four non-model modes are in bold):
- *model–owner (fault: model):* Over-initiative, Under-initiative, Satisficing, Instruction-Following Failure, Reasoning Failure, Unauthorized Irreversible Action, Sycophancy, Domain Knowledge Deficit, Value Misalignment; *(fault: owner/grader):* **Instruction–Grader Mismatch**.
- *model–grader (model):* Specification Gaming, Evaluation Awareness. *model–third party (model):* Indirect Prompt Injection, Contextual Sycophancy.
- *model–context (model):* State Tracking Failure, Goal Drift, Context Rationale Erosion. *model–memory (model):* Missed Write, State Staleness, Overgeneralization, Memory Rationale Erosion, Pollution, Redundancy, Missed Read, Memory Following Failure.
- *model–tool (model):* Incorrect Tool Selection, Tool Hallucination, Tool Feedback Neglect, Tool Recovery Failure, Malformed Arguments, Suboptimal Arguments; *(fault: tool/harness):* **Mistranslation**.
- *model–model peer / subagent (model):* Delegation Failure, Communication Failure (×2 each).
- *model–external environment:* Recovery Failure (model), **Service Failure** (environment), **Stale State Delivery** (environment). *model–local environment (model):* Observation Failure, Recovery Failure.

**Task formulation and metric.** The judge receives the evidence bundle (through the Claude Agent SDK with file-reading tools) and must output JSON `{trial_id, task_id, edge, fault_side, failure_mode, first_divergence, evidence_quote, rationale, changed_from_turn1/changed_from_prev}` with `edge`/`failure_mode` as exact strings from `taxonomy.py`. Score = per-trial **set-F1** between the predicted taxonomy-cluster set and each acceptable gold set, F1(A,B)=2|A∩B|/(|A|+|B|), taking the max over gold sets, averaged over the 50 trials. (For the other four benchmarks: TRAIL joint accuracy / weighted F1, TELBench first-error accuracy, AgentRx and Who&When step-level accuracy.)

**Baseline numbers (paper Table 2, F1 on MegaRCA-Mix after four judge turns):**

| Judge | Single-turn | Passive Continuation | Continual Search |
|---|---|---|---|
| GPT-5.5 | 0.356 | 0.569 | 0.569 |
| Opus-4.8 | 0.471 | 0.479 | **0.608** |

(The abstract quotes GPT-5.5 0.349 → 0.498, i.e. a different run/version; v2 Table 2 gives the numbers above.) Evidence coverage: both strategies start at 70.5 % of relevant artifacts opened at turn 1; Continual Search reaches 95.2 % (turn 3) and 98.5 % (turn 4) while passive continuation plateaus at 75.6 %. The judge opens the primary trajectory in 38/50 trials by turn 2; config files, console logs and raw session records are only opened in later turns, and these are what fix misdiagnoses.

## Schema

Not observable (unreleased). From the paper, a trial consists of: the raw agent trajectory (Claude Code session), `config.json` / trial configuration, agent-side logs (console), verifier/grader outputs, sandbox artifacts (files produced in the environment), plus the gold annotation = acceptable set(s) of (edge, fault_side, failure_mode) with a first-divergence citation. Judge outputs follow the JSON format listed above.

## Statistics

All from the paper (nothing computable). Machine-readable: `notes/megarca_mix_stats.json` (lists empty).

| Statistic | Value (paper) |
|---|---|
| Trials | 50, all failed (success/failure split: 0 / 50) |
| Median log length | 286 K tokens; 1.05 MiB |
| Steps per trajectory | not reported |
| Position of the labelled error | not reported (labels are first-divergence citations) |
| Category distribution | not reported |
| Fault-side distribution | not reported (taxonomy has 4 sides: model / harness / environment / grader) |
| Source benchmarks | GAIA, SWE-Bench, HLE, OpenRCA + 15 others from Harbor Index (29 benchmarks, 7 domains in Harbor Index overall); per-benchmark counts not given |
| Agent / models | Claude Code with Opus-4.8 and GPT-5.5; per-model counts not given |
| Annotators / agreement | human, numbers and agreement not reported |

## Example trajectory

No MegaRCA-Mix trial is printed in the paper. The closest thing is the worked example of the judge in Appendix A.1 / Figure 10 — a **GAIA2** (adaptability config) trial `scenario_universe_21_5e0gvz`, which is *not* one of the 50 MegaRCA-Mix trials but uses the same label format. Reconstructed from the paper's prose (`from_paper: true`): `notes/megarca_mix_example.json`, normalised `notes/megarca_mix_example_norm.json`.

**Source id:** `scenario_universe_21_5e0gvz (GAIA2 adaptability trial used as the worked example in Appendix A.1 / Figure 10 of arXiv 2609.13463; NOT one of the 50 unreleased MegaRCA-Mix trials)`  
**Task:** Cancel the user's Saturday appointments and schedule a 'Film Production Day' event with a friend. Reschedule based on the friend's reply; if the friend cannot make it and proposes no alternative, cancel the plan.  
**Final output of the system:** Agent finalised after a single short wait returned no reply from the friend, without rescheduling or cancelling as instructed (task failed the GAIA2 verifier).  

Steps (4 total):

- **Step 1 — Claude Code agent (model)**

  > Action: cancel the user's Saturday appointments and send the friend a message proposing the 'Film Production Day' event. (Reconstructed from the paper's prose; the paper does not print the raw turns.)

- **Step 2 — Claude Code agent (model)**

  > Action: set up a trigger gated on a message-count check and issue one short wait (about 180 simulated seconds) for the friend's reply.

- **Step 3 — environment (external)**  ⟵ ANNOTATED ERROR STEP

  > Observation: the wait returns after roughly 3 real seconds with no notifications; the environment's notification/settings state is empty (config.json / console log show empty environment settings).

- **Step 4 — Claude Code agent (model)**

  > Thought/Action: no reply observed, conclude there is nothing further to do and finish the task without rescheduling or cancelling.

**Annotation:**

- Faulty agent/component: `environment (external service)`
- Faulty step: `3`
- Category: `edge=model–external environment; fault_side=environment; failure_mode=Stale State Delivery`
- Reason / root cause: The environment reported a healthy, completed wait but delivered stale/empty state (no notifications), so the agent's belief that the friend had not replied was induced by the environment rather than by the model cutting scope. A trajectory-only reading (judge turn 2) wrongly blamed the model ('Satisficing'); opening config.json and the console log (judge turn 3) revealed the empty environment settings and corrected the attribution.
- single_turn_trajectory_only_diagnosis: {'edge': 'model–owner', 'fault_side': 'model', 'failure_mode': 'Satisficing'}
- final_diagnosis_after_continual_search: {'edge': 'model–external environment', 'fault_side': 'environment', 'failure_mode': 'Stale State Delivery'}
- taxonomy: Interaction-centric taxonomy of Raj et al. 2026 (arXiv 2607.28802): 41 failure modes, each tied to an edge between the model and another component (owner, grader, third party, context, memory, tool, peer/subagent model, local/external envir […] ) and a fault side (model | harness | environment | grader).
- label_format_megarca_mix: gold = set(s) of acceptable taxonomy clusters + first-divergence citation; scored by max-over-gold-sets set-F1 per trial, averaged over 50 trials

## Notes for the report

- **Unreleased.** Treat MegaRCA-Mix as a *described* benchmark only; cite the numbers but do not count it among usable datasets. The paper's own experiments on *released* data use TRAIL, TELBench, AgentRx and Who&When (algorithm-generated), all of which are covered elsewhere in this survey.
- **What is unique on paper.** (i) Longest traces of any RCA set (median 286 K tokens, ≈ 2× LongRCA's long traces); (ii) the judge gets a *multi-file evidence bundle* (trajectory + config + logs + verifier + sandbox), turning attribution into a search problem; (iii) labels use a *component/fault-side* taxonomy (model vs harness vs environment vs grader) instead of agent/step indices, so some root causes are *benchmark-side* (Stale State Delivery, Service Failure, Instruction–Grader Mismatch, Mistranslation) — a category most other datasets lack; (iv) multiple acceptable gold sets with set-F1 scoring instead of single-step exact match.
- **Caveats.** Only 50 trials; annotation protocol and agreement unreported; no per-benchmark composition; the benchmark count in the text (29) and Table 1 (19 named + implied) are inconsistent; abstract and Table 2 give different GPT-5.5 numbers (0.349→0.498 vs 0.356→0.569).
- **Overlaps / lineage.** Built on Harbor Index (Terminal-Bench team's meta-benchmark) and on the Raj et al. taxonomy; AgentRx (Microsoft) and TRAIL are the closest released analogues in spirit (long single-agent traces with a category taxonomy).
