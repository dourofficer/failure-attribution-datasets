# Lit B: time-series anomaly detection (TSAD), read as the home field of OAT

- Search date: 2026-10-30. This is slice B of the time-series survey. The shared brief is `notes/lit_timeseries/00_context_brief.md`.
- Method: WebSearch (standard and extended) to find candidates. The arXiv export API to confirm id, title, authors, date and comment (venue) for every arXiv id. WebFetch on arXiv HTML pages, and local text extraction of arXiv PDFs, for mechanisms, equations and numbers. Crossref and proceedings pages for papers without arXiv ids.
- **VERIFIED (text)**: id or DOI confirmed, and the quoted mechanism, equation or number was read in the paper text (PDF/HTML).
- **VERIFIED (abs)**: id or DOI confirmed and the abstract read. Any detail beyond the abstract is marked *(from memory, not re-read)*.
- **UNVERIFIED**: not confirmed. Nothing in that state is cited as fact.
- Numbers from arXiv HTML pages came through an automatic summarizer. Re-check them before they go into the report.
- Numbers marked **[computed]** were computed for this note on `data/who_and_when` (184 failures, `history` length = T, `mistake_step` 0-based).

---

## Scope and verdict

- **OAT is a textbook semi-supervised ("novelty") TSAD method.** It trains on normal series only, reconstructs every point, scores the residual, and thresholds on held-out normals. Its TSAD ancestors are EncDec-AD and LSTM-VAE (reconstruction) and LSTM-NDT (prediction residual plus a data-driven threshold). Only the Neural CDE is unusual.
- **The TSAD field spent 2020-2024 finding that its own protocol rewarded noise.**
  - Point-adjust lets a random score reach state-of-the-art F1 (Kim et al. 2022).
  - Most benchmark anomalies can be solved with one line of code, or sit at the end of the series (Wu & Keogh).
  - 1-NN distance, PCA error and the L2 norm match deep detectors (Sarfraz et al. 2024; TSB-AD 2024).
- **Agent-attribution evaluation repeats each of these errors.**
  - "Hit rate" is point-adjust at the trajectory level.
  - Top-3 F1 on single-label data equals hit/2, with a ceiling of 0.5.
  - The early/late error-position prior plays the role of Wu & Keogh's run-to-failure bias.
- **No unsupervised family detects a fluent but wrong step.** This covers one-class, reconstruction, forecasting, contrastive and discord methods. They all score atypicality against normal data, and reasoning errors look typical. The one direct agent study (Dubey 2026, 2,823 episodes) catches loops and tool cascades but ranks organic fabrications at or below chance (AUROC 0.31-0.42).
- **The families that can learn reasoning errors are the weakly supervised ones**, because their label is the outcome, not typicality:
  - MIL from video-level labels (Sultani 2018, RTFM, MIST, VadCLIP);
  - weak segment labels (WETAS, NRdetector);
  - Deep SAD / PU with a few labelled anomalies.
- **That is exactly L1 supervision**, with step localisation built in. Max/noisy-OR MIL is the same object as the report's hazard model. It must be protected against the last-step shortcut and the task-difficulty shortcut.
- **The most valuable thing to transfer is the evaluation protocol, not a model.** That means analytic random baselines, k-matched position priors, step-level affiliation precision/recall, VUS over tolerance buffers, PA%K for error sets, and task-disjoint splits.
- **The cheapest model transfer** is the Sarfraz/Kim floor baselines run on OAT's own embeddings. Next is paired success/failure MIL, using the replayable data engines (tau2, ALFWorld/WebShop, SWE/Terminal-Bench).

---

## OAT as a TSAD method

### 2.1 Where OAT sits in the TSAD taxonomy

| TSAD axis | OAT's choice | Closest TSAD methods (this file) |
|---|---|---|
| Supervision | Semi-supervised / novelty: train on normal (successful) series only | Deep SVDD, EncDec-AD, LSTM-VAE, LSTM-NDT, OmniAnomaly, USAD, DeepLog |
| Score | Reconstruction residual of the observed point, given a path that passes through that point | EncDec-AD, LSTM-VAE, USAD, TranAD, TimesNet-AD |
| Temporal model | Continuous-time controlled DE; spline control path; irregular time u = t/T | none in mainstream TSAD; only the NCDE line |
| Input | 64-d PCA of LLM hidden states per step: a 64-channel multivariate series | multivariate TSAD (SMD/SWaT-style channels) |
| Decoding | Top-k per series; conformal (1-α) quantile of normal-step scores | "r% of validation flagged" (Anomaly Transformer); POT (OmniAnomaly, TranAD); nonparametric dynamic threshold (LSTM-NDT) |
| Granularity | Point anomaly in a very short series (MCP-Atlas about 7 steps; Who&When AG at most 10) | TSAD usually has range anomalies in series of 10^3-10^6 points |
| Evaluation | Per-trajectory P/R/F1/hit rate, macro-averaged; AUROC/AUPRC "on the rank of the anomaly scores" | point-F1, F1-PA, range P/R, affiliation, VUS |

Three consequences follow.

**1. OAT has the identity-shortcut problem that TSAD reconstruction models fight.**
- The spline passes through h_t, so the CDE state at u_t has already integrated the step it is asked to reconstruct.
- An unconstrained model can copy the input and leave a small residual everywhere.
- The gate q(dX/du) is a bottleneck that blocks atypical increments, which keeps the reconstruction on the "success flow".
- This is the TSAD lesson "anomalies are reconstructed too well". Anomaly Transformer (association discrepancy), TranAD (focus-score self-conditioning plus adversarial training) and USAD (adversarial second decoder) each attack it.
- So the gate's +0.172 OOD AUROC is evidence for "restrict reconstruction capacity on atypical inputs". It is not evidence for continuous-time dynamics.

**2. Window-based TSAD assumptions break on agent traces.**
- Anomaly Transformer, DCdetector, TimesNet and TranAD (default window 10) assume many windows inside a long series. On Who&When AG a single window covers the whole trajectory.
- TimesNet's periodicity has no analogue in agent traces, except loops.
- Discord methods need subsequence length m << T.
- These methods only fit as designed on LongRCA (median 145 steps), TraceElephant SWE runs and MemTrace (497 operations).

**3. Agent benchmarks have many short series, each with about one anomaly.**
- The TSAD analogue is the UCR anomaly archive (one anomaly per series) and TSB-AD's per-series scoring.
- Scoring per series and then averaging brings the per-series random-baseline problem (§2.3 a-c).

### 2.2 Standard TSAD baselines OAT did not run

Per WebFetch of arXiv:2607.12747v1 HTML (2026-10-30), OAT's baselines are:
- GPT-4o and GPT-5 "all-at-once" prompting;
- **Random-Step** and **First-Step**, each picking one step per trajectory.

Its ablations are Neural ODE, the RNN predictor, gate on/off, pooling, layer and proxy LLM. No one-class, density, nearest-neighbour or k-matched position baseline appears in the experiments.

Missing baselines, all cheap on the same embeddings:

1. **Kim et al. (2022) Cases 1-3**: a random score; the input itself as the score (‖h_t‖, or ‖h_t − μ_succ‖); and an *untrained* (randomly initialised) model of the same architecture. An untrained gated CDE is the most informative single control for OAT.
2. **Sarfraz et al. (2024) simple baselines**: L2 norm; 1-NN distance to the bank of success steps; PCA reconstruction error fitted on success steps; a 1-layer linear model.
3. **Mahalanobis and Δ-Mahalanobis**, the memoryless baselines in Dubey 2026. **Isolation Forest / OC-SVM**, already planned in `notes/alternatives.md`.
4. **Next-step residual with top-g decoding** (LSTM-NDT, DeepLog). OAT's RNN comparison exists only as a figure.
5. **Matrix-profile AB-join** of failed steps against success steps (at m = 1 this is the same as 1-NN). A left-discord (DAMP) for the online setting.
6. **MASC** (arXiv:2510.14319, Oct 2025). It is unsupervised next-step-embedding reconstruction with a prototype prior, and it reports step-level AUROC on Who&When: the same problem on the same OOD dataset. It is not compared.
7. **Off-the-shelf multivariate TSAD** through the TSB-AD or TimeSeAD libraries (USAD, TranAD, Anomaly Transformer, DCdetector, OmniAnomaly). Expected value is low (§3, E2), but it is the first thing a TSAD reviewer will ask for.
8. **k-matched position priors.** The repo has computed them for Who&When: first-3 hit 0.359 and random-3 hit 0.286, against OAT top-3 0.451. OAT's own First-Step/Random-Step pick one step, so they are not k-matched to top-3.

### 2.3 Evaluation pitfalls that apply to OAT

**(a) "Hit rate" is trajectory-level point-adjust.**
- OAT defines hit = 1[Ŷ ∩ Y ≠ ∅], averaged over trajectories. One correct flag credits the whole label set, exactly as point-adjust (PA) credits a whole anomaly segment for one detection inside it.
- Random baseline for k flags, m gold steps and T steps:
  `E[hit] = 1 − C(T−m, k) / C(T, k) ≈ k·m / T`.
- On Who&When (m = 1, k = 3) this is **0.286 [computed]**. OAT's 0.451 must be read against 0.286, not against 0.
- Like F1-PA, which tends to 1 as segments get longer (Kim et al., Eq. 6-7), hit rate grows with k·m/T. It inflates for large label sets (MP-Bench union, TRAIL) and for short trajectories.

**(b) Top-k F1 on single-label data is hit rate with a different name.**
- With |Y| = 1 and k = 3, per-trajectory precision is 0 or 1/3 and recall is 0 or 1. So F1 = 0.5·hit, with a **ceiling of 0.5**.
- OAT's Who&When top-3 F1 of 0.23 is about 0.451 × 0.5. Random-3 has expected F1 **0.143 [computed]**.
- Either report F1 against both the ceiling and the random value, or drop F1 for single-label datasets.

**(c) Per-trajectory macro averaging with a fixed k.**
- Who&When Algorithm-Generated trajectories have T ≤ 10 (mean 8.7). Hand-Crafted ones have median 32.5 and maximum 130 **[computed]**.
- Top-3 therefore flags at least 30% of an AG trajectory and about 10% of an HC one. The average is dominated by AG, where random is strong.
- Stratify by T, or use k = ⌈ρT⌉. The repo's subset split (AG first-3 hit 0.516 vs HC 0.017) shows how much this matters.

**(d) What the conformal guarantee actually covers.**
- The (1−α) quantile of success-step scores bounds P(score > δ) ≤ α only for a new step exchangeable with the calibration steps, i.e. a step from a new success of the same distribution.
- It does not cover:
  1. correct steps inside failed runs, which sit in a different context;
  2. OOD data (Who&When), where the guarantee is void;
  3. the per-trajectory false-alarm count: α = 0.2 means about 2 false flags per 10 correct steps.
