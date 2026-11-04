# Lit C: change-point detection, quickest detection and online monitoring, read against t_err / t_lock / t_obs

*Slice C of the time-series survey (`notes/lit_timeseries/`), written 2026-10-30 on top of `00_context_brief.md`. Every paper cited was checked on its arXiv / publisher / index page on 2026-10-30; details that could not be checked are marked **unverified**. Numbers marked **(computed here)** come from the Failure-as-a-Process (FaP) annotation release (`data/failure_as_process/repo_cli_trajectory_analysis/data/traj_data_v2_all89tasks.json`, 1,184 FAIL + 610 PASS runs) and from that repo's own monitor results (`results/oracle_results*.json`, `scripts/sample_oracle.py`, `scripts/score_oracle.py`). The procedure is described in §4.6. FaP has no step text, so these numbers are label-side ceilings and baselines, not model results.*

## 1. Scope and verdict

1. **The vocabulary fits.** `t_lock` is the change time ν of a latent absorbing regime (recoverable → locked). `t_obs` is the change time of the observation channel and `t_err` the change time of the action channel. A prefix monitor is a stopping time T, and its detection delay T − ν is ≥ 0 for every true detection.
2. **What this means for U3.** Positive lead time against `t_lock` is not something a change detector measures. It can only come from alarms inside the fix window [t_err, t_lock) or from precursors and task difficulty. On FaP labels the fix window is 0 steps in 39% of failures (median 1). An oracle that alarms exactly at `t_err` gets a median lead of 1. A perfect first-symptom detector (alarm at `t_obs`) gets a median lead of −1, a positive lead on 20% of failures, and misses the 28% silent ones (computed here). So the prompted monitor's median lead of 0 is close to the ceiling for symptom detection. Its real weakness is coverage: it caught 26% of failed runs, and only 5% before lock-in.
3. **CPD on a single trajectory has too little power.** Each run has one change in 5-150 steps, errors are sparse, and agent or role switches look like changes. Every transfer that works has two stages: pool across runs to learn a per-step score or likelihood ratio, then run a sequential statistic within each run. That is the recipe of NN-CUSUM, of the deep-CPD theory of Li et al. (2024), and, read correctly, of Proposal 2.
4. **Main synthesis.** Proposal 2's cumulative hazard is the Shiryaev statistic *without a post-change likelihood*. Add an emission model for post-lock steps (an absorbing 2- or 3-state chain) and it becomes the Bayes-optimal Shiryaev filter for online `t_lock`. Its smoother gives the offline attribution posterior. Precursor evidence enters through the hazard, which can produce lead; symptom evidence enters through the likelihood ratio, which can only detect after the change.
5. **Alarm calibration with a guarantee is available.** A Shiryaev–Roberts threshold A = m/α bounds the per-run false-alarm probability by α when the likelihood ratio is exact. Split-conformal calibration of the run-maximum gives the same per-run guarantee from successful runs only, and conformal test martingales and e-detectors give comparable distribution-free guarantees (Ville bound, ARL bounds). This is the direct upgrade of OAT's per-step conformal threshold.
6. **Imports from ECTS and process mining.** Alarm-based prescriptive monitoring prices an alarm with a cost model (c_in, c_out, c_com, effectiveness eff(k)), and eff(k) is exactly Proposal 1's repair-effect profile. Per-prefix-length AUC suffers survivor bias, and successful agent runs are shorter (FaP median 16 vs 27 steps). Temporal stability is a separate metric.
7. **The 2026 agent-monitor papers say the same.** In PrefixGuard, AgentForesight, the key-step web monitor, Disentangling Task Difficulty and Last Step Matters, pooled AUROC is dominated by cross-task pairs, and early within-task AUROC is 0.50-0.55. Every U3 number must be reported within task.
8. **Low value.** Critical-slowing-down early-warning signals: the series are too short, and repetition or thrash is a post-lock tail, not a precursor. Per-trajectory kernel or PELT segmentation as an attribution method: useful only as an offline baseline on long traces (LongRCA, TRAIL).

## 2. The three timestamps as change-point objects

### 2.1 Generic model and what each framework estimates

```
y_t            per-step observation: features of s_t = (a_t, u_t, o_t)
z_t ∈ {0,1}    latent; 0 = recoverable/on-track, 1 = locked (absorbing);   ν = min{t : z_t = 1}
y_t | y_<t  ~  f_0(· | y_<t)  for t < ν,     f_1(· | y_<t)  for t ≥ ν
T              stopping time (online alarm) adapted to y_1..y_t
ν̂              offline estimate from y_1..y_m (whole run)
```

| Framework | Estimand | Error / loss | Agent reading |
|---|---|---|---|
| Offline CPD (PELT, BinSeg, kernel CPD) | ν̂ (or a set of change points) | \|ν̂ − ν\|, F1 within margin M, covering | post-hoc location of `t_lock` (single change) or of the event set E (multiple changes) |
| Bayesian online CPD | run-length posterior P(r_t \| y_1:t), r_t = t − (last change) | log predictive loss, location error | online P(change at t); offline MAP segmentation |
| Shiryaev (Bayesian quickest detection) | π_t = P(ν ≤ t \| y_1:t) with a prior on ν (classically geometric with hazard ρ) | minimise E[(T − ν)^+] subject to P(T < ν) ≤ α | **online lock-in probability = U3's target quantity** |
| Lorden / Pollak minimax (CUSUM, SR) | T only (no prior on ν) | worst-case delay WADD = sup_ν ess sup E_ν[(T − ν + 1)^+ \| y_<ν], or CADD = sup_ν E_ν[T − ν \| T ≥ ν], subject to ARL = E_∞[T] ≥ γ | alarm time; delay vs `t_lock`; ARL is measured on successful runs (E_∞ = "no change ever") |
| ECTS / early event prediction | the class S from a prefix plus a trigger time | misclassification cost + delay cost (or harmonic mean of accuracy and earliness) | prefix monitor for S, which mixes precursors (before ν) and detection (after ν) |

**Window algebra for one alarm T on a failed run.** T < t_err is a precursor or task-difficulty alarm; classical CPD calls it a false alarm. t_err ≤ T < t_lock is a useful early warning (inside the fix window). T ≥ t_lock is a detection with delay T − t_lock. On a successful run every alarm is a false alarm, but successful runs contain *transient* changes: 71.0% of FaP PASS runs have at least one annotated error event, median first error at step 5 (computed here). This is the "epidemic", change-and-revert case of the CPD literature, and the reason a detector that fires on the first error is unusable (per-run false-alarm rate ≈ 0.71).

### 2.2 Mapping the labels

| Label | Change-point object | Channel | What can estimate it | FaP facts |
|---|---|---|---|---|
| `t_lock` (FaP), `k_lock` | change time ν of the absorbing latent regime | latent state | offline ν̂; online Shiryaev π_t; T (with delay) | median step 12, relative 0.57 |
| `t_obs` | change time of the observation stream o_t (exceptions, failing tests, contradictory outputs) | observation | any detector on o_t features. It cannot fire before `t_obs` except through precursors | lag t_obs − t_lock: median 1, p10 −9, p90 14. Silent in 28.0%. t_obs < t_lock in 28.3% of non-silent runs |
| `t_err`, `k*` (Who&When, TraceElephant, TrajErrBench, LongRCA, SearchAuditBench) | change time of the action channel u_t: the decisive wrong action/belief | action | detectors that read u_t (embeddings, proxy-LM NLL, LLM judge). Observation-only detectors are blind to it | median step 7, relative 0.31. Fix window t_lock − t_err: median 1, 0 in 39.1%, ≥3 in 43.9% |
| AgentRx root | first failure event *never recovered from*: an action-channel event selected by a state property; best read as lock-in *onset* | action + state | multiple-CPD with a persistence requirement | root ≠ first failure in 27% (41% of Magentic-One): earlier failures are transient changes |
| Error sets E (AgentRx events, TRAIL spans, MP-Bench votes) | multiple change points, or a marked point process of events | action / observation | PELT/BOCPD (multiple changes), event detectors | TRAIL marks the *first* instance of each error, except Resource Abuse (*last*) |
| Tolerance span [k_s, k_e] (SearchAuditBench) | localisation margin | — | F1 within margin M = span | median span length 4 messages |

So OAT, which by its own App. H fires on failure verbalisation and on reactions to empty tool returns, is an observation-channel detector scored against action-channel labels. That mismatch alone predicts a late bias against `k*`.

### 2.3 Ceilings and position baselines for U3 on FaP labels (computed here)

Lead time = t_lock − T, as defined in FaP's `score_oracle.py`. "Caught" means at least one alarm on a failed run. Per-run false-alarm rate (FAR) is the fraction of the 610 PASS runs with any alarm.

| Alarm rule (label-side, no model) | caught (of 1,184 FAIL) | P(lead > 0) | median lead (caught) | per-run FAR |
|---|---|---|---|---|
| oracle at `t_err` (perfect decisive-step detector) | 1.000 | 0.609 | +1 (mean +6.6) | — |
| oracle at `t_obs` (perfect first-symptom detector) | 0.720 | 0.204 | −1 (mean −2.3) | — |
| oracle at `t_lock` | 1.000 | 0 | 0 | — |
| last step m ("last-step shortcut") | 1.000 | 0 | −9 (mean −23.2) | 1.0 |
| first annotated error event | — | — | — | 0.710 |
| clock: alarm when the run reaches step 12 | 0.814 | 0.492 | +3.5 | 0.667 |
| clock: step 20 | 0.635 | 0.311 | 0 | 0.420 |
| clock: step 46 (FAR ≤ 0.10) | 0.282 | 0.068 | −12 | 0.097 |
| clock: step 57 (FAR ≤ 0.05) | 0.198 | 0.044 | −23 | 0.049 |
| FaP prompted monitor (Claude Sonnet 4.6, calibrated prompt; 300 FAIL + 300 PASS) | 0.260 | 0.053 | 0 (mean +1.47) | ≤ ~0.095 (1.9% per-prefix FP × 5 cuts, union bound; not reported per run) |
| same monitor given the task requirements | 0.390 | 0.087 | 0 (mean +1.91) | ≤ ~0.28 (5.5% per prefix) |

