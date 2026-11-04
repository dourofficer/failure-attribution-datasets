# LongRCA Bench — inspection notes (G2, Nov 2026)

Scripts: `inspect/longrca_stats.py` (reason heuristics, root type, verifier/judge activity, error signs), `inspect/longrca_reason_llm.py`
(LLM classification of all 1,140 `mistake_reason` texts), `inspect/longrca_priors.py` (structural priors, verifier theatre, final-write
inconsistencies), `inspect/longrca_skel.py` (skeleton reader), `inspect/g2_dump.py`. Outputs under `results/longrca/`
(`stats.md`, `stats.json`, `reason_llm.md`, `reason_llm.jsonl`, `priors.md`, `judge_verdicts.json`, `reads/`, `all_at_once_std*.jsonl`, `prefix_probe.jsonl`).

## 1. Data as loaded

- 1,140 records, 177,884 steps (loader `loaders/longrca.py`; `mistake_step` 0-based = idx). Sources: TravelPlanner 685, WebArena-Verified 177,
  SWE-bench Pro 128, VitaBench 108, Terminal-Bench 2 42. Roles: agent outputs are `role=agent`; every `user`-role history entry (terminal
  output, tool result, evaluator record, *and the VitaBench user simulator*) is `role=tool` under the name `Computer_terminal`.
- Team shapes differ per source and matter for everything below:
  - **SWE-Pro / TB2**: `DiagnostAgent` (planner) delegates to `ActionAgent` (implements) and `JudgeAgent` (verifies) via composite hand-off
    names `DiagnostAgent (-> ActionAgent)` / `(-> JudgeAgent)`; verdicts come back as `Computer_terminal` relay messages
    ("Delegated agent finished with result: JudgeAgent finishes task with VERDICT: PASS"). 285 / 272 steps mean.
  - **TravelPlanner**: MagenticOne group chat; `Task_Planner` writes the plan and picks the next speaker; `transport_agent`, `stay_agent`,
    `food_attr_agent` call sandbox tools and write a blackboard; `verifier_agent` writes `add_verifier_conclusion(passed=true/false)`;
    the run terminates on the literal text `TASK_COMPLETE` (283/685), max rounds (88) or an `is_request_satisfied` ledger (314); then
    whichever agent is selected as "writer" emits the final itinerary JSON from a blackboard snapshot (writer = manager 234, verifier 167,
    food_attr 140, transport 40, stay 39, none 65).
  - **WebArena**: `Task_Planner` (Planner) → `Action_Expert` (WebSurfer, 1 observation per cycle) → `Verification_Expert` (Critic), at most
    6 coordination cycles; 95/177 runs end with "Reached the multi-agent coordination budget" and `UNKNOWN_ERROR`.
  - **VitaBench**: single `Action_Expert` talking to a simulated user (`Computer_terminal`), Chinese; ends with `###STOP###` (87),
    `too_many_errors` (14) or `max_steps` (7).
- Loader caveat (not a bug, but a convention to remember): `Computer_terminal` is a label target in 55 records (34 TP tool returns,
  19 VitaBench *user-simulator* messages, 1 SWE relay, 1 TB2 relay). The schema's `error_agent` therefore sometimes names the environment.
- `labels.reason` is long (SWE median ≈ 1.3k chars) and 686/1,140 cite a step number; 48 use "it is recommended / suggested that the root
  cause be marked at step N" phrasing, i.e. the released text is a reviewer-facing recommendation, not a bare rationale.

## 2. Close-reading notes (13 trajectories)

