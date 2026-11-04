# HORIZON — inspection findings (G3 single-agent natural failures)

*Scripts: `inspect/horizon_stats.py`, `inspect/horizon_os_signals.py`, `inspect/horizon_os_etc.py`, `inspect/horizon_os_terminal.py`,
`inspect/horizon_web_p6.py`, `inspect/horizon_web_labels.py`, `inspect/horizon_rawdump.py`; outputs under `results/horizon/`
(`stats.md`, `os_signals.md`, `os_etc.md`, `os_terminal.md`, `web_p6.md`, `web_labels.md`, `disagreements.jsonl`, `step_labels.json`,
`os_features.json`, `os_etc_drift.json`, `web_prefix_pairs.json`, `prefix_probe.jsonl`, `all_at_once_std.jsonl`). Raw dumps read in full are in
`inspect/g3_dumps/horizon_raw__<id>.txt`.*

**One-paragraph summary.** HORIZON's labels are LLM-judge outputs, and the judge is grading a different task than the environment: it reads the
LLM-augmented step list (depth extension) or the "A AND B AND C" composite (breadth extension) without the checker, so 12.9% env/judge disagreement is
*systematic* (80.8% of it survives a second judge pass) and is mostly rubric mismatch, not evaluator error. Two prompt-construction artefacts dominate
the OS failures: **75.5% of GPT-5-mini OS failures (764/1,012) and 93% of its "Catastrophic Forgetting" labels (594/639) are the agent answering
the one-shot *example* question of the AgentBench system prompt ("how many files are in /etc?") instead of the task**, always in the last two turns;
and **38% of Claude's OS failures (321/852) end with `finish` instead of `answer(...)` after the correct number was already computed**. On the web
subset, the judge's step label coincides with the first syntactic anomaly (unparseable `Action: none` or the first identical repeated action) in 27%
of cases, is *earlier* than it in 31% and later in 26%; 30% of all step labels sit on an `Action: none` parse failure and 12 of 294 step labels are on
runs the environment scored 1.0. Cheap whole-trajectory features (length, max action repeat) separate web pass from fail with AUROC 0.85–0.91, so
"failures deviate from the normal flow" (P6) holds at the *trajectory* level here — but only because 89% of web failures end in an early-stop
(parse ×3 or max steps) and successes are 3–6 steps long. A prefix monitor flags the judge's step in 85% of 20 runs but flags 24% of earlier and 75% of later steps too; the
all-at-once baseline matches the judge on 53% of 60 runs (71% when the label is on `Action: none`, 34% otherwise), with misses split 16 earlier /
12 later — no late bias.

---

## 1. Data as loaded

- Loader: `loaders/horizon.py`; 4,006 records = 3,782 `result_2` (os 2,735 / web 597 / embodied 270 / database 180) + 224 web/GPT records that exist
  only in `result_5`. Step labels (`error_steps`) on 294 web/GPT records only (147 merged into result_2 records, 147 in result_5-only records).
- Env verdict: `passed` for os/database, `score` for web, none for embodied (outcome None). Judge label `failure_type` (`Success` or one of 7 modes)
  in `labels.extra['judge_failure_type']`, judge `reason` in `labels.reason`. A second full judge pass (`result_3`) and an earlier 1,499-record pass
  (`result_1`) exist in the raw files; the loader keeps only result_2/5 — I read result_3 directly.
- Step granularity: web = `[Step n]` blocks (Page/Agent/Action); os = `[Task]` user step then alternating agent / `OS response` env steps
  (OS `run` key = repetition 0/1/2, **the depth level is `cfK` inside the id**, K = 1..10, 11 base-task families, 262–276 runs per level); database
  and embodied = a single step. **The database "trajectory" text contains `Correct : False/True` and a `Notes` line from an earlier analysis**, i.e.
  the judge sees the env verdict (98.3% exact agreement r2/r3, 0.6% env disagreement are consequences, not independent judgments).
- `result_5` `steps` field = a 5-step window *centred on the judge's failure step* (fail at position 3 of 5 in 269/294; 274 windows have exactly 5
  entries; only 15 windows end at the last step). So it is a post-hoc excerpt, not evidence that the judge only looked at the tail.
- Loader caveat (no fix needed, note for STATUS): the OS `level` is not exposed; use `re.search(r'aug-cf(\d+)-', id)`.

## 2. Close-reading notes

Read in full (raw judge record + both passes): 8 web, 9 os, 1 database, 3 embodied = 21 trajectories; 15 of them are env/judge disagreements.

**Env-fail / judge-Success**
- `web_claude_5_mini_step_2.1_21` (score 0, 3 steps): "Show the most recent cancelled order AND tell me its total". Agent reads the table, stops with
  "#000000170 ... $365.42" (correct) without opening the order page. The "Show" sub-task is a URL check → env 0. Judge: Success. Rubric mismatch; the
  agent did the informational job. *Who is right:* env under its rubric.
