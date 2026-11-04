# MP-Bench — inspection notes (G1, 2026-11-01)

Scripts: `inspect/mp_bench_stats.py` (-> `results/mp_bench/stats.{txt,json}`), `inspect/who_and_when_overlap.py` (WW↔MP-Bench, `results/who_and_when/overlap.txt`), `inspect/g1_gt_visibility.py`, `inspect/g1_condensed.py mp_bench --ids ...`. Baseline: `results/mp_bench/all_at_once_std.jsonl`, `all_at_once_inventory.jsonl` (+ `_analysis.md`).

## 1. Data as loaded

- 289 logs (169 manual = 57 Who&When Hand-Crafted + 112 MAST Magentic-One GAIA console logs; 120 automatic = Who&When Algorithm-Generated), 6,901 steps, three annotators per log. 277 logs have ≥1 flag, 12 manual logs have none.
- `labels.error_steps` = union of flags; `votes` = per-step count; `extra.per_annotator` = per-annotator (step, category, reason, ideal_action); the loader's primary step (`extra.earliest_majority_step`, used by `error_step()`) = earliest step with ≥2 votes, else earliest flag.
- **Loader caveat (not a bug, a consequence of the data):** the ≥2-vote primary is corrupted by annotator duplication (§3.1): in 7 manual logs the primary is a content-free `Next speaker X` line (manual/114, 116, 117, 118, 119, 168, 169), and after de-duplication 26 manual logs have no majority step at all. For my own analyses I use the de-duplicated votes (`results/mp_bench/stats.json: prim_dedup`). Do not fix in the shared loader; note it.
- 177 of the 289 logs are Who&When logs: the step lists are identical (0 count mismatches), so labels can be compared step-for-step (`results/who_and_when/overlap_map.json`).

## 2. Close-reading notes

| id (source) | n | votes | what happened / where the labels sit | my reading |
|---|---|---|---|---|
| manual/18 (MAST L2, "beta geometric") | 9 | 3:1, 5:3, 6:1, 7:3, 8:3 | step 3's Bing snippet already shows "beta-geometric (BG) distribution"; step 5 the click silently fails (page unchanged); step 7 WebSurfer summarises "Markov models"; step 8 FINAL ANSWER Markov Model. | The decisive miss is step 3→5 (evidence visible, not extracted; click failed); unanimity sits on 5, 7, 8 = the failed click and the two downstream symptoms. The only flag on the step where the answer was visible (3) is 1 vote. |
| manual/116 (= WW HC/12, Box Office Mojo) | 20 | 7:2, 11:2, 15:2, 16:3, 19:2, 12:1, 13:1, 17:1 | WebSurfer at 12 clicks the "Domestic" *sort* on the worldwide chart (never loads the domestic chart); the Assistant at 16 then recites a (wrong) domestic top-10 from memory; final 5 vs GT 6. | The cause (12) has **one** vote (annotator 2); the 2-vote steps 7/11/15 are `Next speaker` lines flagged as "procedural bloat" by annotators 1 and 3, whose annotations are verbatim identical. Loader primary = step 7, a non-decision. |
| manual/124 (= WW HC/2, Ted Danson) | 86 | 21 flagged steps, 7 with 3 votes (19, 23, 24, 27, 37, 82, 85) | 86-step scrolling loop; the run ends with **FINAL ANSWER: CSI Cyber = ground truth** (`is_correct=False` in the file). Annotators 1 and 3 identical again; annotator 2 flags different steps (8, 15, 35, 78, 85). WW's step 4 (first search) gets 0 votes from all three. | A success-by-answer labelled as failure; annotators then flag *process inefficiency* steps. Illustrates that MP-Bench flags are "steps that look bad", not steps that changed the outcome. |
| manual/166 (= WW HC/6, Mission Bay) | 8 | 4:2, 5:3, 6:2, 7:2 | search snippet names "$1.08 billion for 1800 Owens Street" (an office building); orchestrator accepts it (5) and the run ends. | Clean case; all annotators agree with WW (5). Annotator reasons cite the ground truth ("ground truth is $3,080,000") — outcome-informed annotation. |
| manual/123 (= WW HC/19, Fubo) | 69 | 21:2, 37:2, 45:2, 49:2 + seven 1-vote | three `I clicked 'Select Year:'` steps (40, 44, 48) never choose 2020; max-time → "Unable to determine". Annotators 1/3 flag only the four `is_in_loop=true` ledgers ("Planning Error"); annotator 2 flags the WebSurfer non-selections (36, 44, 48). | The majority set is the *orchestrator's own loop detector* (symptom); the actual non-actions have one vote. WW labels the Stalled/Replanning step (50), which nobody in MP-Bench flags. |
| automatic/3 (= WW AG/3) | 8 | 0:1, 1:1, 2:2, 4:3, 6:3, 7:1 | after a timeout the Verification_Expert fabricates the red/green numbers (4); 6 "verifies" the maths on fabricated data. | All agree with WW on 4; the earlier 2-vote step 2 (did not use tools) is an omission-type alternative cause. |
| automatic/10 (= WW AG/10) | 10 | 2:3, 5:3, 9:3, 3:2, 4:2, 0:1, 1:1, 7:1 | Validation_Expert asks for manual census lookup (2–4), then fabricates population numbers (5), final 732,050 vs 736,455. | Majority starts at 2 (omission: no tool use); WW picks the fabrication (5). Both defensible — the omission/commission split recurs in 28/120 automatic logs. |
| automatic/82 (= WW AG/82) | 7 | 4:1 only | 17,000 hours = "17 thousand hours" = GT 17; the run is right up to output format. | Two of three annotators flag nothing; the one flag is a format note. Confirms WW's label/reason are wrong (who_and_when.md §5). |
| manual/18-like MAST L3 logs (manual/60, /75 skimmed) | 40–60 | 10–20 flags | long scroll loops; unanimity on FINAL ANSWER step and on `is_in_loop` ledgers. | same pattern as the WW HC long logs. |

