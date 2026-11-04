# G2 — full-trace and long-horizon datasets: cross-dataset synthesis (2026-11-01)

Datasets: TraceElephant (220 runs, LLM-call traces, 3 systems), LongRCA (1,140 runs, median 145 steps, 5 sources), TRAIL (148 span
trees, all errors labelled), SearchAuditBench (1,243 deep-search runs, critical step + tolerance span + root cause), MemTrace (160
memory-system failures, execution-graph slices; spot-check). Per-dataset notes: `findings/datasets/{traceelephant,longrca,trail,
searchauditbench,memtrace}.md`. Baseline = Qwen3.8-27B all-at-once (`baseline/all_at_once.py`), prefix monitor = `inspect/prefix_probe.py`.

Caveat on all LLM numbers: the shared vLLM server was oversubscribed (16 running / 50 queued for most of the session); LongRCA's
baseline is on 21/60 records at the time of writing, SearchAuditBench's numbers are those reported by its fork; memtrace's baseline
had to be restricted to slices ≤ 700 ops because the shared renderer cannot fit 3,661-op slices into 200k tokens.

## 1. Phenomena that recur across the group

**R1. The decisive step is a *decision about* an observation, and the datasets attribute it to whoever's name is on the record, not to
whoever decided.** TraceElephant: 30/90 Magentic-One gold steps are orchestrator ledger calls recorded by the middleware under the
specialist's name (`WebSurfer`), and the human `mistake_agent` follows the recorded name in 218/219 runs; SWE-Agent "agents" are tool
names that mismatch the tool actually called in 225/1,551 calls. LongRCA: the same environmental condition (NYC-named listings in
605/685 TravelPlanner runs, logged-out WebArena sessions in 52/76 Reddit runs) is blamed on six / three different roles depending on
which role *reacted* to it; 55 labels name `Computer_terminal` (the environment). TRAIL: the same malformed `page_down` call is put on
the LLM span in some traces and on the TOOL span in others; TOOL-span evidence is visible in the tool span in only 12/95 cases. MemTrace:
the "faulty op" for Retrieval/Response errors is fixed by (error type, query id), so "who" is an op-type lookup. Agent-level accuracy
on this group therefore measures agreement with an instrumentation convention as much as diagnosis.

**R2. The surface symptoms are after the label, but they do not point at it.** Loops/duplicates: TraceElephant Captain 0% of pre-label
steps vs 39% of post-label steps are near-duplicates, SWE-Agent 4.6% vs 31%; Magentic ledger stall flags fire after the label in 30/59
runs (median +4.5) and *before* it in 24 (median −13). LongRCA: tool errors / FAIL verdicts / `passed:false` / problem words occur at
the same per-step rate before and after the root (AUROC 0.50–0.54 in every source); the first judge FAIL is >100 steps after the root
and about another bug. TRAIL: prefix monitor flags 54% of post-gold vs 17% of pre-gold LLM steps. So P1's first half ("symptoms are
louder downstream") holds for loops and monitors, but the symptoms are *diffuse* (constant-rate retries, long loops) rather than a
peak one can back-propagate from; the thing that separates root from non-root is outside the trajectory (hidden tests, evaluator rule,
gold answer), not a louder downstream step.

