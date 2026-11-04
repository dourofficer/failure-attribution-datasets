# Why step-level failure attribution is hard: hypotheses from the data

Draft v1, 2026-11-01. Synthesis of the per-dataset inspections (`findings/datasets/<slug>.md`), the group syntheses
(`findings/groups/g{1..4}_*.md`), the literature note (`lit/known_phenomena.md`, phenomena P1–P8) and the Qwen3.8-27B
baselines and probes (`results/<slug>/`). Record ids are given so every claim can be re-checked. Items marked PENDING
depend on runs that had not finished when this draft was written (see §8).

## 0. What was done

- 19 datasets loaded into one schema (`loaders/`, 34,828 records, `loaders/STATUS.md`); 18 close-read by four group
  agents (≥8–20 trajectories each, 400+ in total), with text-free statistics designed per dataset (`inspect/`).
- Two LLM instruments on a local Qwen3.8-27B (thinking on): (i) **all-at-once judge** (`baseline/all_at_once.py`: task,
  optional ground truth, whole trajectory → decisive agent/step; `inventory` variant lists every mistake first);
  (ii) **prefix monitor** (`inspect/prefix_probe.py`: steps 0..k only, no outcome, "is the latest step a mistake?").
- Literature: SOAP, EMFA, Shen 2026, trajectory-judge, False Success, DRIFT, Huang/Jamshidi cascades, ProcessBench,
  position-bias work (`lit/known_phenomena.md`), on top of the existing `notes/lit_*`.

## 1. The baseline picture

All-at-once judge (Qwen3.8-27B, ground truth given where released; `inspect/summarize_baselines.py`):

| dataset | n | agent% | exact% | ±3% | in-set% | misses later / all | med steps |
|---|---|---|---|---|---|---|---|
| Who&When (all 184) | 184 | 63 | 43 (HC 31 / AG 48) | 68 | 43 | 41/94 | 10 |
| MP-Bench (vs earliest majority) | 80 | 70 | 45 | 60 | 74 (any flagged) | 24/43 | 10 |
| AgentRx (vs root cause) | 73 | 68 | 29 (τ 38 / M1 23) | 60 | 40 (any failure event) | 21/52 | 33 |
| SymFail | 60 | 78 | 25 | 75 | 25 | 22/45 | 13 |
| TraceElephant | 90 | 72 | 33 | 58 | 33 | 22/60 | 21 |
| TRAIL (vs earliest HIGH span) | 40 | 85 | 28 | 42 | 40 (any error span) | 16/29 | 18 |
| TrajErrBench | 80 | 95 | 44 | 58 | 44 | 23/44 | 29 |
| LongRCA (mini sample) | 60 | 48 | 20 (TP 13 / WA 45) | 28 | 20 | **30/48** | 142 |
| AgentErrorBench | 60 | 100 (single agent) | 28 | 47 | 28 | 16/43 | 60 |
| AgentHallu (hallucinated) | 80 | 94 | 69 (BFCL 86) | 96 | 69 | 20/25 | 6 |
| HORIZON web (judge labels) | 60 | 100 | 53 | 77 | 53 | 12/28 | 18 |
| TracerTraj | 60 | 87 | 45 | 75 | 45 | 18/33 | 10 |
| CORRECT-Error (no gt) | 80 | 75 | 75 | 91 | 75 | 14/20 | 10 |
| Who&When Pro text | 100 | 45 | **75** | 94 | 75 | 11/25 | 4 |
| Who&When Pro, last step masked | 100 | 36 | **30** | 93 | 30 | 13/70 | 4 |
| Aegis (agent only meaningful) | 60 | 30 | – | – | – | – | 10 |
| SearchAuditBench (no gt, no web) | 40 | 98 (one role) | 40 (span 48) | 45 | 48 | 9/23 | 36 msgs |
| MemTrace (op slices ≤110k tokens) | 30 | – (op type) | 30 | 40 | 30 | 11/18 | 482 ops |

Reading the table: exact accuracy tracks the *label convention's* locality, not the difficulty of the task. The three
highest natural scores (AgentHallu 69, HORIZON 53, Who&When AG 48) are datasets whose label is a category landmark, a
judge's own symptom step, or a single commission in a ≤10-step log; the lowest (LongRCA 20, SymFail 25, TRAIL 28,
AgentErrorBench 28, AgentRx 29) are exhaustion runs, structural labels and loop-entry labels (X2, X7).

Prefix monitor (`inspect/summarize_probes.py`; no outcome, no ground truth):

| dataset | records | gold flagged% | earliest flag = gold% | flag% before gold | flag% after gold |
|---|---|---|---|---|---|
| Who&When | 20 | 80 | 35 | 27 | 70 |
| TraceElephant | 12 | 58 | 25 | 23 | 57 |
| TrajErrBench τ² | 20 | 60 | 40 | 17 | 37 |
| AgentErrorBench | 20 | 40 | 25 | 8 | 56 |
| AgentHallu | 20 | 45 | 20 | 12 | 35 |
| HORIZON (judge labels) | 20 | 85 | 35 | 24 | 75 |
| TRAIL | 12 | 33 | 17 | 17 | 54 |
| SearchAuditBench | 12 | 67 | 42 | 16 | 38 |
| LongRCA | 10 | 60 | 40 | 12 | 26 |
| **Who&When Pro (injected)** | 20 | **100** | **85** | **7** | 58 |