What these numbers say:

1. The clock monitor is the position prior that U3 must beat. Failed runs are longer, so "the run is still going" is itself a failure signal. At a matched per-run FAR of about 10%, the clock catches as many failures as the prompted monitor (28% vs 26%) but 12 steps late.
2. The prompted monitor's contribution is *timing*, not coverage. When it fires, its own decisive-step guess is within ±2 steps of `t_lock` in 86-88% of cases (FaP `docs/terminology.md`). Locating lock-in after the fact is easy; alarming early is hard.
3. FaP's headline "82% precision, 18% recall" is computed per *prefix*, on POSITIVE (failed, cut ≥ t_lock) against NEGATIVE (passing) prefixes, with NOTYET prefixes (failed, cut < t_lock) excluded (`score_oracle.py`). Early warnings inside the fix window are therefore neither TPs nor FPs in that number.
4. Failed runs are cut at round(f·t_lock) for f ∈ {0.25, 0.5, 0.75, 1.0, 1.25}, while passing runs are cut at round(f·m) (`sample_oracle.py`). Lead time therefore has a resolution of 0.25·t_lock (about 3 steps at the median), and the cut grid depends on the label. A *trained* monitor evaluated on this grid could exploit prefix length. U3 must be evaluated at every step (§4).

### 2.4 Which datasets provide which change objects

| Dataset | t_err-like | t_lock-like | t_obs-like / symptom channel | multiple events | successes | step text | steps (median) | operational t_lock by replay |
|---|---|---|---|---|---|---|---|---|
| Failure-as-a-Process | `t_err` | `t_lock` (`t_commit`) | `t_obs` (`t_surface`), `forewarning_types` (command_error 415, empty_or_unexpected_output 456, repeated_command 180, contradictory_evidence 109, self_doubt 48) | 8-code `action_segments` for all 1,794 runs; PASS `num_error_events`, `first_error_step` | 610 (annotations only) | **no** (≈3-step excerpts for 433 PASS) | 27 / 16 | Terminal-Bench yes |
| AgentRx | (root) | root = first unrecovered failure | — | all failure events (6.7 per Magentic-One run) | no | yes (73 public) | 33 | τ-bench rows yes |
| TRAIL | first HIGH-impact span (proxy) | — | span `status_code` / tool errors | every error span + impact | mixed, not outcome-selected | yes (A) | 20 spans | SWE subset |
| Who&When | `k*` | — | Magentic-One ledger flags `is_in_loop`, `is_progress_being_made` (built-in self-monitor) | — | no | C | 10 | no |
| TraceElephant | `k*` | — | Magentic-One ledger | — | no (160 withheld) | A | 21 | SWE-agent subset yes |
| TrajErrBench | `k*` | — | — | — | no | B | 29 / 117 msgs | yes |
| LongRCA | earliest unrepaired root | — | — | — | no | B | **145** (root-to-end median 48) | sandboxes only |
| MP-Bench | step sets, 3 annotators | — | — | yes | no | C | 10 | no |
| SearchAuditBench | critical step + tolerance span | — | — | — | no | B | 20 decisions | no |
| HORIZON / AgentHallu | step (HORIZON: 294 web runs) | — | — | — | **yes** | B | 11 / 6 | docker / BFCL subset |

Two warnings about the FaP `action_segments`. They are the only per-step sequence available today with outcomes and all three timestamps. But segment boundaries coincide with `t_err` in 87.8%, `t_lock` in 86.1% and `t_obs` in 80.5% of failed runs, against a base boundary density of 0.555 per step (computed here). The segmentation was produced in the same LLM-drafted annotation pass, so it leaks the labels. Use it only as an upper bound for "step-type" features, never as evidence that CPD works. The code at `t_lock` is W (write/edit) in 55% of failures and X (execute) in 26%: lock-in happens on *commit* actions.

## 3. Methods

Each subsection gives: citation, mechanism, mapping (a)-(f) from brief §7, supervision level, what breaks, and code. "OAT score" means OAT's per-step error e_t; "P2 hazard" means Proposal 2's h_θ(τ_<t, s_t).

### A. Offline change-point detection

#### 3.1 Penalised-cost segmentation: PELT, binary segmentation, wild binary segmentation
- **Papers.** Killick, Fearnhead, Eckley, "Optimal detection of changepoints with a linear computational cost", JASA 107(500):1590-1598, 2012, arXiv:1101.1438, DOI 10.1080/01621459.2012.737745. Fryzlewicz, "Wild binary segmentation for multiple change-point detection", Ann. Statist. 42(6):2243-2281, 2014, arXiv:1411.0858, DOI 10.1214/14-AOS1245. Truong, Oudre, Vayatis, "Selective review of offline change point detection methods", Signal Processing 167:107299, 2020, arXiv:1801.00718 (organises methods by cost function, search method and constraint on the number of changes; ships the `ruptures` library).
- **Mechanism.** Minimise Σ_{i=1}^{K+1} C(y_{τ_{i−1}+1 : τ_i}) + β·K over the number K and locations τ of change points. Optimal partitioning solves F(t) = min_{s<t} [F(s) + C(y_{s+1:t}) + β] exactly. PELT prunes any s with F(s) + C(y_{s+1:t}) ≥ F(t), because s can never again be the optimal last change; the expected cost is linear when the number of changes grows with n. Binary segmentation splits recursively at the argmax of a CUSUM-type contrast. WBS takes that maximum over many random sub-intervals, which detects close or small changes, and stops by threshold or a modified SIC. The single-change special case ("at most one change", AMOC) is ν̂ = argmin_k [C(y_{1:k−1}) + C(y_{k:m})]. For a Gaussian mean cost this is the argmax of the standardised CUSUM |S_k − (k/m)S_m| / sqrt(k(m−k)/m).
- **Mapping.** (a) x_t: a scalar per-step score (OAT score, P2 hazard logit, count of symptoms such as tool exception + empty return + repeated command), or a vector for a multivariate cost. (b) Nothing to train (L0) apart from β. (c) Output: a change-point set; AMOC gives one ν̂. (d) Targets: AMOC against `t_lock` (FaP once rejoined with CodeTracer step text; AgentRx root) and against `k*` (LongRCA root: exact / ±5 accuracy). Multiple changes against AgentRx failure events and TRAIL error spans (set-F1 within margin M; TRAIL location accuracy). (e) Baselines: per-dataset position prior (FaP `t_lock` relative median 0.57; Who&When first-3 hit 0.36), the "zero" (no-change) and last-step predictors.
- **What breaks.** (f) A run of 10-30 steps holds one change and a few post-change points, so power is low. In multi-agent runs a change of speaker or role is a distribution change unrelated to failure, so the score must be residualised per role or step type first (like removing seasonality). The penalised cost finds the boundary of the *tail regime* (thrash/repeat 22.6%, verification theatre 27.6% of FaP failures), so it estimates `t_lock`/`t_obs` and will be late against `t_err` by about the fix window.
- **Code.** `ruptures` (Python; verified via the review), R `changepoint` and `wbs` packages (unverified), TCPDBench wrappers (§3.18).

#### 3.2 Kernel change-point detection (KCpA; kernel multiple change-point with model selection)
- **Papers.** Harchaoui, Bach, Moulines, "Kernel change-point analysis", NeurIPS 2008 (NIPS 21, pp. 609-616). Arlot, Celisse, Harchaoui, "A kernel multiple change-point algorithm via model selection", JMLR 20(162):1-56, 2019, arXiv:1202.3878.
- **Mechanism.** KCpA tests for a change in a window with the maximum kernel Fisher discriminant ratio between the segments before and after each candidate point. It derives the null limit distribution, so the false-alarm probability is fixed, and takes the argmax as the location estimate. Arlot et al. use the kernel least-squares cost C(y_{a:b}) = Σ_{t∈[a,b]} k(y_t, y_t) − (1/(b−a+1)) Σ_{s,t∈[a,b]} k(y_s, y_t), i.e. within-segment scatter in the RKHS, minimised by dynamic programming for each number of segments D. D is chosen with a penalty that generalises Lebarbier's (2005) univariate penalty (∝ D·(c1 log(n/D) + c2); exact form and calibration unverified), and they prove a non-asymptotic oracle inequality. Changes in any distributional feature that the kernel sees are detectable.
- **Mapping.** (a) x_t = OAT's 64-d PCA step embedding h_t, or a proxy-LM embedding of (u_t, o_t), with a Gaussian kernel. (b) L0. (c) Segmentation, or with D = 2 one change. (d) `t_lock`/`t_obs` (FaP rejoined), `k*` on LongRCA (median 145 steps, the only set long enough), TRAIL spans (20 per trace). Metrics as in 3.1. (e) Position prior. Also the same segmentation on *shuffled* step order, which shows how much of the signal is ordering.
- **What breaks.** Embeddings change at every phase (explore → write → verify: FaP segments change every ~2 steps), so the kernel cost finds phases, not failures. D is unknown and the penalty theory assumes independent observations. Very short runs (Who&When median 10) make D = 2 nearly the only option.
- **Code.** `ruptures` implements kernel CPD (class names unverified). Original code not checked.

