# G3 — single-agent natural failures: cross-dataset synthesis (Nov 2026)

Datasets: trajerrbench (τ²-bench 400 + SWE-Pro 86), agenterrorbench (ALFWorld 100 / WebShop 50 / GAIA 50), agenthallu (443
hallucinated + 250 clean), horizon (3,782 judge-labelled runs, 294 web step labels), failure_as_process (1,184 FAIL + 610 PASS
annotations, no step text). Per-dataset notes in `findings/datasets/<slug>.md`; this file only synthesises. Probes: prefix
monitor (Qwen3.8-27B, prefix only, no outcome) on 20 records per dataset; all-at-once baseline on trajerrbench (80), agenthallu
(40, list-task-safe copy), agenterrorbench / horizon PENDING (runner). Status of each section is marked where numbers are
missing.

## 1. What recurs across the five datasets

**R1. The labelled step is a *convention* applied to a chain, and each dataset's convention sits at a different point of the
same chain: proposal → commitment → symptom → claim.**
- trajerrbench τ²: the label is the *proposal* message (318/400 = 79.5 %); the DB write follows at +2 (123 runs) / +4 (70);
  the baseline's modal miss is exactly +2 (8/34 misses, 4 land on the write itself).
- agenthallu: the label is a near-deterministic function of the category and a structural landmark (Planning → step 0 in
  96 %, Human-Interaction → the first `ask_human` in 89 %, Retrieval → the *fetch* step that returned the bad evidence, not
  the step that adopted it; oracle-category position rules reach 55.8 % exact, above every published LLM attributor).
- agenterrorbench: the label sits at the n-th repetition of a symptom (later than the first malformed action in 51/71 ALFWorld
  runs; later than the first "Nothing happens" in 54/77), i.e. at the *entry into the stagnation phase*.
- horizon: the judge's step is "first deviation" in 31 % of runs and "at/after the first syntactic anomaly" in 53 %; its
  reason text cites the loop in 77 % of cases even though the label is at the loop start in only 9.9 %.
- failure_as_process: three timestamps make the chain explicit (t_err W-step 58 %, t_lock W 55 %, t_obs X/V 82 %); the
  released t_err collapses onto t_lock in long runs (the 7 genuine disagreements are 50–140 steps apart).
Consequence: a method's "late bias" is measured against a moving target; the *same* prediction (the DB write, the adoption
step, the first repetition) is +2 on τ², +1 on agenthallu-Retrieval, −k on agenterrorbench. Signed-offset reporting must be
per convention, not per method (gap in P1 confirmed and sharpened).

**R2. Silent failures are the majority, and they are the ones labels cannot be checked on.**
- τ²: 262/400 (65.5 %) have no transcript symptom at all (no tool error, no user pushback); baseline exact 30/60 on those vs
  3/7 with a tool error — the model *cannot* use a symptom it does not have, so it falls back to the earliest rule violation it
  can find (−8 in `f3362419`).
- agenthallu: in 84 % of hallucinated runs the correct answer never enters the context ("the right evidence never arrived"),
  tool errors occur at the same rate in clean (33.6 %) and hallucinated (40.4 %) runs; the Qwen detection probe without ground
  truth reaches only 23/40 detections with 8/40 false alarms, and *every* exact-step success (8/8) is on a detected run.
- failure_as_process: 28 % silent; by trigger, spec_neglect is 44 % silent and 86 % never-aware.
- horizon: 227 OS "Success" judge labels on env-fail runs, 86 % ending in a confident `answer(...)` (P4).
- agenterrorbench is the exception — ALFWorld/WebShop produce "Nothing happens" / empty result pages every few turns — but
  there the symptom is so frequent that it stops being informative (R4).

**R3. The visible error signs appear in successes at the same rate.** FaP PASS runs: 71 % have ≥ 1 error event, at the same
relative position (0.28) as FAIL t_err (0.31), with the same evidence strings (`sudo: not found`, ModuleNotFoundError);
agenthallu clean runs carry tool errors at the hallucinated rate; horizon OS: 89 % of *passing* OS runs have "swallowed
output" responses, and loops/repeats separate OS pass from fail at AUROC 0.53–0.57; web: `Action: none` in 58 % of GPT passes
vs 61 % of fails. The prefix monitor therefore flags 8–24 % of pre-label steps and 35–75 % of post-label steps on every
dataset — it detects *trouble*, not *the cause*.

