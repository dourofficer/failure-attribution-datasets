# Slice A: neural differential equations and rough paths, read for step-level failure attribution

*Written 2026-10-30 for the time-series survey (`00_context_brief.md`). Companion to `01_oat_vs_ncde.md`, which holds the side-by-side table of OAT against Kidger et al. 2020; this file does not repeat it. Every paper below was checked on its arXiv abstract page or publisher page on 2026-10-30. Where the PDF was read (Kidger 2020, Morrill 2021/2022, NRDE, ANCDE, Neural Flows, SDA2D, Cochrane 2020, Sig-Networks), statements are tagged **[paper]**. Statements tagged **[derivation]** are my own algebra, not claims made in any paper. **[unverified]** means I could not confirm the item from a primary page. Venue and year come from the arXiv comment field or the proceedings page.*

## Scope and verdict

1. The NDE and rough-path lineage has three things OAT did not use. (i) A theory of which control paths can run online: Morrill et al. (TMLR 2022) show that natural cubic splines are offline, linear and Hermite-with-backward-differences interpolation are online only at the observation times, rectilinear interpolation is online at all times, and ODE-RNN is a special case of the rectilinear NCDE. (ii) Filtering models that predict each step *before* seeing it (ODE-RNN, GRU-ODE-Bayes, NJ-ODE, latent SDE). These give a per-step innovation or NLL that cannot collapse to zero. (iii) Signature tools with calibrated one-class scores (conformance, variance norm, signature MMD, novelty tests with false-positive bounds) and online change detectors (signature-MMD regime detection; signature quickest detection, July 2026).
2. No paper we found in this lineage localises errors among discrete agent steps. The NCDE anomaly-detection papers (SDA2D at AAAI-26, GDFlow at CIKM-25, PoA at KDD-23) are offline detectors over sensor windows. SDA2D and GDFlow build their path with cubic splines; PoA does not name its interpolation. OAT is the first transfer of this recipe to agent traces that we found, and it inherits the offline spline.
3. The literature backs the brief's critique; it does not prove it:
   - An NCDE with linear interpolation, solved by Euler with one step per knot, *is* a residual RNN (NRDE §3.2).
   - The documented NCDE gains come from irregular timestamps, which `u = t/T` throws away.
   - An NCDE can represent the identity between paths (Kidger Thm C.1), so OAT's reconstruction objective has a degenerate optimum.
   - Signature networks gain under 1 macro-F1 point over a BiLSTM on per-utterance change detection (Sig-Networks, EACL 2024).
4. Most promising mappings: **(1)** a causal filter (Hermite-backward or rectilinear NCDE, GRU-ODE-Bayes, NJ-ODE) used as a prefix monitor and scored by per-step predictive NLL, on AgentRx `k_lock` and on AgentErrorBench / TrajErrBench with successes collected by replay. **(2)** Signature conformance (SigMahaKNN) on expanding windows of step embeddings: a training-free one-class baseline OAT must beat. **(3)** Signature change and quickest detection (signature-MMD windows; a stopping rule that is linear in the signature) as the label-free change point (U2) and the learned monitor (U3). For P1 at L1+: TE-CDE and expected-signature regression over bags of rollouts.

## What OAT took from NCDE and what it changed

Notation: `y_t = (h_t, u_t)` are the knots, with `u_t = t/T` and `Δ = 1/T`. `S` is the natural cubic spline, so `X = S`. OAT's model: `z(u) = g2(h_Q) + ∫_0^u f(v, z(v)) q(dX/dv) ⊙ dX/dv dv`, `h_hat = g1(z)`, Euler solver.

| OAT choice | Precedent in the lineage | Contradiction or caveat from the lineage |
|---|---|---|
| natural cubic spline | Kidger 2020 default; SDA2D and GDFlow use it inside sliding windows | Kidger 2020 §6.4 "Choice of X" [paper]: "natural cubic splines ... are not causal ... infeasible ... in real-time settings". Morrill 2022 Table 1: offline. Morrill also reports that it is not always best even offline: CharacterTrajectories accuracy 83.6±6.1 (natural cubic) vs 97.6–99.3 (linear / Hermite / rectilinear) [paper] |
| `u = t/T`, time as a channel | time as a channel is required for uniqueness (Morrill 2022 §2.4) | Morrill uses the index parametrisation `s_i = i` and relies on reparametrisation invariance [paper]. OAT breaks that invariance twice: `f` depends on `v` explicitly, and `q` acts on `dX/du`, which scales with `T` [derivation, below]. `t/T` also needs `T`, so the time channel itself is non-causal |
| Euler solver | Morrill 2022 §2.2: Euler needs the control to be piecewise C² with bounded second derivative, which the spline satisfies | with one Euler step per knot, linear interpolation turns the model into a residual RNN on increments (NRDE §3.2). With a natural cubic spline it is still non-causal (below) |
| reconstruct every observation of successful runs | SDA2D (AAAI-26) reconstructs `x_t` and the state derivative per time point; GDFlow (CIKM-25) scores NCDE+flow NLL per window; PoA (KDD-23) trains on resampled normal data | Kidger Thm C.1 [paper]: "a Neural CDE can easily represent the identity function between paths". Reconstructing the control path is a degenerate objective (01 §2). No precedent addresses this; the filtering models avoid it by predicting before the update |
| gate `q(dX/du) ⊙ dX/du` | ANCDE (ICDM 2021): `Y(t) = a(t) ⊙ X(t)`, `a(t) = σ(h(t))` from a bottom NCDE, top NCDE driven by `dY/dt` [paper] | ANCDE's attention depends on history and acts on the path. OAT's gate is memoryless, acts on the derivative, and gets no training signal on out-of-distribution derivatives |
| conformal threshold on held-out successes | Cochrane et al. 2020 split the normal corpus in half to calibrate conformance [paper]; Gasteratos et al. 2025 give false-positive tail bounds and p-values for signature statistics; Wang & Chakraborty 2026 bound `P(τ < θ) ≤ ε` for an online stopping rule | OAT controls a per-step false-positive rate pooled over steps. A monitor needs the per-trajectory false-alarm probability, which the stopping-rule literature controls |

**[derivation] Non-causality survives the knot grid.** `01_oat_vs_ncde.md` §2 says that with one Euler step per knot "the spline is inert". That holds exactly for **linear** interpolation, and it is the NRDE §3.2 equivalence. It does not hold for the natural cubic spline. For uniform knots the second derivatives solve `M_{i-1} + 4M_i + M_{i+1} = 6(y_{i+1} − 2y_i + y_{i-1})/Δ²`, with `M_0 = M_T = 0`. The spline is C², so its slope at knot `i` is unique: `S'(u_i) = (y_{i+1} − y_i)/Δ − Δ(2M_i + M_{i+1})/6`. An Euler step from knot `i` therefore gives

`z_{i+1} = z_i + f(u_i, z_i) · q(S'(u_i)) ⊙ [ (y_{i+1} − y_i) − Δ²(2M_i + M_{i+1})/6 ]`.

The inverse of the tridiagonal (1, 4, 1) matrix decays as `(−0.268)^{|i−j|}`, where 0.268 = 2 − √3. I checked this numerically with scipy's natural `CubicSpline` (41 uniform knots, interior knot). The increment `S'(u_i)·Δ` puts weights −0.804, 0, +0.804, −0.215, +0.058 on `y_{i−1}, y_i, y_{i+1}, y_{i+2}, y_{i+3}`. So each Euler update is a centred difference `0.8(y_{i+1} − y_{i−1})`, with no weight on `y_i` itself, plus look-ahead terms at relative weights −0.27 and +0.07. OAT's `h_hat(u_t)` therefore sees future steps, and the gate's input `S'(u_i)` is a smoothed derivative that looks ahead. Morrill's own wording [paper]: "Any change in one datapoint has a small effect on the entire construction, even at earlier times." For attribution this means that an error at step `k` leaks backwards into the scores at `k−1` and `k−2`. That costs exact-step accuracy on Who&When, where 36% of errors sit at steps 0–2.