#### 3.3 Learning the penalty or metric from weak labels
- **Papers.** Hocking, Rigaill, Vert, Bach, "Learning sparse penalties for change-point detection using max margin interval regression", ICML 2013, PMLR 28:172-180 (author order differs between sources). Truong, Oudre, Vayatis, "Supervised kernel change point detection with partial annotations", ICASSP 2019, DOI 10.1109/ICASSP.2019.8683471 (method details beyond "learn a metric from partial expert annotations" unverified; the follow-up NeurIPS 2022 workshop paper learns a metric from partial annotations).
- **Mechanism.** Each annotated signal gives an *interval* of log-penalties log β for which the optimal segmentation makes zero annotation errors, where annotations are regions saying "no change here" or "≥1 change here". A per-signal penalty log β_i = w·x_i (x_i = signal features such as log length or a variance estimate) is learned by convex max-margin interval regression (accelerated proximal gradient). Truong et al. instead learn the kernel or metric from a few annotated change points, then segment new signals without labels.
- **Mapping.** (a) As in 3.1/3.2. (b) **Weak L2 on a small calibration set.** Agent labels are already regions: SearchAuditBench tolerance spans [k_s, k_e] ("exactly one change inside"), FaP's [t_err, t_lock] ("the change is here; none before t_err"), MP-Bench consensus sets. (c) Per-run penalty, hence the number of changes, plus a learned step metric. (d) Train the penalty on 20-50 labelled runs and test on the rest: SearchAuditBench CS-Loose (inside span), LongRCA ±5, AgentRx event-set F1. (e) Unlearned BIC/SIC penalty and the position prior.
- **What breaks.** The labelled set must share the step unit and role structure with the test set (brief §1: step units differ). Penalty features such as log m leak run length, which correlates with failure.
- **Code.** R `penaltyLearning` (verified). Truong et al.: not checked.

#### 3.4 Learned CPD detectors: classifiers trained on simulated changes, deep kernels, contrastive latent spaces
- **Papers.** Li, Fearnhead, Fryzlewicz, Wang, "Automatic change-point detection in time series via deep learning", JRSS-B 86(2), 2024, arXiv:2211.03860, DOI 10.1093/jrsssb/qkae004. Chang, Li, Yang, Póczos, "Kernel change-point detection with auxiliary deep generative models" (KL-CPD), ICLR 2019, arXiv:1901.06077. Deldari, Smith, Xue, Salim, "Time series change point detection with self-supervised contrastive predictive coding" (TS-CP2), WWW 2021, arXiv:2011.14097.
- **Mechanism.** Li et al. train a neural classifier on labelled series ("contains a change" or not). Classical tests such as the CUSUM for a mean change can be written as small networks, so a trained network does at least as well given enough data; they bound the error rate as a function of training size. The learned detector matches CUSUM under i.i.d. Gaussian noise and beats it under autocorrelated or heavy-tailed noise. KL-CPD learns a deep kernel for an MMD two-sample test between past and future windows; to cope with few change examples it maximises a lower bound on test power using surrogate samples from an auxiliary generative model. TS-CP2 learns window embeddings with contrastive predictive coding: adjacent windows are positives and distant windows negatives. A change score is a drop in similarity between consecutive window embeddings (exact score from the paper body, unverified).
- **Mapping.** (a) Windows of w = 2-4 steps of embeddings or symptom features. (b) Li-style: **synthetic L2 from injected-failure corpora.** Who&When Pro (12,326), Aegis (9,533, injector public), CORRECT-Error (2,226) and TracerTraj provide trajectories with known injection steps. These play the role of "simulated changes": train there, test on natural failures (Who&When, TrajErrBench, LongRCA). KL-CPD and TS-CP2 are L0 and can use every unlabelled log. (c) Per-step change score. (d) `k*` exact / ±k, AUROC per step. (e) Position prior per dataset. The injected sets carry strong position priors of their own (Who&When Pro relative 0.83; CORRECT-Error 52% in the last fifth), so a detector trained on them must also beat "predict the injected-set prior".
- **What breaks.** Injection artefacts and injected position priors transfer as shortcuts. Contrastive "adjacent = similar" learning treats benign phase transitions as changes, and separating failure-relevant changes needs L1. Windows of 3 in a 10-step run leave few valid positions.
- **Code.** Not checked for any of the three.

### B. Bayesian online change-point detection

#### 3.5 BOCPD, learned hazard, robust BOCPD
- **Papers.** Adams, MacKay, "Bayesian online changepoint detection", arXiv:0710.3742, 2007. Wilson, Nassar, Gold, "Bayesian online learning of the hazard rate in change-point problems", Neural Computation 22(9):2452-2476, 2010, DOI 10.1162/NECO_a_00007. Knoblauch, Jewson, Damoulas, "Doubly robust Bayesian inference for non-stationary streaming data with β-divergences", NeurIPS 2018, arXiv:1806.02261.
- **Mechanism.** The run length r_t is the time since the last change. With hazard H(r), the recursion is P(r_t, y_1:t) = Σ_{r_{t−1}} P(y_t | r_{t−1}, y^{(r)}) · P(r_t | r_{t−1}) · P(r_{t−1}, y_1:t−1), where P(r_t = 0 | r_{t−1}) = H(r_{t−1}+1) and P(r_t = r_{t−1}+1 | r_{t−1}) = 1 − H. The predictive P(y_t | ·) comes from a conjugate model of the current segment, and normalising gives the run-length posterior. This is exact online inference of the most recent change, and P(r_t = 0 | y_1:t) is the online change probability. Wilson et al. place a hierarchy on H, so the hazard is inferred rather than fixed. Knoblauch et al. replace the likelihood by a β-divergence generalised posterior, which makes BOCPD robust to outliers (false discoveries reduced "from >90% to 0%" on real data), with linear time and constant space.
- **Mapping.** (a) y_t = scalar or low-dimensional step score (OAT score, symptom indicators, proxy-LM NLL), modelled conditionally on step type or agent. (b) L0 with constant H. **L1 with a learned covariate hazard H_θ(τ_<t)**: that is P2's hazard plugged into BOCPD as the change-time prior, and Wilson et al. is the constant-covariate version of this idea. (c) Online P(r_t = 0); offline MAP segmentation; "the last change before the end" estimates `t_lock`. (d) `t_lock` and lead time (FaP rejoined); AgentRx failure events as the multiple-change set (set-F1); TRAIL spans. (e) Clock monitor (§2.3) for the online use; position prior for the offline use.
- **What breaks.** BOCPD assumes exchangeable observations within a segment, but agent steps within a regime are neither stationary nor exchangeable (progress, role alternation). The predictive model therefore needs conditioning (a GRU predictive is fine, but then conjugacy and exactness are lost). The absorbing lock-in model is a special case: zero hazard after the first change, or a two-regime product partition. Single tool exceptions are outliers, not changes, which is the case robust BOCPD was built for. Recovered errors in successes are transient changes that standard BOCPD will flag.
- **Code.** Not checked for the originals. TCPDBench (§3.18) wraps `bocpd` and `bocpdms` (both appear in its verified results).

#### 3.6 Bayesian CPD and survival analysis on rollout-estimated outcome series ("forking tokens")
- **Paper.** Bigelow, Holtzman, Tanaka, Ullman, "Forking paths in neural text generation", arXiv:2412.07961, 2024 (venue unverified).
- **Mechanism.** For each token index t and each alternative token w, they resample S = 30 continuations, so the outcome distribution o_t is a probability-weighted histogram of final answers. They run Bayesian change-point detection on the drift series of o_t: BEAST, linear segments, priors on the number of changes and on the noise, a change accepted when its Bayes factor exceeds 9. Separately, a discrete-time survival analysis uses the hazard h(t) = probability mass of "forking" alternatives that move o_t by more than ε in L2. Some forking tokens are punctuation, i.e. single tokens decide the outcome.
- **Mapping.** (a) t = agent step. The series is V̂_t = fraction of N rollouts from τ_≤t that succeed (L1+), or o_t over final answers. (b) L1+ (rollouts) only, with no step labels. (c) Change points of V̂_t: the largest drop estimates `t_err`, and the first crossing of V̂_t ≤ ε gives an **operational `t_lock`** (the point of no return of P1 task T3). Hazard of forking steps. (d) Against `k*` on replayable TrajErrBench (τ2, SWE-Pro) and the TraceElephant SWE-agent subset (exact / ±1). Against FaP `t_lock` on re-run Terminal-Bench tasks. This also tests whether the annotated `t_lock` ("locked given the agent's actual later behaviour") equals the rollout point of no return. (e) Position prior; P2's L1 hazard as the cheaper competitor.
- **What breaks.** Cost: N rollouts × m prefixes. With N = 10, the binomial SE of V̂_t is up to 0.16, so drops smaller than about 0.3 are invisible. Stochastic environments add variance. Only replayable systems qualify.
- **Code.** Not checked.

### C. Quickest detection

