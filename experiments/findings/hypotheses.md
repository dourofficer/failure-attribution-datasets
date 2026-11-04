# Why step-level failure attribution is hard on these datasets: hypotheses and evidence

Deliverable of the inspection (2026-10-31). Raw observations in order of discovery are in `worklog.md`; the code that
produced every number is under `experiments/` (see `../README.md`). Evidence tags: **[ann]** computed from the released
annotations or logs; **[read]** from reading trajectories; **[lit]** from the surveyed literature / report;
**[LLM]** from the local Qwen3.8-27B all-at-once baseline (`baseline/all_at_once.py`, no gold answer, no thinking, 200k context).

Hypothesis ids (H1, H2, ... H13, H3') are the ids used throughout `worklog.md` and are kept for cross-reference;
the order below is by family, not by id. The hypotheses are grouped into three families: (A) the thing being labelled is not a point, (B) the label is a convention
or a hindsight artefact rather than a property of the log, (C) shortcuts and artefacts that make reported accuracies
misleading. Each hypothesis states the claim, its scope, the evidence, what an attributor would have to do differently,
and the deferred experiment that would settle it.


## 0. The baseline in one table

All-at-once attribution with Qwen3.8-27B (no gold, no thinking), scored against each dataset's primary label
(`baseline/summary.py`; "in label set" counts set-valued labels; "earlier/later" = share of predictions before/after
the gold step; published numbers are the papers' own, usually with the gold given, different backbones, not
compute-matched). Rule baselines (first / last / longest / shortest decision step) are in `worklog.md`.

| dataset | n | parsed | agent | exact | ±3 | in label set | earlier | later | published (exact step, %) |
|---|---|---|---|---|---|---|---|---|---|
| agenterrorbench | 199 | 196 | 100.0 | 24.0 | 42.9 | 24.0 | 63.3 | 12.8 | direct 28.0; AgentDebug 45.0 |
| agenthallu | 443 | 439 | 94.5 | 56.9 | 87.0 | 56.9 | 16.9 | 26.2 | GPT-5 32.7; Gemini 41.1 |
| agentrx | 73 | 73 | 63.0 | 30.1 | 53.4 | 46.6 | 39.7 | 30.1 | W&W-style 18.8-22.7; AgentRx 36.4-42.7 |
| correct_error | 300 | 300 | 74.3 | 70.3 | 89.7 | 70.3 | 15.0 | 14.7 | Qwen-7B judge 6-63; CORRECT 17-80 (Acc@1) |
| horizon | 94 | 94 | 100.0 | 39.4 | 80.9 | 39.4 | 51.1 | 9.6 | judge labels, no leaderboard |
| longrca | 200 | 200 | 44.5 | 16.0 | 28.5 | 16.0 | 25.0 | 59.0 | V4-Flash AAO 7.6; RCTA 24.1 |
| mp_bench | 277 | 276 | 53.6 | 38.0 | 59.4 | 83.3 | 22.5 | 35.1 | nDCG task (no exact-step number) |
| searchauditbench | 200 | 197 | 97.0 | 21.8 | 32.0 | 21.8 | 49.2 | 28.9 | AAO 32.1; SearchAuditor 39.9 (CS-strict) |
| symtrace | 536 | 536 | 55.4 | 31.7 | 80.2 | 31.7 | 30.2 | 38.1 | n/a (repair benchmark) |
| traceelephant | 219 | 216 | 56.0 | 35.2 | 65.7 | 35.2 | 28.2 | 36.6 | GPT-4o AAO w/o gold 22.7; dynamic 27.6; w/ gold 33.3 |
| tracertraj | 340 | 340 | 85.0 | 37.6 | 78.8 | 37.6 | 22.9 | 39.4 | AgenTracer-8B 36.2 agentic / 18.9 code / 57.6 math (w/ gold) |
| trail | 124 | 124 | 65.3 | 34.7 | 45.2 | 50.0 | 21.0 | 21.0 | Gemini-2.5-Pro Loc 0.55 (set metric) |
| trajerrbench | 486 | 486 | 93.4 | 42.0 | 57.8 | 42.0 | 25.7 | 32.3 | direct 41.5-52.5 τ² / 10.5-17.4 SWE; TrajDebug 52.8 / 24.4 |
| who_and_when | 184 | 184 | 60.9 | 43.5 | 67.4 | 43.5 | 33.2 | 23.4 | GPT-4o AAO w/ gold 12.5 AG / 5.3 HC; AgenTracer-8B 42.9 / 20.7 |
| who_and_when_pro | 300 | 300 | 92.7 | 74.0 | 95.3 | 74.0 | 11.7 | 14.3 | GPT-5.4 72.3 (text) |

Three readings of the table that the hypotheses below explain:
- A 27B open model without the gold matches or beats most published prompting numbers (Who&When 43.5 vs 12.5/5.3,
  TraceElephant 35.2 vs 22.7, LongRCA 16.0 vs 7.6, SWE-Pro 30.2 vs 17.4, AgentHallu 56.9 vs 32.7, Who&When Pro 74.0 vs
  72.3). The published numbers understate what reading does; the remaining gap to 100 is mostly not a reading gap.
- Where the model is "wrong", the direction and the category of the miss are systematic (H13, H5), the step it chose is
  often one another annotation team flagged (H11), and on the injected sets position alone explains most of the score
  (H10).
- The recovered-error phenomenon is measurable with the same model (H1): it is a reader inconsistency on the
  single-agent and long sets and a consequence disagreement on the multi-agent sets.

---------------------------------------------------------------------------------------------------------------------
## A. The error is a process, not a point

### H1. Recovered early errors are the attributor's main false-positive attractor
**Claim.** Failed runs routinely contain early mistakes that the system later corrects or routes around (a wrong first
guess, a partial page read followed by a better one, a failed tool call retried). They are the most *visible* wrongness
in the log. A reader that scores wrongness instead of consequence picks them; the human label skips them.
**Scope.** Natural long-horizon sets: Who&When HC, TraceElephant, MP-Bench manual, LongRCA, AgentRx, TrajErrBench,
SearchAuditBench, Failure-as-a-Process. Not the injected sets (their prefix is a successful run by construction).
**Evidence.**
- [ann] AgentRx annotates every failure event: 30/44 Magentic-One logs have >1 event; the root is not the earliest in
  17/44. Non-root events are overwhelmingly *Instruction/Plan Adherence* failures of the specialist (192 non-root vs 11
  root; 25 of them before the root), whereas the root is the consumer's *Misinterpretation of Tool Output* (22 root vs 9
  non-root).