**R4. Terminal/harness artefacts decide a large fraction of "natural" failures and are label-free detectable.** horizon:
75.5 % of GPT OS failures answer the in-context example question (`/etc`), 93 % of "Catastrophic Forgetting" labels are this
mechanism; 38 % of Claude OS failures end with `finish` instead of `answer`; 89 % of web failures end in an early stop
(parse ×3 or max steps). agenterrorbench: 33 % of GPT-4o ALFWorld turns and 46 % of Llama turns are quoted/prose-wrapped
actions the environment rejects, and 24/25 runs with ≥ 10 malformed actions are labelled with a cognitive module. τ²: 29
runs are ended by the simulated user mid-confirmation (14 blamed on the agent), 25 end in `transfer_to_human_agents`.
agenthallu BFCL: silent `None` responses in 8–22 % of gold steps. A pre-attribution *artefact checker* (regexes on the last
two turns and on action syntax) would remove a third to three quarters of the runs from the step-attribution problem.

**R5. Loops are the symptom phase, and labels sit at their entry, not at their cause.** agenterrorbench: action-repeat
fraction 0.10 → 0.38 (ALFWorld), 0.30 → 0.64 (WebShop), 0.01 → 0.58 (GAIA) before vs after the label; horizon web: 66 % of
failures contain the same action ≥ 3× vs 8 % of passes, but the judge places the label at the loop start in only 9.9 %; FaP:
thrash_repeat is the tail in 22.6 % and the aware-wrong-fix runs make a median 4 recovery attempts over 15 post-lock steps. The
monitor's post-label flag rate (56 % AEB, 75 % HOR, 37 % τ², 35 % AH) is the loop.

**R6. Annotation quality problems are specific and nameable, not diffuse noise.**
- FaP: `dual_annotations.csv` column B is a jittered copy of A (B−A uniform on [−10,+10] for t_lock, ±1 for t_err; B violates
  t_err ≤ t_lock in 247 runs and [1, m] in 226); the reported κ 0.94–0.96 is not inter-annotator agreement.
- trajerrbench: the zh edition (the one the paper evaluates on) ships the hidden user goal in `task_description`; en does not.
  Giving Qwen the goal changes 16/50 predictions but not accuracy (22 → 22) — outcome knowledge changes *which* step is
  blamed, not how often it is right (replicates the Who&When-with-GT finding). One label on a tool message; 14 user-stop
  terminations blamed on the agent.
- agenterrorbench: labels copied from another run (`Qwen3-8B_008`, `GPT-4o_003`), 23 Llama labels with no type/reason,
  19/157 reasons reused verbatim, ~50 % of ALFWorld labels name cognition for a format error.
- agenthallu: 73 Human-Interaction labels blame an `ask_human` *call* (asking is punished), 112 labels at step 0, Retrieval
  labels one hop before the agent's mistake.
- horizon: 25.4 % of category labels change between two passes of the same judge; 12 step labels on runs the environment
  passed; embodied labels flip pass/fail 26 % between passes.

## 2. Where the datasets differ, and why

| axis | τ² (TEB) | SWE-Pro (TEB) | AEB ALFWorld/WebShop | AEB GAIA / AH | HOR web/OS | FaP |
|---|---|---|---|---|---|---|
| what fails | hidden DB state vs policy/intent | hidden tests | budget cap after loop | wrong final claim | env checker / judge | hidden tests |
| symptom in transcript | 34 % | self-tests pass in 32/57 | every few turns ("Nothing") | rarely (16 % GT ever visible) | loop / early stop 89 % | 72 % (28 % silent) |
| label convention | proposal message | an edit among ~7 | n-th repetition | category landmark | mixed first/last | decisive write; = lock-in when long |
| local detectability (prefix probe, gold flagged) | 60 % | not probed | 40 % (ALF 2/9) | 45 % (AH) | 85 % | n/a |
| baseline exact | 49 % | 15 % | PENDING | PENDING (40 recs) | PENDING | n/a |
| dominant miss | +2 (write) | −5…−92 (early edit) | expected −k (first repetition) | expected +1 (adopt vs fetch) | expected on `none`/stop | — |

Why: the *checker* determines the symptom. Where the checker is a hidden DB diff or hidden tests (τ², SWE-Pro, FaP, BFCL)
failures are silent and labels are outcome-informed reconstructions; where the checker is the environment's own step feedback
(ALFWorld, WebShop, horizon) symptoms are abundant but uninformative; where the checker is answer equality (GAIA, agenthallu
QA) the symptom is the absence of evidence, which no local monitor sees. Local detectability tracks this: 85 % (horizon, loud
harness) → 60 % (τ², policy rules) → 40–45 % (AEB/AH, hindsight and provenance labels).

