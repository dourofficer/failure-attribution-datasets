# Worklog: inspecting the failure-attribution datasets (started 2026-10-31)

Running notes, in order of discovery. Synthesised hypotheses go to `hypotheses.md`.
Infrastructure: `vllm/serve.sh` (Qwen3.8-27B, GPU 5, port 8210, 200k ctx), `common/llm.py` (cached client),
`loaders/` (unified schema, see SCHEMA.md), `baseline/all_at_once.py` (+ `score.py`), `inspect/` (ad-hoc analyses).

## 2026-10-31

- AgentRx raw annotations (`data/agentrx/github/data/ground_truth`): root ≠ earliest event in 2/29 τ-bench and 17/44
  Magentic-One trajectories. Reading the cases: the earlier events are NOT "errors that got corrected" in most of them;
  they are the *specialist's* failure (WebSurfer reads 18% / 9% / 42% of a page) and the root is the *orchestrator's
  acceptance* of the incomplete result one or two steps later. So AgentRx's "first unrecoverable failure" convention
  moves blame from the producer of bad information to the consumer that failed to check it. Who&When's convention
  does the opposite. Example 5f982798: Who&When step 3, AgentRx step 33 (FileSurfer opens a hallucinated placeholder
  path `path_to_july_2020_paper.pdf`); in between, 30 steps of a WebSurfer that never manages to read the PDF
  (step 13: clicked PDF, OCR shows only "2103.07786"; step 17: "Nothing to summarize"), with the orchestrator ledger
  flagging is_in_loop=true at step 18. Two defensible roots 30 steps apart in one 67-step log.
- MP-Bench raw votes (3 annotators): in 88/157 manual and 46/120 automatic logs at least one annotator flags a step
  EARLIER than the first majority (>=2 votes) step; 291 such minority-early flags in the manual set. These are the
  "plausible but not consensus" early errors. (Category breakdown below.)
- Who&When reasons rarely mention recovery (12/184 match lifecycle keywords, mostly "subsequent steps" propagation
  language). LongRCA reasons are long narratives: 731/1140 match; many explicitly say "after correcting X, the agent
  then ..." or "subsequent fixes also failed" -> LongRCA's labelled root often sits AFTER a recovered error and
  BEFORE a sequence of failed repairs. TraceElephant reasons (33/220) are mostly "did not do X first / early enough".
- MP-Bench category split: MAJORITY-flagged steps are Verification 19%, Planning 17%, Reasoning 16%, Reasoning-Action
  Mismatch 10%; MINORITY flags that precede the first majority step are Planning 26%, Tool/Agent Invocation 17%,
  Contextual 16%, Reasoning-Action Mismatch only 2.6%. Annotator 2 produces 224 of the 380 early minority flags.
  Reading: consensus follows *locally verifiable* wrongness (a stated action that visibly did not happen, a wrong
  inference from visible evidence); early "could have planned better / should have used another tool" judgements do
  not get consensus. Median gap between an early minority flag and the first majority step: 4 steps (p90 37).