| id | n / gold | blamed | what happened; where the labelled step is; do I agree; where the symptoms are |
|---|---|---|---|
| travelplanner__397 | 16 / 11 | manager_agent | Shortest TP run. Manager records cities and a transport request on the blackboard (steps 5–10) and asks the transport_agent to search; the harness then emits `Orchestration (task_result): Text 'TASK_COMPLETE' mentioned` (step 11) although no agent wrote the token in its visible output (the planner's step-1 plan text mentions the completion token). The writer then fabricates a 7-day plan from an empty blackboard. Label = the orchestration record, agent = manager. **Disagree on mechanism**: the decisive event is a harness termination fired by a text-match, the manager never emitted it; the label blames the agent whose *name* is on the orchestration line. Symptom = the fabricated plan at step 13. |
| travelplanner__003 | 93 / 90 | verifier_agent | Clean run: all searches grounded, verifier passes 8/9 checks, planner summarises a correct plan at step 87. The verifier, acting as writer at step 90, copies "Indian Grill Room" into Day-2 dinner instead of Mangle Di Kulfi (duplicate dinner → evaluator fails). **Agree**: a transcription error in the final structured write; cause = symptom, fully checkable locally (duplicate across days, blackboard had a different draft). Nothing before step 90 is wrong. |
| travelplanner__158 | 134 / 40 | Computer_terminal | `accommodation_search(city="Johnstown")` returns listings named "Sunny 1 Bedroom in Bedstuy, Brooklyn" (step 40). stay_agent notices (41), verifier flags "Accommodation Data Quality Critical Issue, passed:false" (58), re-search returns the same (72–75), manager proceeds anyway; final plan uses the listings. Label = the tool return. The benchmark's accommodation table *is* NYC Airbnb data relabelled with other cities, so the data were valid for the evaluator; 605/685 TP runs contain such returns (§3). **Disagree**: the agents' distrust of valid data, and the manager's decision to proceed without resolving it, are the agent-side causes; blaming the tool makes the label unlearnable. |
| travelplanner__165 | 119 / 1 | Task_Planner | The NL query says "accommodations that are not shared rooms"; the structured `local_constraint` says `"room type": "shared room"`. The planner's fact sheet (step 1) explicitly notes the discrepancy and follows the NL text; the evaluator uses the structured field. **Disagree**: a benchmark data contradiction (5 TP records have it: 144, 152, 165, 359, 604) labelled as a planning error at step 1; no step in the run could have known which field the grader trusts. |
| vitabench__055 | 56 / 42 | Action_Expert | User (step 1) says her sister-in-law *cannot come*; at step 13 says the niece "will sleep with the sister-in-law" and wants two rooms; tickets ordered = 1 adult + 1 child; at step 47 the user herself summarises "2-person seat". Label: `instore_book(customer_count=2)` "one fewer". **Disagree / undecidable**: the simulated user is self-contradictory; the hidden rubric wants 3. The agent's 2 is consistent with the tickets it sold. Symptom: none in the trajectory (user says thanks, `###STOP###`). |
| vitabench__085 | 130 / 117 | Computer_terminal | Business trip, user alone (step 1); at step 113 the *user simulator* answers in the assistant's voice ("I recommend the adult ticket… do you need one for your child?") and at 117 insists "I told you I have a kid, I need 2 tickets". Label = the user message. Annotators correctly identify a simulator fault; the record is nevertheless scored as an agent/step label. |
| webarena_verified__092 | 13 / 8 | Verification_Expert | Critic reads 10 of 12 reviews from one viewport + metadata, finds no "under water photo" and returns `SUCCESS, retrieved_data: []` instead of `NOT_FOUND_ERROR`. Label step is right; the rationale ("correctly determined that no reviewer mentioned…") is probably wrong — two reviews were never seen. The annotator had no gold answer and accepted the agent's claim. |
| webarena_verified__003 | 63 / 18 | Verification_Expert | Forum list sorted by post count; Critic at step 18 asserts it is alphabetical; planner amplifies ("scroll up to find D"), click error, six cycles burnt, direct URL `/f/diy` only in cycle 5; budget exhausted → `UNKNOWN_ERROR`. **Agree**; the first wrong belief is the root, the symptom is 43 steps later. Typical of the 95 budget-exhaustion runs: the "error" is a belief statement by the Critic/Planner, not an action. |
| swe_bench_pro__001 | 309 / 25 | DiagnostAgent (-> ActionAgent) | First delegation plan tells ActionAgent to make `_parse_content` return 3 values and to put the bcrypt default in the filter layer; ActionAgent implements faithfully; JudgeAgent FAIL (187, a different bug) → fix → PASS (269) → "Task Complete". Hidden tests fail 4/39. The rationale starts "Final eval came back 35/39 with reward=0 … working backwards from those four" and explains that all pytest runs imported the *installed* ansible, not `/app/lib`, so every green was false. **Agree with the step** (and with the convention "instruction step is the root"); but note the label is derived by backward search from the hidden test names, which no auditor sees. Visible symptoms: none that discriminate; the trajectory ends in a confident success claim. |
| swe_bench_pro__075 | 220 / 206 | JudgeAgent | ActionAgent creates `ca.go` (untracked), JudgeAgent runs `git status` (sees it untracked), `go build`, tests pass, VERDICT: PASS. Eval compiles the *patch*, which excludes untracked files. Label = the PASS verdict. **Partly disagree**: the judge is blamed for not knowing that untracked files are dropped by the harness; the DiagnostAgent/ActionAgent never `git add`ed either. The failure is a harness convention nobody in the team was told. |
| swe_bench_pro__074 | 661 / 205 | DiagnostAgent (-> ActionAgent) | At step 205 the planner designs a public `TTLCache.GetOrLoad` + goroutine instead of the private `fnCache` the hidden tests reference. **Agree given the tests**, but the required private name is only in the gold patch/tests; from the problem statement alone the design is reasonable. 22/170 SWE/TB2 rationales explicitly cite hidden tests / gold patch expectations. |
| swe_bench_pro__038 | 142 / 121 | JudgeAgent | ActionAgent's fix passes all tests; JudgeAgent cannot import an internal package from `/tmp`, so it *appends* a test function to `config_test.go` (121) and returns PASS. Label: violating "test files must not be modified". The rationale gives no mechanism linking this to the eval failure (test files are normally overwritten by the harness). Candidate "rule violation ≠ cause" label. |
| terminal_bench_2__001 | 390 / 212 | ActionAgent | Two interpreters: venv python already has numpy 2.4.4 (step 5), system pip shows 2.3.0 (step 7); the agent notes the discrepancy at step 8 and step 12. At 212 `pip install --upgrade cython numpy` uninstalls the *system* numpy 2.3.0 → 2.4.4 (visible in the tool output at 213). JudgeAgent FAIL (308, a different np.int issue) → fix → PASS (366). **Agree**: the root is a single careless command whose effect is printed in the next tool message; the constraint ("keep 2.3.0") is in the task text. A prefix monitor that tracks declared constraints could flag it at 213. |
| terminal_bench_2__016 (skim) | 546 / 398 | JudgeAgent | JudgeAgent sends `sendkey ret` + `quit` to the QEMU monitor during verification, killing the VM; the verifier itself destroys the artefact. A rare case where the verification step *is* the cause rather than theatre. |

Overall impression: labels on SWE-Pro/TB2 are careful and are almost always the *instruction* or *edit* that diverged from the hidden
tests, found by backward search from the test names (hindsight); labels on TravelPlanner/VitaBench/WebArena frequently point at
environment behaviour (tool data, user simulator, auth state, harness termination) and at the final write.

## 3. Targeted statistics

### 3.1 What the rationales say (heuristic classes; LLM classes in `results/longrca/reason_llm.md`)

| source | n | causal link stated | no link (heuristic) | redundant/wasted work, with link | redundant, no link | mentions hand-off | mentions verification | cites evaluator / test outcome |
|---|---|---|---|---|---|---|---|---|
| swe_bench_pro | 128 | 72% | 18% | 9% | 1% | 50% | 61% | 26% (33) |
| terminal_bench_2 | 42 | 79% | 12% | 10% | 0% | 33% | 67% | 14% (6) |
| travelplanner | 685 | 60% | 15% | 21% | 4% | 12% | 61% | 14% (98) |
| vitabench | 108 | 59% | 31% | 9% | 0% | 10% | 26% | 4% |
| webarena_verified | 177 | 55% | 17% | 25% | 3% | 36% | 43% | 3% |
| ALL | 1140 | 61% | 17% | 19% | 3% | 21% | 55% | 13% (146) |

- LLM classification (Qwen3.8-27B, no thinking, 100-record stratified sample = first 20 per source; `results/longrca/reason_llm.jsonl`;
  the full 1,140 run was abandoned because the shared server delivered ≈1 call/min):

| source | n | states a causal link | mentions outcome | wrong_action | redundant_work | handoff_instruction | verification | premature_stop | ignored_evidence |
|---|---|---|---|---|---|---|---|---|---|
| swe_bench_pro | 20 | 80% | 85% | 50% | 0% | 50% | 0% | 0% | 0% |
| terminal_bench_2 | 20 | 95% | 100% | 60% | 0% | 35% | 0% | 0% | 5% |
| travelplanner | 20 | 70% | 80% | 40% | 5% | 0% | 5% | 10% | 35% |
| vitabench | 20 | 60% | 75% | 15% | 0% | 0% | 5% | 5% | 70% |
| webarena_verified | 20 | 80% | 80% | 50% | 5% | 5% | 5% | 0% | 35% |
| ALL | 100 | 77% | 84% | 43% | 2% | 18% | 3% | 3% | 29% |

  So **23% of rationales state no causal link** (close to the report's 364/1,140 = 32%, lower because the LLM accepts implicit
  consequences) but **only 2% are mainly about redundant / wasted work**: the "~1/5 blame redundant work" figure comes from rationales
  that *mention* repetition (my regex: 22%) while blaming a substantive decision. Of the LLM's 23 no-link cases, 7 are terse "what was
  wrong" statements (swe_006/015/016), 6 are protocol complaints (tp_001 "redundant duplicate work", tp_008 "generated the plan without
  the completion token"), and 8 are VitaBench user/rubric conflicts (vita_001/004: "the task input and the evaluation target are
  self-contradictory"). VitaBench rationales are 70% "ignored a user request / constraint", i.e. the root is an omission relative to
  the hidden rubric, not a wrong action; SWE/TB2 rationales are 50%/35% "wrong hand-off instruction".
- Reading the heuristic "no link" cases (10 across sources: swe 023/089, tb2 041/042, tp 534/500, vita 054/025, wa 023/050): most are
  *short* statements of a wrong action whose consequence is left implicit ("Fabricate a non-existent taxi"), not claims without a causal
  story. Two are genuinely non-rationales: `webarena_verified__023` = "This case involves some racist, negative, and bad remarks; it is
  recommended to delete it..." (the label step 18 is arbitrary), and `terminal_bench_2__042` = one generic sentence. The paper-level
  number "364/1140 state no causal link" is therefore mostly a brevity artefact; the LLM classifier's `causal_link` field gives the
  cleaner estimate (see `reason_llm.md`).
- Rationales name a role that does not exist in the trajectory in **557/1,140 (49%)**: "Action_Expert" in 352 TravelPlanner reasons
  (TP has no such agent), "Planner"/"WebSurfer"/"Critic" in 169 WebArena reasons, "Verification_Expert" in 25 TP reasons. The annotators
  evidently worked from a *different rendering* (the LLM navigation summaries / a generic role vocabulary), and the texts were
  translated/polished afterwards.
- An **unreleased error taxonomy leaks** into the rationales: `E1_verification_gap`/`verification_gap` (50 mentions),
  `E2_premature_or_wrong_completion` (9), `ignored_constraint` (16), `unrecovered_tool_failure` (3), `USER_INTENT_UNDERSPECIFIED` (3),
  `output_format_error` (1). The paper says "no failure taxonomy, only free text"; the annotation protocol had one.
- **Hindsight anchoring is explicit**: 146 rationales (SWE-Pro 26%) quote the evaluator ("Final eval came back 35/39 with reward=0",
  "the single casualty is test_performance_and_scalability[8000]") and then "work backwards" to the step; 22/170 SWE/TB2 rationales cite
  hidden tests or the gold patch as the thing the step diverged from.

### 3.2 Root-step type and what follows it

| source | root = hand-off / orchestration record | root = a tool call | blamed role acts again after root | median later messages by blamed role | root followed by a tool error |
|---|---|---|---|---|---|
| swe_bench_pro | 59% | 95% | 98% | 13.5 | 12% |
| terminal_bench_2 | 40% | 93% | 98% | 18.5 | 0% |
| travelplanner | 0% (29 orchestration records) | 39% | 89% | 6 | 2% |
| vitabench | 0% | 44% | 94% | 11 | 14% |
| webarena_verified | 10% | 0% | 80% | 2 | 0% |

- The root is the blamed role's *last* message in only 2/128 SWE, 1/42 TB2, 78/685 TP, 7/108 Vita, 36/177 WA records: the blamed role
  almost always keeps acting (and usually keeps looking fine) after its decisive mistake.
- **Distance from root to the first visible failure signal** (tool error / judge FAIL / verifier `passed:false` / verbal problem word):

| source | no tool-or-verifier signal after root | median dist → first tool error (n) | → first verifier/judge FAIL (n) | → first verbal "problem" word (n) | median steps after root | signal within 3 steps |
|---|---|---|---|---|---|---|
| swe_bench_pro | 2% | 8 (125) | 128.5 (34) | 15 (127) | 184 | 23% |
| terminal_bench_2 | 5% | 13.5 (40) | 126 (13) | 11 (41) | 152 | 14% |
| travelplanner | 32% | 35.5 (250) | 28 (367) | 8 (426) | 55 | 13% |
| vitabench | 81% | 1 (21) | – (0) | – (0) | 24 | 13% |
| webarena_verified | 16% | 26 (23) | 22.5 (148) | 2 (153) | 26 | 12% |

  Tool errors are *frequent everywhere* in SWE/TB2 (24–27% of tool steps before and after the root; 41% duplicate tool calls before the
  root in SWE-Pro), so a tool error is not evidence of the root; the first *judge* failure, when it exists, is >100 steps later and
  usually about a different bug (§3.3). VitaBench has essentially no visible signal at all: 81% of runs show no error after the root and
  the user ends the chat with thanks.

### 3.3 Verification theatre (DiagnostAgent–ActionAgent–JudgeAgent) and the TravelPlanner verifier

| source | n | runs with no JudgeAgent verdict | JudgeAgent verdicts after root (median, max) | last verdict after root | any FAIL after root | green test run after root | final DiagnostAgent message claims completion |
|---|---|---|---|---|---|---|---|
| swe_bench_pro | 128 | 1 | 1, 3 | PASS 124 / FAIL 2 | 27 (21%) | 81 (63%) | 118 (92%) |
| terminal_bench_2 | 42 | 22 | 0, 3 | PASS 20 | 3 (7%) | 17 (40%) | 18 (43%); 3 admit failure |

  Verdict sequences after the root (SWE-Pro): `P` 83, `FP` 20, `PP` 14, `PPP` 2, `FPP` 2, `PFP` 2, `F` 1, none 2. So **97% of SWE-Pro
  runs end with a JudgeAgent PASS issued after the root**, and in the 27 runs where the judge did say FAIL it was about something else
  (the FAIL is followed by a fix and a PASS; the root survives). Judges verify by re-running the same tests the ActionAgent ran (often
  against the wrong code, as in swe_001) and by static review (swe_004 rationale: "only performed a static code review and judged it
  as PASS"). The judge is itself blamed in 7 records; in 50 rationales the judge's miss is tagged `E1_verification_gap` but *not*
  chosen as the root — the convention puts the root at the instruction/edit and treats the verifier as a non-catching bystander.
- TravelPlanner verifier: 79/685 runs never produce a verifier conclusion; 286 have only `passed:true` conclusions; 320 have ≥1
  `passed:false` and in **217 of those the run still terminated as complete** (the manager/planner emits `TASK_COMPLETE` or the ledger
  says satisfied). "Verifier says fail after root" in 37% of TP runs vs "says pass" in 40%; both are weak signals of the root position.

### 3.4 Environment and harness faults inside the labelled set

- **TravelPlanner accommodation data**: 605/685 runs (88%) contain an `accommodation_search` return whose listing names are NYC
  neighbourhoods (Brooklyn, Williamsburg, East Village, Harlem…) for a non-NY city; agents verbally call it wrong data in 451 runs
  (searches are repeated, `passed:false` conclusions written, plans "cannot proceed"). The benchmark's accommodation table is the original
  TravelPlanner one (NYC Airbnb names relabelled with cities), so the evaluator accepts them. Only 33 of these runs are labelled
  `Computer_terminal`; the other 572 blame stay_agent (174), manager (121), Task_Planner (84), transport (72), verifier (65),
  food_attr (56) — the same perceived fault is assigned to six roles depending on which agent reacted to it most visibly.
- **WebArena session state**: 52/76 Reddit (Postmill) runs show the logged-out header ("Log in / Sign up") in every WebSurfer observation
  and never a logged-in one, although the prompt states "You are already logged in"; 16 of them are MUTATE tasks that cannot succeed
  logged out. 64/177 WA rationales mention login/auth. Blame for the same condition goes to Action_Expert (22), Task_Planner (17) and
  Verification_Expert (13).
- **TravelPlanner termination**: 283 runs end by the text-match `Text 'TASK_COMPLETE' mentioned`; 23 roots sit exactly on that
  orchestration record, 29 roots are orchestration records in total; 22 runs reach the writer with an *empty* candidate list and 113
  with empty verifier conclusions. 5 TP tasks have the NL/structured room-type contradiction (§2).
- **VitaBench**: 37/108 rationales argue with the user simulator or the rubric; at least 6 state outright that the agent was not at
  fault (`vitabench__008`, `044`, `062`: "The agent is not at fault / executed correctly; the verifier/rubric was wrong";
  `001`, `004`: "the task input and the evaluation target are self-contradictory"; `102`: "label step 19 as USER_INTENT_UNDERSPECIFIED").
  These 19 `Computer_terminal` and ≥6 "agent not at fault" records are scored as ordinary step labels.

### 3.5 Structural priors (exact / within-5 hit rate; `results/longrca/priors.md`)

| rule | swe_bench_pro | terminal_bench_2 | travelplanner | vitabench | webarena |
|---|---|---|---|---|---|
| first `DiagnostAgent (-> ActionAgent)` delegation | **45% / 51%** | 14% / 21% | – | – | – |
| last such delegation | 24% / 27% | 10% / 14% | – | – | – |
| first file edit | 11% / 25% | 12% / 31% | – | – | – |
| final itinerary JSON write (fires 51%) | – | – | 7% / 13% | – | – |
| last Action_Expert turn | – | – | – | 3% / 6% | 20% / 29% |
| last agent step | 0% / 0% | 0% / 2% | 0% / 23% | 3% / 6% | 0% / 27% |
| uniform over agent steps | 0.9% | 1.1% | 1.2% | 4.5% | 2.1% |

  The paper's best method (RCTA) reaches 24.1% exact overall; "first delegation" alone gives 45% on SWE-Pro because the annotation rule
  "if a hand-off instruction already contains the error, the instruction step is the root" plus the team design (one big plan up front)
  makes the first plan the default root. On TravelPlanner the final JSON write is the root in 48 runs, and in 27 of those the JSON has a
  mechanically detectable inconsistency (duplicate meal across days / item absent from the blackboard); across all 347 TP final JSONs,
  42% have a duplicate meal and 12% name an item that is not on the blackboard — so inconsistency alone does not identify the 48.

### 3.6 Local detectability (prefix probe) — see §4.2

## 4. Baseline error analysis

The shared vLLM server was oversubscribed (≈30 jobs, 54 queued requests) during this session, so the official
`baseline/all_at_once.py longrca --n 60` run (started 09:08) had delivered 21/60 records when this was written; the rows were read
straight from the cache with `inspect/longrca_partial.py` (`results/longrca/all_at_once_std_partial.jsonl`,
`all_at_once_std_partial_analysis.md`). The remaining 39 will land in `all_at_once_std.jsonl` when the run finishes; numbers below
are on the 21 (14 TravelPlanner, 3 VitaBench, 3 WebArena, 1 SWE-Pro).

### 4.1 Scores (Qwen3.8-27B, all-at-once, 150k-token budget, 20k max tokens, thinking on)

| metric | n/21 | % |
|---|---|---|
| agent correct | 8 | 38 |
| step exact | 4 | 19 |
| step within 3 | 5 | 24 |
| step within 5 | 6 | 29 |
| truncated (thinking hit 20k tokens, no JSON) | 3 | 14 |

Signed offset of the 18 parsed predictions: later than gold 7, earlier 7, exact 4; of the misses, 6 are > 3 steps too early and 7 > 3
steps too late — **no late bias** on this source mix (median |offset| 48 steps; the four exact hits are 3 WebArena/SWE records with a
single explicit instruction-vs-action deviation and one TP ungrounded-city case). Per subset: WebArena 2/3 exact, SWE-Pro 1/1 exact,
TravelPlanner 1/14, VitaBench 0/3. Agent accuracy 38% is below the role prior (TP majority role 26%, WA 56%, Vita 82%).

### 4.2 What the model does (reasoning read for 9 failures, 4 successes)

- **It must guess the failure criterion, and guesses the protocol.** TravelPlanner failures are decided by evaluator rules
  (duplicate restaurants, minimum nights, city sequence, sandbox membership) that appear nowhere in the trajectory; the annotators
  quote them ("The final verifier's failure items include invalid city sequence, repeated Day 3 dinner…", `travelplanner__434/029/105`).
  The model instead latches onto the one failure signal it can see — the empty `Orchestration (task_result):` final record and the
  workflow rule "the manager should emit the agreed completion token" — and blames a protocol step: 7/14 TP predictions cite the
  completion token / writer / `is_request_satisfied` (`travelplanner__165`: pred 113 "manager should have emitted the token", gold 1;
  `__105`: pred 138 "skipped the completion-token step", gold 141 = final JSON; `__029`: thinking exhausted on "why is the final output
  blank"). This is P4 in a new form: an outcome-blind auditor invents an outcome.
  *Loader note*: `final_output` for TP is the last agent step, which is the empty orchestration record; rendering the final itinerary
  JSON instead would remove one distraction (shared loader, not changed here).
- **Recovered errors are picked when nothing else is visible.** `vitabench__025`: pred 10 (booking without confirmation, later cancelled
  and redone), gold 58 (wrong museum + time clash, never corrected); `webarena_verified__094`: pred 36 (a failed Sign-In click, recovered
  at 46) and the reasoning concludes "the system's final answer was correct… no single decisive mistake" — the gold (planner stops
  after "no orders" without using the order filter) needs the gold answer to see. The model has no mechanism to discount a mistake that
  the trajectory itself repaired.
- **Environment conditions are blamed on whoever reacted.** `travelplanner__434`: pred 9 stay_agent "dismissed valid tool results as
  mislabeled" — the model explicitly reasons that the NYC-named listings are valid and blames the first agent that distrusted them;
  gold 93 (manager/planner, 84 steps later, same mechanism); `__240`: pred 84 "manager emitted TASK_COMPLETE prematurely", gold 39
  stay_agent chose a listing with min-nights 5. Same condition, different reacting role, exact miss.
- **Very early predictions come from spec-compliance reading.** `travelplanner__077`: pred 2 (planner asked for a return flight; the
  model argues the trip is open-jaw) vs gold 210 (final JSON city fields); `__325`: pred 8 (Ann Arbor not in the city list) vs gold 227
  (final JSON fabricated placeholders); `__385`: pred 99 vs gold 7. The model does enumerate the late write errors in its reasoning but
  the prompt's "earliest step" instruction pushes it to the earliest *plausible* deviation (P2: convention mismatch, here the model is
  *earlier* than the annotator).
- **Successes are local instruction–action mismatches.** `webarena_verified__001` (told to click 'New', scrolled instead),
  `__018` (clicked the thumbnail instead of the title), `swe_bench_pro__116` (first delegation plan merges features in the wrong order;
  the model finds it from the spec), `travelplanner__406` (stores Park City although `city_search` did not return it). These are the
  cases where the error is a checkable deviation from an explicit instruction or tool return in the same window.
- **Truncation**: 3/21 runs exhausted 20k thinking tokens without an answer, all TravelPlanner 106–228 steps; the reasoning is a
  linear walk through the plan rules rather than a search.

What the model can do by reading the whole trajectory: find instruction/action deviations and ungrounded facts (WA, SWE-Pro plan
errors, TP city choices). What it cannot: know which evaluator rule failed (TP), see the gold answer (WA RETRIEVE, Vita rubric), or
discount recovered errors; on those it falls back to protocol violations and early plausible deviations.

### 4.3 Prefix probe (local detectability; partial)

`inspect/prefix_probe.py longrca --n 10 --max-steps 80 --window 5 --workers 3` (82 probes on 10 records ≤ 80 steps: 4 WA, 3 Vita,
3 short TP); 27/82 probes had returned when this was written (`results/longrca/prefix_probe_partial.jsonl`). On the 4 records whose
gold step has been probed: gold flagged in 3/4 (`webarena_verified__029` conf 0.88, `vitabench__022` 0.75, `travelplanner__628` 0.97;
`webarena_verified__103` not flagged, conf 0.8 "not a mistake"); flags on steps before the gold 1/11, after the gold 4/12. Early reading:
the labelled step is locally recognisable without the outcome in these short runs, but neighbours after it are flagged at a similar
rate (`vitabench__022`: 10 flagged at 0.97 before the gold 12), so the probe gives a region, not a step. Final numbers to be appended
when the run completes.

## 5. Annotation issues (prevalence estimates)

| issue | estimate | evidence |
|---|---|---|
| label points at the environment / simulator / harness, not an agent | 55/1140 explicit (`Computer_terminal`), plus ≥29 TP orchestration-record roots and ≥6 Vita "agent not at fault" rationales → **≈8%** | §3.4; ids: travelplanner__158/010/043/098/233/…, vitabench__001/004/008/044/062/085/102, travelplanner__397/261/323 |
| same environmental condition blamed on different roles | TP NYC-listing runs: 6 roles; WA logged-out runs: 3 roles | §3.4 |
| benchmark data contradiction labelled as agent error | 5 TP (room type), ≥2 Vita (001, 004) | §2 |
| hindsight / evaluator-anchored labels | 146 rationales quote the evaluator; 22 SWE/TB2 cite hidden tests/gold patch | §3.1 |
| rationale from a different rendering (wrong role names) | 557/1140 (49%) | §3.1 |
| undisclosed taxonomy | ≥80 rationales carry `E1_verification_gap`-style tags | §3.1 |
| non-rationale / junk | webarena_verified__023 ("recommended to delete it") | §3.1 |
| "root = first instruction" convention dominates SWE-Pro | 45% of roots are the first delegation | §3.5 |
| judge PASS after the root treated as bystander, not cause | 124/128 SWE-Pro; judge blamed in 7 | §3.3 |

The paper's own IAA (40.3% exact, 38% of pairs > 20 steps apart) is consistent with these: the disagreement is largely *which role's
reaction to a shared environmental condition counts as the decision*, and *instruction vs. implementation*.

## 6. Candidate hypotheses

**H-L1. Environment-perceived faults are the dominant hidden variable in TravelPlanner/WebArena/VitaBench labels.**
Statement: in ≥60% of TP runs and ≥50% of WA-Reddit runs the trajectory contains a condition the agents treat as an environment fault
(wrong-city listings, logged-out session, contradictory user); the labelled root is then whichever role's *reaction* to it the annotator
found decisive, which varies across annotators (6 roles for the same TP condition). Evidence: §3.4. Test: re-annotate 50 NYC-listing TP
runs with two annotators given an explicit rule ("tool data are valid"); measure agreement vs. the released labels; measure whether
step-accuracy of any method on these runs is near the role prior. Shared with: who_and_when/traceelephant (WebSurfer-heavy blame),
searchauditbench (unverified source), memtrace (data-vs-system). Targeted method: an attributor that first classifies each trajectory
as "environment-fault present" and, if so, scores the *first agent decision that proceeds despite the unresolved fault* (manager
proceed / verifier accept) rather than the tool return — i.e. a two-stage "condition → reaction" scorer.

**H-L2. On SWE-Pro the root is an instruction-level convention: the first delegation plan.**
Statement: 45% of SWE-Pro roots are the first `DiagnostAgent (-> ActionAgent)` message; the remaining roots are mostly a later delegation
or the edit that implemented it. Evidence: §3.5, swe_001/074 readings, rule "if the hand-off already contains the error, the instruction
is the root". Test: a classifier that only sees delegation messages and the problem statement (no execution) and predicts "which
delegation diverges from the spec" — if it beats RCTA's 24% on SWE-Pro, step attribution on this source is a spec-compliance check, not
an execution-trace problem. Shared with: traceelephant Captain-Agent (orchestrator instructions), who_and_when HC. Method: parse the
hand-off plan into requirement items, align with the task's "hard constraints", flag the first unaligned item.

**H-L3. Verification theatre is near-universal and non-informative in the Diagnost/Action/Judge team; the root survives every PASS.**
Statement: 97% of SWE-Pro runs end with a JudgeAgent PASS after the root; the 21% of FAIL verdicts are about other bugs and are
followed by a fix; 63% of runs show a green test run after the root (often against the wrong code). Evidence: §3.3, swe_001/075/038.
Test: for each run, check whether the judge ever ran the hidden test file names (visible in the rationale) — predict that the judge's
tests overlap the hidden tests in <20% of runs; measure attribution accuracy of a method that *ignores* all judge/verifier steps vs one
that weights them. Shared with: failure_as_process (verification theatre 27.6%), trail, trajerrbench VERIFY.*. Method: treat verifier
PASS as zero evidence and verifier FAIL as evidence *against* the fixed region (the root is elsewhere), i.e. a "verifier-exclusion" prior.

**H-L4. The final structured write is a distinct, locally checkable failure class in TravelPlanner.**
Statement: 48–140 TP roots sit on the writer's final JSON (duplicated meals, items not on the blackboard, wrong city strings); these are
cause = symptom cases where a consistency check between the JSON and the blackboard snapshot localises the error without reasoning
over the preceding 100 steps. Evidence: §3.5(c), tp_003. But 42% of all final JSONs carry a duplicate, so the check must be conditioned
on the evaluator's rule set (TravelPlanner commonsense checks). Test: implement the TravelPlanner validator on the final JSON and the
blackboard; measure how many of the 140 late roots it flags and how many early-root runs it falsely flags. Shared with: searchauditbench
(final-answer critical step 17%), who_and_when (orchestrator FINAL ANSWER). Method: a "last-mile validator" head that runs before any
trajectory-wide scorer and claims the last write when the inconsistency is an evaluator-rule violation.

**H-L5. Trajectory-visible symptoms do not separate "after the root" from "before the root" on LongRCA; the symptom the annotators
used is the evaluator's verdict, which is outside the trajectory.**
Statement (P1 refinement, partly a refutation): surface error signs (tool errors, FAIL verdicts, `passed:false`, verbal problem
words) occur at nearly the same per-step rate before and after the root in every source — AUROC of "step carries a sign" for
"step ≥ root" is 0.50–0.54 pooled and 0.52–0.54 within record (`results/longrca/symptom_auroc.md`):

| source | sign rate before root | after root | AUROC pooled | within-record |
|---|---|---|---|---|
| swe_bench_pro | 21.1% | 24.8% | 0.519 | 0.521 |
| terminal_bench_2 | 19.0% | 18.7% | 0.499 | 0.521 |
| travelplanner | 7.2% | 9.8% | 0.513 | 0.518 |
| vitabench | 1.0% | 4.4% | 0.517 | 0.526 |
| webarena_verified | 20.3% | 27.5% | 0.536 | 0.537 |

So "downstream contamination" in the SOAP sense (symptoms louder after the cause) is *not* visible at the surface here: these systems
err, retry and complain at a constant rate throughout, and the decisive error is distinguished only by its relation to the hidden
evaluator rule (TP), the hidden tests (SWE) or the gold answer (WA/Vita). Test: repeat with an LLM "is this step a problem" score
instead of regexes (the prefix probe, §4.3) and with evaluator feedback injected; if AUROC stays ≈0.5 without feedback and rises with
it, late-symptom back-propagation methods cannot work on LongRCA without the verdict. Method: condition the attributor on the
evaluator's failure items (available at audit time in practice) and search backwards from the *rule*, not from the trajectory's
noise.

**H-L6. Labels are closer to a hidden-outcome reader than to any trajectory-only auditor (P3) — measurable on SWE-Pro.**
Statement: because 26% of SWE-Pro rationales explicitly start from the failing test names and 22 cite the gold patch, an auditor given
the failing test names should jump from ≈10% to ≥30% exact, while one given only the trajectory stays near the structural prior.
Test: run All-at-Once with and without the `tests_status`-style failing-test list (not released here, but derivable from rationales
for a 40-run subset). Shared with: traceelephant SWE-Agent, trajerrbench SWE-Pro, trail SWE.

**H-L7. The rationale's role vocabulary shows annotators judged a summary, not the trace.**
Statement: 49% of rationales name a role absent from the record; if annotators judged LLM navigation summaries, then the labelled
step tends to be the step the summary *mentioned*, which an LLM auditor given the same summary will also pick. Test: regenerate
per-trajectory summaries with the paper's prompt (if available) or a generic one and measure how often the gold step is among the
summary's cited steps vs. a random step; compare judge accuracy with and without the summary.

**H-L8. An outcome-blind auditor invents an outcome: when the failure criterion is hidden, the all-at-once judge blames the one
failure-like thing it can see (protocol violations, empty orchestration records, recovered errors).**
Statement: 7/14 TravelPlanner predictions in the partial baseline blame the completion-token/writer protocol, none of the gold
labels do; 2 predictions pick errors the trajectory repaired. Evidence: §4.2. Test: re-run All-at-Once on the same 60 records with
(a) the evaluator's failure items (from the rationales' quoted verifier output) and (b) the gold answer / rubric injected; predict
TP exact accuracy rises from ≈7% to >25% and WA/Vita agent-correct predictions stop citing recovered errors. Shared with:
searchauditbench (no gold answer), traceelephant SWE-Agent (tests_status), who_and_when (no-GT setting). Method: never attribute
without a failure description; when none exists, generate candidate failure descriptions first (what *could* have failed the
evaluator) and attribute per candidate.

## 7. Open questions

- Which TravelPlanner evaluator rule actually failed in each run is not released; the rationales mention it in ~100 cases. With the
  rule, the 140 late-root runs could be verified mechanically.
- The paper's RCTA step accuracy per source is not given; the 45% first-delegation prior on SWE-Pro suggests the headline 24.1% hides
  a source where a trivial rule wins and sources (Vita, WA) where nothing does.
- Were the LLM navigation summaries the annotators saw retained? They would explain the role-name mismatch and allow H-L7 directly.
- Do the 20 hidden "E1/E2" taxonomy codes exist for every record? If so, the dataset secretly has a failure-mode label.


## 4b. Baseline results (filled from results/longrca/ after the runner finished, 2026-11-01)

Qwen3.8-27B all-at-once, gold = mistake_step; `step_in_set` counts a prediction inside the full labelled set.
Signed categories: `later` = predicted after the gold (symptom side), `earlier` = before it. Reasoning excerpts for
failures and successes are in `results/longrca/all_at_once_std_analysis.md`.

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| travelplanner | 38 | 31.6 | 13.2 | 23.7 | 13.2 |
| vitabench | 4 | 100.0 | 0.0 | 0.0 | 0.0 |
| webarena_verified | 11 | 81.8 | 45.5 | 54.5 | 45.5 |
| swe_bench_pro | 6 | 66.7 | 33.3 | 33.3 | 33.3 |
| terminal_bench_2 | 1 | 0.0 | 0.0 | 0.0 | 0.0 |
| ALL | 60 | 48.3 | 20.0 | 28.3 | 20.0 |

categories: {'later(>3)': 27, 'earlier(<-3)': 16, 'exact': 12, 'later(+1..3)': 3, 'earlier(-1..3)': 2}
agent right but step wrong: 17; step right but agent wrong: 0
| n_steps | n | step_exact% | within3% | agent% |
|---|---|---|---|---|
| 0-10 | 0 | 0.0 | 0.0 | 0.0 |
| 11-30 | 1 | 0.0 | 0.0 | 100.0 |
| 31-1000 | 59 | 20.3 | 28.8 | 47.5 |
wrote results/longrca/all_at_once_std_analysis.md
