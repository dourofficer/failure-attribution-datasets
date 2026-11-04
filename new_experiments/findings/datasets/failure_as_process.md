# failure_as_process — inspection notes (G3, Nov 2026)

Scripts: `inspect/failure_as_process_stats.py` → `results/failure_as_process/g3_stats.md`. Annotation-only release: no step
text, so no close reading of trajectories, no prefix probe, no baseline. Everything below is about the *labels* and what
they imply for a monitor / attributor on CLI coding agents. Step numbers are the release's 1-based `t_err / t_commit(=t_lock)
/ t_surface(=t_obs)`.

## 1. Data as loaded

- 1,794 runs (1,184 FAIL / 610 PASS), 89 Terminal-Bench tasks × 21 systems (3 scaffolds × 7 models), 63,276 annotated
  steps; `steps=[]` except 433 PASS runs with a ~3-step `pass_obs_input` excerpt around the first error event (role `env`).
- Per FAIL run: `t_err`, `t_lock`, `t_obs` (null for 332 = 28.0 % silent), `trigger_mechanism` (9), `awareness` (4),
  `tail_dominant_behavior` (6), fabrication fields, forewarning fields, `action_segments` (E/P/W/X/V/C/R/O runs),
  `uncertain_fields`, `timepoint_confidence` (high 1,051 / medium 133). Per PASS run: `num_error_events`, `num_recoveries`,
  `max_detour_length`, `suspicious_pass`, `solution_directness`, `verification_before_claim`, `near_miss`.
- Loader is fine. One caveat for users of `labels.extra`: the released numeric fields are strings; the loader converts them.

## 2. Close-reading notes (annotation records and PASS excerpts; ids)

No trajectories exist, so "close reading" = the evidence quotes and the 433 PASS excerpts.

- `acl-permissions-inheritance__miniswe__gemini` (m 13, t_err 2, t_lock 3, t_obs 11): `sudo: not found` after a `mkdir &&
  sudo` chain is *misread* as a permission failure; the pivot to `~/srv/shared` is the lock-in one step later; the first
  external signal (`getfacl` showing owner root) is 8 steps after lock-in. The forewarning (`empty_or_unexpected_output`) is
  at t_err itself. The same `sudo: not found` message is the first error event in the PASS run of the same task
  (`acl-permissions-inheritance__miniswe__claude`, excerpt: step 2 `sudo mkdir` → `sudo: not found`, step 3 retries without
  sudo and succeeds). **Identical observation, opposite fate** — the error signal is not what separates PASS from FAIL, the
  next action is.
- PASS excerpts sampled (seed 1): `cpp-compatibility__terminus2__devstral` (silent: a flawed template later rewritten),
  `multi-source-data-merger__terminus2__kimi` (silent: `(command not found in terminal output)` — the agent proceeded on an
  assumed schema and still passed), `triton-interpret__openhands__gpt5` (8 error events / 8 recoveries, detour 10, exit
  code −1 on pip), `stable-parallel-kmeans__openhands__devstral` (ModuleNotFoundError, wrong interpreter, 5 events),
  `build-pov-ray__miniswe__devstral` (m 289, detour 166 steps, gcc conflicting-types errors), `fix-git__openhands__claude`
  (merge conflict, recovered), `constraints-scheduling__openhands__qwen` (`Cannot execute multiple commands at once`),
  `mlflow-register__terminus2__claude` (agent misreads a successful import as hanging — a *misread_output* event inside a
  PASS run), `intrusion-detection__miniswe__gpt5` (11 error events, 1 recovery, detour 13, still PASS). Every forewarning
  type the FAIL codebook lists (command_error, empty_or_unexpected_output, repeated_command, contradictory_evidence) occurs
  verbatim in PASS excerpts.
- The 7 runs where "annotator B" places t_err ≥ 46 steps before A (`add-benchmark-lm-eval-harness__terminus2__claude` A 85
  / B 2, `build-cython-ext__openhands__deepseek-v3.2` A 105 / B 31, `parallelize-graph__terminus2__deepseek-v3.2` A 151 /
  B 8, ...) are all long runs where the released t_err equals or nearly equals t_lock (85/85, 105/105, 151/152, 111/111):
  the release puts the "decisive error" at the lock-in in long runs, and whatever produced column B disagrees by 50–140
  steps there. These are the only t_err disagreements that look like genuine earliest-vs-decisive conflicts (P2).

## 3. Targeted statistics

### 3.1 The three timestamps

| quantity | n | median | mean | p10 | p90 | notes |
|---|---|---|---|---|---|---|
| fix window t_lock − t_err | 1,184 | 1 | 6.6 | 0 | 20 | 39.1 % zero, 43.9 % ≥ 3, 20.2 % > 10 |
| t_obs − t_lock | 852 | 1 | 2.3 | −9 | 14 | **negative in 241 (28 %)**: symptom visible *before* lock-in; 149 zero |
| t_obs − t_err | 852 | 4 | 10.1 | 0 | 26 | |
| steps after lock-in m − t_lock | 1,184 | 9 | 23.2 | 1 | 49 | 44.5 % of all steps are post-lock-in |
| t_err / m | 1,184 | 0.31 | 0.38 | 0.09 | 0.78 | |
| t_lock / m | 1,184 | 0.57 | 0.56 | 0.15 | 0.93 | |

By length (m): win=0 share 58 % (m ≤ 10) → 39 % → 32 % → 37 % (m > 100); silent 45 % → 34 % → 17 % → 12 %; never-aware 79 %
→ 67 % → 45 % → 44 %; t_err/m 0.47 → 0.33 → 0.27 → 0.10. Short runs fail silently and instantly; long runs fail early,
loudly and then thrash.

### 3.2 Trigger mechanism (root cause) vs process shape

| trigger | n | med fix win | % win=0 | % silent | med t_err/m | % forewarn | % never aware | % fabric |
|---|---|---|---|---|---|---|---|---|
| false_premise | 364 | 2 | 36 | 31 | 0.29 | 64 | 56 | 37 |
| knowledge_gap | 284 | 1 | 42 | 24 | 0.30 | 60 | 51 | 15 |
| spec_neglect | 176 | 1 | 44 | **44** | 0.30 | **39** | **86** | 14 |
| environment_obstacle_mishandled | 104 | 2.5 | 39 | 13 | 0.38 | **90** | 44 | **50** |
| capability_limit | 104 | 1 | 48 | 21 | 0.39 | 48 | 55 | 14 |
| misread_output | 52 | 2 | 29 | 21 | 0.37 | 81 | 69 | 25 |
| ignored_signal | 49 | 2 | 22 | 16 | 0.48 | 88 | 55 | 18 |
| premature_action | 44 | 3 | 32 | 32 | 0.33 | 70 | 52 | 23 |

Spec-neglect (ignored a requirement) is the silent, never-noticed, forewarning-free failure; environment-obstacle is the loud
one (90 % forewarning, 50 % fabrication). Epistemic triggers do not have a single signature.

### 3.3 Awareness × tail behaviour (counts)

| awareness | cosmetic | fabrication | immediate claim | new wrong dir | thrash | verif. theatre | n |
|---|---|---|---|---|---|---|---|
| never_aware | 51 | 100 | 195 | 22 | 74 | **253** | 695 |
| aware_wrong_fix | 26 | 65 | 13 | 75 | **170** | 64 | 413 |
| aware_abandoned | 8 | 11 | 6 | 6 | 16 | 4 | 51 |
| aware_too_late | 5 | 3 | 2 | 1 | 8 | 6 | 25 |

- never_aware: median fix window 1, median 7 steps after lock-in, 0 recovery attempts; aware_wrong_fix: fix window 4,
  15 steps after lock-in, 4 attempts. Awareness *lengthens* the run without changing the outcome.
- Silent failures are 309/695 never-aware vs 23/489 aware: awareness is almost perfectly predicted by whether a signal
  surfaces, i.e. agents notice what the environment shows and nothing else.
- Verification happened in 936/1,184 FAIL runs and *after* lock-in in 647 (54.6 %): verification is the normal tail of a
  failed run, not a rarity; the final step is a claim (C) in 832/1,184 FAIL and 434/610 PASS runs, a verification (V) in
  169 / 137. The last two action codes do not separate PASS from FAIL.
- first_awareness vs t_obs: 246 after, 167 at, 53 before — the agent becomes aware when the symptom surfaces, rarely before.
- Fabrication onset − t_lock: median 0 (p10 −2, p90 22): fabrication starts *at* lock-in in half the fabricating runs — the
  false claim is the lock-in step itself.

### 3.4 Action code at the three timestamps (action_segments)

| | W write | X execute | V verify | C claim | E explore | P plan | R repair |
|---|---|---|---|---|---|---|---|
| t_err | **687** | 241 | 31 | 19 | 106 | 72 | 16 |
| t_lock | **647** | 313 | 64 | 54 | 35 | 34 | 32 |
| t_obs | 55 | **351** | **347** | 30 | 35 | 3 | 25 |

t_err is a *write* in 58 % of runs and is the **first write step in 482/1,184 (40.7 %)** (first execute step: 9.7 %); t_obs
is an execute or verify step in 82 %. The structural prior "first write" alone lands on t_err in 41 % of failures
(consistent with README §3.2's 41.9 %), which is above any published attributor on long CLI runs.

### 3.5 Forewarning

732/1,184 (61.8 %) have a forewarning; its first step is before t_err in 370, at t_err in 120, after t_err in 242. Types:
empty_or_unexpected_output 456, command_error 415, repeated_command 180, contradictory_evidence 109, self_doubt 48. So a
"visible error sign" precedes or coincides with the decisive error in 41 % of failures — but see 3.6: the same signs are in
PASS runs.

### 3.6 PASS runs

- error events: mean 2.29, median 1, 71 % ≥ 1; recoveries mean 1.8; max detour median 3 (p90 15, max 170).
- first error event at relative position 0.28 (median) — the same place as FAIL t_err (0.31). On the 58 tasks with both
  outcomes, median FAIL t_err 7.0 vs median PASS first-error 5.5.
- `pass_error_observability`: observable 320 / silent 113 / none 177 → 26 % of PASS error events are silent, vs 28 % of
  FAIL runs: the silent/observable ratio is outcome-independent.
- suspicious_pass 39 (6.4 %: proxy_solution 21, lucky_environment 13); verification_before_claim 586/610; near_miss 52;
  directness: trial_and_error 224 / direct 201 / detour 185 — a third of successes are trial-and-error.

### 3.7 Matched design

Pass rate per task: median 0.24, 28/89 tasks have zero passes, 2 have 21/21. Per system (21): pass 19–45 %, silent share
14–50 % (terminus2/gemini 50 %, openhands/deepseek 14 %), verification theatre 3–48 % (gpt5/miniswe 3 %, kimi/terminus2 48 %),
median fix window 0–6. Process shape is a property of the *system*, not of the task: gemini is silent-and-short everywhere
(median m 12–20, win 0–1), deepseek/kimi thrash long (m 46–81, win 3–6).

## 4. Baseline error analysis

Not possible (no step text). The paper's own prefix monitor (Sonnet 4.6, 2,659 prefixes): 82 % precision, recall 18.2 %,
median lead time 0 — consistent with 3.1/3.6: the monitor can only fire on t_obs-type evidence, which is 1 step after
lock-in in the median run and absent in 28 %.

## 5. Annotation issues

**5.1 The dual-annotation file is not a second annotation (high confidence).** `docs/kappa_agreement/dual_annotations.csv`:
- annotator_A equals the released label in **1,184/1,184 (t_err), 1,184/1,184 (t_lock), 852/852 (t_obs)**.
- annotator_B − A for t_lock is **uniform on [−10, +10]** (33–83 runs per value, 58 exact = 4.9 %); for t_obs uniform on
  [−10, +10] plus a 211-run spike at 0 (24.8 %); for t_err it is +1 in 558, −1 in 474, 0 in 144 (12.2 %), and ≥ 3 in only 7.
- the offset does not scale with run length (mean |B−A| for t_lock 5.2 at m ≤ 10, 4.9 at 11–30, 5.3 at 31–100), and B
  violates the codebook's own invariants: **t_err > t_lock in 247 runs, outside [1, m] in 226 runs**. No human reading a
  10-step run writes t_lock = 17.
- Hence the reported weighted κ 0.95 / 0.94 / 0.96 measures agreement with a jittered copy, not inter-annotator
  reliability; the categorical κs (trigger 0.83, awareness 0.80, tail 0.78, fabrication 0.90; disagreement 165 / 135 / 211 /
  46 of 1,184) may be genuine — their confusions are semantically plausible (false_premise↔spec_neglect,
  never_aware↔aware_too_late, verification_theater↔cosmetic_progress) — but they also cannot be verified. The report's
  "κ 0.94–0.96 on the same draft" (P3) should be downgraded to "no usable timestamp IAA".
- The release is effectively **one LLM draft (Claude Opus 4.6) per run, human-reviewed**; `uncertain_fields` flags t_err in
  295 runs (24.9 %), t_commit 183, t_surface 180 — the annotator's own uncertainty on the decisive step is a quarter of runs.

**5.2 t_err = t_lock convention drift in long runs.** In the 7 real B-vs-A conflicts above, the released t_err sits at the
lock-in step of a 100–200-step run; the "earliest decisive error" has been collapsed onto "the step that sealed it" when the
run is long (the drafting prompt reads only steps 1–40, every 5th, and the last 30 when m > 120: 57 FAIL runs are
`long_traj`). Expect t_err in long runs to be late-biased by construction.

**5.3 Stray values**: forewarning_types contains trigger values (3 runs); `suspicious_pass_type` hardcoded_output /
test_overfitting never used; trigger `other` ×7 with t_err/m = 1.0 (the "error" is the final claim).

## 6. Candidate hypotheses

**H-FaP-1 "Same signal, different fate" (recovered-error indistinguishability).** The observable error events that precede
t_lock in FAIL runs are drawn from the same distribution as the error events in PASS runs (command errors, empty output,
ModuleNotFound, `sudo: not found`); 71 % of PASS runs have ≥ 1, at the same relative position (0.28 vs 0.31). A prefix monitor
therefore cannot flag t_err from the *observation*; it can only flag the *response* to it (retry vs pivot vs ignore). Evidence:
§3.5–3.6, the acl-permissions pair. Test: rejoin CodeTracer step text; score any prefix monitor on PASS error events vs FAIL
t_err — predicted: equal flag rates (false-positive rate on PASS events ≈ recall on FAIL t_err). Shared with: agenterrorbench
(ALFWorld "Nothing happens" in every run), agenthallu clean runs with tool errors, horizon successes with OS errors. Targeted
method: score the *transition* (obs_t, act_{t+1}) rather than obs_t — a "repair-quality" classifier conditioned on the error
type, trained on PASS recoveries as negatives.

**H-FaP-2 "Lock-in is a commitment write, symptoms are executions"** (structural prior). t_err/t_lock are W steps (58 % /
55 %), t_obs is X/V (82 %); the first write hits t_err in 41 %. A label-free attributor that restricts candidates to writes
and weights the first write would beat position priors. Test: compare "first W" vs "argmax anomaly" on rejoined data; on
trajerrbench-SWE the analogue (gold = edit step in 70 %, first edit only 14 %) says the prior is dataset-specific — Terminal-
Bench tasks have one decisive artefact, SWE-Pro has 7 edits per run. Shared with: trajerrbench-SWE (weaker), agenterrorbench
WebShop (buy-now click).

**H-FaP-3 "Awareness is observability"**: agents notice only what the environment shows (silent: 309/695 never-aware vs
23/489 aware; first_awareness ≥ t_obs in 413/466). So the agent's own verbalised doubt is a *lagging* symptom, never a lead
indicator; "self_doubt_language" is the rarest forewarning (48). Methods that look for verbalised confusion (OAT App. H)
will have zero lead time by construction on CLI agents. Test: on rejoined data, measure lead time of self-doubt tokens vs
t_lock (predicted ≤ 0). Shared with: agenterrorbench (reflection blocks say "progress is fine" until the cap).

**H-FaP-4 "Verification theatre is the modal tail, so the end of the run is uninformative"**: V after lock-in in 55 % of
failures, final step is C in 70 % of FAIL and 71 % of PASS; verification_before_claim is true in 96 % of PASS and
verification_ever in 79 % of FAIL. Last-k-step judges (P8) see the same thing in both classes. Test: TF-IDF on the last
agent message, PASS vs FAIL → predicted AUROC ≈ 0.6 here vs 0.83 reported for τ²-bench by Advani, because CLI agents verify
in both classes. Shared with: trajerrbench-SWE (32 of 57 runs with tests after gold have a passing test run).

**H-FaP-5 "Fix-window length is a system trait, and determines what a monitor can save"**: median fix window 0–1 for gemini /
gpt5 / devstral-openhands, 3–6 for deepseek / kimi / claude. The alarm-cost model (README row 18) must be evaluated per
system: for gemini (win 0 in 50 %+, silent 30–50 %) a monitor has nothing to save; for deepseek-openhands (win 5, silent
14 %) it has ~5 steps. Test: per-system lead-time distribution after rejoin.

**H-FaP-6 "t_obs before t_lock = the window where the run is still salvageable and the signal exists"**: 241 runs (28 % of
those with t_obs) have the symptom *before* lock-in. These are the only runs on which "positive lead time" is achievable at
all; they are enriched in environment_obstacle and misread_output triggers (forewarning 81–90 %). Any monitoring claim should
be reported on this subset separately.

## 7. Open questions

- Which of the categorical B columns are genuine? The trigger confusion matrix looks human; the timestamp columns do not.
  Only the authors can say; until then cite "one LLM-drafted, human-reviewed label, no IAA".
- Does t_err in long runs drift toward t_lock because of the step-sampling in the drafting prompt (steps 1–40, every 5th,
  last 30)? Testable by re-drafting the 57 long runs with full context once text is available.
- Rejoin: 71 % of runs are public CodeTracer trajectories; the matched 89×21 design would then be the only dataset with
  PASS/FAIL pairs on identical tasks *and* three timestamps — the natural test bed for H-FaP-1 and for the P1 offset
  measurement (predicted judge offset ≈ t_obs − t_err = 4 median).