#### 3.7 CUSUM, Shiryaev, Shiryaev–Roberts and the Lorden/Pollak criteria
- **Papers.** Page, "Continuous inspection schemes", Biometrika 41(1-2):100-115, 1954, DOI 10.1093/biomet/41.1-2.100. Shiryaev, "On optimum methods in quickest detection problems", Theory Probab. Appl. 8(1):22-46, 1963, DOI 10.1137/1108002. Lorden, "Procedures for reacting to a change in distribution", Ann. Math. Statist. 42(6):1897-1908, 1971, DOI 10.1214/aoms/1177693055. Moustakides, "Optimal stopping times for detecting changes in distributions", Ann. Statist. 14(4):1379-1387, 1986 (CUSUM exactly optimal under Lorden's criterion for i.i.d. data with known f_0, f_1). Surveys: Veeravalli, Banerjee, "Quickest change detection", arXiv:1210.5552 (book chapter; Bayesian and minimax formulations). Xie, Zou, Xie, Veeravalli, "Sequential (quickest) change detection: classical results and new directions", IEEE JSAIT 2(2):494-514, 2021, arXiv:2104.04186.
- **Mechanism.** With Λ_t = f_1(y_t | y_<t) / f_0(y_t | y_<t) and ℓ_t = log Λ_t:
  ```
  CUSUM:      W_t = max(0, W_{t-1} + ℓ_t),               T_C  = inf{t : W_t ≥ b}
  SR:         R_t = (1 + R_{t-1}) · Λ_t,  R_0 = 0,          T_SR = inf{t : R_t ≥ A}
  Shiryaev:   π̃_t = π_{t-1} + (1 − π_{t-1}) ρ_t            (predict with hazard ρ_t)
              π_t = π̃_t Λ_t / (π̃_t Λ_t + 1 − π̃_t)          (update);  T_S = inf{t : π_t ≥ 1 − α}
  ```
  Lorden showed CUSUM is first-order optimal for WADD subject to ARL ≥ γ, with WADD ≈ log γ / D and D = KL(f_1 ‖ f_0) per step. Moustakides proved exact optimality. SR is the Bayes procedure in the limit of a vanishing geometric prior and is near-optimal for Pollak's CADD. **Per-run false-alarm bounds for short runs (derived here):** under the no-change law, E_∞[Λ_t | y_<t] = 1, so R_t − t is a martingale. Hence P_∞(T_SR ≤ m) ≤ m/A. Since R_t ≥ e^{W_t}, also P_∞(T_C ≤ m) ≤ m·e^{−b}. A run of at most m steps therefore has per-run FAR ≤ α with A = m/α or b = log(m/α). Agent runs end, so this per-run FAR replaces ARL.
- **Mapping.** (a) y_t = per-step features. Λ_t comes from a model of post-lock steps (f_1) against on-track steps (f_0) (§3.8, §3.9). (b) L1 (outcome-supervised Λ) or L2 (where `t_lock` labels exist: FaP, AgentRx). (c) Alarm time T; the Shiryaev posterior π_t is an online lock-in probability. (d) Lead/delay against `t_lock` and `t_obs`, per-run FAR on successful runs, AMOC curve (§3.18); FaP rejoined, AgentRx τ-bench, Who&When/TraceElephant Magentic-One runs (compared with the ledger flags). (e) Clock monitor and first-symptom rules (§2.3, §4.4).
- **What breaks.** f_0 and f_1 are unknown and non-stationary (they depend on task and step type), and the bounds hold only for the true Λ. A learned Λ̂ needs empirical calibration (§3.10). Short runs: with m = 27 and α = 0.1, b ≈ 5.6 nats, so a 2-step delay needs about 2.8 nats of evidence per step (rough Lorden asymptotics, an approximation at this scale). The silent 28% have D ≈ 0 in the observation channel. The change is policy-dependent: the agent reacts to its own error, and post-change behaviour is the tail taxonomy (repairs the wrong problem 24% of runs, keeps repeating 15%, verification theatre 28%, fabricated success 15%, gives up 18%). In practice f_1 is a mixture.
- **Code.** Standard; nothing to check.

#### 3.8 Synthesis: Proposal 2's hazard + an emission model = a Shiryaev filter (online U3) and a change-point smoother (offline U1/U2)
- **Source.** This follows from 3.7 plus brief §4; it is not a paper.
- **Mechanism.** P2's cumulative hazard 1 − Π_{s≤t}(1 − h_s) is π_t with Λ_t ≡ 1. It is a forward prior that never revises the change time with evidence that arrives *after* the change. A run that looked normal until step 7 and has thrashed since gives P2 no way to move mass back to step 7, except by having learned h_7 from step-7 features alone. Fix: an absorbing two-state chain (on-track → locked, transition probability h_θ(τ_<t, s_t)) with emissions f_0, f_1 over step features (shared encoder, two heads), plus the outcome as a final emission (S = 0 iff z_m = 1). The forward algorithm gives the likelihood of (y_1:m, S), fitted at L1 by maximum likelihood or EM. Online, the forward filter is the Shiryaev statistic π_t. Offline, the smoother P(ν = t | y_1:m, S = 0) is the attribution posterior for `t_lock`. Dropping S gives the L0 change-point mixture U2. A third, transient state (error, recoverable, with a return transition) absorbs recovered errors: 71% of FaP PASS runs contain one, and AgentRx roots differ from the first failure in 27% of runs.
- **Mapping.** (a) Step embedding plus symptom features plus step-type code. (b) L1, with L1+ for the hazard and L2 for model selection only. (c) π_t, P(ν = t | ·), P(S = 0). (d) U3: lead/delay against `t_lock` (FaP rejoined), per-run FAR. U1: distance to `t_lock` and `t_err` reported separately (prediction: the smoother sits at `t_lock`, late against `t_err` by the fix window). AgentRx root, Who&When `k*`. (e) Clock and position priors; P2 hazard-only (the Λ ≡ 1 ablation); OAT.
- **What breaks.** Identifiability of f_1 versus the hazard at L1. Precursors (through h) and symptoms (through Λ) can trade off. Report both channels and fix the hazard features to be strictly pre-step.
- **Code.** None; small (one GRU encoder, two heads, forward algorithm).

#### 3.9 Neural likelihood-ratio CUSUM and learned CUSUM for LLM error onset
- **Papers.** Moustakides, Basioti, "Training neural networks for likelihood/density ratio estimation", arXiv:1911.00405, 2019. Gong, Lee, Cheng, Xie, "Neural network-based CUSUM for online change-point detection", arXiv:2210.17312 (v6, 2024; the v1/ICASSP 2023 version by Lee, Xie, Cheng was titled "Training neural networks for sequential change-point detection", DOI 10.1109/ICASSP49357.2023.10095005). Itkin, "Quickest detection of hallucination onset: delay bounds and learned CUSUM statistics", arXiv:2606.12476, 2026.
- **Mechanism.** A classifier trained with logistic loss to separate pre-change from post-change samples has a logit that estimates log f_1/f_0 up to a constant. The logits are accumulated with the CUSUM recursion. The 2024 version adds NTK-based learning guarantees for the standard detection metrics. Itkin treats token-level hallucination onset as a quickest-detection problem with a Markov latent state, validated on RAGTruth. A causal recurrent labeller acts as a CUSUM with learned increments, and Lorden's bound puts the delay floor at about 1.3 tokens at FAR 0.01. Among caught onsets the learned detector alarms in 11-13 tokens against 31 for a linear per-token probe. But every detector catches under a third of onsets at that FAR, the recall-honest delay is 56-66 tokens, and most of the gain comes from a better per-token score, not from temporal accumulation.
- **Mapping.** (a) x_t = step embedding plus symptom features. (b) **L1:** positives = steps of failed runs, negatives = steps of successful runs. Failed-run steps are a mixture π f_1 + (1−π) f_0, so the classifier's odds equal π Λ + (1 − π). The score is still monotone in Λ (a positive-unlabelled argument), provided pre-lock steps of failed runs share f_0 with successful runs. **L2:** positives = steps ≥ `t_lock` (AgentRx, FaP rejoined). (c) Per-step LLR estimate; CUSUM alarm. (d) As 3.7. (e) Clock monitor; the per-step classifier thresholded without accumulation (Itkin's decomposition: does accumulation add anything?).
- **What breaks.** The monotonicity argument fails when failed runs come from harder tasks, because then their pre-lock steps differ from successful runs and the classifier learns difficulty. Draw negatives from successful runs **of the same task** (FaP: 21 runs per task, pass rates 19-45%). Itkin's result warns that U3 gains will come mostly from the per-step score.
- **Code.** Not checked.