- [ann] MP-Bench: in 88/157 manual and 46/120 automatic logs at least one of three annotators flags a step earlier than
  the first majority step (291 such early minority flags in the manual set; median gap 4 steps, p90 37).
- [ann] Failure-as-a-Process: 433/610 PASS runs contain error events (max detour median 3 steps, p90 15); 637/1,184 FAIL
  runs contain recovery *attempts*; 35% of failures are "aware, wrong fix". TRAIL: 20 of 22 correct-ending GAIA traces
  carry error spans, 45 of them HIGH impact.
- [read] SearchAuditBench 277: the agent hallucinates the rank-2 player at message 4, reads the real leaderboard at
  message 7 and corrects itself; the label is at message 8. LongRCA swe_bench_pro__093: "the initial delegation plan in
  step 37 does contain obvious flaws ... these problems were later discovered and fixed" -> label at 399.
- [ann] LLM-tagged rationales: "earlier error recovered" is stated in 4% of LongRCA rationales (8% WebArena) and ~0
  elsewhere; annotators rarely document what they skipped, so the recovered errors are invisible in the labels.
- [LLM] Inventory prompt (every mistake tagged recovered/fatal) joined with the all-at-once prediction: the model
  itself finds a recovered mistake before the gold in 24% (Who&When), 28% (AgentRx), 23% (TraceElephant), 53%
  (LongRCA), 38% (TrajErrBench), 45% (AgentErrorBench), 21% (AgentHallu), 67% (SearchAuditBench) of runs. When its
  all-at-once pick is earlier than the gold, that step is one it tags *recovered* in 26/38 LongRCA, 53/82 TrajErrBench,
  40/62 AgentHallu, 44/96 SearchAuditBench, 21/33 TracerTraj and 42/114 AgentErrorBench cases -- on the single-agent and long sets the trap is real and is an
  inconsistency of the reader (it picks a step it would call recovered if asked) -- but only 14/55 Who&When, 3/25
  AgentRx, 9/49 TraceElephant, 7/51 MP-Bench: on the multi-agent sets the early picks are tagged *fatal*, i.e. a
  disagreement about which early error mattered (H2/H7), not about recovery.
- [LLM] On the 41 LongRCA runs whose human rationale itself documents an earlier corrected error, the all-at-once
  pick is that corrected error in the clearest cases: terminal_bench_2__031 (human: "after correcting the column
  order ... subsequently misjudged the data", gold 160; model blames step 20, the corrected column-order mistake, and
  its own inventory tags step 20 "recovered"); swe_bench_pro__093 (human: plan flaws at 37 "later discovered and fixed",
  gold 399; model blames 50, inventory tags 50/54/66/177/341 recovered); travelplanner__094 (data pollution noticed by
  step 60-65, gold 73 = the step that ignores it; model blames the producer at 23). Of the 14 early picks on these 41
  runs, 8 are steps the model itself calls recovered.
- [LLM] The mirror image in the lock-in regime: on the 80 LongRCA runs whose rationale says later repair attempts
  failed, the model is later than the gold in 62% (exact 27%): the visible failed fixes attract the blame away from
  the decision they tried to repair. Recovered errors pull the reader early; failed repairs pull it late.
- [LLM] The model tags the GOLD step itself as recovered in 7-28% of runs (CORRECT 28%, AgentErrorBench 20%,
  MP-Bench 19%, TrajErrBench 16%, Who&When 15%); reading the Who&When cases, several golds are recovered errors by the
  dataset's own counterfactual definition (HC/1: a misclick on an ad, navigated back four steps later; HC/3: one of
  five identical scrolls, the run reaches the right page 60 steps later and dies on a content-filter error).
- [LLM] Forcing the fate inventory does not raise exact accuracy (lower on 9 of 10 sets, e.g. TrajErrBench 37.7 vs
  42.7, CORRECT 54.2 vs 71.5): tagging fates and judging consequence are different skills, and the inventory's
  "earliest never-recovered" rule pulls the choice away from each dataset's convention.
- [LLM] Outcome-blind inventory on AgentHallu (249 successful / 441 failed runs): in runs that SUCCEEDED the model
  still lists 1.5 mistakes, calls one fatal in 23% and names a decisive step in 90%; p_success AUROC 0.765; blind
  decisive == gold 42% vs 57% with the outcome known. The reader's "fatal" is a wrongness judgement that does not know
  about consequence; a quarter of its attribution accuracy is the outcome label doing the work.
**Implication for method design.** Attribution needs a *consequence* test, not a wrongness test: either rollouts
(Proposal 1), a learned success-probability curve whose *drop without recovery* marks the step (Proposals 2/4), or at
least an explicit recovered/fatal tag per candidate before choosing the decisive one.
**Deferred.** Rollout screen at the recovered steps of AgentRx/MP-Bench minority flags: the effect should be ~0.

