# trajerrbench — inspection notes (G3, Nov 2026)

Scripts: `inspect/trajerrbench_swe_stats.py` (SWE-Pro structure), `inspect/trajerrbench_goal_probe.py` (hidden user goal),
ad-hoc τ² structure stats saved in `results/trajerrbench/g3_tau2_struct.json`; prefix probe
`results/trajerrbench/prefix_probe_tau2.jsonl`; baseline `results/trajerrbench/all_at_once_std*.jsonl`.
Dumps for close reading in `inspect/g3_dumps/trajerrbench__*.txt`.

## 1. Data as loaded

- 486 records (400 τ²-bench airline/retail, 86 SWE-Bench Pro), all `outcome=fail`, one `critical_error_step` each
  (0-based message index = `idx`), `categories=[module.subtype]` (17 null). Step 0 is the system/policy prompt; τ² messages
  alternate assistant / user / tool; SWE-Pro is OpenHands (assistant tool call → tool result, `think` tool returns
  "Your thought has been logged").
- Loader is correct. Two things the loader could not know:
  1. **The en edition's `task_description` is the first user utterance only; the zh edition's `task_description` carries the
     simulated user's hidden scenario ("场景：零售 / 用户目的：…") in 400/400 τ² files and a different (translated) issue
     text in 86/86 SWE files.** The paper evaluates on zh, so every published τ² number was obtained *with the user's goal
     visible to the detector*; our en runs are a strictly harder task. See §3.5 and `inspect/trajerrbench_goal_probe.py`.
  2. `metadata.extra.agent_framework_description` contains "DATASET NOTES (tau²-bench)" — a paragraph of annotation
     heuristics ("picking one [candidate] to act on is a substantive commitment, not a probe", "presenting an option … commits
     the assistant") that was evidently written for the TrajDebug detector. It is an explicit statement of the labelling
     convention and explains the statistics in §3.1.
- One label sits on a **tool** message: `tau2bench/airline_failed_qwen3-max_715755ce-…`, step 30 (a flight-search result),
  typed reason.MissingAssumptionCheck. Annotation error (the guideline says only assistant steps are judgable).

## 2. Close-reading notes

τ²-bench (9 runs read in full; ids abbreviated to the uuid prefix):

| id | n / gold | type | what happened | agree? | visible symptom |
|---|---|---|---|---|---|
| airline/deepseek `00c9f923` | 29 / 17 | plan.WrongOrder | user (regular member, says Gold) complains of a delay, wants compensation; agent offers a $200 certificate at 17 without the policy's precondition (change/cancel first) and issues it at 25 | yes; decidable from the policy at step 0 + tool output at 6 (membership regular) | none: tool returns success, user says thanks |
| retail/gpt-5 `05bb39c2` | 21 / 15 | reason.WrongChoice | boots size 10 → size 8; agent proposes the only available size-8 synthetic variant at 15, modifies at 17 | **no / undecidable**: the zh hidden goal says "size 8, same material, don't care about waterproof" — exactly what the agent chose. Whatever failed the DB check (refund to gift card? the batched 3 tool calls at step 9?) is invisible | none |
| airline/qwen `389d00a9` | 31 / 17 | reason.InvalidInference | user wants to change a New York→Chicago booking; tool shows FQ8APE EWR→ORD; agent says "none of your reservations is NY→Chicago" and books a new JFK→ORD flight | yes; locally detectable iff you know EWR is New York | the new booking at 27 (conspicuous DB write, 10 steps later) |
| retail/deepseek `537bcfdc` | 17 / 9 | reason.MissingAssumptionCheck | user lists 6 items to cancel; 4 orders; agent looks up only #W9722559 (the last) at 9, cancels it at 13 | yes, by the DATASET-NOTES convention ("picking one candidate is a commitment"); a blind reader would blame 11 (the claim "this is your recent order") or 13 (the cancel) | the agent itself notes at 11 that boots/watch/keyboard are not in this order — a self-reported contradiction that it then ignores |
| retail/deepseek `2524ed31` | 33 / 23 | obs.IgnoreOutput | T-shirt exchange; hidden goal: smaller, cotton, prefers black; agent lists variants from the product JSON at 23 and omits/misstates some; exchanges to blue M at 29 | plausible; the omission is inside a 3 k-char JSON, only checkable by diffing the listing against the tool output | user says "I was hoping for black" at 24 (pushback 1 step later) |
| retail/deepseek `7b8f7044` | 21 / 19 | verify.PrematureTermination | user confirms the return and refund method at 18; agent at 19 asks for confirmation *again*; user says "yes … ###STOP###" and the episode ends with no `return_delivered_order_items` call | the label blames the redundant re-confirmation; the proximate cause is the **simulated user quitting** at 20. Step 19 read alone is a polite, policy-compliant message | none until the transcript ends |
| airline/gpt-5 `67fa12fe` | 14 / 10 | act.WrongTool | user asks for the upgrade price before confirming; agent calls `transfer_to_human_agents` | yes; locally detectable (request is in scope) | transfer (episode ends) |
| airline/qwen `0250f877` | 7 / 3 | act.WrongTool | gift-card balance query; immediate transfer | yes; locally detectable (get_user_details would answer) | transfer |
| airline/gpt-5 `4437db52` | 69 / 63 | reason.WrongChoice | 20 search calls over 5 dates; at 63 the agent presents an itinerary (HAT286 IAH→LAS) whose numbers do not match the step-50/54 search results, then books it; final message says $966 charged vs $876 quoted | plausible but unverifiable in a 69-message run; the symptom is the price mismatch at 67 | mismatch at 67 (4 steps later) |

SWE-Bench Pro (4 runs read around the gold step, 58–162 messages):

- `gemini / protonmail__webclients-b530…` (58 / gold 8, verify.NoVerification): the agent creates `useCanCheckItem.ts` at
  step 8 and never writes the required test suite; its own `yarn test` at 24 **passes** (existing provider test). Gold = the
  file-creation step; "NoVerification" describes the whole tail, not step 8. Six later edit/view steps are equally plausible.
- `kimi / qutebrowser-96b9…` (90 / gold 2, act.WrongTool): gold is the agent's *first* message — a `think` call that
  restates the issue as "invalid inputs should return −1 (not raise)" and "the test files are already updated, so we just
  need to make the function pass them". A false premise at step 2 that shapes 88 later steps; type "act.WrongTool" is a
  mis-typing (it is reason.MissingAssumptionCheck / false premise). Locally detectable only by re-reading the issue text.
- `gemini / openlibrary-4b7e…` (100 / gold 52, verify.NoVerification): gold is a `str_replace` adding
  `AuthorRemoteIdConflictError` + `merge_remote_ids` to `models.py`; there are 10 further edits; nothing in the transcript
  says this one is wrong — only the hidden tests do.
- `claude / openlibrary-1894…` (162 / gold 100, reason.WrongChoice): gold is a `think` message deciding to rename
  `find_enriched_match` → `find_threshold_match` and restructure `find_match`; the edits follow at 98–130. The label is on
  the *decision*, not on the edit, consistent with the τ² "proposal step" convention (§3.1).

## 3. Targeted statistics

### 3.1 τ²: the gold step is the *proposal*, the DB write is 2–4 steps later (n = 400)

| gold step kind | n | share |
|---|---|---|
| assistant message to the user (no tool call) | 318 | 79.5 % |
| tool call, non-write (lookup/search) | 26 | 6.5 % |
| tool call that writes the DB (cancel/modify/book/…) | 56 | 14.0 % |

- 337/400 runs have a DB write at or after the gold step; lag gold → first write: 0 in 56, **2 in 123, 4 in 70**, 6 in 25,
  ≥ 8 in 63 (median 2). The step annotators blame is the message in which the wrong option is *presented*; the user says
  "yes" and the conspicuous commitment happens one assistant turn later. A detector that keys on DB writes is late by +2
  in the modal case (inside the paper's own [GT−3, GT] relaxed window only if it errs *earlier*, never later).
- 73/400 runs (18 %) contain **no DB write at all**: 25 end in `transfer_to_human_agents`, 37 in the user's `###STOP###`,
  11 otherwise. Their labels: reason.InvalidInference 23, MissingAssumptionCheck 10, WrongChoice 9 … — "wrong answer /
  wrong refusal" failures with no state change.
- Gold is preceded by a tool output in 288 (72 %) and by a user turn in 111 (28 %); it is the last assistant step in 28.

### 3.2 τ²: visible symptoms after the gold step are rare

| after gold | n | share |
|---|---|---|
| any tool `Error:` return | 41 | 10.3 % |
| user pushback (regex: "actually / that's not / wrong / I said / instead / …") | 110 | 27.5 % (lag 1 in 57, 3 in 16) |
| tool error **or** pushback | 138 | 34.5 % (median lag 3) |
| **nothing visible at all** | **262** | **65.5 %** |

Tool errors before the gold occur in 26 runs. The frequent tool errors (`Gift card balance is not enough` 25, `User not
found` 22, `Non-delivered order cannot be exchanged` 12) are mostly absorbed. So two thirds of τ² failures are *silent in the
transcript*: the only evidence that anything went wrong is the hidden DB diff the annotators saw. This is the mechanism
behind P3 here, and it is why pre-annotators with diagnostics (53–77 % match) beat blind detectors.

### 3.3 τ²: the simulated user ends the dialogue while the agent is still asking

- 29 runs end with the agent requesting confirmation and the user answering "yes … ###STOP###"; in 14 of them the gold is
  that last agent step (typed PrematureTermination 7, WrongActionSequence 6, …). Reading step 19 of `7b8f7044` alone, no
  monitor flags it — the "error" is a redundant question, and the proximate cause is the user simulator's stop rule.
- 198/400 runs end with STOP after an agent question of some kind (mostly "anything else?"), so the stop itself is not a
  signal; only the combination (open confirmation request + no write) is.

### 3.4 SWE-Pro: the candidate set is the edit steps, and the agent's own tests pass (n = 86)

| gold step kind | n |
|---|---|
| `str_replace_editor` create/str_replace/insert | 48 |
| bash edit (sed -i / heredoc) | 12 |
| `think` / plain message | 12 |
| bash other (git, grep, run) | 12 |
| bash test run / view | 2 |

- Edits per run: median 7 (mean 8.6); gold is an edit in 60 runs, the **first** edit in only 12, median rank 3. Gold before
  the first edit in 14 (false premise / wrong plan).
- Test runs after the gold step exist in 57 runs; in **32 of them a test run after gold passes** (the agent's chosen tests do
  not cover the hidden requirement); 17 runs never run a test. 20 final messages explicitly claim completion.
- Median 21 assistant steps after the gold (vs 3 in τ²): long post-error tails of plausible work. Fleiss κ 0.67 is
  explained by (i) 7 interchangeable edits, (ii) no transcript evidence of which one is wrong, (iii) the proposal-vs-edit
  convention (claude gold = think step at 100 vs edits at 98–130).

### 3.5 Hidden user goal (zh edition) — `inspect/trajerrbench_goal_probe.py`

`python3 -I inspect/trajerrbench_goal_probe.py --n 50 --workers 2` — the std baseline prompt with and without the zh
"用户目的" text on the same 50 τ² records (`results/trajerrbench/goal_probe_{std,goal}.jsonl`):

| condition | n | exact | within 3 | pred later | pred earlier | parse fail |
|---|---|---|---|---|---|---|
| std (en, no goal) | 50 | 22 (44 %) | 28 | 14 | 14 | 0 |
| + hidden user goal | 50 | 22 (44 %) | 29 | 17 | 10 | 1 |

Both exact 17, goal-only 5, std-only 5; the prediction changed in 16/50. **Knowing the user's goal changes *which* steps
Qwen blames but not *how many* are right** — the same pattern the literature note reports for giving Who&When judges the
ground-truth answer (−1 … +1.8 pp) and for SOAP-with-GT. The goal removes intent ambiguity but the annotators' step is
still a convention (proposal vs write, earliest vs decisive) that the goal does not pin down. The paper's zh-vs-en gap is
therefore probably small for weak judges; whether it matters for Gemini-class detectors is open.

### 3.6 Prefix probe (local detectability), τ², 20 records, window ±6 agent steps, 124 calls

`python3 -I inspect/prefix_probe.py trajerrbench --subset tau2bench --n 20 --max-steps 40 --window 6 --tag tau2`
(`results/trajerrbench/prefix_probe_tau2.jsonl`). The monitor sees policy + prefix only (no outcome, no goal).

| metric | value |
|---|---|
| gold step flagged as a mistake | 12/20 (60 %) |
| earliest flagged step == gold | 8/20 (40 %) |
| argmax-confidence step == gold | 9/20 (45 %) |
| flag rate on agent steps before gold | 9/53 (17 %) |
| flag rate on agent steps after gold | 19/51 (37 %) |

- By gold kind: tool-call golds flagged 3/4, message golds 9/16. By module: reason 7/11, obs 3/4, act 1/2, plan 1/2,
  verify 0/1.
- **Every one of the 8 unflagged golds is judged "correct" with confidence 0.72–0.95 because the step is a proposal that
  asks for confirmation**: e.g. `3dce6d78` (verify.NoVerification, gold 19) "correctly proposes the matching May 26
  booking and requests explicit confirmation"; `53f57d…` (reason.WrongChoice, 17) "correctly lists the cancellation
  details and requests confirmation"; `99e140da` (WrongChoice, 15) "presents valid exchange options with correct prices";
  `cd869b…` (act.ToolSchemaMismatch, 19) "correctly executed the tool call" although the tool returned an error next.
  Without the hidden goal or the DB diff, these proposals are indistinguishable from correct ones → H-TEB-2/3.
- Flagged golds are the policy-decidable ones: cancelling an ineligible reservation (`8f3e7…`, `f7219…`), exchange on a
  pending order (`089586`), inventing a rule ("basic economy cannot be modified", `516c89e9`), $50 bag fee inside the free
  allowance (`926caed8`), treating a personal event as insurance-covered (`f181a5ac`), assuming "#W6832752 is the latest
  order from its number" (`5609b557`). The monitor also flags the *downstream* steps (post-gold flag rate 37 % vs 17 %):
  in `8f3e7…` steps 13, 16, 18, 21, 23 — the proposal, the write, the confirmation — are all flagged; the earliest flag
  (13) is 5 steps *before* the gold, i.e. an "earlier plausible-but-not-decisive" error (P2).
- Interpretation: local detectability on τ² is bimodal — rule violations are visible from step 0's policy; candidate-
  selection and intent errors are invisible. The 52 % direct-prompting ceiling in the paper (on zh, with the goal) and the
  60 % local-flag rate here are the same number seen from two sides.

## 4. Baseline error analysis

`python3 -I baseline/all_at_once.py trajerrbench --n 80 --workers 4 --budget-tokens 150000` (Qwen3.8-27B, thinking on, no
ground truth available; `results/trajerrbench/all_at_once_std.jsonl`, `_analysis.md`).

| subset | n | agent ok | step exact | within 3 | pred later / earlier (misses) | modal miss offset |
|---|---|---|---|---|---|---|
| τ²-bench | 67 | 98.5 % | **49.3 %** | 64.2 % | 20 / 14 | **+2 (8 runs), +4 (3), −4 (3)** |
| SWE-Pro | 13 | 76.9 % | 15.4 % | 23.1 % | 3 / 7 (1 truncated) | −5 median; −92, −44, −18, +62, +28 |
| all | 80 | 95.0 % | 43.8 % | 57.5 % | | |

Categories (all): exact 35, later 1–3: 8, later > 3: 15, earlier 1–3: 3, earlier < −3: 18, truncated 1. By length: 11–30
messages 52 % exact, > 30 messages 34 %.

**τ² conditional accuracies** (from `g3_tau2_struct.json`): no post-gold tool error 30/60 exact; with one 3/7; gold =
message 26/56 (46 %); gold = tool call 7/11 (64 %); runs with no DB write 6/10; by module reason 18/35, obs 5/9, plan
5/14, act 1/2, verify 3/5. Of the 34 τ² misses, 4 land exactly on the first DB write after the gold and 8 are at +2 (the
next assistant turn, usually the write) — the proposal/commit offset of H-TEB-1 is the single largest miss mode. The model
never blames the user (0/80), as instructed by the framework description.

Reasoning excerpts (`_analysis.md`):

- *later, +2, the write instead of the proposal* — `retail/deepseek 72db038b` (gold 21 plan.WrongOrder, pred 23): the model
  sees both and argues itself into the write: "Step 21 is a proposal, but the user's confirmation could be seen as approving
  the sequence … In root cause, we usually pick the action that caused the failure, not the earlier utterance … The return
  tool call is decisive because it changed status. I'd lean 23." Textbook H-TEB-1: the model knows the convention question
  and picks the opposite answer from the annotators.
- *later, +2* — `airline/deepseek d17cfcde` (gold 15 obs.MisreadOutput, pred 17): it reads the symptom backwards from the
  final "You're all set" and stops at the recommendation step, one turn after the misread.
- *later, +2* — `airline/gpt-5 d5114820` (gold 13 reason.InvalidInference, pred 15 = the `transfer_to_human_agents` call):
  blames the conspicuous transfer, not the inference that led to it.
- *earlier, −8* — `retail/gpt-5 f3362419` (gold 17 WrongChoice, pred 9): finds a genuine but harmless policy violation
  ("three get_order_details calls in a single step, violating one tool call at a time") and, unable to see what was wrong at
  17 without the hidden goal, reports the earliest *rule* violation. Its reasoning tail enumerates hypotheses about the
  hidden task ("maybe the failure is that the agent selected silver…") — the silent-failure problem of H-TEB-2 verbatim.
- *later, +6* — `retail/deepseek de92188f` (gold 33 verify.PrematureTermination, pred 39): hunts for "made-up procedure
  details" in the tail and picks the most elaborate fabrication instead of the step where the return was left unexecuted.
- *earlier, −2* — `retail/gpt-5 ec69ace6` (gold 17 obs.IgnoreOutput, pred 15): an item-classification slip one turn before
  the labelled ignore; defensible either way (P2 ±1 ambiguity).
- *SWE, −18 / −92 / −44* — `gemini ansible`, `grok …`, `kimi openlibrary-lccn`: the model enumerates every edit ("1. Step 6
  … ✓ 2. Step 24 … ✓ …"), finds each locally correct, and either picks the one edit it can argue against or admits "I'm
  struggling to find the decisive mistake … all tests passed"; it then guesses an edit far from the label. H-TEB-4: the
  transcript does not contain the information; both the model and the annotators are guessing among ~7 edits, and only the
  annotators saw the failing tests.
- *successes* — `retail/deepseek 0498e32d` (gold 19 WrongChoice): correctly reasons that "the user had two orders containing
  hiking boots … the agent assumed the pending order … asked a leading question" (candidate-selection commitment);
  `airline/deepseek f6c82e77` (gold 21): a date arithmetic check ("created 2024-05-14 09:52, now 2024-05-15 15:00, older than
  24 h") — a policy-decidable error; `airline/gpt-5 97d825f7` (gold 14): membership + insurance eligibility read off the
  tool output. All three successes are *rule-checkable from the policy and the tool outputs*; none required the hidden goal.

What the model handles: policy violations and eligibility arithmetic (τ² reason/obs with visible evidence) — ~50 % exact and
most of the rest within +2. What it cannot do by reading: (i) silent intent mismatches (hidden goal), where it reports an
earlier harmless violation; (ii) the proposal-vs-write convention, which it resolves the other way; (iii) SWE-Pro, where it
cannot know which of 7 passing-tested edits the hidden tests reject.

## 5. Annotation issues

1. **Outcome-informed labels on silent failures** (65.5 % of τ² runs have no transcript symptom): the label is a
   reconstruction from the DB diff, not something a reader of the transcript can verify. Prevalence estimate: at least the
   `05bb39c2`-type cases where the agent's choice matches the hidden goal and the failure is in an unobservable detail;
   from the 9 read, 1 clearly undecidable, 2 ambiguous → 10–30 % of τ².
2. **Edition leakage**: zh task descriptions contain the hidden user goal (400/400) — the paper's τ² numbers (direct
   prompting 41–52 %) are not comparable to blind detection. Expect the en edition to be harder by the goal-probe delta.
3. **Proposal-step convention** (§3.1) is stated only in the detector-facing DATASET NOTES, not in the paper; it moves 79.5 %
   of τ² labels off the DB write to the preceding message. Any method tuned on Who&When-style "wrong action" labels will be
   systematically +2.
4. **User-simulator terminations blamed on the agent**: 14 runs (3.5 %) where the gold is the agent's last (reasonable)
   confirmation request.
5. Label on a tool message (1), type mis-assignments (kimi `96b9` act.WrongTool for a false premise; verify.NoVerification
   placed on a file-creation step), 17 null types.
6. SWE-Pro: 24 of 110 runs dropped for no 2-way agreement; the retained κ 0.67 is still the lowest in the family, and §3.4
   explains why no amount of annotator training will raise it: the transcript under-determines the step.

## 6. Candidate hypotheses

**H-TEB-1 "Proposal/commit offset": the decisive step is the message that proposes the wrong action; the conspicuous step
is the tool call that executes it after user consent, +2 (modal) / +4 steps later.** Evidence: §3.1 (318/400 message golds,
lag 2 in 123, 4 in 70). Test: signed offset of any detector's prediction; predicted mode +2 for DB-write-keyed scorers;
TrajDebug's "wrong commitment + violated reference" trigger definition is exactly this fix. Shared with: searchauditbench
(critical message vs final answer), agenthallu Human-Interaction (user turn vs agent's use of it), FaP (t_err W-step vs
t_obs X/V). Targeted method: candidate set = assistant messages immediately *preceding* a user "yes"/confirmation; score the
proposal against the policy, not the write.

**H-TEB-2 "Silent failures need the oracle": 65.5 % of τ² failures have no transcript symptom; attribution accuracy on them
is bounded by how much of the policy/goal the detector can reconstruct.** Test: split the baseline's exact-step accuracy by
"has post-gold symptom" (§3.2) — predicted ≥ 15 pp gap; and the goal-probe delta (§3.5). Shared with: FaP silent 28 %,
agenthallu clean-looking hallucinations, horizon env-pass/judge-fail. Targeted method: rule-grounded checking (policy
clause ↔ step) rather than anomaly scoring; for silent runs the "symptom" must be *derived* (simulate the DB rule).

**H-TEB-3 "Policy-decidable vs intent-dependent": act.*, plan.WrongOrder, obs.* and the transfer cases are decidable from
step 0 + the tool outputs (locally detectable); reason.WrongChoice/InvalidInference on candidate selection depend on the
hidden goal.** Test: prefix-probe gold-flag rate by category; predicted act/obs ≫ reason. Targeted method: two-track scorer
(constraint checker + intent-consistency checker).

**H-TEB-4 "SWE-Pro ambiguity is structural": with 7 edits per run and passing self-tests, the transcript under-determines
the gold; κ 0.67 and best detector 24 % are the ceiling, not a method gap.** Test: an oracle given the failing hidden test
names should jump far above 24 % (TrajDebug's pre-annotators with diagnostics: 31–56 %). Shared with: FaP (t_err = write
step, hidden tests), traceelephant SWE. Targeted method: map failing-test → touched symbols → edit steps (static dependency
back-trace), not LLM judgement of the transcript.

**H-TEB-5 "The user simulator is an unlabelled actor"**: in 29 runs the user ends the dialogue mid-confirmation; the agent is
blamed in 14. Any attributor that only scores assistant steps is forced to pick the last agent step; a model that reads the
user's STOP as the cause is "wrong" by convention. Test: re-label the 29 with the user turn allowed; measure how many
annotators move the blame.

## 7. Open questions

- What do the pre-annotations look like per record (not shipped)? With them one could measure P3 directly (label distance to
  Gemini's draft vs to a blind reader).
- Does the zh user goal raise exact-step accuracy mainly on WrongChoice/MissingAssumptionCheck (candidate-selection errors)?
  (goal probe, pending)
- How many of the 73 no-write runs are refusals the policy actually required (i.e. mislabelled successes)? τ²-bench's
  evaluator also checks the final assistant message content for some tasks; without the task spec we cannot tell.
