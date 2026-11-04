# Time-series methods for failure attribution: synthesis

*Written 2026-10-30. Anchor: OAT (Yeh, Zhu, Deep, Li, NeurIPS 2026, arXiv:2607.12747). Starting hypothesis (the user's): OAT takes its mathematical model from the Neural CDE paper (Kidger et al. 2020, arXiv:2005.08926) and applies it to failure attribution, so other time-series formulations may transfer the same way. This file is the synthesis; the evidence is in the eight files listed at the end (about 550 KB, roughly 300 verified papers, seven parallel survey slices plus two analysis notes). Numbers marked **measured** were computed this session on data in `data/`; scripts are in `scripts/lit_timeseries/`. Everything else is a reasoned expectation.*

## 1. The hypothesis holds, at equation level

OAT's Eq. (4)-(7) are Kidger et al.'s Eq. (1)-(3) with the observation renamed: a natural cubic spline control path through `(h_t, u_t)` with a time channel, an initial state from the first observation, `z(u) = z(0) + ∫ f(z) dX`, solved as an ODE. What OAT adds is not the dynamics but (i) a one-class reconstruction loss on successful runs, (ii) a gate on `dX/du`, (iii) a conformal per-step threshold, and (iv) CORAL for domain shift. Full table in `01_oat_vs_ncde.md`.

Three things about the transfer are weak, and the literature confirms each (`lit_A`):

- **The motivation evaporates.** NCDE gains are documented on irregularly sampled, informative timestamps (PhysioNet, MIMIC-IV, CERT). OAT's `u = t/T` makes every trajectory a regular grid; the only irregularity left is variable length.
- **The spline makes OAT non-causal, even on the knot grid.** The natural-cubic-spline derivative at a knot weights neighbours roughly −0.80, 0, +0.80, −0.22, +0.06 on `h_{t−2..t+2}` (**measured** with scipy), so an error at step `k` leaks into the scores of `k−1` and `k−2`, and OAT cannot run as a prefix monitor. The fix is Morrill et al.'s rectilinear or Hermite-backward interpolation (arXiv:2106.11028, in `torchcde`). The time channel `t/T` is itself non-causal.
- **The objective is degenerate.** Kidger's Theorem C.1 says an NCDE can represent the identity between paths; reconstructing the control path therefore has a zero-score optimum for every trajectory. OAT's scores depend on the optimiser not reaching it. The gate, which throttles atypical increments so `z` cannot follow them, is what prevents collapse and is the whole OOD gain (+0.172 AUROC, with −0.028 in-domain). TSAD calls this "anomalies reconstructed too well" and solved it in USAD / Anomaly Transformer / TranAD (`lit_B`).

Deciding experiments, all small: score steps by the gate alone; swap the spline for a causal interpolant; predict-before-ingest; train once on successes and once on all runs. OAT's code is not released, so this is a reimplementation from Eq. (4)-(13).

## 2. OAT as a recipe, and the literatures that own each slot

OAT = step representation + model of *normal* behaviour + per-step deviation score + decoder with a false-alarm guarantee, trained on successes only. Each slot has a field (table in `01_oat_vs_ncde.md` §4). What the seven slices add is that the same recipe, under different names, has been run and critiqued for decades:

| Field | The OAT-shaped method there | What that field learned that OAT does not use |
|---|---|---|
| TSAD (`lit_B`) | EncDec-AD, LSTM-VAE, LSTM-NDT: train on normal, reconstruct, threshold on held-out normal | Point-adjust and "hit rate" reward random scores; 1-NN / PCA / L2 match deep detectors; run-to-failure bias = position priors; no one-class method catches a fluent wrong step |
| Process mining (`lit_E`) | conformance checking: align a trace to a model discovered from successful traces, first "model move" = deviation | discovery from few looping traces yields permissive models; align to a *task reference* instead; score a node given its causal parents (CIRCA), not its prefix |
| Event sequences (`lit_G`) | DeepLog / FSM surprisal under a success-model over step types | mark-only surprise detects symptoms (`t_obs`), not causes; omission scores formalise missing verification |
| Change-point (`lit_C`) | CUSUM / BOCPD on a per-step score | a monitor is a stopping time, delay ≥ 0 by construction; calibrate per run, not per step; report within task |
| Signatures (`lit_A`) | SigMahaKNN conformance on expanding windows, calibrated by splitting the normal corpus | training-free; the baseline the CDE must beat |

## 3. Findings that converge across slices

**3.1 Every label-free or one-class method localises the symptom, not the cause.** This is the single strongest result. OAT's App. H says it fires on failure verbalisation and reactions to empty tool returns. On Failure-as-a-Process (FaP) marks, transition surprise fitted on PASS runs lands within ±1 of `t_err` 19.6% of the time (position prior 25.2%) but does slightly better on `t_lock` and `t_obs` (**measured**, `lit_G`). RUDDER-style return decomposition credits the step where failure becomes *predictable* (`lit_F`). An L1 noisy-OR / hazard posterior puts mass on steps generated by an already-failed run (`lit_D`). Quickest-detection theory says a monitor's delay past the change is non-negative for every true detection, so "positive lead time against `t_lock`" can only come from the fix window `[t_err, t_lock)`, which has median 1 step and is empty in 39% of FaP failures (**measured**, `lit_C`). Consequences: (a) score every method against `t_err`, `t_lock` and `t_obs` separately where the dataset has them; (b) add a "first observable symptom" heuristic as a mandatory baseline, since it is what exposes this bias; (c) the only mechanisms that move credit *backwards* from symptom to cause are dependency-graph transport (CIRCA / Budhathoki Shapley / TVT, `lit_E`, `lit_F`), Hawkes branching posteriors (`lit_G`) and rollouts (P1).

**3.2 Baselines are much stronger than any paper reports.** Position priors were known (brief §1). The slices add two more families:

| Baseline | Dataset | Exact hit | Position prior | Source |
|---|---|---|---|---|
| first write/edit step | FaP `t_err` (1,184) | 41.9% | 10.1% | **measured**, `lit_G`, `lit_E` |
| first source-file edit | TraceElephant SWE-Agent `k*` (44) | 45.5% | 4.5% | **measured**, `lit_G` |
| first WebSurfer step | Who&When Hand-Crafted (58) | 19.0% | 3.4% | **measured**, `lit_G` |
| step before first `Computer_terminal` turn | Who&When Alg.-Gen. (126) | 34.1% | 19.8% | **measured**, `lit_G` |
| first skipped gold call (reference alignment) | AgentHallu BFCL (103) | 36% (fires on 55%) | 18% | **measured**, `lit_E` |
| first surprising step-type (success model) | FaP `t_err` | 21% | 10% | **measured**, `lit_E` |

Caveats: the rules were chosen after inspecting the same data (held-out validation on TrajErrBench SWE-Pro, AgentErrorBench, LongRCA is required); they may reveal an annotation convention ("decisive = first wrong commit") as much as a property of failures; no gain on TraceElephant's GAIA multi-agent runs. Separately, `lit_B` recomputes OAT's Who&When numbers against the metric's structure: with one gold step and k = 3, F1 = hit/2 with a ceiling of 0.5, so OAT's F1 0.23 is its hit 0.45 halved; random top-3 hit is 0.286, first-3 is 0.359, so OAT's skill over the position prior is about 0.14 with a ±0.07 confidence interval on 184 runs. The RCA field went through the same crisis (random "Dummy" ties most PC/Granger + PageRank methods, ASE'24; rule-based matches SOTA on four benchmarks, FSE'26; `lit_E`).

**3.3 Proposal 2's hazard model is one object with five names.** The discrete-time logistic hazard with time-varying internal covariates and right-censored successes (`lit_D`: person-period regression, pycox `LogisticHazard`) is, at L1, current-status survival data whose likelihood `1 − Π(1−h_t)` is exactly noisy-OR multiple-instance learning (`lit_B`, `lit_D`); its cumulative hazard is the Shiryaev statistic *without* a post-change likelihood (`lit_C`); it is the grouped-time intensity of a latent terminal mark, `h_t = 1 − exp(−∫λ_F)` (`lit_G`); and it is RUDDER's return decomposition constrained to be monotone with one change point (`lit_F`). Each field contributes a known defect and a known fix:

| Defect | Field | Fix |
|---|---|---|
| failures-only release identifies timing only up to a one-parameter family (Jewell & van der Laan 2004) | survival | record the pass rate of the system that generated the successes and weight by it |
| post-lock steps are internal covariates of an already-failed run, so hazard rises on symptoms | survival / WTAL ("localisation by classification") | model post-lock steps as emissions of a hidden locked state (absorbing 2-3 state chain = Shiryaev filter), mask the final step, Hide-and-Seek dropout |
| unmodelled task difficulty makes population hazard fall with step index (Vaupel 1979) and inflates pooled AUROC (within-task AUROC 0.50-0.55 in 2026 monitor papers) | survival / monitoring | per-task frailty or stratification; report within task; same-task negatives (FaP: 89 tasks × 21 systems) |
| the target is `k_lock`, not `k*` | all | multi-state model healthy → erred → locked → observed, giving separate posteriors for `t_err`, `t_lock`, `t_obs`; L1+ restarts turn current-status into interval-censored data |
| hazard forbids recovery | RL credit | RUDDER-style unconstrained decomposition, or a transient state that absorbs recovered errors |
| failure modes are competing causes | survival | cause-specific heads give a joint (when, mode, who) posterior and can train on Aegis / MAST mode labels that have no step |
| some tasks are infeasible, no step to blame | survival | cure / "doomed at step 0" atom |

The cheapest decisive experiment uses data already on disk: FaP ships per-step action codes for all 1,794 PASS and FAIL runs; a logistic hazard on codes + position + per-task frailty can be fitted at L1 today and scored separately against the three timestamps (**measured** so far: mark-only hazard 7.9% exact on `t_err`, below the position prior, `lit_G`, so content covariates are needed). Caveat: FaP's `action_segments` boundaries coincide with `t_err` / `t_lock` / `t_obs` in 86-88% of runs vs 55% by chance (**measured**, `lit_C`, `lit_G`), so use per-step codes, never segment structure.

**3.4 The dependency graph is the lever OAT does not pull.** SymFail (event-dependency graph; 47% of edges join non-adjacent steps, **measured** on 600 graphs, `lit_E`), MemTrace (execution DAG) and TRAIL (OpenTelemetry span tree) ship the structure that microservice RCA needs. CIRCA scores a node by how unusual it is *given its parents* and promotes a parent when its children are also abnormal; Budhathoki et al. split outlier blame over ancestors with Shapley values (in DoWhy). Both target OAT's documented failure mode. For log-only datasets, TraceCompiler's def-use rule recovers data edges from tool arguments at P 0.93 / R 0.94. No LLM-free RCA method has been run unchanged on any of these three datasets, and the datasets release no successes, which every such method needs.

**3.5 Counterfactual surrogates: TE-CDE is OAT's missing half.** The three notions of "the step that caused it" differ (`lit_F`): model-prediction importance (time-series saliency), return contribution under the agent's own policy (RL credit), and the effect of an executed intervention (sequential causal inference; this alone is the report's `φ`). TE-CDE (Seedat et al. ICML 2022, arXiv:2206.08311) is an NCDE encoder plus a decoder driven by the treatment path, i.e. P1's surrogate `f(τ_{<k}, s_k, δ)` built on OAT's encoder. Agent logs violate positivity (one action per prefix), so it must be trained on randomised interventions: the Aegis injector on MASLab (temperature 0) and repair rollouts on τ²-bench / ALFWorld / WebShop / SWE-bench. Restart-measured prefix values (arXiv:2610.17633) are the ground truth for all three notions and already show that 66% of judge-labelled "first mistake" steps show no success drop.

**3.6 "Who" has formal versions.** Hawkes branching posteriors and CAUSE give instance-level "which mark excited the failure mark" (`lit_G`); COMA / Shapley counterfactual credits give per-agent effects, exact under temperature-0 replay (`lit_F`); EventADL-style actor-resource random walks are the cheap graph version (`lit_E`). All must beat the role prior (LongRCA 40.3%, Who&When HC 53.4%), and none has been tried on agent logs.

**3.7 The evaluation protocol is the most valuable transfer.** Four slices independently propose it: analytic random values and k-matched position and mark priors reported as skill scores; affiliation precision/recall and VUS with the tolerance set from annotator disagreement; PA%K / PSDS-style curves for set-valued labels (MP-Bench, AgentRx, TRAIL); ranked probability score and PIT calibration for posteriors; per-run conformal false-alarm rate, AMOC curves, P(lead > 0), within-task AUROC and temporal stability for monitors; task-disjoint splits; and a label-free check on replayable systems (success drop when the top-ranked steps are replaced and re-run). Formulas are in `lit_B` §4, `lit_C` §4 and `lit_D` §4.

**3.8 The data gap.** No released dataset has outcomes + step text + real timestamps together (`lit_G`), and none has step text + all three timestamps (`lit_C`). The core MAS benchmarks release failures only, and the three graph datasets release no successes. The data engine of the report (τ²-bench, ALFWorld/WebShop, SWE-bench / Terminal-Bench, MASLab with the Aegis injector) is therefore a prerequisite for most of the L1 and all of the L1+ methods below, and the FaP rejoin with the public CodeTracer trajectories (71% of runs) is the prerequisite for any U3 model result.

## 4. Consolidated method-to-benchmark matrix

Top items across the seven rankings, deduplicated and ordered by (effort, expected information). "Decides" states what the experiment settles.

| # | Method | Slice | Benchmark(s) | Target | Supervision | Effort | Decides / expected gain |
|---|---|---|---|---|---|---|---|
| 1 | Evaluation package (random + position + mark + first-symptom baselines, skill scores, affiliation / VUS / PSDS, per-run FAR, within-task) | B, C, D, E, G | all 21 | all | none | S | Makes every later claim falsifiable; likely shrinks several published gains to within the prior's CI |
| 2 | OAT ablations: gate-only score, causal interpolant, index time axis, predict-before-ingest, successes vs all runs | A, B | Who&When, AgentHallu | `k*` | L1-sel. | S | Whether the gate, the spline look-ahead or the CDE carries OAT's 0.76 AUROC |
| 3 | Floor suite on OAT's embeddings: 1-NN to success bank, PCA error, Mahalanobis, linear AR residual, SigMahaKNN conformance, untrained gated CDE | A, B | Who&When, AgentHallu, HORIZON | `k*` | L1-sel. | S | Whether learning adds anything over distance to successes |
| 4 | L1 logistic hazard on FaP action codes + position + task frailty, scored vs `t_err` / `t_lock` / `t_obs` | D, G | FaP (1,794 runs, on disk) | 3 timestamps | L1 | S | Which timestamp an L1 posterior recovers; frames Proposal 2 |
| 5 | Reference alignment: first model move against gold actions / calls / expert plans; Declare rules from the written policy | E, F | TrajErrBench-τ², AgentRx τ rows, AgentHallu-BFCL, AgentErrorBench-ALFWorld | `k*`, `a*` | L0 + spec | S | Orthogonal to OAT (omissions vs embedding anomalies); BFCL pilot 0.28-0.36 vs 0.18 |
| 6 | Omission / commission scores for missing verification and premature termination | G | FaP, MAST-Data, TrajErrBench VERIFY.*, Aegis FM-3.x | mode + step | L1-sel. | S | A rule already separates (C-without-V 16% PASS vs 29% FAIL); OAT cannot express omissions |
| 7 | Symptom CUSUM + process-mining XGBoost monitor, conformal test-martingale wrapper on OAT scores | C | FaP rejoined, AgentRx, Terminal-Bench / τ² | `t_lock` lead, recall at FAR | L1 | S | The monitor baselines any neural U3 must beat; per-run guarantee instead of OAT's per-step one |
| 8 | Hidden multi-state model (healthy / erred / locked / observed) = Shiryaev filter with post-lock emissions; forward = online monitor, smoother = offline attribution | C, D | FaP, AgentRx, Who&When, TrajErrBench | `t_err`, `t_lock`, `t_obs`, `k*` | L1 (+L1+) | M | Moves posterior mass from symptoms toward lock-in / error; one model for U1 and U3 |
| 9 | Parent-conditional anomaly with descendant adjustment (CIRCA) / Shapley outlier attribution on OAT's embeddings over the shipped graphs | E, F | SymFail, MemTrace, TRAIL (+ TraceElephant via def-use edges) | failure node, `E`, `a*` | L1 (needs collected successes) | M | The only non-rollout mechanism that walks back from symptom to cause |
| 10 | Paired same-task success/failure MIL (Sultani / RTFM top-k), final step masked, position-only MIL control; Deep SAD / PU with 25-200 labelled steps | B, D | AgentHallu, HORIZON, data-engine corpora; test TrajErrBench, AgentErrorBench | `k*`, `E` | L1 (+ small L2) | M | Only family that can raise reasoning-error recall above the prior |
| 11 | RUDDER-style causal prefix-success model with action/observation half-steps and per-task offset; blame = drop between consecutive predictions | F | τ² → TrajErrBench, AgentRx; ALFWorld/WebShop → AgentErrorBench; AgentHallu | `k*`, `k_lock`, assistant vs user | L1 | M | Causal, online, uses failures, allows recovery; expect `t_obs` bias, mitigated by #9-style transport |
| 12 | Censored marked-TPP hazard with mark × content covariates (EasyTPP backbone, cloglog head) | G | FaP, AgentHallu, data-engine corpora; test Who&When, TraceElephant, TrajErrBench | `k*`, `t_err`, `t_lock` | L1 (+L1+) | M | Must beat the mark prior; mark-only version measured below position |
| 13 | Competing-risk hazard with cause-specific and agent heads; mode-only likelihood on Aegis | D | Who&When Pro, Aegis, AgentRx | (step, mode, agent) | L1 + mode | M | Joint when / what / who from one model; uses 11k mode-labelled traces no step method uses |
| 14 | Spectrum attribution over replays (TraceRCA / MicroRank / FAMAS, Ochiai on (agent, step-type, tool, argsig)) | E | self-collected τ², ALFWorld, Terminal-Bench, K = 10-20 runs per task | `a*`, `k*` | L1 over replays | M-L | FAMAS reports +9.6 pp step over the best LLM on Who&When; unknown on natural replayable sets |
| 15 | Hawkes branching posterior / CAUSE / difference rewards under temperature-0 replay for "who" | G, F | LongRCA, Who&When HC, TraceElephant Magentic-One, Aegis | `a*` | L0 / L1+ | M | Must beat the role prior; plausible only on long logs |
| 16 | Restart-measured prefix values (EPV protocol) as ground truth; L1+ interval-censored hazard from restarts | D, F | TraceElephant SWE-Agent, TrajErrBench SWE-Pro, τ², Terminal-Bench | `k_lock` (certified PNR), `k*` | L1+ | L | Largest expected gain: restarts identify position, which L1 cannot; tests whether `k*` labels mark causes |
| 17 | TE-CDE / Causal-Transformer surrogate `f(prefix, k, δ)` trained on Aegis injections + repair rollouts | A, F | MASLab, τ², ALFWorld/WebShop, TraceElephant SWE replay | `φ` profile, `k*`, fragility | L1+ | L | Replaces rollouts at test time; the competitor is the rollout `φ`, not the prior |
| 18 | Alarm-based cost model with `eff(k)` measured by rollouts | C | TrajErrBench-τ², TraceElephant SWE, Terminal-Bench | net cost, operational `t_lock` | L1+ | L | Connects U3 to P1; a monitor judged by cost saved |

Low value, documented so they are not re-proposed: off-the-shelf deep TSAD (Anomaly Transformer, TranAD, DCdetector) on 10-step series (`lit_B`); critical-slowing-down early-warning signals (`lit_C`); per-trajectory kernel / PELT segmentation except as a long-trace baseline (`lit_C`); Inductive-Miner discovery from successes (`lit_E`); synthetic control / interrupted time series / Granger for instance-level `k*` (`lit_F`); off-the-shelf NCDE anomaly detectors SDA2D / GDFlow / PoA, all offline spline-based (`lit_A`).

## 5. Pilot numbers measured this session

All single runs, no confidence intervals, rules chosen post hoc on the data they are scored on. Scripts: `scripts/lit_timeseries/`.

| What | Data | Result |
|---|---|---|
| natural-cubic-spline derivative weights at a knot, uniform grid | synthetic | −0.804, 0, +0.804, −0.215, +0.058 on `y_{i−1..i+3}`: non-causal (`lit_A`) |
| OAT metric structure | Who&When 184 | random top-3 hit 0.286, first-3 0.359, OAT 0.451; F1 ceiling 0.5 at k=3; random exact 0.095, random ±1 0.263; best constant relative position ±1 0.408 (`lit_B`) |
| fix window `t_lock − t_err` | FaP 1,184 FAIL | 0 steps in 39%, median 1; `t_err` oracle median lead +1; `t_obs` oracle median lead −1, positive on 20%; 28% silent (`lit_C`) |
| naive symptom alarm on PASS runs | FaP 610 PASS | 71% contain ≥ 1 error event (false alarms) (`lit_C`) |
| clock baseline at 10% per-run FAR | FaP | catches 28% of failures, median lead −12 (`lit_C`) |
| segment-boundary leakage | FaP | `t_err` / `t_lock` / `t_obs` on an `action_segments` boundary 88 / 86 / 81% vs 55% chance (`lit_C`, `lit_G`) |
| mark-structural priors | FaP, TraceElephant-SWE, Who&When | see §3.2 (`lit_G`) |
| transition surprise (PASS-fitted) vs `t_err` / `t_lock` / `t_obs`, ±1 | FaP | 19.6 / 22.6 / 17.7% vs position 25.2 / 19.4 / 15.1% (`lit_G`) |
| mark-only L1 hazard, exact `t_err` | FaP | 7.9% vs position 10.1% (`lit_G`) |
| outcome-blind HMM change point | FaP | outcome AUROC 0.498; lands on `t_err` 29.3% (explore→edit phase boundary) (`lit_G`) |
| run length as a failure detector | FaP | AUROC 0.653 (`lit_G`) |
| C-without-V rule (claim with no verify in previous 3 steps) | FaP | 16.3% PASS vs 28.7% FAIL (`lit_G`) |
| Magentic-One ledger stall flags vs `k*` | Who&When HC 58 | flags in 36 logs; first flag after `k*` in 61%, median 4.5 steps later (`lit_G`) |
| first-surprising-step-type decoder vs first-write rule | FaP | 0.21 vs 0.41 exact, 13% overlap; trajectory AUROC 0.58 < length 0.65 (`lit_E`) |
| gold-call alignment | AgentHallu BFCL 103/61 | first deviation 0.28, first skipped call 0.36 (fires on 55%) vs position 0.18; within ±2 position wins 0.64; alignment-cost AUROC 0.655 vs length 0.47 (`lit_E`) |
| non-adjacent dependency edges | SymFail 600 graphs | 47% of edges (`lit_E`) |

## 6. A phased plan

- **Phase 0 (days, data on disk).** Items 1-7 of §4. Deliverables: the evaluation package applied to OAT's published numbers and to the report's Section 7 baselines; the OAT ablation table; the FaP hazard-vs-three-timestamps table; the reference-alignment and omission baselines. These settle how much of OAT is the gate, how much of any attributor is a prior, and which timestamp L1 recovers.
- **Phase 1 (weeks, needs collected successes).** Collect successes on τ²-bench, ALFWorld/WebShop, Terminal-Bench and MASLab; rejoin FaP with CodeTracer; collect SymFail-style successes with the SymTrace capture layer. Then items 8-13: the multi-state model, CIRCA on the graph datasets, paired MIL, the RUDDER-style attributor, the marked-TPP hazard, competing risks on Aegis / Who&When Pro.
- **Phase 2 (months, needs rollouts).** Items 14-18: spectrum attribution, restart-measured prefix values as ground truth, the TE-CDE surrogate on randomised interventions, the cost model. These are the time-series versions of Proposals 1 and 3 and share the report's data engine.

## 7. Per-benchmark view

| Dataset | Time-series methods that fit, and why |
|---|---|
| Who&When, MP-Bench | OOD test only (no successes, output-only logs, live web). OAT ablations (1.1), floor suite (1.2), signature conformance (1.3), Hawkes "who" on Hand-Crafted (2.10); MP-Bench consensus rate is a human estimate of a graded error set, so nDCG@5 and PA%K with consensus weights |
| TraceElephant | SWE-Agent subset is replayable: EPV restart curves (3.1); mark prior "first source edit" 45.5% **[computed]**; full LLM I/O supports def-use graph recovery for 2.7; Magentic-One ledger flags are a built-in symptom monitor (first flag after `k*` in 61%, median 4.5 steps later **[computed]**) |
| Who&When Pro, CORRECT-Error, TracerTraj | injected, late-position prior: use as Tier-C exact-label tests only, with last-k baselines; Who&When Pro's 17 modes for competing-risk heads (2.8) |
| LongRCA | long (median 145): signature-MMD / PELT change points as label-free baselines, Neural RDE / Log-NCDE for tractability, Hawkes branching for roles; affiliation metrics handle the length; 40% exact agreement caps everything |
| AgentRx | `k_lock` labels and all failure events: the lock-in target for 2.2, 2.5, 2.6; tau-bench rows replayable |
| SymFail, MemTrace, TRAIL | the three datasets with graphs: parent-conditional RCA (2.7), TVT-style transport; TRAIL and MemTrace are the only ones with real timestamps (3S / time-rescaling GoF, Resource Abuse via TOOL-mark intensity); none ships successes, so collect them |
| Aegis, MAST-Data | (agent, mode) and trace-level mode labels without steps: competing risks with known cause / unknown time (2.8); MIL "who" over agent bags; Aegis's temperature-0 wrappers give exact difference rewards for "who" |
| AgentErrorBench, TrajErrBench | replayable single-agent systems with human steps: the Tier-A training grounds for 2.3, 2.5, 3.1-3.3; AgentErrorBench's early prior (0.23) and TrajErrBench's late prior (0.65) are the two position regimes a method must clear |
| SearchAuditBench | tolerance spans: Tatbul front-end range recall, span-mass metrics; final answer is the critical step in 17%, so a final-step baseline is mandatory |
| Failure-as-a-Process | the only release with both outcomes and all three timestamps: hazard on codes (2.1), multi-state model (2.2), monitor ceilings (0.3), frailty estimation (89 × 21); step text must be rejoined from CodeTracer; codes leak labels |
| AgentHallu, HORIZON | the only released sets with successes and text: in-domain one-class and L1 training (1.2, 2.3, 2.4); BFCL gold calls give a task reference for alignment (1.4) |

## 8. Corrections and additions for the report

- Brief / report text saying OAT "omits positional baselines" should read "omits *k-matched* positional baselines": OAT reports Random-Step and First-Step as single-step baselines (`lit_B`).
- MP-Bench publishes a random nDCG@5 (0.128 hand-crafted, 0.315 automatic) but no position prior (`lit_B`).
- FaP's "82% precision / 18% recall" monitor headline is computed per prefix and excludes prefixes taken before lock-in, so early warnings in the fix window count as neither hits nor false alarms; and the cut grid is a fraction of `t_lock`, so lead-time resolution is about 3 steps (`lit_C`).
- FaP `action_segments` leak the timestamps (§5); any model must use per-step codes.
- GraphTracer (arXiv:2510.10581) has been withdrawn for a methodology error; CHIEF (arXiv:2602.23701) compares against it (`lit_E`).
- Mark-structural priors (§3.2) belong next to the position priors in the report's Section 7 and in Proposal 2's baseline list.
- The report's Proposal 2 should name its model class (discrete-time logistic hazard, current-status likelihood = noisy-OR MIL) and cite the identifiability results of §3.3; its `\note{}` question ("why would the agent's own policy assign high probability to its mistakes?") is answered by the selection argument in `lit_B` and `lit_D`: under the agent's policy, a fluent wrong summary is a typical draw; the only thing that makes it atypical is conditioning on the success-selected reference, and the only thing that makes it *causal* is the outcome or an intervention.

## 9. Consolidated open gaps

1. No causal, non-degenerate one-class NCDE detector exists; no NCDE paper localises errors among discrete events; no control path for marked events or span trees.
2. No paper applies TPPs, Hawkes influence, RCA-from-traces, conformance checking, survival analysis or RL credit assignment to an agent attribution benchmark and scores it against `k*`. The nearest 2026 work (Cho et al. FSMs, Dubey's ESN+CUSUM, TraceToChain, PrefixGuard, Time-to-Inconsistency, MASC) reports trajectory-level or prefix-level numbers, or step AUROC without position baselines.
3. No benchmark pairs step labels with measured prefix-value curves beyond EPV's 107 SWE-bench failures; no injected set has uniformly randomised positions with both failed and absorbed branches released.
4. The latent absorbing event has no treatment in survival or MIL theory with language covariates; "transient" (change-and-revert) changes, which are 71% of FaP successes, were not surveyed in the change-point slice.
5. Lead-time and false-alarm conventions differ across the 2026 monitor papers; no per-run standard exists.
6. The mark vocabulary is not standardised across datasets; the mark-structural priors depend on a cross-dataset step-type tagger that does not exist.
7. What "time" is for an agent (steps, tokens, wall-clock, progress) is unresolved; a token clock did not improve the position prior on TraceElephant **[computed]**.

## 10. Files

| File | Slice | Size |
|---|---|---|
| `00_context_brief.md` | shared brief: datasets, labels, supervision levels, OAT and NCDE formulations | 14 KB |
| `01_oat_vs_ncde.md` | equation-level comparison and derivations | 10 KB |
| `lit_A_nde_signatures.md` | NCDE lineage, online interpolation, Neural RDE/SDE/CNF, signatures and conformance | 56 KB, ~40 papers |
| `lit_B_tsad.md` | one-class / reconstruction TSAD, evaluation pitfalls, weak-label and video-MIL localisation, log anomaly detection | 82 KB, ~65 papers |
| `lit_C_changepoint_online.md` | change-point, quickest detection, early classification, predictive process monitoring, monitor protocol | 75 KB, ~50 papers |
| `lit_D_survival_weak_supervision.md` | discrete-time survival, competing risks, cure and multi-state models, RUL, MIL / WTAL / PU | 95 KB, ~65 papers |
| `lit_E_rca_traces_process_mining.md` | metric / trace / log RCA, process mining, conformance, agent observability, two pilots | 77 KB, ~65 papers |
| `lit_F_temporal_attribution_credit.md` | time-series saliency, RL credit assignment, sequential treatment effects, TE-CDE | 90 KB, 50 papers |
| `lit_G_point_processes_event_sequences.md` | TPPs, Hawkes Granger causality, event-sequence anomaly, HMM / switching models, identifiability map | 75 KB, ~45 papers |
| `scripts/lit_timeseries/` | the pilot scripts behind §5 | 11 files |
