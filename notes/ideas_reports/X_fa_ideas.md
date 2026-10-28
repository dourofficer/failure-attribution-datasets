# Batch X: ideas adopted from the independent `fa_ideas` pass

*Added 2026-10-27.* Source: `/dataDisk/home/thanhdo/fa_ideas/` (README + `ideas_{0,A..F}_*.md`, compiled 2026-10-26, an independent reading of the same 54 papers under its own brief `FA_CONTEXT.md`). The comparison with our batches CORE/A–G is in `notes/fa_ideas_review.md`. Only ideas that are new or materially sharper than ours are given cards here; overlaps were merged into the existing cards of `notes/failure_attribution_ideas.md`. Numbers marked **[verified]** were recomputed by us from `data/` or from the extracted paper text.

Conventions as in the other batches: P1 = Proposal 1 (rollout screens, repair-effect profile), P2 = Proposal 2 (outcome-supervised hazard), levels L0/L1/L1+/L2.

---

## X0. Facts established by the pass (not ideas, but they change several cards)

- **OAT has no Isolation-Forest / OC-SVM / density baseline in arXiv v1 (2607.12747v1).** [verified: full-text search] Its ablations are CDE vs ODE (Fig. 3), gated vs ungated control path (+0.172 OOD AUROC, −0.028 in-domain; Fig. 4), CDE vs RNN next-step predictor (Fig. 5, figure only), and layer / pooling / proxy-LLM choices (App. G). Our CORE-OAT card and `notes/alternatives.md` cited "F1 0.411 vs 0.435" for one-class detectors; that number has no source in the paper. The argument "the signal comes from selection, not from the dynamics" still stands, but it must rest on the small RNN gap and on the gate carrying the whole OOD gain.
- **Positional baselines on Who&When (184 failures, `mistake_step` 0-based into `history`).** [verified]

  | Baseline | Hit rate |
  |---|---|
  | OAT top-3 (paper, Tab. 2) | 0.451 |
  | first 3 steps | 0.359 |
  | random 3 steps (k-matched) | 0.286 |
  | first step | 0.109 (paper 0.115) |

  Position-only ranking ("earlier = more anomalous") gives mean per-trajectory AUROC 0.602, above GPT-5 (0.584) and equal to ungated OAT (≈0.586); gated OAT's 0.758 is genuinely above it. Subsets: Algorithm-Generated (median 10 steps) first-3 0.516 vs random-3 0.360; Hand-Crafted (median 32.5 steps) first-3 0.017 vs random-3 0.125. Median relative error position 0.33; 36% of errors at steps 0–2. Every OAT-style result needs k-matched random, first-k, position-only AUROC, and a "last-k steps masked" variant (so failure verbalisation cannot be read as the symptom).
