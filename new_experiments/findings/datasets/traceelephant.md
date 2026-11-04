# TraceElephant — inspection notes (G2, 2026-11-01)

Scripts: `inspect/traceelephant_structure.py` (step types, ledger flags), `inspect/traceelephant_stats.py` (repetition, SWE edit
positions, GT visibility), `inspect/traceelephant_ww_overlap.py` + `inspect/traceelephant_llm_checks.py` (Who&When pairs, reason
types), `inspect/g2_dump.py` (close reading dumps in `results/traceelephant/reads*/`). Outputs under `results/traceelephant/`.

## 1. Data as loaded

- 220 runs (85 Captain-Agent, 91 Magentic-One, 44 SWE-Agent), 5,960 steps; a step is one LLM call. 219 labelled (task_26 of
  AssistantBench/Magentic has `mistake_step='none'`). Loader renders output + `Action:` tool calls + the *new* tool observations that
  appear at the end of the next call's input, so the observation of action k is attached to step k.
- Step-type structure found by `traceelephant_structure.py` (this matters for everything below):
  - **Magentic-One**: 1,228 ledger calls (JSON with `is_in_loop / is_progress_being_made / is_request_satisfied / next_speaker`),
    841 specialist actions (tool call + observation), 205 plan, 172 facts, 217 text. The calls alternate action / ledger. The tracing
    middleware records the orchestrator's ledger-update call **under the agent_id of the active specialist**: of 1,228 ledger calls,
    744 are recorded as `WebSurfer`, 77 `FileSurfer`, 49 `Coder`, 1 `ComputerTerminal`, only 355 as `Orchestrator`. Verified on the raw
    `step_records.json` (gaia_task_101, steps 5/9): the call's last input message is the orchestrator's ledger prompt ("Recall we are
    working on the following request ... Please answer the following questions"), the output is the ledger JSON, agent_name = WebSurfer.
  - **Captain-Agent**: 1,633 text turns (expert messages, including python code blocks executed by the group chat; execution results are
    not separate steps), 103 final/`TERMINATE` turns, 10 tool calls. Roughly half of the Orchestrator calls are one-word speaker
    selections (`WebServing_Expert`).
  - **SWE-Agent**: 1,153 tool-call steps, 398 text steps. "Agents" are tool names; agent_name equals the tool called in the step in
    1,326/1,551 calls (85%); in 225 calls it is a different tool (e.g. django-10880 step 11: name `bash`, call `str_replace_editor`), so
    the `mistake_agent` label is a middleware heuristic, not an actor.
- Gold-step type: Magentic-One ledger 40 / plan 18 / text 16 / action 10 / facts 6; Captain text 70 / final 15; SWE action 24 / text 20
  (by tool: source edit 28, source view 6, repro/test edit 5, text 4, submit 1).

## 2. Close-reading notes (11 trajectories)

| id | n / gold | what happened | label verdict |
|---|---|---|---|
| captain gaia_task_13 | 5 / 2 | InformationExtraction_Expert answers from memory ("Susa" -> Iran -> Hoveyda) with no tool call; Orchestrator check says "no contradictions, need to double-check: No"; GT Morarji Desai (first place named in Esther NIV is India) | agree; nothing visible after the step except verification theatre |
| captain gaia_task_25 | 59 / 2 | Step 2 is a sensible `perform_web_search(DOI)`; step 4 finds the MUSE link; step 6 "Since I cannot directly access external content, please check the article" then 50 near-identical "Please access the article..." turns | **disagree**: step 2 is fine; decisive step is 4/6 (refuses to browse). Label = first expert step (earliest-step convention) |
| swe django-10880 | 20 / 11 | repro script runs raw SQL, so "Query executed successfully" at step 10 before any fix (never reproduced the ORM bug); step 11 edits `compiler.get_distinct` (wrong place: bug is in `Count`'s template); submits | agree that 11 is the first wrong source edit; a monitor could already flag step 5/9 (reproduction does not exercise the bug) |
| swe django-11299 | 94 / 21 | from step 18 the repro script fails with "Settings already configured"; step 21 pastes a second `settings.configure` block; steps 22–93 repeat edit/run of the repro script (31% of post-gold steps are near-duplicates); never touches Django source | agree with the reason; the loop is the symptom, label at its start |
| magentic gaia_task_101 | 48 / 8 | WebSurfer clicks a ScienceDirect result (step 7) and hits a CAPTCHA; step 8 is the orchestrator ledger ("due to the captcha ... explore alternative sources") recorded as WebSurfer; 40 more steps of alternative searches; no answer | label sits on the ledger that *reacts* to the captcha, blamed on WebSurfer; the act (click) is step 7 |
| magentic assistant_bench_task_11 | 20 / 12 | PortfoliosLab gives VGT/MGK *annualized* 10-y returns (step 10/11); ledger step 12 (recorded WebSurfer) says "now get VONG"; step 13–15 StatMuse gives VONG *total* return 419.5%; ledger 16 compiles 22.47% vs 419.5%; final answer VONG (GT VGT) | reason ("compared annualized with total return") describes step 16/17; label at 12 is the orchestrator's acceptance of the annualized number as the comparable datum — defensible but 4 steps before the visible error, and the agent label (WebSurfer) is wrong: it is an orchestrator decision |
| magentic gaia_task_102 | 39 / 0 | facts sheet guesses "sixth studio album = Bad" (GAIA counts Thriller); every later search presupposes Bad; Dirty Diana lyrics scraped; answer "me" (GT "stare") | agree with step 0 (unverified educated guess that fixes the search presupposition); the reason text ("identifies Dirty Diana as fifth single") names a *consequence* at step 4 |
| magentic gaia_task_109 | 14 / 5 | web search for "station closest to Cleveland Elementary School" returns Cleveland Park (wrong: Shaw-Howard); answer 0 (GT 8) | plausible earliest; the misidentification is only stated in ledger 6/8 |
| magentic assistant_bench_task_28 | 38 / 35 | candidate list never completed (`is_in_loop` at 16); final answer step 35 says "Becker 85% is lowest" while listing CSI at 80% (arithmetic contradiction); GT CSI: Cyber was visible in steps 7–8 and dropped | **disagree with the convention**: correcting step 35 yields CSI (80%), still wrong; the decisive error is dropping CSI: Cyber from the candidate list (steps 9–18). Label agent `Coder` is the ledger's `next_speaker`, the step is an Orchestrator call |
| magentic assistant_bench_task_2 | 47 / 46 | 45 steps failing to download NOAA / Weather Underground data (stall flags from step 20), then final step fabricates "43%" from memory | agree (fabricated final answer); label = last step, every earlier step is a recoverable navigation failure |
| magentic assistant_bench_task_26 | 24 / none | finds a Q3-2021 report, answers $2.95M (GT $3.08M); reason blames step 11 navigation but `mistake_step='none'` | label inconsistent with its own reason |

Patterns seen while reading: (i) Captain-Agent experts answer from parametric memory in a single turn and the Orchestrator's
"double-check" step rubber-stamps it; (ii) Magentic-One failures are long navigation struggles where the decisive step is either
the orchestrator's acceptance of a wrong datum (ledger) or a fabricated final answer; (iii) SWE-Agent failures are "fix the wrong
place" after a reproduction that never reproduced, followed by long edit/run loops on the repro script.

## 3. Targeted statistics

**3a. Ledger stall flags vs the label (Magentic-One, 90 labelled).** 59/90 runs contain at least one ledger with `is_in_loop=true`
or `is_progress_being_made=false`. First stall flag: before the gold step in 24 runs (median −13 steps), at it in 5, after it in 30
(median +4.5, p90 +9). Stall rate on ledger calls: 72/476 = 15% before gold, 9/40 at gold, 230/701 = 33% after gold. So stall flags
are a weak, late symptom detector (they fire after the label by 1–20 steps in a third of runs and fire spuriously early in a quarter).

**3b. Who is blamed vs who acted.** 40/90 Magentic-One gold steps are ledger calls; 30 of them are recorded under a specialist name
(WebSurfer 30, FileSurfer 5, Coder 1 of the 36 non-Orchestrator ones) and the human `mistake_agent` equals the recorded name in 218/219
runs. The ledger is produced by the orchestrator prompt, so **~30/90 (33%) of Magentic-One agent labels blame a specialist for an
orchestrator decision** (e.g. assistant_bench_task_11, gaia_task_101, gaia_task_126). Only 6/32 of these ledger-gold steps follow an
action whose observation contains an error signal (captcha / error / not found), against a 15% base rate on all actions, so the label
is not simply "the step after the visible failure" — it is the orchestrator's instruction content that annotators judged wrong.

**3c. Repetition before vs after the label** (near-duplicate step content, Jaccard > 0.9 against the previous 12 steps, steps < 60
chars excluded): Captain-Agent 0/271 = 0% before gold vs 259/658 = 39% after (20/85 runs have a post-gold loop, none a pre-gold one);
SWE-Agent 28/609 = 4.6% before vs 278/885 = 31% after (9 vs 20 runs); Magentic-One 0.7% vs 0.3% (observations differ each step, loops
are only visible in the ledger flags). Loops are the dominant post-label symptom in two of three systems and almost never precede
the label: P1 (downstream symptoms louder than the cause) holds structurally here.

**3d. SWE-Agent: first source edit vs label.** gold == first edit of a non-test, non-repro file in 18/44 (41%); gold later than it in
20/44 (median offset 0, mean +4.8, p90 +18), earlier in 5, no source edit in 1. 5 labels sit on repro/test edits, 6 on `view` calls, 4
on text. A "first source edit" rule is a strong prior (41% vs 1/35 position prior) but misses the half of runs where the first edit was
acceptable and a later edit broke things.

**3d'. SWE-Agent: fix before reproduce (H-TE3 test).** Of 44 runs, 25 edit a source file before ever running a reproduction
script, 9 ran only reproductions that reported success (never reproduced the issue) before the first source edit, and only 10 saw a
failing reproduction before editing; 13/44 ever run the project's test suite. After the first source edit, the last reproduction run
reports "ok" in 30/38 runs that have one, i.e. the agent ends believing the fix works (false success, P8). So the label ("wrong
edit") sits on the first *source* commit, but the detectable process anomaly — editing without a failing reproduction — is earlier
and present in 34/44 (77%) runs.

**3e. Captain-Agent: label vs first specialist turn / code.** Gold is the first specialist turn in only 9/85; code was executed before
the gold step in 65/85; the gold step itself contains code in 41/85; 15/85 labels are Orchestrator final-answer turns; 8 runs contain no
code at all (pure memory answers).

**3f. Ground truth visible but lost.** In 19/176 GAIA/AssistantBench runs the exact GT string occurs in some step (e.g. task_28 "CSI:
Cyber" at steps 7–8, gold 35; gaia_task_21 "Claude Shannon" at steps 3–12, gold 23; gaia_task_126 at 3–8, gold 12). In 5 runs the final
`## ANSWER` block contains the GT token (4 are numeric coincidences such as "0", "3"; gaia_task_6 answers 3 = GT 3 and is still a
labelled failure — likely an evaluator formatting miss).

**3g. Reason-text types (LLM-classified, `reason_types.json`, 220 reasons).** commission (a concrete wrong act/claim at the step)
96 = 44%, omission ("did not verify / should have used X") 75 = 34%, outcome-only 24 = 11%, mixed 25. By system: Captain omission 39/85
(46%), Magentic 29/91 omission + 23 outcome-only, SWE commission 32/44. 50/220 (23%) are about missing verification; 102/220 (46%) name a
downstream consequence (loop, wrong answer) rather than only the act. An omission label is not visible in the step's own text (what
the step *didn't* do), which bounds any content-only scorer on a third of the labels.

**3g'. Who&When same-task pairs (`ww_overlap.json`, `ww_mechanism.json`).** 135 TE runs share a task text with Who&When; 85 pairs are
same-system (25 Magentic-One ↔ WW Hand-Crafted, 60 Captain ↔ WW Algorithm-Generated). Blamed agent agrees in 14/85 (12/25 Magentic,
2/60 Captain — Captain cannot agree by construction: TE uses fixed generic experts `InformationExtraction_Expert` etc., WW-AG uses
task-specific experts such as `Movie_Expert`). An LLM comparison of the two reason texts rates the failure *mechanism* as the same in
only 2/85 pairs (gaia_task_13 "Susa", gaia_task_123 "Bob's coin guess"), related in 24, different in 59. Relative position of the
label differs by more than 0.1 in 71/85 pairs (TE later in 39, earlier in 32). Conclusion: **the TE–WW disagreement is run-specific**
— independent runs of the same task fail through different mechanisms at different places — not a difference of labelling convention;
the brief's "18/86 agree" is therefore not a measurement of annotator convention, and task-level priors ("this task fails at step k /
on agent A") have little value across runs.

**3h. Local detectability (prefix probe, 12 runs ≤ 60 steps, window ±6).** See §4.

## 4. Baseline error analysis

`results/traceelephant/all_at_once_std.jsonl` (Qwen3.8-27B, all-at-once with ground truth, n=90: 38 Magentic, 35 Captain, 17 SWE;
analysis in `all_at_once_std_analysis.md`). Inventory variant pending in the shared chain.

| subset | n | agent ok | step exact | within 3 | earlier / later than gold (misses) |
|---|---|---|---|---|---|
| magentic-one | 38 | 81.6 | 26.3 | 52.6 | 14 / 14 |
| captain-agent | 35 | 60.0 | 37.1 | 62.9 | 16 / 6 |
| swe-agent | 17 | 76.5 | 41.2 | 58.8 | 8 / 2 |
| ALL | 90 | 72.2 | 33.3 | 57.8 | 38 / 22 (28 are > 3 steps too early, 10 > 3 too late) |

Step exact 33% is above the paper's All-at-Once (28.1 with GT, GPT-4o); no truncation or parse failures. By length: ≤10 steps 29%
exact (85% within 3), 11–30 steps 46%, >30 steps 20%.

**Direction of the misses: earlier, not later.** 38 of 60 misses are *before* the gold step (median signed offset 0, p10 −9). The
"earliest step" wording in the prompt makes the model climb to the first plausible deviation (Captain gaia_task_38: pred 4 "generic
search instead of the Wayback CDX API", gold 8 "asked the user to browse"; Magentic assistant_bench_task_27: pred 3 "search query
without the 2-block constraint", gold 13; sphinx-10673: pred 3 (first edit) vs gold 6 (an Orchestrator summary step)). Late misses are
the fabrication/symptom cases (captain gaia_task_60: pred 5 "fabricated placeholder PDF search", gold 1 "Orchestrator chose a web
expert instead of a PDF specialist" — here the human label is the earlier, more speculative one and the model's is the decisive act).
So on TraceElephant the full-context judge does **not** show the late bias of P1; the *labels* are frequently the earlier of two
defensible steps and the judge disagrees in both directions.

**Ledger-gold cases (13 in the sample): 1 exact, 5 earlier, 7 later.** The model mostly names the *same* agent as the label (WebSurfer),
i.e. it also attributes the ledger content to the recorded name (gaia_task_114: "it seems the same agent is generating instructions,
not actions... the step label says WebSurfer, so use WebSurfer"). The model notices the artefact and defers to the label format; agent
accuracy on Magentic (82%) is therefore partly agreement on an artefact.

**What the model handles (3 successes read).** Single-step wrong commitments with the ground truth in hand: SWE wrong-place edits
(pytest-5262 step 5 "modified write() instead of the mode property", matplotlib-14623 step 8), "estimated instead of exact" answers
(gaia_task_76 step 11 "average edits/year instead of XTools month counts"), an off-by-radius bug present in the first script
(gaia_task_77 step 5). All are cases where the labelled step contains a checkable claim and the GT tells the model what "wrong" means.

**What it cannot do.** (i) Decide between an early plausible deviation and the later decisive one without the annotators' convention
(pytest-10356: pred 9 first edit vs gold 20; the reasoning explicitly weighs "step 9 is where this first manifests as a code change" vs
"the fundamental mistake is the wrong diagnosis"). (ii) Resolve dropped candidates: assistant_bench_task_28 pred 9 ("chose Ranker,
whose list omits CSI: Cyber, instead of Next Episode") — arguably a *better* label than the gold 35, but scored as a miss of 26 steps.
(iii) Weigh a long loop: gaia_task_10 reasoning oscillates between the expert's refusal (8) and the Orchestrator's routing (9/13/15)
and lands on 8 by convention.

**3h. Prefix probe** — pending (`results/traceelephant/prefix_probe.jsonl`, 12 runs ≤ 60 steps, ±6 window, 141 probes).

## 5. Annotation issues (prevalence estimates)

1. **Agent label follows the middleware name, not the actor** (Magentic-One ≈ 30/90 = 33%; SWE-Agent 225/1,551 calls carry a tool name
   that is not the tool called, so "str_replace_editor 80%" is partly an artefact). Ids: gaia_task_101 (step 9 = ledger, blamed
   WebSurfer), assistant_bench_task_11 (step 13), assistant_bench_task_28 (step 36 is an Orchestrator final answer, blamed `Coder`
   = the ledger's next_speaker), assistant_bench_task_28 also has `mistake_step='Step 36'`.
2. **Earliest-step convention overrides decisiveness**: captain gaia_task_25 (label on a correct search step; failure begins 2–4
   steps later); gaia_task_102 (label on an unverified guess in the facts sheet, reason names the consequence 4 steps later). From the
   Who&When-pair comparison and the reading, roughly 1 in 5 Captain labels sit on a plausible-but-not-wrong early step.
3. **Decisiveness not checked against the ground truth**: assistant_bench_task_28 (fixing the labelled arithmetic still gives a
   wrong answer because the true candidate was dropped earlier).
4. **Inconsistent records**: assistant_bench_task_26 (`mistake_step='none'` but the reason names step 11); label strings `'Step 36'`.
5. **Failure set contains evaluator misses**: gaia_task_6 (answer 3 = GT 3). Small (≈1–3%).
6. **Reason texts are mostly omissions** ("did not verify / should have checked"): see §3g; an omission is not locally visible in
   the step's own text, which caps what any content-based scorer can do at that step.

## 6. Candidate hypotheses

- **H-TE1 "Ledger as the decision locus, mis-attributed by instrumentation"**: in orchestrator-led MAS the decisive step is the
  orchestrator's acceptance/instruction (ledger), not the specialist's action; datasets that attribute by thread/agent_id systematically
  move the blame to the specialist. Evidence: 3b. Test: re-label the 30 ledger-gold runs with the orchestrator as actor and re-score
  agent accuracy of baselines (they will rise, because the model blames the Orchestrator for ledger content). Shared with Who&When
  (Magentic-One orchestrator "thoughts"), MP-Bench, AgentRx Magentic. A targeted method should attribute a step to the *prompt owner*
  (whose system prompt produced the call), recoverable from `input.messages`.
- **H-TE2 "Loop onset = label + k"**: for Captain and SWE-Agent the first near-duplicate step is a strong, label-free symptom that
  occurs only after the gold step; the gold is the last non-duplicate step before the loop in a sizable fraction. Evidence: 3c. Test:
  predict gold = (first duplicate index − 1) and compare with position priors; combine with "first source edit" for SWE. Shared with
  Who&When-HC (ledger stalls), LongRCA (redundant work), TRAIL (Resource Abuse spans).
- **H-TE3 "Unverified reproduction"**: SWE failures where the repro script passes before any fix (never reproduces the issue) end in
  wrong-place edits; the label lands on the edit, but the detectable anomaly is the passing reproduction. Test: count runs with
  "success"-type repro output before the first source edit vs. after; compare with TrajErrBench-SWE and TRAIL-SWE.
- **H-TE4 "Presupposition lock-in"**: an unverified guess in the facts/plan step is copied into every later search query (gaia_task_102
  "Bad"), so later evidence confirms the guess; attribution must look at query *construction* not results. Test: for facts-gold runs,
  measure how many subsequent queries embed the guessed entity. Shared with SearchAuditBench (Candidate Mismanagement / premature
  lock-in) and LongRCA WebArena.
- **H-TE5 "Seen-but-dropped answers"**: in ~11% of runs the GT string is visible in an observation before the label; the decisive
  step is where it is dropped from the candidate set, which neither a symptom detector nor a first-error rule finds. Test: with GT
  available, locate the last step containing the GT and compare with gold; without GT, detect candidate-set shrinkage in ledgers.

## 7. Open questions

- Did the annotators see the raw `agent_name` (yes, per the paper's UI) — i.e. is H-TE1 an annotation artefact or a deliberate
  convention ("the specialist's turn includes the ledger that follows it")? The paper's agent accuracy numbers inherit it either way.
- Full observability vs outputs-only: the inputs are redundant; the only extra information in the inputs is screenshots (not rendered
  here). Does any label depend on a screenshot? Not testable without vision.
