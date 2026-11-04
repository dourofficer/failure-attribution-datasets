# CORRECT-Error — inspection notes (G4)

Scripts: `inspect/correct_error_stats.py` (→ `results/correct_error/stats.md`), `inspect/g4_dump.py`, `inspect/g4_label_check.py`.
Dump of 20 read trajectories: `results/correct_error/close_reading_dump.txt`.

## 1. Data as loaded

- 2,226 rows, one Magentic-One-variant selector group chat (Planner / WebSurfer / Coder / CodeExecutor / FileSurfer; user message at idx 0), 7 benchmarks (wikimqa 733, hotpot 578, musique 312, arc 304, math500 157, mmlu_pro 92, gaia 50), gpt-5-nano 1,908 / gpt-4o-mini 318. No GT, no reason, no categories; `mistake_agent` free text (Planner 73.6%, WebSurfer 21%, `Unknown` 42, Coder/CodeExecutor/Orchestrator/Solver …).
- Loader is fine; `mistake_step` is a 0-based index into `history` (user message at 0), 43 rows point at 0.
- Length is bimodal: 610 rows ≤ 4 steps (ARC/MMLU-Pro: Planner answers from parametric knowledge in one turn), 809 rows at 21–22 steps (a round cap).

## 2. Close-reading notes (20 trajectories)

| id | bench / n | label | what the rewritten step does | wrong vs prefix? | continuation |
|---|---|---|---|---|---|
| musique_task306_1 | musique / 10 | 9 Planner (last) | "Analysis" recaps three sources saying 323 BCE, then "Updated Understanding: Death year: 322 BCE" with a made-up justification ("normalized … astronomical -322 convention") | **yes, within the same step** | none (last) |
| musique_task85_3 | musique / 22 | 3 Planner | reinterprets "founder of the Liberal Party became PM" as the 1949 election instead of the 1939 Lyons death already found at step 1 | yes vs own step 1 | 18 steps of Planner re-asking WebSurfer the same verification queries until the cap; a Planner→Planner turn right after the rewrite (selector artefact) |
| arc_task6_1, arc_task27_1, gaia_task122_2 | 2 steps | 1 Planner | one-turn parametric answer rewritten (hibernation insulation; "red is hottest"; "Transformer encoder has 8 layers → 4 more") | factual only | none |
| math500_task242_3 | math500 / 7 | 3 Planner | "5 years → **60** bi-monthly periods" after step 1 computed 30 periods | yes vs own step 1 | CodeExecutor computes with 60; loyal |
| math500_task94_1 | math500 / 8 | 7 Planner (last) | final-answer rewrite | partly | none |
| mmlu_pro_task1_1, _task53_1 | 4 steps | 3 Planner (last) | final-answer rewrite after one search | — | none |
| musique_task479_3 | musique / 21 | 0 user, `Unknown` | **the task text itself was rewritten** ("Let me know if you want a concrete, safe test plan …"); the run then searches for "first-action analysis frameworks" for 20 steps | n/a | the whole run is garbage |
| arc_task39_1, arc_task178_1 | arc / 8, 4 | 0 user, `Unknown` | the task is intact; the real error is later (task178: step 3 "MgBr₂ corresponds to option D: Mg₃Br₂") | n/a | label is wrong; the rewritten step is unrecorded |
| wikimqa_task273_1 | wikimqa / 4 | 2 WebSurfer | an ordinary search step; nothing visibly wrong; Planner answers "Scotland" at 3 | no | — |
| gaia_task41_4 | gaia / 12 | 11 Planner (last) | final answer "cuddly" where the evidence says "cuddly or fluffy" (GAIA GT: fluffy) | ambiguous | none |
| hotpot_task359_3, hotpot_task69_2, wikimqa_task49_2 / 377_3 / 324_1 / 64_2 | 21–22 steps | 1–6 Planner | an early Planner turn that mis-states the entity / question, followed by 15–20 steps of search–verify loops to the cap | mostly yes vs the step before | loop to cap; WebSurfer pages (DuckDuckGo result pages) carry the true facts repeatedly, the Planner keeps its reinterpretation |