**[derivation] What the score is when `f` is near the identity.** Take the identity solution (`f ≡ [I 0]`, `g1 = g2 = I`) with no gate and an Euler step per knot. Then `h_t − h_hat(u_t) = (Δ²/6) Σ_{i<t} (2M_i + M_{i+1})`, a running sum of spline curvature. With the gate, the residual also accumulates `Σ_{i<t} (1 − q_i) ⊙ Δy_i`. Once an increment is suppressed, `z` cannot recover it, so the residual stays raised after the first suppressed jump unless later increments happen to cancel it. Two testable predictions follow. First, gated-OAT scores on a failed trajectory should look like a step function starting at the first strongly gated step, not like a spike. Second, top-3 decoding will then pick that step and the steps after it. Both fit OAT's App. H: it fires on failure verbalisation and on reactions to empty tool returns, which is the behaviour of a `t_obs` detector.

**[derivation] The gate depends on `T`.** `dX/du ≈ T · Δh_t` and the time-channel derivative is 1. Who&When Hand-Crafted runs (median 32.5 steps) therefore present derivatives about 4.6× larger than MCP-Atlas training runs (about 7 steps) for the same embedding change. A gate trained to suppress "atypically large" derivatives (OAT §4.1) suppresses more on longer runs because of length alone. Per-trajectory ranking is only partly protected, because `q` is nonlinear. The conformal threshold, calibrated on short in-domain runs, is not protected at all. Test: regress the number of conformal flags per trajectory on `T` on Who&When, and rerun OAT with `s_i = i` (Morrill's parametrisation) plus a separate `t/T` feature.

**[derivation] What trains the gate.** OAT's text describes no regulariser on `q`. Reconstruction on successes rewards `q < 1` only where passing an increment through *hurts* reconstruction, i.e. directions the trained `f` handles badly. On derivatives never seen in training, `q` is set by how a 4-layer, width-12 MLP extrapolates, not by any objective. The +0.172 OOD AUROC is therefore an empirical fact without a mechanism. Two ablations settle it: the gate-only score `‖(1 − q(dX/du)) ⊙ dX/du‖` (01 §2), and replacing `q` with a fixed norm clip.

**Is the signal from selection or from the CDE? What the literature implies.**
- (a) Kidger 2020 Thm C.1 and NRDE §3.2: on a uniform step grid, an NCDE with causal interpolation is a residual RNN driven by increments. Any CDE-vs-RNN gap in OAT's Fig. 5 must therefore come from look-ahead in the spline, from the task difference (reconstruct with access vs predict without access), or from the gate. Continuous time cannot be the source.
- (b) The NCDE gains reported in this literature come from irregular, informative timestamps: PhysioNet and MIMIC-IV (Kidger 2020; Morrill 2022), CERT logs (Jurišić et al., NCDE F1 0.364 vs LSTM 0.133 on CERT 6.2). OAT discards timestamps.
- (c) On per-utterance change labels over sentence embeddings, the closest analogue to per-step labels, signature networks barely beat a BiLSTM. Anno-MI macro-F1: Seq-Sig-Net .525 vs BiLSTM .518 vs FFN-history .520 [paper, Sig-Networks Table 3].

So the rough-path machinery is not expected to carry the signal. The candidates that remain are selection (training on successes), look-ahead, and the gate. This is consistent with the brief's critique. It is not a test of it: the gate-only score, the causal predict-before-update variant, and a "train on all runs" control are the three experiments that test it.

## Methods

Per entry: citation; mechanism; mapping (a) input `x_t`, (b) training data and supervision level, (c) output, (d) target / dataset / metric, (e) position baseline to beat, (f) what breaks; code. Datasets and baselines are those of brief §2. Which datasets release successes matters for every one-class or L1 method. Who&When, TraceElephant, MP-Bench, AgentRx, TrajErrBench and AgentErrorBench do **not** release successes. AgentHallu (250 clean), HORIZON (1,284 judged successes), TRAIL (mixed) and Failure-as-a-Process (610 PASS, annotations only, no step text) do. Replayable systems (tau2-bench, ALFWorld/WebShop, SWE-bench, Terminal-Bench, Aegis/MASLab) can generate successes.

### A. Control paths and causality

#### A1. Neural CDEs (Kidger, Morrill, Foster, Lyons; NeurIPS 2020; arXiv:2005.08926)
- **Mechanism.** `z_t = z_{t0} + ∫ f_θ(z_s) dX_s`, `z_{t0} = ζ_θ(x_0, t_0)`. `X` is a natural cubic spline through `(t_i, x_i)` with time as a channel. Solved as `dz/ds = f_θ(z_s) dX/ds`. Linear readout; cross-entropy; adjoint backprop.
- **Theory [paper].** Universal approximation (Thm B.14). Thm C.1: any `dz = h(z, X_s) ds` model is an NCDE, but not conversely, because "a Neural CDE can easily represent the identity function between paths".
- **Limitation [paper].** The natural cubic spline is not causal: `X_t` depends on `x_i` for `t < t_i`.
- **Map.** This is OAT's backbone (brief §4); the useful content for us is Thm C.1 and §6.4 ("Choice of X": the spline is not causal).
- **Code.** github.com/patrick-kidger/NeuralCDE, torchcde.

#### A2. Online NCDEs / choice of interpolation (Morrill, Kidger, Yang, Lyons; arXiv:2106.11028; TMLR 2022 as "On the Choice of Interpolation Scheme for Neural CDEs")
- **Mechanism [paper].** Four required properties of a control path: adapted measurability, smoothness, boundedness, uniqueness.
  - Measurability has three grades: *continuously online* (`z(t)` depends only on data up to `t`), *discretely online* (online at the observation times), *offline*.
  - Schemes: natural cubic = offline. Linear = discretely online if no data is missing. Hermite cubic with backward differences (each piece matches gradients `x_i − x_{i−1}` and `x_{i+1} − x_i`) = discretely online and smooth.
  - Rectilinear: `X(2i) = (t_i, x̃_i, c_i)`, `X(2i−1) = (t_{i+1}, x̃_i, c_i)`, i.e. time advances with values held, then values jump with time held. This is continuously online, and ODE-RNN is a special case of the rectilinear NCDE.
  - Uses the index parametrisation `s_i = i`; the solution is invariant to reparametrisation.
  - MIMIC-IV online monitoring: beats ODE baselines on 3/3 tasks and non-ODE baselines on 2/3.
- **Map.**
  - (a) `x_t = (h_t^{PCA≤16}, τ_t, c_t, onehot(step type, agent))`, with `τ_t` = wall-clock or cumulative tokens (TRAIL spans carry `timestamp`, `duration`, `llm.token_count.*`, per `notes/trail.md`) or the step index.
  - (b) Successes (OAT's L1 selection) or all runs (L0).
  - (c) Per-step innovation `e_t = ‖h_t − ĥ(t^-)‖²`, where `ĥ(t^-)` is read from `z` **before** the rectilinear jump at step `t`. This is the step that removes the identity leak.
  - (d) AgentRx `k_lock`, scored by lead time and set-F1 against the failure-event set. Who&When `k*` (top-3 hit, AUROC). AgentErrorBench critical step, with ALFWorld/WebShop successes collected by deterministic replay.
  - (e) Who&When first-3 = 0.36, random-3 = 0.29, position-only AUROC 0.60; AgentErrorBench relative position median 0.23.
  - (f) A prefix monitor cannot score steps 0–2 well (36% of Who&When errors). `t/T` must be replaced by an online feature.
- **Supervision.** L1-selected or L0.
- **Code.** github.com/jambo6/online-neural-cdes; schemes in torchcde.

#### A3. Neural Rough DEs (Morrill, Salvi, Kidger, Foster, Lyons; ICML 2021; arXiv:2009.08295)
- **Mechanism [paper].** Choose `r_0 < … < r_m` with `m ≪ n` and depth `N`. Replace `f(Z) dX/dt` by `f̂(Z) LogSig^N_{r_i, r_{i+1}}(X) / (r_{i+1} − r_i)` on `[r_i, r_{i+1})`. This is the log-ODE method. With `r_i = t_i` and `N = 1` it reduces to an NCDE with linear interpolation. Handles length up to 17k. The piecewise-linear path makes window `i` available at `r_{i+1}`, so it is discretely online at window ends.
- **Map.**
  - (a) Step embeddings (PCA ≤ 8–16: depth-2 log-sig dimension is `d + d(d−1)/2`) plus step type.
  - (b) Successes or all runs.
  - (c) Per-window innovation, then step-level localisation inside the flagged window.
  - (d) LongRCA earliest root step (median 145 steps, max 728; exact and ±k; human exact agreement only 40%). MemTrace faulty operation (497 ops per slice). TraceElephant LLM-call steps.
  - (e) LongRCA position prior (not given in brief; compute it).
  - (f) Window granularity vs single-step targets; long traces have few failures per domain.
- **Supervision.** L0/L1.
- **Code.** github.com/jambo6/neuralRDEs.

#### A4. Log-NCDEs (Walker, McLeod, Qin, Cheng, Li, Lyons; ICML 2024; arXiv:2402.18512)
- **Mechanism.** NRDE plus the full Log-ODE step, which includes the Lie brackets of the vector field. Series up to 50k observations. The abstract reports wins over NCDE, NRDE, LRU, S5 and Mamba.
- **Map.** Same as A3, for long traces (LongRCA, MemTrace). Gain over A3 is accuracy per window, not localisation.
- **Supervision.** L0–L2.
- **Code.** Not linked on the arXiv page [unverified].

#### A5. Rough Transformers (Moreno-Pino, Arroyo, Waldon, Dong, Cartea; NeurIPS 2024; arXiv:2405.20799)
- **Mechanism.** Multi-view signature attention: attention over local-window and global signatures of the input path. Robust to sequence length and sampling frequency; a fraction of the compute of NDE models.
- **Map.**
  - (a) Step embeddings.
  - (b) L2 per-step labels where splits exist (TracerTraj train/test, Who&When Pro injected), or L1 sequence labels with attention attribution.
  - (c) Per-step logits.
  - (d) Who&When / TraceElephant `k*` exact.
  - (f) Injected-to-natural shift (CORRECT-Error relative position 0.95 vs natural 0.4–0.5); attention is not faithful attribution.
- **Supervision.** L2/L1.
- **Code.** Not on the arXiv page [unverified].

### B. Learnable and attentive control paths (OAT App. A, "attention-based control paths")

#### B1. ANCDE (Jhin, Shin, Hong, Park, Park; ICDM 2021; arXiv:2109.01876)
- **Mechanism [paper].**
  - A bottom NCDE produces `h(t)`. Attention is either time-wise, `a(t) = σ(FC(h(t))) ∈ [0,1]`, or element-wise, `a(t) = σ(h(t)) ∈ [0,1]^{dim X}`.
  - Variants: soft sigmoid, hard rounding, or straight-through with slope annealing.
  - A top NCDE is driven by `Y(t) = a(t) ⊙ X(t)`, i.e. by `dY/dt = ȧ ⊙ X + a ⊙ Ẋ`.
- **Relation to OAT.** OAT's `q(dX/du) ⊙ dX/du` is ANCDE's element-wise attention with three changes: no bottom NCDE (memoryless), applied to the derivative not the path, trained by reconstruction not classification.
- **Map.**
  - (a) Step embeddings.
  - (b) Option 1: replace OAT's `q` with a history-dependent `a(t)` (L1-selected). Option 2 (L1): train an ANCDE classifier on outcome `S` (AgentHallu 443 failed + 250 clean; HORIZON; replay-collected tau2 / ALFWorld runs) and read `1 − a(t)` as the attribution.
  - (c) Per-step attention mass.
  - (d) AgentHallu hallucination step (exact, ±1); AgentErrorBench critical step.
  - (e) Position prior.
  - (f) Attention is not faithful. A classifier trained on `S` can use task-difficulty features unrelated to any step. Hard attention plus short trajectories (median 6 in AgentHallu) means few positions to choose from.
- **Supervision.** L1.
- **Code.** github.com/sheoyon-jhin/ANCDE.

#### B2. EXIT (Jhin et al.; WWW 2022; arXiv:2204.08771)
- **Mechanism.** An encoder-decoder produces a latent continuous path that replaces or complements explicit interpolation. The decoder can extrapolate past the observed range.
- **Map.** Extrapolation is a forecast of the next step from the prefix. If the encoder is restricted to the prefix, the residual `‖h_{t+1} − Ŷ(t+1)‖` is a one-step-ahead innovation. Same targets as A2.
- **Supervision.** L1-selected.
- **What breaks.** The encoder reads the whole series; it must be made causal.
- **Code.** Not on the arXiv page [unverified].

#### B3. Learnable Path in NCDEs (Jhin, Jo, Kook, Park, Woo, Lim; AAAI 2023; arXiv:2301.04333)
- **Mechanism (arXiv HTML).**
  - Encoder NCDE on the spline gives `e(t_N)`; then `h(0) = φ(e(t_N))`, a decoder NODE `dh/dt = f(h, t)`, and the latent path `Y = m(h)`.
  - Final NCDE: `dz/dt = g(z) (dY/dh) f(h, t)`.
  - Loss `L_task + L_Y`, with `L_Y = Σ [α‖Y(t_i) − x_i‖² − β log p(ĥ(t_i))]`. The density term uses Hutchinson's estimator, i.e. a CNF on the decoder state.
- **Relevance.** This already combines OAT's two future-work items: a learned path plus an exact-likelihood term.
- **Map.** Score `= α‖Y(t_i) − h_i‖² − β log p`. Same targets as A2.
- **What breaks.** `h(0)` depends on `e(t_N)`, i.e. the whole sequence, so it is offline. An encoder-decoder pair is a lot of parameters for 100 training trajectories.
- **Code.** Not linked [unverified].

#### B4. Kernel/GP-smoothed control paths (Serov, Kuleshov, Zaytsev; arXiv:2602.02157, Feb 2026)
- **Mechanism.** Replaces exact interpolation with kernel or GP smoothing to cut the number of function evaluations.
- **Map.** Relevant only as evidence that the control-path choice is still open. A one-sided (causal) kernel would give a smoothed online path.
- **Supervision.** n/a. Online use is not stated.

### C. Filtering: continuous-time models that predict before they update

These give the per-observation predictive distribution that OAT lacks. They are the natural fix for the identity leak.

#### C1. ODE-RNN and Latent ODE (Rubanova, Chen, Duvenaud; NeurIPS 2019; arXiv:1907.03907)
- **Mechanism.** ODE-RNN evolves `h` by an ODE between observations and applies an RNN update at each observation. Latent ODE is a VAE whose ODE-RNN encoder is reversed in time. Both can model observation times with a Poisson process.
- **Map.**
  - (a) Step embeddings; if timestamps are real (TRAIL), the Poisson term also scores *when* a step happens (stalls, bursts).
  - (b) Successes or all runs.
  - (c) Per-step predictive residual or Gaussian NLL of `h_t` from `h(t^-)`.
  - (d) As A2.
  - (f) With uniform indices the ODE part carries no information and the model is a GRU.
- **Supervision.** L1-selected/L0.
- **Code.** Not on the arXiv page [unverified].

#### C2. GRU-ODE-Bayes (De Brouwer, Simm, Arany, Moreau; NeurIPS 2019; arXiv:1905.12374)
- **Mechanism.** A continuous-time GRU-ODE propagates a Gaussian state between observations; a Bayesian update network assimilates each sporadic observation (filtering).
- **Map.**
  - (a) Step embeddings.
  - (b) Successes (OAT-style) or all runs.
  - (c) Two per-step scores: the predictive NLL `−log N(h_t; μ_t^-, Σ_t^-)`, and the update size `KL(post_t ‖ prior_t)` ("surprise"). The running sum is a monitor statistic for CUSUM-type thresholding.
  - (d) AgentRx `k_lock` (lead time; brief's FaP prompted monitor: median lead 0, recall 18%). Who&When `k*` AUROC. MP-Bench nDCG@5 with consensus rate as graded relevance.
  - (e) Position-only AUROC 0.60 (Who&When).
  - (f) Gaussian NLL in 64 dims from about 700 training steps is ill-conditioned; use PCA ≤ 16 or a diagonal covariance. Early errors have no prefix to predict from.
- **Supervision.** L1-selected/L0.
- **Code.** Not on the arXiv page [unverified].

#### C3. Neural Jump ODE (Herrera, Krach, Teichmann; ICLR 2021; arXiv:2006.04727)
- **Mechanism.** A neural ODE evolves the prediction between observations and jumps at each new one. The output converges to the L²-optimal prediction `E[X_t | F_{t_k}]`. Learning the conditional expectation is posed as a filtering problem.
- **Why it matters.** It is the only paper here with a guarantee that the per-step residual is the *innovation* under the training law.
- **Map.** Trained on successes, the innovation `h_t − E_succ[h_t | prefix]` is exactly "deviation from how successful runs continue". Trained on all runs, it is deviation from the agent's own policy, which per brief §4 should *not* flag on-policy mistakes. That pair is the cleanest test of the selection hypothesis. Targets as A2.
- **Supervision.** L1-selected vs L0, as a controlled comparison.
- **Code.** Not on the arXiv page [unverified].

#### C4. Neural Jump SDEs (Jia, Benson; NeurIPS 2019; arXiv:1905.10403)
- **Mechanism.** A latent state flows between events and jumps at events. Event intensity is conditioned on the latent state. Handles marked point processes (Hawkes, Stack Overflow badges, medical records, earthquakes).
- **Map.**
  - (a) Marks only: step type (TRAIL `span_kind` LLM/TOOL/CHAIN/AGENT, tool name), acting agent, exception flag, plus real timestamps where available.
  - (b) All runs (L0) or successes.
  - (c) Per-event surprisal `−log λ_{m_t}(t_t) + ∫ λ`.
  - (d) TRAIL error spans (set-F1); AgentRx failure events; Who&When `a*` ("who") as a mark-level argmax.
  - (f) On uniform indices the time part is empty, leaving a categorical next-mark model. Marks miss content errors (wrong facts with a well-formed call).
- **Supervision.** L0/L1.
- **Code.** Not on the arXiv page [unverified].

#### C5. Neural Flows (Biloš, Sommer, Rangapuram, Januschowski, Günnemann; NeurIPS 2021; arXiv:2110.13040)
- **Mechanism [paper].** Model the solution `x(t) = F(t, x_0)` directly, with `F(0, x) = x` and `F(t, ·)` invertible. Architectures: ResNet flow `F = x + φ(t) g(t, x)` with Lip(g) < 1; GRU flow; coupling flow `F_A = x_A exp(u(t, x_B) φ_u(t)) + v(t, x_B) φ_v(t)`. Applied to latent-variable time series, temporal point processes and density estimation without a solver.
- **Map.** A drop-in for C1–C4 without the Euler error OAT carries. The coupling flow gives exact likelihoods. Gain is speed and exactness, not attribution accuracy.
- **Supervision.** As C1.

### D. Stochastic paths and likelihood (OAT App. A: "Neural SDEs", "exact likelihood via CNF")

#### D1. Latent SDEs with the stochastic adjoint (Li, Wong, Chen, Duvenaud; AISTATS 2020; arXiv:2001.01328)
- **Mechanism.** Adjoint gradients for SDEs combined with stochastic variational inference for latent SDEs (fit on 50-dimensional motion capture). The prior SDE is learned from data; a posterior SDE explains each sequence. The ELBO KL term is a time integral of the squared drift difference over diffusion. The KL form is from my reading, not from the abstract [unverified].
- **Map.**
  - (a) Step embeddings.
  - (b) Successes train the prior dynamics.
  - (c) Per-step KL rate (how hard the posterior must push against success dynamics around step `t`), plus predictive uncertainty.
  - (d) MP-Bench nDCG@5; AgentHallu step.
  - (f) The standard posterior encoder is bidirectional (offline); 100 trajectories is very little for an SDE prior.
- **Supervision.** L1-selected.
- **Code.** torchsde.

#### D2. Neural SDEs as infinite-dimensional GANs (Kidger, Foster, Li, Oberhauser, Lyons; ICML 2021; arXiv:2102.03657)
- **Mechanism.** The generator is an SDE driven by Brownian motion; the discriminator is a Neural CDE; a Wasserstein objective.
- **Map.** The trained NCDE discriminator is a learned critic on paths. Its value on prefixes `τ_{≤t}` gives a per-step "realism drop".
- **Supervision.** L1-selected.
- **What breaks.** GAN instability with about 100 paths.
- **Code.** torchsde examples.

#### D3. Non-adversarial Neural SDE training with signature kernel scores (Issa, Horvath, Lemercier, Salvi; NeurIPS 2023; arXiv:2305.16274)
- **Mechanism.** Strictly proper scoring rules on path space built from signature kernels, `φ(P, y) = ½ E k(X, X') − E k(X, y)`. The form is my reading of "signature kernel scores" [unverified]. Computed by solving linear path-dependent PDEs; supports conditional generation given a past path.
- **Map (L1+).**
  - (b) Generate continuations from prefix `τ_{≤k}` (replay: TraceElephant SWE-Agent subset, tau2, ALFWorld; or the Aegis injector), labelled by outcome.
  - (c) Score the observed continuation, giving a calibrated "how atypical is what happened next", and the change in the score along `k`.
  - (d) TrajErrBench critical step; P1 fragility curves.
  - (f) Needs rollouts.
- **Code.** Not linked on arXiv [unverified]; sigkernel library exists (E3).

#### D4. Stable Neural SDEs (Oh, Lim, Kim; ICLR 2024 spotlight; arXiv:2402.14989)
- **Mechanism.** Langevin-type, linear-noise and geometric SDE classes with stability guarantees. Robust to distribution shift and missing data (30 datasets).
- **Map.** Use as the dynamics family for D1 when the deployment shift is MCP-Atlas → Who&When. Expected to address OAT's need for CORAL, not attribution itself.
- **Supervision.** As D1.

#### D5. FFJORD (Grathwohl, Chen, Bettencourt, Sutskever, Duvenaud; ICLR 2019; arXiv:1810.01367) and Neural ODE CNFs (Chen et al., NeurIPS 2018; arXiv:1806.07366)
- **Mechanism.** Continuous normalising flow `dx/dt = g(x, t)`. `log p` is obtained by integrating `−tr(∂g/∂x)`, which FFJORD estimates unbiasedly with Hutchinson's estimator. Free-form architectures.
- **Map.**
  - (c) Conditional CNF `p(h_t | z_{t−1})` with the context `z_{t−1}` from a causal NCDE (A2) or GRU (C2); score = per-step NLL, which is exactly OAT's App. A item.
  - (d) As A2/C2.
  - (f) Density estimation in 64 dims from about 700 steps overfits. Use PCA ≤ 8–16 and report NLL calibration on held-out successes.
- **Supervision.** L1-selected/L0.

#### D6. Continuous-time flow process, CTFP (Deng, Chang, Brubaker, Mori, Lehrmann; NeurIPS 2020; arXiv:2002.10516)
- **Mechanism.** A normalising flow applied as a differential deformation of a Wiener process. Efficient likelihood and marginals for irregular observations, with interpolation.
- **Unverified detail.** The likelihood factorises over observations through the Markov base process, which would give a per-observation conditional likelihood. This is from my reading.
- **Map.** Per-step `−log p(h_t | h_{<t})` without a separate encoder. The same reduced-dimension caveat as D5.
- **Supervision.** L1-selected/L0.

#### D7. GDFlow: NCDE plus normalising flow (Lee, Kim, Jun, Woo; arXiv:2409.05346; CIKM 2025 as "Anomaly Detection for ADAS with NCDE-based Normalizing Flow")
- **Mechanism (arXiv HTML).** Cubic-spline path per sliding window. One NCDE gives a temporal state `H(T)`; a second, graph NCDE driven by `dH/dt` gives a spatial state `Y(T)`. `S = Y ⊙ H` is mapped by a flow to `N(μ, Σ)`.
- **Objective.** Quantile NLL `−ψ(log p(S), q)` with `q ∈ {0.01, …, 0.1}` to sharpen the boundary of the normal class. Trained on normal data only. The score is the window NLL; F1 uses the best threshold on test data.
- **Relevance.** This is the NCDE+flow design that OAT lists as future work, already published.
- **Map.** Replace OAT's reconstruction with the quantile NLL of a per-step conditional flow. Targets as A2.
- **What breaks.** Window-level scores; optimistic threshold selection; the spline is offline.
- **Code.** Not mentioned [unverified].

### E. NCDE anomaly detectors: the direct precedents of OAT

#### E1. SDA2D (Sun, Zhou, Wu, Li; AAAI-26; DOI 10.1609/aaai.v40i30.39770; no arXiv version found)
- **Mechanism [paper].**
  - A natural cubic spline over the whole series; NCDE inside windows; `z(t_0)` is the mean of an initialisation layer over the window.
  - States `r_i = concat(z(t_1..t_W))`, then a temporal-spatial attention module.
  - The model reconstructs both `x_t` and the **system-state derivative** `SD_t`, which is the NCDE vector field times `dX/dt`.
  - Score `s_t = ‖x_t − x̂_t‖² + ‖SD_t − ŜD_t‖²`; threshold `μ + 3σ` after min-max scaling.
  - Metric VUS-PR (a range-aware PR area) on MSL, SMAP, SWaT, TAO.
- **Relation to OAT.** Same family: one-class reconstruction with an NCDE, scored per point. SDA2D adds a derivative-reconstruction term, motivated by anomalies that "produce too little reconstruction error" because they alter dynamics, not values. That is OAT's App. H miss (latent reasoning errors look like success steps).
- **Map.**
  - (c) Add `‖f(z_t) Δy_t − pred‖²` as a second term to the OAT score.
  - (d) Evaluate with a range-aware metric: SearchAuditBench tolerance spans `[k_s, k_e]`; ±k on Who&When.
  - (f) Offline spline; window-mean initial state leaks the future.
- **Supervision.** L1-selected.
- **Code.** github.com/ProEcho1/SDA2D.

#### E2. Precursor-of-Anomaly detection (Jhin, Lee, Park; KDD 2023; arXiv:2306.15489)
- **Mechanism (arXiv HTML).**
  - Two co-evolving NCDEs over non-overlapping windows. One classifies "window `i` contains an anomaly". The other predicts "window `i+1` will contain an anomaly" from data up to `i`, trained by distillation from the first.
  - Self-supervised: anomalies are synthesised by resampling normal training data; true labels are used only at test.
  - MSL, SWaT, WADI with 30–70% of observations dropped.
- **Map.**
  - (a) Step embeddings.
  - (b) Successes plus *synthetic* failures, e.g. step deletion, swap, or observation corruption: the "corrupt" interventions of P1 applied offline, without re-execution.
  - (c) `P(error within the next w steps | prefix)`.
  - (d) Lead time vs AgentRx `k_lock` and FaP `t_lock` (FaP needs re-collected Terminal-Bench traces with step text).
  - (f) Synthetic perturbations differ from natural errors (the injected-position skew in brief §1).
- **Supervision.** L1-selected plus synthetic negatives.
- **Code.** github.com/sheoyon-jhin/PAD.

#### E3. NCDE vs LSTM for user anomaly detection on logs (Jurišić, Tomičić, Bernik; *Signals* 7(4):59, DOI 10.3390/signals7040059; abstract-level verification only)
- **Mechanism.** NCDE and LSTM predictors on CERT 4.2/6.2 insider-threat event logs. Prediction-error signals feed a downstream classifier. On CERT 6.2 the NCDE reaches F1 0.364 vs LSTM 0.133, attributed to steadier error signals on sparse, irregularly timed events.
- **Map.** The only verified NCDE application to *event logs*. It supports using real event times (TRAIL span timestamps) rather than `t/T`.
- **Supervision.** L0/L1.
- **What breaks.** Event-level construction of the path is not described in the abstract [unverified].

### F. Signature toolbox

#### F1. Signature kernels: Király & Oberhauser (JMLR 20(31), 2019; arXiv:1601.08169); Salvi, Cass, Foster, Lyons, Yang (SIAM J. Math. Data Sci. 2021, DOI 10.1137/20M1366794; arXiv:2006.14794)
- **Mechanism.** Sequentialisation turns any static kernel into a kernel on sequences via signature features; string kernels are a special case and alignment kernels are closely related. Salvi et al. compute the untruncated signature kernel as the solution of a Goursat PDE in the two paths' increments.
- **Map.**
  - (a) A static kernel on step embeddings combined with a kernel on step types.
  - Gives a kernel between whole trajectories or prefixes for D3, F3, F7 and for kernel nearest-neighbour baselines.
  - (f) Cost is quadratic in length (LongRCA 728 steps is fine; MemTrace graphs are not sequences).
- **Code.** github.com/crispitagorico/sigkernel.

#### F2. Embeddings for signatures (Fermanian; arXiv:1911.13211; published in CSDA 2021 per the repec record found in search [unverified]) and discrete iterated sums (Diehl, Ebrahimi-Fard, Tapia; Acta Appl. Math. 2020; arXiv:1906.05823)
- **Findings.** Fermanian: the embedding choice drastically changes accuracy, and lead-lag is consistently the strongest. Diehl et al.: time-warping invariants of discrete series are exactly iterated sums of increments (quasisymmetric functions).
- **Map.** The principled *discrete-event* control path:
  - one channel per step type or agent, holding cumulative counts;
  - signature levels = counts of ordered (non-contiguous) sub-sequences of step types;
  - add a time / index channel.
- **What breaks [derivation].** Warping invariance means that, without a time channel, repeated identical steps and stalls are invisible. Repeated `h_t = h_{t+1}` also gives a zero increment to OAT's CDE. "Step repetition" is a MAST failure mode, so the index channel is mandatory.

#### F3. Signature MMD two-sample test (Chevyrev & Oberhauser; JMLR 23(176), 2022; arXiv:1810.10971)
- **Mechanism.** Robust signature moments characterise the law of a stochastic process. They give an MMD on laws of paths, kernelisable with the signature kernel, and a non-parametric two-sample test.
- **Map (diagnostic).**
  - (b) L1: compare the law of prefixes `τ_{≤k}` of failed vs successful runs of the *same* tasks (AgentHallu clean vs failed; HORIZON; replay collections).
  - (c) The first `k` at which the test rejects is a population-level detectability horizon. If it is not reached before the median `k*`, no prefix monitor can work on that dataset.
  - (f) Population-level only, not per trajectory; the task-difficulty confound must be controlled by pairing on task.

#### F4. Higher-order kernel mean embeddings and filtration MMD (Salvi, Lemercier, Liu, Horvath, Damoulas, Lyons; NeurIPS 2021; arXiv:2109.03582)
- **Mechanism.** Embeds the conditional law of a process given its filtration. Gives a higher-order MMD that detects differences the standard MMD misses (same marginal law, different information flow), plus adapted conditional-independence tests.
- **Map (L1+).**
  - (b) Rollouts from each prefix.
  - (c) Distance between the conditional law of the future given `τ_{≤k}` and given `τ_{≤k+1}`. A jump at `k` means step `k` changed what can still happen, a kernel analogue of the repair-effect profile `e_τ(k)`.
  - (d) TraceElephant SWE-Agent replay subset, tau2-bench, Aegis re-runs; target `k*` (exact) and P1 fragility curves.
  - (f) Expensive (many rollouts per prefix); estimates are noisy at N ≈ 5–10.

#### F5. Distribution regression on expected signatures (Lemercier, Salvi, Damoulas, Bonilla, Lyons; AISTATS 2021; arXiv:2006.05805)
- **Mechanism.** Labels attach to *groups* of streams. A feature model and a kernel model on expected signatures, both universal; robust to irregular sampling.
- **Map (P1-T1 at L1+).**
  - Bag = the N continuations sampled from prefix `τ_{≤k}` (optionally with intervention `δ`); label = their empirical success rate.
  - The model learns `p̂(τ_{≤k}, δ)`; then `e(k) = max_δ p̂_δ − p̂_0` without re-execution at test time.
  - (d) TrajErrBench (replayable), AgentErrorBench ALFWorld/WebShop.
  - (f) Needs a data engine; bags are small.

#### F6. Conformance / variance-norm anomaly detection on streams (Cochrane, Foster, Lyons, Perez Arribas; arXiv:2006.03487 v1, June 2020) → SigMahaKNN (Shao, Chan, Cochrane, Foster, Lyons; same arXiv id, v2, Dec 2023)
- **Mechanism [paper].**
  - The variance norm `‖x‖_μ = sup_{Cov(φ,φ) ≤ 1} φ(x)`, which is infinite off the span of the corpus.
  - Conformance `dist(x; μ) = inf_{y ∈ supp μ} ‖x − y‖_μ`, applied to signature features.
  - Calibration: split the corpus in half, read off the scale `R` from in-corpus distances, and treat conformance `r + R` as anomaly `r`.
  - Invariant to affine maps of the features. PenDigits AUC 98.9%, vessel traffic 89.1%, 19/28 UCR wins over a shapelet method.
  - v2 (SigMahaKNN): dimensionless, invariant to reparametrisation and to concatenation of streams.
- **Map. The training-free baseline for OAT.**
  - (a) Expanding-window signatures of `(t, h_t^{PCA≤8}, step-type counts)`, lead-lag embedded.
  - (b) Corpus = successes (MCP-Atlas as OAT; AgentHallu clean; HORIZON judged successes; replay-collected).
  - (c) Per-step score `c_t = conf(τ_{≤t}) − conf(τ_{≤t−1})`, the increment in non-conformance, or conformance of a sliding window ending at `t`. The corpus split gives a threshold with the same meaning as OAT's conformal `δ`.
  - (d) Who&When top-3 / AUROC (with CORAL as OAT), AgentHallu step, MP-Bench nDCG@5.
  - (e) First-3 0.36, position-only AUROC 0.60, OAT 0.45 / 0.76.
  - (f) Whole-stream method, so per-step scores come from differencing, which is noisy. The off-span infinity is a hard novelty signal that fires on any OOD trajectory. Same OOD problem as OAT: needs CORAL or in-domain successes.
- **Supervision.** L1-selected.
- **Code.** pip `signature_mahalanobis_knn` (github.com/datasig-ac-uk/signature_mahalanobis_knn, MIT).

#### F7. Novelty detection on path space (Gasteratos, Jacquier, Lemercier, Lyons, Salvi; arXiv:2512.03243, Dec 2025)
- **Mechanism.** Novelty detection as a hypothesis test with signature statistics. Transportation-cost inequalities give false-positive tail bounds, quantiles and p-values beyond the Gaussian case (laws of RDE solutions). Expected-signature formulas for a smooth CVaR give one-class SVMs. Type-II error lower bounds.
- **Map.** Per-prefix p-values `p_t` for "τ_{≤t} is drawn from the success law". Feed them to a sequential test whose false-alarm probability is controlled *per trajectory* (OAT's conformal controls only pooled steps).
  - (d) AgentRx `k_lock` lead time; Who&When `k*`.
  - (f) The bounds assume RDE-type laws; LLM-embedding paths have no such guarantee.
- **Supervision.** L1-selected.
- **Code.** Not linked [unverified].

#### F8. Online regime-change detection with signature MMD (Issa & Horvath; arXiv:2306.15835, 2023)
- **Mechanism.** A path-wise two-sample test (signature-feature MMD) between recent small batches and a reference, tuned for reactivity. Regime clustering on top. Finance data.
- **Map (P2-U2, L0).**
  - (a) Step embeddings plus step types.
  - (b) No labels: within a trajectory, compare the windows before and after `t`; across trajectories, pool pre-change windows to learn `q_0`.
  - (c) `k̂ = argmax_t MMD(window_{<t}, window_{≥t})` or the first threshold crossing.
  - (d) Who&When / TraceElephant / MP-Bench `k*` (exact, ±1), AgentRx `k_lock`.
  - (e) Position prior, relative positions 0.40–0.47 on these sets.
  - (f) Short trajectories (Who&When median 10, AgentHallu 6) leave windows of 2–5 steps. The test has no power there; it suits LongRCA / TraceElephant / TrajErrBench SWE-Pro (117 messages).
- **Supervision.** L0.
- **Code.** Not linked [unverified].

#### F9. Quickest detection with rough-path signatures (Wang & Chakraborty; arXiv:2607.22958, July 2026)
- **Mechanism (arXiv HTML).**
  - Pre-change and post-change dynamics are independent geometric rough paths; the observed path is their concatenation at a random `θ` (Chen's identity gives the concatenated signature).
  - Under Bayesian delay plus false-alarm costs, the optimal rule is `τ_l = inf{t : |⟨l, Ŝig_{0,t}⟩| ≥ 1}`: the first hitting time of a half-space by a linear functional of the time-augmented signature. It is adapted, i.e. online.
  - `l` is fitted by zeroth-order stochastic approximation over truncated-signature coefficients.
  - Bounds: delay `≤ g^{-1}(1+δ)` with probability `≥ 1 − ε`, and `P(τ < θ) ≤ ε`. A distributionally robust version exists.
  - Comparable to CUSUM/Shiryaev for Brownian paths, better for fractional Brownian paths.
- **Map (P2-U3, the cleanest learned monitor).**
  - (a) Time-augmented, lead-lag signatures of `(h^{PCA≤4–8}, step type)` up to `t`.
  - (b) Fit `l` on trajectories with known `θ = k_lock` (AgentRx L2, 73 public) or with an outcome-only surrogate loss (L1: stop late on successes, early on failures).
  - (c) Alarm time `τ_l`.
  - (d) Lead time `k_lock − τ`, false alarms on successes, AgentRx; FaP `t_lock`/`t_obs` once traces are re-collected on Terminal-Bench.
  - (e) "Alarm at a fixed relative position" and the FaP prompted monitor (82% precision, 18% recall, median lead 0).
  - (f) Theory needs independent pre/post paths. Agent errors are path-dependent: the post-change regime depends on what went wrong. Few labelled `k_lock`.
- **Supervision.** L2 (small) / L1.
- **Code.** Not linked [unverified].

#### F10. Signature Isolation Forest (Campi, Staerman, Peters, Matsui; arXiv:2403.04405, 2024–25)
- **Mechanism.** Functional isolation forest with signature-based splits, replacing the fixed dictionary and linear inner product.
- **Map.** Whole-trajectory scores on successes vs failures; per-step use only via sliding windows. Low priority: an ensemble alternative to F6.
- **Supervision.** L1-selected.

#### F11. Sequential path-signature networks for per-post change detection (Tseriotou, Tsakalidis, Foster, Lyons, Liakata; Findings ACL 2023, DOI 10.18653/v1/2023.findings-acl.310) and the Sig-Networks toolkit (Tseriotou et al.; EACL 2024 demos; arXiv:2312.03523)
- **Mechanism [paper].**
  - For each post or utterance `d_i`, build its *causal* history `H_i` from the `w` most recent data points (or `n` shifted units of `w`).
  - SWNU: conv-1d, then an LSTM over signatures of locally expanding windows, then signature pooling. Seq-Sig-Net: a BiLSTM over SWNU units.
  - Concatenate the SBERT embedding of the current point and classify it.
  - Tasks: Anno-MI counselling (change / sustain talk per utterance), Longitudinal Rumour Stance switch / no-switch per post (325 conversations, 5,568 posts), mood changes in social-media timelines.
  - Anno-MI macro-F1: Seq-Sig-Net .525, BiLSTM .518, FFN-history .520, BERT .519.
- **Map. The closest existing task to per-step attribution: per-element labels on a sequence of text embeddings, with causal history.**
  - (a) Step embeddings plus step type.
  - (b) L2 training on the sets with splits: TracerTraj train/test, Who&When Pro (12k injected), CORRECT-Error.
  - (c) Per-step `P(error | history)`.
  - (d) Natural test sets: Who&When, TraceElephant, MP-Bench (nDCG@5), TRAIL (span set-F1).
  - (e) Position prior. A *supervised* position-only model trained on the same split (relative position, step type) is required, because injected training sets carry a late-position prior (Who&When Pro 0.83, CORRECT 0.95).
  - (f) The signature layer adds under 1 F1 point over a BiLSTM on Anno-MI. The value here is the causal per-element design, not the signature.
- **Supervision.** L2.
- **Code.** pip `sig-networks`, github.com/ttseriotou/sig-networks, github.com/datasig-ac-uk/nlpsig.

### G. Counterfactual NCDEs (for P1)

#### G1. TE-CDE (Seedat, Imrie, Bellot, Qian, van der Schaar; ICML 2022; arXiv:2206.08311)
- **Mechanism.** A controlled differential equation over the latent trajectory of an irregularly sampled patient history estimates potential outcomes under time-varying treatments at any time. Adversarial training balances time-dependent confounding. Tumour-growth simulator.
- **Map (P1-T1, L1+).**
  - (a) Prefix path of step embeddings.
  - Treatment = intervention `δ` at step `k` (oracle action, hint, fix-observation, corrupt-output; brief §6); outcome = re-rolled success.
  - (b) Replay data: TraceElephant SWE-Agent subset, tau2, ALFWorld/WebShop, Aegis injector at temperature 0.
  - (c) `p̂_δ(τ_{≤k})`, hence `e(k)` and fragility curves `r(k/T)`.
  - (d) TrajErrBench `k*` (exact) and correlation of `e(k)` with re-executed effects.
  - (f) Confounding by *where* interventions were tried; the balancing assumptions are untested on text agents; expensive data.
- **Code.** Not on the arXiv page [unverified].

### H. Adjacent: closest LLM-trajectory work and agent applications

#### H1. Step-level first-error detection via hidden-state transport geometry (Alvarez & Baheri; arXiv:2605.13772, May 2026)
- **Mechanism.** One forward pass; a label-conditioned teacher builds a trace-specific contrastive-PCA projection and scores each step with seven geometric transition features; a BiLSTM student is distilled to run without labels. ProcessBench, PRM800K, HaluEval, TruthfulQA.
- **Why it matters.** It is not an NDE paper. Its abstract reports that the student "collapses under shift" while the teacher transfers. That is the same OOD fragility OAT patches with the gate and CORAL.
- **Map.** A per-step hidden-state geometry baseline (L2 teacher) for AgentHallu / AgentErrorBench.

#### H2. Agent and robot NCDE applications
- **PINCoDE** (Sural, Kekeh, Liu, Pecora, Benosman; arXiv:2510.00401; NeurIPS 2025 listing found in search): physics-informed NCDEs forecasting 10 to 100 robots. ADE below 0.5 m at 1 minute; 2.7× lower pose error at 4 minutes with curriculum.
- **The IJCAI-25 NDE survey** (Oh et al.; arXiv:2502.09885).
- Neither addresses failure localisation. No paper was found that applies NCDEs or signatures to LLM-agent traces other than OAT (searches on 2026-10-30: NCDE + agent / LLM / robot failure; signatures + LLM hidden states; signatures + process mining / event logs).

**Tooling.** Signatory (Kidger & Lyons; ICLR 2021; arXiv:2001.00706): GPU signatures and log-signatures. The signature survey (Lyons & McLeod; EMS Surveys, arXiv:2206.14674).

## Ranked recommendations

Effort: **S** = days, runs on data already downloaded. **M** = 2–4 weeks or needs successes from a replay collection. **L** = needs rollouts per prefix. Gains are hypotheses to test, not results.

| # | Method | Benchmark(s) | Target label | Supervision | Expected gain over OAT / position prior | Effort | Risk |
|---|---|---|---|---|---|---|---|
| 1 | **OAT ablations from this lineage:** (i) gate-only score `‖(1−q)⊙dX/du‖`; (ii) Morrill parametrisation `s_i = i` instead of `t/T`; (iii) Hermite-backward and linear interpolation instead of the natural cubic spline; (iv) predict-before-ingest innovation | Who&When (OOD, as OAT), AgentHallu (in-domain successes available) | `k*` | L1-selected | Decides whether the gate, the spline look-ahead, or the CDE carries the 0.76 AUROC. Expect (i) to retain most of the OOD gain and (iii)/(iv) to lose some in-domain AUROC but become valid online | S | Low. OAT code is not released, so it must be reimplemented from Eq. 4–13 |
| 2 | **SigMahaKNN conformance** on expanding windows, corpus = successes (F6) | Who&When (+CORAL), AgentHallu, MP-Bench | `k*`; nDCG@5 | L1-selected | A training-free reference. If it matches OAT, the CDE is unnecessary. Must beat first-3 0.36 / position-AUROC 0.60 | S | Per-step scores by differencing are noisy; off-span infinities on OOD data |
| 3 | **Causal filter monitor**: GRU-ODE-Bayes / NJ-ODE / rectilinear NCDE, per-step NLL, CUSUM threshold (C2, C3, A2), trained once on successes and once on all runs | AgentRx (`k_lock`), AgentErrorBench (ALFWorld/WebShop successes by replay), TrajErrBench tau2 | `k_lock`, critical step | L1-selected vs L0 | Gives the lead-time metric OAT cannot report. The successes-vs-all-runs contrast directly tests the selection hypothesis | M | Early errors (AgentErrorBench median relative position 0.23) leave little prefix |
| 4 | **Signature quickest-detection rule** `τ_l` (F9) with `l` fitted on `k_lock` or by an outcome surrogate | AgentRx; FaP after re-collection | `k_lock`, `t_lock` | L2 (73 traces) / L1 | Interpretable linear monitor with a per-trajectory false-alarm bound; baseline FaP prompted monitor (median lead 0) | M | Tiny labelled set; theory assumes independent pre/post regimes |
| 5 | **Signature-MMD change point** within a trajectory (F8) | TraceElephant, TrajErrBench SWE-Pro, LongRCA | `k*` | L0 | The only fully label-free option here; useful as the U2 baseline. Expected near the position prior on short sets | S–M | No power on trajectories under 15 steps |
| 6 | **Conditional flow NLL** (D5/D7) on a causal NCDE context, quantile-NLL objective | AgentHallu, MP-Bench | `k*`; graded `E` | L1-selected | OAT's own future-work item; may fix the "too little reconstruction error" miss (App. H) if errors change dynamics more than values | M | Density in 64 dims from about 700 steps; needs PCA ≤ 16 |
| 7 | **SDA2D-style derivative term** added to the OAT score (E1) | Who&When, SearchAuditBench | `k*`, tolerance span | L1-selected | Targets the latent-reasoning misses; range-aware evaluation on SearchAuditBench spans | S | Same offline spline; may only add the gate's signal twice |
| 8 | **Sig-Networks causal per-step classifier** (F11) trained on injected sets | train TracerTraj / Who&When Pro → test Who&When, TraceElephant, MP-Bench | `k*`, `a*` | L2 | Supervised ceiling for this representation; must beat a supervised position+step-type model | S–M | Injected late-position prior transfers as a shortcut |
| 9 | **NRDE / Log-NCDE** on long traces (A3, A4) | LongRCA, MemTrace | earliest root step / faulty op | L0/L1 | Makes 145–728-step traces tractable; localisation only to window resolution | M | 40% human exact agreement caps measurable gains |
| 10 | **Expected-signature regression / TE-CDE / filtration MMD** as P1 surrogates (F5, G1, F4) | TrajErrBench, AgentErrorBench, TraceElephant SWE replay | `e(k)` profile, `k*` | L1+ | Learns `p̂_δ(prefix)` so attribution needs no re-execution at test time | L | Rollout cost; confounding of intervention placement |

## Open gaps

1. **No causal, non-degenerate one-class NCDE detector exists.** SDA2D, GDFlow, PoA and OAT all use offline splines or window-level encoders, and all reconstruct (or classify) data that is inside their own control path. The filtering models (C1–C3) have the right structure but have not been used for anomaly *localisation* in any paper found.
2. **No discrete-event control path.** NCDEs assume real-valued channels sampled from a continuous signal. Agent steps are marked events: agent id, step type, tool name, exception flag, plus free text. Nobody has published a jump or rectilinear control for marks; the iterated-sums signature (F2) and Neural Jump SDE (C4) are the nearest pieces. TRAIL's span *trees* have no path model at all; DFS order equals chronological order there, but the parent–child structure is lost.
3. **No per-observation likelihood in the NCDE family.** An NCDE gives a state, not a density. CTFP and conditional CNFs give one only under continuous-path assumptions that a tool-call → observation jump violates.
4. **Localisation within a sequence is rare.** The signature anomaly methods (F6, F7, F10) score whole streams. Change detectors (F8, F9) return one time and assume homogeneous regimes and long segments. None outputs an error *set* `E`, a tolerance span, or a responsible agent, and none is evaluated with a range-aware metric except SDA2D's VUS-PR.
5. **False-alarm control at the wrong level.** OAT's conformal step controls the pooled per-step false-positive rate under exchangeability of steps, which within-trajectory dependence and position effects violate. The quickest-detection and novelty-testing results (F7, F9) control per-trajectory false alarms but only for RDE-type laws. No method gives coverage for the decisive step itself (see `fa_ideas_review.md` C3).
6. **Position confounds are not modelled.** `f(v, z)` with `v = t/T` hands the model relative position. No NCDE anomaly paper reports a position-only baseline. Every experiment here must report first-k, random-k and position-AUROC alongside.
7. **Reparametrisation invariance vs "pace" signals.** Signatures and CDE solutions are invariant to time warping (F2), so stalls, loops and repeated identical steps are invisible without an explicit time or index channel. These are failure modes in MAST, and FaP's tail behaviour. Gating `dX/du` (OAT) breaks the invariance in an uncontrolled way, through `T`.
8. **No attribution from an outcome-trained NCDE.** An NCDE classifier trained on `S` (L1) has a natural attribution: the adjoint `∂ŷ/∂X` along the path, a path-integrated gradient. I found no paper that evaluates this as event localisation. It is a cheap L1 experiment on AgentHallu and replay collections.
9. **The success-selection premise is untested in this literature.** Every one-class NCDE / signature detector assumes a clean normal corpus. Successful agent runs contain recovered errors (2.3 per 22.8 steps on Terminal-Bench, brief §1), so the "normal" law already includes errors. That favours change-point or hazard formulations over pure one-class conformance.

### Sources (all checked 2026-10-30)
arXiv: 2005.08926, 2106.11028, 2009.08295, 2402.18512, 2405.20799, 2109.01876, 2204.08771, 2301.04333, 2602.02157, 1907.03907, 1905.12374, 2006.04727, 1905.10403, 2110.13040, 2001.01328, 2102.03657, 2305.16274, 2402.14989, 1810.01367, 1806.07366, 2002.10516, 2409.05346, 2306.15489, 1601.08169, 2006.14794, 1911.13211, 1906.05823, 1810.10971, 2109.03582, 2006.05805, 2006.03487 (v1 and v2), 2512.03243, 2306.15835, 2607.22958, 2403.04405, 2312.03523, 2206.08311, 2605.13772, 2510.00401, 2502.09885, 2001.00706, 2206.14674, 2607.12747 (OAT). DOIs: 10.1609/aaai.v40i30.39770 (SDA2D), 10.3390/signals7040059 (Jurišić et al.), 10.18653/v1/2023.findings-acl.310 (Tseriotou et al. 2023), 10.1137/20M1366794 (Salvi et al. 2021).
