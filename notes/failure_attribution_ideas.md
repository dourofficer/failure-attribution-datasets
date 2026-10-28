# Ideas for Failure Attribution Mined from the `papers/` Corpus

*Compiled 2026-10-27. Target problem: step/agent/category attribution for failed LLM-agent trajectories, as defined in the 21-dataset survey at `/dataDisk/home/thanhdo/failure-attribution-datasets/report/` (Proposal 1 = interventional repair-effect profile via replay rollouts; Proposal 2 = outcome-supervised step-hazard model, levels L0/L1/L1+/L2).*

**How this was produced.** All 54 PDFs in `papers/` were read end to end. Seven directly relevant papers (OAT, Progress Advantage, Hide-and-Seek, UQ-in-Agents, PQM, SpikeScore, Cyclical Entropy Eruption) were read by the coordinator; the other 47 were split into seven thematic batches (A–G) read by parallel reader agents under one shared brief. The full per-paper reports (mechanism, idea cards with section references, quotable facts, code availability) are in `notes/ideas_reports/` (files `CORE.md`, `A.md` … `G.md`, ~320 KB). This file is the consolidated, deduplicated, ranked view. Idea codes refer to the report files (e.g. `A4.1` = batch A, paper 4, card 1; `CORE` ideas are named). On 2026-10-27 it was cross-checked against an independent pass over the same papers (`/dataDisk/home/thanhdo/fa_ideas/`, 9 files); the ideas adopted from it carry codes `X1`–`X13` and are detailed in `notes/ideas_reports/X_fa_ideas.md`, and the full comparison is in `notes/fa_ideas_review.md`. Two factual points from that pass changed existing cards: OAT arXiv v1 contains no one-class density baseline (our earlier "F1 0.41" figure has no source), and positional baselines on Who&When are strong (first-3 hit 0.359, random-3 0.286, position-only AUROC 0.602 vs OAT top-3 0.451 and gated-OAT AUROC 0.758); see `X0` in the X report.

**Supervision vocabulary.** L2 = step labels; L1+ = outcomes of several continuations of the same prefix; L1 = outcome label only; L0 = raw logs. Grey-box = needs log-probs or hidden states of an open model (self-collected runs, or released logs re-encoded by a proxy open model — see idea 2 below, which makes most grey-box ideas applicable to released data).

---

## 1. Top 15 ideas (ranked by plausibility × leverage)

| # | Idea | Source | Supervision | Relation to proposals | Plaus. | Effort |
|---|------|--------|-------------|-----------------------|--------|--------|
| 1 | **Progress advantage = zero-cost estimate of the interventional effect.** A*(s,a)=Q*−V* from log π_RL/π_ref is, by definition, the "effect of this action vs the policy's average action" — the same object as Proposal 1's φ with δ = resample. Validate PA against rollout-measured p₀/φ in replayable envs; then use it as the surrogate f and as the hazard model's input sequence. | Progress Advantage (CORE) | L0 (needs checkpoint pair; cross-policy scoring works) | Links P1 and P2 | 5 | M |
| 2 | **Proxy-model re-encoding of released text logs.** Teacher-force released trajectories (TraceElephant, SymFail, MemTrace, AgentHallu, LongRCA) through an open 7–14B model to get per-token NLL/entropy/attention/hidden states. Proxy–generator token-NLL correlation 0.83–0.98 (HalluEntity App. B); OAT and LUMINA both work with proxy models. Prerequisite for every grey-box idea on released data. | HalluEntity, LUMINA, OAT (A2.1) | L0 | Infrastructure for both | 5 | S–M |
| 3 | **Ranking-with-margin loss for the attributor (PQM).** Train the step scorer so every step before t* outranks steps at/after t* by margin ζ, with internal order after t* unconstrained — handles "later steps are also wrong but we don't know which". Q* = P(success \| prefix) is exactly P2's survival function and P1's p₀; PQM's 32-rollout Monte-Carlo Q is P1's screen. | PQM (CORE) | L2 or L1+ | Strengthens both | 5 | S–M |
| 4 | **Candidate-step annotation + partial-label distillation; hazard model as the student.** Set-valued labels are already native (MP-Bench votes, SearchAuditBench tolerance spans, t_err/t_lock/t_obs). Prompt attributors/humans for *all plausible* steps (one call beats 40 self-consistency samples), distil with the candidate-renormalised target; survival likelihood with a set S is Σ_{t∈S} h_t∏(1−h_s). | CanDist (D7.1, D7.2) | L0 + LLM candidates, or L2-set | Strongest L2-set path for P2 | 5 | M |
| 5 | **Distance-aware listwise step ranker (first + second-order Plackett–Luce).** Candidates = steps, relevance = continuous distance (index distance, annotator votes, or 1−φ from P1), LoRA'd LLM + value head; yields exact/±k/nDCG natively; second-order term teaches "how much closer". | GeoRanker (G7.1) | L2 / L1+ | Consumer of P1's profile | 5 | M |
| 6 | **MIL contrastive objective (inter-trajectory max-contrast + intra-trajectory onset-contrast) as the L1 alternative to the survival MLE.** Onset proxy argmax_t(s_t−s_{t−1}) lands within 0.01 of oracle onset with no temporal labels; uniform label propagation costs −19 bACC. Same encoder as P2 U1 → direct comparison on AgentHallu / HORIZON / FaP. | Hide-and-Seek (CORE) | L1 | Alternative/ensemble for P2 | 5 | S |
| 7 | **Capture/retention scan: exact, judge-free step labels for memory-loss failures.** For agents with explicit textual state, scan 1(gold fact ∈ state_t): capture failure / retention failure (t* = overwrite step) / reasoning failure; thousands of natural-position failures from released code; trivially replayable repair (re-insert the fact). Also a ground-truth testbed for the hazard estimator (per-update loss hazard ∝ 1/H). | Multi-Head Memory (F5.1, F5.2) | L1 + gold | Testbed for both | 5 | S |
| 8 | **Observation-utilisation score per step (LUMINA): MMD between next-token distributions with the real vs a swapped same-type observation, plus the logit-lens "information-processing rate".** Low E (ignored tool output) / high I (fabricated arguments) → when + a 2-D "what" signature; two forward passes, proxy-model compatible. | LUMINA (A4.1); kin: observation-ablation Δ_t (B4a), context-integration point (A6.1), core-evidence knockout (A7.1), blanked re-decode flag (A6.2) | L0 | Execution-free surrogate for P1's δ="different observation"; covariate for P2 | 4 | M |
| 9 | **PU / mixture-proportion estimator: P(step is error) from a success-vs-failure step discriminator corrected by a KL-matched error proportion.** Steps of successes = clean cell; failed-run steps = mixture; closed-form posterior η(x)=1−(β/α)(n_s/n_f)·odds(κ(x)); identifiability = anchor-set condition (always-good steps exist). Also per-role proportions → "who" without step labels. | UDA with unobservable subpopulation (C8.1, C8.2) | L1 | Strengthens P2 (identifiability + bounds) | 4 | S–M |
| 10 | **Per-step DPO implicit reward from success/failure trajectory pairs (grey-box L1 step scorer).** Pair failed and successful runs of the same task, train DPO + λ·SFT on successes (SFT term prevents likelihood collapse of both sides); β·Σ log π_θ/π_ref over agent tokens of step t gives a credit profile; generator becomes a 79.6% discriminator without discriminator training. Caveat from DPO theory: on-policy bad steps start deep in the non-flippable regime (margin bound log 3) → use a reference that did not generate the trajectory or an embedding Bradley–Terry head. | CodeLutra (E4.1), DPO diverse-values (D1.1) | L1 | Alternative L1 estimator for P2 | 4 | M |
| 11 | **Committee-vote cleaning of human step labels; remove, don't flip.** Members = prompted attributors of different families, seed-ensembles of step scorers, P1's rollout effect, P2's hazard model; flag labels a majority out-ranks by margin; remove flagged trajectories; measure cleaning precision/recall on injected-label-noise versions of exact-label sets. | PrefCleanBench (D4.1, D4.2) | L2 (+L1+) | Decision rule for P1's label comparison | 4 | M |
| 12 | **Verifier-gated dense reward (HERO) for RL-trained attributors.** With natural step accuracy at 10–30%, most GRPO groups are all-miss (zero gradient). Stratify by the sparse verifier (exact/within-span), min-max normalise a dense proxy (distance, φ) *within* each stratum; dense negatives matter most; weight prompts by rollout-score variance. | HERO (E1.1, E1.2) | L2 or L1+ | Consumes P1's φ | 4 | M |
| 13 | **Dual-accuracy / abstention evaluation on paired clean runs.** A judge counts only if it localises t* in the failure AND says "no decisive error" on a matched success; failure-only benchmarks never penalise always-blaming. Successes exist in AgentHallu, HORIZON, FaP, TRAIL. | UPD, OOD survey (B2a, C1.2) | eval only | Exposes P(fail\|prefix) false alarms | 4 | S |
| 14 | **Gradient-projection acquisition: which steps to label (L2) or roll out (L1+).** Train a small head on success-run steps; score failed-run steps by squared projection of their centred gradient on the top singular direction; top-k beats entropy/margin/random and saturates at ~1k labels. Turns P1's O(T·N) screen into a budgeted screen. | OOD with human feedback (C2.1) | L1 → L2/L1+ | Budget for both | 4 | M |
| 15 | **Judge-free consensus over N sampled attributions (ModeX) + departure-from-consensus curve over sibling rollouts.** Spectral mode over n-gram similarity of (step, agent, category, rationale) beats an LLM judge selecting among the same N; cluster size = confidence. Sibling-rollout degree curve d_t = density of the failed run among its siblings' step-aligned prefixes → first sustained drop = t_err candidate (L0/L1). | ModeX (E5.1, E5.2, E5.3) | none / L1 | Orthogonal; reuses P1's rollouts | 4 | S–M |