Recurring observations:
1. **The rewritten Planner step has a characteristic shape**: a correct "Analysis of Previous Result" that quotes the evidence, then an "Updated Understanding" that contradicts it, plus an over-long justification. The contradiction is *inside the step* or against the agent's own previous turn (306, 85, 242, 178-style). The rewriter (GPT-5 strategy + generator model) tends to keep the recap and change the conclusion — the seam is visible.
2. **Two regimes by length**: ≤4-step rows are "rewrite the only answer" (label = last step, trivially); 21–22-step rows are "rewrite an early interpretation and let the system loop to the cap" (label median ≈ 3–6, then 15+ steps of repetition). The loop is a loud *natural* symptom produced by the base system's inability to terminate, not a consequence specific to the error.
3. **`Unknown`/user-labelled rows (43)** are of two kinds: the task was rewritten (479), or the record of the rewritten step was lost (178: the error is at step 3). Either way the label is unusable.
4. Suffix loyalty: after the rewrite, the Planner's later turns restate the wrong understanding every round ("the correct interpretation is …") — the error becomes the *most repeated* content of the trajectory, which is the opposite of a symptom.

## 3. Targeted statistics (`results/correct_error/stats.md`)

### 3a. Position / agent priors

| benchmark | n | steps | label = last step % | last step is Planner % | label agent Planner % | labelled step has FINAL ANSWER/TERMINATE % | label at user msg | agent/step mismatch % | steps after label (mean) |
|---|---|---|---|---|---|---|---|---|---|
| arc | 304 | 5.3 | 81.6 | 88.8 | 87.8 | 84.2 | 11 | 7.9 | 2.2 |
| gaia | 50 | 10.9 | 64.0 | 84.0 | 62.0 | 64.0 | 0 | 10.0 | 2.2 |
| hotpot | 578 | 12.8 | 41.7 | 58.3 | 73.2 | 48.8 | 8 | 6.7 | 6.7 |
| math500 | 157 | 6.3 | 65.0 | 96.8 | 60.5 | 65.6 | 3 | 30.6 | 2.0 |
| mmlu_pro | 92 | 6.1 | 71.7 | 87.0 | 83.7 | 71.7 | 6 | 12.0 | 3.1 |
| musique | 312 | 14.7 | 36.5 | 50.0 | 74.4 | 50.0 | 6 | 5.8 | 7.6 |
| wikimqa | 733 | 14.5 | 42.2 | 56.2 | 70.1 | 49.1 | 9 | 5.6 | 6.8 |
| ALL | 2226 | 11.8 | **50.0** | 65.1 | 73.6 | 56.4 | 43 | 8.4 | 5.6 |

- "last step + its agent" rule: step 50.0%, step+agent 47.9% — above every LLM-as-judge Acc@1 the paper reports (6–63% per task) and close to CORRECT's own average.
- Distance label→end is bimodal: 0 steps 50.0%, 1 step 7.3%, 2–5 steps 5.0%, **≥6 steps 37.6%**. There is almost no middle ground: either the error is the last step or it is followed by a long loop.
- Agent/step mismatch 8.4%: WebSurfer→Planner 55 (the label names the Planner but the index points at the WebSurfer turn; the Planner spoke at k-1 in 92 of the 186 mismatches), user→Unknown 42, Planner→WebSurfer 32, Planner→Orchestrator/Coder/Solver/… 40 (free-text agent names). math500 has 30.6% mismatch (the label says Coder/CodeExecutor, the index points at the Planner turn that *contains* the code).
- 599 questions have >1 injected variant (1,385 rows); only 165 variant groups share a step count and 68 share the prefix up to the earliest label — the variants are mostly re-runs with different injection points (e.g. labels [3,0,2], [5,3,5]), not the same run with a different step rewritten. So the dataset does not provide the clean "same prefix, different injected step" contrast its construction suggests.