## 3. Targeted statistics

**3.1 Annotator duplication.** Over 289 logs, annotator 1 and annotator 3 submitted *verbatim identical* annotation lists (same steps, same category, same reason text) in **19 manual logs** (11% of manual; 0 automatic), and identical step sets with different text in 17 more; annotators 1 and 2 are verbatim identical in 8 logs. In 28/223 logs ann1 and ann3 share at least one verbatim reason. Consequence: a "3-vote" step on those logs is really a 2-vote step, and a "2-vote" step can be one annotator counted twice. De-duplicating (counting ann3 only where its (step, reason) differs from ann1) leaves **26 manual logs with no majority step** and changes the primary in 14 more (manual: 129 unchanged / 14 changed / 26 none; automatic: 119 / 0 / 1).

**3.2 What gets 1, 2, 3 votes (manual logs).**

| votes | n | WebSurfer | Orch ledger | Orch final-answer step | `Next speaker` | Orch other (MAST) | median rel. position | error-string rate |
|---|---|---|---|---|---|---|---|---|
| 0 (never flagged agent steps) | 3,565 | 23% | 13% | — | 15% | 24% | — | 0.05 |
| 1 | 1,239 | 31% | 10% | — | 0% | 41% | 0.54 | 0.09 |
| 2 | 579 | 28% | 18% | 3% | 11% | 27% | 0.60 | 0.11 |
| 3 | 305 | 39% | 18% | **24%** | 0% | 8% | **0.82** | **0.27** |

Unanimous flags are late (median 82% of the log), 24% of them are the FINAL ANSWER step itself, and they carry error strings 5× more often than unflagged steps. 129/305 unanimous flags sit in the last three steps; in 127 of 157 flagged manual logs the maximum-vote step set includes one of the last three steps. Automatic logs: the 3-vote steps are 100% Expert messages, median position 0.44 — the short CaptainAgent logs do not show the late-consensus effect.