### H3'. The natural unit of blame is an episode, not a step; inside the episode the exact index is a convention
**Claim.** Failures are implemented by several consecutive distinct decisions (search -> visit -> commit) or by a block
of near-identical retries. Annotators place the label at an episode boundary (first step, last repeat before a pivot,
the commit) by convention that differs between teams; exact-step metrics then measure the convention.
**Evidence.**
- [ann] SearchAuditBench's own tolerance spans contain >1 assistant decision in 75.5% of cases (2: 430, 3: 323, 4: 146,
  5-6: 40); only 16 of the 939 multi-decision spans are near-duplicate repeats, so the "equally defensible" steps are
  distinct decisions of one line of reasoning; the critical step is the first of its span in 528, the last in 240.
- [ann] Repetition blocks (>=3 near-identical same-agent actions): LongRCA 83% of runs, label inside a block in 256
  (first of block 53, last 16, elsewhere 187); AgentErrorBench 84% of runs, 98.5% of the steps after the label are
  repeats; TrajErrBench 51%; Who&When 22%.
- [read] Who&When HC 3.json: five identical archive scrolls at steps 16/20/24/28/32, label on the fifth, i.e. the last
  before the orchestrator's pivot at 33; nothing in the content distinguishes it from 20/24/28.
- [ann] Annotators avoid labelling a retry: the labelled step is a near-duplicate of the previous same-agent step in
  3.7% (LongRCA) / 12% (TrajErrBench) vs 14% / 16% for a random decision step.
- [lit] Exact-step agreement LongRCA 40% (±5: 50%), TraceElephant α 0.64, MP-Bench 16% three-way; SymFail node κ 0.81
  but category C2 (stalled progress) 0.37.
- [LLM] When the gold sits inside a repeat block and the prediction misses it, the prediction lands in the SAME block
  in 82/131 AgentErrorBench, 33/49 LongRCA and 7/14 AgentRx cases; exact accuracy is far lower on in-block golds
  (TRAIL 12% vs 63%, AgentErrorBench 18% vs 37%). SearchAuditBench: strict 22.3 vs span-tolerant 30.6.
**Implication.** Score and train at episode level (set/span metrics, nDCG against votes) and treat the within-episode
index as a convention parameter ("first", "last before pivot", "commit") declared per dataset.

### H6. The system's own self-monitoring is a salient but lagging and noisy symptom signal
**Claim.** Orchestrator ledgers ("is_in_loop", "no progress", "Stalled... Replanning") are the most legible statements
of failure in the text; they fire before the label in a third of cases and long after it in the rest, so an attributor
anchored on them is off by many steps, and in the "before" cases the human label sits *after* the system already
declared itself stuck.
**Evidence.** [ann] Who&When HC (58 Magentic-One logs): is_in_loop fires in 36, before the label in 14 (down to -65
steps), after in 22 (median +8, max +48); "Stalled... Replanning" fires in 25, after the label in 23 (median +22).
Failure-as-a-Process: forewarning signals before lock-in in 62% of failures, but the prompted prefix monitor has lead
time 0. [lit] OAT fires on failure verbalisation (fa_ideas review).
**Deferred.** Ablate ledger text from the prompt and measure the shift of the baseline's predictions.

---------------------------------------------------------------------------------------------------------------------
## B. The label is a convention or a hindsight artefact