**R3. The full-context LLM judge is not late-biased; it is *convention*-biased in both directions.** Signed offsets of misses:
TraceElephant 38 earlier / 22 later (Captain 16/6, SWE 8/2, Magentic 14/14); LongRCA partial 7/7; TRAIL std 13 earlier / 16 later,
inventory 18/11. The judge, told to find the "earliest decisive" step, climbs to the first plausible deviation (first search query,
facts/plan step, first edit) where annotators chose a later act, and on search/fabrication runs it chooses the last fabrication where
annotators (TRAIL) chose the first recovered formatting bug. Literature hypothesis 1 ("≥60% of misses land after gold") is refuted for
the all-at-once judge on this group; what is confirmed is P2 (the label is one of several defensible steps and the judge's convention
differs from the annotators').

**R4. Labels are hindsight-derived from information no auditor sees.** LongRCA: 146 rationales quote the evaluator verdict and "work
backwards"; 22/170 SWE/TB2 cite hidden tests or the gold patch. TRAIL: the GAIA `true_answer` is literally in step 2 of 117/117 traces
(so every annotator, judge and prefix monitor is outcome-informed), and HIGH-bearing traces are 88% of wrong vs 68% of correct runs.
TraceElephant: labels are "earliest after which failure is inevitable", which is only decidable with the ground truth (gaia_task_102:
step 0 guess "Bad" is wrong only because GAIA counts Thriller as the sixth album). SearchAuditBench: see §3 (which root causes need
the gold answer). MemTrace: the label is the op where the *gold evidence* leaves the data flow, so it requires the evidence. P3 confirmed
on every dataset of the group; the practical consequence is that an attributor without the failure description guesses the
criterion and blames protocol violations (LongRCA H-L8: 7/14 TravelPlanner predictions blame the completion-token protocol, 0 gold
labels do; TRAIL: the judge invents a failure in 9/40 correct-ending runs).

**R5. "Successes" are inside the failure sets and errors are inside the successes.** TRAIL: 34/117 GAIA runs end correctly yet 31 carry
errors and 23 carry a HIGH; TraceElephant: gaia_task_6 answers the GT and is a labelled failure; LongRCA: ≥6 VitaBench rationales say the
agent was not at fault, 5 TravelPlanner tasks contradict themselves (NL vs structured constraint); SearchAuditBench filtered evaluator
false negatives before release. P6 (normal-flow premise) is refuted where testable (TRAIL); P7 is confirmed in TRAIL's category table
(formatting/instruction/orchestration errors are outcome-neutral, P(correct)=0.28–0.29 vs base 0.29; retrieval 0.13 and tool-hallucination
0.17 cascade).

**R6. Verification theatre and the final write are the dominant late labels.** LongRCA: 97% of SWE-Pro runs end with a JudgeAgent PASS
issued after the root; 217/320 TravelPlanner runs with a `passed:false` verifier still terminate as complete; 140 TravelPlanner roots are in
the last 6 steps. TRAIL: 46/117 GAIA primaries are the manager's final LLM call. TraceElephant: Captain 15/85 labels are final-answer
turns, Magentic assistant_bench_task_2 fabricates the final number after 45 failed navigation steps, SWE-Agent ends with an "ok"
reproduction run in 30/38 runs that have one. SearchAuditBench: critical = final answer in 17% (Unsupported Answer / Constraint Neglect
by construction). MemTrace: Response errors (34/160) are the last op by definition. P8 confirmed everywhere.

**R7. Structural priors are strong because the label is a convention.** First `DiagnostAgent (-> ActionAgent)` delegation = 45% exact on
LongRCA SWE-Pro (paper's best method 24% overall); first CodeAgent action span = 40% on TRAIL GAIA (judge 31%); first source edit = 41%
on TraceElephant SWE-Agent; last query-bearing retrieval op ≈ 70/140 on MemTrace; "last assistant step" is a non-trivial CS-Loose
baseline on SearchAuditBench. Any method must be reported against these.

**R8. Errors of omission dominate and are invisible in the step itself.** TraceElephant reason texts: 34% omission + 11% outcome-only;
LongRCA VitaBench 70% "ignored a request"; MemTrace: 20/160 faulty ops have no dependency path to the output (deleted / never-extracted
facts), long_context Update errors are one of ~459 identical ops; TRAIL: the unlabelled root in 2c77a8fe/041b7f9c is "printed the task
instead of calling search_agent". Content-only scorers are bounded by this; what identifies the step is the *expected* flow (the task
constraint, the gold evidence, the plan item) that the step failed to carry forward.

## 2. Phenomena that differ between datasets, and why

| phenomenon | where it holds | where it does not | why |
|---|---|---|---|
| loops after the label | TraceElephant Captain/SWE, TRAIL page_down series, LongRCA SWE repro loops | Magentic-One (observations differ each step), MemTrace (no loops) | loops need a cheap repeated action with identical output; browsing systems vary the observation |
| late bias of the judge | TRAIL search-agent runs (+22 median), LongRCA TravelPlanner late writes picked early | Captain/SWE (judge earlier), memory-answer runs | the judge's "earliest plausible" rule vs the annotators' "first HIGH / first commit" rule |
| environment faults inside the failure set | LongRCA TP/WA/Vita (≥60% of TP runs), TRAIL infeasible-tool tasks | TraceElephant SWE, MemTrace | benchmarks with simulators / relabelled data / unavailable modalities |
| agent label = instrumentation artefact | TraceElephant Magentic (33%), SWE-Agent tools | LongRCA (roles are real), SearchAuditBench (single role) | tracing by thread/agent_id vs by prompt owner |
| localisation trivial given the type | MemTrace Retrieval/Response (110/160), TRAIL memory runs (37/117 → step 8) | LongRCA TravelPlanner, SearchAuditBench mid-trajectory | fixed pipelines make the faulty op a lookup; open-ended agents do not |
| gold answer available to the auditor | TRAIL (leaked), TraceElephant (metadata), MemTrace (golden_answers) | SearchAuditBench (hidden by design), LongRCA (hidden evaluator rules) | benchmark design; accuracy gaps between these settings measure R4 |

## 3. Ranked hypotheses for the group

1. **G2-H1 Attribute to the prompt owner, not the record owner** (TraceElephant H-TE1; LongRCA H-L1 "condition → reaction"; TRAIL H4).
   Statement: in orchestrator-led and tool-mediated systems the decisive step is the decision that accepts/forwards a wrong observation;
   datasets that attribute by thread or by reacting role mislabel the agent in ~30% of multi-agent runs. Test: re-derive the actor from
   `input.messages` (whose system prompt produced the call) on TraceElephant and re-score agent accuracy; two-stage "environment
   condition present → first decision that proceeds despite it" scorer on LongRCA TP/WA. Expensive part: re-annotation of 50 runs.
2. **G2-H2 The judge's late bias is a myth on long traces; the measurable effect is a convention mismatch with sign that depends on
   trace type** (TraceElephant §4, TRAIL H3, LongRCA §4.1). Test: score every method under three gold conventions (earliest plausible
   deviation, first commit/HIGH, last unrecovered fabrication) and report per-convention accuracy; predict that each method is near its
   own convention and that "late bias" disappears once the convention is matched. Cheap: labels for the three conventions can be
   derived from TRAIL (earliest span / earliest HIGH / last fabrication) and AgentRx (first vs root).
3. **G2-H3 Without the failure description the auditor invents one** (LongRCA H-L8, TRAIL 9/40 invented failures, SearchAuditBench
   no-gold design). Test: All-at-Once with (a) nothing, (b) the evaluator's failure items / gold answer, (c) a wrong failure description;
   predict exact accuracy on TravelPlanner rises from ≈7% to >25% with (b) and that (c) moves predictions to the step consistent with the
   wrong description — i.e. the attributor is a conditional reader of the outcome, not a detector.
4. **G2-H4 Forward-trace the expected flow instead of back-tracing symptoms** (MemTrace H-MT1, TraceElephant H-TE5 seen-but-dropped
   answers, TRAIL H2 recovered errors). Statement: the root is the first step where a required item (gold evidence, plan constraint,
   candidate entity) stops being carried forward; backward tracing from the failure cannot reach deletions (20/160 MemTrace), dropped
   candidates (19/176 TraceElephant runs have the GT visible before the label) or constraints never checked. Test: implement a
   forward tracer on MemTrace (string/embedding) and score the 50 Update/Extraction cases; on TraceElephant, predict gold = last step
   containing the GT string + 1 for the 19 runs.
5. **G2-H5 Recovered errors must be demoted, but the datasets disagree on whether they are errors** (TRAIL H2: primary = recovered
   formatting bug in ≥5 read traces; LongRCA 21% FAIL-then-PASS judge sequences = recovered side bugs; TraceElephant stall flags that
   precede the label by 13 steps). Test: a recovery detector (same tool/goal later succeeds) applied before scoring; predict it moves
   TRAIL predictions later and LongRCA predictions earlier, improving both only under an "unrecovered" convention.
6. **G2-H6 Verifier output is zero evidence; treat PASS as absent and FAIL as evidence the root is elsewhere** (LongRCA H-L3, TraceElephant
   §3d' false-success reproductions, TRAIL manager "verified" claims). Test: ablate verifier/judge steps from the attributor's input;
   predict no loss (and a gain from fewer distractors) on SWE-Pro/TB2.
7. **G2-H7 Localisation is free when the pipeline is fixed; the task is typing** (MemTrace H-MT2, TRAIL memory-answer runs, LongRCA
   first-delegation prior). Test: report accuracy conditioned on the structural prior firing; predict method gains concentrate in the
   open-ended remainder.
8. **G2-H8 Fix-before-reproduce / unverified presupposition is the detectable early anomaly in coding and search runs** (TraceElephant
   H-TE3/H-TE4: 34/44 SWE runs edit source without a failing reproduction; facts-step guesses copied into every query). Test: count
   runs with a failing repro before the first source edit in TrajErrBench-SWE / TRAIL-SWE; predict the labelled edit is within 3 steps of
   the first "edit without failing repro" in >50%.

## 4. P1–P8 verdicts with numbers (group level)

- **P1** (downstream contamination): symptoms after the label — confirmed for loops (Captain 0%→39%, SWE 4.6%→31% duplicate rate) and
  prefix monitors (TRAIL 17%→54% flag rate); refuted as a *judge* bias (TraceElephant misses 38 earlier / 22 later; TRAIL 13/16; LongRCA
  7/7) and refuted as a surface signal on LongRCA (AUROC 0.50–0.54).
- **P2** (conventions differ): confirmed — TRAIL primary ≠ earliest span in 58/144 (median 5 spans); TraceElephant label vs judge
  disagree in both directions on 60/90; LongRCA SWE-Pro root = first delegation in 45%; TE–WW same-task pairs share a mechanism in 2/85
  (so cross-run agreement is not a convention test at all).
- **P3** (anchoring on the outcome): confirmed — LongRCA 146 evaluator-quoting rationales, 49% of rationales name a role absent from
  the trace; TRAIL gold leaked in 117/117 traces, HIGH-bearing 88% wrong vs 68% correct.
- **P4** (outcome-only judging): confirmed in a new form — the outcome-blind judge invents failures (TRAIL 9/40 correct runs; LongRCA
  7/14 TP protocol blames).
- **P5** (length): confirmed — TraceElephant exact 46% (11–30 steps) → 20% (>30); TRAIL 38.5% → 7.1%; LongRCA 3/21 truncations.
- **P6** (normal flow): refuted where testable — 31/34 correct TRAIL runs carry errors; TraceElephant/LongRCA have no successes.
- **P7** (absorption by type): confirmed — TRAIL formatting/instruction/orchestration errors outcome-neutral, retrieval/hallucination
  errors cascade; LongRCA judge FAIL-then-PASS 21% = absorbed side bugs; MemTrace 20/160 omissions are "absorbed" from the graph's view.
- **P8** (verification theatre / false success): confirmed — LongRCA 97% PASS after root, 92% completion claims; TraceElephant SWE 30/38
  final "ok" repro runs; TRAIL 46/117 final-call primaries; SearchAuditBench 17% final-answer criticals.

## 5. What was skipped or limited

- LongRCA baseline: 21/60 records at time of writing (server); the full run continues in the shared chain. Reason classification on a
  100-record sample instead of 1,140.
- MemTrace: baseline restricted to slices ≤ 700 ops (the shared renderer cannot fit the longest slices); no prefix probe (steps are
  operations, not agent decisions); the slice-pollution loader issue is documented, not fixed.
- TraceElephant: inventory variant pending in the shared chain; prefix probe on 12 runs ≤ 60 steps.
- No vision: screenshots in TraceElephant were not rendered, so "does full observability change the label" is answered only for text.