Three observations that organise everything below:

1. **The whole-trajectory judge is not late-biased, except on the longest traces.** On every natural dataset with
   median length ≤60 steps the misses split roughly evenly before and after the gold (Who&When 41 later / 53 earlier;
   TraceElephant 22 / 38; TrajErrBench 23 / 21; TRAIL 16 / 13; AgentRx 21 / 31; AgentErrorBench 16 / 27; HORIZON
   12 / 16). Literature hypothesis 1 ("≥60% of misses after gold") is refuted for this instrument on those sets. The one
   exception is LongRCA (median 142 steps): 30 of 48 misses are later, median |offset| 28 steps — late bias appears
   when the trace is long enough that the judge can no longer hold the early steps (P5), not as a general property.
2. **The prefix monitor is late-biased.** Steps after the gold are flagged at 2–7× the rate of steps before it on
   every natural dataset (e.g. Who&When 70% vs 27%, AgentErrorBench 56% vs 8%, HORIZON 75% vs 24%), and the earliest
   flag coincides with the gold in only 17–42%. SOAP's "downstream consequences are more conspicuous" (P1) is a
   property of per-step / online scorers, not of holistic judges.
3. **Injected data is a different task.** On Who&When Pro the injected step is locally detectable in 100% of records
   and is the earliest flag in 85%, with 7% false flags on the replayed prefix; and the judge's 75% exact collapses to
   30% when the last step is masked (48% of labels are the last agent step). Natural gold steps are locally flagged in
   33–80% and are the earliest flag in ≤42%.

## 2. Cross-dataset phenomena

Each phenomenon names the datasets where it was observed and the evidence (file § or record ids).

### X1. The post-error "symptom field" is diffuse, not a peak
After the labelled step, trajectories fill with near-duplicate actions, retries, stalls and verifier chatter, but the
density is flat rather than peaked, so there is nothing to back-propagate *from*.
- TraceElephant: near-duplicate steps 0% before vs 39% after the label (Captain), 4.6% vs 31% (SWE-Agent); Magentic
  ledger stall flags fire after the label in 30/59 runs (median +4.5) and before it in 24 (median −13) (g2 R2).
- AgentErrorBench: action-repeat fraction 0.10→0.38 (ALFWorld), 0.30→0.64 (WebShop), 0.01→0.58 (GAIA) across the label
  (H2); the label often sits on the 2nd–4th identical query (`GPT-4o_001` turn 29/30).
- LongRCA: tool errors, FAIL verdicts, `passed:false` and "problem words" occur at the same per-step rate before and
  after the root (AUROC 0.50–0.54 in every source); the first judge FAIL is >100 steps after the root and about a
  different bug (g2 R2).
- AgentRx Magentic-One: annotated-failure density 0.041/step before the root vs 0.145 after; MP-Bench: 3-vote steps have
  median relative position 0.82 and 24% are the FINAL ANSWER step (g1 G1-B).
- Who&When HC: first ledger loop flag +4.5, first repeated WebSurfer action +8, first stall +22, first paraphrased
  instruction +4 steps after the label (`results/who_and_when/signals.txt`).

### X2. The labelled step is a convention, and the conventions diverge by 7–70 steps on the runs that matter
- Same logs, three teams: Who&When vs AgentRx exact 16/44 (36%), ±3 57%, gaps up to 74 steps; Who&When's step is
  unflagged by all three MP-Bench annotators in 26/57 HC logs; on short single-commission runs they agree (AG step has
  ≥2 MP-Bench votes in 116/120; τ-retail root = only failure in 22/29) (g1 G1-A).
- 13/58 Who&When HC runs and 69 SymFail C2 cases end by budget exhaustion; AgentRx roots on those runs are "first
  search" followed by 7–24 adherence repeats; there is no step whose correction would have succeeded.
- TRAIL primary (earliest HIGH) ≠ earliest span in 58/144 (median 5 spans). TrajErrBench: gold is the message that
  *proposes* the wrong action; the tool call that executes it after user consent comes +2 (modal) / +4 steps later
  (H-TEB-1, 318/400 golds are proposal messages). AgentHallu Retrieval: gold is the step whose *observation* carried the
  wrong fact, one hop before the agent asserts it (H-AH2). HORIZON: judge labels are a mixture of "first deviation"
  (27%) and "last chance" (Memory-Limitation at the step where the answer was visible and dropped) (horizon H2).
- The conventions sit at different points of one chain, proposal → commitment → first symptom → claim (g3 R1):
  TrajErrBench τ² labels the proposal (79.5%), the DB write follows at +2/+4 and the judge's modal miss is exactly +2;
  AgentHallu labels the category landmark (fetch step, first `ask_human`, step 0); AgentErrorBench labels the entry into
  the stagnation phase (later than the first malformed action in 51/71 ALFWorld runs); Failure-as-a-Process t_err
  collapses onto t_lock in long runs; HORIZON's judge is "first deviation" in 31% and "at/after the first anomaly" in 53%.