- **OAT's in-domain AUROC (0.629) is below its OOD AUROC (0.758)**, consistent with Who&When's early-error prior interacting with OAT's u = t/T time axis and query-initialised latent state. Proxy LLM embeddings (Llama-4-Scout, Gemma-4-31B, GPT-oss-120B) lose little (Fig. 10): the signal is content, not privileged internal state. Layer-0 embeddings score F1 ≈ 0.21, below random-step 0.255.
- **Capture check on Who&When.** [verified, our stricter replication] Under exact normalised string match the gold answer appears anywhere in the failed history for 7 of 96 usable trajectories (fa_ideas: 13 of 145 with a looser filter). Under 10% of Who&When failures are retention failures; the capture/retention scan (F5.1) applies to MemTrace, SearchAuditBench and LongRCA, not Who&When.
- **Extra evidence for the purple note** (why the agent's own policy gives high probability to its mistakes): UQ-in-Agents Tab. 2, the agent's own NLL / entropy / verbalised confidence predict τ²-bench failure at AUROC 0.47–0.69 (below chance for Kimi-K2.5 on Retail), and the uncertainty curves of successful and failed runs overlap within 1 sd (Fig. 4, App. F.2); OAT App. H, the misses are early latent reasoning errors "because such statements can appear in successful trajectories". Framing from Debate-or-Vote Thm 2: under the system's own policy V_t = P(success | prefix_t) is a Doob martingale, so an error is a step where V_t *drops*, not a low-probability action. The objection applies to density models of all trajectories; it does not apply to outcome-supervised hazard or value models, which only need the step to be outcome-predictive.

---

## X1. Outcome-trained value curve with martingale consistency ("hazard with recovery")
*Sources: Debate-or-Vote (martingale), PQM (ranking shape), UQ-in-Agents (negative evidence). fa_ideas A-group §4.1 and B-group A1.*

- **Mechanism.** Train V_θ(prefix_t) ≈ P(success | prefix_t) from outcome labels only, with (i) the terminal constraint V_T = outcome, (ii) a TD(0) / martingale consistency loss V_t ≈ V_{t+1} on all trajectories, (iii) optionally PQM's comparative margin loss where branch pairs exist. Readouts: decisive step t* = argmin_t (V_t − V_{t−1}) (largest drop); lock-in = first t with V_t < ε; recovered error = a drop followed by a rise. Confidence = size of the drop.
- **Why it matters for P2.** The discrete-time hazard is absorbing (no rises). Failure-as-a-Process PASS runs carry 2.3 recovered error events each, so absorption is false at step level. V_t generalises h_t: h_t = 1 − V_t / V_{t−1} on monotone segments, and rises are allowed elsewhere. The two label conventions become two summaries of one curve: t_err ≈ first step where V stops rising, t_lock ≈ the largest drop.
- **Testable claim.** The largest drop aligns with t_lock rather than t_err. Data: Failure-as-a-Process (t_err / t_lock), AgentRx (first-unrecovered convention), TraceElephant (measure the true p_0(k) by rollouts and check that V_θ reproduces it; this is PQM's Fig. 3 protocol with 32 rollouts per step).
- **Link to P1.** The drop V_{k−1} − V_k estimates −A^π(s_k, a_k) under the agent's own policy; the repair effect e(k) = max_δ p_δ − p_0 is Q(s_k, δ*) − Q(s_k, a_k). They coincide when the agent usually does the right thing at s_k. One model trained on screens can predict both; train P1's surrogate f(prefix, k, δ) with the same ranking loss.
- **Addresses** problems 1 (conventions), 5 (calibrated P(success) per step), 7 (stochasticity is built in).
- **Risk.** Long traces need chunked encoders; a value model trained on injected faults may learn the injection artefact; the martingale property assumes the scorer sees the same information as the policy.
- **Plausibility 5 / effort M.**

## X2. Contrastive OAT
*Source: OAT. fa_ideas A-group §1 idea 1.*

- **Mechanism.** Fit the same step-dynamics predictor (start with a GRU or linear AR, which OAT's Fig. 5 puts close to the CDE) separately on success and failure trajectories of the *same tasks*. Score each step by r_t = e_t^succ − e_t^fail (residual log-ratio), or train one predictor conditioned on the outcome bit.
- **What it tests.** If r_t beats e_t^succ, outcome information is step-local and the success-only reference is not all that matters; if it does not, OAT's one-class selection is the whole story. OAT is the degenerate case of the P2 likelihood with the failure term dropped.
- **Data.** Failure-as-a-Process (89 tasks × 21 systems, PASS + FAIL, t_err / t_lock), AgentHallu (250 successes, 443 failures). For TrajErrBench τ², generate successes by replay. Proxy embeddings suffice (OAT Fig. 10).
- **Controls.** The X0 positional baselines, plus the last-k masked variant.
- **Plausibility 4 / effort S.**

## X3. Wild-step filtering with residualisation, bag constraints and a go/no-go diagnostic
*Source: VLMGuard (+ SAL / HaloScope lineage). fa_ideas D-group §1 (1a–1c). Refines our B5a.*

- **Mechanism.** Reader-LLM step activations f_t (last token, prefix-conditioned, middle layers). (1) **Residualise** before the SVD: regress f_t on agent role, step type (tool call / observation / reasoning / final answer), relative position and log length, or run the SVD within role; otherwise the top directions are step type, VLMGuard's own "top directions encode style and length" failure. (2) **Bag constraint**: score wild steps (all steps of failed runs) by projection energy κ_t on the top-k directions; take the top-1 or earliest-above-quantile step per failed run as a positive; negatives are steps of successful runs plus steps well before the candidate. Train an MLP probe. (3) **Earliest-crossing decoding**: feed the probe score as the emission of P2's first-passage posterior P(t* = t | fail) ∝ h_t Π_{s<t}(1 − h_s), h_t = σ(a·g(f_t) + b), and fit a, b by outcome likelihood. (4) **Outcome-only model selection**: choose layer, k, and threshold by the AUROC of max_t score (last 2 steps masked) for separating held-out failed vs successful runs of the same tasks, keeping the method at L1.
- **One-day diagnostic first (1b).** On labelled data (Who&When, TRAIL, AgentRx) measure Δ = ‖μ_err − μ_corr‖ per layer and the fraction of the error-mean-difference vector that lies in the top-k principal subspace of the residualised wild embeddings. VLMGuard's Prop. 3.3 says separation needs rare contamination and a large Δ. A small alignment means the whole SAL / VLMGuard / HaloScope family is a dead end for reasoning errors, a useful negative result that answers the OAT question.
- **Do not** run the unsupervised filter on Who&When Pro or Aegis: the injector's style is an easy outlier direction (see X4's register probe).
- **Data.** Failure-as-a-Process (matched PASS/FAIL), AgentHallu, MP-Bench / TRAIL (set labels), Who&When for comparability.
- **Risk.** Decisive errors are near-OOD; the mean gap may be dominated by downstream symptom steps or by task difficulty, so the filter finds "failed-run-ness" rather than the error.
- **Plausibility 4 / effort S–M.**

## X4. FA-CleanBench: rule filters, seed-ensemble margin, judge committee, register-leak probe, replay audit
*Sources: PrefCleanBench, Data-Laundering (SDR). fa_ideas E-group §2 and §8b. Refines our #11 (D4.1).*

- **Rule validity filters** (free): the labelled agent speaks in the trace; the labelled step exists and belongs to the labelled agent; the injected step differs from the original; the run actually fails; the injection is not after the final answer; the final answer changes under injection. Known dirty rows in our notes: CORRECT-Error 8.4% agent/role mismatch and 43 rows pointing at the user message; AgentErrorBench 27 empty failure types and one label beyond the trajectory length; TracerTraj 21 tasks in both train and test.
- **Seed-ensemble margin** (RwGap analogue): 8 attributors with different seeds; m = score(labelled step) − max_{t≠label} score(t); drop the bottom p ∈ {10, 20, 30, 40}%.
- **Judge committee** (VoteMaj analogue): 4–6 LLM attributors plus a trained one; remove traces where the majority names a step outside ±k. **Remove, never relabel**: relabelling to a committee's choice bakes in the committee's symptom bias. PrefCleanBench's best filtering rate (20–30%) matched the known noise level.
- **Register-leak probe** (SDR): score each step by its likelihood ratio under the injector model vs the agent model (Min-K% or mean token confidence). If this finds the injected step well above chance *without reading the outcome*, the dataset has a style shortcut and an attributor trained on it learns "rewritten text", not errors. Mitigation: regenerate the post-injection continuation with the agent model, or style-equalise all steps with one paraphraser, then re-run the probe. Low power when injector and agent are the same family (GPT-4o).
- **Replay audit** (what preference cleaning cannot do): on TraceElephant and on injected traces with a clean source run, re-run from the prefix with the injection reverted (P1's intervention at k = t_inj). If success is not restored at rate ≥ p_min, the label is invalid. This gives true cleaning precision and recall per method.
- **Evaluation.** Downstream exact / ±k / set-F1 on natural human-labelled sets (Who&When, MP-Bench, TraceElephant, AgentRx) across backbones and objectives. Prediction: dropping 20–30% of injected traces beats adding the same number of uncleaned ones. Check the step-position distribution of the removed traces, since committees share the symptom-over-cause bias and may remove correct early-cause labels.
- **Plausibility 4 / effort M.**

## X5. Conformal risk control for decisive-step coverage
*Sources: OAT (success-calibrated FPR), Hide-and-Seek (functional bands), DOR. fa_ideas A-group §1 idea 3.*

- **Mechanism.** Keep the success-calibrated false-flag control, then add a conformal-risk-control layer calibrated on a small step-labelled set (MP-Bench consensus, AgentRx, TrajErrBench τ² where agreement is 91%) that outputs the smallest top-score set S with P(t* ∈ S) ≥ 1 − α. Works on any step scorer (hazard, X1 value drops, judges with a step distribution).
- **Output.** Set size vs coverage curves on MP-Bench, AgentRx, TRAIL. No FA method currently offers a coverage guarantee on the decisive step; OAT's guarantee is on in-distribution false positives only.
- **Caveats.** Exchangeability across trajectories of different length; per-trajectory thresholds (OAT App. A lists adaptive thresholds as open) may need length-stratified calibration.
- **Plausibility 4 / effort S.**

## X6. Knowledge-edit fault injection
*Source: KnowledgeSmith. fa_ideas C-group §7 (C7.1).*

- **Mechanism.** Run open-model agents (Qwen3 / Llama on GAIA, AssistantBench, τ²-Bench, or AgentErrorBench's setups) after a *leaf-level* AlphaEdit of one task-critical fact, or after unlearning it. The error arises fluently, on-policy, wherever the agent first relies on the fact, so error positions follow the natural distribution rather than the late skew of prompt injection. Ground truth: the first step that diverges from a twin run with the unedited model (same seed, temperature 0) and mentions the fact; confirm with a P1 repair rollout (swap the unedited model back in at that step). In a MAS, editing one agent's weights gives an exact *who*.
- **Use.** Training data for X3 / TSV / P2, and a natural-like test set for injected→natural transfer.
- **Risk.** Open agents and editing infrastructure (about 6 h per 1k edits on an H100); edits over-spread in 35% of cases, so check collateral damage with the preservation probes; only factual-knowledge errors can be injected this way, not planning or tool-use errors.
- **Plausibility 3 / effort M–L.**

## X7. Missing-cell correction for injected → natural (UDA with an unobservable source subpopulation)
*Source: UDA-unobservable-subpopulation. fa_ideas D-group §3 (3a–3c). Operationalises our #9 (C8.1).*

- **Step 1, tabulate.** Source = injected (Who&When Pro steps; Aegis agents), target = natural (Who&When, TraceElephant). Cross Y (decisive error / responsible agent) with A ∈ {position bucket early/mid/late, step type, agent role}. The empty or tiny source cells (error × early, or never-injected roles) are the paper's setting.
- **Step 2, missing cells.** Do not use injected positives at all there. Train a domain classifier κ(x) = P(source | f_t, A) on source *correct* steps vs target steps; the η1 formula turns "unlike any source correct step" into error probability (PU learning). The FA convention adds a constraint the paper lacks: Σ_a β_{1a} = N_fail / N_steps exactly, which with distribution matching pins the per-bucket priors.
- **Step 3, observed cells.** Apply label-shift reweighting to correct the injected position prior, a direct fix for the last-step bias.
- **Step 4, make invariance true.** Generate the source by injecting into the *same* systems that produced the natural failures (TraceElephant replay, P1 injection screens), so p(X | Y = 0, A) is invariant by construction; the UDA correction then covers the positions and error types the screen budget never injected.
- **Evaluation.** Train on the injected source, test exact and ±k on Who&When / TraceElephant *by position bucket*; the gain should be largest on early decisive steps.
- **Risk.** Invariance fails for Y = 1 (synthetic errors), so only the PU branch is robust; many cells may be missing at once, which the paper flags as beyond scope.
- **Plausibility 4 / effort M.**

## X8. Self-adversarial, on-manifold, causally verified fault injection
*Source: UniGame. fa_ideas F-group §7 (F7.1). Supersedes our B6 (which was rated 2).*

- **Mechanism.** An adversary picks (trajectory, step k, perturbation instruction: "misread a number in o_k", "skip verification", "hand off to the wrong agent"). The fault is realised by the *agent's own model* with the perturbation as a hidden instruction, and the trajectory is **rolled forward** so later steps react consistently (UniGame's decoder-realised perturbations beat embedding perturbations, +2.0 vs +0.7). Filters: (a) a realism discriminator trained on natural vs injected failures (Who&When vs Who&When Pro), keeping only injections it cannot tell apart; (b) a **causality check**: ≥ N rollouts fail after injection and succeed without it, so the label is a true repair-effect label. Injections that fool the current attributor go to a hard buffer; the attributor trains on clean plus buffer; the adversary also chooses k, so it places faults where the attributor is weak, counteracting the late-injection skew and last-step shortcut.
- **Data.** TraceElephant's replayable environments and P1 infrastructure; evaluate transfer to Who&When, MP-Bench, TrajErrBench.
- **Risk.** The adversary can drift to artefacts that fool the attributor but never occur naturally (the realism filter must hold); cost of a rollout continuation plus causality rollouts per candidate.
- **Plausibility 3–4 / effort L.**

## X9. Identity-bias test for attributors (Attribution-IBC)
*Source: Identity-Skews-Debate. fa_ideas A-group §5 idea 1. Complements our F2.2 (anonymisation as a replay δ).*

- **Mechanism.** Run the same judge on each trajectory with (a) real agent names, (b) anonymised names (Agent A/B/C), (c) *permuted* role labels with content kept. Measure how much the who-distribution shifts and whether blame follows the name or the content; report agent and step accuracy under each condition next to a "blame the modal agent" prior baseline. Attribution-IBC = Δ_real − Δ_anon.
- **Data.** Who&When (Magentic-One, CaptainAgent roles), Aegis (9.5k agent labels), MP-Bench.
- **Payoff.** A diagnostic of problem 6 and a free debiased judge. In the source, 18 of 20 model/dataset cells showed identity bias and anonymisation cut subversion by 64%.
- **Risk.** Role names carry real information (the WebSurfer does browse), so the permutation must keep content-role consistency.
- **Plausibility 4 / effort S.**

## X10. Streaming attributor with LRU-rotated suspect-memory heads
*Source: Multi-Head Recurrent Memory. fa_ideas A-group §8 idea 2.*

- **Mechanism.** A judge reads a 10^5–10^6-character trace chunk by chunk, keeping H = 4–8 independent note heads of candidate error steps and evidence, updated stage-wise (exactly one head rewritten per chunk, least-recently-updated first) instead of one rolling summary. In the source, LRU rotation beat LLM-chosen routing and stage-wise beat merged select+update; retention rose from 26.5% (1 head) to 87.1% (8 heads).
- **Prediction.** Early root causes survive to the end, so step accuracy improves on long traces whose cause is early. Data: LongRCA (median 145 steps; 3–24% step accuracy today), TRAIL, Hand-Crafted Who&When (median 33 steps).
- **Plausibility 3 / effort S.** No training.

## X11. Relevance-conditioned who-rule
*Source: RAG internal representations (analysis paper). fa_ideas C-group §6 (C6.2).*

- **Mechanism.** An LLM judge labels each consumed observation as relevant / distracting / irrelevant to the current sub-goal. Rule: relevant observation + wrong next step → blame the consumer (reasoning failure); distracting observation → blame the agent that issued the query or retrieval (retrieval failure). Black-box, usable on closed logs.
- **Data.** Who&When (Orchestrator vs WebSurfer blame, agent accuracy ≈ 54% and prior-driven), SearchAuditBench, AgentHallu Retrieval vs Reasoning.
- **Companion finding.** Instruction-tuned models abstain or give up after irrelevant context (97–98% abstention with a random document), so some "early termination" failures lock in at the noisy-observation step, not at the give-up step; relevant to the t_err vs t_lock conventions.
- **Plausibility 3 / effort S.**

## X12. "Failure to withhold" as an error class, with a solvability probe
*Source: MM-UPD. fa_ideas F-group §4 (F4.1). Our B2a (dual accuracy) and B2c (δ_read vs δ_decide) already cover F4.2/F4.3.*

- **Subtypes.** AAD: the agent picks the least-wrong candidate when none is correct; IVQD: it extracts an answer from an observation irrelevant to the sub-question (wrong page, wrong file); IASD: the available tools cannot solve the subgoal, yet it proceeds. The decisive step is where the agent *committed* instead of stopping, re-searching or asking, which is often earlier than the final answer (problem 6).
- **Detector.** At each step a judge-based solvability probe asks whether o_{≤t} contains enough information for the current subgoal; if no and u_t commits, flag the step.
- **Data.** Who&When and TraceElephant (confidently wrong GAIA final answers), SearchAuditBench (repair often = "keep searching"), AgentRx / TRAIL taxonomies. Training-mix lesson from the source: include 20–40% no-error or ambiguous examples when fine-tuning on injected data.
- **Risk.** Solvability from o is itself a judgement call in open-ended tasks.
- **Plausibility 3 / effort M.**

## X13. Three-way active step labelling and symptom-shift noise curves
*Sources: OOD-with-Human-Feedback, PO-under-noisy-feedback. fa_ideas D-group §2 (2a) and E-group §3 (3b). Extends our C2.1/C2.2 and D2.1/D2.2.*

- **Three-way labels.** Extend the label set to {correct-but-unusual, symptom of an earlier error, decisive error}: covariate-shifted steps (retries, rare tools, new log formats) vs semantic outliers. This is the only label set that teaches cause-vs-symptom directly. Selector: gradient projection of a step model trained on success-run steps (or the X3 probe). Simulate the annotator with existing labels: AgentRx labels every failure event plus the first unrecovered one; Failure-as-a-Process gives t_err (cause), t_lock, t_obs (symptom); MP-Bench vote counts give error yes/no and ambiguity. Budgets k ∈ {25, 50, 100, 200}; baselines random, attributor entropy, BADGE, hazard top-1. Hypothesis to test: top-k selection returns obvious symptom steps (tracebacks, empty observations), so near-boundary or mixed sampling may beat top-k, reversing the source's Table 5. The same selector chooses P1 rollout sites.
- **Symptom-shift noise curves.** Besides ε-flips (move t* to a random step, swap the agent), inject "propagation noise" (move t* to the symptom step), FA's dominant realistic noise. Train attributors and plot natural-test accuracy vs ε by trace length and backbone; the theory predicts a flat region then a linear drop, with the knee earlier for poorly separated data (long traces, output-only logs). Decides how much cleaning (X4) is worth and how many rollouts per label P1 needs (rollout labels are ω-uncertain by nature).
- **Plausibility 3 / effort M.**

---

## Merged into existing cards (no new code)

- **CORE-PA**: add the cumulative-sum readout (argmin of the running sum = lock-in; argmin per-step = decisive) and negative-advantage mass per agent for *who*; TIES-merged references beat both endpoints for α in 0.2–0.7.
- **CORE-H&S**: onset proxy within ±0.016 of the annotated onset while the peak lags by +0.07 to +0.11; test rise-vs-peak on LongRCA (root-to-end median 48 steps).
- **#4 CanDist**: per-dataset candidate sets, Aegis → all steps of the labelled agent; injected sets → [t_inj, first symptom step] plus the agent; MP-Bench → vote-weighted union; Failure-as-a-Process → [t_err, t_lock]; LongRCA / Who&When → t̂ ± k from the human agreement window. Stratify small-loss selection by position bin and agent role to stop collapse onto the last-step / orchestrator prior.
- **#8 / B4a observation ablation**: mask the top-attended evidence span (or the gold-matched span), never the whole observation and never a random span (VAUQ: core mask ≈ ground-truth mask > blank > random); build the observation-influence matrix M[t, s] and read it backwards from a symptom step as provenance; faithful use of a *wrong* upstream message routes blame upstream.
- **#7 capture/retention**: Who&When caveat from X0.
- **B6**: superseded by X8.
- **#15 ModeX**: cluster the N continuations of a screen on tasks without a verifier; collapse from multi-modal to uni-modal continuations marks lock-in; early-divergence lets rollouts be truncated.
- **E1.1 HERO**: three-tier gate for RL-trained attributors, exact > in-annotator-set > other, with the dense reward inside the 0-group (α small, 0.05–0.1).
- **A3.1 DACA**: who is a k-way MCQ, when is a 5-way MCQ over the judge's top-5; fit τ only on agreement cases; MP-Bench vote fractions as soft targets; do not distil a judge's step distribution where it disagrees with the outcome model (that flattens confidence).