- SearchAuditBench case 277 (Quest-35B, xBench): at msg 4 the agent *hallucinates* the rank-2 fouls player
  (Nurkić/Portland) before visiting any page; at msg 7 it reads basketball-reference and corrects itself to
  Giannis/MIL. Textbook recovered early error. The annotated critical step is msg 8 ("turns a single leaderboard
  result into a settled binding") although the visited page lists Giannis as #2 and the agent's downstream computation
  (22) is consistent with that page; the gold (7) comes from a different rank-2 player. The rationale is written
  backwards from the gold: the step blamed is where the agent's path diverged from the path that reaches the gold,
  not a step that was wrong given its evidence. -> hindsight labelling.
- "Is the gold answer string visible in the log?" (exact normalised substring, short/numeric gold skipped):
  Who&When HC 6/49 usable, AG 5/81; TraceElephant 23/123; AgentHallu 27/319; SearchAuditBench 211/1,002 usable,
  and in Candidate Mismanagement 68 of 71 visible cases the gold appears BEFORE OR AT the critical step (the agent saw
  the right candidate and discarded it). Consistent with fa_ideas' note that Who&When is not a retention benchmark;
  SearchAuditBench partly is.
- Magentic-One ledger self-monitoring vs Who&When HC label (58 logs): is_in_loop fires in 36 logs, BEFORE the label
  in 14 (as early as 65 steps before), after in 22 (median +8); is_progress_being_made=false similar; "Stalled...
  Replanning" fires in 25 logs, almost always after the label (23/25, median +22). The system's own flags are a lagging
  symptom detector with large variance, not a cause pointer; and in 14 logs the human label sits AFTER the system
  already declared itself looping (e.g. 3.json: loop flagged at 21, label at 32).
- Who&When HC 3.json read in full (93 steps): the WebSurfer scrolls the APOD archive one viewport (1%) at a time at
  steps 16/20/24/28/32, identical actions; the orchestrator repeats "continue scrolling" at 22/26/30; label = step 32
  = the LAST scroll before the orchestrator changes strategy at 33/34. Nothing distinguishes step 32 from 20, 24, 28
  except that the pivot follows it. Within a homogeneous repeated block the exact-step label is arbitrary; the natural
  unit is the block (or the instruction that started it, step 22, an orchestrator step). The run reaches the right
  page (ap150801.html) only at step 92, i.e. the "decisive" error is 60 steps before the system recovers the path.
- Rationale tags (LLM-tagged, inspect/tag_reasons.py, 2,060 rationales): share of rationales that are GENERIC
  (no run-specific evidence): Who&When 48% (AG 52%, HC 41%; e.g. "The code is wrong.", "The searching result is
  wrong."), TraceElephant-Magentic 25%, LongRCA 1%. USES_GROUND_TRUTH: LongRCA SWE-bench Pro 57% ("working backwards
  from the four failing tests"), AgentHallu 45%, VitaBench 30%, Terminal-Bench 29%, AgentRx 29%, Who&When 12%.
  LATER_REPAIR_FAILED: WebArena 29%, Terminal-Bench 29% (the lock-in regime). EARLIER_ERROR_RECOVERED mentioned in 4% of
  LongRCA rationales (8% WebArena) and ~0 elsewhere; explicit examples: swe_bench_pro__093 ("the initial delegation plan
  in step 37 does contain obvious flaws ... these problems were later discovered and fixed" -> label at 399).
  BLAMES_ENVIRONMENT: TraceElephant-Magentic 23%, Who&When HC 17%, AgentRx 14%. SYMPTOM_ONLY: Who&When 19%.
- Repetition blocks (inspect/repeat_blocks.py, loose matching): LongRCA 84% of runs contain a block of >=3 near-identical
  same-agent actions; 18.7% of all agent steps are repeats; the label sits inside such a block in 233/1140 (first of
  block 60, last 13, elsewhere 160). Who&When: 3% repeats, blocks in 15% of logs (mostly HC).
- Observation-side signals (inspect/obs_signals.py; labelled step vs a random decision step of the same run):
  the labelled step is NOT more often preceded by an error/empty observation than a random step (TrajErrBench 10% vs
  8%, SearchAuditBench 12% vs 14%, LongRCA 8% vs 9%, Who&When 6% vs 12%). It is LESS often a retry of the previous
  same-agent action (LongRCA 3.7% vs 14.4%, TrajErrBench 12% vs 16%): annotators label the first novel decision, not
  the repeats. It is MORE often the last decision step (LongRCA 8.2% vs 1.7%, SearchAuditBench 15.7% vs 7.8%,
  AgentErrorBench 14.6% vs 8.5%). The observation right AFTER the labelled step is slightly more often an error
  (Who&When 19% vs 13%, LongRCA 13% vs 10%): the label tends to sit where the consequence first shows.
- Repetition (loose matching, digits normalised, so ALFWorld "go to drawer 1/2" over-merge - caveat): AgentErrorBench
  78% of decision steps are repeats and 98.5% of the steps after the label are; TrajErrBench 40% / 54% after label;
  LongRCA 23% / 18%; SearchAuditBench 9%; AgentHallu 8%; Who&When 11%.
- Loader-stage label-quality findings (from the per-dataset parsing reports, verified where marked *):
  * TraceElephant Magentic-One: 40 of the 90 labelled steps are LLM calls whose OUTPUT is the orchestrator's progress
    ledger JSON, and 36 of them carry a specialist's agent_name (WebSurfer 30, FileSurfer 5, Coder 1) because the
    middleware names the call after the next speaker. The gold "who" on those rows is the name of the call, not the
    role that produced the text. An attributor reading content will answer "Orchestrator" and be scored wrong.
  - Who&When: 6 logs where mistake_agent != agent of the labelled step (HC/20, HC/22, HC/49, AG/14, AG/15, AG/59);
    2 labels on Computer_terminal tool steps; 20 AG labels on step 0; 6 labels on orchestrator instruction steps.
  - LongRCA: 60 labels on tool-role Computer_terminal records (55 blame Computer_terminal itself); 9 agent mismatches.
  - AgentRx: magentic 08cae58d has all 28 WebSurfer events pointing at the 'Orchestrator (-> WebSurfer)' instruction
    steps (systematic off-by-one); 9 root causes on user-role steps (tau 'User' blamed 8x); 2 agent mismatches.
  - AgentErrorBench: GPT-4o_003_memory GAIA labels turn 3 of a 1-turn run; 27 empty failure types; 8 'step_limit'
    labels on the last turn. TrajErrBench: one label on a tool message; 17 null types.
  - Who&When Pro: injection flags inside the raw trajectory coincide with the label in 100% of flagged rows (leak).
- * Verified the TraceElephant artefact on assistant_bench_task_10 step 10: agent_name=WebSurfer, output = the
  orchestrator ledger JSON whose instruction says "Search ... in the Ensembl Release 102 archive"; the human reason
  blames "targeting Release 102 instead of 101", i.e. the orchestrator's decision, labelled WebSurfer.
- Position/role priors (inspect/priors.py; "decision" = agent step that is not bookkeeping): label in the first 3
  decisions: Who&When 50%, AgentHallu 63%, MP-Bench 42%, AgentErrorBench 31%; in the last 3: Who&When Pro 78.5%
  (last decision alone 48%), SearchAuditBench 33%, AgentHallu 50% (short runs: both ends). Majority-agent prior for
  "who": Who&When 18% (WebSurfer), TraceElephant 26%, AgentRx 32% (Assistant), TrajErrBench 79%, single-agent sets 100%.
  So "who" is only a real task on Who&When / TraceElephant / MP-Bench / LongRCA / Aegis; elsewhere it is given or a prior.
- AgentRx vs Who&When on the same 44 Magentic-One logs (both 0-based over the same message list): root == W&W step in
  16/44; within ±3 in 25/44; the W&W step is one of AgentRx's annotated failure EVENTS (any, incl. recovered) in only
  27/44 and within ±1 of an event in 30/44 -> in a third of the logs the Who&When decisive step is not a failure event
  at all for the AgentRx annotators. Agent agrees in 27/44. Signed difference median 0 but range -70..+32.
- Who&When Pro surface tell: injected steps are much SHORTER than ordinary decision steps of the same framework (median
  chars, injected vs other): MacNet 743 vs 2463, smolagents 742 vs 1571, MathChat 502 vs 1525, Magentic-One 336 vs 270,
  ALF-Agent 385 vs 130 (longer). The injector (the base agent under an injection prompt) writes terse wrong steps.
- MP-Bench (3 annotators) vs Who&When on the 177 shared logs: first-majority step == W&W step in 99/176 (56%), within
  ±3 in 128 (73%); the W&W step received 3 votes in 87 logs, 2 in 48, 1 in 16 and 0 in 26 -> for 42 logs (24%) at most
  one of three fresh annotators considers the published decisive step a failure step at all. When they disagree the
  MP-Bench majority is EARLIER (54) more often than later (23).
- Who&When Pro shortcut (inspect/wwpro_length_shortcut.py, direction learned on half, scored on the other half):
  predicting the shortest/longest decision step gives exact-step accuracy MacNet 87%, MathChat 86%, DVD 79%,
  smolagents 52%, overall 49% (random 30%); the last-decision prior alone gives 48% overall (smolagents 52%, MathChat
  80%, Magentic-One 56%). The paper's best all-at-once step accuracy is 72% (text); a large part of it is reachable
  without reading.
- LongRCA: the 60 labels on tool-role records are mostly (55) "Delegated agent finished with result: ActionAgent
  finishes task with STATUS: SUCCESS ..." relays, i.e. the nested agent's self-report delivered through
  Computer_terminal; 5 are evaluator records. The blamed "Computer_terminal" (55x) is the messenger of a false
  success claim, which the role-level label cannot express.
- Injected / taxonomy loaders (group B reports): CORRECT-Error: 1,112 of 2,226 labels on the LAST step (50%), 43 on the
  user message (step 0), 30 on CodeExecutor tool steps, 186 rows name an agent that is not the sender of the labelled
  step. TracerTraj: 471 labels on the last step, sender == mistake_agent in 100%. Aegis MacNet is_injected flags mark
  turns of agents that are not in the faulty set (2,420 of 13,446 flagged turns), so the flags are not a step label.
  SymFail: 102 of 536 failure nodes are the Magentic-One echo of the task (agent_id 'user'), 98 are the final node.
  MAST: trace_id not unique (206 values for 1,642 records); 32 traces unparsable; 5 ProgramDev-v2 traces have an empty
  task. TRAIL: 4 traces with no error, 38 without a HIGH-impact error; outcome derivable for 22 GAIA traces.
- Failure-as-a-Process annotations (1,184 FAIL / 610 PASS): 637 FAIL runs (54%) contain recovery ATTEMPTS; awareness:
  never aware 59%, aware-but-wrong-fix 35%, abandoned 4%, too late 2%. Fix window >=3 steps in 44%, >10 in 20%.
  Environment-obstacle triggers have the most recovery attempts (75%) and the longest fix windows (median 2.5).
  PASS runs: 433/610 (71%) contain error events, max detour median 3 steps (p90 15), 52 near-misses, 39 suspicious
  passes. Forewarning signals before lock-in in 62% of failures.
- TRAIL: 20 of the 22 GAIA traces that end with the correct answer carry error spans, including 45 HIGH-impact errors;
  Formatting / Task Orchestration / Tool Selection errors are over-represented in correct runs, Tool Output
  Misinterpretation and Poor Information Retrieval under-represented. "Impact" in TRAIL is a severity judgement
  decoupled from outcome.
- AgentRx event categories: non-root events are overwhelmingly Instruction/Plan Adherence failures (192 non-root vs 11
  root; 25 of them BEFORE the root), whereas the root is Misinterpretation of Tool Output (22 root vs 9 non-root). The
  recoverable/ignored early errors are the specialists' partial compliance; the decisive one is the consumer's
  misreading. Category texture for H1 and H2.
- AgentErrorBench, first 72 baseline rows: the model predicts EARLIER than gold in 63% (median -4 steps). Reading the
  cases: (a) the 8 'system.step_limit' gold labels sit on the LAST turn with the reason "apple was still not found at
  the end of the task due to the step limit" -- these are symptom labels, not causes; the model blames the initial
  search strategy at turn 1, which is the only defensible cause. (b) 'plan.inefficient_plan' labels sit at the turn
  where the annotator thinks the strategy should have changed (after several repeats), the model blames the first
  wrong assumption ("desklamp is likely on desk 1"). Both are the earliest-vs-decisive convention gap, and (a) is a
  label error by the dataset's own definition.
- SearchAuditBench tolerance spans: 75.5% of the 1,243 spans contain more than one assistant decision (2: 430, 3: 323,
  4: 146, 5-6: 40). The dataset's own protocol concedes that two to four adjacent decisions are "equally defensible"
  critical steps (see next line for whether they are repeats or distinct decisions).
  Of the 939 multi-decision spans only 16 contain adjacent near-duplicate decisions; the critical step is the FIRST
  decision of its span in 528, the last in 240, in the middle in 171. So the "equally defensible" steps are distinct
  actions (search -> visit -> commit) that implement one wrong line of reasoning: the unit annotators are actually
  uncertain about is an EPISODE, not a repetition block. H3 should be stated as "episode boundaries", with repetition
  blocks the special case seen in ALFWorld / LongRCA.
- Reading-free rule baselines (inspect/rule_baselines.py; exact / ±3 %):
  | dataset | first | last | longest | shortest | random | published best LLM (exact) |
  | Who&When | 12.0/51 | 10.9/39 | 22.8/56 | 9.8/52 | 19.6/57 | 12.5 AG / 5.3 HC all-at-once (GPT-4o) |
  | TraceElephant | 5.5/18 | 2.3/22 | 5.9/38 | 6.4/45 | 7.8/40 | 33.3 dynamic agentic |
  | MP-Bench (first majority) | 11.0/46 | 8.0/26 | 17.4/48 | 7.2/42 | 11.0/47 | nDCG task |
  | LongRCA | 2.2/5 | 7.7/14 | 5.3/13 | 0.3/5 | 2.1/8 | 24.1 RCTA |
  | AgentRx | 5.5/23 | 15.1/25 | 5.5/26 | 5.5/18 | 8.2/34 | 36-43 AgentRx |
  | Who&When Pro | 14.0/81 | 47.9/85 | 14.5/92 | 46.2/88 | 31.1/88 | 72.3 GPT-5.4 |
  | TrajErrBench τ² | 5.0/8 | 7.5/15 | **45.8/62** | 4.0/27 | 10.0/26 | 52.8 TrajDebug / 52.5 Gemini direct |
  | TrajErrBench SWE-Pro | 1.2/2 | 1.2/4 | **18.6/22** | 0.0/5 | 5.8/9 | 24.4 TrajDebug / 17.4 direct |
  | AgentErrorBench | 9.0/23 | 14.6/17 | 6.5/16 | 12.1/26 | 8.5/18 | 45 AgentDebug / 28 direct |
  | SearchAuditBench | 5.1/12 | 15.7/27 | 18.0/28 | 3.1/19 | 7.2/20 | 39.9 SearchAuditor CS-strict |
  | AgentHallu | 25.3/72 | 4.7/66 | **28.4/81** | 7.2/73 | 18.1/80 | 32.7 GPT-5 / 41.1 Gemini |
  | SymFail (node) | **40.4/82** | 15.5/49 | 33.5/77 | 18.4/70 | 17.2/67 | n/a |
  | TracerTraj | 5.8/48 | 11.7/47 | 9.9/59 | 12.7/62 | 13.4/65 | 18.9-57.6 AgenTracer |
  | CORRECT-Error | 18.0/48 | 50.0/61 | 22.9/68 | **50.8/78** | 26.5/63 | 30-80 CORRECT Acc@1 |
  | TRAIL (earliest HIGH) | 0.0/46 | 3.2/44 | 7.4/58 | 16.8/51 | 13.7/55 | Loc 0.55 Gemini |
  The LONGEST decision step is a competitive attributor on natural single-agent sets (τ²-bench 45.8% exact, within 7
  points of the best published method; SWE-Pro 18.6% above the direct-prompting baselines; AgentHallu 28.4% within 4
  points of GPT-5; Who&When 22.8% above every prompting number in the paper). The decisive step is textually heavy:
  it is where the agent explains, commits or writes the large artefact. Shortness is the tell on injected sets
  (CORRECT 50.8%, Who&When Pro 46.2%). Random ±3 is 40-88% on the short sets, so ±k windows on them are near-trivial.
- Why "longest" works on τ²-bench: the gold step is a plain message (316/385) and its length rank among decisions is
  median 2 (p75 3); it is the longest in 183 cases, concentrated in reason.* labels (131/238) -- the message where the
  agent summarises what it found and commits to a (wrong) policy reading ("Here's what I found ... I can help cancel
  this since ..."). The decisive step is the COMMIT step, and commit steps are long.

### Baseline results (Qwen3.8-27B, all-at-once, no gold, no thinking)
- AgentErrorBench (199): exact 24.0, ±3 42.9 (paper: direct prompting 28.0 avg with GPT-4.1, AgentDebug 45.0).
  Prediction EARLIER than gold in 63%, later in 13% (median -2). By category: system.environment_error 71% exact,
  action.* 60%, reflection.progress_misjudge 50%; plan.inefficient_plan 8% (earlier 88%), planning.inefficient_plan 0%,
  memory.over_simplification 11% (earlier 83%), plan.constraint_ignorance 11% (earlier 89%), system.step_limit 0%
  (earlier 100%, the symptom labels). Locally verifiable categories are easy; judgement categories pull the model to an
  earlier step than the annotator chose. Gold inside a repeat block: 131/196; when the prediction misses, it lands in the
  SAME block in 82 of 131 (and is then ±3 in 49%). ALFWorld 18% exact, WebShop 28%, GAIA 33%.
- Who&When (184): agent 60.9, exact 43.5, ±3 67.4 (AG: 51.6 / 80.2; HC: 25.9 / 39.7). Paper's GPT-4o all-at-once
  with gold: 12.5 (AG) / 5.3 (HC); AgenTracer-8B with gold 42.9 / 20.7. A 27B open model without the gold and with the
  "corrected later is not decisive" sentence in the prompt is already above the published prompting numbers, so the
  published step accuracies understate what prompting does today. HC misses are later than gold (40%) as often as
  earlier (35%); on logs >100 steps exact is 10%. Rationales tagged symptom-only (30) are the EASIEST (66.7% exact):
  a symptom label is what a reader finds first. Gold agent Orchestrator: 16.7% exact, 44% agent; WebSurfer 36% / 67%.
- H11 test on the 177 Who&When logs re-annotated by MP-Bench: baseline exact accuracy on Who&When labels that all 3
  MP-Bench annotators also flagged = 52.9% (±3 79%); 2 votes = 50.0%; 1 vote = 18.8%; 0 votes = 15.4% (±3 23%). On
  the 0-vote logs the model's chosen step is itself flagged by at least one MP-Bench annotator in 54% of cases and by a
  majority in 38%. The model fails mostly where the label is contested; "accuracy" there is agreement with one
  annotation team against another.
- SymFail (536): exact 31.7, ±3 80.2. CrewAI 75.5% exact (5-node graphs, label almost always the single agent action);
  Magentic-One 14.4% exact but 85% ±3 -- 102 of its 181 labels sit on the framework's echo of the task (role user) where
  no attributor will point (0% exact, prediction always later); AG2 2.9% exact (82 labels on the final_result node, the
  model goes earlier in 73%). The dataset's node convention, not the content, decides the score; C4 (plan-action-outcome
  inconsistency, locally verifiable) 48.9% exact vs C3 (unresolved runtime condition, i.e. environment) 16.3%.
- AgentRx (73): exact 31.0, ±3 54.9, agent 64.8 (paper: W&W-style prompt 18.8/22.7 step, AgentRx method 42.7/36.4).
  τ-retail 53.6% exact, Magentic-One 16.3%. Root-is-not-first-event logs 16.7% exact vs 35.8% when the root is the
  first event. Gold Orchestrator 9.1% exact (model later/earlier 45/45), gold User (under-specified intent) 0%.
  Prediction vs the full event list: the prediction is an annotated event (any) in 34/71, but only 4 are earlier
  (recovered) events; of the 28 predictions before the root, 24 are steps the annotators did not mark at all.
  Those 24 unannotated early picks: 8 are orchestrator ledger/thought steps and 8 have an annotated specialist event
  within the next 2 steps -- the model blames the decision/instruction that precedes the annotated execution failure
  (H7), and on τ-retail it blames the first policy misstatement (7) while the annotator waits for the consequential
  one. The recovered annotated events themselves attract the model only 4 times: on AgentRx the early-bias is an
  instruction-vs-execution convention more than a recovered-error trap.
- TracerTraj agentic/test (150 sampled): exact 52.0, ±3 79.7 (paper, with gold: AgenTracer-8B 36.2, Claude-Sonnet-4
  30.3). Direction of error splits by label provenance: on INJECTED labels the model is later than gold in 40% and
  earlier in 6% (it blames the step where the corrupted content is consumed, the symptom); on DIAGNOSED (counterfactual
  replay of natural failures) labels it is earlier in 35%, later in 22%. Same model, same prompt, same system: the
  sign of the bias is a property of how the label was made (H13).
- TracerTraj coding/test (127): exact 14.6, ±3 72.4, agent 81.3 (paper with gold: AgenTracer-8B 18.9, Claude 15.5);
  later than gold in 57% -- MetaGPT runs where the injected step is a requirements/architecture artefact and the model
  blames the Engineer's implementation of it.
- TraceElephant (219, 201 parsed): exact 34.3, ±3 65.2, agent 60.2 (paper, GPT-4o without gold: all-at-once 22.7,
  dynamic agentic 27.6; with gold 33.3). Captain-Agent GAIA 39.7% exact, Magentic-One GAIA 32.9%, SWE-Agent 29.6%.
  The specialist-named ledger artefact measured: on the 40 Magentic-One labels that sit on a ledger call named after
  the next speaker, step exact is 12.5% (vs 46.9% on the other 49) and agent accuracy 42.5%; the model answers
  "Orchestrator" on 35% of them, and agent accuracy would be 75% if that answer were accepted. Rationales that blame
  the environment (27): 7.4% exact, the model is later in 59% (it waits for the agent to act on the broken
  observation). Gold Orchestrator: agent accuracy 11.9%.
- MP-Bench (277 with a majority step): exact vs first-majority step 38.0, ±3 59.4; manual 23.4 / automatic 59.7.
  The model's step is in the union of all flags in 83.3%, in the majority set in 63.8%, carries 3 votes in 36.6%,
  2 votes 27.2%, 1 vote 19.6%, 0 votes 16.7%. Exact accuracy by the majority category of the gold step: Reasoning
  Error 69.6%, Contextual Understanding 51.5%, Tool/Agent Invocation 48.1%, Verification 42.9%, Planning 22.0%, Tool
  Usage 21.9% (model later in 59%). Gold with 3 votes: 50.9% exact; with 2 votes: 31.6%.
- TrajErrBench τ²-bench (400; 370 scored after excluding 30 whose label is on the user side or missing): exact 45.4,
  ±3 62.4 (paper, zh edition: direct GPT-5.4 41.5, Gemini-3.1-Pro 52.5, TrajDebug 52.8). By module: act.* 70-88%,
  reason.* 48-53%, obs.* 33-45%, plan.BadDecomposition 25% (later 57%), plan.UnrealisticPlan 0% (later 100%).
  Model vs the longest-step rule, case by case: model right 168, rule right 169, both right 80, union 257 (69%):
  the two make largely independent errors, so the rule is not what the model does, but a reader that combined
  "commit step" structure with content would beat every published number.
- LongRCA (200 sampled, median 145 steps): exact 16.0, ±3 28.5, agent 44.5 (paper, DeepSeek-V4-Flash: all-at-once
  7.6 / 19.9, RCTA 24.1 / 37.4). The model is LATER than gold in 59% (median +6 steps), earlier in 25%: on long
  multi-agent runs it drifts to the late planner/verifier decision. TravelPlanner: later in 68%; gold stay_agent (the
  specialist that returned wrong hotel data early) gets 4% exact and 4% agent accuracy, the model blames the
  manager/planner later (consumer-blame bias, H2). Gold task_planner 12% exact (later 68%). WebArena 22.6% exact.
  Runs >100 steps: 14.3% exact, later 68%. Rationales tagged "later repairs failed" (25): 20% exact; "earlier error
  recovered" (9): 11%. Same-block misses: when the gold is in a repeat block (49) the miss lands in the block 33 times.
- CORRECT-Error (300 sampled): exact 70.3, ±3 89.7, agent 74.3 (paper, Qwen-2.5-7B: LLM-as-judge Acc@1 6-63, CORRECT
  17-80 by task). When the gold is the last decision step (138/296) the model is exact in 98% (135); when it is not
  (158) in 48% (76). Gold Planner 88.4% exact, gold WebSurfer 28.8% (model later 42%: it blames the Planner that accepts
  the rewritten WebSurfer observation -- consumer-blame again, here against an injected producer label).
- TRAIL (124 with labels; gold = earliest HIGH-impact span, 95 have one): exact 34.7 vs that gold; the model's step is
  one of the annotated error spans (any impact) in 50% and a HIGH one in 42%; GAIA 50.6% exact, SWE-bench 14.3%.
  Gold on a TOOL span (10): 0% (the model always blames the LLM call that issued or consumed it). Gold inside a repeat
  block (33): 12.1% vs 62.9% outside.
- TrajErrBench SWE-Bench Pro (86, ~120 messages / 200k chars each): exact 30.2, ±3 38.4 (paper zh: direct 10.5-17.4,
  TrajDebug 24.4). Later than gold in 44%, earlier in 26%. Human κ on this split is 0.67 (pairwise 66.7%), so 30%
  exact is within a third of the human ceiling.
- Who&When Pro (300 sampled, text+video): exact 74.0, ±3 95.3, agent 92.7 (paper, text split: GPT-5.4 72.3, Claude
  Sonnet 4.6 69.8). Gold is the last decision in 143/298 -> 93% exact there; otherwise 57%. MathChat 96.6%,
  smolagents 81.2%, Magentic-One 75.0%, EVA (video) 41.7%. A.3 premature termination 96.4% exact (the label is the
  final step by definition); V.2 inadequate verification 94.4%; P.1 perception 36.4%; R.1 hallucination 58.1%.
  A 27B model with no gold matches the frontier numbers because the structure (late, terse, final) carries the label.
- SymFail inventory (200): the model lists 2.9 mistakes per run and tags 90% of them FATAL (530 fatal / 58 recovered);
  inventory-decisive exact 30.0 vs std 31.5. With at most three LLM calls per run there is nothing to recover from;
  the recovered-error question has to be answered on the long natural sets.
- AgentHallu (443): exact 56.9, ±3 87.0, agent 94.5 (paper: GPT-5 32.7, Gemini-2.5-Pro 41.1, step-by-step GPT-5 42.7).
  Human-Interaction 75.3% (the step that repeats the user's wrong fact), Planning/Fact Derive 28.6% (later 71%), Task
  Decompose 36.7% (later 60%), Tool-Use incorrect arguments 40.0% (earlier 46%). SmolAgents 32.1% (later 62.5%).
- HORIZON web (94 judge-labelled): exact 39.4 vs the LLM-judge step, ±3 80.9; earlier in 51%.

### Inventory prompt (every mistake tagged recovered / fatal) joined with the std prediction — the H1 test
  | dataset | traj with a model-RECOVERED mistake before gold | std earlier than gold -> that step tagged recovered / fatal | gold step tagged recovered | inventory-decisive exact vs std |
  | Who&When | 24% | 14 / 41 | 15% | 39.9 vs 43.2 |
  | AgentRx | 28% | 3 / 22 | 7% | 32.4 vs 31.0 |
  | TraceElephant | 23% | 9 / 39 | 8% | 29.6 vs 34.7 |
  | MP-Bench | 16% | 7 / 44 | 19% | 36.1 vs 39.5 |
  | LongRCA | 53% | 26 / 12 | 9% | 15.0 vs 16.0 |
  | TrajErrBench | 38% | 53 / 29 | 16% | 37.7 vs 42.7 |
  | AgentErrorBench | 45% | 42 / 72 | 20% | 21.4 vs 24.0 |
  | AgentHallu | 21% | 40 / 22 | 12% | 55.6 vs 57.2 |
  | TracerTraj coding | 33% | 21 / 12 | 14% | 8.1 vs 14.6 |
  | CORRECT-Error | 14% | 13 / 15 | 28% | 54.2 vs 71.5 |
  Reading: (1) the model itself finds a recovered mistake before the gold in a fifth to a half of runs, so the
  phenomenon is pervasive; (2) on the single-agent / long sets (LongRCA, TrajErrBench, AgentHallu, TracerTraj) the
  model's early all-at-once picks ARE steps it calls "recovered" when asked to tag fates -- the recovered-error trap
  is real there and is an inconsistency of the reader, not a disagreement about consequence; (3) on the multi-agent
  sets (Who&When, AgentRx, TraceElephant, MP-Bench) the early picks are tagged FATAL: there the model disagrees with
  the annotator about which early error mattered (consumer/producer, instruction/execution), not about recovery;
  (4) the model tags the GOLD step itself as recovered in 7-28% of runs: Who&When HC/1 (gold 12 = a misclick on an
  ad, navigated back at 16), HC/3 (gold 32 = one of the scrolls, the run reaches the right page at 92 and dies on a
  content-filter error), HC/2 (gold 4, generic rationale) -- by the counterfactual definition several golds are
  themselves recovered errors; (5) forcing the inventory does NOT raise exact accuracy (lower on 9 of 10 sets): tagging
  fates is not the same as judging consequence, and the "earliest never-recovered" rule in the inventory prompt pulls
  the choice away from the annotators' conventions.
- SearchAuditBench (200 sampled): CS-strict 22.3, CS-loose (inside the tolerance span) 30.6 (paper with
  Claude-Opus-4.8: all-at-once 32.1 / 47.1, SearchAuditor 39.9 / 54.8). Earlier than gold in 49%: the model blames the
  first query that missed the evidence path rather than the later commit; runs >100 messages 10.9% strict; gold on the
  last message 77.8%. Entity-Relation Misbinding 43.5% (a locally checkable slip) vs Candidate Mismanagement 16.1%,
  Constraint Neglect 16.2% (judgement about what should have been kept open).
- Outcome-BLIND inventory on AgentHallu (final, 249 successful / 441 failed): in SUCCESSFUL runs the model lists
  1.5 mistakes per run, calls at least one of them FATAL in 23% (independent of run length: 23% at <=5 steps, 19% at
  <=10, 31% at >10) and names a "decisive step" in 90% of them; in failed runs 2.2 mistakes, >=1 fatal in 63%.
  Verdict accuracy 77% on successes, 63% on failures; p_success AUROC 0.765. Decisive == gold 42% blind vs 57% when
  told the run failed: a quarter of the all-at-once accuracy comes from knowing the outcome, and the "fatal" judgement
  fires on a quarter of runs that succeeded.
- Agent names anonymised (Agent_1..k in order of appearance, names scrubbed from all text; same prompt): step exact
  Who&When 43.5 -> 45.7, TraceElephant 35.2 -> 33.8, MP-Bench 38.0 -> 38.8 (the same step is named in 79-84% of runs);
  agent accuracy Who&When 61.0 -> 65.9, TraceElephant 60.8 -> 63.9, MP-Bench 56.7 -> 57.1. The orchestrator is blamed
  MORE once it has no name: gold-Orchestrator agent accuracy 41 -> 53 (Who&When), 12.5 -> 25 (TraceElephant), 31 -> 41
  (MP-Bench). So the role-name prior does not inflate "who" accuracy here; the name "Orchestrator" shields the
  orchestrator from blame (a reader deference effect), and the WebSurfer-heavy label distribution is matched by content
  (the WebSurfer's steps are where the visible observations go wrong), not by its name.
- Outcome-blind inventory on TRAIL (148; 22 end with the correct GAIA answer): on the 22 correct runs the model lists
  1.9 mistakes but tags one FATAL in only 5% (vs 23% on AgentHallu successes) and calls the run a success in 95%.
  Against the human error spans (all 577, correct and failed runs alike): the model's listed steps hit an annotated
  span with precision 44% and recall 36% (HIGH-impact spans 120/197 = 61%); of the HIGH spans it finds it tags 63%
  fatal, of the non-HIGH ones 15% -- its fate tag tracks the annotators' impact rating, which TRAIL itself decouples
  from outcome (H1 evidence: 45 HIGH errors in correct runs).
- SearchAuditBench inventory (193): the model finds a RECOVERED mistake before the gold in 67% of runs (the highest of
  all sets: deep-search agents try a wrong candidate, drop it, try another), and when its all-at-once pick is earlier
  than the gold (50% of runs) that pick is a step it tags recovered in 44 of 96 cases. Inventory-decisive inside the
  tolerance span 30% vs std 31%; the inventory lists some step inside the span in 64% of runs.
- Outcome-blind inventory on HORIZON web (150 sampled; 44 env-verified successes / 105 failures): in SUCCESSFUL runs
  the model declares a FATAL mistake in 34% (vs 23% AgentHallu, 5% TRAIL) and names a decisive step in 100%; in
  failed runs 6.0 mistakes, >=1 fatal in 89%; p_success AUROC 0.856; verdict correct 66% on successes, 89% on
  failures. The false-fatal rate on successful runs varies 5-34% across sets: the reader's wrongness detector is not
  outcome-aware, and WebArena-style runs (long, with many tolerated slips) are where it over-fires most.
- LongRCA, the 41 trajectories whose HUMAN rationale documents an earlier error that was later corrected (tag A):
  std exact 10/40 (25%, above the 16% overall), ±5 16/40; earlier than gold 14, later 16; of the 14 early picks the
  model's own inventory tags 8 as RECOVERED and 5 as fatal; the inventory finds a recovered mistake before the gold in
  26/40. Three cases read in full are the phenomenon exactly: terminal_bench_2__031 -- human: "After correcting the
  column order, ActionAgent had already localized the peaks ... but subsequently misjudged the data" (gold 160); model
  blames step 20, the column-order mistake that was corrected, while its inventory lists step 20 as recovered.
  swe_bench_pro__093 -- human: "the initial delegation plan in step 37 does contain obvious flaws ... later discovered
  and fixed" (gold 399); model blames step 50 (the None-handling flaw), inventory: 50, 54, 66, 177, 341 all recovered.
  travelplanner__094 -- human: pollution identified by step 60-65, root = the step 73 that ignores it; model blames the
  stay_agent's step 23 that introduced the polluted data (producer vs consumer, and the early error was flagged).
- LongRCA, the 80 trajectories whose human rationale says LATER REPAIR ATTEMPTS FAILED (tag B): std exact 21/79 (27%),
  ±5 30/79; the model is LATER than gold in 49/79 (62%) and earlier in 9: when the run contains a sequence of failed
  repairs, the reader blames one of the repair attempts rather than the decision they were trying to repair, and the
  inventory (partial) tags that late pick FATAL in 19 of the first 49 such cases. The lock-in regime produces the
  mirror image of the recovered-error trap: visible failed fixes attract blame away from the root.

### Deeper dig (2026-11-01): what would raise step accuracy
- Candidate recall of the inventory lists (if the attributor proposed its listed mistakes as candidates; oracle
  reranker bound): gold in the list / in the top-3 as listed: Who&When 78% / 67%, MP-Bench 72% / 66%, TraceElephant
  65% / 56%, TrajErrBench 55% / 50%, AgentRx 58% / 48%, AgentErrorBench 58% / 41%, LongRCA 47% / 28%, SearchAuditBench
  39% / 27%; top-1 as listed is at or below the all-at-once exact score everywhere. The model's candidate generation is
  well ahead of its choice: a reranker that picks the right one of its first three candidates would add 15-25 points
  on the multi-agent sets. Ordering fatal-first does not help (the fate tag is not calibrated on causality).
- Where the misses land (std outputs): on SearchAuditBench 70% of the "later" misses are the final answer and 65% of
  the "earlier" misses are the first query -- the reader is bimodal (first query or final commit) on deep search; on
  AgentErrorBench 57% of early misses are the very first decision; on Who&When Pro 52% of later misses are the last
  decision. "Who" is derived from "when": when the step is right the agent is wrong in <=1% (7% TraceElephant, the
  ledger artefact), and when the step is wrong the agent is still right in 18-77% (single-agent sets trivially).
  The model's own length preference is weak: it picks the longest decision step in 26% of τ²-bench runs although the
  gold is the longest in 41%; it is not exploiting the commit-step structure that the rule exploits.
- Lever: 3 sketched same-dataset examples with their labels and rationales (convention learning). Who&When: exact
  43.5 -> 44.6 (HC 25.9 -> 29.3, AG unchanged), agent 60.9 -> 65.2. Small; the convention is not easily absorbed from
  three sketches (or Who&When's labels are too inconsistent to convey one).
- Lever: few-shot on AgentRx: exact 30.1 -> 35.6, ±1 37.0 -> 52.1, agent 63.0 -> 65.8; "later" misses 30 -> 21%.
  The AgentRx convention (first unrecovered failure) is partly learnable from three sketches.
- Miss taxonomy (the model classifies its own miss with the gold and the human rationale revealed; codes: A same error
  other step, B pick is an upstream cause, C pick is a downstream symptom, D pick was recovered, E other mistake,
  F human label questionable, G pick not a mistake):
  | dataset | misses | A | B | C | D | E | F+G | human right | attributor right | both |
  | Who&When | 104 | 25 | 29 | 34 | 3 | 5 | 5 | 61 | 30 | 10 |
  | AgentRx | 49 | 27 | 18 | 29 | 2 | 16 | 8 | 57 | 20 | 22 |
  | TraceElephant | 132 | 39 | 14 | 33 | 1 | 9 | 5 | 68 | 17 | 15 |
  | MP-Bench | 159 | 21 | 17 | 43 | 2 | 8 | 10 | 68 | 23 | 9 |
  | TrajErrBench | 262 | 20 | 11 | 32 | 5 | 18 | 13 | 84 | 13 | 3 |
  | LongRCA | 239 | 15 | 5 | 44 | 10 | 24 | 2 | 90 | 5 | 4 |
  | AgentErrorBench | 149 | 25 | 44 | 13 | 1 | 17 | 1 | 47 | 43 | 10 |
  | SearchAuditBench | 150 | 18 | 18 | 31 | 9 | 13 | 12 | 83 | 16 | 1 |
  | AgentHallu | 186 | 33 | 9 | 30 | 10 | 15 | 4 | 85 | 9 | 5 |
  | TracerTraj | 200 | 42 | 4 | 27 | 8 | 14 | 5 | 74 | 8 | 18 |
  | CORRECT-Error | 84 | 33 | 20 | 30 | 7 | 0 | 10 | 55 | 26 | 19 |
  | SymFail | 366 | 81 | 2 | 15 | 0 | 0 | 1 | 28 | 4 | 68 |
  Readings: (i) "downstream symptom" (C) is the largest class on the natural multi-agent and long sets (MP-Bench 43%,
  LongRCA 44%, TRAIL 37%, Who&When 34%): with the answer revealed the model agrees it stopped at a consequence;
  (ii) "same error, other step" (A) is 20-40% everywhere and 81% on SymFail -- convention, not error; (iii) "upstream
  cause" (B) dominates only on AgentErrorBench (44%) where it also judges the attributor right in 43% of misses --
  the one set where the labels, not the reader, look wrong; (iv) when confronted, the model calls its pick
  "recovered" (D) in only 1-10%, far below what the blind inventory implied -- it defends its all-at-once pick as a
  cause even where its own inventory had tagged the step recovered.
- The model's own reason as a confidence signal (LLM-tagged properties of the std reasons; exact accuracy with vs
  without the property): mentions_loop -> Who&When 23 vs 47, MP-Bench 24 vs 42, AgentRx 8 vs 36, SearchAuditBench 9
  vs 25, TrajErrBench 20 vs 43 (LongRCA inverted, 39 vs 16: there loops are what gets labelled); blames_strategy ->
  AgentErrorBench 16 vs 32, SearchAuditBench 12 vs 25, TraceElephant 24 vs 37; hedged -> AgentErrorBench 13 vs 28,
  SearchAuditBench 15 vs 26; states_contradiction -> AgentErrorBench 30 vs 14, TrajErrBench 44 vs 29, AgentHallu 59
  vs 43, SearchAuditBench 25 vs 12, TraceElephant 36 vs 22. A justification that names a contradiction and does not
  talk about loops or strategy is roughly twice as likely to be right; "the agent kept looping" is the signature of a
  symptom pick.
- Selective prediction from the reason tags (keep a prediction only if its reason states a contradiction and does not
  mention loops, strategy or hedging): kept share / exact on kept / exact on dropped: AgentErrorBench 19% / 44.7 / 19.0,
  SearchAuditBench 50% / 31.2 / 13.4, TraceElephant 54% / 42.6 / 24.7, Who&When 54% / 50.5 / 35.3, MP-Bench 53% / 44.0
  / 35.0, AgentRx 65% / 34.8 / 24.0, TrajErrBench 77% / 43.9 / 37.9, AgentHallu 72% / 59.6 / 51.6; LongRCA inverted
  (68% / 15.7 / 29.5). A free, model-internal abstention signal on every set except the long-horizon one.
- Lever: few-shot on τ²-bench (150-run panel): exact 39.3 -> 42.7, ±1 39.3 -> 44.0.
- Lever (negative): a backward "cause or symptom?" second pass over the std pick (look for an earlier step that made
  the pick inevitable and was never corrected) HURTS: Who&When exact 43.5 -> 33.2 (earlier picks 33% -> 53%), AgentRx
  35.4 -> 20.8 (earlier 29% -> 54%). Asked to look for an earlier cause, the model finds one and overshoots upstream:
  it cannot tell an earlier imperfection from an earlier cause by reading, so the symptom/cause direction is not
  fixable by instruction; it needs a consequence measurement. (Details of changed picks in the next line.)
  Backward pass details: Who&When 69/184 picks changed, all to an earlier step; 24 were right and became wrong, 5
  became right, 40 wrong before and after. Of the 101 earlier candidates the model named, it marked ONE as
  "corrected before the pick"; AgentRx 0 of 26. Primed to look for causes, the reader does not see recoveries at all
  -- the exact blind spot the recovered-error phenomenon predicts, now measured on the reader side.
- Lever: few-shot on TraceElephant (120-run panel): exact 35.0 -> 35.0, agent 60.0 -> 65.0. Backward pass on MP-Bench
  (first 164): 51.2 -> 45.1. Pattern so far: three sketched examples give +0 to +5 exact (and +2 to +5 agent); the
  backward cause check costs 6-14 points everywhere.
- Lever: few-shot on LongRCA (60): exact 18.3 -> 18.3, agent 48.3 -> 56.7. Backward on MP-Bench (full 264): 39.8 ->
  33.7 (earlier picks 23% -> 42%). The backward pass is uniformly harmful (-6 to -14 exact on four sets).
- Lever: backward pass on τ²-bench (150): exact 42.7 -> 47.3 (the one set where it helps: the label convention there
  is the earliest policy misstatement, which "look earlier" finds). Few-shot on AgentErrorBench (100): 21 -> 22.
  Two-stage consequence check (inventory -> per-candidate "undone later?" -> choose) on Who&When (first 96): 36.5 ->
  29.2; it drifts earlier like the backward pass. Both second passes move the pick in the direction the prompt names,
  not toward the gold: the reader's consequence judgement is not improved by asking for it twice.
- Two-stage on Who&When (full 183): 43.5 -> 39.9. Backward on TraceElephant (first 72): 33.3 -> 26.4.
- Two-stage on AgentRx (73): 30.1 -> 31.5 (neutral); on τ²-bench (first 48): 31.2 -> 41.7. Backward on LongRCA (60):
  20.0 -> 18.3; on TraceElephant (120): 33.3 -> 27.5. Emerging split: on τ²-bench (single agent under an explicit
  policy, label = the earliest policy misreading) both second passes HELP (+5 to +10); on every multi-agent set they
  HURT (-2 to -14). Re-examination works when "was this step wrong?" can be checked against a written policy and the
  label convention is "earliest", and fails when the question is which of several agents' slips mattered.
- Two-stage on τ²-bench (full 150): 38.7 -> 44.0, ±1 38.7 -> 45.3; the backward pass gave +4.6 on the same panel.
- Backward on AgentErrorBench (100): 21.0 -> 19.0 (earlier 66% -> 71%). Two-stage on TraceElephant (first 72): 33.3
  -> 29.2.
- Backward on SearchAuditBench (100): 20.0 -> 16.0 (earlier 52% -> 64%). Two-stage on TraceElephant (full 120): 35.0
  -> 31.7. Second-pass panel is now complete for backward (8 sets): τ² +4.6, everything else -2 to -14.
- Two-stage on LongRCA (60): 16.7 -> 21.7 (later picks 58% -> 33%); on AgentErrorBench (first 72): 20.8 -> 20.8 (±3
  40 -> 29). Revised reading of the second passes: both the backward pass and the two-stage check shift the pick
  EARLIER by a roughly constant amount regardless of content (earlier share +10 to +20 points on every set). They
  help exactly where the base reader was too late (LongRCA 59% later: +5; τ²-bench: +5) and hurt where it was
  balanced or early (Who&When, AgentRx, TraceElephant, MP-Bench, AgentErrorBench, SearchAuditBench: -2 to -14). A
  second pass is a position prior in disguise, not a consequence judgement.
- Lever: giving the reference answer (Who&When, 184): exact 43.5 -> 45.1 (AG 51.6 -> 54.0, HC 25.9 -> 25.9), agent
  60.9 -> 64.1. The gold adds almost nothing for this reader, against +5 to +20 points reported for GPT-4o in the
  paper: the published gold gain was a weak-reader effect (answer matching), not label information (H4).
- Gold panel complete: TraceElephant (120) 34.2 -> 34.2; AgentRx τ-retail (29, expected actions given) 51.7 -> 51.7;
  Who&When 43.5 -> 45.1. Knowing the correct answer does not move this reader's step choice: its misses are not about
  not knowing what the right outcome was.
- Lever: self-consistency (5 samples at T=0.7, majority vote) on Who&When (184): greedy 43.5, vote 42.9, any-of-5
  oracle 57.1 (HC 22.4 vote / 41.4 oracle; AG 52.4 / 64.3). No accuracy gain from voting, but the vote share is a
  calibrated confidence: unanimous (86 runs) 57% exact, 4/5 (37) 43%, 3/5 (31) 19%, 2/5 (28) 29%. Combined with the
  reason tags this gives a selective attributor; and the 14-point oracle gap says the right step is among the samples
  in a further 14% of runs where the vote picks another -- a selection problem again (H15).
- Self-consistency panel so far (greedy / vote / any-of-5 oracle; exact when share>=0.8 vs <=0.4): AgentRx 30.1 /
  30.1 / 41.1 (42.1 vs 11.1); τ²-bench 38.0 / 42.7 / 57.3 (52.7 vs 31.2); Who&When 43.5 / 42.9 / 57.1 (52.8 vs 26.7).
  Voting gives +0 to +5; the oracle over five samples is +11 to +19 everywhere; vote share separates a 42-53% stratum
  from an 11-31% one on all three sets.
- Self-consistency, more sets (greedy / vote / any-of-5; exact at share>=0.8 vs <=0.4):
  | longrca | 60 | 18.3 | 15.0 | 31.7 | 25, 24.0 | 20, 5.0 |
  | traceelephant | 119 | 33.6 | 32.8 | 44.5 | 68, 41.2 | 22, 18.2 |
  | agenterrorbench | 97 | 21.6 | 18.6 | 30.9 | 60, 23.3 | 19, 5.3 |
- Lever: extended reasoning (thinking mode, 12k completion budget) on Who&When: 47/184 answers truncated before the
  JSON (median 6.1k completion tokens, p90 at the 12k cap); on the 137 that finished, HC 32.1% exact (std 25.9), AG
  48.6% (std 51.6). Re-running the truncated ones and AgentRx / τ²-bench with a 32k budget (queue 8).
- Lever: extended reasoning with a 32k budget on Who&When (184; 8 still unanswered): exact 43.5 -> 35.3, ±3 67.4 ->
  66.8, agent 60.9 -> 56.5; later picks 23% -> 35%. Median 5.3k reasoning tokens (p90 15.8k). Thinking longer makes
  this reader worse at the exact step and pushes it toward later steps: deliberation re-derives the failure from the
  final answer backwards and stops at the first visible break.
- Extended reasoning (32k) on AgentRx (73, 4 unanswered): exact 30.1 -> 30.1, ±1 37.0 -> 45.2, agent 63.0 -> 71.2.
  Neutral on the exact step, slightly better in the neighbourhood and on the agent.
- Extended reasoning (32k) on τ²-bench (150, 4 unanswered): exact 39.3 -> 42.7, ±1 39.3 -> 43.3, ±3 60.7 -> 56.0.
  Thinking panel: Who&When -8.2, AgentRx 0.0, τ²-bench +3.4 -- the same single-agent-helps / multi-agent-hurts split
  as the second passes, at 10-30x the generation cost.