#### 3.10 Distribution-free alarms: conformal test martingales, e-detectors, backward confidence sequences
- **Papers.** Volkhonskiy, Nouretdinov, Gammerman, Vovk, Burnaev, "Inductive conformal martingales for change-point detection", arXiv:1706.03415, 2017 (venue unverified). Vovk, Petej, Nouretdinov, Ahlberg, Carlsson, Gammerman, "Retrain or not retrain: conformal test martingales for change-point detection", arXiv:2102.10439, 2021 (venue unverified). Shin, Ramdas, Rinaldo, "E-detectors: a nonparametric framework for sequential change detection", arXiv:2203.03532 (journal unverified). Shekhar, Ramdas, "Sequential change detection via backward confidence sequences", arXiv:2302.02544, 2023.
- **Mechanism.** *Conformal.* Each new observation gets a conformal p-value p_t from its nonconformity score relative to a calibration set. A betting function g (∫g = 1) builds S_t = Π_{j≤t} g(p_j), a test martingale under exchangeability, so Ville's inequality gives P(sup_t S_t ≥ 1/α) ≤ α. Change detection runs a CUSUM- or SR-style procedure on the martingale (the exact construction in Vovk et al. is unverified). The only assumption is i.i.d./exchangeable pre-change data; no model of f_0 or f_1 is needed. *e-detectors.* Sums (SR-type) or maxima (CUSUM-type) of e-processes started at each time. The pre- and post-change classes are nonparametric and composite, ARL has non-asymptotic bounds, and the running example detects a mean change in bounded variables without i.i.d. assumptions. *Backward CS.* Run a forward and a backward confidence sequence for a functional θ and alarm when they stop intersecting; this reduces change detection to sequential estimation.
- **Mapping.** (a) x_t = OAT's e_t, or any bounded per-step score. (b) **L1 at its weakest:** successful runs only, exactly OAT's data. (c) A per-run alarm with false-alarm guarantee α. (d) U3 on MCP-Atlas (OAT's in-domain set) and Who&When (OOD), FaP rejoined; detection rate at α. OAT's App. H says its hard per-step threshold under-detects when several steps are flagged; a martingale accumulates them. (e) OAT top-k / per-step conformal threshold; clock monitor.
- **What breaks.** Steps are not exchangeable within a run (early steps differ from late ones) or across tasks, so validity is only approximate. Mitigations: Mondrian calibration by relative-position bucket and step type; or calibrate at the run level, taking the (1−α)(1+1/n) empirical quantile of max_t W_t over n held-out successful runs. That is valid under exchangeability of *runs*. Stratify by length, since longer runs have more chances to alarm. For e-processes, the null "E[x_t | past] ≤ μ_0" must hold on successful runs, which contain recovered errors, so μ_0 rises and detection slows.
- **Code.** Not checked.

### D. Early classification, precursors and early warning

#### 3.11 Early classification of time series (ECTS): ECTS, ECEC, TEASER, EARLIEST, cost-based triggers
- **Papers.** Xing, Pei, Yu, "Early classification on time series", Knowl. Inf. Syst. 31(1):105-127, 2012, DOI 10.1007/s10115-011-0400-x (ECTS, minimum prediction length, 1-NN). Lv, Hu, Li, Li, "An effective confidence-based early classification of time series" (ECEC), IEEE Access 7:96113-96124, 2019, DOI 10.1109/ACCESS.2019.2929644. Schäfer, Leser, "TEASER: early and accurate time series classification", DMKD 34(5):1336-1362, 2020, arXiv:1908.03405, DOI 10.1007/s10618-020-00690-z. Hartvigsen, Sen, Kong, Rundensteiner, "Adaptive-halting policy network for early classification" (EARLIEST), KDD 2019, pp. 101-110 (DOI unverified). Achenchabe, Bondu, Cornuéjols, Dachraoui, "Early classification of time series: cost-based optimization criterion and algorithms", Machine Learning (accepted 2021), arXiv:2005.09945. Renault, Bondu, Cornuéjols, Lemaire, "Early classification of time series: a survey and benchmark", TMLR 2025, arXiv:2406.18332.
- **Mechanism.** ECTS finds, per training series, the minimum prefix length from which its 1-NN relations are stable, and predicts once a test prefix reaches its neighbour's MPL. Accuracy matches full-length 1-NN. ECEC fuses classifiers trained on N prefix lengths into a confidence score, with one adaptive threshold trading accuracy against earliness. TEASER has two tiers: per-prefix probabilistic classifiers, and a second classifier that decides whether the current prediction is reliable enough to emit (the aeon implementation scores the harmonic mean of accuracy and earliness). It is 2-3× earlier than competitors on 45 datasets at equal or better accuracy. EARLIEST couples an RNN discriminator with a stochastic halting policy trained by RL. Achenchabe et al. minimise E[c_m(ŷ | y) + c_d(t)] non-myopically, estimating the expected cost of deciding at each future t + τ from confidence groups or clusters, and trigger when "now" is the minimiser; this beats myopic triggers. Renault et al. separate *prediction* from *decision (trigger)*, benchmark nine algorithms, and release `ml_edm`.
- **Mapping.** (a) x_t = prefix features (step-type counts, symptoms, embeddings). (b) L1 (S per run). (c) Class probability P(S = 0 | τ_≤t) and a trigger time. (d) U3 lead against `t_lock`, per-run FAR, and the trigger's position relative to [t_err, t_lock]; FaP rejoined, HORIZON (judged successes), AgentHallu (250 clean runs). (e) Clock monitor (§2.3).
- **What breaks.** ECTS assumes the class is fixed at t = 0 and only *revealed* progressively. Agent failure is *created* at `t_err`. A classifier that is confident before `t_err` can only be reading task difficulty or a weak agent, so within-task evaluation is compulsory (§3.17). ECTS benchmarks have fixed length and earliness t/m. Here m is unknown online and varies 1-1,189, so earliness must be measured against `t_lock`, not m. The ECTS delay cost is symmetric in the class, while only the failure class benefits from earliness (the point made by the alarm-based PPM papers, §3.16).
- **Code.** `ml_edm` (verified), aeon `TEASER` (verified). EARLIEST: PyTorch implementation exists (third-party mirror verified; official repo unverified). Others not checked.

#### 3.12 Precursor mining with deep temporal multiple-instance learning
- **Paper.** Janakiraman, "Explaining aviation safety incidents using deep temporal multiple instance learning", KDD 2018, pp. 406-415, arXiv:1710.04749 (DOI unverified; KDD talk by Das & Janakiraman).
- **Mechanism.** Flights carry only flight-level adverse-event labels and no time-step annotation. An RNN scores each time step as an instance, a MIL aggregation produces the bag (flight) prediction, and high-scoring steps are reported as precursors. Recurrence models the temporal build-up. (A secondary summary reports test AUC 0.9447; unverified.)
- **Mapping.** (a) Bag = trajectory, instance = step. (b) L1. (c) Per-step precursor score, i.e. P2's "noisy-OR / any error" MIL relaxation with a recurrent encoder. (d) `k*` (Who&When, TrajErrBench), AgentRx root, FaP `t_err` (rejoined). Lead: precursor peaks before `t_lock`. (e) Position prior; P2 hazard (survival link) as the main competitor.
- **What breaks.** Max-type MIL pooling localises the *most discriminative* step, which in agent runs is the failure verbalisation or final answer (last-step shortcut). Mask the last k steps. Flight data is long and regular; agent runs are short and irregular.
- **Code.** Not checked.

#### 3.13 Clinical early-warning scoring: sepsis utility, AKI lead/false-alert ratios
- **Papers.** Reyna et al., "Early prediction of sepsis from clinical data: the PhysioNet/Computing in Cardiology Challenge 2019", Crit. Care Med. 48(2):210-217, 2020, DOI 10.1097/CCM.0000000000004145. Tomašev et al., "A clinically applicable approach to continuous prediction of future acute kidney injury", Nature 572:116-119, 2019, DOI 10.1038/s41586-019-1390-1.
- **Mechanism.** *Sepsis utility* (from the PhysioNet challenge page). Each hourly prediction U(s, t) is scored. For septic patients, positive predictions between 12 h before and 3 h after t_sepsis earn up to +1.0; very early ones are penalised up to −0.05; late or missed predictions cost up to −2.0. For non-septic patients, a positive costs −0.05 and a negative costs nothing. Score = (U_total − U_no-prediction)/(U_optimal − U_no-prediction). Labels were shifted 6 h earlier; 104 groups submitted 853 entries, and generalisation across hospitals stayed hard. *AKI.* A continuous per-step risk that AKI occurs within the next 48 h, reported as the share of events caught with up to 48 h lead at a fixed false-alert ratio: 55.8% of inpatient AKI and 90.2% of AKI needing dialysis, at 2 false alerts per true alert.
- **Mapping.** (a)-(c) Any per-step risk. (d) **A U3 utility:** reward alarms in [t_err, t_lock] (the useful window), decay the reward from `t_lock` to `t_obs`, give a small penalty for alarms before `t_err` and a large one for misses, give −c per alarm on a successful run, and normalise as above. Report "% of failures caught with lead ≥ k steps at r false alerts per true alert". (e) Clock monitor, which the normalisation automatically compares with "never alarm".
- **What breaks.** Windows of hours become windows of steps. The FaP fix window has median 1 step (0 in 39%), so the reward window often collapses to a point. Scoring every step weights long runs more, so normalise per run.
- **Code.** PhysioNet scoring code (exists per the challenge page; not inspected).

#### 3.14 Early-warning signals of critical transitions (critical slowing down)
- **Papers.** Scheffer et al., "Early-warning signals for critical transitions", Nature 461:53-59, 2009, DOI 10.1038/nature08227. Dakos et al., "Methods for detecting early warnings of critical transitions in time series illustrated using simulated ecological data", PLoS ONE 7(7):e41010, 2012, DOI 10.1371/journal.pone.0041010. Bury et al., "Deep learning for early warning signals of tipping points", PNAS 118(39):e2106140118, 2021, DOI 10.1073/pnas.2106140118.
- **Mechanism.** Near a fold bifurcation, recovery from perturbations slows down (critical slowing down), so rolling variance and lag-1 autocorrelation (also skewness) rise before the transition. Dakos et al. catalogue metric-based and model-based indicators and how to compute them on detrended rolling windows (window and trend-test details unverified here). Bury et al. train a deep classifier on simulated normal-form bifurcations; it flags approaching tipping points, and their type, in systems it never saw.
- **Mapping.** (a) x_t = step-to-step embedding drift ‖h_t − h_{t−1}‖, or similarity to the previous k actions. (b) L0. (c) Kendall-τ trend of the rolling indicator; an alarm when the trend is significant. (d) Lead against `t_lock` on LongRCA (median 145 steps; the only set long enough), FaP rejoined. (e) Clock monitor.
- **What breaks.** Most runs are 10-30 steps, too short for rolling windows. Agent lock-in is not a bifurcation of a smooth system. The repetition pattern that would raise autocorrelation (FaP `thrash_repeat`, the dominant tail in 22.6% of failures) is a *post*-lock signature, i.e. detection, not warning. Low priority.
- **Code.** Not checked.

### E. Predictive process monitoring (process mining)

#### 3.15 Outcome-oriented predictive monitoring, next activity, remaining time
- **Papers.** Teinemaa, Dumas, La Rosa, Maggi, "Outcome-oriented predictive process monitoring: review and benchmark", ACM TKDD, 2019, arXiv:1707.06766, DOI 10.1145/3301300 (24 tasks from 9 real logs, 11 methods; open-source benchmark). Tax, Verenich, La Rosa, Dumas, "Predictive business process monitoring with LSTM neural networks", CAiSE 2017, LNCS 10253:477-492, arXiv:1612.02130. Verenich, Dumas, La Rosa, Maggi, Teinemaa, "Survey and cross-benchmark comparison of remaining time prediction methods in business process monitoring", arXiv:1805.02896 (16 methods, 16 logs; journal version unverified).
- **Mechanism.** Offline: extract all prefixes of the historical cases, *bucket* them (single bucket, by prefix length, by cluster, by state, KNN), *encode* each prefix (static, last state, **aggregation**: counts of activities plus numeric aggregates, index-based) and train a classifier per bucket. Online: bucket and encode the running prefix, then predict the case outcome. Results: XGBoost is best on average; "single bucket + aggregation encoding" has the best AUC in 10 of 24 tasks; aggregation beats last-state encoding. Earliness is evaluated as AUC per prefix length. In some logs AUC *falls* at long prefixes because short, easy cases have already finished and drop out of the evaluation (survivor bias, shown by recomputing on long traces only). Tax et al. predict the next activity and its timestamp with an LSTM and iterate to get the remaining sequence and remaining time.
- **Mapping.** (a) Activity = (agent, tool|status), FaP's 8 action codes, or symptom types (tool exception, empty return, repeated query). Case outcome = S. (b) L1. (c) P(S = 0 | prefix); remaining steps; next step type. (d) U3 AUROC by *absolute* prefix length and by prefix relative to `t_lock`; lead at fixed per-run FAR. FaP rejoined, Terminal-Bench / τ2 (PrefixGuard's benchmarks). (e) **Single-bucket aggregation encoding + XGBoost on step-type counts** is the cheap baseline every learned U3 monitor must beat. PrefixGuard already ran the LSTM form (PPM-LSTM, a tool|status activity alphabet of 34-139 symbols) and beat it on AUPRC in every setting.
- **What breaks.** Survivor bias is worse here than in business logs, because successful agent runs end earlier (FaP median 16 vs 27). Past step 16 most surviving runs are failures, so per-prefix AUC conflates "still running" with "failing". Evaluate on length-matched strata or relative to `t_lock`. Remaining-time prediction is itself a failure signal (failures run long), which is a confound, not a feature to report as success.
- **Code.** Teinemaa benchmark framework (open source, verified). Others not checked.