### 3b. Prefix vs suffix inconsistency (LLM, `g4_label_check.py correct_error --n 40`)

Qwen3.8-27B auditor, labelled step marked, no GT/outcome, 40 random rows (`results/correct_error/label_check.jsonl`):

| rows | n | local_wrong (prefix only) | contradicts_prefix | corrected_later | symptoms_later | decisive = yes | no_later | no_other | "nothing visible" | style_odd |
|---|---|---|---|---|---|---|---|---|---|---|
| label is the last step | 19 | **100%** | 63% | 0% | 0% | **95%** | 0% | 5% | 0% | 11% |
| label followed by 1–5 steps | 4 | 25% | 25% | 0% | 25% | 25% | 0% | 50% | 75% | 0% |
| label followed by ≥6 steps (loop rows) | 17 | 65% | 59% | **53%** | 53% | **12%** | 41% | 41% | 35% | 29% |
| all | 40 | 77.5% | 57.5% | 22.5% | 25% | 52.5% | 17.5% | 25% | 22.5% | 17.5% |

- The prediction held for the terminal rows: the rewritten final step is always locally wrong and in 63% it contradicts its own recap / the previous turn ("changes the source-supported date June 10, 1819 into October 6, 1819", "concludes John Sturges was born first despite James Cruze's 1884 birth date").
- It did **not** hold for the loop rows: in 53% the auditor finds the rewritten step *corrected later* (the Planner's next turn restates the right fact; the run still loops to the cap) and in only 12% does it call the labelled step decisive — it blames a later turn (41%) or nothing/the environment (41%). In 35% it sees nothing wrong at the marked step at all (several of these are WebSurfer/user-indexed labels, i.e. the off-by-one of §3a). So the long regime contains a large share of rows where the injected error was absorbed and the failure is the base system's looping; the label is right by construction and wrong by content.
- Symptoms after the label are the loop itself (listed as every second step to the cap); `style_odd` is low (≤29%): the rewrite keeps the Planner's voice.

### 3c. Loop structure and the Planner→Planner seam (no LLM; `results/correct_error/stats.md` §b)

| rows | n | label last | Planner→Planner adjacency right after the label | any adjacency in the run | Planner "Updated Understanding" after the label verbatim-repeating an earlier one |
|---|---|---|---|---|---|
| long (21–22 steps) | 809 | 0% | **56.5%** | 59.3% | 144/5,598 (3%) |
| mid (5–20) | 807 | 70% | 10.4% | 10.7% | 0% |
| short (≤4) | 610 | 90% | 0.2% | 0.7% | 0% |

- The selector group chat never schedules the Planner twice in a row on its own (0.7% of short runs); in the long rows a Planner→Planner pair exists in 59% of runs and in 95% of those the *first* such pair starts at the labelled step. The rewrite inserted/replaced a Planner turn and the original Planner turn (or a re-run) follows it: a **structural seam**.
- Rule "first Planner→Planner adjacency, else last step" with no text reading: **74.0% exact, 81.0% within ±1** over all 2,226 rows (last-step rule alone 50.0%). Among the 570 rows with an adjacency: 94.6% exact. The paper's best numbers (CORRECT, Qwen-2.5-7B, Acc@1 17–80% per task) and every LLM-judge baseline (6–63%) are below this rule.
- Repetition after the label is paraphrased, not verbatim (3%); a change-point on the Planner's "Updated Understanding" text finds the label in only 13% (long rows), so the loop is not a clean localiser — the seam is.

## 4. Baseline error analysis

PENDING — `all_at_once.py correct_error --n 80 --no-gt` (chain C). Will categorise with `analyze_baseline.py` and additionally split by (label = last step) vs (≥6 steps after); prediction: near-perfect on the first group (judge names the final answer), "later" misses on the second group (judge blames a step inside the loop).

## 5. Annotation / construction issues (prevalence)

1. **50% of labels are the last step** and 56% of labelled steps contain the final answer: the task collapses to "is the final answer wrong?" on half of the data.
1b. **A structural seam locates the label in most of the rest**: Planner→Planner adjacency starts at the labelled step in 540/2,226 rows (24%); combined with the last-step rule a text-free predictor reaches 74.0% exact (§3c). Any accuracy reported on CORRECT-Error must be compared against 74%, not against the 6–63% LLM-judge baselines.
2. **43 rows (1.9%) label the user message** (`Unknown`): rewritten task text or lost rewrite record.
3. **8.4% agent/step mismatch**, concentrated in math500 (31%); free-text agent names.
4. **The rewrite leaves a seam**: evidence recap + contradicting conclusion inside one step, or contradiction with the agent's own previous turn; the generator does not rewrite the recap. Prevalence to be estimated by the LLM `contradicts_prefix` (pending); 11 of 15 non-trivial read rows.
5. **Round-cap loops as the only continuation**: 37.6% of rows have ≥6 steps after the label, all of them repetition to the cap; the symptom is framework behaviour, not error-specific.
6. No GT and no reason: a "false failure" check is impossible; the paper's 47% "taken for human-labelled" is about realism, not label correctness.
7. **Absorbed rewrites in the loop regime** (§3b): in 17 audited long rows the rewritten step is corrected by a later Planner turn in 53% and judged decisive in 12%; the run fails by looping to the cap. Prevalence estimate: ≈40–50% of the 809 long rows (≈15–20% of the dataset) carry a label that no content-based reader would pick.

## 6. Candidate hypotheses

**H1 — Prefix-seam detection beats everything on CORRECT-Error (and generalises to no natural data).** The rewritten step contradicts its own recap or the agent's previous turn. Test: an NLI/LLM "does step k contradict steps <k (esp. the same agent's last turn)?" scorer, prefix-only, vs the all-at-once judge; expect ≥70% top-1 on rows with label < last step; expect the same scorer to be at chance on Who&When (natural causes rarely contradict the prefix, they *extend* it wrongly). Shared with WWP (H1), tracertraj injected shell rows.