## 3. Ranked hypotheses (group-wide first)

1. **Convention-aware offset (R1).** Every attributor's signed offset against each dataset is dominated by a dataset-specific
   constant (+2 τ², +1 AH-Retrieval, −k AEB loops, 0 ↔ t_lock FaP). A method that predicts the *chain* (proposal, commitment,
   first symptom, claim) and lets the scorer pick the convention will beat single-step methods on every set at once. Test:
   output 3 steps per run, score each against each dataset's gold; expected: the "commitment" output matches τ² at +2 → 0,
   the "first symptom" output matches AEB. Cheap: re-score existing baseline outputs with a per-dataset shift.
2. **Artefact-first attribution (R4).** Run deterministic checkers (terminal action, action syntax, example-leak, user-stop,
   transfer) before any LLM attribution; on horizon-OS-GPT this alone explains 75 % of failures, on ALFWorld-GPT-4o half the
   budget. Test: precision of regex checkers vs env verdict on all 3,332 horizon runs and 100 ALFWorld runs.
3. **Same-signal-different-fate (R3; FaP H1, AH H3).** Monitors must score the *response to* an error, not the error. Test on
   FaP once text is rejoined (PASS error events vs FAIL t_err flag rates), and now on agenthallu clean vs hallucinated runs
   with tool errors (flag rate on clean tool-error steps vs gold steps).
4. **Silent-failure ceiling (R2; TEB H2).** Exact-step accuracy on τ² is bounded by the policy-decidable share (~60 %); the
   remaining 40 % need the oracle (goal or DB diff) — and even with the goal Qwen does not gain. Test: split every τ² result by
   "has transcript symptom"; replicate with Gemini-class judges to see whether the goal helps stronger readers.
5. **Category-then-position (AH H1).** Predict the failure category first, then apply the category's structural rule; 55.8 %
   oracle ceiling on agenthallu vs 41 % best LLM. Test two-stage prompting on agenthallu, then AEB (module) and TEB (module).
6. **Label-at-entry-of-loop (AEB H2, HOR H4, R5).** Human and judge labels mark the *entry* into stagnation; the first
   occurrence of the repeated (action, observation) pair precedes it in > 60 % of runs. Test: compute first-recurrence step vs
   label on AEB and horizon web; re-label a sample with the first occurrence highlighted.
7. **Hindsight labels are unflaggable (AEB H4, HOR §3.5 misses, τ² unflagged proposals).** The gold steps the prefix monitor
   calls "reasonable" (12/20 AEB, 8/20 τ², 3/20 HOR) are exploration-order / candidate-selection choices wrong only given hidden
   state. Test: give the attributor the hidden state (object location, user goal, failing test) and measure the jump; the
   residual is the convention problem (1).
8. **Fetch-vs-adopt (AH H2).** Retrieval labels sit on the tool call that returned bad evidence; attributors that ask "who
   asserted the falsehood" land +1. Test: signed offset per category on the agenthallu baseline (PENDING) and on TEB obs.*.
9. **Proposal/commit offset (TEB H1)** — the τ² instance of (1), already measured: modal miss +2, 4/34 on the write.
10. **SWE-Pro is structurally under-determined (TEB H4).** 7 edits/run, self-tests pass in 32/57, median 21 steps after gold;
    κ 0.67 and 24 % best are the ceiling. Test: oracle failing-test names → static back-trace → expected > 50 %.
11. **Judge labels inherit prompt leakage (HOR H3).** 93 % of GPT "Catastrophic Forgetting" = answering the example question;
    a judge without the system prompt invents memory explanations. Test: re-judge with the prompt.
12. **No-decisive-step runs exist (AEB H3, FaP capability_limit 8.8 %, TEB 73 no-write runs).** Attributors need a refusal
    class; test by pass^k with a larger budget.
13. **Awareness = observability (FaP H3).** Verbalised doubt never leads the symptom (self_doubt 48/732 forewarnings;
    first_awareness ≥ t_obs in 413/466); verbalisation-based monitors have zero lead time on CLI agents.
14. **Fix-window is a system trait (FaP H5).** Median 0–1 for gemini/gpt5, 3–6 for deepseek/kimi; monitor value must be
    reported per system.