#### 3.16 Alarm-based prescriptive monitoring and temporal stability
- **Papers.** Teinemaa, Tax, de Leoni, Dumas, Maggi, "Alarm-based prescriptive process monitoring", BPM Forum 2018, LNBIP 329:91-107, arXiv:1803.08706. Fahrenkrog-Petersen, Tax, Teinemaa, Dumas, de Leoni, Maggi, Weidlich, "Fire now, fire later: alarm-based systems for prescriptive process monitoring", Knowl. Inf. Syst. 64(2):559-587, 2022, arXiv:1905.09568, DOI 10.1007/s10115-021-01633-w. Teinemaa, Dumas, Leontjeva, Maggi, "Temporal stability in predictive process monitoring", DMKD 32:1306ff., 2018, arXiv:1712.04165, DOI 10.1007/s10618-018-0575-9.
- **Mechanism.** The cost of a case depends on its outcome and on the first alarm index I (at most one alarm per case):

  | | undesired outcome | desired outcome |
  |---|---|---|
  | alarm at step I | c_in(I) + (1 − eff(I))·c_out | c_in(I) + c_com |
  | no alarm | c_out | 0 |

  Here c_in is the cost of intervening, c_out the cost of the undesired outcome, c_com the cost of compensating an unnecessary intervention, and eff(k) ∈ [0,1] the share of c_out that an intervention at step k avoids. The alarm fires at the first prefix with p̂(undesired | prefix) ≥ τ, and τ is chosen by minimising total cost on a separate thresholding log (TPE). In 2018 a single global τ beat per-prefix-length τ_k. The ROI analysis needs eff·c_out > c_in; at a 1:1 cost ratio never alarming is optimal. The 2022 journal version finds that letting the threshold vary as the case progresses, and *delaying* alarms rather than firing at the first crossing, both reduce net cost. Temporal stability: successive predictions for the same case should not flip. XGBoost and LSTM are the most stable; smoothing improves stability at a small accuracy cost.