**H2 — Suffix consistency is anti-informative.** After the rewrite the Planner restates the wrong understanding each round; a scorer that rewards "steps consistent with the final answer" would score the injected content *highest* (it is the most repeated). Test: measure the embedding similarity of each step to the final output; expect the labelled step to be the argmax more often than the chance rate in the long rows. This is the inverse of P1 (downstream contamination): here contamination is total and uniform, so there is no gradient to back-propagate — consistent with SOAP's +0.4 pp on CE.

**H3 — Length regime predicts the method that works, and the long regime is solved by a scheduling seam.** Short rows (≤4 steps): last-step rule (90%); long rows: the first Planner→Planner adjacency (95% exact where present, 56% of long rows). Tested (§3c): combined text-free rule 74.0% exact. Remaining ~26%: long rows without a seam (the rewrite replaced a turn in place) — those are the only rows on which CORRECT-Error measures attribution rather than artefact detection; evaluation should be restricted to them (≈350 rows) or the seam must be removed by merging adjacent Planner turns. A content change-point on the Planner's "Updated Understanding" is weak (13%).

**H4 — Agent label noise is an off-by-one, not random.** Tested (stats.md §c): of the 144 mismatches with a named agent, the *previous* turn is by the labelled agent in 64% (next turn 43%, labelled agent named inside the indexed turn only 21%). So the index mostly points one step *after* the rewritten turn (the WebSurfer turn that follows the rewritten Planner instruction). Implication: for mismatched rows the step label should be shifted to k−1 when `steps[k-1].agent == mistake_agent`; a scorer that trusts the index learns to blame the observation that follows the error — a mild built-in "late" bias of ≈6% of rows.

## 7. Open questions

- Which Who&When hand-crafted failure served as template for each row (not released) — would allow a direct injected-vs-natural pairing on the same error type.
- Are the 809 cap-length rows failures *because of* the rewrite or would the base system have looped anyway (parent successes are not released)?
- Why do gpt-4o-mini rows (318) behave differently (arc 8-step runs with WebSurfer searches)?