**3.3 1-vote flags are mostly downstream.** Of 1-vote flags, 948/1,239 manual (77%) and 219/308 automatic (71%) lie *after* the earliest majority step. Reading them (manual/124, /123) they are mainly repeated scroll/click steps and ledgers — continuation symptoms, not alternative causes. The 291 manual 1-vote flags *before* the majority step are the interesting minority: in the cases read, they are the actual cause (manual/116 step 12; manual/18 step 3; manual/123 steps 36/44).

**3.4 Category agreement on the same step:** manual 329 same / 555 different, automatic 119 / 209 — annotators who agree on the step disagree on the category two times out of three. The 9-class taxonomy is not reproducible at the step level.

**3.5 Label reliability vs Who&When (177 shared logs).** Hand-Crafted (57): the WW step receives 0 votes in **26**, 1 vote in 12, 2 in 6, 3 in 13; it is the loader primary in 9 and the earliest flag in 8; in 11 logs no annotator flags anything within ±3 steps of the WW step (HC/2, 17, 20, 21, 22, 27, 35, 38, 41, 47, 50). WW "Orchestrator (-> X)" instruction labels get 0 votes in 6/6 — MP-Bench annotators flag the ledger thought that contains the same text, one step earlier (a step-identity convention gap worth ±1). Agent agreement 23/57. Algorithm-Generated (120): WW step has ≥2 votes in 116, 3 votes in 74, equals the primary in 91; a *majority step strictly earlier* than WW exists in 28 (omission-type steps, §2).

**3.6 Ground-truth visibility.** The GT string appears in an agent step *before* the primary step in 19 manual logs (82 never, 10 after) — "answer seen, not extracted" is a ~15% phenomenon on the manual logs (e.g. manual/18, /124), rare in automatic (3).

Prefix probe: not run on MP-Bench (the WW HC probe covers the same logs; see who_and_when.md §3).

## 4. Baseline error analysis

(filled in from `results/mp_bench/all_at_once_std.jsonl` and `all_at_once_inventory.jsonl` — see §4 addendum)

## 5. Annotation issues (prevalence)

1. **Duplicate annotators** (19 verbatim-identical manual logs, 8 more for the 1/2 pair, ~9% of all logs): consensus rates and the paper's 16.2% unanimity are inflated on those logs; "majority" primaries on 7 logs are `Next speaker` lines.
2. **Outcome-informed flags**: reasons quote the ground truth ("wrong by factor of 350x"); FINAL ANSWER steps are flagged unanimously in 10 manual primaries and 73 unanimous flags overall — the step that *reveals* the error is treated as an error.
3. **Procedural flags**: `Next speaker` / redundant ledger steps flagged as "Reasoning-Action Mismatch" (manual/116 and the other 6 Next-speaker primaries).
4. **Failure set contains a success**: manual/124 (HC/2) ends with the ground-truth answer.
5. **Category labels are per-annotator and inconsistent** (§3.4).
6. 12 manual logs with zero flags from all three annotators (annotators found no mistake in a failed log).

## 6. Candidate hypotheses

**H-M1 "Consensus is a symptom detector": annotator agreement grows with distance from the cause; unanimous steps are the final answer and the loud late steps, while the causal step is a 1-vote step in the first half.** Evidence: §3.2 (median position 0.82 for 3 votes, 24% FINAL ANSWER, error-string rate 0.27 vs 0.09), §2 manual/18, /116, /123. Test: score a model's ranking with nDCG against (a) the consensus ranking and (b) the de-duplicated earliest-flag ranking; a model that ranks the final answer first will look good on (a) and bad on (b). Shared with WW-HC (same logs), AgentRx (post-root failure density 3.5× pre-root), TRAIL/MAST style multi-flag sets. A targeted method should *down-weight* steps whose "wrongness" is explained by an earlier flagged step (the SOAP back-propagation idea, but applied to annotator votes as well as to model scores).