- Steps within one trajectory are dependent. With an 80/20 split of 103 successes (about 21 calibration trajectories), the effective calibration size is about 21, not about 140.
- Fix: calibrate on the per-trajectory maximum, `δ_traj = Q_{1−α}( max_t e_t over calibration trajectories )`. This is the "healthy null" threshold Dubey 2026 uses for CUSUM. It controls the probability that a whole success run is falsely flagged.

**(e) The position confound is Wu & Keogh's run-to-failure bias.**
- u = t/T and z(0) = g2(h_Q) make the expected residual a function of relative position. Position-only AUROC is 0.602, the same as ungated OAT (repo).
- Wu & Keogh: "a naïve algorithm that simply labels the last point as an anomaly has an excellent chance of being correct."
- In injected sets (CORRECT-Error relative position 0.95, Who&When Pro 0.83) the last step plays that role. In Who&When the first steps do.
- The best constant relative position (q = 0.23) puts k* within ±1 for **40.8%** of Who&When failures **[computed]**. This q was tuned in-sample, so treat it as an upper bound for the prior.

**(f) Threshold and k tuned on test.**
- Kim et al. note that TSAD papers report best-threshold F1 ("All thresholds were obtained from those that yielded the best score").
- OAT sweeps k ∈ {1, 3, 5} (App. G.1). k should be fixed on validation data and kept the same across datasets.

**(g) Task leakage.**
- Le & Zhang (ICSE 2022): random rather than chronological training splits leak and inflate log-anomaly accuracy.
- Zavrak (arXiv:2605.11053): random splits inflate tool-call attack AUROC by up to 26 pp relative to task-disjoint splits.
- Whether OAT's MCP-Atlas successes (train) and failures (test) share tasks is **UNVERIFIED**. Check it.

**(h) Label noise and tolerance.**
- Kim et al.'s t-SNE analysis (some labelled anomalies look normal) and Wu & Keogh's "mislabeled ground truth" have a direct agent analogue: exact-step annotator agreement of 40-91%.
- Exact-step metrics punish near-misses that annotators themselves would make. §4.3-4.4 fix this.

---
## Methods

**What each family can catch.**
- Surface errors: exceptions, loops, empty returns, malformed calls, failure verbalisation.
- Reasoning errors: fluent but wrong summaries, unfounded conclusions, wrong plans. These are 58% of TrajErrBench, 59% of Who&When Pro and 70% of TRAIL labels.

| Family | Signal it uses | Catches surface errors | Catches reasoning errors |
|---|---|---|---|
| One-class hypersphere (A) | distance from the success manifold, context-free | yes | no (a wrong summary embeds like a right one) |
| Reconstruction (B) | residual given the series | yes | no; partial hook in Anomaly Transformer's "ignored context" (B6) |
| Forecasting / next-step (C) | surprise given the prefix | yes (strongest on loops and cascades) | no: fabrications at or below chance in Dubey 2026 |
| Contrastive (D) | representation inconsistency between views | yes | only if trained with injected reasoning faults (D4) |
| Distance / discord (E) | nearest-neighbour distance to successes | yes | only against same-task successes from near-deterministic environments (E1) |
| Weak labels / MIL (F) | outcome or segment labels | yes | **yes, in principle**: the label carries correctness |
| Discrete events / logs (G) | step-type order and counts | structural errors only | no |
| Agent-trace AD 2025-26 (H) | mixes of the above | mostly | only the label-trained ones |

Each entry below gives: citation and verification status; mechanism; the mapping (a)-(f) from the brief's §7; supervision level; what breaks; code.

### A. One-class hypersphere family

#### A1. Deep SVDD

**Citation.** Ruff et al., *Deep One-Class Classification*, ICML 2018, PMLR 80 (proceedings.mlr.press/v80/ruff18a). VERIFIED (abs). The objective was confirmed through Deep SAD's Eq. 7, which reduces to Deep SVDD when no labels are given.

**Mechanism.**
- Objective: `min_W (1/n) Σ_i ‖φ(x_i; W) − c‖² + (λ/2) Σ_l ‖W_l‖²_F`.
- Score: `s(x) = ‖φ(x) − c‖²`.
- c is fixed after an initial forward pass, and the network has no bias terms, to avoid hypersphere collapse *(from memory, not re-read)*.

**Mapping.**
- (a) x_t = OAT's 64-d step embedding, optionally concatenated with one-hots for agent id and step type. Context-free.
- (b) Trained on steps of successful runs. L1-selected, the same as OAT.
- (c) Output: per-step distance.
- (d) Targets: k* / E on Who&When and AgentHallu (443 failed with step labels, plus 250 clean runs that can serve as normal training data). Metrics: per-trajectory AUROC and top-k hit, each against its analytic random value (§4.1).
- (e) Must beat position-only AUROC 0.60 and the 1-NN baseline (E2).
- (f) Breaks: it is context-free, so a normal step in the wrong place is invisible. Successes are contaminated (Failure-as-a-Process PASS runs carry 2.3 recovered errors each).

**Supervision.** L1-selected, then discarded (the OAT setting).

**Code.** Not checked.

#### A2. THOC

**Citation.** Shen, Li, Kwok, *Timeseries Anomaly Detection using Temporal Hierarchical One-Class Network*, NeurIPS 2020 (proceedings hash 97e401a0…). VERIFIED (abs).

**Mechanism.**
- A dilated RNN with skip connections gives features at several time scales.
- Hierarchical clustering yields several hyperspheres per scale.
- The objective is "Multiscale Vector Data Description": soft-assigned distance to the centres, summed over scales.
- The centres are pushed to be orthogonal, and a temporal self-supervision task is added.
- The anomaly score is the MVDD distance at the final step *(from memory)*.
- Anomaly Transformer's text lists THOC (Shen et al. 2020) among the methods evaluated with point-adjust.

**Mapping.**
- (a) Step embeddings.
- (b) Successes (L1-selected).
- (c) Per-step score against behaviour prototypes. The scales map to step / sub-task / phase. The centres play the role of MASC's prototype (C3) and of Automata-from-traces FSM states (H4).
- (d) Fits only where trajectories are long: LongRCA (root step; median 145 steps), TraceElephant SWE subset.
- (e) Position prior.
- (f) Breaks: T ≈ 10 gives no multi-scale structure.

**Catches.** Surface and structural errors only.

**Code.** Not checked.

#### A3. COUTA (calibrated one-class)

**Citation.** Xu et al., *Calibrated One-class Classification for Unsupervised Time Series Anomaly Detection*, IEEE TKDE. arXiv:2207.12201. VERIFIED (abs).

**Mechanism.**
- One-class training on windows, with two calibrations.
- Uncertainty-modelling calibration penalises uncertain predictions, to restrain irregular samples when the training data is contaminated.
- "Native anomaly" calibration creates dummy anomalies by perturbation and trains the model to discriminate them.

**Mapping.** This is the right repair for "successes are not clean".
- (a) h_t.
- (b) Training data: success runs (contaminated), plus perturbation-made anomalies: step deletion, duplicated tool call, observation replaced by an empty return, swapped agent label. Supervision: L1-selected plus synthetic.
- (c) Per-step score.
- (d) Test on TRAIL span-F1 and AgentRx set-F1. Failure-as-a-Process has no step text, so use its PASS-run statistics only to set the contamination rate.
- (e) Must beat ungated and gated OAT.
- (f) Breaks: the native anomalies are surface perturbations, so this teaches surface detection.

**Code.** Not checked.

### B. Reconstruction family

#### B1. EncDec-AD

**Citation.** Malhotra et al., ICML 2016 Anomaly Detection Workshop. arXiv:1607.00148. VERIFIED (abs).

**Mechanism.**
- An LSTM encoder-decoder learns to reconstruct normal sequences.
- The per-point reconstruction error is the anomaly score.
- The abstract reports it works on series as short as 30 points.
- Errors are scored with a Gaussian/Mahalanobis model fitted on normal validation errors *(from memory)*.

**Mapping.** OAT with the CDE removed: a sequence autoencoder over success-step embeddings, scored by per-step error.
- This is the direct test of whether continuous time matters at all.
- (d) Who&When and MCP-Atlas-like data. (e) Position prior.
- (f) Breaks: the whole-sequence bottleneck spreads error across steps, which weakens localisation on long runs. Encoding the whole sequence is as non-causal as OAT's spline.

**Catches.** Surface errors.

**Code.** Not checked.

#### B2. LSTM-VAE (multimodal execution monitor)

**Citation.** Park, Hoshi, Kemp, IEEE RA-L 2018 (DOI 10.1109/LRA.2018.2801475). arXiv:1711.00614. VERIFIED (abs + DOI).

**Mechanism.**
- An LSTM-VAE fuses heterogeneous sensor streams and reconstructs their *expected distribution*.
- The score is reconstruction-based (likelihood of the observation).
- The threshold is **state-based**: it varies with the latent state.
- Reported AUC 0.871 on 1,555 robot-assisted feeding executions covering 12 anomaly types.

**Mapping.** Robot executions are the closest physical analogue to agent episodes.
- (a) [step embedding; observation features: return length, exception flag, empty-return flag, repeated-query flag, latency].
- (b) Successes. (c) Per-step NLL.
- The state-based threshold is a phase-conditioned threshold. It directly fixes OAT's single conformal δ, which mixes early and late steps.
- (d) TraceElephant (observation level A) k*; AgentErrorBench critical step ±1.
- NLL instead of reconstruction error is OAT's own stated future work (likelihood via CNFs).
- (f) Breaks: VAE likelihoods across heterogeneous step types are poorly calibrated, and 103 successes are too few.

**Catches.** Surface errors.

**Code.** Not checked.

#### B3. OmniAnomaly

**Citation.** Su et al., KDD 2019 (DOI 10.1145/3292500.3330672). VERIFIED (DOI). The mechanism is confirmed through TranAD's related-work text: "stochastic recurrent neural network (similar to an LSTM-VAE) and a planar normalizing flow to generate reconstruction probabilities … adjusted Peak Over Threshold (POT)".

**Mechanism.**
- A stochastic RNN with latent variables, a planar normalising flow, and a reconstruction-probability score.
- POT (extreme-value theory) threshold.
- It is one of the PA-using papers Anomaly Transformer cites.

**Mapping.** Same as B2. POT needs many scores in the tail, so it only works for the long-trajectory datasets.

**Code.** Not checked.

#### B4. USAD

**Citation.** Audibert et al., KDD 2020 (DOI 10.1145/3394486.3403392). VERIFIED (DOI). The mechanism is confirmed through TranAD's text: "an autoencoder with two decoders with an adversarial game-style training framework".

**Mechanism.**
- Score `α‖W − AE1(W)‖² + β‖W − AE2(AE1(W))‖²` *(from memory)*.
- The adversarial second decoder amplifies the error on inputs unlike the training data. That is the job OAT's gate does.

