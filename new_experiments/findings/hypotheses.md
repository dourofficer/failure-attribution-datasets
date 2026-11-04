# Why step-level failure attribution is hard: hypotheses from the data

Draft v2, 2026-11-02 (v1 of 2026-11-01 kept as `hypotheses_v1.md`). Synthesis of the per-dataset inspections
(`findings/datasets/<slug>.md`), the group syntheses (`findings/groups/g{1..4}_*.md`), the literature note
(`lit/known_phenomena.md`, phenomena P1–P8), the Qwen3.8-27B baselines and probes (`results/<slug>/`), and the
omission/commission experiment of 2026-11-02 (`results/omission_commission/`, §2b). Record ids are given so every claim
can be re-checked. Items marked PENDING depend on runs that had not finished when this draft was written (§8).

v2 changes: every observation (X1–X12) and hypothesis (H1–H13) now opens with a plain-language statement of what it
claims and a concrete example, before the evidence bullets; a glossary was added; §2b documents the omission →
commission experiment and answers "is this error type easy to attribute when the trajectory and the gold are known".

## Glossary (read once)

Datasets (slug → paper; `loaders/STATUS.md` has the loading details):
- `who_and_when` (WW; subsets Hand-Crafted = HC, Algorithm-Generated = AG), `mp_bench` (MPB; manual / automatic),
  `agentrx` (ARx; τ-retail / Magentic-One), `symtrace` (called SymFail in v1), `who_and_when_pro` (WWP, injected),
  `correct_error` (CE, injected), `tracertraj` (TT, injected), `aegis` (injected), `mast_data` (no step labels):
  the multi-agent-system (MAS) family, mostly Magentic-One logs. Groups g1 (output-only MAS) and g4 (injected).
- `traceelephant` (TE; Captain-Agent / Magentic-One / SWE-Agent), `longrca`, `memtrace`, `trail`: full traces, long.
  Group g2.
- `agenterrorbench` (ALFWorld / WebShop / GAIA), `trajerrbench` (TEB; τ²-bench / SWE-Pro), `agenthallu` (AH),
  `horizon`, `searchauditbench` (SAB), `failure_as_process` (FaP): single-agent natural failures. Group g3.

Terms:
- **Label / gold step**: the step the dataset blames. **Exact**: prediction = label. **±k**: within k steps.
  **In-set**: prediction is any labelled step when the dataset labels several.
- **Decisive step**: the earliest step whose correction would have made the run succeed. Most datasets claim to label
  this; §2 X2 shows that each team operationalises it differently (a *convention*).
- **Symptom**: a visible consequence of an earlier error (a loop, a tool error, a retry, a verifier FAIL). **Cause**: the
  step that produced it. "Late bias" = predicting a symptom instead of the cause.
- **All-at-once judge**: one LLM call that sees the whole trajectory (and the ground truth when released) and names the
  step. **Prefix monitor**: an LLM call that sees only steps 0..k and is asked whether step k is a mistake (online view).
- **Injected vs natural**: injected datasets (WWP, CE, TT, Aegis) take a successful run and have an LLM corrupt one step;
  natural datasets label failures that happened on their own.
- **Omission / acceptance / commission** (§2 X3, §2b): a required item (fact, page, tool result, constraint) never enters
  the agent's working state (omission); a later step acts as if it had (acceptance); a later step asserts a value or
  takes an action that no observation supports (commission).
- **Lock-in** (FaP `t_lock`): the step after which the run no longer revises its committed answer or plan.
- **Required item / provenance**: for the final claim, which observation (if any) supports it. "GT never observed" means
  the ground-truth string occurs in no tool/env return of the run.

## 0. What was done

- 19 datasets loaded into one schema (`loaders/`, 34,828 records, `loaders/STATUS.md`); 18 close-read by four group
  agents (≥8–20 trajectories each, 400+ in total), with text-free statistics designed per dataset (`inspect/`).
- Two LLM instruments on a local Qwen3.8-27B (thinking on): (i) **all-at-once judge** (`baseline/all_at_once.py`: task,
  optional ground truth, whole trajectory → decisive agent/step; `inventory` variant lists every mistake first);
  (ii) **prefix monitor** (`inspect/prefix_probe.py`: steps 0..k only, no outcome, "is the latest step a mistake?").
- A third instrument on 2026-11-02: a **label-blind shape classifier** (`inspect/oc_classify.py`: task, ground truth,
  final output, whole trajectory → omission / acceptance / commission steps and the overall shape), plus a text-free
  provenance pass (`inspect/oc_provenance.py`) on all 19 loaders. See §2b.
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

How to read the table: "misses later / all" is the number of wrong predictions that land *after* the label, over all
wrong predictions; 0.5 means no late bias. Exact accuracy tracks the *label convention's* locality, not the difficulty
of the task. The three highest natural scores (AgentHallu 69, HORIZON 53, Who&When AG 48) are datasets whose label is a
category landmark, a judge's own symptom step, or a single commission in a ≤10-step log; the lowest (LongRCA 20, SymFail
25, TRAIL 28, AgentErrorBench 28, AgentRx 29) are exhaustion runs, structural labels and loop-entry labels (X2, X7).

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

How to read it: "gold flagged%" = the monitor says "mistake" when shown the prefix ending at the gold step; "flag%
before/after gold" = the share of non-gold steps before/after the label that it also flags (false alarms and symptoms).

Three observations that organise everything below:

1. **The whole-trajectory judge is not late-biased, except on the longest traces.** In words: when a model reads the
   whole run and is wrong, it is as likely to blame a step *before* the label as one after it. The literature expected
   the opposite (symptoms attract blame). On every natural dataset with median length ≤60 steps the misses split roughly
   evenly before and after the gold (Who&When 41 later / 53 earlier; TraceElephant 22 / 38; TrajErrBench 23 / 21; TRAIL
   16 / 13; AgentRx 21 / 31; AgentErrorBench 16 / 27; HORIZON 12 / 16). Literature hypothesis 1 ("≥60% of misses after
   gold") is refuted for this instrument on those sets. The one exception is LongRCA (median 142 steps): 30 of 48 misses
   are later, median |offset| 28 steps — late bias appears when the trace is long enough that the judge can no longer
   hold the early steps (P5), not as a general property.
2. **The prefix monitor is late-biased.** In words: a model that sees the run step by step, without knowing the outcome,
   flags the consequences much more readily than the cause, because the cause often looks reasonable at the time. Steps
   after the gold are flagged at 2–7× the rate of steps before it on every natural dataset (e.g. Who&When 70% vs 27%,
   AgentErrorBench 56% vs 8%, HORIZON 75% vs 24%), and the earliest flag coincides with the gold in only 17–42%. SOAP's
   "downstream consequences are more conspicuous" (P1) is a property of per-step / online scorers, not of holistic judges.
3. **Injected data is a different task.** In words: a corrupted step contradicts what came before it, so it is locally
   obvious; a natural error usually is not. On Who&When Pro the injected step is locally detectable in 100% of records
   and is the earliest flag in 85%, with 7% false flags on the replayed prefix; and the judge's 75% exact collapses to
   30% when the last step is masked (48% of labels are the last agent step). Natural gold steps are locally flagged in
   33–80% and are the earliest flag in ≤42%.

## 2. Cross-dataset phenomena

Each phenomenon opens with what it claims in plain words and one example, then lists the datasets where it was observed
and the evidence (file § or record ids).

### X1. The post-error "symptom field" is diffuse, not a peak

**What it claims.** After the real error, the run does not produce one loud symptom that points back to the cause. It
produces many weak ones (retries, repeated actions, stalls, verifier chatter) spread over the rest of the run at a
roughly constant rate. So a method that looks for "the moment things went wrong" and walks back from it has no clear
starting point. **Example.** In TraceElephant Captain-Agent runs, 0% of steps before the label are near-duplicates of
an earlier step and 39% after it are, but the duplicates are spread out, not clustered just after the label.

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

**Why it matters.** Back-propagation from symptoms (the SOAP/EMFA idea) needs a symptom to start from; here the symptom
is a density change, not an event, so the start point is itself uncertain by several steps.

### X2. The labelled step is a convention, and the conventions diverge by 7–70 steps on the runs that matter

**What it claims.** "The decisive step" is not one well-defined thing. A failure unfolds as a chain: a bad proposal, a
commitment to it, the first visible symptom, the final wrong claim. Each annotation team picks a different link of that
chain, and on short runs with one obvious slip the links coincide, so the teams agree; on long runs the links are far
apart, so the same log receives labels tens of steps apart. **Example.** The same 44 Magentic-One logs are labelled by
Who&When and by AgentRx; the two labels coincide exactly in 16 and differ by up to 74 steps.

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

**Why it matters.** A method cannot score above the agreement between conventions unless it is told which convention
to follow; exact-step accuracy on long runs is partly a measure of which convention the method happens to imitate.

### X3. Omission → commission pairs: the evidence gap and the fabrication are both "the" error

**What it claims.** A large share of failures unfold in two steps. First a required item never enters the run
(omission): a page does not load, pip times out, a lookup is requested but never performed, the agent answers from
memory without searching. Later, an agent fills the gap by asserting something no observation supports (commission): it
"assumes" the numbers, lists a top-10 from memory, invents an arXiv id. Often a third step sits in between
(acceptance): an orchestrator ledger declares the item "gathered". Both the gap and the fabrication are defensible
answers to "where is the error", so annotation teams split between them, and single-step scoring penalises a method for
picking the other half. **Example.** Who&When HC/12: the WebSurfer at step 12 clicks the "Domestic" sort on the
worldwide table and never loads the domestic chart; the ledger at 13 claims both lists were gathered; the Assistant at
16 lists a wrong domestic top-10 from memory. Who&When labels 16; MP-Bench gives step 12 one vote and step 16 three.

- AG/3 (pip timeout → assumed numbers), AG/10 (manual-lookup requests → fabricated census figures), HC/12 (chart never
  loaded → list from memory), AgentRx 5f982798 (PDF not rendered → invented arXiv id); MP-Bench majority is strictly
  earlier than Who&When in 28/120 AG logs, always on the omission step (g1 G1-C).
- AgentRx resolves the pair by type: WebSurfer omissions are "recovered" (25/26 pre-root events), orchestrator
  acceptance/misinterpretation is "root" (22/73).
- AgentHallu: in 84% of hallucinated runs the ground-truth string never appears in any step; tool errors occur at the
  same rate in clean runs (33.6% vs 40.4%) — the signal is claim provenance, not trouble (H-AH3).
- TraceElephant reason texts: 34% omission + 11% outcome-only; LongRCA VitaBench 70% "ignored a request"; MemTrace:
  20/160 faulty ops have no dependency path to the output (g2 R8).
- **Measured on 2026-11-02 across all datasets: see §2b.** The pair shape is the majority shape in every
  evidence-gathering dataset (72–81% of runs in WW, MPB, ARx, TE, TRAIL), and the label sits within one step of the
  omission member far more often than of the commission member (WW 49% vs 6%, MPB 50% vs 4%).

**Why it matters.** The omission is defined by what did *not* happen, so it is invisible to any scorer that reads the
step's own text; the commission is visible but is not where most conventions put the label. H3 (forward provenance) and
the "predict the pair, accept either member" scoring rule follow from this.

### X4. The actor on the record is not the actor who decided

**What it claims.** Agent-level labels ("who is to blame") often follow the name the logging framework wrote on the
step, not the component that made the decision. Orchestrator calls get recorded under the specialist's name, tools are
named as agents, and an environment condition is blamed on whichever role happened to react to it. **Example.** In
TraceElephant, 30 of 90 Magentic-One gold steps are orchestrator ledger calls stored under the specialist's name, and the
human `mistake_agent` follows the stored name in 218 of 219 runs.

- TraceElephant: 30/90 Magentic-One gold steps are orchestrator ledger calls recorded under the specialist's name, and
  the human `mistake_agent` follows the recorded name in 218/219 runs; SWE-Agent "agents" are tool names, mismatching
  the tool called in 225/1,551 calls (g2 R1).
- LongRCA: one environmental condition (NYC-named listings in 605/685 TravelPlanner runs; logged-out sessions in 52/76
  Reddit runs) is blamed on six / three different roles depending on who *reacted*; 55 labels name `Computer_terminal`.
- TrajErrBench: the simulated user ends the dialogue mid-confirmation in 29 runs; the agent is blamed in 14 (H-TEB-5).
  AgentHallu Human-Interaction blames the `ask_human` step (56/73 are the first tool call) although the adoption step is
  where the agent could have resisted (H-AH4).

**Why it matters.** Agent accuracy partly measures agreement with an instrumentation convention (also g1 G1-E, g4 H5);
a method that re-derives the decider from the prompt owner can disagree with the label while being right.

### X5. Labels are written with information the attributor never sees

**What it claims.** Annotators (and the dataset's own LLM judges) knew the outcome, the gold answer, the failing tests
or the evaluator's verdict when they chose the step. A method that is not given that information is solving a different,
harder problem, and when it lacks a failure description it tends to invent one. **Example.** The same Who&When log HC/30
rendered with and without the ground-truth answer gets step 8 from the judge in one case and step 66 in the other, because
knowing the answer switches the judge from "where did the plan drift" to "where did the wrong value first appear".

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
  Who&When log rendered with and without ground truth gets different steps (HC/30: step 8 vs step 66).

**Why it matters.** Reported accuracies compare an outcome-blind method with outcome-informed labels; H9 and H13 say what
to do about it (make the failure description an explicit input; measure the hindsight share).

### X6. Successes contain the same errors ("same signal, different fate")

**What it claims.** Tool errors, retries, loops and wrong intermediate facts occur in successful runs at about the same
rate as in failed ones. What separates the two is not whether a bad signal appeared but how the next step responded to
it (recovered or not). A detector that fires on the signal alone will fire on successes too. **Example.** In
Failure-as-a-Process, 71% of PASS runs contain at least one annotated error event, at the same relative position as the
decisive error of FAIL runs.

- Failure-as-a-Process: 71% of PASS runs have ≥1 error event, 2.3 per run, at the same relative position as FAIL
  t_err (0.28 vs 0.31); observable events before lock-in in FAIL runs are drawn from the same distribution (H-FaP-1).
- TRAIL: 34/117 GAIA runs end correctly, 31 carry errors, 23 carry a HIGH; formatting/instruction/orchestration errors
  are outcome-neutral (P(correct) 0.28–0.29 vs base 0.29) while retrieval (0.13) and tool-hallucination (0.17) cascade.
- AgentHallu clean runs: tool errors at the same rate as hallucinated ones; AgentRx recovered WebSurfer failures carry no
  error string in 0/24 and only 6/24 are followed by a ledger flag — recovery is silent, visible only as a paraphrased
  re-ask (g1 G1-D).
- HORIZON: trajectory-level separation of pass/fail (AUROC 0.87–0.91 on n_steps) comes from successes being short and
  failures early-stopped, not from dynamics (horizon H5).

**Why it matters.** "Anomaly relative to successful runs" (the OAT / one-class idea) has little to detect at the content
level; H8 and H12 say to score the *transition* (signal → response) and the phase structure instead.

### X7. Structural and positional priors explain much of the published accuracy

**What it claims.** For many datasets a rule that never reads the text (last agent step; first occurrence of a specific
structural event; a fixed step per error category) matches or beats the published LLM attributors. The label position is
largely determined by the framework's structure and the annotation convention, not by the content of the step.
**Example.** In CORRECT-Error the labelled step starts a Planner→Planner adjacency; the rule "first Planner→Planner
adjacency, else last step" reaches 74.0% exact, while the paper's LLM judges score 6–63%.

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

**Why it matters.** Every method should be reported against its dataset's structural prior; a gain below the prior is
not evidence of reasoning (H5, H7).

### X8. Injected and natural errors differ in kind, not degree

**What it claims.** An injected error step contradicts its own prefix (it changes a number the run already observed, or
rewrites a conclusion under an unchanged evidence recap), is written in the injector's voice, and is usually the last or
near-last step. A natural error step looks locally reasonable and is often a *non-event* (something not done). Training
on injected data therefore teaches local-contradiction detection and a last-step prior, neither of which transfers.
**Example.** The prefix monitor flags the injected Who&When Pro step in 100% of records with 7% false alarms on the
replayed prefix; natural labels are flagged in 33–80%.

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

**Why it matters.** H7: injected sets are useful for one channel (local consistency) and misleading as a benchmark of
natural attribution.

### X9. Environment and harness failures are labelled on agents; no dataset has a "no attributable step" class

**What it claims.** When the environment was broken (placeholder pages, content filters, install timeouts, infeasible
tasks, prompt leakage), the datasets still label an agent step, usually the one that issued the doomed call, because the
schema forces a step. An attributor is then trained and scored to blame someone for a failure no step caused.
**Example.** In SymTrace, 450 of 536 runs never reached a usable page (`__SHOPPING__` placeholder); the label goes to the
action that issued the call.

- SymFail: 450/536 runs never reached a usable page (`__SHOPPING__` placeholder); the label goes to the action that
  issued the doomed call. Who&When HC/48 (Azure content filter), AG/3 (install timeout), 37 missing WebSurfer turns;
  AgentRx "Guardrails Triggered" 9/44 roots. LongRCA: ≥60% of TravelPlanner runs sit on a simulator condition;
  ≥6 VitaBench rationales say the agent was not at fault. AgentErrorBench: 8 Qwen ALFWorld runs explore 30 distinct
  locations with 0 invalid actions and run out of budget; ~5 GAIA runs are infeasible with the given tools (H3).
  HORIZON: 594/639 Catastrophic-Forgetting labels are prompt-construction leakage (example question drift) (H3).

**Why it matters.** H4 / H4b: classify the regime first and allow an "environment / budget / no decisive step" output.

### X10. Verification theatre and the final write are the dominant late labels

**What it claims.** Runs end with a verifier saying PASS, a ledger saying "satisfied", or a confident final claim,
regardless of whether the task was solved; successes and failures end the same way. These end-of-run steps attract
annotator votes and judge predictions but carry no information about where the failure started. **Example.** 97% of
LongRCA SWE-Pro runs end with a JudgeAgent PASS issued after the root cause; in Failure-as-a-Process the final step is a
claim in 70% of FAIL and 71% of PASS runs.

- LongRCA: 97% of SWE-Pro runs end with a JudgeAgent PASS after the root; 217/320 TravelPlanner runs with
  `passed:false` still terminate as complete; 140 roots in the last 6 steps. TRAIL: 46/117 GAIA primaries are the
  manager's final call. SearchAuditBench: critical = final answer in 17%. MP-Bench: 24% of unanimous flags are FINAL
  ANSWER; `is_request_satisfied=true` ledgers are voted 16/18; AgentRx root = orchestrator acceptance 22/73.
  Failure-as-a-Process: verification after lock-in in 55% of failures, final step is a claim in 70% of FAIL *and* 71% of
  PASS — the end of the run is uninformative (H-FaP-4).

**Why it matters.** H11: treat verifier and claim steps as zero evidence for localisation.

### X11. Silent failures need an oracle the trajectory does not contain

**What it claims.** In a large minority of runs nothing in the transcript shows that anything went wrong: the agent
violated a policy clause, chose the wrong candidate given a hidden user goal, or wrote hidden state (a database row)
that is never echoed. Attribution then requires an external oracle (the policy, the goal, the DB state), and giving the
judge that oracle changes *which* step it blames more than how often it is right. **Example.** 65.5% of TrajErrBench τ²
failures have no transcript symptom at all; the policy violations among them are decidable only from the step-0 policy
text.

- TrajErrBench τ²: 65.5% of failures have no transcript symptom; policy violations (act.*, obs.*, WrongOrder) are
  decidable from the step-0 policy plus tool outputs, candidate-selection errors (reason.WrongChoice) need the hidden
  goal (H-TEB-2/3). AgentHallu BFCL: the decisive call leaves hidden state; gold response visibly errors in only 19–56%
  (H-AH5). Failure-as-a-Process: 28% silent failures; awareness is observability (first awareness ≥ t_obs in 413/466),
  so verbalised doubt is a lagging symptom (H-FaP-3).
- Giving the judge the hidden oracle does not automatically help: with the simulated user's goal (leaked in the zh edition
  of TrajErrBench, see §4) Qwen changes 16/50 predictions but accuracy stays 22/50; with the ground-truth answer on
  Who&When the published step accuracy moves by −1 to +1.8 pp. Outcome knowledge changes *which* step is blamed more
  than *how often* it is right (g3 R6, lit P3).

**Why it matters.** H9 / H13: the failure description must be an explicit input, and labels that need hidden state
should be measured and reported separately.

### X12. Terminal and harness artefacts decide a large share of "natural" single-agent failures

**What it claims.** Many single-agent failures are not reasoning failures at all but artefacts of the harness: the model
answers the in-context example question instead of the real one, ends with `finish` instead of `answer`, wraps its
action in quotes so the environment rejects it, or the simulated user hangs up. These are detectable with a regex on the
last two turns or on action syntax, and they carry cognitive-sounding labels. **Example.** 75.5% of GPT OS failures in
HORIZON answer the in-context example question (`/etc`), and 93% of the judge's "Catastrophic Forgetting" labels are
this mechanism.

- HORIZON: 75.5% of GPT OS failures answer the in-context example question (`/etc`; 93% of the judge's "Catastrophic
  Forgetting" labels are this mechanism), 38% of Claude OS failures end with `finish` instead of `answer`, 89% of web
  failures are early stops (parse ×3 or max steps) (g3 R4). AgentErrorBench: 33% of GPT-4o and 46% of Llama ALFWorld
  turns are quoted/prose-wrapped actions the environment rejects, and 24/25 runs with ≥10 malformed actions carry a
  *cognitive* label. TrajErrBench: 25 runs end in `transfer_to_human_agents`, 29 are ended by the simulated user.
  AgentHallu BFCL: silent `None` responses in 8–22% of gold steps.

**Why it matters.** A deterministic artefact checker on the last two turns and on action syntax would remove a third to
three quarters of these runs from the step-attribution problem (H4b).

## 2b. The omission → commission experiment (2026-11-02)

**Question.** How many trajectories, in each dataset, have the X3 shape; which member of the chain does each dataset's
label sit on; and is this error type easy to attribute when the whole trajectory and the gold answer are known.

**Instruments.**
- *Text-free provenance* (`inspect/oc_provenance.py`, all 19 loaders, `results/omission_commission/provenance_*.jsonl`):
  for every failed run with a short ground-truth string (3–120 normalised characters, not a 1–3 digit number), does the
  string occur in any *observation* (tool / env returns; the `Observation:` part of agent steps; WebSurfer /
  FileSurfer / terminal messages in output-only MAS logs)? Before or at the label? For the final answer string: does it
  first appear in an observation (evidence-origin), in agent text before any observation (memory-origin), or nowhere
  before the final step? The GAIA annotator metadata leaked into TRAIL's framework spans and TRAIL's `final_answer`
  tool spans are excluded from the observation channel.
- *Label-blind shape classifier* (`inspect/oc_classify.py`, Qwen3.8-27B with thinking, three vLLM instances, prompt in
  the file): sees task, ground truth, final output and the whole trajectory (100k-token cap), not the label. Returns
  `missing_item`, `omission_step` + kind (never_sought / attempt_failed / delegated_not_done / visible_not_extracted /
  obtained_then_dropped), `acceptance_step`, `commission_step` + kind (fabricated_fact / unjustified_assumption /
  hallucinated_tool_result / misread_evidence / wrong_binding / action_without_basis), `shape` (pair /
  commission_only / omission_only / other) and a `decisive_step`. All labelled records for the seven smaller datasets;
  stratified samples (60–150) for the rest. Sanity check on the hand-read cases: HC/12 → omission 12
  (visible_not_extracted), acceptance 13, commission 16; AG/3 → 3 (attempt_failed) → 4 (unjustified_assumption);
  AG/10 → 0 (never_sought) → 5 (fabricated_fact); all three as read by the g1 agent and the annotators.
- *Scoring* (`inspect/oc_summarise.py`): a label "sits on" a member if it is within ±1 of that member's step; members
  are checked in the order omission, acceptance, commission. "Pair with substantive fabrication" excludes pairs whose
  commission is only a forced final answer in the last two steps (`action_without_basis` at the end of an exhausted run).

**Text-free result** (failed runs; `inspect/oc_provenance_table.py`):

| dataset | failed runs | GT checkable | GT never in any observation | GT observed at/before label | final answer appears nowhere before the final step |
|---|---|---|---|---|---|
| who_and_when | 184 | 134 | 95% | 4% | 26% (memory-origin 54%) |
| mp_bench | 289 | 195 | 84% | 7% | 100% (79 checkable) |
| agentrx | 73 | 12 | 58% | 25% | 100% (9) |
| traceelephant | 220 | 119 | 86% | 9% | – |
| trail (GAIA) | 148 | 77 | 64% | 34% | 100% (75) |
| agenthallu (hallucinated) | 443 | 204 | 84% | 9% | 73% (78) |
| searchauditbench | 1,243 | 713 | 72% | 25% | 92% (499) |
| symtrace | 536 | 59 | 93% | 5% | 1% (memory-origin 93%) |
| horizon (web) | 625 | 622 | 83% | 5% | 100% |
| memtrace | 160 | 94 | 90% | 10% | 100% (9) |
| who_and_when_pro (injected) | 6,257 | 3,718 | 79% | 18% | 87% |
| aegis (injected) | 9,533 | 5,111 | 96% | 0% | 87% |
| tracertraj (injected) | 3,998 | 35 | 100% | 0% | 100% |
| longrca, trajerrbench, agenterrorbench, correct_error, mast_data, failure_as_process | – | 0 | no usable ground-truth string | | |

Reading: wherever the gold can be checked, the required item never entered the run in 64–95% of failed runs. The
omission side is therefore the common case everywhere, not an AgentHallu peculiarity. The final-answer column is weaker
evidence than it looks: in most datasets the answer string is first formed in the final step itself, so "nowhere before
the end" mostly says the answer was composed at the end, not that it was fabricated. The classifier is the instrument
for the commission side.

**Classifier result** (run complete 2026-11-02 17:37; `results/omission_commission/summary.txt`, regenerated by
`inspect/oc_summarise.py`; "all" = every labelled failed record, "sample" = stratified by subset, seed 0):

| dataset (coverage) | n parsed | pair | pair w/ substantive fabrication | commission only | omission only | other | label within ±1 of omission / acceptance / commission (pairs) | label on none | classifier decisive = label (exact / ±1) |
|---|---|---|---|---|---|---|---|---|---|
| who_and_when (all) | 183 | 78% | 60% | 2% | 20% | 1% | 49 / 15 / 6 | 29% | 40 / 49 |
| mp_bench (all labelled) | 273 | 72% | 52% | 2% | 22% | 4% | 50 / 7 / 4 | 40% | 34 / 41 |
| agentrx (all) | 73 | 81% | 45% | 7% | 11% | 1% | 22 / 10 / 15 | 53% | 34 / 40 |
| traceelephant (all) | 213 | 81% | 78% | 3% | 15% | 1% | 31 / 19 / 9 | 40% | 28 / 38 |
| trail (all) | 144 | 79% | 78% | 3% | 5% | 13% | 32 / 17 / 4 | 47% | 37 / 40 |
| searchauditbench (sample 150) | 149 | 80% | 61% | 9% | 9% | 3% | 26 / 15 / 11 | 48% | 34 / 38 |
| longrca (sample 120) | 118 | 66% | 64% | 0% | 28% | 6% | 13 / 8 / 8 | 72% | 14 / 17 |
| symtrace (sample 120) | 120 | 58% | 57% | 0% | 41% | 1% | 74 / 10 / 3 | 13% | 28 / 45 |
| agenthallu (sample 150, hallucinated) | 144 | 56% | 48% | 12% | 9% | 23% | 74 / 6 / 1 | 19% | 45 / 69 |
| trajerrbench (sample 120) | 118 | 54% | 53% | 10% | 10% | 25% | 28 / 16 / 8 | 48% | 24 / 25 |
| memtrace (sample 60; 15 over context) | 45 | 53% | 40% | 9% | 33% | 4% | 38 / 0 / 21 | 42% | 44 / 60 |
| agenterrorbench (all) | 198 | 45% | 36% | 1% | 40% | 14% | 24 / 10 / 3 | 63% | 20 / 21 |
| horizon (sample 120, step-labelled) | 120 | 5% | 5% | 0% | 89% | 6% | 67 / 0 / 0 | 33% | 41 / 58 |
| who_and_when_pro (injected, sample 120) | 119 | 66% | 51% | 22% | 7% | 6% | 78 / 9 / 3 | 10% | 68 / 82 |
| correct_error (injected, sample 80) | 78 | 55% | 51% | 14% | 26% | 5% | 81 / 7 / 9 | 2% | 67 / 73 |
| tracertraj (injected, sample 120) | 117 | 56% | 50% | 28% | 9% | 8% | 57 / 17 / 0 | 26% | 32 / 55 |
| aegis (injected, sample 80) | 73 | 27% | 27% | 64% | 1% | 7% | 55 / 0 / 0 | 45% | 11 / 21 |

Unparsed or refused outputs (thinking overran or prompt over the 200k context) were 0–6 per dataset except MemTrace
(15 of 60). Dominant kinds (`results/omission_commission/summary.txt`): omission = `never_sought` in WW, TRAIL,
SymTrace, TEB, AH (answering or acting without looking) and `attempt_failed` in MPB, TE, SAB, LongRCA, HORIZON (a call
that returned nothing and was not retried); commission = `unjustified_assumption` / `fabricated_fact` in the
retrieval datasets and `action_without_basis` (a final answer or consequential action with no evidence) in the MAS
logs and TEB.

Reading the table:
- **The pair is the majority shape wherever the agent has to gather evidence**: 72–81% in WW, MPB, ARx, TE, TRAIL and
  SAB, 66% in LongRCA, 53–58% in SymTrace, AH, TEB and MemTrace. Even after removing forced final answers, half or more
  of the runs in those datasets contain a substantive fabrication that fills a gap.
- **It is a minority shape where the failure is about acting, not knowing**: HORIZON (89% omission-only: the agent
  skips a required action and stops; nothing is fabricated), AgentErrorBench (40% omission-only loops and 14% format /
  budget "other"), and Aegis (64% commission-only: the injector corrupts an obtained value, nothing was missing).
- **Which member the label sits on differs by dataset, and is mostly the omission.** Injected sets (WWP 78%, CE 81%)
  and AgentHallu (74%) / SymTrace (74%) put the label on the omission member; MPB (50%) and WW (49%) do so half the
  time; ARx spreads over acceptance and commission; LongRCA (72%), AgentErrorBench (63%) and ARx (53%) label a step
  near none of the three members, which are the long or exhaustion-dominated sets of X2.
- **Knowing the shape does not give the step.** The classifier's decisive step matches the label in 14–45% exact on the
  natural sets (±1: 17–69%), in the range of the all-at-once judge of §1, while scoring 67–68% exact on the two
  injected sets whose labels are the (last) commission step.

**Answer to "is this error type easy to attribute when the trajectory and the gold are known".** Easy for the
mechanism, not for the step.
- *Easy part.* With the gold in hand the required item is known, so the omission question reduces to "did this item
  ever enter an observation" (a string check finds it absent in 64–95% of checkable runs) and the commission question to
  "where does the wrong value first appear without support". The classifier names the chain members consistently with
  the hand reads and finds the pair shape in 72–81% of runs in every evidence-gathering dataset.
- *Hard part.* Scoring against the dataset's single labelled step. The classifier's own decisive step matches the label
  in 14–45% exact / 17–69% ±1 on the natural datasets (WW 40/49, MPB 34/41, ARx 34/40, TE 28/38, TRAIL 37/40, SAB 34/38,
  LongRCA 14/17), the same range as the all-at-once judge, although it has correctly described the failure. Three reasons: (1) the omission step is a judgment, not an
  event — the planning step, the first failed call, the last failed call, or the delegation that was never executed are
  all defensible, and in long HC runs the classifier puts it at the last failed attempt while Who&When labels the
  orchestrator's first wrong instruction, 17 steps earlier on median; (2) conventions pick different members — WW and
  MPB sit on the omission side in about half of the pairs, ARx more often on acceptance or commission, and in 29–53% of
  pairs the label is within one step of none of the three; (3) exhaustion runs produce a degenerate pair whose
  "commission" is a forced final answer with no basis (strict-pair rate drops from 78% to 60% on WW and 81% to 45% on
  ARx), where the label marks the start of a wasted episode that no step-level definition pins down.
- *Without the gold* the easy part also gets harder: the required item must be inferred from the task's constraints
  rather than read off the answer, which is what the AgentHallu claim-support idea in H3 is about.

**Does knowing the mechanism raise attribution accuracy?** (added 2026-11-03; same classifier outputs, label within ±1,
all parsed runs.) Three ways of turning the chain into a prediction, against the classifier's single decisive step:

| dataset | single decisive step | best fixed member per dataset (fallback: decisive) | any member (pair output, either accepted) |
|---|---|---|---|
| who_and_when | 49% | omission 48% | **66%** |
| mp_bench | 41% | omission 49% | **55%** |
| traceelephant | 38% | commission 38% | **56%** |
| symtrace | 45% | omission 50% | **58%** |
| searchauditbench | 38% | commission 32% | **48%** |
| agentrx | 40% | commission 40% | **48%** |
| trajerrbench | 25% | commission 29% | **37%** |
| longrca | 17% | omission 14% | **25%** |
| trail | 40% | commission 38% | 44% |
| agenthallu | 69% | omission 76% | 65% |
| agenterrorbench | 21% | omission 23% | 25% |
| horizon | 58% | omission 63% | 60% |
| who_and_when_pro / correct_error / tracertraj / aegis (injected) | 82 / 73 / 55 / 21% | commission 83 / 79 / 52 / 37% | 84 / 78 / 60 / 37% |

- As a *single-step* predictor, the mechanism adds nothing: choosing a fixed member per dataset (the convention lever of
  H6) moves accuracy by −6 to +8 points, because conventions are mixed within each dataset.
- As a *pair* output scored with either member accepted (the H3 rule), it adds 8–18 points on every evidence-gathering
  dataset (WW 49→66, TE 38→56, MPB 41→55, SymTrace 45→58, SAB 38→48). This is a change of output format and metric, in
  the spirit of SearchAuditBench's tolerance span, not a better localiser.
- The "any member" column is also the ceiling of a perfect member-selector: 44–66% on the natural sets. The remaining
  34–56% of runs have their label near none of the three members: long or exhaustion runs (LongRCA, AgentErrorBench,
  AgentRx Magentic) where the label marks the start of a wasted episode rather than a link of the chain (X2, H4).
- Where the label is a category landmark (AgentHallu, HORIZON) the single decisive step already encodes the convention
  and the pair output is slightly worse.

So the mechanism explains the cap (the label is one of two or three defensible points, chosen by convention) and
converts into accuracy only when the output is allowed to be the pair; what it buys a single-step method is a
candidate set of two or three steps instead of N, with the choice among them left to convention.

**Caveats.** One classifier model and prompt; samples of 60–150 on the larger datasets; "label on member" uses ±1 and
the dataset's primary label (root cause for ARx, earliest HIGH span for TRAIL, earliest majority for MPB); the
text-free check is a normalised substring match and under-counts paraphrased evidence.

## 3. Ranked hypotheses

Each hypothesis has four parts: **Claim** (plain words, with the situation it addresses), **Why we believe it**
(evidence, pointing to §2), **How to test it** (cheap = this infrastructure, days; expensive = new annotation or
training), **What a method would do** (the design consequence).

**H1. Late bias lives in per-step scoring, not in holistic judgement; the fix for monitors is dependency-aware
back-propagation, the fix for judges is convention matching.**
- *Claim.* Two different instruments fail in two different ways. An online monitor (sees the prefix, judges the latest
  step) flags symptoms because the cause looked reasonable when it happened; it is late-biased and needs a mechanism to
  push blame back along dependencies. A holistic judge (sees everything) is not late-biased; its misses are about which
  link of the chain to blame, so what it needs is to be told the convention.
- *Why we believe it.* §1 observations 1–2 (judge misses split evenly before/after the gold; monitor flags 2–7× more
  after the gold); X1 (the symptom field is diffuse, so there is no single symptom to back-propagate from).
- *How to test.* Cheap: signed-offset distributions per instrument on every dataset (done for two instruments; add OAT-
  and SOAP-style scorers on the same embeddings). Expensive: apply SOAP/EMFA rescoring to the prefix-monitor curve
  (expected to halve its median offset) and to the judge (expected to do nothing).
- *Method.* Use the monitor only to propose a *region* (the onset of the first flags) and the judge to pick the step
  inside it under an explicit convention.

**H2. Attribute to the first decision that proceeds despite a condition (the acceptance step), not to the condition and
not to the actor on the record.**
- *Claim.* When a tool fails, a page does not load, or a specialist returns nothing, the error is not the failure
  itself (the environment did that) and not the specialist whose name is on the message; it is the next decision that
  carried on as if the condition had not occurred: the orchestrator ledger that says "gathered", the agent that executes
  a proposal after consent, the step that adopts a fetched wrong fact.
- *Why we believe it.* X4 (record owner ≠ decider); AgentRx root = orchestrator acceptance 22/73 and
  `is_request_satisfied` ledgers voted 89% (g1 H-A2); TrajErrBench proposal-vs-execution +2; AgentHallu fetch-vs-adopt
  +1; §2b: 77% of Who&When pairs and 92% of AG pairs contain an explicit acceptance step.
- *How to test.* Cheap: a claim-vs-evidence check on every orchestrator ledger in the 102 Magentic logs (one call each),
  predicted ≥70% hit on roots; re-derive the actor from the prompt owner in TraceElephant and re-score agent accuracy.
  Expensive: re-annotate 50 runs under the "first decision despite condition" rule.
- *Method.* Candidate set = decision steps that consume an observation; score the consistency between the claim made
  and the evidence available.

**H3. Forward-trace required items instead of back-tracing symptoms: the root is the first step where a required item
(gold evidence, plan constraint, candidate entity, task requirement) stops being carried forward.**
- *Claim.* Most failures are about something that went missing (X3, §2b): a fact never retrieved, a constraint dropped,
  a candidate never evidenced. A missing thing leaves no symptom at the step where it went missing, so tracing backwards
  from the final claim cannot reach it. Tracing *forwards*, item by item ("was this requirement obtained? is it still
  present at step t?"), finds the first step where an item is dropped or should have been obtained; the fabrication that
  later fills the gap is the second member of the pair and should be accepted as an alternative answer.
- *Why we believe it.* §2b: GT never enters any observation in 64–95% of checkable failed runs; the pair shape is 72–81%
  of runs in WW, MPB, ARx, TE, TRAIL; the label sits within one step of the omission member in 31–50% of pairs vs 4–15%
  for the commission; AgentHallu 84% "evidence never arrived"; MemTrace 20/160 roots with no dependency path to the
  output; TraceElephant 19/176 runs where the ground truth is visible before the label and then dropped (g2 H4).
- *How to test.* Cheap: the "last step containing the GT string + 1" rule on the 19 TraceElephant runs; a claim-support
  classifier on AgentHallu's 693 runs vs the judge's detection AUROC; §2b's classifier scored with "either member" vs
  single-step (done: see the table). Expensive: a forward tracer on MemTrace's 50 Update/Extraction cases; blind
  re-labelling of 50 pairs under an explicit "omission member / commission member" rule to measure which the annotators
  mean.
- *Method.* Provenance tracing of the final claim and of each task constraint; blame the drop; output the pair and
  accept either member in scoring.

**H4. Classify the failure regime before attributing; a large minority of runs have no decisive step.**
- *Claim.* Runs that end by budget exhaustion, environment outage or a terminal artefact have no step whose correction
  would have succeeded, yet the datasets label one anyway (X2, X9, X12). An attributor should first decide which regime
  it is in ("one decisive mistake" vs "exhaustion / blocked / artefact") and only localise in the first.
- *Why we believe it.* X2 exhaustion runs (22% of Who&When HC, 84% of SymFail, 8+ AgentErrorBench budget runs); X9
  environment failures; X7 terminal-action artefacts (HORIZON 75% of GPT-OS failures); AgentErrorBench WebShop
  bifurcation ("never looked" loop regime vs "looked and misjudged" buy regime, H5); §2b: on AgentErrorBench the pair
  shape covers only 39% and 24% of runs are "other" (loops, format, budget), and in Who&When HC the strict-pair rate is
  47% because the "commission" is often a forced final answer.
- *How to test.* Cheap: a regime classifier from text-free features (distinct-action fraction, null observations,
  terminal action, env error at first tool call), and cross-team agreement measured per regime (expected ≈0–36% on
  exhaustion vs >60% on single-commission). Expensive: pass^k re-runs with a larger budget; if the task then succeeds,
  the run had no decisive step.
- *Method.* A "no attributable step / environment / budget" output class, and per-regime attributors.

**H4b. Run deterministic artefact checkers before any LLM attribution.**
- *Claim.* A regex on the last two turns and on action syntax identifies a third to three quarters of single-agent
  failures as harness artefacts (X12) with high precision; those runs should leave the step-attribution problem.
- *Why we believe it.* X12.
- *How to test.* Cheap: regexes for terminal action (`finish` vs `answer`, example-question drift, `Action: none` ×3,
  transfer-to-human, user stop) and action syntax (quoted/prose-wrapped actions) scored against the environment verdict
  on all 3,332 HORIZON runs and the 100 ALFWorld runs; expected precision >0.95 on GPT-OS and Claude-OS.
- *Method.* Artefact class → no step attribution; otherwise proceed to the regime classifier of H4.

**H5. The step is a near-deterministic function of the error category and structural landmarks; predict the category,
then apply a positional rule.**
- *Claim.* Once you know *what kind* of failure it is (planning, retrieval, human interaction, first write, delegation),
  the dataset's step is almost fixed by convention: step 0, the fetch step, the first `ask_human`, the first write. So
  the LLM's job is to name the category; the step follows from a rule, and a rule beats the LLM at the step.
- *Why we believe it.* X7 (AgentHallu oracle-category rules 55.8% > best LLM 41.1%; FaP first write 41%; LongRCA first
  delegation 45%; CORRECT-Error seam 74%); AgentErrorBench module-dependent positions; TrajErrBench VERIFY.* late /
  PLAN.* early.
- *How to test.* Cheap: two-stage prompting (category → step) on AgentHallu, AgentErrorBench, TrajErrBench, scored
  against step-first; report every method against the structural prior of its dataset.
- *Method.* Learn P(step | category, landmarks) and use the LLM only for the category.

**H6. Every label set is a mixture of conventions (earliest detectable, decisive, first unrecovered, lock-in, last
chance, acceptance); methods should be scored under each, and "late bias" largely disappears once conventions match.**
- *Claim.* Within one dataset, different annotators (or the same annotator on different runs) applied different rules
  for which link of the chain to label (X2). A method that follows one rule consistently will look "early" on some runs
  and "late" on others, which reads as bias but is a convention mismatch. Scoring under several stated conventions,
  jury-style, separates real localisation errors from convention noise.
- *Why we believe it.* X2; g2 R3 (the judge climbs to the first plausible deviation where annotators chose a later act,
  and picks the last fabrication where TRAIL chose the first recovered bug); HORIZON mixture (27% first anomaly / 26%
  after / 31% before); §2b: the label lands on different pair members in different datasets (WW/MPB omission, ARx
  acceptance/commission) and on none of them in 29–53% of pairs.
- *How to test.* Cheap: derive three conventions from TRAIL (earliest span / earliest HIGH / last fabrication) and
  AgentRx (first vs root) and score the judge under each. Expensive: blind re-labelling of 100 TrajErrBench τ² and 100
  SearchAuditBench cases without the LLM draft or diagnostics (expected <70% / <55% reproduction, skewed earlier).
- *Method.* Output an earliest-deviation step *and* a last-recoverable step (and, per H3, the pair).

**H7. Injected-fault data trains prefix-contradiction detection and last-step priors, not symptom back-tracing; an
attributor trained on it will not transfer to natural failures, and its published accuracy is mostly positional.**
- *Claim.* Because injected steps contradict their own prefix and sit at the end (X8), a model trained on them learns
  "find the step that contradicts what came before" and "guess the last step". Neither helps on natural failures, where
  the error is a non-event that is consistent with its prefix. Reported gains on injected benchmarks are therefore not
  evidence of attribution ability.
- *Why we believe it.* X8; §1 observation 3 (100% local detectability, 75→30 under last-step masking); authorial-voice
  cues; SOAP's reported +8.5 pp on WW-AG vs +0.4 on CE.
- *How to test.* Cheap: seam-stripped CORRECT-Error and last-step-masked WWP evaluation of any published model; a style
  classifier with content masked, transferred to Who&When (expect chance). Expensive: retrain an AgenTracer-style model
  on WWP with and without terminal injections and test on Who&When/TraceElephant.
- *Method.* Use injected data only for the local-consistency channel; gate it on "does this trajectory have symptoms at
  all".

**H8. Score transitions, not observations: the error is in the response to a signal that successes also receive.**
- *Claim.* Since successes receive the same bad signals (X6), the discriminating event is the *pair* (signal at t,
  response at t+1): did the next action change strategy, re-ask, verify, or did it carry on? Scoring the observation
  alone cannot separate recovered from unrecovered signals.
- *Why we believe it.* X6 (FaP same distribution of error events in PASS and FAIL; AgentHallu equal tool-error rates;
  TRAIL outcome-neutral categories); AgentErrorBench "Nothing happens" read as world state in 83% of GPT-4o cases (H1);
  recovery is a paraphrased re-ask (g1 G1-D).
- *How to test.* Cheap: paraphrase detector vs ledger flags on the 102 Magentic logs; prefix monitor scored on FaP PASS
  error events vs FAIL t_err once step text is rejoined (predicted equal flag rates). Expensive: a repair-quality
  classifier on (obs_t, act_{t+1}) trained with PASS recoveries as negatives.
- *Method.* Condition the step score on the preceding observation's error type and on whether the next action changes
  strategy.

**H9. The attributor is a conditional reader of the outcome; without the failure description it invents one, and with
the wrong one it follows it.**
- *Claim.* The judge does not localise "the" error; it localises the error it has been told about (or guesses one).
  Given the right failure description it climbs to the right place; given none it blames something plausible but
  unrelated; given a wrong one it follows it. So the failure description is the main input, not a hint.
- *Why we believe it.* X5 (judge invents failures in 9/40 correct TRAIL runs; TravelPlanner protocol blames 7/14; HC/30
  flips between step 8 and 66 with/without ground truth; TrajErrBench pre-annotators with diagnostics 53–77% vs blind
  detectors 52%); §2b: with the gold given, the classifier identifies the missing item but still matches the label in
  only 28–40%.
- *How to test.* Cheap: All-at-Once with (a) nothing, (b) the evaluator's failure items, (c) a wrong failure description
  on LongRCA TravelPlanner and TRAIL (predict exact rises ≈7→25% with (b) and follows (c)).
- *Method.* Make the failure description an explicit input (verifier output, failing test names, unmet constraint) and
  attribute relative to it; for silent failures (X11) derive the description by simulating the rule (policy clause, DB
  state, file system).

**H10. Exact-step accuracy on orchestrated logs is convention noise below ~5 pp; collapse decision triples and report
±1 as primary.**
- *Claim.* Magentic-One writes one decision as three messages (ledger, instruction, next-speaker) and SymTrace
  duplicates every call into two nodes; different teams label different copies. Differences of a few points in exact
  accuracy on these logs are which copy a method prefers, not better attribution.
- *Why we believe it.* X2 last bullet (ledger/instruction/next-speaker triples; SymFail duplicate nodes 357/536;
  MP-Bench annotator duplication on 19/169 manual logs).
- *How to test.* Cheap: recompute all published Who&When-HC numbers with the collapse (expected +5–10 pp for every
  method, with rank changes).
- *Method.* A decision-unit normaliser before scoring.

**H11. Verifier and claim steps are zero evidence for localisation; treat PASS as absent and FAIL as evidence the root is
elsewhere.**
- *Claim.* Verification and completion claims at the end of a run are produced regardless of outcome (X10). They should
  not be candidates for the step and should not count as evidence; their *absence* (a claim with no verification) is
  the only informative pattern.
- *Why we believe it.* X10.
- *How to test.* Cheap: ablate verifier/judge/claim steps from the judge's input on LongRCA SWE-Pro and TB2 (predict no
  loss, fewer distractors); TF-IDF on the last message PASS vs FAIL (predict AUROC ≈0.6 on FaP vs 0.83 on τ²).
- *Method.* Down-weight verification and completion claims; use their absence (claim without verification: PASS 16.3% vs
  FAIL 28.7% in FaP) as a feature.

**H12. The label-free "normal flow" exists only as task-phase structure, not as content.**
- *Claim.* One-class / anomaly methods assume successful runs define a normal content distribution that failures
  deviate from. At the content level that is false (X6): successes contain the same events. What successes do share is
  a phase order (plan → fetch → write → verify → claim); deviations in phase order or phase skipping are the only
  label-free signal available.
- *Why we believe it.* X6; HORIZON H5 (separation from length and early-stop, not dynamics); SymFail templates; FaP
  first-write prior.
- *How to test.* Fit OAT-style one-class scorers on HORIZON web and AgentHallu successes and check whether step scores
  peak at the first divergent step or at the early-stop tail; compare success-reference and failure-reference scorers on
  the same embeddings (Spearman on pre-lock-in vs post-observation steps).
- *Method.* Model the phase sequence, score deviations in phase order and phase skipping, not in content.

**H13. Hindsight labels are unflaggable by any prefix method; measure the share and give the attributor the hidden state
or exclude them.**
- *Claim.* Some labels mark a step that was wrong only in hindsight (the search order was wasteful given where the
  object turned out to be; the candidate was wrong given a hidden user goal). No method that sees only the prefix can
  flag them, and no method without the hidden state can justify them. Benchmarks should report that share separately.
- *Why we believe it.* The prefix monitor calls the gold "reasonable" in 12/20 AgentErrorBench, 8/20 TrajErrBench τ²
  and 3/20 HORIZON records (g3 R7); AgentErrorBench exploration-order labels (X5); τ² 65.5% symptom-free failures.
- *How to test.* Cheap: split every result by "gold flagged by the prefix monitor" and by "has transcript symptom".
  Expensive: give the attributor the hidden state (object location, user goal, failing test names) and measure the
  jump; the residual is the convention problem of H6.
- *Method.* Evaluate attributors on locally-wrong steps and globally-suboptimal steps separately.

## 4. Annotation issues (stated confidently, with prevalence)

In words: these are defects of the label sets themselves, found by checking the released files. They bound what any
method can score and should be fixed or excluded before comparing methods.

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
- **Single-annotator, outcome-informed SearchAuditBench** (from `notes/searchauditbench_investigation.md`): one
  annotator per case after a Claude pre-screen that saw the gold answer; multi-cause and environment-caused failures
  removed by construction; no agreement figure.

## 5. Literature phenomena P1–P8: verdicts on the data

In words: P1–P8 are the claims the literature makes about why attribution is hard (`lit/known_phenomena.md`); this
table says which ones the data supports, and in what form.

| P | what it claims | verdict | key numbers |
|---|---|---|---|
| P1 downstream contamination | symptoms after the error attract blame | holds for per-step monitors and annotator consensus; **does not hold for the holistic judge**; symptoms are diffuse, not peaked; absent in injected data | monitor after/before flag ratios 2–7×; judge misses later/all ≈ 0.4–0.5 everywhere; LongRCA symptom AUROC 0.50–0.54; WWP post-label symptom rate below WW pre-label rate |
| P2 label is a convention | "decisive step" is operationalised differently by each team | confirmed, with the divergence concentrated on exhaustion / long runs | WW vs ARx 36% exact on shared logs; TRAIL primary ≠ earliest in 58/144; TEB proposal-vs-execution +2 |
| P3 anchoring on outcome / drafts | annotators follow the outcome or an LLM draft | confirmed on every dataset with rationales; the judge is a conditional reader too | LongRCA 146 evaluator quotes; TRAIL gold in 117/117 traces; HC/30 flip |
| P4 outcome-only judges | judges reason from the outcome, not the process | confirmed in a new form: the outcome-*blind* judge invents failures | TRAIL 9/40 correct runs blamed; TP protocol blames 7/14; HORIZON judge-Success runs end with `answer()` 86% |
| P5 length degrades localisation, not agent accuracy | long traces hurt the step, not the agent | confirmed | WW exact 50/32/21% for ≤10/11–30/>30 steps, agent flat 64/63/59; TE 46→20; TRAIL 38.5→7.1 |
| P6 normal-flow premise | successes define a normal distribution failures deviate from | refuted as content, weakly supported as phase structure | FaP PASS 71% with errors; TRAIL 31/34 correct runs with errors; HORIZON separation = length; SymFail 70% template |
| P7 absorption by type | some error types are recovered, others cascade | confirmed | TRAIL category fatality table; ARx recovered = Adherence 25/26, root = Misinterpretation 22/73; WWP recovered injections kept as failures (2/13; CE loop rows decisive=yes 12%) |
| P8 verification theatre / final write | runs end with unearned PASS/claims | confirmed everywhere | LongRCA 97% PASS after root; FaP final claim 70% FAIL vs 71% PASS; MPB 24% unanimous FINAL ANSWER flags |

## 5b. Which ML principles model these problems

See `lit/ml_principles/README.md` (synthesis) and the three cluster notes. In short: the definition of the decisive step
is Halpern–Pearl actual causation with a normality selection rule (exact); loops and ±1 tolerance are Chockler–Halpern
responsibility (exact); what a log can certify is a Tian–Pearl bound on the probability of necessity (exact); label
conventions are labelling functions on a monotone chain and should be scored jury-style (exact for evaluation);
annotators and the holistic judge compute a hindsight distribution while the prefix monitor computes the policy-side one
(exact, explains H13); "no decisive step" is a selective-prediction output space with named reject classes (exact);
omission errors need forward slicing / where-provenance, not backward symptom tracing (exact on lineage logs; now
supported by §2b); "same signal, different fate" is a response-conditional treatment effect and a matched-anchor
contrastive design (exact); injected-data priors are shortcut learning (exact, audit already published for the injected
side) and the transfer failure is task shift, not distribution shift (analogy); silent policy failures and terminal
artefacts are runtime verification (exact), hidden-goal labels are not monitorable (H13). Fourteen no-LLM pilots are
listed there.

## 6. Experiment programme implied by the hypotheses

Cheap (days, this infrastructure):
1. Signed-offset and per-regime scoring for every instrument and dataset (H1, H4, H6); publish the structural-prior
   baseline table (H5, H7).
2. Decision-unit collapse and ±1 re-scoring of Who&When HC (H10); de-duplicated MP-Bench consensus (§4).
3. Claim-vs-evidence check on Magentic ledgers; proposal-vs-execution shift on TrajErrBench; fetch-vs-adopt shift on
   AgentHallu (H2); provenance rule on TraceElephant's 19 runs and AgentHallu claim-support classifier (H3). **Done
   2026-11-02 (§2b): text-free provenance on all loaders and the label-blind pair classifier; next is "either member"
   scoring of the published attributors and a forward tracer prototype.**
4. Outcome-conditioning ablation (none / correct / wrong failure description) on LongRCA TravelPlanner and TRAIL (H9);
   verifier-step ablation (H11); last-step masking and seam stripping on injected sets (H7).
5. Two-stage category→step prompting (H5).

Expensive (later):
6. Blind re-labelling under stated conventions (TrajErrBench τ², SearchAuditBench, 13 Who&When HC exhaustion runs, and
   50 omission→commission pairs under an explicit member rule) (H3, H6).
7. pass^k re-runs with larger budgets on AgentErrorBench / SymFail to identify no-decisive-step runs (H4).
8. Rejoin Failure-as-a-Process step text; score prefix monitors on PASS error events vs FAIL t_err; repair-quality
   transition classifier (H8).
9. OAT-style vs failure-reference scorers on HORIZON/AgentHallu successes (H12); SOAP/EMFA rescoring of the monitor
   curves (H1).
10. Retrain an injected-data attributor with/without terminal injections and test transfer (H7).

## 7. Caveats

- The judge and the shape classifier are one model (Qwen3.8-27B) with one prompt each; sample sizes are 40–184 per
  dataset for the judge, 60–277 for the classifier; prefix probes 10–20 records each. Directions are consistent across
  datasets, magnitudes are not final.
- Close readings are by LLM agents (four group agents) with record ids; the strongest claims (annotation errors, convention
  gaps) were checked against the released files, but a human pass over the cited ids is still needed.
- Trajectories were rendered as text; screenshots (TraceElephant, WWP image splits) were not used.
- The §2b classifier was validated on three hand-read cases only; its "omission step" placement in long runs (last failed
  attempt rather than first) is a prompt choice that a re-labelling study should settle.

## 8. Pending

- §2b is complete (17 datasets). Not yet done: scoring the *published* attributors with the "either member" rule, the
  forward-tracer prototype, and a human check of 20 classifier outputs per dataset (only three hand-read cases verified).
- All judge baselines are complete and summarised in the per-dataset files (§4 or §4b) with reasoning excerpts in
  `results/<slug>/*_analysis.md`. SearchAuditBench exact 40% (CS-Strict; the paper's All-at-Once with Claude Opus 4.8 is
  32.1%, SearchAuditor 39.9%), misses skew *earlier* (14 earlier / 6 later); MemTrace 30% exact on 30 slices, 3 records
  still over the context limit.
- The agents' own readings of the judge's reasoning (≥6 failures / ≥3 successes) exist for Who&When, TraceElephant,
  TRAIL, TrajErrBench, AgentErrorBench, CORRECT-Error and Who&When Pro; for MP-Bench, SymFail, AgentRx, LongRCA, HORIZON
  and AgentHallu only the metric tables and categorised misses were added (§4b), not a read of the reasoning.