### H2. Producer-blame vs consumer-blame: datasets disagree on who is responsible when bad information is handed over
**Claim.** The same log admits a producer label (the specialist that returned partial/wrong content) and a consumer
label (the orchestrator/planner that accepted it unchecked). Who&When and TraceElephant lean producer; AgentRx ("first
unrecoverable"), MP-Bench majority votes and LongRCA ("if the hand-off instruction contains the error, the instruction is
the root") lean consumer; CORRECT-Error (Planner 74%) and Who&When Pro (orchestrator 78% on Magentic-One) are
consumer-heavy by construction.
**Evidence.**
- [read] AgentRx c7afe008 / 52f7224e: WebSurfer reads 18% / 9% / 42% of the page (events), root = orchestrator "searched
  with incomplete information" 1-2 steps later. Who&When vs AgentRx on 5f982798: step 3 vs step 33.
- [ann] AgentRx vs Who&When on the same 44 logs: same step 16/44, within ±3 25/44, same agent 27/44; the Who&When step is
  not one of AgentRx's failure events at all in 17/44.
- [ann] TraceElephant artefact (verified): in the Magentic-One traces the orchestrator's ledger call is logged under the
  *next speaker's* name; 40 of the 90 labelled steps are such ledger calls and 36 of them carry a specialist's name, so
  the gold "who" is the name of the call, not the role whose decision the rationale describes (assistant_bench_task_10:
  "targeting Release 102 instead of 101" is the orchestrator's instruction, labelled WebSurfer).
- [lit] Agent agreement Who&When vs TraceElephant 18/86 paired tasks.
- [LLM] Consumer-blame bias of the reader against producer labels: LongRCA gold stay_agent (early wrong hotel data)
  4% exact / 4% agent, the model blames the manager or planner later (TravelPlanner later in 68%); CORRECT-Error gold
  WebSurfer 28.8% exact vs Planner 88.4% (model later in 42%, blaming the Planner that accepts the rewritten
  observation); Who&When HC/5: "step 12 yielded no usable text" is in the model's own reason, yet it blames step 16
  where the WebSurfer answered anyway. On TraceElephant's 40 specialist-named ledger labels: step exact 12.5% vs 46.9%
  elsewhere, agent accuracy 42.5% rising to 75% if "Orchestrator" were accepted. Gold Orchestrator rows: agent
  accuracy 11.9% (TraceElephant), 44% (Who&When), 45% (AgentRx).
- [LLM] Anonymising agent names does not lower "who" accuracy (Who&When 61 -> 66, TraceElephant 61 -> 64, MP-Bench
  57 -> 57) and raises it on gold-Orchestrator rows (41 -> 53, 12.5 -> 25, 31 -> 41): the name prior is not what makes
  "who" easy, and the name "Orchestrator" makes the reader reluctant to blame it. The producer/consumer split is a
  content-level convention, not a naming artefact.
**Implication.** "Who" needs a declared rule (relevance-conditioned: blame the consumer when the observation was
sufficient, the producer when it was not); otherwise agent accuracy measures the rule, and role-name priors dominate.

### H4. Labels are written in hindsight from the gold answer or the failing tests
**Claim.** Annotators and LLM pre-annotators know the reference; the labelled step is where the agent's path diverges
from a path that reaches the gold, even when the step was reasonable on the evidence the agent had. Attributors without
the gold cannot reproduce such labels; with it, they reproduce them by answer-matching rather than by reasoning.
**Evidence.**
- [read] SearchAuditBench 277: the visited page lists Giannis as #2 in fouls; the label blames "turning a single
  leaderboard result into a settled binding"; the gold comes from a different rank-2 player.
- [ann] LLM-tagged rationales that rely on the gold / tests: LongRCA SWE-bench Pro 57% ("working backwards from the four
  failing tests"), AgentHallu 45%, VitaBench 30%, Terminal-Bench 29%, AgentRx 29%, Who&When 12%.
- [lit] Who&When +5-20 pp step accuracy when the gold is given; TracerTraj / CORRECT labels generated with gold access;
  TrajErrBench annotators saw the failure diagnostics (κ 0.91 on τ²-bench where diagnostics are exact DB constraints,
  0.67 on SWE-Pro).
- [LLM] Rationales tagged uses_ground_truth are not markedly harder for the no-gold baseline (Who&When 42.9% vs
  43.6%, TraceElephant 32.1% vs 34.7%, LongRCA 13.8% vs 16.4%): the hindsight component is small on these sets, so
  the gap papers report when the gold is given is mostly answer-matching of the final step, not label reproduction.
**Deferred.** Blind re-annotation without the gold on a sample; measure how many labels move.

### H5. Agreement follows local verifiability, not causal weight
**Claim.** Steps whose wrongness is checkable inside the step and its observation (a claimed click that did not happen,
an inference contradicting visible text, an ignored tool error) get consensus; judgement calls (bad plan, wrong tool,
should have asked) do not, even when earlier and causally heavier. Datasets therefore over-sample verifiable errors
as "decisive".
**Evidence.** [ann] MP-Bench majority-flagged steps: Verification 19%, Planning 17%, Reasoning 16%, Reasoning-Action
Mismatch 10%; minority flags *before* the first majority step: Planning 26%, Tool/Agent Invocation 17%,
Reasoning-Action Mismatch 2.6%. [lit] SymFail κ per category C1 0.70 / C3 0.72 / C4 0.69 vs C2 (stalled) 0.37.
[LLM] Baseline exact accuracy by gold category: MP-Bench Reasoning Error 69.6%, Contextual Understanding 51.5%, Tool/Agent
Invocation 48.1%, Verification 42.9% vs Planning 22.0%, Tool Usage 21.9%; AgentErrorBench environment_error 71%,
action.* 60%, reflection.progress_misjudge 50% vs plan.inefficient_plan 8%, memory.over_simplification 11%,
plan.constraint_ignorance 11%; SymFail C4 plan-action-outcome inconsistency 48.9% vs C3 unresolved runtime 16.3%.
The same verifiability gradient that drives human agreement drives the model: on judgement categories the model picks
an earlier step than the annotator (AgentErrorBench plan.* earlier in 65-89%).

### H11. Independent annotation teams do not reproduce the published decisive step for a quarter to a third of logs
**Claim.** The exact step is not a stable property of the log.
**Evidence.** [ann] MP-Bench (3 fresh annotators) on the 177 shared Who&When logs: majority == Who&When 99/176 (56%),
within ±3 73%; the Who&When step received 3 votes in 87 logs, 2 in 48, 1 in 16, 0 in 26 -> for 42 logs (24%) at most one
annotator calls it a failure step; when they differ the majority is earlier (54) more often than later (23). AgentRx on
44 shared logs: same step 16. Who&When rationales: 48% generic ("The code is wrong."), 19% symptom-only. [lit] LongRCA
exact agreement 40%.
[LLM] Baseline exact accuracy on the Who&When labels stratified by the MP-Bench votes the label received: 3 votes
52.9%, 2 votes 50.0%, 1 vote 18.8%, 0 votes 15.4%; on the 0-vote logs the model's own step is flagged by at least one
MP-Bench annotator in 54%. On MP-Bench itself the model's step is inside the union of flags in 83% of logs, in the
majority set in 64%, exact against the first-majority step in 38%.
**Implication.** Report accuracy against vote-weighted or set targets; a single-label exact-step score on Who&When has a
ceiling near 55-60% for any method, and "misses" on contested logs are agreement with another annotation team.

### H12. Environment-caused failures are pinned to the nearest step, not to a cause
**Claim.** When the environment is broken (placeholder URL, blocked site, 404, unreadable PDF, container without sudo),
no agent decision is the cause; datasets without a fault-side label put the index on the task echo, the retry, the final
answer or the messenger.
**Evidence.** [ann] SymFail: 102/536 failure nodes are the Magentic-One echo of the task (agent 'user'), 98 are the
final node; 173 WebArena runs never reached the site. LongRCA: 55 labels on Computer_terminal relays of a delegated
agent's false "STATUS: SUCCESS". Rationale tag blames_environment: TraceElephant-Magentic 23%, Who&When HC 17%, AgentRx
14%. Failure-as-a-Process: environment-obstacle triggers have the most recovery attempts (75%) and the longest fix
windows. [read] 5f982798 steps 13/17 (PDF unreadable, "Nothing to summarize").
[LLM] Rationales that blame the environment: TraceElephant 7.4% exact (later in 59%), LongRCA 0% (9 cases); SymFail C3
unresolved-runtime labels 16.3% vs C4 48.9%; SymFail labels on the task-echo node 0% (102 cases), AgentErrorBench
'system.step_limit' 0% (8). The model consistently blames the step that *acts on* the broken observation, one or more
steps later than a label placed on the observation, the echo or the retry.
**Implication.** A fault-side pre-classifier (model / tool / environment / task) before step localisation; score
environment-caused failures separately.

### H7. The root is often an instruction, the visible failure the execution
**Claim.** Hand-off instructions that already contain the error or set an unproductive strategy ("continue
scrolling") are the root, but the executor's repeated failures are what the text shows; conventions split on which to
label.
**Evidence.** [read] Who&When HC 3.json (orchestrator instruction at 22 starts the scrolling episode; label on the
WebSurfer at 32). [ann] LongRCA: composite hand-off names are the reference role in 91 cases; Who&When HC blames the
orchestrator in 31% of logs and 6 labels sit on orchestrator instruction steps. AgentRx 08cae58d: all 28 WebSurfer events
are pinned to the orchestrator's instruction steps (off-by-one). [LLM] AgentRx: of the model's 28 picks before the
root, 24 are steps the annotators never marked, 8 of them orchestrator ledger/thought steps and 8 immediately followed
by an annotated specialist event -- the reader blames the instruction, the annotator the execution; with names removed
the reader blames the orchestrator even more often (see H2).

---------------------------------------------------------------------------------------------------------------------
## C. Shortcuts and artefacts behind reported accuracies

### H10. Surface shortcuts (position, length) account for a large share of published accuracies, on natural sets too
**Claim.** The decisive step is textually distinctive without being read: on injected sets it is late and terse (the
injector rewrites one step of a successful run and keeps only failing continuations); on natural single-agent sets it is
the *commit* step, where the agent summarises and decides, which is the longest message of the run. Reported LLM
accuracies on these sets are therefore partly position/length matching, and gains that do not beat these rules are
not evidence of attribution.
**Evidence (inspect/rule_baselines.py, exact-step %; worklog has the full table).**
- Injected: Who&When Pro last-decision 47.9 and shortest-step 46.2 (random 31; paper's best LLM 72.3; shortest/longest
  with direction learned per framework: MacNet 87, MathChat 86); CORRECT-Error shortest-step 50.8, last-decision 50.0
  (paper 30-80 Acc@1); TracerTraj shortest 12.7 / random 13.4.
- Natural: TrajErrBench τ²-bench longest-step 45.8 (best published 52.8; direct prompting 41.5-52.5); SWE-Pro longest
  18.6 (best 24.4, direct 10.5-17.4); AgentHallu longest 28.4 (GPT-5 32.7); Who&When longest 22.8 (above every prompting
  number in the paper, 5-25); SymFail first-decision 40.4; AgentRx last-decision 15.1.
- [read] τ²-bench: the gold is a plain message in 316/385 cases, length rank median 2; it is the longest in 183 cases,
  concentrated in reason.* labels (131/238): "Here's what I found ... I can help cancel this since ..." -- the commit.
- Register: injected steps are shorter than the same agent's own steps (MacNet 743 vs 2,463 chars, smolagents 742 vs
  1,571, MathChat 502 vs 1,525, CORRECT Planner 862 vs 1,555). [lit] fa_ideas register-leak probe; survey Fig. errpos.
- ±3 windows on short sets are near-trivial: random ±3 is 57% on Who&When, 80% on AgentHallu, 88% on Who&When Pro.
- [LLM] Who&When Pro 74.0% exact overall (frontier models in the paper 70-72), 93% when the injected step is the last
  decision vs 57% otherwise; CORRECT-Error 70.3% overall, 98% when the gold is the last decision vs 48% otherwise;
  TracerTraj injected labels: later than gold in 40%, earlier in 6%.
**Implication.** Every attribution result needs these rules as baselines; an attributor that is trained on these sets
can learn "the long commit message" / "the terse late step" instead of causality; evaluation should stratify by length
rank and position, and injection should be uniform over position with an injector that preserves the agent's register.
**Deferred.** A tiny length+position classifier per dataset as the published baseline; invariance test of trained
attributors under length-preserving paraphrase of the gold step.

### H8. "Answer was in the context" failures are consumption failures that acquisition-oriented readers miss
**Evidence.** [ann] SearchAuditBench Candidate Mismanagement: the gold string appears before/at the critical step in 68
of the 71 cases where it appears at all (17% of the category); Who&When <10% (consistent with fa_ideas). Rare elsewhere.

### H9. Datasets contain plain label errors that bound any method
**Evidence.** [ann] AgentErrorBench: 8 'system.step_limit' labels on the last turn whose reason is "the apple was still
not found due to the step limit" (symptom, not cause); one label out of range; 27 empty types. Who&When: 6 logs whose
blamed agent is not the agent of the labelled step, 2 labels on tool steps, 1 "failed" run that ends with the correct
answer (2.json). CORRECT-Error: 186 rows name an agent that did not speak at the labelled step, 43 labels on the user
message. TraceElephant: one label names an agent absent from the trace. LongRCA: 60 labels on tool records.

### H13. The direction of the reader's error follows the label convention and provenance
**Claim.** On natural long-horizon runs the judge blames the first suboptimal action while annotators blame the first
*consequential* one (prediction earlier than gold); on injected and short runs the judge drifts to the symptom
(prediction later than gold).
**Evidence.** [LLM] Share of predictions earlier / later than the gold: AgentErrorBench 63 / 13 (median -2), HORIZON
51 / 10, SearchAuditBench 49 / 29, AgentRx 40 / 30, Who&When 33 / 23, TRAIL 21 / 21, TrajErrBench 26 / 32, TraceElephant
28 / 37, MP-Bench 23 / 35, AgentHallu 17 / 26, LongRCA 25 / 59 (median +6), TracerTraj coding 29 / 57, TracerTraj
agentic injected 6 / 40 vs counterfactually diagnosed 35 / 22, CORRECT 15 / 15. Early bias on single-agent natural sets
whose labels mark the consequential decision; late bias on long multi-agent runs (the model drifts to the
planner/verifier decision near the end) and on injected labels (it blames the consumer of the corrupted content). The
sign of the error follows the label convention and provenance, so a single "symptom shift" story is wrong.

### H14. The reader stops at the symptom, and its justification says so
**Claim.** The largest class of misses on natural multi-agent and long runs is a *downstream* pick: the model names a
consequence of the gold error (the step where the damage became visible, often a loop or a stall). The second class is
a convention disagreement on the same error. Genuinely different errors and recovered picks are minorities. The
model's justification carries the signature: reasons that mention looping, stalling or strategy are the symptom picks.
**Evidence.** [LLM] Miss taxonomy with the gold and the human rationale revealed (`baseline/miss_taxonomy.py`):
"pick is a downstream symptom" MP-Bench 43%, LongRCA 44%, TRAIL 37%, Who&When 34%, TrajErrBench 32%; "same error,
other step" 20-40% (SymFail 81%); "pick is an upstream cause" dominates only on AgentErrorBench (44%), where the model
also judges itself right in 43% of misses. The model admits its pick was recovered in only 1-10% once confronted,
although its own blind inventory had tagged many of those picks recovered (H1): it defends the all-at-once choice.
[LLM] Reason tags vs correctness: mentions_loop halves exact accuracy on Who&When (23 vs 47), MP-Bench (24 vs 42),
AgentRx (8 vs 36), SearchAuditBench (9 vs 25), TrajErrBench (20 vs 43); states_contradiction doubles it on
AgentErrorBench (30 vs 14), SearchAuditBench (25 vs 12), TrajErrBench (44 vs 29). Keeping only predictions whose
reason states a contradiction and avoids loop/strategy/hedge language raises exact accuracy on the kept half from
43.5 to 50.5 (Who&When), 34 to 43 (TraceElephant), 22 to 31 (SearchAuditBench), 24 to 45 (AgentErrorBench, 19% kept);
LongRCA is the exception (loops are what its annotators label).
[LLM, negative] The obvious fix does not work: a backward second pass ("is there an earlier step that made your pick
inevitable and was never corrected?") lowers exact accuracy from 43.5 to 33.2 on Who&When and 35.4 to 20.8 on AgentRx;
69/184 picks move, all earlier, 24 right-to-wrong vs 5 wrong-to-right, and of 101 earlier candidates the model names it
marks one as corrected before the pick (AgentRx: 0 of 26). Primed for causes, the reader cannot see recoveries.
**Implication.** The symptom/cause direction is not fixable by instruction: the reader needs a *measured* consequence
(rollouts, or a success-probability model fitted on outcomes) to decide between its own pick and the earlier candidate.
What is cheap and works is the other side: a justification verifier / abstention rule on the reason text, since the
symptom picks announce themselves.

### H15. Candidate generation is far ahead of candidate selection
**Claim.** The reader's inventory already contains the gold step in most runs and in its first three candidates in
half to two thirds; the all-at-once choice among them is the weak link. An oracle reranker over the model's own top-3
would add 15-25 exact points on the multi-agent sets.
**Evidence.** [LLM] Gold in the inventory list / in the top-3 as listed: Who&When 78 / 67, MP-Bench 72 / 66,
TraceElephant 65 / 56, TrajErrBench 55 / 50, AgentRx 58 / 48, AgentErrorBench 58 / 41, LongRCA 47 / 28,
SearchAuditBench 39 / 27, against all-at-once exact 43.5 / 38 / 35 / 42 / 30 / 24 / 16 / 22. Ordering candidates
fatal-first does not help: the fate tag is not calibrated on causality.
**Implication.** Build the attributor as propose-then-verify: generate candidates with the reader, then select with a
consequence test (rollouts where replay exists; a learned success-probability model or the two-stage check otherwise),
which is also what the training-side literature converged on (ELPO, ProVer, CSO).

---------------------------------------------------------------------------------------------------------------------
## D. What the hypotheses imply for a targeted method, and what to test next

**Design consequences (each traces to the hypotheses above).**
1. *Separate wrongness from consequence.* The reader already finds the mistakes (gold listed in the inventory in
   55-85% of runs); what it lacks is a consequence test. The minimal version is a two-stage prompt: inventory with
   fates, then choose among the *fatal* ones only after checking, for each candidate, whether a later step undid it
   (H1). The real version is a learned or rolled-out success-probability curve whose drop-without-recovery marks the
   step (survey Proposals 2/4).
2. *Declare the convention, then attribute.* Three binary conventions decide a large share of the exact-step score:
   producer vs consumer (H2), instruction vs execution (H7), first-of-episode vs commit (H3'). A method should predict
   the *episode* (set/span) and emit the step under an explicitly selected convention; evaluation should score at
   episode level and report each convention separately.
3. *Fault-side first.* Classify environment / tool / task / model before localising (H12); on environment-caused
   failures no step is right and the datasets disagree where to pin it.
4. *Position and length are confounds, not features.* Report first/last/longest/shortest rules next to every number
   (H10); stratify by position and length rank; when training on injected data, inject uniformly over position with an
   injector that preserves the agent's register.
5. *Use the disagreement.* Vote-weighted or set targets (MP-Bench, AgentRx events, TRAIL spans, SearchAuditBench spans)
   are closer to the counterfactual quantity than a single index (H11); a method's "misses" on single-label sets should
   be reported against the union of annotations where one exists.
6. *The verifiability gradient is the difficulty axis.* Report accuracy per category family (verifiable slip vs
   judgement call), because averages hide that the hard half is the judgement half (H5).

**Deferred experiments (not run here; ordered by cost).**
- D1 Episode-level re-scoring of every baseline output with a block/episode segmenter (cheap; `inspect/repeat_blocks.py`
  is the start) -> how much of the exact-step gap is convention.
- D2 Two-stage consequence prompt (inventory -> fatal-only choice with an explicit "was it undone later?" check) on the
  single-agent/long sets where the reader's early picks are self-declared recovered (LongRCA, TrajErrBench, AgentHallu).
- D3 Fault-side pre-classifier + separate scoring (SymFail, TraceElephant, LongRCA environment cases).
- D4 Length/position classifiers per dataset as published baselines; paraphrase-invariance test of trained attributors.
- D5 Blind re-annotation of a sample without the gold (H4) and a two-convention re-labelling (producer/consumer,
  instruction/execution) of 100 Who&When logs (H2/H7) -> the two accuracies a method should report.
- D6 Rollout verification at (a) the steps the inventory tags recovered and (b) the gold steps the model tags
  recovered (Who&When HC/1, HC/3, ...): the direct test that some published golds have zero repair effect (H1, H9).
- D7 Ledger ablation (remove orchestrator self-monitoring text) to measure how much it anchors the reader (H6).
- D8 Outcome-blind inventories on the successful runs of every set that has them (TRAIL, HORIZON, Failure-as-a-Process
  excerpts) to measure the false-fatal rate of the reader as a function of run length (H1 control).

---------------------------------------------------------------------------------------------------------------------
## F. What moves the score: levers tested on a fixed panel

Panel: Who&When (184), AgentRx (73), τ²-bench (150), TraceElephant (120), LongRCA (60), AgentErrorBench (100); every
variant is scored on exactly the ids it ran on, with the standard run restricted to the same ids
(`baseline/compare_variants.py`, `baseline/analyze_sc.py`). Exact-step accuracy, standard -> variant.

| lever | Who&When | AgentRx | τ²-bench | TraceElephant | LongRCA | AgentErrorBench | reading |
|---|---|---|---|---|---|---|---|
| 3 same-dataset examples with rationales | 43.5 -> 44.6 | 30.1 -> 35.6 | 39.3 -> 42.7 | 35.0 -> 35.0 | 18.3 -> 18.3 | 21.0 -> 22.0 | +0 to +5; conventions are only partly learnable from sketches |
| reference answer given | 43.5 -> 45.1 | 51.7 -> 51.7 (τ-retail) | - | 34.2 -> 34.2 | - | - | no effect: misses are not about the outcome |
| backward cause-or-symptom pass | 43.5 -> 33.2 | 35.4 -> 20.8 | 42.7 -> 47.3 | 33.3 -> 27.5 | 20.0 -> 18.3 | 21.0 -> 19.0 | shifts picks earlier by a constant; helps only where the base was late |
| two-stage (inventory -> undone-later check) | 43.5 -> 39.9 | 30.1 -> 31.5 | 38.7 -> 44.0 | 35.0 -> 31.7 | 16.7 -> 21.7 | 20.8 -> 20.8 | same: a position prior in disguise |
| 5 samples, majority vote | 43.5 -> 42.9 | 30.1 -> 30.1 | 38.0 -> 42.7 | 33.6 -> 32.8 | 18.3 -> 15.0 | 21.6 -> 18.6 | -3 to +5 |
| any-of-5 oracle | 57.1 | 41.1 | 57.3 | 44.5 | 31.7 | 30.9 | the right step is among the samples 11-19 points more often than the vote finds it |
| extended reasoning (thinking, 32k) | 43.5 -> 35.3 | 30.1 -> 30.1 | 39.3 -> 42.7 | - | - | - | hurts on Who&When (later picks 23 -> 35%), neutral on AgentRx, +3 on τ²; 10-30x the generation cost |

Three conclusions for building attributors:
- **Prompt-level levers are worth -8 to +5 points; selection is worth 11-25.** Extended reasoning is not a lever
  here: it lowers Who&When by 8 points (the model re-derives the failure backwards from the final answer and stops
  at the first visible break) and helps only on τ²-bench. The oracle over five samples (+11 to +19)
  and the oracle over the model's own top-3 candidates (+15 to +25, H15) are the headroom; voting, examples and the
  gold do not reach it. The missing component is a selector with access to consequence, not a better reader.
- **Second passes are direction priors.** Both re-examination prompts move every pick earlier by 10-20 points of
  "earlier" share regardless of content, so they help on sets where the base reader is late (LongRCA, τ²) and hurt
  elsewhere. Primed for causes, the reader marks almost no earlier candidate as "corrected" (1 of 101 on Who&When,
  0 of 26 on AgentRx): reading cannot see recovery.
- **Confidence is free and calibrated.** Vote share (unanimous 52-57% exact vs <=2/5 11-31%) and reason-text properties
  (states a contradiction, no loop/strategy language: kept half 7-20 points above the dropped half) give a selective
  attributor without any training; LongRCA is the exception for the reason tags.

---------------------------------------------------------------------------------------------------------------------
## E. Research questions that follow from the findings

**On the object being labelled**
- RQ1 Is the decisive step a stable property of a failed run at all, or only an episode plus a convention? Test: the
  rollout screen on episode-sized windows; if repair effects are flat inside an episode and drop outside it, the
  episode is the unit and exact-step metrics are measuring conventions (H3', H11).
- RQ2 How much of a reader's early-pick error is a self-inconsistency it can be made to resolve? Test: a two-stage
  reader (inventory, then a per-candidate "was this undone later, and by which step?" check) on the sets where early
  picks are self-declared recovered (LongRCA, TrajErrBench, SearchAuditBench, AgentHallu); the gain bounds how much
  of the recovered-error trap is prompt-fixable versus needing consequence measurement (H1).
- RQ3 Do recovered errors and failed repairs have a text-visible signature that predicts the outcome of a rollout
  (a dip-and-rise versus a dip without rise), i.e. can a value curve fitted from outcomes alone separate them? Test:
  Proposal 2/4's hazard model with a recovery transition, validated on the 41 "recovered" and 80 "repairs failed"
  LongRCA runs and on Failure-as-a-Process fix windows (H1, Proposal 4).
- RQ4 Which published decisive steps have zero repair effect? Test: rollouts at the gold steps the model tags
  recovered (Who&When HC/1, HC/3 and the 7-28% of golds so tagged per set); a measurable label-error rate per dataset
  under the dataset's own counterfactual definition (H1, H9).

**On conventions and annotation**
- RQ5 How much of the disagreement between annotation teams, and between readers and annotators, is explained by two
  declared binary conventions (producer/consumer, instruction/execution)? Test: re-label 100 shared Who&When /
  AgentRx / MP-Bench logs under both conventions and report four accuracies; if the conventions explain most of the
  44-log AgentRx-vs-Who&When gap, "who" should be reported per convention (H2, H7).
- RQ6 Does annotator consensus track causal effect or local verifiability? Test: rollout effects at MP-Bench steps
  with 3, 2 and 1 votes; if effect size does not rise with votes but verifiability does, benchmarks are selecting
  checkable errors, not decisive ones (H5).
- RQ7 What fraction of failures in each dataset has no agent-side cause, and where do the step labels land when the
  environment is the cause? Test: a fault-side classifier (model / tool / environment / task) validated on SymFail,
  SearchAuditBench's excluded cases and MegaRCA's sides; score attribution separately per side (H12).
- RQ8 Do gold-aware labels differ from blind labels in kind rather than degree? Test: blind re-annotation without the
  reference on a sample from SearchAuditBench and LongRCA SWE-Pro (the sets whose rationales rely on the gold most);
  measure which labels move and whether they move toward the commit step (H4).

**On evaluation and shortcuts**
- RQ9 How much of published attribution accuracy survives position- and length-matched controls? Test: report the
  first/last/longest/shortest rules and a tiny per-dataset classifier next to every method; evaluate methods on the
  stratum where the rules fail (H10).
- RQ10 Does an attributor trained on injected data learn the injector's register rather than causality? Test:
  paraphrase the injected step at matched length and position, re-inject uniformly over position, and measure the
  transfer drop to natural failures (H10).
- RQ11 What is the ceiling on exact-step accuracy implied by annotator agreement, per dataset, and how do methods rank
  once scored against vote-weighted or set targets instead? Test: rescore every baseline against MP-Bench votes,
  AgentRx events, TRAIL spans, SearchAuditBench spans (H11).

**On the reader itself**
- RQ12 Why does the sign of the reader's error follow label provenance (early on consequential-decision labels, late
  on long multi-agent runs and injected labels)? Test: the same model on the same tasks under the three conventions of
  RQ5 and with the outcome hidden; if the sign tracks the prompt's definition of "decisive", the bias is definitional
  and should be controlled by the prompt, not trained away (H13).
- RQ13 What makes a reader's "fatal" judgement outcome-aware? Test: the outcome-blind inventory's false-fatal rate
  (5-34% on successful runs) as a function of run length and of giving the reader the success predicate, versus a
  value model trained on outcomes; the question is whether consequence can be read or must be measured (H1).
- RQ14 Does removing the system's own self-monitoring text (ledgers, "stalled, replanning") change where the reader
  points, and in which direction? Test: ledger ablation on Who&When HC and TraceElephant Magentic-One (H6).

**Added after the lever panel (Section F)**
- RQ15 Can a selector with access to consequence close the oracle gap? Test: take the model's top-3 candidates (or its
  five samples) and choose among them with (a) N rollouts from each candidate where replay exists (τ², ALFWorld, SWE),
  (b) a success-probability model fitted on outcomes elsewhere; the gain over the vote is the value of consequence
  information, the headroom is +11 to +25 (H15, F).
- RQ16 Is the direction prior of second passes a property of the prompt or of the model? Test: the same two-stage and
  backward prompts with the shift measured on successful runs and on injected runs with known positions; if the shift is
  constant, "earlier" instructions should be replaced by a per-dataset calibrated offset, which is what they implement.
- RQ17 How much of a trained attributor's gain is selection rather than reading? Test: train only a reranker on the
  frozen reader's candidates (features: vote share, reason tags, position/length rank, fate tag) and compare with
  end-to-end fine-tuning on the same labels; if the reranker matches it, attribution training is a selection problem.
- RQ18 Does label convention explain the per-dataset sign of the second-pass effect? Test: on datasets whose convention
  is "earliest" (τ², LongRCA) versus "first unrecovered" (AgentRx) versus annotator-specific (Who&When), predict the sign
  from the base reader's earlier/later balance before running the pass.
