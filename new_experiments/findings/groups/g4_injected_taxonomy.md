# G4 — injected-fault and taxonomy datasets: cross-dataset synthesis

Datasets: Who&When Pro (text), TracerTraj, CORRECT-Error, AEGIS, MAST-Data (spot check). Per-dataset notes in
`findings/datasets/{who_and_when_pro,tracertraj,correct_error,aegis,mast_data}.md`; scripts `inspect/g4_*.py`,
`inspect/<slug>_stats.py`; outputs `results/<slug>/`. Natural-failure comparison numbers come from Who&When (loader `who_and_when`).

Sections marked PENDING depend on LLM runs that were still queued on the shared servers when this report was handed back
(status at hand-back: no LLM output had returned after ~2 h because the 8210 queue held 80+ requests from all agents; 8211 came up late).
In flight, relaunched on the load-balanced client, outputs will appear under `results/<slug>/`:
`inspect/prefix_probe.py who_and_when_pro --n 20 --max-steps 30` (→ prefix_probe.jsonl), `inspect/g4_label_check.py` for
who_and_when_pro (--per-subset 8, 64 rows), correct_error (--n 40), tracertraj (--per-subset 10, 60 rows) (→ label_check.jsonl),
`inspect/mast_data_probe.py` (35 traces → mode_probe.jsonl), and the baselines `all_at_once.py who_and_when_pro --n 100 --mask-last 1
--tag masklast`, `correct_error --n 80 --no-gt`, `tracertraj --n 60`, `aegis --n 60` (the runner's chain C also produces
who_and_when_pro std). To finish: run `python3 -I inspect/analyze_baseline.py <slug> [name]` and re-run the four probe scripts
(cached calls are instant) to print the summary tables, then replace the PENDING blocks in the dataset files and §2/§7 here.
All text-free statistics, close readings and hypotheses below are complete.

## 1. What the group looks like once the labels are decoded