- Magentic-One emits ledger → instruction → next-speaker triples with the same text; Who&When labels the instruction,
  MP-Bench the ledger, AgentRx the "request satisfied" ledger after it; SymFail duplicates every LLM call into two
  nodes and labels one copy in 357/536 cases (g1 G1-E). ±1 tolerance is a necessity on these logs.

### X3. Omission → commission pairs: the evidence gap and the fabrication are both "the" error
- AG/3 (pip timeout → assumed numbers), AG/10 (manual-lookup requests → fabricated census figures), HC/12 (chart never
  loaded → list from memory), AgentRx 5f982798 (PDF not rendered → invented arXiv id); MP-Bench majority is strictly
  earlier than Who&When in 28/120 AG logs, always on the omission step (g1 G1-C).
- AgentRx resolves the pair by type: WebSurfer omissions are "recovered" (25/26 pre-root events), orchestrator
  acceptance/misinterpretation is "root" (22/73).
- AgentHallu: in 84% of hallucinated runs the ground-truth string never appears in any step; tool errors occur at the
  same rate in clean runs (33.6% vs 40.4%) — the signal is claim provenance, not trouble (H-AH3).
- TraceElephant reason texts: 34% omission + 11% outcome-only; LongRCA VitaBench 70% "ignored a request"; MemTrace:
  20/160 faulty ops have no dependency path to the output (g2 R8).

### X4. The actor on the record is not the actor who decided
- TraceElephant: 30/90 Magentic-One gold steps are orchestrator ledger calls recorded under the specialist's name, and
  the human `mistake_agent` follows the recorded name in 218/219 runs; SWE-Agent "agents" are tool names, mismatching
  the tool called in 225/1,551 calls (g2 R1).
- LongRCA: one environmental condition (NYC-named listings in 605/685 TravelPlanner runs; logged-out sessions in 52/76
  Reddit runs) is blamed on six / three different roles depending on who *reacted*; 55 labels name `Computer_terminal`.
- TrajErrBench: the simulated user ends the dialogue mid-confirmation in 29 runs; the agent is blamed in 14 (H-TEB-5).
  AgentHallu Human-Interaction blames the `ask_human` step (56/73 are the first tool call) although the adoption step is
  where the agent could have resisted (H-AH4).
- Agent-level accuracy therefore partly measures agreement with an instrumentation convention (also g1 G1-E, g4 H5).

### X5. Labels are written with information the attributor never sees
- LongRCA: 146 rationales quote the evaluator verdict and "work backwards"; 22/170 SWE/TB2 rationales cite hidden tests
  or the gold patch; 49% of rationales name a role absent from the trace (g2 R4).
- TRAIL: the GAIA `true_answer` is in step 2 of 117/117 traces (every annotator and judge is outcome-informed);
  HIGH-bearing traces are 88% of wrong vs 68% of correct runs.
- TrajErrBench: pre-annotators saw the failure diagnostics; 65.5% of τ² failures have no transcript symptom at all
  (H-TEB-2), and SWE-Pro (7 edits per run, passing self-tests) under-determines the gold (κ 0.67; H-TEB-4).
- AgentErrorBench: exploration-order labels (`Qwen3-8B_006/010/021/023/026`) are the turn where the search order was
  wasteful *given where the object actually was* (H4) — hindsight by construction.
- Consequence: without the failure description the judge invents one — 7/14 LongRCA TravelPlanner predictions blame
  the completion-token protocol (0 gold labels do); TRAIL judge invents a failure in 9/40 correct-ending runs; the same
  Who&When log rendered with and without ground truth gets different steps (HC/30: step 8 vs step 66), because outcome
  knowledge switches the judge's heuristic from "where did the wrong value first appear" to "where did the plan drift".

### X6. Successes contain the same errors ("same signal, different fate")
- Failure-as-a-Process: 71% of PASS runs have ≥1 error event, 2.3 per run, at the same relative position as FAIL
  t_err (0.28 vs 0.31); observable events before lock-in in FAIL runs are drawn from the same distribution (H-FaP-1).
- TRAIL: 34/117 GAIA runs end correctly, 31 carry errors, 23 carry a HIGH; formatting/instruction/orchestration errors
  are outcome-neutral (P(correct) 0.28–0.29 vs base 0.29) while retrieval (0.13) and tool-hallucination (0.17) cascade.
- AgentHallu clean runs: tool errors at the same rate as hallucinated ones; AgentRx recovered WebSurfer failures carry no
  error string in 0/24 and only 6/24 are followed by a ledger flag — recovery is silent, visible only as a paraphrased
  re-ask (g1 G1-D).
- HORIZON: trajectory-level separation of pass/fail (AUROC 0.87–0.91 on n_steps) comes from successes being short and
  failures early-stopped, not from dynamics (horizon H5).

### X7. Structural and positional priors explain much of the published accuracy
- Last agent step = label in 48% Who&When Pro (MathChat 79%), 50% CORRECT-Error, 48% TracerTraj-diagnosed; the judge's
  WWP exact drops 75→30 with the last step masked (§1).