**Mapping.**
- A fast ablation of "gate vs adversarial amplification" on the same 64-d series.
- α/β is a sensitivity dial.

**Catches.** Surface errors.

**Code.** Not checked.

#### B5. TranAD

**Citation.** Tuli, Casale, Jennings, VLDB 2022. arXiv:2201.07284. VERIFIED (text).

**Mechanism.**
- Two-phase transformer.
- Phase 1 reconstruction error becomes a "focus score" that conditions phase 2.
- Adversarial training and MAML.
- Score `s = ½‖O1 − Ŵ‖² + ½‖Ô2 − Ŵ‖²` (Eq. 13).
- "At test time, we only consider the data until the current timestamp", so it is causal.
- POT thresholds. Default window 10.

**Mapping.**
- (a) h_t plus telemetry.
- (b) Success windows.
- (c) Causal per-step score, usable as an online monitor (report task U3).
- (d) t_lock and lead time on AgentRx or Terminal-Bench re-runs.
- (f) Breaks: every window after the error is anomalous (errors propagate), so the onset must be decoded as a change point. The window equals a whole short trajectory.

**Catches.** Surface errors.

**Code.** Not checked.

#### B6. Anomaly Transformer

**Citation.** Xu, Wu, Wang, Long, ICLR 2022. arXiv:2110.02642. VERIFIED (text).

**Mechanism.**
- *Prior association*: a learnable Gaussian kernel over relative distance.
- *Series association*: the self-attention weights.
- `AssDis` = symmetric KL between the two, averaged over layers, trained with a minimax strategy.
- Score (Eq. 6): `AnomalyScore(X) = Softmax(−AssDis(P,S;X)) ⊙ [‖X_i − X̂_i‖²]`.
- Rationale: an anomaly cannot build associations to the whole series, so its attention concentrates on adjacent points.
- The threshold flags r% of validation data.
- Evaluation uses PA: "if a time point in a certain successive abnormal segment is detected, all anomalies in this abnormal segment are viewed to be correctly detected."

**Mapping.** The adjacent-concentration idea is the one reconstruction-family hook for a reasoning-error class: **a step that ignores its evidence**.
- (a) Two options: the step-embedding series, or, more directly, the *agent LLM's own attention mass* from step t's tokens onto the query span, onto earlier observations, and onto the immediately preceding step.
- (b) Fit the success distribution of the "local vs global attention" ratio per step type.
- (c) Per-step discrepancy.
- (d) TraceElephant (full LLM I/O) and MemTrace (memory reads) k*.
- (e) Position prior. The Gaussian prior has edge effects at t = 1, which correlate with Who&When's early errors.
- (f) Breaks: needs white-box access to the agent model, or a proxy re-encoding. The original numbers are PA-inflated.

**Catches.** Mostly surface. Possibly "ignored evidence" (untested).

**Code.** Not checked.

#### B7. TimesNet (reconstruction-based AD)

**Citation.** Wu et al., ICLR 2023. arXiv:2210.02186. VERIFIED (abs + text).

**Mechanism.**
- FFT picks the dominant periods.
- The 1-D series is reshaped into 2-D (intra-period × inter-period) and processed with 2-D inception blocks.
- For AD, "we only change the base models for reconstruction and use the classical reconstruction error as the shared anomaly criterion". Preprocessing follows Anomaly Transformer (non-overlapping windows).
- Code: github.com/thuml/TimesNet.

**Mapping.** Agent traces have no period, except loops: a repeated tool-call cycle is a periodic segment. Cycle detection (H2) does that job directly.

**Value.** Low.

**Catches.** Loops only.

#### B8. Diffusion-based TSAD: ImDiffusion and Pintilie et al.

**Citation.**
- Chen et al., *ImDiffusion*, VLDB 2024, arXiv:2307.00754. VERIFIED (abs).
- Pintilie, Manolache, Brad, ICDM 2023 AI4TS workshop, arXiv:2311.01452. VERIFIED (abs).

**Mechanism.**
- ImDiffusion masks part of the series and imputes it with a conditional diffusion model. The imputation error at masked points, taken from the step-by-step denoised outputs, is the score. In production at Microsoft it gave +11.4% F1 over the legacy detector. Code: github.com/17000cyh/IMDiffusion.
- Pintilie et al. test two diffusion models, and extend PA%K to **ROCK-AUC**, which is agnostic to both the threshold and K.

**Mapping.**
- Masked-step imputation = "reconstruct h_t from τ minus {t}" (alternatives.md item 4). It is bidirectional, so offline only.
- Because the next observation can reveal the error, the score at t_err can be lifted by the symptom at t_obs. That helps attribution offline and is useless for monitoring.
- 103 successes are far too few to train a diffusion model.
- The evaluation contribution (ROCK-AUC) is worth more than the model.

**Catches.** Surface errors.

### C. Forecasting / next-step residual

#### C1. LSTM-NDT

**Citation.** Hundman et al., KDD 2018. arXiv:1802.04431. VERIFIED (abs).

**Mechanism.**
- An LSTM predicts the next value, and the error is smoothed (EWMA).
- **Nonparametric dynamic threshold**: `ε = μ(e_s) + z·σ(e_s)`, with z chosen per series to maximise the relative drop in mean and std of the errors below ε, penalised by the number of flagged points and sequences. False-positive pruning follows *(details from memory, not re-read)*.
- SMAP and MSL telemetry.

**Mapping.**
- OAT's RNN ablation is this model without the threshold.
- The per-series threshold needs **no calibration set**. That makes it a principled alternative to conformal on OOD data such as Who&When, where success calibration is not exchangeable.
- (a) h_t. (b) Successes. (c) Residual `e_t = ‖h_t − f(h_{<t})‖`.
- (d) Who&When exact / ±1; AgentErrorBench critical step; AgentRx k_lock as a monitor.
- (e) Position prior and OAT's Fig. 5 RNN.
- (f) **Cold start**: the first steps have no context, so their residuals are high. That falls exactly on Who&When's early-error prior and inflates the apparent skill. Normalise residuals by step index on the successes.

**Catches.** Surface errors.

**Code.** Not checked.

#### C2. ESN ensemble + CUSUM one-class monitor (agent-native)

**Citation.** Dubey, *Real-Time Detection and Repair of LLM Agent Failures*, arXiv:2608.02464 (Aug 2026). VERIFIED (abs + HTML summary).

**Features per channel.**
- e: a 32-d char-3-gram hash of the step output.
- u: token-surprisal aggregates.
- m: action one-hot, log latency, output length, error flag.
- v3/v4 add behavioural and content-grounding features, up to 60 dimensions.

**Mechanism.**
- Each channel has a fixed random reservoir. A ridge readout is fitted on *healthy runs only* to predict the next step's features.
- q_t is the normalised squared one-step error, averaged over the reservoirs.
- CUSUM: `S_t = max(0, S_{t−1} + z(q_t) − κ)`. The alarm fires when the maximum over channels of S_t exceeds θ, where θ is the (1−β) quantile of the maximum score over healthy validation episodes.

**Results.**
- 2,823 episodes: 0.71 of failures detected at a 5% false-alarm budget; AUROC 0.872.
- The advantage over Mahalanobis grows with the post-onset horizon: +0.09 at ≤3 steps, +0.40 at ≥9 steps.
- **No cross-deployment transfer**: AUROC 0.527 cold vs 0.885 recalibrated.
- **Organic fabrications: within-organic AUROC 0.31-0.42**, and content corruption is detected poorly.
- A deterministic verifier (recompute stated totals from tool results, check required calls) catches 60% at 0/63 false positives.
- Code: github.com/sunnydubey1111/agent-trajectory-sentinel.

**Mapping.**
- (a) Cheap telemetry; no LLM needed.
- (b) L1-selected healthy runs.
- (c) Per-step surprise plus a cumulative alarm (change point).
- (d) t_obs / t_lock with lead time, and detection at a fixed per-run false-alarm budget. Use Terminal-Bench re-runs (Failure-as-a-Process protocol) and AgentRx k_lock. Onsets in the paper come from injections.
- (e) Mahalanobis and the position prior.
- (f) Breaks: needs a per-deployment healthy null, and is blind to fabrication.

**Verdict.** The strongest existing evidence that one-class step monitors see *surface* failures and not reasoning failures.

#### C3. MASC (next-execution reconstruction with a prototype)

**Citation.** Shen et al., arXiv:2510.14319 (Oct 2025). VERIFIED (abs + HTML summary).

**Mechanism.**
- Prediction: `x̂_t = f_θ(LLM_frozen(q̃, h̃_1, …, h̃_{t−1}))`. Step text is embedded with all-MiniLM-L6-v2; the frozen backbones are Qwen-2.5-7B and LLaMA-3.1-8B.
- A prototype p is learned by attention over the predicted embeddings.
- Loss: `L = (1/T) Σ ‖x̂_t − x_t‖² + λ (1/T) Σ (1 − cos(x̂_t, p))`.
- Score: `s(t) = α‖x̂_t − x_t‖² + β(1 − cos(x̂_t, p))`, flagged above a predefined δ.
- The paper says it is trained "using only normal trajectories". It does not explain where normal trajectories come from in Who&When, which releases failures only (**provenance unverified**).

**Results.**
- Who&When 20/80 split (HC 10/45, Auto 25/100): AUC-ROC 64.5-77.8 across backbones and with/without ground truth.
- The AgentDebug baseline (74.31, Auto with GT) beats MASC's best in that cell (69.62).
- No position baseline.
- Code: anonymous.4open.science/r/MASC-7194.

**Mapping.**
- The direct competitor to OAT in the same setting (step AUROC on Who&When).
- Read its AUROC against position-only 0.60.
- The prototype term is a fix for cold start (C1-f).

**Catches.** Surface errors.

### D. Contrastive / self-supervised scoring

#### D1. CPC and LNT

**Citation.**
- van den Oord, Li, Vinyals, *Contrastive Predictive Coding*, arXiv:1807.03748. VERIFIED (abs).
- Schneider et al., *Local Neural Transformations*, arXiv:2202.03944. VERIFIED (abs).

**Mechanism.**
- CPC: an autoregressive context c_t predicts future latents through InfoNCE: `L = −E log[ exp(z_{t+k}ᵀ W_k c_t) / Σ_j exp(z_jᵀ W_k c_t) ]`.
- LNT learns local transformations of CPC-style latents and outputs **a score per time step**. Tested on LibriSpeech and cyber-physical systems.

**Mapping.**
- An InfoNCE density-ratio score: `s_t = −log softmax_j(h_jᵀ W c_{t−1})` over the true h_t and negatives drawn from *other success runs at similar relative position*.
- A ranking score normalises away the size of the residual, which removes part of the cold-start / position confound.
- (b) Successes. (d) Who&When, TraceElephant.
- (f) Breaks: if negatives come from other tasks, task identity is the easiest cue. The score then measures "off-task" drift, not correctness.