### Additions from the `fa_ideas` cross-check (codes X1–X13; cards in `notes/ideas_reports/X_fa_ideas.md`)

| Code | Idea | Source | Supervision | Relation to proposals | Plaus. | Effort |
|---|------|--------|-------------|-----------------------|--------|--------|
| X1 | **Outcome-trained value curve V_t ≈ P(success \| prefix) with a martingale / TD(0) consistency loss ("hazard with recovery").** Decisive = largest drop, lock-in = ε-crossing, recovery = rise; removes P2's absorbing assumption (FaP PASS runs have 2.3 recovered errors each); testable claim: the largest drop sits at t_lock, not t_err. | Debate-or-Vote, PQM, UQ-in-Agents | L1 (+L1+) | Generalises P2; same loss trains P1's surrogate | 5 | M |
| X2 | **Contrastive OAT.** Fit the step-dynamics predictor on successes and on failures of the same tasks; score r_t = e_t^succ − e_t^fail. Tests whether outcome information is step-local; OAT is the one-class degenerate case. | OAT | L1 | Direct test of the purple-note question | 4 | S |
| X3 | **Wild-step filtering done right**: residualise reader activations (role, step type, position, length) before the SVD, bag-constrained positives, first-passage decoding, outcome-only hyperparameter selection; plus a one-day subspace-alignment diagnostic that tells whether the SAL/HaloScope family can work on reasoning errors at all. | VLMGuard | L0/L1 | L0/L1 initialiser for P2 | 4 | S–M |
| X4 | **FA-CleanBench**: rule validity filters tied to dirty rows in our notes, seed-ensemble margin, judge committee (remove, never relabel), register-leak probe for injected sets, and replay at k = t_inj as a label auditor giving measurable cleaning precision/recall. | PrefCleanBench, SDR | L2 / L1+ | P1 as label auditor | 4 | M |
| X5 | **Conformal risk control for decisive-step coverage**: smallest top-score set S with P(t* ∈ S) ≥ 1−α, calibrated on a small labelled set on top of success-calibrated false-flag control; set size vs coverage on MP-Bench / AgentRx / TRAIL. | OAT, Hide-and-Seek | L2 (small) | Wraps any P2 scorer | 4 | S |
| X6 | **Knowledge-edit injection**: AlphaEdit one wrong leaf fact into an open agent; fluent on-policy errors at natural positions; editing one agent's weights gives an exact who; twin-run divergence + repair rollout as ground truth. | KnowledgeSmith | L2 by construction | Natural-position training data | 3 | M–L |
| X7 | **Missing-cell correction** for injected→natural: tabulate (error × position × role); PU learning with the prior pinned by "one decisive step per failure" where injected data has no cell; label-shift reweighting elsewhere; generate the source on the same replayable systems. | UDA unobservable subpopulation | L1 + injected | Operationalises #9 against Fig. errpos | 4 | M |
| X8 | **Self-adversarial, on-manifold, causally verified injection**: adversary picks step + fault, the agent's own model realises it, roll forward, realism filter, rollout causality check, hard buffer; adversary chooses k to defeat position shortcuts. | UniGame | L1+ by construction | Yields P1 repair-effect labels for free | 3–4 | L |
| X9 | **Judge identity-bias test**: rerun with anonymised and permuted agent names; Attribution-IBC; "blame the modal agent" baseline. | Identity-Skews-Debate | eval only | Problem 6 diagnostic + free debiased judge | 4 | S |
| X10 | **LRU suspect-memory streaming attributor** for long traces (H = 4–8 note heads, stage-wise update). | Multi-Head Recurrent Memory | none | LongRCA / TRAIL | 3 | S |
| X11 | **Relevance-conditioned who-rule**: relevant observation + wrong step → blame consumer; distracting → blame retriever. Black-box. | RAG representations | none | Problem 6 | 3 | S |
| X12 | **"Failure to withhold" error class** (AAD / IVQD / IASD subtypes) with a solvability probe; decisive step = the commit. | MM-UPD | L0 + judge | Extends B2a/B2c | 3 | M |
| X13 | **Three-way active labelling** {correct-unusual, symptom, decisive} with the annotator simulated from AgentRx / FaP, and **symptom-shift noise curves** (move t* to the symptom step). | OOD-with-HF, PO-noisy-feedback | L1 → L2 | Budget for both; teaches cause vs symptom | 3 | M |