- CORRECT-Error: a Planner→Planner adjacency starts at the labelled step; rule "first Planner→Planner adjacency else last
  step" = 74.0% exact with no reading (paper's LLM judges 6–63%) (g4).
- LongRCA SWE-Pro: first `DiagnostAgent (-> ActionAgent)` delegation = 45% exact (paper's best 24%); TRAIL GAIA first
  CodeAgent action span = 40% (judge 31%); TraceElephant SWE first source edit = 41%; MemTrace last query-bearing
  retrieval op ≈ 70/140 (g2 R7). Failure-as-a-Process: first write hits t_err in 41% (H-FaP-2).
- AgentHallu: oracle-category rules (Planning→step 0 96%, Human-Interaction→first `ask_human` 89%, Retrieval→fetch
  step) reach 55.8% exact vs 41.1% for the best published LLM (H-AH1). SymFail: 70% of labels are predictable from
  (framework template, tool status) (g1 G1-E/H-S1).
- HORIZON OS: 75.5% of GPT failures are example-question drift two turns from the end, 38% of Claude failures are
  finish-without-answer; a regex on the terminal action should reach precision >0.95 (horizon H1).

### X8. Injected and natural errors differ in kind, not degree
- Injected steps contradict their own prefix (plan, previous observation, task): WWP 7/13 read, CE rewrites keep the
  evidence recap and change the conclusion, TracerTraj shell injections rewrite the observation in the command, Aegis
  corruptions change the numbers; prefix monitor flags them in 100% with 7% false flags (§1).
- Natural labelled steps are instead *loud at the step* in the sense of symptoms: Who&When HC labels contain a tool
  error in 12% and a self-correction phrase in 22% (WWP 2.8% / 3.5%), i.e. the human label often sits on the first
  visible symptom (g4 §2a).
- Continuations are loyal to the injection (stop in 48–50%; rationalise — MathChat 0055 re-derives the wrong number with
  impossible arithmetic); post-label symptom rates in WWP (tool errors 4.7%, self-corrections 7.4%) stay below Who&When's
  *pre*-label rates (10% / 16%); residual symptoms are framework loops unrelated to the injection (g4 §2c).
- LLM-authored corruptions have an authorial voice: Aegis turns announce the mode ("calculated incorrectly", "again for
  emphasis", "Incorrect Answer: (B)"), a regex attributes the agent at 91% in Debate (prior 70%); WWP injected turn is the
  length outlier of its agent (argmax |z| 50–92% vs 23–33% chance); TracerTraj leaks `_attacked_solution.py` (54% of
  coding), `| sed` (18% of shell injections), refusals (12% of math) (g4 §2b).
- Counterfactual-with-ground-truth diagnosis (TracerTraj "diagnosed") converges on the final answer (42%) or a tool
  outage (`crawl4ai not installed`, ≈29%) (g4 H4). Mode labels are injector instructions, not descriptions (WWP 3/13,
  Aegis 8/10 mismatches).

### X9. Environment and harness failures are labelled on agents; no dataset has a "no attributable step" class
- SymFail: 450/536 runs never reached a usable page (`__SHOPPING__` placeholder); the label goes to the action that
  issued the doomed call. Who&When HC/48 (Azure content filter), AG/3 (install timeout), 37 missing WebSurfer turns;
  AgentRx "Guardrails Triggered" 9/44 roots. LongRCA: ≥60% of TravelPlanner runs sit on a simulator condition;
  ≥6 VitaBench rationales say the agent was not at fault. AgentErrorBench: 8 Qwen ALFWorld runs explore 30 distinct
  locations with 0 invalid actions and run out of budget; ~5 GAIA runs are infeasible with the given tools (H3).
  HORIZON: 594/639 Catastrophic-Forgetting labels are prompt-construction leakage (example question drift) (H3).

### X10. Verification theatre and the final write are the dominant late labels
- LongRCA: 97% of SWE-Pro runs end with a JudgeAgent PASS after the root; 217/320 TravelPlanner runs with
  `passed:false` still terminate as complete; 140 roots in the last 6 steps. TRAIL: 46/117 GAIA primaries are the
  manager's final call. SearchAuditBench: critical = final answer in 17%. MP-Bench: 24% of unanimous flags are FINAL
  ANSWER; `is_request_satisfied=true` ledgers are voted 16/18; AgentRx root = orchestrator acceptance 22/73.
  Failure-as-a-Process: verification after lock-in in 55% of failures, final step is a claim in 70% of FAIL *and* 71% of
  PASS — the end of the run is uninformative (H-FaP-4).

### X12. Terminal and harness artefacts decide a large share of "natural" single-agent failures
- HORIZON: 75.5% of GPT OS failures answer the in-context example question (`/etc`; 93% of the judge's "Catastrophic
  Forgetting" labels are this mechanism), 38% of Claude OS failures end with `finish` instead of `answer`, 89% of web
  failures are early stops (parse ×3 or max steps) (g3 R4). AgentErrorBench: 33% of GPT-4o and 46% of Llama ALFWorld
  turns are quoted/prose-wrapped actions the environment rejects, and 24/25 runs with ≥10 malformed actions carry a
  *cognitive* label. TrajErrBench: 25 runs end in `transfer_to_human_agents`, 29 are ended by the simulated user.
  AgentHallu BFCL: silent `None` responses in 8–22% of gold steps. A deterministic artefact checker on the last two turns
  and on action syntax would remove a third to three quarters of these runs from the step-attribution problem.

### X11. Silent failures need an oracle the trajectory does not contain
- TrajErrBench τ²: 65.5% of failures have no transcript symptom; policy violations (act.*, obs.*, WrongOrder) are
  decidable from the step-0 policy plus tool outputs, candidate-selection errors (reason.WrongChoice) need the hidden
  goal (H-TEB-2/3). AgentHallu BFCL: the decisive call leaves hidden state; gold response visibly errors in only 19–56%
  (H-AH5). Failure-as-a-Process: 28% silent failures; awareness is observability (first awareness ≥ t_obs in 413/466),
  so verbalised doubt is a lagging symptom (H-FaP-3).
- Giving the judge the hidden oracle does not automatically help: with the simulated user's goal (leaked in the zh edition
  of TrajErrBench, see §4) Qwen changes 16/50 predictions but accuracy stays 22/50; with the ground-truth answer on
  Who&When the published step accuracy moves by −1 to +1.8 pp. Outcome knowledge changes *which* step is blamed more
  than *how often* it is right (g3 R6, lit P3).

## 3. Ranked hypotheses

Each: statement → evidence → how to test (cheap now / expensive later) → what a targeted method would do.

**H1. Late bias lives in per-step scoring, not in holistic judgement; the fix for monitors is dependency-aware
back-propagation, the fix for judges is convention matching.**
Evidence: §1 observations 1–2 (judge misses split evenly; monitor flags 2–7× more after the gold); X1 (symptom field is
diffuse). Test (cheap): signed-offset distributions per instrument on every dataset (done for two instruments; add OAT-
and SOAP-style scorers on the same embeddings); (expensive): SOAP/EMFA rescoring applied to the prefix-monitor curve,
expected to halve its median offset, and applied to the judge, expected to do nothing. Method: use the monitor only to
propose a *region* (first flag onset) and the judge to pick the step inside it under an explicit convention.

**H2. Attribute to the first decision that proceeds despite a condition (the acceptance step), not to the condition
and not to the actor on the record.**
Evidence: X4 (record owner ≠ decider), AgentRx root = orchestrator acceptance 22/73 and `is_request_satisfied` ledgers
voted 89% (g1 H-A2), TrajErrBench proposal-vs-execution +2, AgentHallu fetch-vs-adopt +1. Test (cheap): claim-vs-evidence
check on every orchestrator ledger in the 102 Magentic logs (one call each), predicted ≥70% hit on roots; re-derive the
actor from the prompt owner in TraceElephant and re-score agent accuracy; (expensive): re-annotate 50 runs under the
"first decision despite condition" rule. Method: candidate set = decision steps that consume an observation; score the
consistency between the claim made and the evidence available.

**H3. Forward-trace required items instead of back-tracing symptoms: the root is the first step where a required item
(gold evidence, plan constraint, candidate entity, task requirement) stops being carried forward.**
Evidence: X3 (omission→commission pairs), AgentHallu 84% "evidence never arrived", MemTrace 20/160 roots with no path to
the output, TraceElephant 19/176 runs where the ground truth is visible before the label and then dropped (g2 H4).
Test (cheap): "last step containing the GT string + 1" rule on the 19 TraceElephant runs; claim-support classifier on
AgentHallu's 693 runs vs the judge's detection AUROC; (expensive): forward tracer on MemTrace's 50 Update/Extraction
cases. Method: provenance tracing of the final claim and of each task constraint; blame the drop, accept the pair.

**H4. Classify the failure regime before attributing; a large minority of runs have no decisive step.**
Evidence: X2 exhaustion runs (22% of Who&When HC, 84% of SymFail, 8+ AgentErrorBench budget runs), X9 environment
failures, X7 terminal-action artefacts (HORIZON 75% of GPT-OS failures), AgentErrorBench WebShop bifurcation ("never
looked" loop regime vs "looked and misjudged" buy regime, H5). Test (cheap): regime classifier from text-free features
(distinct-action fraction, null observations, terminal action, env error at first tool call) and cross-team agreement
measured per regime (expected ≈0–36% on exhaustion vs >60% on single-commission); (expensive): pass^k re-runs with a
larger budget — if the task then succeeds, the run had no decisive step. Method: a "no attributable step / environment /
budget" output class, and per-regime attributors.

**H4b. Run deterministic artefact checkers before any LLM attribution.**
Evidence: X12. Test (cheap): regexes for terminal action (`finish` vs `answer`, example-question drift, `Action: none`
×3, transfer-to-human, user stop) and action syntax (quoted/prose-wrapped actions) scored against the environment
verdict on all 3,332 HORIZON runs and the 100 ALFWorld runs; expected precision >0.95 on GPT-OS and Claude-OS. Method:
artefact class → no step attribution; otherwise proceed to the regime classifier of H4.

**H5. The step is a near-deterministic function of the error category and structural landmarks; predict the category,
then apply a positional rule.**
Evidence: X7 (AgentHallu oracle-category rules 55.8% > best LLM 41.1%; FaP first write 41%; LongRCA first delegation 45%;
CORRECT-Error seam 74%); AgentErrorBench module-dependent positions; TrajErrBench VERIFY.* late / PLAN.* early. Test
(cheap): two-stage prompting (category → step) on AgentHallu, AgentErrorBench, TrajErrBench, scored against step-first;
report every method against the structural prior of its dataset. Method: learn P(step | category, landmarks) and use the
LLM only for the category.

**H6. Every label set is a mixture of conventions (earliest detectable, decisive, first unrecovered, lock-in, last
chance, acceptance); methods should be scored under each, and "late bias" largely disappears once conventions match.**
Evidence: X2; g2 R3 (judge climbs to the first plausible deviation where annotators chose a later act, and picks the last
fabrication where TRAIL chose the first recovered bug); HORIZON mixture (27% first anomaly / 26% after / 31% before).
Test (cheap): derive three conventions from TRAIL (earliest span / earliest HIGH / last fabrication) and AgentRx (first vs
root) and score the judge under each; (expensive): blind re-labelling of 100 TrajErrBench τ² and 100 SearchAuditBench
cases without the LLM draft or diagnostics (expected <70% / <55% reproduction, skewed earlier). Method: output an
earliest-deviation step *and* a last-recoverable step.

**H7. Injected-fault data trains prefix-contradiction detection and last-step priors, not symptom back-tracing; an
attributor trained on it will not transfer to natural failures, and its published accuracy is mostly positional.**
Evidence: X8; §1 observation 3 (100% local detectability, 75→30 under last-step masking); authorial voice cues; SOAP's
reported +8.5 pp on WW-AG vs +0.4 on CE. Test (cheap): seam-stripped CORRECT-Error and last-step-masked WWP evaluation of
any published model; style classifier with content masked, transfer to Who&When (expect chance); (expensive): retrain
AgenTracer-style model on WWP with and without terminal injections and test on Who&When/TraceElephant. Method: use
injected data only for the local-consistency channel; gate it on "does this trajectory have symptoms at all".

**H8. Score transitions, not observations: the error is in the response to a signal that successes also receive.**
Evidence: X6 (FaP same distribution of error events in PASS and FAIL; AgentHallu equal tool-error rates; TRAIL
outcome-neutral categories); AgentErrorBench "Nothing happens" read as world state in 83% of GPT-4o cases (H1);
recovery is a paraphrased re-ask (g1 G1-D). Test (cheap): paraphrase detector vs ledger flags on the 102 Magentic logs;
prefix monitor scored on FaP PASS error events vs FAIL t_err once step text is rejoined (predicted equal flag rates);
(expensive): repair-quality classifier on (obs_t, act_{t+1}) trained with PASS recoveries as negatives. Method: condition
the step score on the preceding observation's error type and on whether the next action changes strategy.

**H9. The attributor is a conditional reader of the outcome; without the failure description it invents one, and with
the wrong one it follows it.**
Evidence: X5 (judge invents failures in 9/40 correct TRAIL runs; TravelPlanner protocol blames 7/14; HC/30 flips between
step 8 and 66 with/without ground truth; TrajErrBench pre-annotators with diagnostics 53–77% vs blind detectors 52%).
Test (cheap): All-at-Once with (a) nothing, (b) the evaluator's failure items, (c) a wrong failure description on
LongRCA TravelPlanner and TRAIL (predict exact rises ≈7→25% with (b) and follows (c)). Method: make the failure
description an explicit input (verifier output, failing test names, unmet constraint) and attribute relative to it;
for silent failures (X11) derive the description by simulating the rule (policy clause, DB state, file system).

**H10. Exact-step accuracy on orchestrated logs is convention noise below ~5 pp; collapse decision triples and report
±1 as primary.**
Evidence: X2 last bullet (ledger/instruction/next-speaker triples; SymFail duplicate nodes 357/536; MP-Bench annotator
duplication on 19/169 manual logs). Test (cheap): recompute all published Who&When-HC numbers with the collapse (expected
+5–10 pp for every method, with rank changes). Method: a decision-unit normaliser before scoring.

**H11. Verifier and claim steps are zero evidence for localisation; treat PASS as absent and FAIL as evidence the root is
elsewhere.** Evidence: X10. Test (cheap): ablate verifier/judge/claim steps from the judge's input on LongRCA SWE-Pro and
TB2 (predict no loss, fewer distractors); TF-IDF on the last message PASS vs FAIL (predict AUROC ≈0.6 on FaP vs 0.83 on
τ²). Method: down-weight verification and completion claims; use their *absence* (claim without verification: PASS
16.3% vs FAIL 28.7% in FaP) as a feature.

**H13. Hindsight labels are unflaggable by any prefix method; measure the share and give the attributor the hidden state
or exclude them.** Evidence: the prefix monitor calls the gold "reasonable" in 12/20 AgentErrorBench, 8/20 TrajErrBench τ²
and 3/20 HORIZON records (g3 R7); AgentErrorBench exploration-order labels (X5); τ² 65.5% symptom-free failures. Test
(cheap): split every result by "gold flagged by the prefix monitor" and by "has transcript symptom"; (expensive): give the
attributor the hidden state (object location, user goal, failing test names) and measure the jump — the residual is the
convention problem of H6. Method: evaluate attributors on locally-wrong steps and globally-suboptimal steps separately.

**H12. The label-free "normal flow" exists only as task-phase structure, not as content.** Evidence: X6; HORIZON H5
(separation from length and early-stop, not dynamics); SymFail templates; FaP first-write prior. Test: fit OAT-style
one-class scorers on HORIZON web and AgentHallu successes and check whether step scores peak at the first divergent step
or at the early-stop tail; compare success-reference and failure-reference scorers on the same embeddings (Spearman on
pre-lock-in vs post-observation steps). Method: model the phase sequence (plan → fetch → write → verify → claim), score
deviations in *phase order and phase skipping*, not in content.

## 4. Annotation issues (stated confidently, with prevalence)

- **Failure-as-a-Process's second annotator is a synthetic jitter of the first (verified on
  `docs/kappa_agreement/dual_annotations.csv`, 1,184 FAIL runs).** B − A on `t_lock` is near-uniform on [−10, +10] (33–83
  runs per value, 58 exact matches); on `t_err` it is −1 / 0 / +1 in 474 / 144 / 558 runs (8 outliers); on `t_obs` uniform on
  [−10, +10] with a spike at 0 (211/852). Column B violates t_err ≤ t_lock in 247 runs and the [1, m] range in 226 (g3). The
  paper's κ 0.94–0.96 therefore measures nothing about annotator agreement; treat FaP labels as single-annotator,
  LLM-drafted.
- **TrajErrBench's zh edition (the one the paper evaluates on) ships the simulated user's hidden goal in
  `task_description`** (verified: e.g. "you want to change the May 21 flight from EWR to a direct flight that day"); the en
  edition carries only the opening user line. Published zh numbers are oracle-assisted. One label sits on a tool message;
  14 user-stop terminations are blamed on the agent.
- **Outcome-informed and hindsight labels**: LongRCA (146/1,140 rationales quote the evaluator; 49% name an absent role),
  TRAIL (gold answer in every trace), TrajErrBench (diagnostics shown to pre-annotators), AgentErrorBench exploration-order
  labels and labels copied from another run (`Qwen3-8B_008`, `GPT-4o_003`; 19/157 reasons reused verbatim; ~50% of ALFWorld
  labels name cognition for a format error), Failure-as-a-Process (one Claude draft), HORIZON (25.4% of category labels
  change between two passes of the same judge; 12 step labels on runs the environment passed; embodied pass/fail flips 26%).
- **Wrong or contradictory labels**: Who&When AG/82 (reason contradicts the log: 17,000 h vs GT 17), HC/2 (ends with the
  correct answer), AG/79 (over-specified correct answer); 20 AG labels at step 0 (team composition, no step); CORRECT-
  Error 43 labels on the user message and 8.4% agent/index off-by-one; TracerTraj 12% of math labels are refusals and
  coding tasks leak `_attacked_solution.py`; Aegis MacNet `is_injected` flags contaminated sink nodes (51% of records),
  not corrupted steps; HORIZON 594/639 "Catastrophic Forgetting" labels are prompt leakage; Who&When Pro modes are
  injector instructions (3/13 read mismatch), Aegis 8/10.
- **Non-independent annotators**: MP-Bench annotators 1 and 3 verbatim identical on 19/169 manual logs (26 logs lose
  their majority after de-duplication); SymFail adjudicator overrides all three annotators in 20 cases; 7 MP-Bench
  majority primaries are `Next speaker` lines.
- **Environment failures labelled as agent errors**: SymFail 450/536; LongRCA TravelPlanner/WebArena simulator
  conditions; Who&When HC/48; AgentErrorBench infeasible GAIA tasks; TracerTraj `crawl4ai` outages.
- **Agent labels follow instrumentation**: TraceElephant 30/90 Magentic golds under the specialist's name; SWE-Agent
  tool-name mismatches 225/1,551; LongRCA 55 `Computer_terminal` labels.
- **Position priors baked in**: last agent step 48–50% in WWP / CE / TT-diagnosed; CE Planner→Planner seam (24% of rows,
  95% exact where present).

## 5. Literature phenomena P1–P8: verdicts on the data

| P | verdict | key numbers |
|---|---|---|
| P1 downstream contamination | holds for per-step monitors and annotator consensus; **does not hold for the holistic judge**; symptoms are diffuse, not peaked; absent in injected data | monitor after/before flag ratios 2–7×; judge misses later/all ≈ 0.4–0.5 everywhere; LongRCA symptom AUROC 0.50–0.54; WWP post-label symptom rate below WW pre-label rate |
| P2 label is a convention | confirmed, with the divergence concentrated on exhaustion / long runs | WW vs ARx 36% exact on shared logs; TRAIL primary ≠ earliest in 58/144; TEB proposal-vs-execution +2 |
| P3 anchoring on outcome / drafts | confirmed on every dataset with rationales; the judge is a conditional reader too | LongRCA 146 evaluator quotes; TRAIL gold in 117/117 traces; HC/30 flip |
| P4 outcome-only judges | confirmed in a new form: the outcome-*blind* judge invents failures | TRAIL 9/40 correct runs blamed; TP protocol blames 7/14; HORIZON judge-Success runs end with `answer()` 86% |
| P5 length degrades localisation, not agent accuracy | confirmed | WW exact 50/32/21% for ≤10/11–30/>30 steps, agent flat 64/63/59; TE 46→20; TRAIL 38.5→7.1 |
| P6 normal-flow premise | refuted as content, weakly supported as phase structure | FaP PASS 71% with errors; TRAIL 31/34 correct runs with errors; HORIZON separation = length; SymFail 70% template |
| P7 absorption by type | confirmed | TRAIL category fatality table; ARx recovered = Adherence 25/26, root = Misinterpretation 22/73; WWP recovered injections kept as failures (2/13; CE loop rows decisive=yes 12%) |
| P8 verification theatre / final write | confirmed everywhere | LongRCA 97% PASS after root; FaP final claim 70% FAIL vs 71% PASS; MPB 24% unanimous FINAL ANSWER flags |

## 5b. Which ML principles model these problems

See `lit/ml_principles/README.md` (synthesis) and the three cluster notes. In short: the definition of the decisive step
is Halpern–Pearl actual causation with a normality selection rule (exact); loops and ±1 tolerance are Chockler–Halpern
responsibility (exact); what a log can certify is a Tian–Pearl bound on the probability of necessity (exact); label
conventions are labelling functions on a monotone chain and should be scored jury-style (exact for evaluation);
annotators and the holistic judge compute a hindsight distribution while the prefix monitor computes the policy-side one
(exact, explains H13); "no decisive step" is a selective-prediction output space with named reject classes (exact);
omission errors need forward slicing / where-provenance, not backward symptom tracing (exact on lineage logs);
"same signal, different fate" is a response-conditional treatment effect and a matched-anchor contrastive design (exact);
injected-data priors are shortcut learning (exact, audit already published for the injected side) and the transfer
failure is task shift, not distribution shift (analogy); silent policy failures and terminal artefacts are runtime
verification (exact), hidden-goal labels are not monitorable (H13). Fourteen no-LLM pilots are listed there.

## 6. Experiment programme implied by the hypotheses

Cheap (days, this infrastructure):
1. Signed-offset and per-regime scoring for every instrument and dataset (H1, H4, H6); publish the structural-prior
   baseline table (H5, H7).
2. Decision-unit collapse and ±1 re-scoring of Who&When HC (H10); de-duplicated MP-Bench consensus (§4).
3. Claim-vs-evidence check on Magentic ledgers; proposal-vs-execution shift on TrajErrBench; fetch-vs-adopt shift on
   AgentHallu (H2); provenance rule on TraceElephant's 19 runs and AgentHallu claim-support classifier (H3).
4. Outcome-conditioning ablation (none / correct / wrong failure description) on LongRCA TravelPlanner and TRAIL (H9);
   verifier-step ablation (H11); last-step masking and seam stripping on injected sets (H7).
5. Two-stage category→step prompting (H5).

Expensive (later):
6. Blind re-labelling under stated conventions (TrajErrBench τ², SearchAuditBench, 13 Who&When HC exhaustion runs) (H6).
7. pass^k re-runs with larger budgets on AgentErrorBench / SymFail to identify no-decisive-step runs (H4).
8. Rejoin Failure-as-a-Process step text; score prefix monitors on PASS error events vs FAIL t_err; repair-quality
   transition classifier (H8).
9. OAT-style vs failure-reference scorers on HORIZON/AgentHallu successes (H12); SOAP/EMFA rescoring of the monitor
   curves (H1).
10. Retrain an injected-data attributor with/without terminal injections and test transfer (H7).

## 7. Caveats

- The judge is one model (Qwen3.8-27B) with one prompt; sample sizes are 40–184 per dataset; prefix probes 10–20
  records each. Directions are consistent across datasets, magnitudes are not final.
- Close readings are by LLM agents (four group agents) with record ids; the strongest claims (annotation errors, convention
  gaps) were checked against the released files, but a human pass over the cited ids is still needed.
- Trajectories were rendered as text; screenshots (TraceElephant, WWP image splits) were not used.

## 8. Pending

- All baselines are complete and summarised in the per-dataset files (§4 or §4b) with reasoning excerpts in
  `results/<slug>/*_analysis.md`. SearchAuditBench exact 40% (CS-Strict; the paper's All-at-Once with Claude Opus 4.8 is
  32.1%, SearchAuditor 39.9%), misses skew *earlier* (14 earlier / 6 later); MemTrace 30% exact on 30 slices, 3 records
  still over the context limit.
- The agents' own readings of the judge's reasoning (≥6 failures / ≥3 successes) exist for Who&When, TraceElephant,
  TRAIL, TrajErrBench, AgentErrorBench, CORRECT-Error and Who&When Pro; for MP-Bench, SymFail, AgentRx, LongRCA, HORIZON
  and AgentHallu only the metric tables and categorised misses were added (§4b), not a read of the reasoning.