- `web_claude_5_mini_step_4.1_28` (score 0, 15 steps): four-part composite; the agent cycles My Orders ↔ View Order **six times** (steps 3–14), each
  time recomputing a wrong item-sum ($350.42) and each time re-reading the right table total ($365.42), then stops with all four parts correct
  (status canceled / 365.42 / 754.99 / 65.32). Env 0 (composite string match on a four-part answer failed). *Judge right* — a genuine evaluator
  false negative, and a 12-step recovered loop inside a semantically correct run.
- `os_gpt_run_0_aug-cf2-007-bootstrap-00022` (11 turns): count lines in .txt files; agent does the preparatory steps, verifies, answers `3`; env
  False; the three repetitions of this task answer 3, 3 and "162 regular files under /etc". Expected value is not released (horizon-tasks gated).
  Judge: Success in both passes. *Undecidable*; the judge accepted a self-consistent closing it cannot verify (P4).
- `os_claude_run_1_aug-cf1-007-bootstrap-00021`: answers 102 (ls -1 /etc | wc -l); repetitions answer 204, 204; env False for all three. Same
  verdict: undecidable, judge trusts the closing. Note the heredoc/while-loop is echoed back by the harness as `> ...` continuation lines (the
  one-command-per-turn rule breaks multi-line commands).
- `os_claude_run_2_aug-cf2-002-environment-00000`: base task "add the folder into PATH"; the depth augmentation says "create a profile fragment …
  save it ready to be sourced (do **not** source it)". The agent obeys the augmentation; PATH is unchanged; env False; judge Success (both passes).
  **The augmentation contradicts the checker** — a construction flaw, and the judge grades the augmented text.
- `db_gpt_25`: IN-subquery vs JOIN "semantically equivalent"; the judge reads `Correct : False` in the record and overrides it. Unverifiable.

**Env-pass / judge-fail**
- `os_claude_run_1_aug-cf8-007-bootstrap-00023` (6 turns, cf8): eight preparatory steps prescribed; agent skips six of them, `cp` backup, counts 62
  unique characters, answers → env True. Judge: *Instruction* ("ignored the detailed multi-step requirements"). The judge penalises skipping decoy
  steps the checker never inspects. Env right.
- `os_gpt_run_1_aug-cf2-007-bootstrap-00019` (7 turns): r2 *Planning Error* for a real but harmless bug (`2>` attached to the awk stage, not find);
  r3 Success; env True. The judge found a non-fatal defect and called it the failure. Env right.
- `os_claude_run_1_aug-cf10-007-bootstrap-00003` (cf10): agent skips steps 4–9 (age computation) and answers 4 (= all files); judge r2 *CF*, r3
  *Instruction*, both say "returning 4 rather than the required ≥30-day count" — but env True, so 4 **is** the right count (all four logs are from
  2022). **The judge invented a wrong answer.** Env right.
- `os_claude_run_0_aug-cf10-005-new-00004`: same pattern (skipped dedup/report steps, correct count). Env right.
- `web_claude_5_mini_step_3.2_27` (score 1, 3 steps): adds the product to the wish list (confirmation page), then stops with the two correct totals
  *and* "Cannot add product to wishlist as no specific product is visible". Judge CF (both passes). The env checks only the two numbers. Both right:
  this is an **under-claim** (the opposite of false success) that no outcome check sees.
- `web_claude_5_mini_step_1.2_772` (score 1): "Delete all pending negative reviews for Circe fleece"; none exist; agent stops `N/A`; expected
  "Rating isn't Available". r2 Planning Error ("prematurely stopped"), r3 Success. Env right; r2 hallucinated a failure, unstable across passes.
- `web_gpt_5_mini_step_1_713` (score 1, 12 steps): "Create a best sellers report 05/01/2022–05/31/2023" (URL-match task). Agent fills both dates,
  clicks Show Report (task done at step 5), then emits `scroll [direction=down]`-style unparseable actions → `Action: none` ×5 → "Early stop: Failed
  to parse actions for 3 times". r2/r5 Planning Error, **step label 6 = the first `none`**, r3 also failure. Env right; the judge pattern-matches the
  parse-failure tail on a run that had already succeeded.
- `web_gpt_5_mini_step_1_157` (score 1): identical pattern ("Show all customers", 200-per-page selected, then `none` ×3). r2/r5 fail at step 9, r3
  Success.
- `web_claude_5_mini_step_1_258` (score 1, 31 steps): reaches the Explore-projects "All" view, then clicks 'All' 25 more times until max steps.
  Env right (state reached); judge *Environment*. A success with a 25-step loop.