15. **Human-Interaction is an injection experiment (AH H4).** 106 runs got an adversarial human reply; 73 propagated, 23
    absorbed; the label punishes the *ask*. Compare absorption rates with Aegis.

## 4. P1–P8 verdicts with numbers

- **P1 downstream contamination — confirmed, with the sign depending on the convention.** Prefix monitor post-label flag rates:
  AEB 56 % vs 8 % pre, HOR 75 % vs 24 %, τ² 37 % vs 17 %, AH 35 % vs 12 %. Baseline τ²: 20 later vs 14 earlier misses, modal
  +2 (the write). But SWE-Pro misses are *earlier* (7 vs 3; −5 median) and AEB labels are themselves late (n-th repetition), so
  "late bias" is not a universal direction: it is late relative to proposal-type labels and early relative to loop-entry labels.
- **P2 labelled step is a convention — confirmed and quantified.** τ² proposal vs write +2/+4 (79.5 % of labels on the
  proposal); AH category rules 55.8 % oracle; FaP t_err vs t_lock median gap 1, 20 % > 10, and t_err = t_lock in the 7 real
  long-run disagreements; HOR first-deviation 31 % vs at/after-anomaly 53 %; AEB label after first repetition in 51/71.
- **P3 anchoring on pre-annotations / outcome — confirmed in mechanism, not in magnitude.** τ²: 65.5 % of labels are on
  runs with no transcript symptom, so they *must* come from the diagnostics; zh goal leakage; FaP κ file is synthetic. The
  magnitude test (goal probe) shows outcome knowledge changes 32 % of predictions without changing accuracy.
- **P4 outcome-only judges fooled by assertive closings — confirmed on horizon.** 227 OS judge-Success on env-fail, 86 %
  ending in `answer(...)`; r3 repeats 80.8 % of r2's disagreements (rubric, not noise). AH detection probe: 17/40 hallucinations
  missed without ground truth; all exact-step successes require detection first.
- **P5 length degradation — confirmed, modest within these short sets.** τ² 52 % (11–30 msgs) → 34 % (> 30); SWE-Pro
  15 %; HOR r2=r3 agreement 85 → 67 % from ≤ 5 to 16–30 steps; FaP silent share and never-aware *fall* with length (45 → 12 %,
  79 → 44 %) — long runs are loud, short runs are silent.
- **P6 normal flow — refuted as a dynamics claim, confirmed as a length/termination claim.** HOR web AUROC(n_steps) 0.87–0.91
  but OS repeat features 0.53–0.57; 91 % of failing higher-level web runs reproduce the whole passing lower-level run before
  diverging; FaP PASS runs: 71 % with error events, 37 % trial-and-error, 6.4 % suspicious passes; AH clean runs carry tool
  errors at the hallucinated rate. Successes share *phase structure* (first write 41 % of FaP t_err), not clean dynamics.
- **P7 absorption vs cascade — confirmed; fate is decided by the response, not the error.** FaP: same evidence string in PASS
  (recovered) and FAIL (decisive) runs; AH Human-Interaction 73 propagated / 23 absorbed of 106 adversarial replies; AEB
  GAIA 24/50 runs with repeated identical tool errors, label on the first in only 3.
- **P8 verification theatre / false success — confirmed and shown to be outcome-independent.** FaP: verification after
  lock-in in 55 % of FAIL runs, final step a claim in 70 % FAIL / 71 % PASS; TEB-SWE: passing self-tests after gold in 32/57,
  20 explicit completion claims; HOR OS judge-Success on `answer()`-ending failures; τ²: 198/400 runs end "anything else? →
  STOP" regardless of outcome. The end of the run is where every class looks the same.

## 5. What is still pending (exact commands)

- agenterrorbench §4: `python3 -I baseline/all_at_once.py agenterrorbench --n 60 --workers 4 && python3 -I inspect/analyze_baseline.py agenterrorbench`
- horizon §4: `python3 -I baseline/all_at_once.py horizon --n 60 --workers 4 && python3 -I inspect/analyze_baseline.py horizon`
- agenthallu §4: `python3 -I inspect/agenthallu_baseline.py agenthallu --n 40 --workers 2` (shared baseline crashes on BFCL
  list-valued tasks — a loader/render incompatibility to fix in `loaders/agenthallu.py`: stringify `question`), then
  `python3 -I inspect/analyze_baseline.py agenthallu`
- FaP: everything beyond annotations needs the CodeTracer rejoin.