---

## 2. All ideas by theme

Each entry: **name** — mechanism → mapping; datasets; risk. (plausibility/effort, source).

### 2.1 Per-step signals from model internals (grey-box, L0)

- **Progress advantage per step (argmin of per-step reward)** — rivals AgenTracer on Who&When Hand-Crafted with no training; aggregation (MEAN/MIN vs MAX/MEAN) matters and can be *learned* from outcome labels; TIES-merged intermediate references sharpen the signal (beat both endpoints for α in 0.2–0.7). Cross-policy scoring (Gemma pair scoring Qwen trajectories, AUROC 0.75) makes it a universal text-only baseline for all 21 datasets. Readouts: argmin per-step advantage = decisive step; argmin of the running sum = lock-in; negative-advantage mass per agent = *who* (testable on Who&When, Aegis, MP-Bench). Risk: released logs come from GPT-4o. (5/S, CORE-PA; readouts from fa_ideas)
- **Observation-side value shock δ_t = V(s_t) − E[V(s_{t+1})]** — the residual PA cannot recover in a stochastic MDP is exactly the tool/user-side surprise; with V from P2's survival function, sign/size of δ_t at the labelled step gives the *fault side* (model vs observation) that MegaRCA-Mix, AgentRx "User" blame and SearchAuditBench's excluded environment failures need. (3/M, CORE-PA)
- **OAT reconstruction error as a hazard covariate; propagation-decay decoding** — OAT scores decay along error-propagation chains (origin > inherited); decode t* as the start of the first peak-then-decay run rather than argmax. Mean pooling ≫ last token; later layers better; CORAL alignment for OOD. (4–5/S, CORE-OAT)
- **OAT is a t_obs detector, not a t_err detector** — it fires where failure is verbalised and misses latent early reasoning errors (App. H: "such statements can appear in successful trajectories"); use FaP's three timestamps to measure which timestamp each estimator targets. **Correction:** OAT v1 reports no one-class density baseline; its ablations are CDE vs ODE, gate (+0.172 OOD AUROC, the whole OOD gain), CDE vs RNN (small gap, figure only). Mandatory controls for any OAT-style result: k-matched random-3 (0.286 on Who&When), first-3 (0.359), position-only AUROC (0.602 ≈ ungated OAT), and a last-k-masked variant. (4/M, CORE-OAT; X0)
- **Contrastive OAT** — X2: success-fit minus failure-fit residuals on matched tasks (FaP, AgentHallu). (4/S, X2)
- **Observation-ablation sensitivity Δ_t = log p(a_t \| with o) − log p(a_t \| o ablated)** — ≈0 means the action did not depend on the evidence; earliest such step whose observation contradicts the prior = candidate t*; two passes, no rollout. Conjoin with "the observation mattered". Design rules (fa_ideas F2.2/C5.2): mask the top-attended or gold-matched evidence span, never the whole observation and never a random span (VAUQ: core mask ≈ ground-truth mask > blank > random); mask all copies of a redundant fact; build the observation-influence matrix M[t, s] and read it backwards from the symptom step as provenance; faithful use of a *wrong* upstream message routes blame upstream (who). (4/S–M, B4a; kin A6.2 blanked re-decode, L0, black-box possible)
- **Context Integration Point / Total Context Integration** — layer-wise cosine chain between prompt with and without the observation block; group steps label-free by whether greedy output changes; post-integration-layer distance correlates with correctness (0.72 vs 0.15 pre-layer in the LVLM case). Needs length-matched placeholder, not deletion. (3/M, A6.1)
- **Core-evidence knockout (VAUQ)** — attention-select top-K observation tokens from mid layers, knock out, measure entropy gain; confident outputs whose confidence does not depend on evidence are flagged; the selected spans give an evidence chain (step t relied on step j's observation) = cheap who/when link. (3/M, A7.1)
- **Claim-grounding score (GLSim)** — global (claim-span state vs last-context-token state) + local (claim vs top-K evidence tokens by logit lens) similarity for each factual claim in a step; high-global/low-local = plausible-but-unsupported. Attention grounding is the weakest option (−12 AUROC). Also as-is for GUI/screenshot agents (TraceElephant screenshots, Who&When Pro GUI). (3/M, B1a, B1b)
- **Attention-propagated step scores (Focus over steps)** — own uncertainty on key tokens (tool names, args, numbers) + γ·attention-weighted scores of attended earlier steps; reading the propagation matrix backwards from t_obs gives a mechanistic t_err→t_obs chain. (3/M, A2.2)
- **Last-prompt-token drift monitor** — cos(h(prefix), h(prefix minus newest observation)); spikes precede abstention/retry mode (t_obs with lead time); runs of ≈0 across repeated tool calls = not updating on observations (stuck loops). (3/M, A5.1)
- **Steering vector + OT pseudo-labels (TSV)** — one 4K-param vector at an early-middle layer separates error/clean steps with 32–64 labelled steps (+28 AUROC over raw-embedding probes); outcome-derived bag marginals (successes = all clean; failures ≥1 error) replace exemplars (L1). Risk: error prior ~1–2% vs 15–50% in the paper. (4/3, M, A1.1, A1.2)
- **Unlabelled-mixture subspace bootstrapping (VLMGuard)** — error steps as rare contamination (π≈0.01–0.03): centre, SVD, projection energy, pseudo-label top quantile, train MLP (classifier tolerates 75% false pseudo-positives). L1 variant: mean-difference direction FAIL-steps vs PASS-steps. Last token > mean pooling; summing layers hurts. **Upgraded by X3**: residualise nuisance (role, step type, position, length) first, bag-constrained positives, first-passage decoding, outcome-only model selection, and run the subspace-alignment diagnostic before building anything; never run it on Who&When Pro / Aegis (injector style is the top direction). (3 L0 / 4 L1, M, B5a, X3)
- **Feature-resonance score** — fit one linear layer by MSE pulling success-run step embeddings to a random vector; score failed-run steps by one-step representation movement at the mid-training epoch (low movement = off the good-step manifold); needs only outcome labels, computable per dataset (no transfer); beats kNN/Mahalanobis in the source. (4/M, C3.1)
- **Judge-free "effective relevance" (EMI/CLUB)** — pointwise log q(z_action \| z_context) − log q(z_action) with q fit on successful (context, action) pairs; hallucinated / ignore-error / loop steps score low; 138× cheaper than a judge. Risk: validated at dataset level only. (3/M, C6.1)
- **Sparse-expert (MxD) activations as probe features; divergence-horizon under internal perturbation as a lock-in probe** — low plausibility, large effort; included for completeness. (2/L, G1.1, G1.2)
- **Caution — raw policy representations do not separate success from failure** (Cyclical Entropy Eruption Fig. 3): correct and wrong agent trajectories overlap in last-layer mean-pooled states, more than in other LLM tasks; a SEAL-style outcome head reshapes them. Two uses: SEAL-trained policies as data-engine agents (already outcome-separated states), or SEAL head as pre-training of the hazard encoder, then MIL/survival loss fixes temporal structure. (4/M, CORE-SEAL)

### 2.2 Learning from outcome labels only (L1, L1+)

- **Survival/hazard MLE (Proposal 2) ↔ PQM theory** — Q_σ(prefix) = P(success \| prefix); Theorem 3.5 gives the monotone shape (descends on wrong steps, ascends on correct, large gap at first error); fit h_θ from rollout-estimated Q with the comparative loss instead of MSE. (4/S, CORE-PQM)
- **Value curve with martingale consistency ("hazard with recovery")** — X1: V_θ from outcomes with TD(0)/martingale loss; largest drop = decisive, ε-crossing = lock-in, rise = recovery; h_t = 1 − V_t/V_{t−1} on monotone segments; validate against Monte-Carlo V_t on TraceElephant and FaP t_err/t_lock. (5/M, X1)
- **MIL inter/intra contrastive losses (Hide-and-Seek)** — see Top-15 #6. Also: functional conformal band from successful prefixes for the online monitor (per-trajectory false-alarm guarantee); report TWA and lag to t_lock. Numbers: onset proxy within ±0.016 of the annotated onset while the peak lags by +0.07 to +0.11 (App. C.1); test rise-vs-peak on LongRCA (root-to-end median 48 steps). The hardest false positive in a success is a recovered slip, the data that teaches decisive-vs-first-error (AgentRx: root ≠ first failure in 27%). (5/S, CORE-H&S)
- **PU mixture-proportion estimator** — Top-15 #9; operationalised as the missing-cell correction X7 (tabulate error × position × role; PU where injected data has no cell; label-shift reweighting elsewhere; source generated on the same systems). (4/S–M, C8.1, X7)
- **DPO implicit reward from paired runs** — Top-15 #10. (4/M, E4.1)
- **Outcome-variance weighting and graded-failure targets** — weight hazard-likelihood terms at prefix k by a bounded sigmoid of rollout-outcome variance p_k(1−p_k) (transition region is where t*/t_lock live); where outcomes are graded (WebShop reward, test fraction), PASS/FAIL fixes the stratum and the graded score orders within FAIL. Stratify, don't blend (naive weighted sums destabilise). (3/S, E1.2)
- **Action-type-conditional hazard** — UQ-in-Agents' gating: information-gathering/clarifying actions reduce uncertainty, commit actions (writes, final answers) propagate it; make h_t depend on an action-class covariate (read/ask/think/write/answer; FaP's action codes exist); predicts human labels concentrate on commit steps (lock-in). (4/S, CORE-UQ)
- **Pressure / retry / length covariates for the hazard** — deception rate rises monotonically with pressure level and with number of supervisor-rejected attempts (r=0.72); add prior-failed-attempt count, explicit negative feedback, authority-style instructions, time since last verified success as covariates; hazard is non-stationary and spikes after such events. (3/S, F4.3)
- **Latent-space pair synthesis (LENS) for a step reward model from ~100–500 labelled trajectories** — contrastive VAE on frozen (prefix, step) embeddings, synthesise 4–8× pairs within-trajectory, Bradley–Terry MLP; embedding-MLP ≈ full fine-tuning at 1k pairs; also works with L1+ pairs from rollouts; report retained-ordering rate under an oracle (rollout effect) before training. (4/M, D5.1, D5.2)
- **Small task-specific attributor as pseudo-labeller for unlabelled failures** — a 125M task-specific model labelled better than prompted GPT-4 in the source; our prompted attributors are at 10–30% step accuracy, so a trained small scorer (or P2's L1 hazard model) as teacher → pseudo step labels → bigger student. Weak-model errors are systematic and benign, random flips are not. (4/M, D6.1)
- **Entropy-gated combination of per-benchmark attributor experts (DaWin)** — fine-tune one LoRA expert per labelled set, combine per trajectory by exp(−entropy) (output ensemble, selection, or weight interpolation); cheapest route from several in-domain attributors to one cross-domain attributor. Risk: entropy over T candidates confounded by length. (3/S–M, C5.1)
- **IB bottleneck (Vittle) when fine-tuning the attributor for cross-framework robustness** — separate posteriors over observation vs agent tokens at ~75% depth; LoRA/weight decay were the wrong regularisers for shift. Risk: compression may discard exact tokens attribution needs. (3/L, C7.1)
- **Outlier-anchored calibration (DOR)** — keep the fine-tuned attributor's score distribution on unlabelled steps from *other* frameworks close to the pre-fine-tuning model; low plausibility because the base attributor is not well calibrated. (2/M, B3)

### 2.3 Label noise, scarce labels, set-valued labels (L2)

- **PQM margin-ranking loss** — Top-15 #3.
- **Candidate-set annotation + partial-label distillation** — Top-15 #4; plus "ask for all plausible steps once" as a one-line change to every prompted baseline, reporting recall@|S| and nDCG. Per-dataset candidate sets (fa_ideas C1): Aegis → all steps of the labelled agent; injected sets → [t_inj, first symptom] plus the agent; MP-Bench → vote-weighted union; FaP → [t_err, t_lock]; LongRCA / Who&When → t̂ ± k from the human-agreement window. Stratify small-loss selection by position bin and agent role to avoid collapse onto the last-step / orchestrator prior; the same sets prune P1 screens. (5/M; 4/S, D7.1, D7.2)
- **Listwise distance-aware ranker** — Top-15 #5; plus **oracle-in-top-k diagnostic**: for any cheap screener (prompted top-10, hazard top-k, surprisal spikes) compute the fraction of trajectories with t* in the top-k, separating candidate-generation from selection error; then screen-then-rerank (rollouts only on k steps). (4/S, G7.2)
- **Distribution-matching attributor (LAD)** — train the attributor/surrogate so its distribution over steps matches softmax(φ/η) or the annotator vote histogram instead of collapsing to the symptom step; outputs a calibrated ranked list. Trade-off against exact-step accuracy must be shown. (3/M, E2.1)
- **Committee-vote cleaning, remove-don't-flip; seed-ensemble reward-gap detector** — Top-15 #11; made concrete as FA-CleanBench X4 (rule validity filters, register-leak probe, replay audit with measurable precision/recall). (4/M; 3/S, D4.1, D4.2, X4)
- **Conformal risk control for decisive-step coverage** — X5. (4/S, X5)
- **Disagreement-source audit** — code MP-Bench split votes and human-vs-LLM disagreements into: mislabel / missing context / different criterion (earliest vs proximate vs lock-in) / different threshold / several independent errors / not attributable. In the HH study 66% of low-agreement items were criterion/threshold mismatch, not mistakes — if so here, the exact-step ceiling is a *definition* problem that P1's interventional definition removes. Add "no decisive step / multiple" to any new protocol. (4/S–M, D3.1)
- **Treat annotator disagreement as ambiguity (ω) noise, not random flips** — vote-weighted soft targets; adjacent-step splits are benign for ±k; drop 1-1-1 items; early stopping as the robust regime. Add symptom-shift noise curves (X13): move t* to the symptom step, plot natural-test accuracy vs ε by trace length and backbone. (3/S, D2.2, X13)
- **Noise-tolerance budget from embedding separation** — measure separation of (prefix, error step) vs (prefix, clean step) embeddings under the chosen encoder; with per-dataset flip rate ε from agreement, the finite-step theory predicts the accuracy-vs-N curve and whether plain BT/DPO or a noise-robust loss is needed. (3/S, D2.1)
- **Attributor self-consistency as ambiguity detector** — k=10 samples; consistency predicts human disagreement (validate on MP-Bench); stratify benchmark accuracy into ambiguous vs subtle. (4/S, D6.2)
- **Pairwise step comparisons + Bradley–Terry** — "which of steps i, j is more responsible?" on screened pairs → graded strength γ_k with CIs; CI width flags ambiguous trajectories; feeds the listwise ranker. (3/M, G8.2)
- **Per-mode sample budget Q ∝ log K and orthogonality pre-check** for the "what" head — low value. (2/S, D1.2)

### 2.4 Interventions, replay and data generation (Proposal 1 side)

- **PA ≈ advantage ≈ φ** — Top-15 #1.
- **Instability under induced continuations (SpikeScore)** — branch K short LLM-only continuations from the prefix at a candidate step (no tool execution: re-derive/justify/continue), score curvature (max second-order difference) of a probe along them; erroneous steps yield unstable branches; cross-domain by construction; restrict to hazard-model candidates. (3/M, CORE-SpikeScore)
- **Unsolvable-observation injection on successful runs (UPD's AAD/IASD/IVQD for tools)** — delete the needed fact / return a well-formed irrelevant result / return another tool's output at step k, replay; t_err = k by construction, position-uniform (unlike Who&When Pro/Aegis skew), failure mode "evidence missing"; agent reaction categorised abstain/retry vs fabricate vs ignore. (4/M, B2b)
- **Bottleneck-test δ family: δ_read vs δ_decide** — append the correct extraction of the observation vs the correct action; which one repairs gives the category (perception/observation-misreading vs reasoning/planning); neither → error is earlier. (3/M, B2c)
- **Consensus step as δ (ModeX centroid of siblings' step-k outputs)** — judge-free, always available in replayable envs; zero effect when the policy's mode is itself the error separates idiosyncratic from systematic failures. (3/S, E5.3)
- **Goal–detail repair search with accept-if-improves replay (SDR)** — decompose δ into a coarse repair goal from the taxonomy (re-plan, fix args, insert verification, correct fact, hand off…) screened with 2 rollouts each, then LLM-refined details accepted only if success rate improves; the winning goal is the "what" label; "no δ improves success ⇒ k is not an error step" as the null. (3/M–L, G5.2)
- **Self-adversarial, on-manifold, causally verified injection (UniGame)** — X8 supersedes the earlier B6 card (rated 2): adversary picks step + fault type, the agent's own model realises it, roll forward, realism filter, rollout causality check, hard buffer, adversary chooses k. (3–4/L, X8, B6)
- **Knowledge-edit injection (KnowledgeSmith)** — X6: edit one wrong leaf fact into an open agent's weights; fluent on-policy errors at natural positions; exact who in a MAS. (3/M–L, X6)
- **Martingale-residual attribution** — under the null "communication carries no information" V_t = E[success \| F_t] is a martingale; decisive step = largest negative increment of rollout-estimated V (δ = resample from the agent's own policy); differs from oracle-fix φ exactly when the agent is systematically wrong at k — a clean split between "agent incapability" and "unlucky error". (3/M, F1.2)
- **MAD-oracle freeze as an exact, ~free repair testbed** — in multi-agent debate on MCQ, freezing an agent at the gold answer at (agent, round) and replaying gives the full repair-effect profile per trajectory for cents; natural error-position distribution; train the surrogate f on thousands of exact profiles before moving to coding/web environments. (4/S, F1.1)
- **Hierarchy-stratified repair footprint (KnowledgeSmith)** — stratify φ by plan-level / subgoal / action-level steps; add a footprint metric (fraction of downstream steps whose content changes after the fix) and a residual-symptom metric; tests "early planning errors are decisive". Risk: level confounded with position. (3/M, G3.1)
- **Anonymisation replay** — re-prompt the acting agent with identity labels stripped (orchestrator's own plan as "an opinion", specialist without role name) and continue; positive effect ⇒ failure carried by the identity channel (deference/obstinacy), a category assigned by intervention. Restrict to critic/verifier steps. (3/M, F2.2)
- **Pressure-event injection with known trigger but emergent, displaced error (LH-Deception)** — inject an *incentive* (deadline, authority instruction, missing data) at task index t_trig into verifiable coding/search streams; the failure emerges at t_err ≥ t_trig with the supervisor's first trust drop as t_obs; three timestamps per failure, natural displacement (12.6% of deceptive rounds occur several turns after the trigger), same seed replays across models. (4/M, F4.1)
- **Eruption-phase checkpoints as a natural-failure generator** — during agent-RL entropy eruption, policies emit repetition (MAST FM-1.3), hallucination, format errors at elevated but on-policy rates; sample failures from these checkpoints with the pre/post-eruption pair as a built-in PA reference. (3/M, CORE-SEAL)
- **Anchor synthetic injection on label-free natural candidates (RSL)** — inject at the positions/kinds that low-resonance natural candidates exhibit, rather than at arbitrary k; counters the position skew of released injected sets. (3/M, C3.2)
- **Capture/retention scan testbed** — Top-15 #7; information-survival hazard as identifiability test for P2 (geometric survival with rate ∝ 1/H as the parametric reference). Caveat (verified): under exact match the gold answer appears in the failed Who&When history for under 10% of trajectories (7/96 ours, 13/145 fa_ideas), so the scan targets MemTrace, SearchAuditBench and LongRCA, not Who&When. (5/S; 4/M, F5.1, F5.2)

### 2.5 Multi-agent propagation and "who"

- **Conformity / Obstinacy / Subversion cells as per-role features** — tag each orchestrator step after a disagreeing worker message as adopt-wrong (over-reliance), adopt-right (correction), keep-wrong-own (obstinate error), keep-right-own; turns two MAST coordination modes into measurable events; subversion events are two-candidate cases (originator vs adopter) where humans and the counterfactual may systematically disagree — measurable on MP-Bench. (4/M, F2.1)
- **Pólya-urn propagation model** — fit DCM parameters (α per role, identity weights w) from logs; gives an analytic lock-in round (absorption), per-(agent, round) influence shares of the final wrong majority (Shapley-like "who" without rollouts), and P(fail \| prefix) from the current answer histogram. Categorical answers only; soft counts untested. (3/M, F2.3)
- **Role-conditioned mixture proportions** — per-role error-step proportion by distribution matching failed vs successful runs (L1) → responsibility prior; combine with per-step posterior for "who". (3/S, C8.2)
- **Judge identity-bias test (Attribution-IBC)** — X9: anonymised and permuted agent names on existing judges; quantifies the role-name prior in "who". (4/S, X9)
- **Relevance-conditioned who-rule** — X11: relevant observation + wrong step → consumer; distracting → retriever. (3/S, X11)
- **Observation-side surprise as the environment-fault feature** — estimate U(O_i \| A_i, E_i) with a separate world-model LLM predicting the next tool/user output; surprising observation + ordinary action = environment/tool-side fault (SymFail's 377 failed tool results, AgentRx User blame). (3/M, CORE-UQ)
- **Restatement-sufficiency test (Visionary-R1 caption reward)** — where an agent restates a tool output before acting (web-surfer→orchestrator, SWE test-log summaries), check whether a frozen LM makes the same decision from the restatement as from the raw observation; disagreement flags lossy hand-offs: when + who (the summariser) + what. (4/S–M, B7)
- **Supervisor state (trust/satisfaction/comfort) as an online monitor** — LLM supervisor with bounded memory emits three states per step; first trust drop = online t_obs; compare lead time against post-hoc auditor t_err. (3/S–M, F4.2)
- **Memory-write steps must be candidates** — MetaMind's failure traces show the decisive error as a hallucinated memory write whose symptom appears two rounds later; self-validation scores (0.93 on a bad response) are not usable as attribution signals. (evidence, F3)

### 2.6 Online monitoring, calibration, t_obs / t_lock

- **Functional conformal monitor (Hide-and-Seek)** — time-varying band from successful prefixes; TWA and lag metrics. (5/S)
- **Label-free calibration via base-model agreement (DACA)** — fit temperature of the monitor/judge's Yes/No probability by KL to an open *base* model on prefixes where both agree (post-trained models are over-confident, base models calibrated); works for API judges; single global τ cannot fix length-dependent miscalibration. (3/S, A3.1)
- **Conflict/reverse probe battery as symptom detector** — extract atomic claims the agent relies on at step k, auto-generate direct/reverse/conflict probes, ask the replayed agent; conflict-rate spike = t_obs; localises hallucination vs stale state. (3/M, G3.2)
- **Reframe the 21 datasets as the missing turn-level agent-UQ benchmark** — only 4/44 agent benchmarks are turn-level; evaluate calibration of P(fail \| prefix) *at t** and lead time, not only exact step. (4/S, CORE-UQ)
- **Three-timestamp evaluation of estimators** — report distance to t_err, t_lock, t_obs separately (OAT → t_obs, hazard → t_lock, humans → t_err). (4/M, CORE-OAT)
- **"Failure to withhold" error class with a solvability probe** — X12: AAD / IVQD / IASD subtypes; decisive step = the commit, often before the final answer. (3/M, X12)
- **Paraphrase-consistency / entropy-trajectory diagnostics** — paraphrase the last observation, re-sample the next action m times, dispersion marks unstable decision points; cheaper cousin of L1+ rollouts. (3/M, G6.2)

### 2.7 Evaluation protocols, benchmark hygiene, infrastructure

- **Dual accuracy on paired clean runs** — Top-15 #13. (4/S, B2a, C1.2)
- **Mandatory positional controls** — k-matched random-k, first-k, last-k, position-only AUROC, last-k-masked variant; on Who&When first-3 = 0.359 and position-only AUROC = 0.602 already match ungated OAT. (5/S, X0)
- **LRU suspect-memory streaming attributor for long traces** — X10. (3/S, X10)
- **Three-way active labelling** {correct-unusual, symptom, decisive} — X13; the same selector chooses P1 rollout sites. (3/M, X13)
- **Leave-one-dataset-out (GHD protocol)** — train on one, test on the pooled rest; report Δ = in-domain − cross-domain. (5/S, CORE-SpikeScore)
- **Stratify by error sparsity and position; prefer AUPRC** — error steps are ~1% of steps; likelihood-based monitors have rising FNR late in sequences while error rate also rises late (HalluEntity 9%→36%). (5/S, A2.3)
- **Evaluate on prior-consistent vs prior-contradicting observations** — uncertainty-based detectors collapse exactly when the observation contradicts the model's prior (entropy AUROC 83→48 on counterfactual images); partition error steps by whether the triggering observation agrees with the blanked-decode prediction. (4/S, A7.2)
- **Surface-perturbation invariance** — perturbed twins (rename tools, re-serialise JSON, paraphrase messages, translate); report agreement of t*/agent/category with the original. (4/S, C7.2)
- **Testable-implication checks before trusting an internal signal (LUMINA's H1–H4 style)** — e.g. observation-utilisation should be higher right after a tool call than on planning steps; correlate with rollout effects. (4/S, A4.2)
- **Layer-wise separability sweep as a feasibility map** — coarse mismatch (garbage tool output) separates by mid-layers; plausible-but-wrong observations never fully separate → route those categories to interventional methods; read mid-layers, not final. (3/S, A5.2)
- **Diagnose the cross-benchmark gap as low-level vs concept-level vs incomplete-concept shift** (CONDA) before adapting; JS-divergence bound on step embeddings as a label-free predictor of transfer gaps (EMI). (3/S, C4.2, C6.2)
- **Failure taxonomy as a concept bottleneck with residual concepts + source-free adaptation** — interpretable "what" head; residual concepts surface modes the taxonomy lacks; limited by pseudo-label quality. (3/M, C4.1)
- **Contamination audit (KDS) of Who&When / MAST / TRAIL for every open attributor; laundering-aware variant (SDR) over log renderings** — Who&When is small and widely re-posted; anchor λ=0 with fresh post-cutoff trajectories. (4/S–M; 3/M, G4.1, G5.1)
- **Pairwise-preference arena for attributors with style-controlled Bradley–Terry** — judges compare two attributions (step, agent, category, justification); regress out length/list/header effects (β_length = 0.526 in GeoArena); expert re-judging with replay access; validate votes against replay-based labels. (4/M, G8.1)
- **Unified attribution harness** — dataset adapters to one schema (set-valued labels with votes, t_err/t_lock/t_obs, mapped taxonomy, replayability flag), attributor adapters to one output (ranked steps, agent, category, P(fail \| prefix)), shared metric library with bootstrap CIs. (4/M–L, G6.1)
- **Order-preservation QA for any manufactured training data** — score synthetic/pseudo-labelled pairs with the best oracle available (rollout effect, MP-Bench majority) and report retained ordering before training. (4/S, D5.2)
- **Do not label preference pairs with an LLM judge when a verifier/replay exists** — execution-labelled pairs 48.2 vs GPT-4-labelled 27.8 (CodeLutra); judge-over-16 below single path (ModeX). (evidence, E)

---

## 3. Resolution of the open note in `8_proposals/futureworks.tex`

The purple note asks why the agent's own policy would assign high probability to its mistakes. Two corpus results answer it directly:

- Cyclical Entropy Eruption, §3.3 and Fig. 3/5: correct and wrong agent trajectories "exhibit substantial overlap rather than forming clearly separated clusters" in the policy's representation, and the likelihood of *correct* trajectories decreases during agent RL because of gradient interference from similar wrong ones. Mistakes are ordinary, high-likelihood actions under the policy.
- Progress Advantage, Fig. 3: raw policy log-probability *penalises* correct tool-call strings and policy-relevant terms; only the contrast with a reference policy makes likelihood informative.

Three further pieces (from the fa_ideas pass, verified against the texts):

- UQ-in-Agents Tab. 2: the agent's own NLL, entropy and verbalised confidence predict τ²-bench failure at AUROC 0.47–0.69, below chance for Kimi-K2.5 on Retail; the uncertainty curves of successful and failed runs overlap within 1 sd (Fig. 4, App. F.2).
- OAT App. H: the errors it misses are early latent reasoning errors, "because such statements can appear in successful trajectories".
- Debate-or-Vote Thm 2: under the system's own policy V_t = P(success | prefix_t) is a Doob martingale. An error is a step where V_t *drops*, not a low-probability action. The objection therefore holds for density models of all trajectories and does not apply to outcome-supervised hazard or value models (Proposal 2, X1), which only need the step to be outcome-predictive.

Conclusion for Proposal 2: likelihood under the agent's own policy is not a correctness signal; the informative objects are contrasts (policy vs reference, successful-flow vs observed, outcome-conditioned discriminators) and drops of the success-probability curve. This also explains why OAT must *select* successes rather than model all trajectories. Note for the LaTeX: the sentence next to the purple note attributes an "F1 0.41 one-class detectors" figure to OAT that is not in arXiv v1 (see X0); the argument should rest on the RNN gap and the gate instead.

---

## 4. What could start next week (small effort, high information)

1. **PA baseline across all 21 datasets** with one open checkpoint pair (Qwen3.5-9B / Base), argmin-step decoding, min-step aggregation; plus proxy re-encoding of TraceElephant/SymFail/AgentHallu to unlock per-token features (ideas 1, 2).
2. **Hide-and-Seek MIL vs survival-MLE vs OAT** on AgentHallu (443/250) and HORIZON with the same frozen encoder; score onset against Who&When exact step and FaP timestamps (idea 6).
3. **Candidate-set prompting** as a drop-in change to every prompted baseline; report recall@|S|, nDCG, and coverage of the human step (idea 4, D7.2).
4. **Dual-accuracy + leave-one-dataset-out + position/sparsity-stratified AUPRC** added to the survey's metric table (ideas 13, §2.7).
5. **PQM-style margin-ranking loss vs BCE** for a step scorer trained on Who&When Pro / TracerTraj / CORRECT-Error, tested on Who&When / TrajErrBench (idea 3).
6. **Capture/retention scan** on MemTrace's 160 cases to check how many are retention vs capture failures and whether the human step matches the overwrite step (idea 7).
7. **Contrastive OAT** (X2) with a GRU predictor on AgentHallu (443/250) and Failure-as-a-Process matched tasks, scored against the X0 positional controls, with and without the last 3 steps masked.
8. **Identity-bias test** (X9) and the positional-control battery (X0) on every prompted judge we already run on Who&When / Aegis / MP-Bench; prompting only.
9. **Subspace-alignment diagnostic** (X3, 1b) on Who&When / TRAIL / AgentRx reader embeddings: does the error-mean-difference vector lie in the top-k wild subspace at all?

---

## 5. Paper → ideas index

| Paper | Ideas (codes) | Zero-idea? |
|---|---|---|
| OAT (Yeh et al. 2026) | CORE: decay decoding, t_obs estimator, hazard covariate, CNF q₀; X0 positional controls, X2 contrastive OAT, X5 conformal risk control | |
| Progress Advantage (Oh et al. 2026) | CORE: PA≈φ, PA tokens → hazard, δ_t fault side, universal baseline | |
| Hide-and-Seek (Park et al. 2026) | CORE: MIL losses, functional CP, anti-uniform-label evidence | |
| UQ in LLM Agents (Oh et al. 2026) | CORE: observation surprise, action-conditional hazard, turn-level benchmark framing; Tab. 2 evidence for the purple note | |
| PQM (Li & Li 2025) | CORE: margin-ranking loss, Q*=survival | |
| SpikeScore (Deng et al. 2026) | CORE: continuation instability screen, leave-one-out protocol | |
| Cyclical Entropy Eruption (Li, Im, Li 2026) | CORE: representation-overlap caution/SEAL, eruption checkpoints, resolves the note | |
| TSV | A1.1 steering vector, A1.2 OT with outcome marginals, A1.3 span localiser | |
| HalluEntity | A2.1 proxy re-encoding, A2.2 Focus over steps, A2.3 sparse/position evaluation | |
| DACA | A3.1 label-free calibration | |
| LUMINA | A4.1 observation utilisation, A4.2 implication checks | |
| RAG internal representations | A5.1 drift monitor, A5.2 layer separability map; X11 relevance-conditioned who-rule | |
| Language prior / chain-of-embedding | A6.1 context integration, A6.2 blanked re-decode flag | |
| VAUQ | A7.1 evidence knockout, A7.2 prior-contradicting split | |
| GLSim | B1a claim grounding, B1b GUI perception | |
| Unsolvable Problem Detection | B2a dual accuracy, B2b unsolvable-observation injection, B2c bottleneck δ family; X12 failure-to-withhold class | |
| Miscalibration in prompt tuning (DOR) | B3 outlier-anchored calibration | |
| Multimodal ICL lags | B4a observation-ablation Δ_t, B4b late-layer evidence attention | |
| VLMGuard | B5a subspace bootstrapping, B5b pseudo-label denoising; X3 residualised wild-step filtering + diagnostic | |
| UniGame | B6 learned observation adversary → X8 causally verified self-adversarial injection | |
| Visionary-R1 | B7 restatement sufficiency | |
| Generalized OOD survey | C1.1 AD framing with anomaly prompts, C1.2 dual accuracy | |
| OOD learning with human feedback | C2.1 gradient-projection acquisition, C2.2 covariate-vs-semantic relabelling; X13 three-way active labelling | |
| Feature resonance | C3.1 resonance score, C3.2 anchored injection | |
| CONDA | C4.1 taxonomy concept bottleneck, C4.2 shift diagnosis | |
| DaWin | C5.1 entropy-gated expert combination | |
| EMI (MLLMs under shift) | C6.1 effective relevance, C6.2 JS bound | |
| Vittle | C7.1 IB bottleneck, C7.2 perturbation invariance | |
| UDA unobservable subpopulation | C8.1 PU posterior, C8.2 role proportions; X7 missing-cell correction | |
| DPO diverse values | D1.1 non-flippable on-policy pairs, D1.2 log K budget | |
| PO under noisy feedback | D2.1 noise budget from separation, D2.2 ambiguity noise; X13 symptom-shift noise curves | |
| Position: data-centric alignment | D3.1 disagreement-source audit | |
| PrefCleanBench | D4.1 committee cleaning, D4.2 reward-gap detector; X4 FA-CleanBench | |
| LENS | D5.1 latent pair synthesis, D5.2 order-preservation QA | |
| Weak LLM teacher | D6.1 small pseudo-labeller, D6.2 self-consistency, D6.3 mismatch audit | |
| CanDist | D7.1 candidate distillation, D7.2 ask-for-all, D7.3 budget | |
| HERO | E1.1 verifier-gated dense reward, E1.2 variance weighting | |
| LAD | E2.1 distribution-matching attributor | |
| GEB | E3.1 optimism bonus (not recommended) | |
| CodeLutra | E4.1 per-step DPO reward, E4.2 iterative DPO attributor | |
| ModeX | E5.1 consensus, E5.2 sibling-departure curve, E5.3 consensus δ | |
| Debate or Vote | F1.1 MAD-oracle testbed, F1.2 martingale residual; X1 value curve with martingale loss; purple-note framing | |
| Identity bias in debate | F2.1 conformity cells, F2.2 anonymisation replay, F2.3 Pólya urn; X9 judge identity-bias test | |
| MetaMind | memory-write evidence only | ✓ |
| LH-Deception | F4.1 pressure injection, F4.2 supervisor monitor, F4.3 covariates | |
| Multi-Head Recurrent Memory | F5.1 capture/retention scan (Who&When caveat), F5.2 survival hazard testbed; X10 LRU streaming attributor | |
| MxD | G1.1 expert features, G1.2 divergence horizon (low) | |
| Gradient leading terms | — | ✓ |
| KnowledgeSmith | G3.1 hierarchy footprint, G3.2 conflict probes; X6 knowledge-edit injection | |
| KDS | G4.1 contamination audit, G4.2 kernel change-point (low) | |
| Data laundering (SDR) | G5.1 laundering-aware audit, G5.2 goal–detail repair search; X4 register-leak probe | |
| TorchUMM | G6.1 unified harness, G6.2 paraphrase diagnostics, G6.3 CMAM margin (low) | |
| GeoRanker | G7.1 listwise ranker, G7.2 oracle-in-top-k | |
| GeoArena | G8.1 attributor arena, G8.2 pairwise step BT labels | |
| `fa_ideas` pass (2026-10-26, independent) | X0 verified facts, X1–X13; comparison in `notes/fa_ideas_review.md` | |