**H-M2 "Omission vs commission": when the cause is an omission (not using a tool, not extracting visible evidence), annotators split between the omission step and the later commission step (fabrication) that it enabled.** Evidence: 28/120 automatic logs with an earlier majority step than WW (all read ones are "asked for manual lookup / did not run code"); manual/18 step 3 vs 5. Test: classify flagged steps as omission/commission with an LLM and measure vote split. A method should output *pairs* (omission → commission) rather than one step; evaluation with ±k tolerance hides this.

**H-M3 "Ledger self-diagnosis is annotated as the error"**: Magentic-One's own `is_in_loop=true / is_progress_being_made=false` ledgers are flagged by the majority (manual/123: all four majority steps are such ledgers), i.e. the system's loop detector becomes the human label. Shared with WW-HC (Stalled/Replanning labels) and AgentRx (orchestrator misinterpretation roots). Test: regress vote count on the ledger flags; if R² is high the label is reproducible from the orchestrator's own text, and a method can read the ledger instead of reasoning.

**H-M4 "Short logs are not easier, they are over-determined"**: automatic logs have 5–10 steps and 1–4 Expert speakers; the 3-vote step is an Expert step in 100% of cases and nDCG ≈ 0.7–0.8 is reachable by flagging every Expert message after the first tool error. Test: a no-LLM rule (flag all Expert steps after the first `exitcode: 1`/timeout) vs the leaderboard numbers.

## 7. Open questions

- Which annotator is the duplicate — was one set pasted, or was the GPT-5.1 consolidation accidentally written back into an annotator folder? The release does not say; the 19 logs should be excluded from reliability claims either way.
- The `ideal_action` field (unique to MP-Bench) is unused here; it could give a counterfactual target for omission steps (H-M2).
- Does MP-Bench's judge-scored reasoning metric reward late-symptom explanations (it consolidates annotator rationales that are themselves symptom-heavy)?


## 4b. Baseline results (filled from results/mp_bench/ after the runner finished, 2026-11-01)

Qwen3.8-27B all-at-once, gold = earliest majority-vote step; `step_in_set` counts a prediction inside the full labelled set.
Signed categories: `later` = predicted after the gold (symptom side), `earlier` = before it. Reasoning excerpts for
failures and successes are in `results/mp_bench/all_at_once_std_analysis.md`.

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| automatic | 43 | 74.4 | 58.1 | 69.8 | 90.7 |
| manual | 37 | 64.9 | 29.7 | 48.6 | 54.1 |
| ALL | 80 | 70.0 | 45.0 | 60.0 | 73.8 |

categories: {'exact': 36, 'earlier(<-3)': 11, 'in_label_set': 23, 'earlier(-1..3)': 3, 'later(>3)': 5, 'later(+1..3)': 1, 'truncated': 1}
agent right but step wrong: 21; step right but agent wrong: 1
| n_steps | n | step_exact% | within3% | agent% |
|---|---|---|---|---|
| 0-10 | 48 | 58.3 | 72.9 | 75.0 |
| 11-30 | 11 | 36.4 | 54.5 | 54.5 |
| 31-1000 | 21 | 19.0 | 33.3 | 66.7 |
wrote results/mp_bench/all_at_once_std_analysis.md

Inventory variant (same ids):

| subset | n | agent_ok | step_exact | step_within_3 | step_in_set |
|---|---|---|---|---|---|
| automatic | 43 | 72.1 | 60.5 | 79.1 | 93.0 |
| manual | 37 | 56.8 | 29.7 | 54.1 | 59.5 |
| ALL | 80 | 65.0 | 46.2 | 67.5 | 77.5 |

categories: {'exact': 37, 'earlier(<-3)': 9, 'in_label_set': 25, 'earlier(-1..3)': 6, 'later(>3)': 3}
agent right but step wrong: 16; step right but agent wrong: 1