| dataset | how the label was made | label = last agent step | continuation after label | label-vs-text noise found | text-free predictor |
|---|---|---|---|---|---|
| Who&When Pro text (6,257) | base agent re-prompted to deviate at step t of a replayed success; continuation on-policy | **48.4%** (mathchat 79%, M1 56%, smol 52%) | mean 2.35 agent steps; 0 in 48% | mode = injector instruction, not text (3/13 read); recovered injections kept (2/13); ~1% false failures | last agent step: 48.4% |
| CORRECT-Error (2,226) | one Planner/WebSurfer step rewritten by an LLM inside a successful run | **50.0%** | 0 (50%) or ≥6 (38%, loop to the 22-step cap) | 43 labels on the user message; 8.4% agent/index mismatch; Planner→Planner **seam** at the label in 24% of rows | last step ∪ first Planner→Planner adjacency: **74.0%** |
| TracerTraj (3,998) | agentic: 1,822 injected + 278 DeepSeek-R1 counterfactual; coding: 679 injected (leaks `_attacked_solution.py`) + 589 diagnosed; math: 630 injected (reason = injector's plan) | injected 12.8% / diagnosed **47.8%** (agentic) | injected 4.0 / diagnosed 3.4 steps | diagnosed labels on final answer 42% and on a broken tool (`crawl4ai not installed`) ≈29%; 12% of math labels are refusals; 18% of shell injections carry `| sed` | diagnosed agentic: final-answer step ≈42% |
| AEGIS (9,533) | (agent, mode) pairs from an injection plan; MacNet `is_injected` flags contaminated turns | no step label (MacNet flag ⊃ clean sink node in 51%) | — | mode ≠ text (8/10 pairs read); corrupted turns self-announce ("calculated incorrectly", "again for emphasis") in 27–48% | constant agent per framework: 72% (agentverse 93%) |
| MAST-Data (1,642) | o1 trace-level modes | no step | — | modes on correct-answer traces (3/9 read); mode count ∝ length | — |

Reading: every injected set in this group ships a **positional or structural prior that an attributor can exploit without reading
the error**, and the prior explains a large share of published accuracies (WWP SOTA 72% vs 48% last-step; CE LLM judges 6–63% vs 74% seam rule).

## 2. How injected errors differ from natural ones (the group's central question)

### (a) Local detectability
- **Injected steps contradict their prefix; natural causes extend it.** The WWP injector tells the base agent to deviate at a step where the correct continuation was already implied, so the injected text contradicts its own plan / the previous observation / the task (7 of 13 read; dylan: three identical correct solutions then "the gas expands"). CE rewrites keep the evidence recap and change the conclusion (seam inside the step). TracerTraj shell injections rewrite the observation in the command itself. AEGIS corruptions change the problem's numbers.
- Natural labelled steps (Who&When hand-crafted) are instead *loud at the step*: 12% contain a tool error and 22% a self-correction phrase, i.e. the human label often sits on the first visible symptom (P2/P3), whereas WWP labelled steps carry such markers in 2.8% / 3.5% — no more than their clean prefix.
- **Prefix probe, WWP (done, 20 records / 105 probes, no GT, no outcome)**: injected step flagged as a mistake in **100%**, earliest flagged step = injected step **85%**, argmax-confidence 75%; flag rate on the replayed prefix 7.1%, on the live continuation 58%. Reasons are prefix contradictions. The matching natural-data probe (`results/who_and_when/prefix_probe.jsonl`, G1) had one finished record at hand-back, so the natural side of the contrast is the literature's 3.5–25% WW step accuracy, not our own number.
- **Label check, CE (done, 40 rows)**: `local_wrong` 77.5%, `contradicts_prefix` 57.5% overall; on rows whose label is the last step 100% / 63% and `decisive=yes` 95%; on loop rows (label followed by ≥6 steps) 65% / 59% but `corrected_later` 53% and `decisive=yes` only 12% (no_later 41%, no_other 41%).
- Label checks for WWP (64 rows) and TT (60 rows): **still running at hand-back** (outputs will be `results/{who_and_when_pro,tracertraj}/label_check.jsonl`; rerunning the script prints the table from cache).

### (b) Style
- WWP: the injected turn is the **length outlier** of its agent (shortest for mathchat/smolagents/dylan, z ≈ −1 … −2.2; longest for the Magentic-One orchestrator, z = +1.8), a 3-feature argmax finds it in 50–92% vs 23–33% chance, with no outcome. Hedging/certainty/self-reference carry no signal (|z| < 0.25): the WWP injector preserves the agent's voice.
- AEGIS: the opposite — corrupted turns announce the mode ("we will repeat this again for emphasis", "Incorrect Answer: (B)", "ignore the provided options and fabricate"); a regex attributes the agent in debate at 91% (prior 70%). Prompt-injected agents (smolagents, magentic) look clean.
- CE: the rewritten Planner turn is over-long and ends in a justification paragraph; the structural seam (Planner→Planner) is stronger than any style feature.
- TracerTraj: `| sed` (18% of shell injections), refusals (12% of math), the `attacked` filename (54% of coding).
- PENDING: label_check `style_odd` rates; AEGIS cue classifier with content masked (future).

### (c) Continuation
- The continuation is generated **after** the injection and is loyal to it: it stops (WWP 48% no continuation; CE 50%), rationalises (mathchat 0055 re-derives 147.57 with the valence included — impossible arithmetic written to agree), or restates the wrong understanding every round (CE long rows). Post-label symptom-marker rates in WWP (tool errors 4.7%, self-corrections 7.4%, repeats 13%) stay **below Who&When's pre-label baseline** (10% / 16% / 13.5%): injected trajectories never reach natural levels of visible trouble.
- Where symptoms do occur they are framework artefacts, not consequences of the injection: smolagents `<code>` parsing loops, alfagent's 30-step budget repeats (26% repeats), CE loops to the 22-step cap, TracerTraj coding edit–test loops (34% repeats before *and* after the label). They are loud and misleading (dabench_0298: loud loop at 4–8, silent cause at 2; coding/642: label at 4, 294 loop steps).
- Two sub-populations break the "cause at label" assumption: recovered injections (WWP 0190, 0121: the live steps fix the error and the run fails for a natural reason or a grading format) and environment outages (TracerTraj diagnosed: `crawl4ai not installed`).
- CE label check (done): in the loop regime the rewritten step is *corrected later* in 53% and judged decisive in 12% — the injected error is absorbed and the run fails by looping to the 22-step cap; prevalence estimate ≈15–20% of CORRECT-Error rows with a label no content reader would pick. On WWP the prefix probe flags 58% of live continuation steps (loyal continuation = every later step looks wrong) but the earliest flag is still the injected step (85%): no late bias for a prefix-only judge. WWP/TT label checks still running at hand-back.

## 3. Phenomena that recur across the group

1. **Terminal-step collapse**: label = last agent step in 48% (WWP), 50% (CE), 48% (TT diagnosed); injected steps that *are* the final answer (M1 44.6%, CE 56% contain FINAL ANSWER). Any method's accuracy must be reported conditional on label ≠ last step.
2. **Prefix contradiction as the injected-error signature** (WWP, CE, TT-shell, AEGIS number changes) vs symptom-at-label for natural data (WW). → a two-channel attributor (prefix-consistency channel + downstream-symptom channel) with a gate on "does this trajectory have loud symptoms at all".
3. **Loyal continuation / no gradient to back-propagate**: consistent with SOAP's +8.5 pp on WW-AG vs +0.4 on CE (literature) — on injected data there is no downstream score peak to move back from, the contamination is uniform.
4. **Construction seams and leaks** (CE Planner→Planner, TT `attacked`/`sed`/refusal, AEGIS self-announcement, WWP length outlier, raw WWP flags): each dataset has at least one text-free or style-only shortcut; fine-tuned models (AgenTracer-8B, Aegis-SFT) plausibly learn them, which fits their reported drop on Who&When.
5. **Mode labels are instructions, not descriptions** (WWP 3/13, AEGIS 8/10, MAST 1.3/2.5/3.x relations): the "what" axis is largely unlearnable from the step text; MAST's relational modes (1.3, 1.4, 1.5, 2.5, 3.2, 3.3 ≈ 55% of corpus flags) have no single step.
6. **Counterfactual-with-GT diagnosis converges on the final answer or the outage** (TT diagnosed 42% final answer, 29% crawl_page): "earliest fix that yields success" is not what the procedure finds when the final-answer rewrite always succeeds.
7. **Successful-prefix assumption fails** (debate 0036: a real over-reliance step inside the replayed "correct" prefix; MAST modes on correct traces; AG2/184 correct answer with 1.3+3.3): errors inside successes (P6) appear in the seeds of injected data too.

## 4. What injected data can and cannot teach an attributor

Can:
- Local, prefix-relative error detection (contradiction with own plan / previous observation / task) — the one skill injected data trains cleanly, and the one natural data lacks labels for.
- Mode-conditioned stylistic signatures of *LLM-written* errors (useful as a negative: a detector that keys on them will not transfer).
- With AEGIS MacNet flags: a propagation label (turns downstream of a corruption are flagged) — the only "inherited error" annotation in the group, usable to study P1 if `is_injected` is reinterpreted as contamination.

Cannot:
- Symptom-to-cause back-tracing (no symptom gradient, loyal continuation).
- Agent attribution in multi-agent settings (WWP culprit nearly constant per framework; AEGIS 54% of agents faulty, constant-agent prior 72%).
- "What" classification (modes ≠ text).
- Calibration of *where* natural errors sit (injected rel. pos 0.34–0.53 vs diagnosed/natural 0.59–0.83): a judge tuned on one skews on the other.

## 5. Ranked hypotheses (group)

1. **G4-H1 Prefix-contradiction channel.** Injected steps are detectable by inconsistency with the prefix alone; natural causes are not. **Supported**: WWP prefix probe flags the injected step in 100% and as the earliest flag in 85% with only the prefix; CE auditor `local_wrong` 77.5%, `contradicts_prefix` 57.5% (100%/63% on terminal rows). Still to do: the same probe on Who&When (G1 run unfinished) to close the contrast. Method: two-channel attributor with a symptom-presence gate.
2. **G4-H2 Positional/structural priors account for most reported accuracy.** 48–50% last step; CE seam 74%. Test: `--mask-last 1` baseline on WWP ids (pending); seam-stripped CE evaluation.
3. **G4-H3 Loyal continuation kills the symptom channel; residual symptoms are framework loops that mislead.** Test: label_check `symptoms_later` vs dependency on injected content (pending); SOAP/EMFA-style rescoring gain on WWP vs WW.
4. **G4-H4 Counterfactual-with-GT labels are final-answer/outage labels** (TT diagnosed). Test: rules "final-answer step" / "first crawl_page" on the 278 rows; re-diagnose 30 rows earliest-first.
5. **G4-H5 Mode is unrecoverable from step text; it is recoverable from framework × position.** Test: mode classifier from (fw, rel. pos, agent) vs from text on WWP/AEGIS; MAST probe "step vs pattern" split (pending).
6. **G4-H6 LLM-authored corruptions have an authorial voice** (AEGIS announcements, CE justification paragraphs, WWP length outliers). Test: style classifier with content masked, transfer to WW (expect chance).
7. **G4-H7 Unattributable floor from recovered/absorbed injections and environment outages.** **Supported and larger than expected on CE**: auditor `decisive ≠ yes` in 47.5% of 40 rows, concentrated in the loop regime (88% of 17 long rows; `corrected_later` 53%); TT diagnosed outage labels ≈29%; WWP 2/13 read. Remaining test: WWP/TT label checks (running).
8. **G4-H8 Errors inside successful seed prefixes.** **Weakened**: the prefix probe flags only 7.1% of replayed WWP steps (3/42), so seed prefixes are mostly clean for a monitor; debate-0036-type cases are rare. Keep as a minor caveat, drop from the ranked list.

## 6. Literature phenomena P1–P8 on this group's data

| P | verdict here | numbers |
|---|---|---|
| P1 downstream contamination | **present for a prefix-only judge but without late bias**: WWP continuation steps are flagged 58% of the time (they inherit the error) yet the earliest flag is the injected step in 85%; surface symptom markers after the label stay below WW's pre-label rates; framework loops (TT coding 34% repeats, CE cap loops) are not caused by the labelled step and on CE the auditor blames a later step in 41% of loop rows | WWP probe before/after 7.1% / 58.1%; WWP after-label tool_error 4.7% / self_correct 7.4% vs WW before-label 3.6% / 8.9%; CE loop rows decisive=yes 12%, no_later 41% |
| P2 label is a convention | confirmed in a new form: injected label = injector's choice (rel 0.34–0.53), counterfactual label = last successful fix (rel 0.69, 48% last step), on the same agent (TT agentic) | TT injected vs diagnosed |
| P3 anchoring on LLM drafts / outcome | TT diagnosed labels are DeepSeek-R1 with GT → final answer 42%; CE/WWP labels are by construction (immune) but their *modes* are the injector's instruction (a different anchoring) | — |
| P4 outcome-only judges fooled by assertive closings | supported by construction: 44.6% of M1 injections are the final answer; CE 56% of labelled steps contain FINAL ANSWER; the injected final answers read confidently | — |
| P5 long-trajectory degradation | group is short (median 4–14 steps) except TT coding (≤304) and alfagent (30); TT coding ≥100 steps: label at 1–4% rel. pos followed by hundreds of loops — a length stress test with a known planted cause | 13 coding rows ≥100 steps |
| P6 normal flow / successes contain errors | confirmed: replayed WWP prefix contains a real error (debate 0036); MAST modes on correct traces (3/9); TT math injected refusal rows | — |
| P7 absorption vs cascade | **confirmed with numbers on CE**: in the loop regime the rewritten step is corrected later in 53% of audited rows and judged decisive in 12% — the injection is absorbed, the run still fails (loop to cap), the label stays; WWP 2/13 read; AEGIS debate_21 A1 (prompt injection with no visible effect) | CE 17 loop rows: corrected_later 53%, decisive yes 12%; WWP/TT checks running |
| P8 verification theatre / false success | WWP metagpt reviewer "No issues found" on injected code; CE Planner "TASK_COMPLETE" after rewrite; MAST 3.x modes at the tail; AEGIS evaluator "Correctness: 1 … the solution is incorrect" | — |

## 7. Baseline results — MISSING at hand-back

None of the group's all-at-once baselines had returned when this report was handed back (runner chain C `who_and_when_pro --n 100` plus my own `who_and_when_pro --n 100 --mask-last 1 --tag masklast`, `correct_error --n 80 --no-gt`, `tracertraj --n 60`, `aegis --n 60` were all still queued; the 8210 server held 50–80 waiting requests throughout). The processes are running in the background and write `results/<slug>/all_at_once_std*.jsonl`; to finish: `python3 -I inspect/analyze_baseline.py who_and_when_pro`, `... who_and_when_pro all_at_once_std_masklast`, `... correct_error all_at_once_std_nogt`, `... tracertraj`, `... aegis`, then compare WWP std vs mask-last on the shared ids (the text-free priors in §1 predict a drop of roughly the 48-pp last-step share), split TT by error_source, and rescore AEGIS agent accuracy against the full faulty set. Predictions to check against: CE near-perfect on last-step rows and "later" misses inside the loops; TT diagnosed rows easy for a last-step-biased judge, injected rows hard; WWP misses mostly *later* (the live continuation) by analogy with the 58% continuation flag rate of the prefix probe.

Also missing: WWP and TT label checks (`results/{who_and_when_pro,tracertraj}/label_check.jsonl`) and the MAST mode probe (`results/mast_data/mode_probe.jsonl`); their scripts print summary tables from cache when rerun.