- **Mapping.** **eff(k) is Proposal 1's repair-effect profile e_τ(k)**: the success-rate gain from intervening at step k. It is ≈ 0 for k ≥ `t_lock` by definition, and on log-only data the proxy is eff(k) = 1[k < t_lock]. c_in = cost of the intervention (hint, restart, human), c_com = cost of interrupting a run that would have succeeded, c_out = cost of failure. (a)-(b) Any U3 score; L1 for p̂, L1+ to measure eff by rollouts. (c) Alarm policy and net cost. (d) Net cost per run on FaP rejoined (eff proxy) and on replayable TrajErrBench τ2 / TraceElephant SWE-agent (measured eff). FaP's own "early-stop net = steps saved on failed tails − steps cut on passing runs" (best 0.33 for the calibrated monitor) is the special case eff = 0 with a pure step-cost. (e) Never alarm, always alarm, clock.
- **What breaks.** eff(k) cannot be measured off replay. An alarm changes the run (closed loop), while all evaluation here is open loop. Cost ratios are application choices, so report curves over c_out/c_in.
- **Code.** Not checked (Teinemaa's BPM code is referenced in the papers; unverified).

### F. LLM-agent monitors published in 2026 (the closest prior art for U3)

#### 3.17 PrefixGuard, AgentForesight, key-step web monitoring, task-difficulty disentangling, Last Step Matters
- **Papers.** Huang et al., "PrefixGuard: online failure warning and trace-grounded diagnosis for LLM agents", arXiv:2605.06455 (v2 27 Sep 2026, under review). Zhang, Zhu, Shi, Liu, Tang, "AgentForesight: online auditing for early failure prediction in multi-agent systems", arXiv:2605.08715. Pan et al., "Monitoring web agents without internal signals: observable trajectories and key-step supervision", arXiv:2609.02057. EsfandyariDoulabi et al., "Disentangling task difficulty from run-level failure in agent failure prediction", arXiv:2610.05572. Li et al., "Last step matters: early uncertainty cannot predict failure in long-horizon agents", arXiv:2608.29685 (EMNLP 2026).
- **Mechanism and numbers.**
  - *PrefixGuard.* A GRU over learned step events predicts horizon-specific risk P(run fails within H more steps) from **run outcomes only (L1, no step labels)**. A DFA organises event histories for replay and rule monitoring. The alarm fires at the first crossing of a threshold set by **split-conformal calibration on successful runs at a nominal 10% per-run FAR**. Benchmarks: WebArena, τ²-Bench, SkillsBench, TerminalBench (17 agents, 39 backbones). Lead = (1/N₋) Σ_failed (T_i − A_i)_+ / T_i, with misses counted as 0 (Eq. 12). Horizon-averaged lead is 0.15-0.39 against 0.03-0.12 for baselines (PPM-LSTM, PCA-SPE, DeepLog, LogBERT, a zero-shot LLM judge), with recall at 10% FAR of 56-93%.
  - *AgentForesight.* Online auditing with a 7B auditor. RL stage 1 learns from adjacent safe/unsafe prefix pairs; stage 2 localises the decisive step with a what/where/who reward. AFTraj-2K has decisive-step labels from consensus of several LLM judges (L2 via LLM labels). It beats GPT-4.1 and DeepSeek-V4-Pro on AFTraj-2K and on Who&When, with up to 3× lower step-localisation error.
  - *Key-step web monitor.* The prefix-risk label is the **first critical error that stays uncorrected and leads to failure**; earlier prefixes of failed runs count as on-track. This is a lock-in onset label. It uses macro behaviour features plus micro intention/action/expected-state consistency from black-box queries, on WebArena-Lite and Online-Mind2Web, evaluated at fixed "false-cut" budgets.
  - *Disentangling.* Over 99.93% of the positive-negative pairs behind pooled AUROC are cross-task. A difficulty oracle that never sees the run reaches pooled AUROC 0.945 but chance within a task. Early monitors (trajectory predictors, released monitors, hidden-state probes) reach only 0.50-0.55 within task. Aborting pays off only at within-task AUROC of about 0.84-0.93.
  - *Last Step Matters.* On deep-research tasks no uncertainty signal exceeds mean AUROC 0.60 at 50% progress, while verbal confidence reaches 0.85 at completion. The attributed cause is "path switching" (agents abandon directions mid-run).
- **Mapping.** These are U3 instances at L1 (PrefixGuard), L2 via LLM labels (AgentForesight) and lock-in-style key-step labels (web monitor). None scores against the *three* timestamps; PrefixGuard's lead is normalised by run length, not measured from `t_lock`. (e) None reports the clock monitor. Disentangling's difficulty oracle is the closest thing.
- **What breaks.** Pooled AUROC (task confound). Lead normalised by T_i rewards alarms in long runs. LLM-judge labels (AgentForesight) inherit the judge's position bias.
- **Code.** PrefixGuard: "will be released with the paper" (verified statement). AgentForesight: project page exists, code status unverified. Others not checked.

### G. Metrics for online detectors

#### 3.18 Delay, ARL, AMOC, window scores, margins
- **Papers.** Lorden (1971), Pollak-type CADD and ARL (via the surveys in 3.7). Fawcett, Provost, "Activity monitoring: noticing interesting changes in behavior", KDD 1999, pp. 53-62, DOI 10.1145/312129.312195 (the **AMOC** curve: false-alarm rate against timeliness of the first true alarm; widely used in biosurveillance). Lavin, Ahmad, "Evaluating real-time anomaly detection algorithms: the Numenta Anomaly Benchmark", IEEE ICMLA 2015, arXiv:1510.03336 (scoring that rewards early detection inside anomaly windows and penalises false alarms; window/sigmoid details unverified here). Tatbul, Lee, Zdonik, Alam, Gottschlich, "Precision and recall for time series", NeurIPS 2018, arXiv:1803.03639 (range recall = α·Existence + (1−α)·Overlap, with a cardinality factor, a size function and a positional-bias function δ including **front-end bias**). van den Burg, Williams, "An evaluation of change point detection algorithms", arXiv:2003.06222 (TCPDBench: 37 series × 5 annotators, 14 algorithms; F1 within margin M = 5 with precision against the union of annotations and recall averaged per annotator; segmentation covering; the **"zero" (no-change) baseline beats many methods and no method is significantly better than it in the default setting**; binseg/PELT/BOCPD lead). ECTS harmonic mean of accuracy and earliness (TEASER, §3.11).
- **Mapping to agent labels.**
  - Detection delay T − t_lock, conditional on detection (CADD) and worst-case over runs (WADD).
  - Per-run FAR on successful runs, which replaces ARL for finite runs. On concatenated successful runs, "steps to false alarm" is the empirical ARL.
  - AMOC curve: per-run FAR (x) against median lead to `t_lock` (y). This is the natural summary plot for U3.
  - Front-end-biased range recall for TRAIL error spans and SearchAuditBench tolerance spans (rewards hitting the *start* of a span; see `lit_B_tsad.md` for range metrics generally).
  - TCPDBench multi-annotator F1 for MP-Bench's three annotators' step sets.
  - F1 within margin M for offline CPD, with M = the tolerance span where one exists, otherwise ±1/±2.
  - Always include TCPDBench's lesson: the "zero" predictor (no change) and the last-step predictor must be in every table.
- **Code.** TCPDBench (GitHub, verified via the arXiv comments field). Tatbul metrics, NAB: not checked.

## 4. A monitor protocol (U3)

### 4.1 Data and splits
- **Primary:** FaP failed and passing runs rejoined with step text. 71.4% of runs came from the public CodeTracer release; the rest must be regenerated on Terminal-Bench (replayable). This is the only source of all three timestamps. Until the rejoin is done, run the label-side analyses of §2.3 and the action-code ablation (with the leakage caveat of §2.4).
- **Secondary:** AgentRx τ-bench and Magentic-One (73 public; root = lock-in onset, events = transient changes); Who&When and TraceElephant Magentic-One runs (`k*`, with the ledger flags `is_in_loop` / `is_progress_being_made` as a built-in monitor); TRAIL (spans); PrefixGuard's four benchmarks once released (outcomes only).
- **Splits:** (i) held-out *tasks*, the deployment setting; (ii) **within-task**: FaP has 89 tasks × 21 runs (7 models × 3 scaffolds) with pass rates 19-45%, so every discrimination metric can be computed only over pairs of runs of the same task (as in Disentangling). Calibration set = successful runs of the training tasks.
- **Evaluate at every step** t = 1..m, not on FaP's five t_lock-anchored cuts.

### 4.2 Per-step input streams x_t
1. Symptom indicators from o_t: non-zero exit or exception, empty or null return, output identical to an earlier output, command or query repeated within the last k steps (exact, or embedding cosine > θ), test failure, self-doubt or failure verbalisation, completion claim. These are FaP's `forewarning_types` plus C/V codes.
2. Step type: (agent, tool|status), or FaP's 8 codes (E/P/W/X/V/C/R/O).
3. Step embedding h_t (OAT's representation, causal: no spline).
4. Proxy-LM NLL of u_t given the prefix.
5. Prefix covariates for the hazard: absolute step index, number of failed attempts so far, steps since last verified success.

### 4.3 Statistics (monitors to compare)
| id | statistic | supervision |
|---|---|---|
| M1 | first-symptom rules: alarm at the first step with ≥ j symptoms inside a window of w steps; (j, w) tuned on calibration successes for target FAR | L1 (successes for FAR) |
| M2 | symptom CUSUM: W_t = max(0, W_{t−1} + Σ_k β_k x_{t,k} − μ_0), with β from logistic regression (failed vs successful runs of the same task) | L1 |
| M3 | PPM baseline: single-bucket aggregation encoding (counts of step types/symptoms in the prefix) + XGBoost → p̂_t | L1 |
| M4 | NN-CUSUM: per-step classifier logit (same-task negatives) accumulated by CUSUM | L1 (L2 where `t_lock` exists) |
| M5 | P2 hazard: cumulative hazard 1 − Π(1 − h_s) (Λ ≡ 1) | L1 |
| M6 | Shiryaev filter: hazard + emissions (§3.8) → π_t | L1 |
| M7 | conformal test martingale / e-CUSUM on OAT's e_t | successes only |
| M8 | prompted LLM monitor (FaP prompt, with and without task requirements), run at every step | none (zero-shot) |
| M9 | ledger flags (Magentic-One only): first `is_in_loop = true` or `is_progress_being_made = false` | none |

### 4.4 Baselines that must appear in every table
- **B0 never alarm.** Utility 0; FAR 0.
- **B1 clock.** Alarm when the run reaches absolute step s, with s tuned for FAR. On FaP labels: FAR 0.097 → recall 0.282, median lead −12. FAR 0.42 → recall 0.635, median lead 0 (§2.3).
- **B2 last step.** Alarm at m. Median lead −9.
- **B3 first symptom.** First tool exception / first empty return / first repeated command. On FaP PASS runs "first error event" alone gives per-run FAR ≈ 0.71.
- **B4 difficulty oracle.** p̂ = the task's training-set failure rate, which never reads the run. Its within-task AUROC is 0.5 by construction, and its pooled AUROC shows how much of every other monitor's pooled number is task difficulty.
- **B5 label oracles (ceilings).** Alarm at `t_err` (P(lead > 0) = 0.609, median +1) and at `t_obs` (caught 0.720, P(lead > 0) = 0.204, median −1).

### 4.5 Thresholds and metrics
- **Threshold.** For a target per-run FAR α ∈ {0.05, 0.10, 0.20}, set the threshold to the ⌈(1−α)(n+1)⌉-th order statistic of max_{t≤m_i} statistic_i over n calibration successful runs (split conformal over runs), stratified by length bucket (m ≤ 10, 11-30, > 30). For M6/M4 also report the analytic SR/CUSUM thresholds A = m/α, b = log(m/α) as a check: they are valid only if Λ is correct, so disagreement with the empirical threshold measures LR misspecification.
- **Per failed run** with alarm time T (T = ∞ if none):
  - caught = 1[T ≤ m]
  - lead_lock = t_lock − T (FaP sign convention)
  - lead_obs = t_obs − T (silent runs: report separately)
  - window hit = 1[t_err ≤ T < t_lock], defined only when the fix window is ≥ 1 (60.9% of FaP failures)
  - precursor alarm = 1[T < t_err]
- **Report:**
  1. Recall (caught share) at each α.
  2. P(lead_lock > 0) over *all* failed runs (misses count as no), plus the median and IQR of lead_lock among caught runs.
  3. CADD = mean(T − t_lock | t_lock ≤ T ≤ m).
  4. Window-hit rate.
  5. Precursor-alarm rate.
  6. **AMOC curve** (per-run FAR against median lead_lock).
  7. Within-task AUROC of the run-level max statistic at three anchors: prefix up to t_err, up to t_lock, up to m.
  8. Sepsis-style normalised utility: +1 for T ∈ [t_err, t_lock]; linear decay from +1 at t_lock to 0 at t_obs (or at m if silent); −0.05 for T < t_err; −1 per miss; −0.05 per alarmed successful run.
  9. Alarm-based net cost over c_out/c_in ∈ {2, 5, 10} with eff(k) = 1[k < t_lock] (log-only) or measured eff (replayable).
  10. Temporal stability: number of threshold crossings per run.
- **Leakage checks.**
  - Monitor score with the last k ∈ {1, 2, 3} steps masked (last-step shortcut).
  - Score of successful runs truncated to failed-run lengths (length leak).
  - B4 pooled versus within-task AUROC (difficulty leak).
  - FaP-style per-prefix PR with NOTYET excluded, reported only *next to* the per-run metrics, never alone.

### 4.6 What counts as progress, and the scripts used here
- **Progress against the FaP prompted monitor** (caught 26%, 5% before lock-in, median lead 0, per-prefix FP 1.9%), at matched per-run FAR (≈ 0.10):
  - recall above both the clock (0.28) and the prompted monitor (0.26);
  - P(lead_lock > 0) above the clock (0.068) and the prompted monitor (0.053);
  - within-task AUROC at the t_lock anchor above 0.5.

  A median lead > 0 is a stretch goal: the t_err oracle's median is only +1.
- **Script.** The label-side numbers in §2.3 and §2.4 come from a ~40-line Python pass over `traj_data_v2_all89tasks.json`. Steps:
  1. Split FAIL runs (field `t_commit` present) from PASS runs.
  2. Lead = `t_commit` − alarm step.
  3. Clock FAR = share of PASS runs with m ≥ s.
  4. Segment-boundary alignment = share of runs whose timestamp equals a segment start in `action_segments`.

  The monitor numbers are read from `results/oracle_results_calibrated.json` and `results/oracle_results_calibrated_spec.json` in the FaP repo.

## 5. Ranked recommendations

| # | Method | Benchmark(s) | Target label | Supervision | Expected gain over OAT / position prior | Effort | Risk |
|---|---|---|---|---|---|---|---|
| 1 | Monitor protocol of §4 (per-step evaluation, per-run conformal FAR, AMOC, within-task AUROC, clock/difficulty/label-oracle baselines) | FaP labels now; FaP rejoined; AgentRx; Who&When/TraceElephant (ledger) | `t_lock`, `t_obs`, `t_err` | none (evaluation) | Makes U3 claims falsifiable. The label-side ceilings show median lead > 0 is near-impossible (t_err oracle +1), so recall at matched FAR and P(lead > 0) are the right targets | S | Low. Needs the FaP rejoin for model results |
| 2 | Shiryaev filter = P2 hazard + post-lock emission model (+ transient state) | FaP rejoined, AgentRx, Who&When, TrajErrBench | online π_t → `t_lock`; smoother → `t_lock`/`k*` | L1 (+L1+) | Uses post-change evidence that the hazard-only P2 ignores. Gives online and offline attribution from one model. OAT cannot run online at all (non-causal spline) | M | Medium: identifiability of hazard vs emission at L1; f_1 is a mixture of tail behaviours |
| 3 | Symptom CUSUM (M2) and PPM aggregation + XGBoost (M3) | FaP rejoined, Terminal-Bench/τ2, AgentRx τ-bench | `t_lock` lead, recall at FAR | L1 | Cheap, strong baselines. Expected to beat the clock at matched FAR because accumulation suppresses the 71%-of-successes single-error alarms. Should be reported before any neural monitor | S | Low. Ceiling bounded by silent failures (28%) |
| 4 | Conformal test martingale / e-CUSUM wrapper on OAT scores (M7) | MCP-Atlas (OAT), Who&When, FaP rejoined | per-run alarm; `t_obs`/`t_lock` | successes only | Turns OAT's per-step FPR ≤ α into a per-run guarantee. Fixes under-detection when several steps are flagged. Makes OAT online once the spline is replaced by a causal encoder | S | Medium: step exchangeability fails (use position-Mondrian or run-level calibration) |
| 5 | NN-CUSUM with same-task negatives (M4) | FaP rejoined (21 runs/task), PrefixGuard benchmarks | `t_lock` | L1 / L2 | Learned LLR. Same-task negatives remove the difficulty confound that inflates pooled AUROC (Disentangling) | M | Medium: Itkin's finding that gains come from the per-step score, not accumulation |
| 6 | Alarm-based cost model with eff(k) from rollouts | TrajErrBench τ2, TraceElephant SWE-agent, Terminal-Bench | net cost; eff profile ↔ `t_lock` | L1+ | Connects U3 to P1. A monitor is judged by cost saved, not AUROC. Yields an operational point of no return to compare with annotated `t_lock` | L | Medium-high: rollout cost; closed-loop effects |
| 7 | Offline single-change CPD (AMOC / PELT / kernel) on step scores, penalty learned from tolerance spans (Hocking) | LongRCA, TRAIL, SearchAuditBench, AgentRx | `k*` (±k, CS-Loose), event set F1 | L0 + weak L2 | Label-free segmentation baseline for long traces where position priors are weak (LongRCA root-to-end 48 steps). Expect `t_lock`/`t_obs` hits, late vs `t_err` | M | Medium: phase changes and role switches produce spurious changes |
| 8 | Rollout value series + Bayesian CPD (Forking-Paths style) | replayable sets | operational `t_lock`, largest drop = `t_err` | L1+ | Tests whether annotated `t_lock` equals the point of no return. Also a label generator for training M4/M6 | L | High cost; noisy V̂ with small N |
| 9 | BOCPD with learned covariate hazard / robust β-BOCPD | LongRCA, TRAIL, AgentRx events | multiple events, last change ≈ `t_lock` | L0/L1 | Handles multiple and transient changes natively. Robust variant suppresses single-exception outliers | M | Medium: exchangeability within regimes |
| 10 | ECTS cost-based trigger (Achenchabe) or TEASER-style two-tier reliability gate on top of M3/M6 | FaP rejoined, HORIZON | trigger time vs [t_err, t_lock] | L1 | Principled trigger instead of a fixed threshold. Improves temporal stability | M | Medium: early confidence before `t_err` is mostly task difficulty |
| 11 | Injected-failure-trained change classifier (Li et al. 2024 recipe) | train Who&When Pro / Aegis / CORRECT-Error; test Who&When, TrajErrBench | `k*` | synthetic L2 | Large labelled supply. Tests whether simulated changes transfer | M | High: injection position priors (0.83 / 52% last fifth) transfer as shortcuts |
| 12 | Temporal-MIL precursor scorer (Janakiraman) | Who&When, AgentRx, TrajErrBench | `k*`, root | L1 | Mostly subsumed by P2's noisy-OR. Worth it only as an ablation | S | Last-step shortcut |
| 13 | Critical-slowing-down indicators | LongRCA | `t_lock` lead | L0 | Low. Series too short and the signature is post-lock | S | High (likely null) |

## 6. Open gaps

1. **No dataset has step text and all three timestamps.** FaP is annotation-only, and its `action_segments` leak the timestamps (86-88% boundary alignment). Rejoining FaP with the public CodeTracer trajectories, plus re-running the rest on Terminal-Bench, is the precondition for any U3 model result.
2. **`t_lock` is defined on the realised run.** It means "locked given the agent's *actual* subsequent behaviour", a property of the run rather than the state. The point of no return (rollouts, L1+) is a state property. No dataset has both, so nobody knows whether lock-in labels are reproducible by replay.
3. **The fix window is tiny** (median 1 step, 0 in 39%). At step granularity, "early warning before lock-in" barely exists. Either the step unit is too coarse (Itkin-style token-level monitoring inside the decisive step) or U3 should target "alarm within k steps after `t_lock`" plus cost saved.
4. **No theory for policy-dependent post-change behaviour.** After the error the agent reacts to it (repairs the wrong problem, thrashes, fabricates), so f_1 is a mixture determined by the agent. Classical delay bounds assume a fixed f_1.
5. **Transient vs persistent changes.** Recovered errors (71% of FaP successes; 27% of AgentRx runs before the root) need detectors that wait for persistence. The literature on "epidemic"/transient changes was not surveyed here (gap in this slice).
6. **Lead-time conventions differ:** FaP measures in steps over caught runs only; PrefixGuard normalises by run length and counts misses as 0. A standard (lead_lock in steps over all failed runs, misses = no, plus AMOC) is needed before comparing papers.
7. **Calibration under task shift.** Run-level conformal needs exchangeable tasks. Monitors deployed on new task families (Who&When OOD for OAT) have no guarantee. Weighted conformal under covariate shift was not covered here.
8. **Multi-agent nuisance changes.** Speaker and role switches are distribution changes. CPD on marked or multi-channel sequences conditioned on the agent id is unexplored for this problem.
9. **Closed loop.** Every evaluation above is open-loop. An alarm that triggers an intervention changes the run. Prescriptive-monitoring work (uplift, RL-triggered interventions) is the next literature to read.

## Appendix: verification log (2026-10-30)

Verified on arXiv abstract/HTML pages, publisher/index pages (Project Euclid, OUP, SIAM, PMLR, JMLR, ACM/IEEE listings, PubMed, PhysioNet), or via search results quoting the record: Killick+ 2012; Fryzlewicz 2014; Truong+ 2020 (+ `ruptures`); Harchaoui+ 2008; Arlot+ 2019; Hocking+ 2013 (+ `penaltyLearning`); Truong+ 2019 (existence and DOI only); Li+ 2024; Chang+ 2019; Deldari+ 2021; Adams & MacKay 2007; Wilson+ 2010; Knoblauch+ 2018; Bigelow+ 2024 (method details from the HTML); Page 1954; Shiryaev 1963; Lorden 1971; Moustakides 1986; Veeravalli & Banerjee 2012; Xie+ 2021; Moustakides & Basioti 2019; Gong/Lee/Cheng/Xie 2022-24; Itkin 2026; Volkhonskiy+ 2017; Vovk+ 2021; Shin+ 2022; Shekhar & Ramdas 2023; Xing+ 2012; Lv+ 2019; Schäfer & Leser 2020; Hartvigsen+ 2019; Achenchabe+ 2021; Renault+ 2025 (+ `ml_edm`); Janakiraman 2018; Reyna+ 2020 (utility constants from the PhysioNet page); Tomašev+ 2019; Scheffer+ 2009; Dakos+ 2012; Bury+ 2021; Teinemaa+ 2019 (results read from the PDF); Tax+ 2017; Verenich+ 2018; Teinemaa+ 2018 alarm (cost table and findings read from the PDF); Fahrenkrog-Petersen+ 2022; Teinemaa+ 2018 stability; Fawcett & Provost 1999; Lavin & Ahmad 2015; Tatbul+ 2018 (existence/overlap/front-end bias from the paper text); van den Burg & Williams 2020 (metrics and "zero" result from the HTML); PrefixGuard (lead definition, FAR calibration and baselines from the HTML); AgentForesight; key-step web monitor; Disentangling; Last Step Matters.

Unverified details, as flagged inline: the exact Arlot+ penalty constants; Truong+ 2019 method; TS-CP2 score definition; Vovk+ 2021 CUSUM/SR construction and venue; Volkhonskiy+ and Shin+ venues; TEASER internals beyond the two-tier design and the aeon harmonic-mean scorer; EARLIEST and Janakiraman DOIs; Dakos window/trend-test details; NAB scoring internals; Verenich journal version; the Bigelow+ venue; code availability marked "not checked".