**Catches.** Surface and topical drift.

**Code.** Not checked.

#### D2. TS2Vec

**Citation.** Yue et al., AAAI 2022. arXiv:2106.10466. VERIFIED (text).

**Mechanism.**
- Hierarchical contrastive learning over augmented context views.
- Score (Eq. 4): `α_t = ‖r_t^u − r_t^m‖₁`, where r_t^u is the last-timestamp representation of the unmasked input and r_t^m the same with x_t masked.
- Plus drift normalisation.
- Code: github.com/yuezhihan/ts2vec.

**Mapping.**
- A causal leave-one-step-out influence score: how much step t changes the representation of τ_{≤t}.
- (b) Successes. (c) Per-step score.
- (f) Breaks: any informative step (a new tool result) scores high. Informativeness is not error, so normalise α by its success distribution per step type.

**Catches.** Surface errors.

#### D3. DCdetector

**Citation.** Yang et al., KDD 2023. arXiv:2306.10347. VERIFIED (text).

**Mechanism.**
- Patch-wise and in-patch attention views; no reconstruction; pure contrastive training.
- Score (Eq. 11): `Σ KL(P, sg(N)) + KL(N, sg(P))`.
- Also reports affiliation and VUS, but "employ[s] the commonly-used adjustment technique" (PA).
- Code: github.com/DAMO-DI-ML/KDD2023-DCdetector.

**Mapping.**
- Two-view discrepancy: view 1 = step encoded with local context (previous step only); view 2 = step encoded with global context (query plus all evidence).
- A step that makes sense locally but not globally is the shape of a "locally fluent, globally wrong" reasoning error.
- Untested. The patch sizes assume long series.

#### D4. NCAD

**Citation.** Carmona, Aubet, Flunkert, Gasthaus, IJCAI 2022 (DOI 10.24963/ijcai.2022/394). arXiv:2107.07702. VERIFIED (text).

**Mechanism.**
- Each window is split into a *context window* and a *suspect window*, and both are embedded with a TCN.
- The anomaly score is the distance between the embedding of the context and the embedding of context plus suspect (a "contextual hypersphere").
- Trained with injected synthetic anomalies (contextual outlier exposure, point outliers) and any available labels. It scales from unsupervised to semi-supervised.

**Mapping.** The best structural fit to step attribution among the contrastive methods.
- Score: `d(φ(τ_{<t}), φ(τ_{≤t}))`.
- (b) Trained on successes plus injected faults as outlier exposure: the Aegis injector, TracerTraj counterfactual injections, Who&When Pro. Supervision: L1 + synthetic L2.
- (d) Test on natural Who&When and TraceElephant: exact / ±k / VUS.
- (e) Position prior, plus a last-step baseline on injected data.
- (f) Breaks: the injector's register leaks (fa_ideas "register-leak probe"), and injections skew late.

**Catches.** Reasoning errors only as far as the injections contain them (Who&When Pro: 59% reasoning). This is the most plausible route among the unsupervised-leaning families.

### E. Distance, discord and simple baselines

#### E1. Matrix profile, discords, DAMP

**Citation.**
- Yeh et al., *Matrix Profile I*, ICDM 2016 (DOI 10.1109/ICDM.2016.0179). VERIFIED (DOI).
- Lu et al., *Matrix Profile XXIV / DAMP*, KDD 2022 (DOI 10.1145/3534678.3539271). VERIFIED (DOI; "exact left-discords" on streams confirmed via search summary).
- Yeh, *MMPAD on TSB-AD*, arXiv:2604.02445. VERIFIED (abs); code github.com/mcyeh/mmpad_tsb.

**Mechanism.**
- `MP_i = min_{j : |i−j| > excl} d(T_{i,m}, T_{j,m})`, with z-normalised Euclidean distance between length-m subsequences. The top discord is `argmax_i MP_i`.
- The AB-join takes nearest neighbours of A's subsequences in B.
- DAMP's left-discord uses only past neighbours, so it is online and causal.
- MMPAD adds kNN retrieval for repeated anomalies and moving-average post-processing.

**Mapping.**
- AB-join with A = a failed run and B = the bank of success runs, ideally **successes of the same task** (tau2, ALFWorld/WebShop and SWE data engines yield these for free).
- m = 1 reduces to 1-NN (E2); m = 2-3 scores short action patterns.
- (d) TrajErrBench (tau2) critical step; AgentErrorBench (ALFWorld/WebShop) critical step ±1.
- (e) Position prior.
- (f) Breaks: needs same-task successes to mean anything. Embedding distance is not error.

**Catches.** Surface errors. Some *wrong-plan* errors in near-deterministic environments, where all successful runs of a task look alike.

#### E2. "Simple baselines beat SOTA" studies, used as a baseline suite

**Citation.**
- Sarfraz et al., *Position: Quo Vadis, Unsupervised TSAD?*, ICML 2024, arXiv:2405.02678. VERIFIED (text). Code github.com/ssarfraz/QuoVadisTAD.
- Audibert et al., *Do Deep Neural Networks Contribute to Multivariate TSAD?*, Pattern Recognition 132 (2022), arXiv:2204.01637. VERIFIED (abs).
- Liu & Paparrizos, *The Elephant in the Room* (TSB-AD), NeurIPS 2024 Datasets & Benchmarks. VERIFIED (proceedings abstract). Code TheDatumOrg/TSB-AD.

**What they found.**
- Sarfraz:
  - Baselines: sensor-range deviation, L2 norm, 1-NN distance to training data, PCA reconstruction error, 1-layer MLP, single MLPMixer block, single Transformer block.
  - Metrics: F1, F1-PA and F1_T (Tatbul range-based P/R, bias-corrected as in TimeSeAD).
  - A random detector (p = 0.5 per point) is reported to show F1-PA inflation.
  - Finding: SOTA deep detectors "effectively learn linear mappings".
- Audibert: 16 conventional, ML and DL methods on 5 datasets; no family outperforms the others.
- TSB-AD: 1,070 series, 40 datasets, 40 algorithms; VUS-PR is the most reliable measure; simpler and statistical methods often beat neural ones; neural methods do well on multivariate series and foundation models on point anomalies.

**Mapping: the floor suite to run next to OAT on its own embeddings.** All are fit on the same success steps.
- `s^{NN}_t = min_{h ∈ H_succ} ‖h_t − h‖`
- `s^{PCA}_t = ‖(I − U_k U_kᵀ)(h_t − μ)‖²`
- `s^{L2}_t = ‖h_t − μ_succ‖`
- linear AR residual `‖h_t − A h_{t−1} − b‖`
- Kim's untrained-model and input-as-score cases.

Expectation (not tested): within a few AUROC points of ungated OAT. If so, the CDE is not the source of the signal.

### F. Weak, semi-supervised and trajectory-level labels (the L1 families)

#### F1. Deep SAD

**Citation.** Ruff et al., ICLR 2020. arXiv:1906.02694. VERIFIED (text, Eq. 7).

**Mechanism.**
- `min_W (1/(n+m)) Σ_{i≤n} ‖φ(x_i) − c‖² + (η/(n+m)) Σ_{j≤m} (‖φ(x̃_j) − c‖²)^{ỹ_j} + (λ/2) Σ ‖W_l‖²_F`.
- ỹ = +1 for a labelled normal and −1 for a labelled anomaly; the inverse distance pushes anomalies away from c.
- With m = 0 it reduces to Deep SVDD.

**Mapping.** OAT plus a handful of labelled error steps.
- (a) h_t.
- (b) Unlabelled = steps of failed and successful runs (they really are 82-99% correct at the step level). Labelled = 25-200 annotated error steps (fa_ideas D2 active labelling), TracerTraj train-split steps, or Who&When Pro injections.
- (c) Per-step score.
- (d) Who&When, TraceElephant (k*); MP-Bench, AgentRx (E).
- (e) Position prior and OAT.
- (f) Breaks: labels from injected sets carry the register shortcut, and labelled decisive steps are a biased sample of all errors.

**Supervision.** L1 + small L2.

**Catches.** Reasoning errors, as far as labels exist: this is the one-class variant that can absorb reasoning-error supervision.

**Code.** Not checked.

#### F2. Outlier Exposure (OE)

**Citation.** Hendrycks, Mazeika, Dietterich, ICLR 2019. arXiv:1812.04606. VERIFIED (abs). Code github.com/hendrycks/outlier-exposure.

**Mechanism.**
- Train the detector with an auxiliary set of outliers: `L_in + λ E_{x∼D_out} L_OE(f(x))` *(form from memory)*.
- This generalises to unseen anomaly types, and also fixes generative models giving outliers *higher* likelihood.

**Mapping.**
- Auxiliary outliers = labelled or injected error steps from *other* benchmarks, tested leave-one-dataset-out.
- Do **not** use all steps of failed runs as outliers: 82-99% of them are correct.
- The likelihood failure mode is a warning for OAT's planned CNF variant: a flow trained on successes can rate a fluent wrong step as *more* likely than a correct one.

#### F3. Latent Outlier Exposure (LOE)

**Citation.** Qiu et al., ICML 2022. arXiv:2202.08088. VERIFIED (abs).

**Mechanism.**
- Jointly infer binary latent labels (normal or anomalous) for the unlabelled training data while training.
- Two losses share the parameters, one for normal and one for anomalous data.
- Block-coordinate updates: the most anomalous fraction α of training points gets the anomalous loss (hard or soft) *(selection rule from memory)*.

**Mapping.**
- Train a one-class step model on successes that contain recovered errors.
- Set α from Failure-as-a-Process PASS annotations: 2.3 events in 22.8 steps, about 10%.
- Also usable on L0 pools with unknown outcomes.

**Catches.** No change: it is still atypicality-based. It mainly reduces false alarms on recovered errors.

#### F4. Deep positive-unlabelled anomaly detection

**Citation.** Takahashi et al., *Neurocomputing*, arXiv:2405.18929. VERIFIED (abs). Code github.com/takahashihiroshi/pusvdd.

**Mechanism.**
- PU-autoencoder and PU-DeepSVDD, trained from unlabelled (contaminated) data plus labelled anomalies, with **no labelled normals**.
- The normal-data loss is estimated from the unlabelled and labelled-anomaly losses, using the class prior.
- Comes with a generalisation-error bound.