**Web records with judge step labels**
- `web_gpt_5_mini_step_5.1_24` (5 steps, label 2): search typed, then `scroll [direction=down]` three times (invalid syntax in this harness →
  `Action: none`), early stop. Label = first `none`. Correct and trivially detectable from the step text: the syntax error *is* the decisive error.
- `web_gpt_5_mini_step_2.2_22` (3 steps, label 3 = the stop): judge's own reason says "the benchmark expects only 365.42, so the agent's correct
  multi-item response mismatches an ill-defined instruction" — the judge labels the final step and blames the task. I agree the agent did not "show"
  the pending order; label on the symptom.
- `web_gpt_5_mini_step_2.2_20` (64 steps, label 52, *Memory Limitation*): a 2-task composite; the agent alternates search → My Account → search →
  My Account for 50 steps (never commits to one sub-task), reads $365.42 at step 50, then navigates away. The judge labels step 52 ("lost the
  information"); the real deviation is the alternation from step 2 on. **Label is 50 steps after the loop starts** — the judge labels the one moment
  the answer was visible and dropped, i.e. the counterfactual "last chance", not the first error.
- `web_gpt_5_mini_step_2.2_18` (≥26 steps, label 4, *History Error Accumulation*): same alternation pattern (Video Games ↔ My Account ↔ My Orders);
  label 4 = the first time the agent leaves My Orders without reading it. Here the judge *does* pick the first deviation. Same pathology, two
  different conventions, two different labels (step 52 vs step 4) — the judge is not consistent about "first vs last chance".
- `web_gpt_5_mini_step_2.1_9` (15 steps, label 12, *Environment*): sub-task 1 done at step 6, report dates set, `Show Report` clicked at 11, then
  `scroll [direction=down]` ×3 → none → early stop. Label 12 = first none. The judge blames the "environment" for not parsing the agent's invalid
  syntax; the cause is the agent's action grammar. Category wrong, step right.
- `web_gpt_5_mini_step_5.2_9` (≥27 steps, label 10): five-part composite; after `Show Report` at 9 the agent leaves to Marketing at 10 (label),
  then wanders Reviews/Customers/Reports in a long non-identical cycle. Label at the first decision that abandons a finished sub-result; the
  visible symptoms (`none` at 13–14, menu-cycling) come later. One of the 27% "semantic" labels.

**OS**
- `os_gpt_run_0_aug-cf1-003-ac-00002` (13 turns, env fail, r2 CF / r3 Planning): task "is npm installed? yes/no" with one preparatory step. The
  agent rewrites `npm_detection_preflight.txt` ten times (every OS response is "output is empty", so it never sees progress), then at turn 12
  `find /etc -maxdepth 1 -type f | wc -l` and `answer(There are 54 regular files directly in /etc.)`. **This is the one-shot example question from
  the AgentBench system prompt** ("Now, my problem is: tell me how many files are in the directory /etc?"), which the judge never sees — the judge
  only gets `[Task]` + turns, so it calls it Catastrophic Forgetting.
- `os_claude_run_2_aug-cf3-005-new-00003` (CF both passes): same drift in Claude after the manifest is built ("hallucinated a step 5 to count files
  in /etc").
- `os_claude_run_1_aug-cf1-007-bootstrap-00015` (env fail, *Instruction*): directories created, counted 13, manifest written, then `Act: finish`
  instead of `answer(13)`. Decisive error = last step; the judge's category ("omitted blank line … finished instead of answering") is right. Also
  note `pwd` returns "output is empty" three times (harness swallows `pwd` output in 86% of 154 calls).

**Database / embodied**
- `db_claude_61`: one step; the record itself contains `Correct : False` and `Notes : Planning/implementation error …`; the judge paraphrases the
  notes. Not an independent label.
- `embodied_gpt_01KJP58WBAR097E0Z1GV8F6J2V` (7-line primitive plan, hard-coded poses): r2/r3 Planning Error "no perception"; every plan in this
  domain hard-codes poses, so the criticism applies to successes too. `embodied_claude_01KJPDZEK9YZ65V379E1MWARPY`: r2 *False Assumption*, r3
  *Success* on the identical 10-line plan. `embodied_gpt_01KJP64ECEVPBC8XN4E0GMVZCY`: Success/Success. Embodied labels are coin-flips on plans the
  judge cannot execute (pass/fail agreement between passes 74.1%, no env verdict at all).

## 3. Targeted statistics

### 3.1 Env verdict vs judge (result_2), and judge self-consistency

| group | n | both pass | both fail | env pass / judge FAIL | env fail / judge SUCCESS | disagree % |
|---|---|---|---|---|---|---|
| database | 180 | 66 | 113 | 0 | 1 | 0.6 |
| os | 2,735 | 697 | 1,637 | 174 | 227 | 14.7 |
| web | 597 | 146 | 401 | 26 | 24 | 8.4 |
| model=claude | 1,907 | 534 | 1,101 | 146 | 126 | 14.3 |
| model=gpt | 1,605 | 375 | 1,050 | 54 | 126 | 11.2 |

- Judge label given to env-PASS runs: Instruction 97, Planning 74, CF 12, Environment 12, FA 4, HEA 1 — i.e. *process* complaints (skipped decoy
  steps, harmless bugs, loops after success), never "wrong answer" that the checker confirms.
- result_2 disagrees with env on 452 runs; **result_3 disagrees on the same side in 365 of them (80.8%)** → the disagreement is a property of the
  judge's rubric, not sampling noise. When r2 and r3 split on pass/fail (144 runs), r3 matches env 87 times, r2 57.
- r2 vs r3 exact label agreement: database 98.3 / web 87.6 / os 74.6 / embodied 70.0 (pass-fail 100 / 98.5 / 95.1 / **74.1**). By length: 1–5
  steps 85.2, 6–15 77.2, 16–30 67.0, >30 78.4. Top confusions CF→Planning 204, Instruction↔Planning 213, Planning→CF 98, Success↔Planning 128.
  r1–r2 (450 shared ids): 84.7 exact; r5–r2 (147 web ids): 85.0.
- OS by depth level (cf1→cf10): env pass 57→12%, judge pass 74→7%, CF share 9→42%, r2=r3 90→69%; EFJS falls from 55 (cf1) to 2 (cf10) while
  EPJF stays 9–30: at deep levels the judge *over*-fails (more decoy steps to skip), at shallow levels it *over*-passes.

### 3.2 Where the judge puts `failure_step_number` (294 web/GPT labels)

| statistic | n | % |
|---|---|---|
| label == last step | 8 | 2.7 |
| label within last 5 steps | 123 | 41.8 |
| label within first 5 steps | 134 | 45.6 |
| label on an `Action: none` (unparseable action) | 88 | 29.9 |
| label is first of two identical consecutive actions (loop start) | 29 | 9.9 |
| label repeats an earlier (non-consecutive) action | 91 | 31.0 |
| label is the stop action | 8 | 2.7 |
| none of these (needs semantics to find) | 78 | 26.5 |
| label on a run with env score 1.0 | 12 | 4.1 |

Label vs the first syntactic anomaly in the run (earliest of: start of the first identical-consecutive pair, first `none`):

| relation | n | % |
|---|---|---|
| run has no syntactic anomaly | 47 | 16.0 |
| label == first anomaly | 80 | 27.2 |
| label BEFORE first anomaly | 92 | 31.3 (median −8, min −107) |
| label 1–3 after | 37 | 12.6 |
| label >3 after | 38 | 12.9 (max +40) |

By type, label == first anomaly: Environment 10/17, Planning 69/252, FA 1/7, HEA 0/5, Memory 0/5, Instruction 0/8. Label action type: click 123,
none 88, type 50, goto 20, stop 8. Relative position is flat across deciles (49/35/26/24/24/36/33/25/27/15) — no first/last-step prior.
Judge reason keywords (294): loop/repeat 77%, early stop/max steps 30%, parse/none/invalid action 28%, "navigated away / instead of reading" 21%,
wrong value/misread 13%, forgot/lost 3% — the judge explains the label by the *loop* in three quarters of cases even when the label itself is not on
the loop (loop-start labels are 9.9%): it points at a step and justifies it with the symptom that follows.

### 3.3 Web: pass vs fail cheap features (P6 test) and prefix sharing across levels

| model | n fail | n pass | steps fail/pass | consecutive identical action % f/p | same action ≥3× % f/p | has `none` % f/p | AUROC n_steps | AUROC max-repeat | AUROC consec |
|---|---|---|---|---|---|---|---|---|---|
| gpt | 104 | 45 | 36.4 / 6.2 | 40 / 2 | 73 / 7 | 61 / 58 | 0.867 | 0.879 | 0.686 |
| claude | 321 | 127 | 29.4 / 4.3 | 29 / 2 | 64 / 8 | 43 / 3 | 0.913 | 0.835 | 0.631 |
| all | 425 | 172 | 31.1 / 4.8 | 32 / 2 | 66 / 8 | 47 / 17 | 0.898 | 0.845 | 0.645 |

Stop type × outcome: max-steps early stop 224 fail / 8 pass; parse early stop ("Failed to parse actions for 3 times") 153 fail / 13 pass;
`stop[answer]` 48 fail / 151 pass. **89% of web failures end in an early stop**; only 48 failures are wrong-answer stops.
Same-task pairs (passing run at a lower level, failing run at a higher level, same model): 223 pairs; longest common action prefix mean 2.0; in
204/223 (91%) the failing run reproduces the *entire* passing run (which is 3 steps) before diverging; of 20 pairs with a step label, 0 labels fall
inside the shared prefix, 2 at the first divergent step, 18 later.

### 3.4 OS: signals by env × judge, cheap-feature AUROC, and the two prompt artefacts

| env | judge | n | turns | same cmd ≥3× % | swallowed output % | error resp % | ends `finish` % | ends `answer` % | answer-format mismatch % |
|---|---|---|---|---|---|---|---|---|---|
| fail | Catastrophic Forgetting | 710 | 11.5 | 2 | 87 | 36 | 2 | 98 | 93 |
| fail | Instruction | 406 | 18.7 | 8 | 98 | 31 | 71 | 27 | 45 |
| fail | Planning Error | 487 | 15.3 | 4 | 95 | 34 | 46 | 53 | 69 |
| fail | Success | 227 | 10.0 | 2 | 93 | 10 | 14 | 86 | 5 |
| pass | Instruction | 97 | 13.6 | 3 | 92 | 18 | 5 | 95 | 3 |
| pass | Planning Error | 58 | 10.8 | 0 | 83 | 29 | 3 | 97 | 3 |
| pass | Success | 697 | 9.4 | 1 | 89 | 15 | 1 | 99 | 6 |

AUROC for env FAIL from one feature: GPT — n_turns 0.71, cf level 0.73, answer-format mismatch 0.72, repeats 0.53; Claude — n_turns 0.80, ends-finish
0.81, n_empty 0.74, repeats 0.57. Loops/repeats are *not* what separates OS failures; terminal-action shape is.

**Artefact A — the one-shot example leaks.** The AgentBench system prompt ends "Now, my problem is: tell me how many files are in the directory
/etc?" and the real task follows; HORIZON's prompt even warns "IGNORE THE EXAMPLE". Among runs whose task never mentions /etc:

| model | env | n | final answer mentions /etc | any `/etc` command |
|---|---|---|---|---|
| gpt | fail | 972 | **786 (80.9%)** | 828 (85.2%) |
| gpt | pass | 337 | 5 (1.5%) | 8 (2.4%) |
| claude | fail | 819 | 59 (7.2%) | 99 (12.1%) |
| claude | pass | 493 | 0 | 4 (0.8%) |

Judge label of the 764 drifted GPT failures: CF 594, Planning 168, Environment 3, FA 3, **Success 1**; r3: CF 485, Planning 282. **594/639 (93%) of
all GPT "Catastrophic Forgetting" labels and 764/1,012 (75.5%) of all GPT OS failures are this one mechanism.** The drift happens at turn 8.6 of
10.7 on average, and in 810/836 GPT runs exactly two turns remain after it (the `/etc` count + the answer): the agent finishes the inserted
preparatory steps, then "answers" the example. Before the drift, 71% of OS responses were "output is empty" (GPT overall 67%); 14% of runs had a
repeated command. Claude drifts in 103 runs, later (turn 11.8 of 18.8) and with more turns after.

**Artefact B — `finish` instead of `answer`.** Claude env-fail runs: 549/852 end with `finish`; in 321 the task text explicitly asks for an answer,
and in 290 of those a number already appears in the final Think. Claude env-pass: 0/517. GPT: 2. The judge files these as Instruction (71% of
Instruction labels end in finish) or Planning.

**Harness quirk.** `pwd` returns "The output of the OS is empty" in 128/148 calls (86%), `echo` without redirect 61%, `whoami` 25%; `cat`/`ls`/`wc`
≤6%. Agents react by re-running commands (the `npm` case above rewrites the same file ten times). The judge, which does not know the harness, blames
the agent.

### 3.5 Prefix probe (web/GPT, 20 labelled records ≤ 40 steps, 379 probes, Qwen3.8-27B, no outcome shown)

| metric | value |
|---|---|
| gold step flagged as a mistake (local detectability) | 17/20 (85%) |
| earliest flagged step == gold | 7/20 (35%) |
| argmax-confidence step == gold | 1/20 (5%) |
| flag rate on steps BEFORE the gold step | 52/216 (24.1%) |
| flag rate on steps AFTER the gold step | 107/143 (74.8%) |
| gold on an `Action: none` step: flagged | 7/7 (earliest == gold in 3) |
| gold on a real action: flagged / earliest == gold | 10/13 / 4/13 |

- The monitor flags the judge's step in 85% but it has already flagged something earlier in 13/20 runs. What it flags earlier: redundant/looping
  actions (26 of 52 pre-gold flags), "abandons page X before extracting Y" (18), parse no-ops (8). In `web_gpt_5_mini_step_4_12` (24 steps, label
  20) it flags 13 of the 20 pre-label steps — the whole run is a search ↔ My-Orders alternation and the judge's label is simply the last of many
  equivalent deviations. In `web_gpt_5_mini_step_4.1_4` (40 steps, label 35) the monitor flags step 4 ("navigates to Reports instead of cancelling
  order 302") and 11 more before the judge's step.
- The three misses (`2_2` label 9, `3.2_11` label 4, `4.2_8` label 5) are judged "a reasonable next step" / "redundant but not clearly erroneous":
  the judge's step there is an ordinary navigation click whose wrongness is only visible from what follows (P1-type labels).
- After the label the monitor flags 75% of steps — the tail of every run is none/early-stop/loop — so an "earliest flag" rule lands before the label
  and an "argmax" rule lands after it; neither recovers the judge's convention. This is the SOAP contamination picture on a judge-labelled set:
  the judge's step is locally detectable (85%) but not locally *distinguished* from its neighbours.

## 4. Baseline error analysis

(all-at-once, Qwen3.8-27B, 60 web/GPT records with judge step labels; `results/horizon/all_at_once_std.jsonl`, `_analysis.md`)

Note: the "gold" here is the LLM judge's step; agreement measures judge–judge concordance, not correctness.

| | n | exact | within 3 | earlier | later |
|---|---|---|---|---|---|
| all | 60 | 53.3% | 76.7% | 16 | 12 |
| ≤10 steps | 21 | 85.7% | 100% | | |
| 11–30 steps | 14 | 42.9% | 71.4% | | |
| >30 steps | 25 | 32.0% | 60.0% | | |
| gold on `Action: none` | 21 | 15 (71%) | | 5 | 1 |
| gold at a loop start | 7 | 6 (86%) | | 1 | 0 |
| gold "semantic" | 32 | 11 (34%) | | 10 | 11 |

- **The model handles what the judge handles: parse failures and loop starts.** 21/32 exact hits are on `none`/loop-start labels; on semantic
  labels it is at 34% with misses split evenly earlier and later — no late bias on this set (16 earlier vs 12 later overall), against P1's
  prediction for a prompted judge.
- **Both judges reason from the early-stop backwards.** Success excerpts: `web_gpt_5_mini_step_2.2_26` — "the system final output says failed to
  parse actions for 3 times, corresponding steps 3,4,5. Step 3 first"; `web_gpt_5_mini_step_1_260` (an env-PASS run) — same chain, both judges
  label step 6 on a run that succeeded; `web_gpt_5_mini_step_5_26` (loop start) — "steps 10–12 repeat the same mistake, step 6 is the original".
  The attributor is given `SYSTEM FINAL OUTPUT: Early stop: Failed to parse actions for 3 times` and counts back three steps; the trajectory text
  encodes the label, which is why `none` labels are "easy".
- **Failures read in full (9):**
  - `web_gpt_5_mini_step_4_10` (78 steps, gold 5, pred 74, +69): judge "no coherent decomposition … looping between Invoices and Reports" (step 5);
    model: "if step 6 had been correct, would the task succeed? Not necessarily, it still looped. Step 74 is more direct" → first of the final
    three parse failures. Two defensible conventions (earliest deviation vs last decisive act); the counterfactual wording of the prompt pushes
    the model *late* on long loops.
  - `web_gpt_5_mini_step_2.1_26` (21, gold 17 = first none, pred 4, −13): the model treats the parse failures as symptoms of an earlier detour
    ("clicked an unrelated product link instead of reading the order total"), debates "step 17 is more defensible" and keeps 4. Earlier than the
    judge and arguably right: the order total was on screen at step 3.
  - `web_gpt_5_mini_step_2.1_24` (11, gold 1, category Environment, pred 7): the judge put the label on a lone `none` at step 1 that the agent
    recovered from; the model picks the first of the three fatal nones at 7 and says step 1 "would not have made the task succeed". Judge wrong.
  - `web_gpt_5_mini_step_3.2_3` (91, gold 11, pred 16, +5): judge blames misreading "126 records found" as the review count; model blames
    abandoning the Bestsellers report. Both are deviations in a 91-step wander.
  - `web_gpt_5_mini_step_4_8` (14, gold 6 Instruction, pred 10): thinking rejects its own pick ("the action is not wrong … trailing space is
    minor") and emits it anyway — symptom reflex under JSON pressure.
  - `web_gpt_5_mini_step_3.1_20` (91, gold 5, pred 2) and `web_gpt_5_mini_step_4.1_12` (44, gold 3, pred 2): the search ↔ account alternation;
    the model picks the first re-search, the judge the first irrelevant action one cycle later. A ±1-cycle tolerance merges them.
  - `web_gpt_5_mini_step_5.1_10` (77, gold 26, pred 35, +9) and `web_gpt_5_mini_step_3.2_0` (17, gold 7, pred 4, −3): the model invents an
    environment explanation ("date picker expected MM/DD/YYYY") for a redundant-typing loop; it over-explains loops as environment faults when the
    observation never changes.
- **What whole-trajectory reasoning cannot do here:** fix a convention. The model switches between "first deviation" and "last chance" depending
  on the tail (parse stop → count back three; max-steps loop → hunt for the first detour). It also cannot tell that 3 of its 60 inputs are env-PASS
  runs (`1_157`, `1_597`, `1_260`): it labelled a failure step in all three, exactly like the judge. Trajectory types it handles: short runs ending
  in a parse stop (≤10 steps: 86%); types it cannot: long multi-sub-task wanders (>30 steps: 32%, misses both directions).

## 5. Annotation issues (prevalence estimates)

1. **Judge grades the augmented text, env grades the base task** — 12.9% env/judge disagreement, 80.8% stable across passes; on env-pass runs the
   judge's complaint is skipped decoy steps (97 Instruction + 74 Planning of 184 OS EPJF). Prevalence: ~7% of OS runs and ~4% of web runs carry a
   failure label on a passing run; ~8% of OS runs carry a Success label on a failing run.
2. **Judge cannot verify answers** (no checker, no ground truth for OS): 227 OS "Success" labels on env-fail runs, 86% of them ending with a
   confident `answer(...)` (P4). In the two OS cases I could cross-check with sibling runs, the siblings answered different values (3 / 162; 102 /
   204), so at least some of these are wrong answers the judge waved through.
3. **Catastrophic Forgetting is 93% a prompt artefact on GPT** (§3.4 A). The paper's "GPT failures 18.3% Memory / 64.9% Planning" and the OS
   degradation curve for GPT-5-mini are driven by example-question leakage that happens at the end of the run regardless of depth (drift share of
   GPT fails is 75% at every level). The judge, not seeing the system prompt, invents a memory explanation. Category labels for GPT-OS are therefore
   not about long-horizon memory.
4. **Judge step labels are symptom-coincident in a known fraction**: 30% sit on `Action: none` (a harness parse failure), 2.7% on the stop, 12 of
   294 on runs that passed. The 31% that sit *before* the first syntactic anomaly are the interesting ones (judge reasons like "navigated away
   instead of reading the report"), but the same pathology (sub-task alternation) is labelled at step 4 in one run and step 52 in another.
5. **Database labels are not independent** (record text contains the verdict); **embodied labels are noise** (26% pass/fail flip between passes,
   no env verdict; identical plans get Success and False Assumption).
6. **Category instability**: 25.4% of labels change between two passes of the same judge on the same text; CF↔Planning and Instruction↔Planning
   account for 60% of the changes. Category-level evaluation on HORIZON has a ceiling of ~75% exact agreement.
7. **Model-dependent label semantics**: CF is 68% of GPT judged-failures vs 9% of Claude's; Instruction is 45% of Claude's vs 2% of GPT's. These
   track the two terminal-action artefacts, not cognitive failure modes.

## 6. Candidate hypotheses

**H1. Terminal-action artefacts dominate "natural" single-agent failures, and they are label-free detectable.**
*Statement:* In harness-driven single-agent benchmarks a majority of failures are decided in the final 1–2 agent turns by a formatting/termination
act (wrong terminal action, wrong answer format, answering the in-context example, unparseable action), not by a mid-trajectory reasoning error.
*Evidence:* HORIZON OS: 75.5% of GPT failures = example-question drift (two turns from the end), 38% of Claude failures = finish-without-answer;
web: 36% of failures end in a parse early stop. *Test:* regex detectors (`/etc` when the task has none; `Act: finish` when the task asks for an
answer; `Action: none` ×3) vs env verdict on all 3,332 runs — expect precision >0.95 on GPT-OS and Claude-OS. Then check TrajErrBench τ² (transfer
to human/`transfer_to_human_agents`), AgentErrorBench (format errors, step-limit), AgentHallu BFCL (missing required call) for the same
tail-of-run concentration. *Method:* a terminal-action checker should run *before* any step-level attributor; attribution effort is wasted on runs
whose decisive step is the last one.

**H2. The judge's step label is a mixture of two conventions — "first deviation" and "last chance" — and the mixture weight depends on whether the
run has a syntactic anomaly.** *Evidence:* label == first anomaly 27%, before 31%, after 26%; Memory-Limitation labels sit at the moment the
answer was visible and dropped (step 52 of 64), HEA labels at the first abandonment (step 4). *Test:* re-judge the 294 web runs with the two
conventions stated explicitly and measure which one the released labels match; compare to AgentHallu (counterfactual "fix it and re-roll" = last
chance) and TrajErrBench (earliest). *Method:* an attributor should output both an earliest-deviation step and a last-recoverable step; score
against each.

**H3. Prompt-construction leakage masquerades as a cognitive failure mode in judge-labelled taxonomies.** *Statement:* When a judge sees the
trajectory but not the system prompt, any drift induced by the prompt (examples, conflicting augmented instructions) is labelled as forgetting /
planning. *Evidence:* §3.4 A (594/639 CF labels), the "do not source it" contradiction. *Test:* re-run the HORIZON judge with the system prompt
included on the 836 drifted runs; predict the CF label rate drops below 20% and "Instruction/Environment" rises. *Shared with:* MAST-Data
(judge-labelled modes), AgentErrorBench system.* labels, failure_as_process "false premise" triggers. *Method:* feed the attributor the full
prompt and flag any agent turn whose target (path, entity) appears only in the example, never in the task.

**H4. Loops are symptoms of composite tasks, not causes, and a loop-start label is a convention.** *Evidence:* 66% of web failures contain the same
action ≥3× vs 8% of passes, but the two successes with 25-step and 12-step loops show loops are survivable; judge labels sit at the loop start in
only 9.9%, and the alternation pathology (search ↔ account) starts at step 2 while the label lands anywhere between 4 and 52. *Test:* for the 215
web failures with a loop, compute the first step at which the agent leaves a page that contained the answer; compare to the label. *Shared with:*
AgentErrorBench ALFWorld (30-step cap, early labels), Who&When HC. *Method:* a loop detector gives the *symptom* time; attribution needs the last
page-with-answer before the loop.

**H5. "Normal flow" separation (P6) holds at the trajectory level only because successes are short and failures are early-stopped.**
*Evidence:* AUROC(n_steps) 0.87–0.91 for web, 0.71–0.80 for OS; max-repeat AUROC 0.85 web but 0.53–0.57 OS. In OS the discriminating features are
terminal-action ones (finish 0.81, format 0.72), not dynamics. The 91% whole-prefix reproduction between a passing lower-level run and a failing
higher-level run says the "normal flow" of the composite is literally the success of the first sub-task followed by divergence. *Test:* fit OAT-style
one-class scorers on HORIZON web successes and check whether their step scores peak at the first divergent step (LCP+1) or at the early-stop tail.
*Shared with:* AgentHallu (250 successes), failure_as_process PASS runs.

**H6. Judge "Success" on failing runs is confidence-driven (P4), and "failure" on passing runs is process-driven.** *Evidence:* EFJS runs end with
`answer()` 86% and have the fewest error responses (10%); EPJF labels are Instruction/Planning about skipped steps or harmless bugs. *Test:* train
a TF-IDF classifier on the final agent turn to predict judge-Success vs env-fail (expect AUROC >0.8), as in the False-Success paper. *Method:* an
attributor that has the env verdict should discard judge Success labels on failing runs rather than learn from them.

## 7. Open questions

- The expected answers for OS tasks (horizon-tasks, gated) are needed to decide the 227 OS EFJS cases; sibling-run disagreement (3 vs 162; 102 vs
  204) suggests a share are genuinely wrong, but the 86% swallowed-`pwd` rate suggests the checker container may also differ from the agent's.
- Why does GPT-5-mini drift to the example only at the *end* (turn n−2) and almost never at turn 1 (1%)? A hypothesis worth a 50-run probe: the
  inserted preparatory steps exhaust the "task" attention and the model re-reads the prompt from the top, where "my problem is: /etc" comes first.
- Is the parse early stop (`scroll [direction=down]`) a GPT-5-mini-specific grammar error? 61% of its failures contain a `none` vs 43% of Claude's;
  the 13 passing runs with parse early stops show it is not fatal when the URL state is already reached.
- Does the judge window (`steps`, ±2 around the label) reflect what the judge *read*, or a post-hoc excerpt? The 269/294 centred windows say
  post-hoc; the paper does not say whether the judge saw the full trajectory for the 151-step runs.


## 4b. Baseline results (filled from results/horizon/ after the runner finished, 2026-11-01)

Qwen3.8-27B all-at-once, gold = judge failure_step_number; `step_in_set` counts a prediction inside the full labelled set.
Signed categories: `later` = predicted after the gold (symptom side), `earlier` = before it. Reasoning excerpts for
failures and successes are in `results/horizon/all_at_once_std_analysis.md`.

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| web | 60 | 100.0 | 53.3 | 76.7 | 53.3 |
| ALL | 60 | 100.0 | 53.3 | 76.7 | 53.3 |

categories: {'exact': 32, 'earlier(-1..3)': 9, 'later(+1..3)': 5, 'later(>3)': 7, 'earlier(<-3)': 7}
agent right but step wrong: 28; step right but agent wrong: 0
| n_steps | n | step_exact% | within3% | agent% |
|---|---|---|---|---|
| 0-10 | 21 | 85.7 | 100.0 | 100.0 |
| 11-30 | 14 | 42.9 | 71.4 | 100.0 |
| 31-1000 | 25 | 32.0 | 60.0 | 100.0 |
wrote results/horizon/all_at_once_std_analysis.md