**Mapping.** This is the TSAD form of the repo's PU idea (fa_ideas E3), and it fits the agent setting exactly.
- Labelled anomalies = annotated error steps (any dataset's k* or E).
- Unlabelled = every other step, including steps after k* that may also be wrong.
- Class prior π from the brief's step-sparsity table (0.6% LongRCA … 18% MP-Bench).
- (d) MP-Bench / AgentRx / TRAIL sets with affiliation P/R (§4.3).
- (f) Breaks: π misspecified across datasets; label-selection bias (decisive vs all errors).

**Supervision.** L2 sparse positives + unlabelled.

**Catches.** Reasoning errors, if labelled.

#### F5. Sultani et al.: MIL ranking from video-level labels

**Citation.** Sultani, Chen, Shah, CVPR 2018 (DOI 10.1109/CVPR.2018.00678). arXiv:1801.04264. VERIFIED (text, Eq. 5).

**Mechanism.**
- Each video is a bag of segments. Anomalous videos are positive bags; normal videos are negative bags.
- Hinge ranking loss: `l(B_a, B_n) = max(0, 1 − max_{i∈B_a} f(V_a^i) + max_{i∈B_n} f(V_n^i))`.
- Plus a temporal-smoothness term `λ1 Σ_i (f(V_a^i) − f(V_a^{i+1}))²` and a sparsity term `λ2 Σ_i f(V_a^i)`, because "anomaly often occurs only for a short time".
- UCF-Crime: 1,900 untrimmed videos, 13 anomaly types. Trained on video-level labels, evaluated at frame level.

**Mapping.** This is L1 supervision exactly.
- (a) Step embeddings (OAT's, or a frozen proxy LM) plus observation features.
- (b) Positive bags = failed runs; negative bags = **successful runs of the same tasks**. Sources:
  - AgentHallu: 443 failed + 250 clean;
  - HORIZON: 2,498 failed + 1,284 judge-labelled successes;
  - the data engines: tau2, ALFWorld/WebShop, SWE / Terminal-Bench.
- (c) Per-step score. Decode as argmax (k*), first threshold crossing (t_err), or top-k (E).
- (d) Targets and metrics:
  - AgentHallu hallucination step (exact / ±1, VUS);
  - HORIZON step labels (294 web runs);
  - TrajErrBench tau2 critical step;
  - AgentErrorBench critical step;
  - AgentRx tau-bench rows (set-F1 plus affiliation).
- (e) The right control is the same MIL loss with a **position-only scorer** g(t/T, T, step type). Then OAT.
- (f) What breaks:
  1. **Last-step shortcut**: the final answer reveals the outcome, so the max over the bag picks it. Mask the final step(s) or the answer span.
  2. **Task difficulty**: hard tasks have atypical steps everywhere. Pair bags by task.
  3. **Recovered errors in negative bags**: FaP successes contain errors, so the negative-bag max is often a real error and the hinge pushes errors down. Use LOE-style relabelling, or score "unrecovered" errors only.
  4. **Multiple causes**: the max selects one step; see RTFM's top-k.
- Sparsity matches step-level sparsity. Smoothness is wrong for point errors but right for the post-lock-in regime.
- Max-pooling MIL is the noisy-OR / hazard limit of the report's Proposal 2. The hazard model is "first-passage MIL", which picks the earliest unrecovered step rather than the most anomalous one.

**Catches.** Reasoning errors, if the representation encodes them. The risk is that the easiest discriminator is the symptom (t_obs).

**Code.** Not checked.

#### F6. RTFM

**Citation.** Tian et al., ICCV 2021. arXiv:2101.10030. VERIFIED (abs + text). Code github.com/tianyu0207/RTFM.

**Mechanism.**
- Keep the **top-k snippet feature magnitudes** per video, and enforce a large margin between the mean top-k magnitude of abnormal and normal videos, jointly with MIL classification.
- Dilated convolutions plus self-attention for long- and short-range dependency.
- The paper proves the top-k mean separates abnormal from normal videos better than the max when there is more than one abnormal snippet.

**Mapping.**
- Top-k with k = the expected number of error steps per failed run, a dataset prior: MP-Bench about 4.2, AgentRx 4.6 events, Who&When 1.
- This suits the set-labelled datasets (MP-Bench, AgentRx, TRAIL).
- (f) Breaks: feature magnitude tracks step length and type (tool dumps are long). Normalise per step type.

**Catches.** Same as F5.

#### F7. MIST, VadCLIP and successors

**Citation.**
- Feng et al., *MIST*, CVPR 2021, arXiv:2104.01633. VERIFIED (abs).
- Wu et al., *VadCLIP*, AAAI 2024, arXiv:2308.11681. VERIFIED (abs). Code github.com/nwpu-zxr/VadCLIP.
- Also verified: Zhou et al., *UR-DMU*, AAAI 2023, arXiv:2302.05160; Chen et al., *MGFN*, arXiv:2211.15098; Zhong et al., *GCN label-noise cleaner*, CVPR 2019, arXiv:1903.07256.

**Mechanism.**
- MIST: a multiple-instance pseudo-label generator (sparse continuous sampling) produces clip-level pseudo-labels, which self-train a task-specific encoder. Frame AUC 94.83% on ShanghaiTech.
- VadCLIP: frozen CLIP with two branches, a coarse binary classifier and a fine-grained branch aligning snippets to text prompts of anomaly classes. AUC 88.02% on UCF-Crime, AP 84.51% on XD-Violence.

**Mapping.**
- **MIST**: a self-training loop. MIL step scores give pseudo step labels, which fine-tune a small step encoder, and the loop repeats. Trajectory labels bootstrap step labels.
- **VadCLIP**: taxonomy-conditioned step scoring. Align step embeddings with text descriptions of failure modes (MAST 14, AgentRx 9, TRAIL 21), and train with *trajectory-level mode labels*:
  - MAST-Data has 1,642 traces with mode labels but no steps;
  - Aegis has (agent, mode) labels.
  - The output is (step, mode), recovered from trajectory-level labels.
- (f) Breaks: MAST-Data mode labels come from an LLM judge, and mode prompts can import the judge's priors.

#### F8. Deep temporal MIL for incident precursors

**Citation.** Janakiraman, KDD 2018 (DOI 10.1145/3219819.3219871). arXiv:1710.04749. VERIFIED (abs + DOI).

**Mechanism.**
- MIL combined with a deep RNN on multivariate flight data.
- Flights are labelled as incident or not, with no time-step annotation.
- The model learns per-time-step **precursor** scores whose aggregate predicts the flight label, and the precursors explain the incident.

**Mapping.** The closest pre-LLM analogue of agent failure attribution: run outcome (L1) → per-step precursor.
- The precursor is meant to *precede* the incident, i.e. t_err rather than t_obs.
- Test exactly that: on AgentRx (k_lock plus root cause) and TrajErrBench, check whether the MIL peak lands at the annotated root/decisive step or at the visible symptom.
- Failure-as-a-Process timestamps would be the ideal test, but it releases no step text.

#### F9. WETAS (weakly supervised temporal anomaly segmentation)

**Citation.** Lee et al., ICCV 2021. arXiv:2108.06816. VERIFIED (text).

**Mechanism.**
- Global score `s* = σ(wᵀ GlobalPool(h_1..h_T))`, trained with BCE on instance (series-level) labels.
- Local scores give a *sequential pseudo-label*: an ordered pattern of normal and anomalous segments.
- **DTW alignment** between the input and the pseudo-label gives a variable-length segmentation. An alignment loss feeds the mask back as extra supervision.

**Mapping.**
- It outputs a segment, not a point. With outcome labels it learns the "failure regime" [k_lock, T]; the segment onset estimates lock-in.
- (d) AgentRx k_lock; Failure-as-a-Process t_lock (needs text). Metrics: onset error ±k, and range recall with front-end bias (§4.5).
- Complements the hazard model: it estimates the onset of the regime rather than a per-step hazard.

**Supervision.** L1.

#### F10. NRdetector (noisy segment labels → point detection)

**Citation.** Wang et al., KDD 2025. arXiv:2501.11959. VERIFIED (abs).

**Mechanism.**
- Train from segment-level labels (noisy) plus unlabelled data.
- Confidence-based sample selection, robust segment-level learning, and data-centric point-level detection.
- The loss encourages smoothness of consecutive points and separability between segments with different labels.
- Evaluated on 11 metrics.

**Mapping.**
- SearchAuditBench tolerance spans [k_s, k_e], annotator-disagreement ranges, and Failure-as-a-Process [t_err, t_lock] intervals are all noisy segment labels.
- Train a step-level detector from spans, and evaluate exact-step accuracy.

**Supervision.** L2 at span level.

#### F11. TRACES (prefix risk from weak trajectory labels; agent-native)

**Citation.** Li et al., EMNLP 2026, arXiv:2605.27690. VERIFIED (abs + HTML summary). Code github.com/lab-flair/TRACES.

**Mechanism.**
- Observer-LLM hidden states at agent action steps (Llama-3.1-8B layer 30, or Qwen3-4B layer 32).
- A "mechanism bank" of K = 8 centres with rank-8 subspaces gives affinities s_{t,k}.
- A GRU runs over [x_t; Δx_t].
- Loss: `L = λ_final·BCE(ℓ_T) + λ_pre·L_pre + λ_rank·L_rank`.
  - Safe trajectories: every prefix gets target 0.
  - Unsafe trajectories: prefixes get target 1, weighted by `w_t = [((t/T − ρ)/(1 − ρ))]_+^γ`.
  - The rank hinge makes later prefixes riskier than earlier ones.

**Results.** On ATBench, F1 84.5-86.3 and EAUPC (mean AUROC over prefix ratios 0.2-0.8) up to 82.2. **No step-level evaluation.**

**Mapping.** An L1 prefix-risk monitor, i.e. report task U3.
- The warm-up weight **hard-codes "risk rises late"**, which is a position prior.
- The rank loss imposes monotone risk, so recovery is impossible.
- Both conflict with Who&When's early errors and with Failure-as-a-Process's recovered errors.
- The hazard model learns *where* risk rises instead of imposing it. Use TRACES as the baseline that the hazard model must beat on lead time vs t_lock.

### G. Discrete events and logs

#### G1. DeepLog

**Citation.** Du et al., CCS 2017 (DOI 10.1145/3133956.3134015). VERIFIED (DOI). The mechanism is confirmed through LogBERT's and Le & Zhang's descriptions.

**Mechanism.**
- An LSTM over log keys (parsed templates) predicts the next key from the preceding window.
- An event is anomalous if the observed key is not among the **top-g** predicted candidates.
- A sequence is anomalous if any event is.

**Mapping.**
- (a) x_t = discrete step type: (agent id, tool name or action category, outcome flag). Use the same abstraction as Automata-from-traces: tool name, then [ACTION] tag, then first command token, then role:content_type.
- (b) Success traces. (c) Per-step flag.
- (d) Targets:
  - TRAIL spans in structural categories (e.g. tool selection, resource abuse);
  - MAST FM-1.3 (step repetition) and FM-1.5 (unaware of termination);
  - Who&When exact step for the structural subset only.
- (e) Position prior.
- (f) Breaks: blind to *content* errors at a normal step type, which is most agent errors.

**Catches.** Structural errors; no reasoning errors.

#### G2. LogAnomaly

**Citation.** Meng et al., IJCAI 2019 (DOI 10.24963/ijcai.2019/658). VERIFIED (DOI + title).

**Mechanism.** Semantic template vectors (template2vec), with both *sequential* anomalies (order) and *quantitative* anomalies (count-vector invariants).

**Mapping.**
- Quantitative invariants mined from successes are cheap agent checks, for example: "search was called but nothing was read", "patch written with no test run", "number of tool calls per sub-task".
- TraceAegis (H3) mines similar rules.

**Catches.** Surface errors.

#### G3. LogBERT

**Citation.** Guo, Yuan, Wu, IJCNN 2021. arXiv:2103.04475. VERIFIED (text).

**Mechanism.**
- Masked log-key prediction plus *volume of hypersphere minimisation* (Deep SVDD on a DIST token).
- A key is anomalous if it is not in the top-g candidates at a masked position.
- A sequence is anomalous if more than r keys are anomalous; g and r are tuned on validation.

**Mapping.**
- A bidirectional masked step-type model (alternatives.md item 4) over discrete step tokens.
- The r-of-g rule is a sequence-level decision built from step-level flags. That is the same gap as agent papers flagging steps but reporting a per-trajectory hit.

#### G4. PLELog

**Citation.** Yang et al., ICSE 2021 (DOI 10.1109/ICSE43902.2021.00130). VERIFIED (DOI). The description is from Le & Zhang.

**Mechanism.**
- Probabilistic label estimation for unlabelled sequences, given known normals.
- An attention-based GRU then classifies normal vs abnormal.
- Clustering is used for the label estimate *(detail from memory)*.

**Mapping.** Successes (known normal) plus unlabelled runs give probabilistic trajectory labels. This is the sequence-level counterpart of F3/F4, and is useful at L0 to make pseudo-outcomes when the verifier is missing.

#### G5. Critiques of log-AD evaluation

**Citation.**
- Le & Zhang, *Log-based Anomaly Detection with Deep Learning: How Far Are We?*, ICSE 2022, arXiv:2202.04301. VERIFIED (text).
- Landauer, Skopik, Wurzenberger, *A Critical Review of Common Log Data Sets…*, FSE 2024 (PACMSE), arXiv:2309.02854. VERIFIED (text).
- Background survey: Landauer et al., *Deep Learning for Anomaly Detection in Log Data: A Survey*, MLWA vol. 12 (2023), arXiv:2207.03820. VERIFIED (abs).

**Findings.**
- Le & Zhang: 5 models (DeepLog, LogAnomaly, PLELog, LogRobust, CNN) on HDFS, BGL, Spirit and Thunderbird.
  - Random training-data selection "could cause the data leakage problem and unreasonably high detection accuracy", unlike chronological selection.
  - Grouping (session vs fixed/sliding windows) changes results, and short sequences hurt.
  - Under heavy imbalance, P/R/F are "not comprehensive enough".
  - Small label noise hurts, supervised models more than semi-supervised ones.
  - Models differ in early-detection ability.
- Landauer et al.:
  - "most anomalies are not directly related to sequential manifestations". New event types and deviating sequence lengths or counts detect them.
  - BGL event labels "can be inferred from the event message itself", and a sequence is labelled anomalous if it contains at least one anomalous event.
  - Shuffled HDFS sub-sequences come from concurrency, not anomalies.
  - Some anomalous sequences are identical to normal ones.

**Transfer to agent attribution.**
1. **Session vs event labels.** Landauer's "anomalous if it contains ≥1 anomalous event" is the gap between trajectory outcome and step labels. TRAIL (not selected by outcome) and MAST (per-trace labels) live on this boundary.
2. **"New event type" baseline.** An exception-string / empty-return / failure-verbalisation detector must be run as a baseline. It is what OAT App. H says OAT fires on.
3. **Chronological split** corresponds to a task-disjoint or time-disjoint split.
4. **Early detection** corresponds to lead time before t_lock.

### H. Anomaly detection on LLM-agent traces and reasoning chains, 2025-2026 (other than OAT)

#### H1. Trajectory Guard

**Citation.** Advani, AAAI 2026 TrustAgent workshop, arXiv:2601.00516. VERIFIED (abs + HTML summary).

**Mechanism.**
- A Siamese recurrent autoencoder.
- `L = L_triplet(task anchor; own trajectory as positive; in-batch trajectories as negatives) + 0.5·L_recon` (GRU decoder MSE).
- Trained on 5,752 "good" trajectories (Galileo, AgentAlign). Synthetic GPT-5 perturbations are used for validation and test only.
- **Trajectory-level only.**
- Unsupervised baselines on mean-pooled embeddings: VAE F1 0.69, OC-SVM 0.55, Isolation Forest 0.53.
- On Who&When it reports **recall 0.92 on an all-anomalous set**, where an always-anomalous detector scores 1.0.
- Code not released.

**Mapping.** An L1-style detection head with no attribution. Its Who&When protocol is an example of an uninformative evaluation.

#### H2. Silent-failure detection and cycle detection (IBM)

**Citation.**
- Pathak et al., arXiv:2511.04032. VERIFIED (abs).
- George et al., arXiv:2511.10650. VERIFIED (abs).

**Findings.**
- Two curated datasets (4,275 and 894 trajectories) from two multi-agent apps. XGBoost (supervised) reaches up to 98% accuracy and SVDD (semi-supervised) up to 96%. Trajectory-level.
- Cycle detection combines temporal call-stack analysis (explicit loops) with semantic similarity (redundant content). On 1,575 trajectories: F1 0.72 (P 0.62, R 0.86), against structural-only 0.08 and semantic-only 0.28.

**Mapping.**
- Loops are a MAST/TRAIL category, and a cycle is a *span*, so score it with range-based P/R (§4.5).
- A cheap surface channel to add to any detector.

#### H3. TraceAegis

**Citation.** Liu et al., arXiv:2510.11203. VERIFIED (abs).

**Mechanism.**
- Abstracts stable execution units from normal traces hierarchically and turns them into behavioural rules.
- Detects violations of execution order and of semantic consistency.
- TraceAegis-Bench: 2 scenarios, each with 1,300 benign and 300 abnormal behaviours. Security-oriented.

**Mapping.** Rule mining from successes, the agent counterpart of LogAnomaly invariants (G2).

**Catches.** Structural errors.

#### H4. Automata from agent traces

**Citation.** Cho et al., arXiv:2608.23670. VERIFIED (abs + HTML summary).

**Mechanism.**
- A prefix tree over activity sequences, with states merged by last activity and rare transitions filtered, gives a 7-43-state FSM.
- 12 public datasets, including Who&When, tau2-bench (three domains), WebArena, SWE-agent and ATBench.
- Failure prediction uses per-state features plus cross-entropy anomaly features (trace CE, max surprise, minimum transition probability) and gradient-boosted trees. AUROC up to 0.94 (tau2 telecom).
- **No step-level localisation is evaluated.** No code found.

**Mapping.**
- The discrete-state OAT (alternatives.md item 3). The per-step score is `−log P(type_t | state_{t−1})` on an FSM built from successes.
- Evaluate that score against Who&When k* and TrajErrBench (tau2).

**Catches.** Structural errors only.

#### H5. TrajAD

**Citation.** Liu et al., arXiv:2602.06443. VERIFIED (abs).

**Mechanism.** A supervised generative verifier that outputs a verdict and the index of the first error. Trained on TrajBench, which is synthesised by perturb-and-complete.

**Mapping.** Not anomaly detection in the TSAD sense: it is supervised on synthetic L2 labels. Same register-leak caveat as other injected sets.

#### H6. Graph-based MAS anomaly detectors (security)

**Citation.**
- SentinelAgent, arXiv:2505.24201. VERIFIED (abs).
- G-Safeguard, arXiv:2502.11127. VERIFIED (abs). Code github.com/wslong20/G-safeguard.
- BlindGuard, ACL 2026, arXiv:2508.08127. VERIFIED (abs). Code github.com/MR9812/BlindGuard.

**Mechanism.**
- G-Safeguard: a GNN detects anomalies on the utterance graph, followed by a topological intervention.
- BlindGuard: unsupervised. A hierarchical agent encoder, plus a corruption-guided detector (directional noise injection and contrastive learning) trained *only on normal agent behaviour*.

**Mapping.**
- Node-level anomaly detection on the agent graph is a natural "who" detector at L1-selected supervision.
- It targets injected adversarial agents, which are surface-anomalous by design.
- Transfer to natural "who" (Who&When, where the WebSurfer/Orchestrator role prior dominates) is untested.

#### H7. Hidden-state trajectories for reasoning chains

**Citation.**
- Wang et al., *Chain-of-Embedding (CoE)*, ICLR 2025, arXiv:2410.13640. VERIFIED (abs).
- Alvarez & Baheri, *Where Does Reasoning Break?* (transport geometry), arXiv:2605.13772. VERIFIED (abs).

**Mechanism.**
- CoE: the progressive hidden states across layers are a latent thinking path, and features of that path differ between correct and incorrect answers. Label-free and training-free.
- Transport geometry: the per-step transport cost of hidden-state transitions; the first error is a localised excursion. A label-conditioned teacher (contrastive PCA) is distilled into a BiLSTM student. **The student collapses under distribution shift.**

**Mapping.**
- These are the only trajectory-dynamics methods aimed at reasoning errors.
- OAT mean-pools the last layer and so discards the across-layer path CoE uses.
- The student's collapse under shift mirrors OAT's in-domain vs OOD instability.
- These are not TSAD proper, but they suggest a better x_t: layer-path features per step.

#### H8. Evaluation evidence from agent monitoring

**Citation.**
- Zavrak, arXiv:2605.11053. VERIFIED (abs).
- Rahman et al., *Traverse*, arXiv:2609.17930. VERIFIED (abs).

**Findings.**
- Zavrak: random splits inflate tool-call attack AUROC by up to 26 pp relative to task-disjoint splits. Metadata-only features plateau around AUROC 0.64; content embeddings exceed 0.89.
- Traverse: 2,518 trajectories with 6,967 mistakes in 78 failure types. The strongest of six frontier judges "correctly identifies the first mistake in fewer than a third of runs". Agents rarely self-correct after their first mistake.

**Mapping.** Task-disjoint splits are mandatory, and first-mistake localisation remains hard even for judges, so baselines need to be honest.

---
## Evaluation protocol transfer

### 4.0 The TSAD evaluation papers this section uses

| Paper | Id | Status | Key content used here |
|---|---|---|---|
| Kim et al., *Towards a Rigorous Evaluation of TSAD*, AAAI 2022 | arXiv:2109.05257, DOI 10.1609/aaai.v36i7.20680 | VERIFIED (text) | See the paragraph below this table. |
| Wu & Keogh, *Current TSAD Benchmarks are Flawed…*, IEEE TKDE (+ ICDE 2022 abstract) | arXiv:2009.13807 | VERIFIED (text) | Four flaws: triviality ("solved with a single line of standard library MATLAB code"), unrealistic anomaly density, mislabeled ground truth, run-to-failure bias. Proposes the UCR anomaly archive. |
| Tatbul et al., *Precision and Recall for Time Series*, NeurIPS 2018 | arXiv:1803.03639 | VERIFIED (text) | Range recall `R_T(R_i,P) = α·Existence + (1−α)·Card(R_i,P)·Σ_j ω(R_i, R_i∩P_j, δ)`; range precision has α = 0. δ is a positional bias: flat, front-end (`δ(i,L) = L−i+1`), back-end ("useful … where responses are irreversible"), or middle. |
| Huet, Navarro, Rossi, *Local Evaluation of TSAD Algorithms* (affiliation), KDD 2022 | arXiv:2206.13167, DOI 10.1145/3534678.3539339 | VERIFIED (text) | Zones of affiliation I_j (time points closest to gold event j). Survival functions of the distance of a uniform random prediction in I_j. P/R "quantifying how much a given set of results is better than a random baseline prediction". Robust to adversarial strategies. |
| Paparrizos et al., *Volume Under the Surface*, PVLDB 15 (2022) | DOI 10.14778/3551793.3551830 | VERIFIED (DOI) | VUS-ROC / VUS-PR. |
| Boniol et al., *VUS: Effective and Efficient Accuracy Measures for TSAD* | arXiv:2502.13318 | VERIFIED (text) | Continuous buffer label `label_ℓ(i) = (1 − abs(s−i)/ℓ)^{1/2}` on `[s − ℓ/2, s)` (if pred_i = 1); 1 inside the anomaly; mirrored after the end. Range-AUC over thresholds, then VUS over buffer lengths ℓ. Recall carries Tatbul's existence ratio. |
| Liu & Paparrizos, *TSB-AD*, NeurIPS 2024 D&B | proceedings c3f3c690… | VERIFIED (abs) | VUS-PR is the most reliable measure; simple methods are competitive. |
| Ghorbani, Reinders, Tax, *PATE*, KDD 2024 | arXiv:2405.12096 | VERIFIED (text) | Pre-buffer e (early detection) and post-buffer d (delayed detection) around each anomaly; proximity-weighted TP/FP/FN, with onset-weighted FN. `PATE = mean over (e,d) in E×D of AUC-PR_{e,d}`. |
| Garg et al., *An Evaluation of Anomaly Detection and Diagnosis in MTS*, IEEE TNNLS | arXiv:2109.11428 | VERIFIED (abs) | Existing metrics "cannot distinguish between a good detector and trivial detectors, such as a random or an all-positive detector". Composite F-score Fc1. Scoring function matters more than model. |
| Sørbø & Ruocco, *Navigating the Metric Maze* | arXiv:2303.01272 | VERIFIED (abs) | Taxonomy of 20 TSAD metrics, compared on case studies. |
| Wagner et al., *TimeSeAD*, TMLR 2023 | openreview iMmsCI0JsS | VERIFIED (search: TMLR listing) | 28 deep methods × 21 datasets. A recall-consistent, bias-corrected range metric (Sarfraz's F1_T uses it). |
| Pintilie et al., ROCK-AUC (B8) | arXiv:2311.01452 | VERIFIED (abs) | PA%K made independent of both threshold and K. |

**Kim et al. (2022) in detail.**
- PA (Eq. 4) marks a whole segment S_m as detected if any score in S_m exceeds δ.
- For uniform random scores, F1_PA → 1 as segments get long (Eq. 6-7). Benchmark anomaly ratio γ is 0-0.2, and segment lengths are 100-5,000.
- An *untrained* LSTM encoder-decoder, and the input itself used as the score, are competitive without PA.
- **PA%K** applies PA to a segment only if at least K% of it is detected. Report the area under F1_PA%K over K from 0 to 100. In their example this gives 0.88 for a trained encoder-decoder vs 0.41 for a random score.

### 4.1 Rule 1: report every metric next to its analytic random value and k-matched position priors

Notation:
- N failed trajectories, trajectory n has T_n steps.
- Gold set Y_n with m_n = |Y_n|; m = 1 for k*.
- The detector returns step scores e_{n,t}, or a predicted set Ŷ_n with |Ŷ_n| = k.

Random references (closed form or hypergeometric):
```
exact step:        R_exact = (1/N) Σ_n 1/T_n
±w window:         R_w     = (1/N) Σ_n |[k*_n − w, k*_n + w] ∩ [1, T_n]| / T_n
top-k hit:         R_hit   = (1/N) Σ_n [1 − C(T_n − m_n, k) / C(T_n, k)]
set-F1 (|Ŷ|=k):    R_F1    = (1/N) Σ_n Σ_j Hyp(j; T_n, m_n, k) · 2j / (k + m_n)
                   (j = |Ŷ ∩ Y| is hypergeometric)
per-traj AUROC:    0.5
nDCG@5:            Monte-Carlo over random permutations, using the benchmark's own gains
```

Position priors to report at the same k:
- first-k; last-k (the run-to-failure analogue);
- a constant relative position q, **chosen on other datasets** (leave-one-dataset-out), never in-sample;
- a learned position-only scorer g(t/T, t, T, step type, agent role), trained on other datasets.

Then report a **skill score** `S = (M − M_ref) / (M_max − M_ref)` with `M_ref = max(random, best position prior)` and `M_max` the metric's ceiling. For top-3 F1 on single-label data, `M_max = 0.5`.

Who&When values **[computed]**:

| Quantity | Value |
|---|---|
| R_exact | 0.095 |
| R_{±1} | 0.263 |
| R_hit (k = 3) | 0.286 |
| R_F1 (k = 3) | 0.143 |
| top-3 F1 ceiling | 0.5 |
| first-3 hit | 0.359 |
| in-sample best constant position, ±1 accuracy | 0.408 |

- OAT's top-3 hit 0.451 gives `S = (0.451 − 0.359) / (1 − 0.359) ≈ 0.14`.
- With N = 184, the binomial 95% CI on a hit rate of about 0.45 is about ±0.07. The OAT vs first-3 gap is at the edge of significance without a paired test.
- MP-Bench already publishes a random nDCG@5 (0.128 hand-crafted, 0.315 automatic; `notes/mp_bench.md`), but no position prior. Add first-5 and position-only nDCG@5.

### 4.2 Rule 2: replace "hit rate" (trajectory-level PA) with PA%K over error sets

For set-labelled data (AgentRx all failure events, TRAIL spans, MP-Bench steps with ≥ v votes):
```
credit_K(n) = 1[ |Ŷ_n ∩ Y_n| / |Y_n| ≥ K ]
PA%K-adjusted prediction:  Ŷ'_n = Ŷ_n ∪ Y_n  if credit_K(n),  else Ŷ_n
F1_PA%K(K) from Ŷ' ;   AUC_PA%K = ∫_0^1 F1_PA%K(K) dK
```
- K → 0⁺ recovers hit rate. K = 1 requires full recall of the set.
- Do the same for agent attribution ("who") when several agents are blamed.
- For MP-Bench, weight Y by consensus rate. That is a weighted PA%K whose threshold is on the summed consensus mass recovered.

### 4.3 Rule 3: distance-aware credit — affiliation precision/recall for steps

**Single gold step k* in a trajectory of length T.**
- Let U be uniform on {1..T}.
- Precision credit of a predicted step p: `F̄(d) = Pr(|U − k*| ≥ d)` with `d = |p − k*|`.
- This is 1 for an exact hit, decreases with distance, and its random expectation is about 0.5.
- Precision = mean of `F̄(|p − k*|)` over p ∈ Ŷ.
- Recall = `F̄(min_{p∈Ŷ} |p − k*|)`.

**Gold set E = {e_1, …, e_J}.**
- Partition {1..T} into affiliation zones `I_j = { t : |t − e_j| < |t − e_i| for all i ≠ j }`. Break ties toward the earlier gold step.
- Compute F̄_j for U uniform on I_j:
```
P_prec_j = mean_{p ∈ Ŷ ∩ I_j}  F̄_j(|p − e_j|)        (only zones that contain predictions)
P_rec_j  = F̄_j( min_{p ∈ Ŷ ∩ I_j} |p − e_j| )        (0 if Ŷ ∩ I_j = ∅)
Prec_aff = mean_j P_prec_j ;   Rec_aff = mean_j P_rec_j
```

**Tolerance spans** (SearchAuditBench [k_s, k_e]): distance is 0 inside the span and the distance to the nearest endpoint otherwise.

**Why this helps.**
- It credits near-misses, which matter when annotators disagree by one or two steps.
- It normalises by zone length: a one-step miss on a 5-step run is worth less than on a 145-step LongRCA run. This also removes the per-trajectory averaging artefact of §2.3(c).
- Its random baseline is built in, which was Huet et al.'s explicit design goal.

### 4.4 Rule 4: VUS over a tolerance buffer, with a data-driven maximum buffer

For each trajectory and buffer ℓ (in steps), build the soft label of Boniol et al. around each gold step or span:
```
y_ℓ(i) = 1                                  if i ∈ Y (or inside the span)
       = (1 − dist(i, Y)/ℓ)^{1/2}           if 0 < dist(i, Y) ≤ ℓ/2 and i is predicted positive
       = 0                                  otherwise
```
- Compute range-AUC-ROC(ℓ) and range-AUC-PR(ℓ) from the step scores. Recall carries the existence ratio.
- `VUS = (1/(L+1)) Σ_{ℓ=0}^{L} R-AUC(ℓ)`. ℓ = 0 recovers the plain per-trajectory AUROC/AUPRC that OAT reports.
- **Choose L from human agreement**, not by hand: the 90th percentile of inter-annotator |k1 − k2| on datasets that release several annotations (TrajErrBench, LongRCA, AgentHallu, TraceElephant, MP-Bench). Default L = 2 for runs of 30 steps or fewer.
- Report both per-trajectory (macro) and pooled (micro) versions. The pooled version is what TSB-AD's VUS-PR measures.
- Implementation: the TSB-AD / VUS packages accept a 0/1 label vector plus a score vector. Concatenate trajectories with a gap of L padding steps labelled 0, so buffers do not cross trajectory boundaries.

### 4.5 Rule 5: range-based P/R and early-detection credit for timestamps and monitors

**Attribution against spans** (SearchAuditBench [k_s, k_e]; Failure-as-a-Process [t_err, t_lock]).
- Use Tatbul recall with α = 0.5 and a **front-end** bias, so the earliest defensible step counts most.
- Precision uses a flat bias.
- Cardinality γ = 1/x, which penalises fragmented predictions.

**Lock-in** (AgentRx k_lock, FaP t_lock).
- Use a **back-end** bias on [t_err, t_lock]. Tatbul's own reading is that back-end bias suits irreversible events, which is what lock-in means.

**Monitors (report task U3).** Use PATE with the anomaly event at t_lock.
- An alarm in [t_err, t_lock] is an early warning (pre-buffer e = t_lock − t_err): full credit.
- An alarm after t_lock gets credit decaying with delay d.
- An alarm before t_err, or on a successful run, is a false positive.
- Also report lead time `t_lock − t_alarm`, and detection rate at a fixed **per-run** false-alarm budget on successes (5% in Dubey 2026). For comparison, FaP's prompted monitor has 82% precision, 18% recall and median lead time 0.

### 4.6 Per-benchmark recommendation

| Benchmark | Metric used now | Add (TSAD transfer) | References to print next to every number |
|---|---|---|---|
| Who&When (k*, a*) | exact step, agent accuracy | ±1/±2; affiliation P/R; VUS-ROC (L = 2); hit and F1 shown with ceiling and skill S; split by AG/HC and by T | exact 0.095, ±1 0.263, rand-3 hit 0.286, first-3 0.359 |
| MP-Bench (consensus sets) | nDCG@5 | consensus-weighted PA%K-AUC; affiliation with one zone per flagged step; first-5 and position-only nDCG | random nDCG@5 0.128 / 0.315 |
| AgentRx, TRAIL (sets E) | set-F1 | affiliation P/R; PA%K curve; TRAIL broken down by span kind (LLM/TOOL/CHAIN/AGENT); micro and macro | hypergeometric R_F1 at matched prediction-set size |
| SearchAuditBench (tolerance span) | hit inside span | Tatbul front-end range recall; VUS with the span as the range; **final-step baseline** (critical step is the final answer in 17%) | span-length-weighted random |
| Failure-as-a-Process, AgentRx k_lock (timestamps) | timestamp agreement | range P/R on [t_err, t_lock] (back-end); PATE; lead time at a fixed false-alarm budget | random alarm time; constant-q alarm |
| Injected (CORRECT-Error, Who&When Pro, TracerTraj) | exact step | **last-k baseline** (run-to-failure); results on position-matched subsets | last-step 0.95-relative prior |
| LongRCA (T up to 728) | earliest root step | affiliation (handles long T); VUS with L from its 40% exact agreement | R_exact ≈ 1/145 ≈ 0.007 at the median T (mean of 1/T will be higher) |

### 4.7 Protocol hygiene borrowed from the TSAD and log-AD critiques

1. **Task-disjoint (or time-disjoint) splits** between the success data used for training and calibration and the failures used for testing (Le & Zhang; Zavrak, up to 26 pp inflation).
2. **k, thresholds and α chosen on validation data**, never best-on-test (Kim et al.).
3. Always include Kim's **untrained-model** and **input-as-score** controls, and Landauer's **"new event type" rule**, here an exception / empty-return / failure-verbalisation detector.
4. **Stratify** by trajectory length, by error category (reasoning vs surface, using each dataset's taxonomy), and by subset (Who&When HC/AG; MP-Bench manual/automatic).
5. **Paired bootstrap CIs** at the trajectory level. 184 trajectories give about ±0.07 on a hit rate.
6. **Run-to-failure check**: report each method's score correlation with t/T on correct steps of failed runs. A good attributor should be flat there.

---
## Ranked recommendations

All "expected gain" entries are **estimates, not results**. "Prior" means the best k-matched position prior of §4.1.

| # | Method | Benchmark(s) | Target label | Supervision | Expected gain over OAT / position prior | Effort | Risk |
|---|---|---|---|---|---|---|---|
| 1 | **Protocol package (§4)**: analytic random values, k-matched and leave-one-dataset-out position priors, skill score, affiliation P/R, VUS (L from annotator disagreement), PA%K over sets, Tatbul/PATE for timestamps, task-disjoint splits | all 21 that have step labels | k*, E, k_lock, spans | none | Changes conclusions, not accuracy. OAT's Who&When top-3 skill is about 0.14; expect some published "SOTA" step-attribution claims to fall inside the position-prior CI | S | low |
| 2 | **Floor suite on OAT's embeddings** (E2 + Kim): 1-NN to success bank, PCA error, L2, Mahalanobis, linear AR residual, untrained gated CDE, exception/empty-return rule | Who&When; any success-releasing set (AgentHallu, HORIZON); MCP-Atlas if the OAT data is obtainable | k*, E | L1-selected | Parity with ungated OAT expected (within a few AUROC points). If the untrained gated CDE gets close to gated OAT, the gate rather than learning carries the OOD gain | S | low |
| 3 | **Paired-bag MIL ranking** (F5 Sultani + F6 RTFM top-k), success vs failure of the *same* task, final step masked, position-only MIL as control | AgentHallu (443/250), HORIZON (2,498/1,284), tau2 / ALFWorld / WebShop data engines; test on TrajErrBench-tau2, AgentErrorBench, AgentHallu | k*, E (via argmax / top-k), t_err (first crossing) | L1 | Only family here that can move reasoning-error recall above the prior. Expect gains in-domain; OOD unknown | M | last-step and difficulty shortcuts; recovered errors in negative bags (needs F3 relabelling) |
| 4 | **Deep SAD / PU-SVDD with 25-200 labelled steps** (F1, F4) | TracerTraj train → Who&When / TraceElephant; MP-Bench / AgentRx sets | k*, E | L1 + small L2 | Large gains on categories that are labelled; cheapest way to get reasoning errors into a one-class model | S-M | label-selection bias; class prior π mismatch across datasets |
| 5 | **NCAD-style context-vs-step contrastive with injected outlier exposure** (D4) | train: Who&When Pro / Aegis / TracerTraj injections + successes; test: Who&When, TraceElephant natural | k* | L1 + synthetic L2 | Moderate. Doubles as a clean test of injected→natural transfer | M | register leak; late-position injection skew (needs §4.6 position-matched evaluation) |
| 6 | **MIL "who" over agent bags + VadCLIP-style mode prompts** (F5, F7) | Aegis (agent, mode) train/test; MAST-Data (trace-level modes) | a*, mode; step as by-product | L1 at agent or trace level | New capability: (step, mode) from trajectory-level labels on the two largest non-step datasets | M | MAST-Data labels come from an LLM judge; mode prompts import judge priors |
| 7 | **One-class telemetry monitor** (C2 ESN/Mahalanobis + CUSUM; C1 dynamic threshold) on exception / empty / repeat / latency / length channels | Terminal-Bench re-runs (FaP protocol), AgentRx tau-bench rows | t_obs, t_lock, lead time | L1 (healthy runs) | Good on loops and tool cascades. ≈ 0 on fabrication (Dubey 2026: within-organic AUROC 0.31-0.42). Serves as the surface-error floor for any monitor (U3) | S | needs a per-deployment healthy null; does not transfer cold |
| 8 | **WETAS-style ordered segmentation** (F9) for lock-in onset; compare with TRACES (F11) and the hazard model | AgentRx k_lock; FaP t_lock where text exists | k_lock | L1 | An onset estimate that does not impose the monotone, late-rising risk TRACES hard-codes | M | assumes a single normal→failure switch; recovered errors break it |
| 9 | **Discrete step-type model** (G1 DeepLog / G3 LogBERT / H4 FSM surprise) + cycle detector (H2) | TRAIL structural categories; MAST FM-1.3/1.5; Who&When structural subset | structural spans | L1-selected | High on loops and termination errors; ≈ 0 on reasoning errors. A cheap channel to fuse with #3 | S | narrow coverage |
| 10 | **Contamination-robust one-class training** (F3 LOE, A3 COUTA), α from FaP PASS statistics (about 10% of steps) | any one-class run (#2, #7) | — | L1 | Fewer false alarms on recovered errors in successes | S | small gain |
| 11 | **Same-task AB-join discord** (E1) in near-deterministic environments | ALFWorld / WebShop (AgentErrorBench), tau2 (TrajErrBench) | k* | L1-selected | Can catch wrong-plan errors when successes of the task agree. Free with the data engine | S | meaningless without same-task successes |
| 12 | **Off-the-shelf deep TSAD** (Anomaly Transformer, TranAD, DCdetector, TimesNet, diffusion) via TSB-AD / TimeSeAD | Who&When, MCP-Atlas | k* | L1-selected | None expected (Sarfraz 2024; TSB-AD 2024; window assumptions break on T ≈ 10). Run once only to pre-empt reviewers | M | wasted effort |

---

## Open gaps

1. **No agent benchmark has the structure TSAD benchmarks assume.** That would be many normal series, the anomalous series, point/range labels and a replayable generator.
   - Failure-as-a-Process has successes and timestamps but no step text.
   - AgentHallu (250 clean) and HORIZON (judge-labelled successes) come closest.
   - A UCR-archive-style "one decisive step per run, with released successes of the same task, and a tolerance span" benchmark built from the replayable data engines is missing.
2. **Anomaly is not cause.**
   - TSAD "diagnosis" (TranAD, OmniAnomaly, Garg et al.) means *which channel*, not *which time step caused the outcome*.
   - No TSAD metric rewards the counterfactual repair-effect profile of the report.
   - Affiliation and VUS soften the step-matching problem but still score against one human label.
   - An evaluation that scores detectors against repair-effect φ (Proposal 1) has no TSAD precedent.
3. **Reasoning errors.**
   - No TSAD family has a channel for "the step contradicts the evidence it was given".
   - The nearest hooks are untested: Anomaly Transformer's local-vs-global association (B6), DCdetector's two-view discrepancy (D3), CoE's layer-path features (H7).
   - Dubey 2026 handles content errors with a deterministic verifier, not a detector.
   - An entailment / grounding channel per step (observation ⇒ claim) is the missing feature for every family in §3.
4. **Exchangeability for conformal decoding across tasks.**
   - OAT's per-step guarantee holds only for in-distribution success steps.
   - Task-conditional (Mondrian) or trajectory-level calibration, and a coverage guarantee for the *decisive step* (fa_ideas C3), are not in the TSAD literature for many-short-series data.
5. **MIL's negative-bag assumption fails on agent data.** Successful runs contain recovered errors (2.3 per FaP PASS run). Video MIL assumes clean normal videos. Combining LOE / PU corrections with MIL ranking under the "unrecovered error" semantics is open, and it is the same open problem as the hazard model's recovery term.
6. **Choosing the tolerance buffer.** VUS averages over buffers up to L. No paper ties L to measured annotator disagreement. Agent datasets have that disagreement data (40-91% exact agreement), so this can be done here first.
7. **Online evaluation.**
   - Only Dubey 2026 reports detection at a fixed false-alarm budget against verified onsets, and those onsets come from injections.
   - No natural-failure benchmark reports lead time vs t_lock with a per-run false-alarm budget. FaP has the timestamps but no text.
8. **Unverified items to resolve before citing:**
   - whether OAT's MCP-Atlas success (train) and failure (test) runs share tasks;
   - where MASC's "normal trajectories" for Who&When come from;
   - the exact Deep SVDD, LSTM-NDT, USAD, LOE and PLELog details marked *(from memory)* above.
