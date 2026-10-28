# Batch G report — mechanistic interpretability, data provenance / benchmark integrity, evaluation tooling

Reader note: this batch is far from the target problem. I was strict: two papers get zero cards, two get one, and the geolocalization pair (GeoRanker, GeoArena) carries most of the transferable content. Plausibility scores are my own; "L0/L1/L1+/L2" follow the brief.

---

## 1. MxD — "Towards Interpretability Without Sacrifice: Faithful Dense Layer Decomposition with Mixture of Decoders" (Oldfield et al., NeurIPS 2025; arXiv 2505.21364v3)

**Paper.** Replaces one pre-trained MLP layer with a *Mixture of Decoders*: N (21k–86k) sparsely gated linear "experts" W_n = D·diag(c_n) (Eq. 4, Lemma 1: each expert is full-rank), gated by TopK(Gᵀx) with K=16–256, applied to the dense hidden units z = φ(Eᵀx) (Eq. 3, forward pass = (Cᵀa) ∗ (Dᵀz), Lemma 2). Trained purely by normalized MSE reconstruction of the frozen MLP output on 480M OpenWebText tokens (Sec. 3.1), parameter-matched to Transcoders. Evaluated on GPT2-124M, Pythia-410M/1.4B, Llama-3.2-3B (plus partial Gemma2-27B): downstream CE loss preserved far better than Transcoders/Skip-Transcoders at every K (Fig. 3, Fig. 10); normalized MSE up to an order of magnitude lower (Fig. 9); fraction of 16-token continuations identical to the base model 46–51% for MxD vs 13–22% for STC and ~0 for SAE (Fig. 4). Expert pre-activations a_n used as features: competitive with TC/STC and better than TopK-SAE on 24 SAEBench sample-level and 10 token-level sparse-probing tasks (Fig. 5, 12, 15; logistic probes on the 100 features with largest mean difference); steering via ŷ = y + λ·W_nᵀz with λ=100 (Sec. 3.2.2, LLM-judged). Supervision: none (reconstruction). Cost: 8.5 h RTX3090 (GPT2) to 2 days A100 (3B), Table 10.

**Transferable ideas.**

**Card 1.1 — Sparse-expert activations as step-level probe features (grey-box).**
- *Mechanism in paper:* a K-sparse, non-negative vector a ∈ R^N (N≈20k–86k) per token is a faithful, in-forward-pass decomposition of the MLP; "there exist individual MxD expert units that are predictive of various categories" (Sec. 3.2.1); probes trained on mean-pooled pre-activations over non-padding tokens.
- *Mapping:* sample = a step s_t of a self-collected trajectory run on an open backbone with an MxD layer spliced in (middle layer; paper shows layers 8–15 of 12–32); feature = mean/max-pooled expert pre-activations over the step's generated tokens (and separately over the observation tokens); output = h_t for proposal 2's hazard model, or a step error/no-error probe; supervision L1 (outcome only, via proposal 2's likelihood) or L2 where we have step labels on our own runs. Grey-box only.
- *Datasets:* only self-collected runs (released datasets are text logs). Could re-run Who&When/AgentErrorBench tasks (GAIA, ALFWorld, WebShop) with Llama-3.x/Qwen-2.5 7–8B agents. Baseline: same probe on raw residual-stream hidden states (the paper's own Related Work cites Kantamneni et al. 2025 showing SAE features often *underperform* dense-activation probes [63]).
- *Relation:* strengthens proposal 2 (a candidate featurization for h_t) — not new as a modelling idea.
- *Main risk:* the learned specializations are lexical/topical (punctuation, months, MMO games; App. E) — no evidence any expert tracks "agent error"; probing F1 is merely competitive with baselines; training an MxD per 7–8B backbone is days of GPU and ties the attributor to one model.
- *Plausibility 2, Effort L.*

**Card 1.2 — Divergence-horizon under mechanistic perturbation as a label-free lock-in probe.**
- *Mechanism in paper:* Sec. 3.1.2 / Fig. 4 measures, after replacing a layer, "the percentage of the samples' continuations that are identical in the original LLM and hooked LLMs up to n future tokens" — a horizon at which a small internal perturbation compounds into visible output divergence; steering by expert n is a localized perturbation ŷ = y + λW_nᵀz.
- *Mapping:* at step k, apply a small internal perturbation (ablate/steer the top active experts of step k's tokens, or swap the MxD layer in/out) and regenerate; record the number of subsequent steps (not tokens) before the trajectory's actions diverge from the unperturbed run, and whether the final outcome flips. Steps where tiny perturbations flip the outcome are decision points; the last k whose perturbation can still flip a failed run to success approximates t_lock. Output: when / lock-in; supervision L0 (needs an executable environment for regeneration, like proposal 1); grey-box.
- *Datasets:* replayable ones only (TraceElephant, SymFail, Failure-as-a-Process CLI tasks) re-run with open backbones. Baseline: proposal 1's textual δ perturbation screen.
- *Relation:* strengthens proposal 1 — a mechanistic, fix-agnostic δ ("nudge the representation") that avoids hand-writing repairs; cheaper than N rollouts per candidate fix only if a single regeneration is informative.
- *Main risk:* a random internal perturbation measures sensitivity, not correctness; sensitivity peaks may be at high-entropy but harmless choice points; expert-level steering effects are judged only by LLM coherence scores in the paper.
- *Plausibility 2, Effort L.*

**Quotable facts.**
1. "MxDs' normalized MSE is up to an order of magnitude smaller than Transcoders'" at small K (App. B.2, Fig. 9).
2. Fig. 4a (Pythia-410M): identical 15-token continuations after layer replacement — MxD 0.51, STC 0.22, TC 0.18, SAE 0.0.
3. "Across 108 sparse layers in 4 LLMs (with up to 3B parameters) MxDs (i) pareto-dominate existing techniques on the sparsity-accuracy frontier yet (ii) remain competitive on 34 sparse probing and steering tasks" (Sec. 1).
4. Learned experts have mean normalized rank 0.99 ± 0.005 (Table 4) — no rank deficiency despite top-K sparsity.
5. Training cost Table 10: Llama-3.2-3B layer, 1× A100-80GB, 2 d 0 h; GPT2-124M, 1× RTX3090, 8 h 34 m.

**Code/data released?** Yes — https://github.com/james-oldfield/MxD (training code + equivalence notebooks); no new datasets.

---

## 2. Gradient leading terms — "How Do Transformers Learn to Associate Tokens: Gradient Leading Terms Bring Mechanistic Interpretability" (Im, Oh, Fang, Li, ICLR 2026; arXiv 2601.19208v2)

**Paper.** Theory of early training dynamics for an attention-only transformer with residual stream, causal mask and T5-style relative positions (Def. 3.1), full-batch GD on next-token CE. Theorem 4.1 / D.10 / D.13: for s ≤ η⁻¹·min(1/12L, 5/(8√T)) steps, every layer's weights are, up to O(s²η²)–O(s⁵η⁵T) error, scalar multiples of corpus statistics: output matrix W_O ≈ sη·B̄ (row-centered frequency-weighted bigram matrix, Eq. 9); value V ≈ C(s,2)η²·Φ̄ᵀB̄ᵀ (Φ̄ = centered prefix co-occurrence, Eq. 11); QK matrix W ≈ (3C(s,4)+2C(s,3))η⁴·Q̄, a masked/centered composition of the "interchangeability" matrix Σ_B̄ = B̄ᵀB̄ (Eq. 10) with Φ̄ (App. A). Validation: 3-layer TinyStories model, min cosine ≥ 0.998 across epochs at small LR (Table 1), >0.7 after 100 epochs at large LR (Fig. 4); Pythia-1.4B checkpoints: covariance of per-layer token embeddings matches Φ̄ᵀB̄ᵀ early, drifts first in early layers (Fig. 6), layer-13 heads specialize earliest (Fig. 7). Causal ablation (Table 3): projecting out the leading term raises loss 5.35→8.29 (W_O), →6.2–6.5 (V), →5.35–5.36 (attention). No supervision issue (pure LM training); no agent/sequence-labelling content.

**Transferable ideas.** None. The only honest analogue — "the first gradient step of any outcome-supervised attributor (proposal 2, L1) equals a centered frequency-weighted co-occurrence statistic between step features and the outcome" — is a tautology of logistic regression at zero init, and it is already the obvious L1 baseline (per-step-type failure co-occurrence), not a new idea. The paper's token-association machinery (bigram/context matrices) has no step-level or counterfactual content.

**Quotable facts.**
1. "even after 30 epochs, all weights achieve a cosine similarity of at least 0.9 ... above 0.7, even after 100 epochs, where the loss had dropped from 8.00 to 5.35" (Sec. 5.1).
2. Table 3: removing the leading-term projection — Original 5.349; Output 8.287; Value layers 6.19–6.53; Attention layers 5.350–5.361.
3. "the output layer has the largest order update, while the attention weights have the smallest order updates" (App. B) — predicted by the η¹ vs η⁴ scaling.
4. Pythia-1.4B: "as the model continues training, the weights gradually drift from fixed associative features to represent richer knowledge beyond association, starting with the earlier layers" (Sec. 5.2).

**Code/data released?** Reproducibility statement says code "is available here" (link not in extraction); uses public TinyStories, OpenWebText, FineWeb, Pythia checkpoints.

---

## 3. KnowledgeSmith — "Uncovering Knowledge Updating in LLMs with Model Editing and Unlearning" (Luo et al., ICLR 2026; arXiv 2510.02392v3)

**Paper.** Casts editing and unlearning as one constrained optimization θ' = argmin L_task(Q⁺) + λ L_pres(Q⁻) + λ_reg R(θ',θ) (Eq. 3), differing only in the target distribution (fact vs neutral). Builds a KG-anchored benchmark generator: GPT-4o produces a hierarchy (root/intermediate/leaf), templated 4-choice probes of six types (direct, reverse, multi-hop, contextual, conflict, comparison; App. A.4), 4 domains × 3 levels × 10k samples = 360k training items + 100-probe eval sets. Interventions: AlphaEdit (editing), ReLearn (unlearning), plus MEND/TOFU-GA in App. E; 13 models 1B–123B; train sizes 1–10,000. Metrics: accuracy; Collateral Change Ratio CCR = mean divergence on structurally related probes (proxy 1 − multi-hop acc) for over-spreading; Residual Retention RR (proxy multi-hop acc) for under-spreading (App. B); conflict rate = fraction of queries where the model supports contradictory statements (Sec. 5.2.5); representation shift via CKA/KL/L2/Fisher between pre- and post-update models (Table 1, App. H); SVD rotation-vs-scaling analysis (Sec. 5.6). Findings: editing over-spreads, unlearning under-spreads; root-level interventions have lower ceilings; consistency collapse past a data scale (direct probes degrade while reverse probes stay high, Fig. 3d); unlearning shows abrupt CKA phase transition around 100–1000 samples (Table 14: CKA 0.993→0.001 at 100 samples for Llama3 biology/root) while editing drifts smoothly; history resists updates; editing ≈6 h vs unlearning 0.2–1.5 h per 1k–10k samples on H100.

**Transferable ideas.**

**Card 3.1 — Hierarchy-stratified repair effects with over-/under-spreading metrics.**
- *Mechanism in paper:* interventions are applied at root/intermediate/leaf nodes and measured on the target *and* on structurally related nodes; "Root-level edits/unlearning face a lower ceiling due to structural complexity and the need for coherent propagation across descendants ... Leaf-level edits/unlearning can reach near-perfect in-domain accuracy with fewer examples" (Sec. 5.2.2); CCR/RR (Eq. 4–5) quantify how far an intervention's footprint spreads.
- *Mapping:* intervention = proposal 1's repair δ at step k; hierarchy = plan-level step (root: task decomposition/orchestrator message), subgoal-level (intermediate: sub-plan, agent hand-off), action-level (leaf: single tool call/code edit). Measure (i) repair effect φ(τ,k,δ) stratified by level, (ii) a CCR analogue = fraction of downstream steps whose content changes after the fix (footprint), (iii) an RR analogue = fraction of the original error symptoms (failed tests, wrong intermediate values) that persist after the fix. Output: when + a propagation profile per step; supervision L1+ (rollouts); text-only inputs with replay.
- *Datasets:* replayable sets (TraceElephant, SymFail, Failure-as-a-Process); step hierarchy can be derived from existing module/type labels (AgentErrorBench module labels, MAST planning vs execution, Who&When agent roles). Baseline: unstratified fragility curves of proposal 1.
- *Relation:* strengthens proposal 1 (adds a second axis — propagation footprint — and a hypothesis: plan-level repairs have larger footprint but lower success ceiling; action-level repairs are local and high-success). Tests the folk claim that "early planning errors are decisive".
- *Main risk:* in KGs the hierarchy is given; in trajectories "level" must be inferred and is confounded with position (plans come first), so the stratification may just re-discover the position effect.
- *Plausibility 3, Effort M.*

**Card 3.2 — Conflict/reverse probe battery as a label-free symptom detector (t_obs).**
- *Mechanism in paper:* "conflict rate ... measures the proportion of queries where the model simultaneously supports mutually inconsistent statements after intervention" (Sec. 5.2.5); reverse probes test whether the relation holds in both directions; the paper shows conflicts expose instabilities "residual belief alone cannot" (Fig. 4b).
- *Mapping:* for each step k, extract the atomic claims the agent relies on (facts retrieved, variable values, file paths, test outcomes) and auto-generate direct/reverse/conflict probes; ask the *agent model* (replayed prefix) or the running agent at step k; a spike in conflict rate marks the first observable symptom t_obs and localizes "what" (hallucination vs. stale state). Supervision L0; needs the agent model (replay) — black-box API suffices.
- *Datasets:* AgentHallu (443 hallucinated vs 250 clean runs, step + cause) is the natural test; SearchAuditBench (deep-search, factual claims); TraceElephant for replay. Baseline: SelfCheckGPT-style self-consistency sampling at each step; proposal 2's L0 change-point.
- *Relation:* new as a *symptom* detector (t_obs), complementary to both proposals which target t_err; could supply the "first symptom" timestamp for Failure-as-a-Process style labels.
- *Main risk:* claim extraction from heterogeneous tool outputs is itself an LLM task with errors; many agent failures are procedural (wrong tool args, skipped verification), not factual inconsistencies.
- *Plausibility 3, Effort M.*

**Quotable facts.**
1. Failure-mode frequencies (Table 2): editing — over-spreading 35%, conflict emergence 30%, under-forgetting 20%; unlearning — under-forgetting 35%, over-spreading 15%, conflict 12%.
2. Unlearning phase transition: Llama3 biology/root CKA 0.993 (10 samples) → 0.001 (100) → 0.623 (1000) (Table 14); editing CKA stays 0.999.
3. "unlearning preserves strong OOD accuracy (63–82%) but yields modest in-domain gains (≤30%), while editing substantially boosts in-domain accuracy (up to 50–60% in economics) at the cost of OOD stability" (Sec. 5.3).
4. Sequential updates (Tables 10–11): after 5 edits, Fact-1 accuracy 55.0→53.5%; after 5 unlearnings, Fact-1 54.2→27.2%.
5. Compute: "unlearning typically completes in about 1.5 hours on an NVIDIA H100. Knowledge editing is more resource-intensive (roughly 6 hours)" for 10k examples (App. H).

**Code/data released?** Yes — https://github.com/AIFrontierLab/KnowledgeSmith; generated benchmark data and configs "upon publication".

---

## 4. KDS — "How Contaminated Is Your Benchmark? Measuring Dataset Leakage in LLMs with Kernel Divergence" (Choi, Khanov, Wei, Li, ICML 2025; arXiv 2502.00678v2)

**Paper.** Dataset-level contamination score S(D, M). Extract L2-normalized final-layer embeddings Z of the n benchmark samples from M, LoRA-fine-tune M on D for 1 epoch (SGD, batch 4, lr 1e-4, LoRA r=8 on q/v; Table 9), extract Z'. Build RBF kernels Φ(Z)_ij = exp(−γ‖Z_i−Z_j‖²) with median-heuristic γ, and score S = −(1/E) Σ_ij Φ(Z)_ij log(Φ(Z)_ij/Φ(Z')_ij), E = sqrt(ΣΦ(Z)) (Eq. 5). Eq. 4 shows this equals a soft gate by original similarity times the change in pairwise squared distance. Premise: fine-tuning moves *unseen* samples more than seen ones (histograms Fig. 7: unseen–unseen pairs spread apart). Requirements: monotonicity in contamination λ and consistency across resamples (Sec. 2.2). Results on WikiMIA/BookMIA/ArxivTection with Mistral-7B-Instruct, λ ∈ {0,…,1} in 0.05 steps, 5 subsets each: Spearman 0.999/0.997/0.975 (avg 0.990) vs best baseline Min-K% 0.893/0.998/1.000 and Zlib −1.000 on BookMIA (Table 1); IID Pile subsets avg 0.944 (Table 6); Llama-3.1-8B 0.982, Phi-3-small 0.892 (Table 7). Ablations (Table 2–4): without fine-tuning Spearman drops to 0.683; kernel choice irrelevant; later layers best (Fig. 4); 1-epoch SGD ≫ batch GD or 4 epochs. Cost: 39 s fine-tune for 700 samples, 555 s for 4000 (Table 8). Needs fine-tunable weights; relative score only (ranking datasets for a given model).

**Transferable ideas.**

**Card 4.1 — Contamination audit of attribution benchmarks for open-weight attributor models.**
- *Mechanism in paper:* Eq. 5 with a fixed model M ranks datasets by exposure; "A reliable scoring function is practically valuable because it allows us to identify datasets that are contaminated with respect to model M" (Sec. 2.1); monotonic in λ with low variance (Fig. 3).
- *Mapping:* sample = one annotated failed trajectory (full log text, truncated/chunked to context; or the (trajectory, gold step, gold agent) record as released on GitHub/HF); M = each open-weight model used as an attributor or judge in our experiments (Qwen-2.5/3, Llama-3.x, DeepSeek-R1-distills); datasets D = Who&When (public since 2025), MAST-Data, TRAIL, AgentErrorBench, MP-Bench, etc.; anchor λ=0 with freshly self-collected trajectories post model cutoff and λ=1 with a split we deliberately fine-tune in. Output: a per-(model, dataset) contamination ranking; use it to (i) discount attributor scores on contaminated sets, (ii) decide which sets to hold private, (iii) check whether injected-failure sets (Who&When Pro, Aegis) are also exposed. Supervision: none; grey-box (needs LoRA fine-tuning of M).
- *Datasets:* all released natural-failure sets; baselines: Min-K%/Min-K%++/Perplexity/Zlib on the same samples (the paper's Table 1 shows these can even flip sign).
- *Relation:* new, orthogonal to both proposals; a hygiene step before any attributor comparison. Pairs with Card 5.1 (laundered copies).
- *Main risk:* trajectories are 7k–260k tokens — chunking changes the kernel geometry; KDS validated on 700–4000 short samples; closed attributors (GPT/Claude) cannot be scored at all; KDS is relative, so interpretation hinges on the λ=0 anchor.
- *Plausibility 4, Effort S–M.*

**Card 4.2 — Soft-gated kernel change as a step-level change-point statistic.**
- *Mechanism in paper:* Eq. 4 decomposes the score into (1) a soft gate exp(−‖Z_i−Z_j‖²) favouring originally similar pairs and (2) the change in pairwise distance after an update; the signal is "how much does conditioning on new information reorganize the geometry of previously-similar items". KnowledgeSmith (Table 14) independently uses CKA between pre/post representations to detect abrupt reorganization.
- *Mapping:* sample set = the steps s_1..s_{k} of one trajectory, embedded by an open model (mean-pooled hidden states per step, final or late layer); "update" = extending the prefix to k+1 (re-encode steps in the longer context) or, for L1+ data, replaying from the prefix; statistic KD_k = soft-gated change in pairwise step distances. A spike in KD_k means step k+1 reorganized how earlier steps relate (e.g., a plan was abandoned, a wrong observation re-anchored the context) — a label-free change-point candidate for t_err/t_obs. Output: when (ranked candidates); supervision L0; grey-box.
- *Datasets:* self-collected open-model runs; AgentHallu-style clean vs hallucinated contrasts to validate. Baseline: proposal 2's L0 change-point mixture; OAT; token-surprisal spikes.
- *Relation:* strengthens proposal 2 (one concrete, cheap L0 statistic to plug into the change-point mixture).
- *Main risk:* in KDS the discriminative power comes from the fine-tuning contrast (without it Spearman 0.683); the prefix-extension analogue has no such contrast and may reduce to attention-based context drift that also happens at benign topic shifts.
- *Plausibility 2, Effort M.*

**Quotable facts.**
1. Table 1 average Spearman: KDS 0.990 vs Perplexity 0.966, Min-K% 0.964, Zlib 0.322, Min-K%++ 0.103, SRCT 0.080.
2. "w/o (2) Fine-tuning" ablation: Spearman 0.683 vs 0.999 (Table 2) — the fine-tuning contrast carries the signal.
3. Pile IID subsets (no temporal shift): KDS avg Spearman 0.944 / Pearson 0.948 (Table 6).
4. Cost: WikiMIA n=700 fine-tune 39 s, scoring 0.0008 s; BookMIA n=4000 fine-tune 555 s (Table 8, H200).
5. "unseen-unseen pairs exhibit more significant shifts, with distances increasing more after fine-tuning overall" (App. E, Fig. 7).

**Code/data released?** Yes — https://github.com/deeplearning-wisc/kernel-divergence-score; uses public WikiMIA/BookMIA/ArxivTection/Pile.

---

## 5. SDR — "Combating Data Laundering in LLM Training" (Li, Ye, Li, Liu; ICLR 2026 workshop on Data Problems for FMs; arXiv 2604.01904v3)

**Paper.** Threat: a provider trains on semantics-preserving rewrites ("laundered" surrogates) of proprietary text; membership detectors queried with originals collapse (Table 1, Llama-2 on MIMIR-Wikipedia rewritten "in a lyrical style": Loss AUC 1.000→0.539, TPR@5% 1.00→0.04). Method *Synthesis Data Reversion*: search a rewriting prompt p for an auxiliary LLM M_a such that detectors on Syn_p(D_pro) vs Syn_p(D_held) separate (Eq. 1). Stage 1 (Alg. 1): bound the goal to 23 linguistic registers; build an opening-sentence template per register; score registers by the *target model's mean max-next-token probability* when continuing register-styled openings (Eq. 2); keep top-5; run the detector on full rewrites; pick the best. Stage 2 (Alg. 2): feed the first sentence of a surrogate to the target, get its continuation, ask M_a how to edit p so surrogates match the continuation, accept the new p only if detector Perf improves; K≈10 iterations. Results (Pythia-6.9B, MIMIR-Wiki, Table 2): Recall AUC 64.7→76.2, TPR@5% 8.9→25.3 (inside-register laundering); 61.7→73.4 / 5.6→23.2 (outside-register); holds across Falcon-7B/Llama-2-7B (Table 4), C4/HackerNews (Table 3), auxiliary-model mismatch (Table 5), DeepSeek-v3 or human (Polite dataset) launderers (App. J), partial laundering (App. L). Negative control: AUC/ASR stay ≈0.5 when nothing was laundered (Table 15). Cost: hours; $7–39 GPT-4o per run (App. M). Needs black-box query access + an unseen reference set.

**Transferable ideas.**

**Card 5.1 — Laundering-aware contamination check for attribution benchmarks.**
- *Mechanism in paper:* "Since training-time exposure occurs in the laundered form, memorization signals may no longer appear on the originals" (Abstract); SDR searches format/register transformations and uses continuation confidence as a cheap familiarity proxy (Eq. 2) before running the full detector.
- *Mapping:* attribution benchmarks are unlikely to appear verbatim in pretraining; they appear *transformed*: JSON logs → markdown tables in blog posts, paper appendices, GitHub READMEs, LLM-generated summaries, re-tokenized traces. Candidate transformation set (the "registers"): raw JSON, markdown transcript, paper-style excerpt with gold label, HF dataset viewer rendering, natural-language summary. For each open attributor model M, rewrite a Who&When/TRAIL sample under each rendering, rank renderings by M's continuation confidence, then run Min-K%/KDS on the best rendering against a fresh held-out trajectory set. Output: contamination evidence (and the rendering through which leakage happened); supervision none; black-box for Stage 1, grey-box for KDS.
- *Datasets:* same as Card 4.1; emphasis on Who&When (small, 184 items, widely re-posted). Baseline: Card 4.1 on raw logs.
- *Relation:* complements Card 4.1; orthogonal to both proposals.
- *Main risk:* the practical worry is leakage of (task, gold step) pairs, not long logs; SDR gains are moderate (AUC ~0.65→0.75) and cost hours per (model, dataset); the 23-register taxonomy does not fit log renderings (App. P admits the taxonomy is too coarse).
- *Plausibility 3, Effort M.*

**Card 5.2 — Goal–detail search over repairs δ with accept-if-improves replay feedback.**
- *Mechanism in paper:* unbounded transformation space made tractable by "a high-level transformation goal ... and fine-grained details" (Abstract); Alg. 2 proposes a refined prompt from target-model feedback and "accepts the proposal only when score_new > score_old"; stage ablation (Fig. 2) shows both coarse goal identification and detail refinement matter (TPR@5% 19.9/24.8 → 32.3).
- *Mapping:* proposal 1 needs a repair δ at step k but the space of textual fixes is unbounded. Decompose δ into a coarse *repair goal* drawn from the failure taxonomy (re-plan, re-issue tool call with corrected args, insert verification, correct a fact, hand off to another agent, …; 9–20 modes) and *details* proposed by an auxiliary LLM from the failed continuation (the analogue of the target model's continuation s̃). Perf = success rate of N replays from (prefix_k + δ). Stage 1 screens goals cheaply (e.g., 2 rollouts each), Stage 2 refines details with accept-if-improves. Output: φ(τ,k,δ*) with the best-found δ*, plus a "what" label (the winning goal). Supervision L1+; text-only with replay.
- *Datasets:* replayable sets (TraceElephant, SymFail, Failure-as-a-Process); SearchAuditBench's repair rubric gives human repairs to compare δ* against. Baseline: a single LLM-written fix per step (current proposal 1 default); oracle human repair.
- *Relation:* strengthens proposal 1 (makes "apply fix δ" operational and gives the category label for free). Also an unexplored point: SDR's negative control (no gain when nothing was laundered) maps to "no δ at step k improves success ⇒ k is not an error step", a principled null.
- *Main risk:* each Perf evaluation costs N rollouts; search over ~15 goals × K refinements per candidate step is expensive on 100-step trajectories — needs a cheap screener (see Card 7.2) to restrict k; risk of finding a repair that "works" at a non-causal step by over-steering (the paper controls this via negative control; we would control via success-run injection).
- *Plausibility 3, Effort M–L.*

**Quotable facts.**
1. Table 1: on laundered training data, Loss/Zlib/Min-K/Recall AUC fall from ≥0.999 to 0.52–0.56 and TPR@5% from 1.00 to 0.00–0.08.
2. Table 2 (Pythia-6.9B, inside registers): Recall AUC 64.7%→76.2%, TPR@5% 8.9%→25.3% with SDR; Loss 63.7%→76.6%.
3. Negative control (Table 15): with no laundering, Recall AUC 0.516→0.488, Loss 0.486→0.490 — "SDR does not fabricate evidence".
4. Hyperparameters: sample size m has the strongest effect — m 3→9 raises AUC 0.72→0.81 at unchanged query cost (App. M); K=15 costs ~13.5 h and ~$39 with GPT-4o.
5. Human-laundered Polite data: Loss AUC 0.687→0.751 with SDR but Recall 0.649→0.566 (Table 17).

**Code/data released?** Code "included in the submitted supplementary material and will be released upon publication"; data = public MIMIR subsets (HF iamgroot42/mimir) and Polite dataset.

---

## 6. TorchUMM — "A Unified Multimodal Model Codebase for Evaluation, Analysis, and Post-training" (Luo et al., 2026 preprint; arXiv 2604.10784v2)

**Paper.** Engineering + measurement paper. Four-layer codebase (infrastructure / core / task-execution / API) built around a minimal `BackboneAdapter` protocol (`name`, `load(cfg)`, `generate(batch, gen_cfg)`; App. A.1), three YAML config layers (inference / evaluation / post-training; App. A.2), thin wrappers calling official scorers for two-stage benchmarks; 15 UMMs, 12 benchmarks (understanding, generation, editing, unified), 5 post-training methods (SFT, RecA, UniCoT, IRG, UniGame). Findings under one protocol: no model dominates (Tables 1–4); scale is not predictive (Ovis-U1 3.6B tops GenEval 90.05); SFT often degrades (TokenFlow DPG 71.29→22.16, Table 5); post-training effects are backbone-dependent. Analysis section: Cross-Modal Alignment Margin CMAM = mean cos(matched text/image spans) − mean cos(mismatched) (Eq. 1): OmniGen2 0.126 vs Show-o2 0.030 vs MMaDA 0.019 — the least architecturally unified model is most representationally aligned; query-variation consistency (two meaning-preserving paraphrases per MathVista question; response embeddings + hidden states every 5 layers mean-pooled over the response span; Fig. 5) shows aggressive unification "rewrites" inherited backbone behaviour; CoT trace-formation gap (MMaDA median visible trace 2 tokens, 63.1% answer-only, acc 29.3% vs OmniGen2 220 tokens, 99.5% traces, acc 58.1%; Fig. 3) with teacher-forced next-token entropy trajectories along the response.

**Transferable ideas.**

**Card 6.1 — A unified attribution harness (adapter protocol + canonical trajectory schema + metric library).**
- *Mechanism in paper:* "Switching from one model to another on the same benchmark requires changing only the backbone name and model path in the config file" (App. A.2); "All results are independently reproduced; they do not represent official numbers" (Sec. 4); the central claim that "conclusions drawn from isolated benchmarks or single-model studies can be misleading" (Sec. 6).
- *Mapping:* `DatasetAdapter` per source (Who&When, TraceElephant, MP-Bench, LongRCA, AgentRx, SymFail, TrajErrBench, AgentErrorBench, AgentHallu, SearchAuditBench, MemTrace, Failure-as-a-Process, Who&When-Pro, Aegis, TracerTraj, CORRECT-Error, MAST, HORIZON) → one schema: steps with (agent, content, observation, timestamps), labels as *sets* with annotator votes, t_err/t_lock/t_obs where present, category under a mapped taxonomy, replayability flag. `AttributorAdapter` → canonical output: ranked list of (step, score), agent, category, P(fail | prefix) per step. Metric library: exact, ±k, set-F1, nDCG, agent accuracy, category accuracy, calibration (ECE), lead time; bootstrap CIs. YAML-driven runs; leaderboard. Supervision n/a; text-only.
- *Datasets:* all of the above. Baseline: today's per-paper scripts.
- *Relation:* infrastructure for both proposals (proposal 1's effect labels become just another label source; proposal 2's hazard model another attributor).
- *Main risk:* pure engineering; the schema must handle set-valued/ordinal labels and multi-annotator votes or it will silently flatten them; gated datasets complicate redistribution.
- *Plausibility 4, Effort M–L.*

**Card 6.2 — Paraphrase-consistency and entropy-trajectory diagnostics for step instability.**
- *Mechanism in paper:* Sec. D.2 generates two meaning-preserving query variants and measures dispersion of responses in embedding space and of mean-pooled hidden states across layers; Sec. D.3 tracks teacher-forced next-token entropy along the generated trace and interprets a gradually decreasing entropy curve as "progressively constraining the answer".
- *Mapping:* at step k, paraphrase the last observation/instruction (meaning-preserving), re-sample the agent's next action m times, and measure action dispersion (embedding cosine spread, or exact tool-call agreement); also compute the entropy trajectory of the agent's own step-k tokens. High dispersion / rising entropy marks unstable decision points; combined with outcome labels this gives a cheap L1 feature for h_t. Output: when (candidates), P(fail | prefix) feature; supervision L0/L1; black-box via sampling, grey-box for the hidden-state version.
- *Datasets:* replayable sets and self-collected runs; AgentHallu clean vs hallucinated; baseline: token-surprisal baselines and proposal 2's L1 hazard without this feature.
- *Relation:* strengthens proposal 2 (feature) and is a cheaper cousin of proposal 1's L1+ rollouts (perturb input instead of injecting errors).
- *Main risk:* dispersion tracks task ambiguity and legitimate multi-solution branching, not errors; the paper used it to compare *models*, not to localize events within a trace.
- *Plausibility 3, Effort M.*

**Card 6.3 — CMAM-style matched-vs-mismatched margin to detect "ignored observation" steps.**
- *Mechanism in paper:* Eq. 1: margin between the cosine of a sample's own paired spans and the mean cosine to other samples' spans; low margin = paired items "not much more aligned than random mismatches".
- *Mapping:* paired spans = (observation o_{t−1}, agent output s_t) within a trajectory; mismatched = s_t against other steps' observations. In the agent model's late-layer pooled representations, a step whose output is no more aligned with its own observation than with others is a candidate "did not read the tool result / stale state" error (a frequent category in MAST, AgentErrorBench, MemTrace). Output: what (ignored-observation category) + when; supervision L0; grey-box.
- *Datasets:* AgentErrorBench (module+type labels), MemTrace (memory failures), self-collected runs. Baseline: LLM judge asked "does step t use the observation?".
- *Main risk:* alignment in representation space may be dominated by shared topic; needs a per-trajectory null distribution; untested in the paper beyond three models.
- *Plausibility 2, Effort M.*

**Quotable facts.**
1. "no single model dominates across understanding, generation, and editing, and strong performance in one dimension often comes at the expense of others" (Sec. 1).
2. SFT degradation: "TokenFlow: DPG 71.29 → 22.16" (Sec. 4.5); IRG on Bagel: UEval 30.9 → 9.1 (Table 5).
3. CMAM: OmniGen2 0.126, Show-o2 0.030, MMaDA 0.019 (Fig. 2) — "architectural unification is not equivalent to representational unification".
4. CoT gap: MMaDA median trace 2 tokens, 63.1% answer-only, acc 29.3%; Show-o2 5 tokens, 49.5%, 50.0%; OmniGen2 220 tokens, 99.5% traces, 58.1% (Sec. D.3).
5. Unified-Bench reconstruction drops sharply with structure-aware encoders: Janus 0.8465 (CLIP) → 0.5691 (DINOv3) (Sec. 4.4).

**Code/data released?** Yes — https://github.com/AIFrontierLab/TorchUMM (codebase, configs, reproduced leaderboards); no new datasets.

---

## 7. GeoRanker — "Distance-Aware Ranking for Worldwide Image Geolocalization" (Jia, Park, Gao, Zhao, Li, NeurIPS 2025; arXiv 2505.13731v4)

**Paper.** Two-stage geolocalization: retrieval (G3 encoders over MP16-Pro) yields top-N candidates; Fig. 1 shows the oracle gap — picking the best of top-20 candidates would give 32.7% @1 km vs G3's 16.7%. GeoRanker = Qwen2-VL-7B-Instruct + LoRA (r=16 on q/k/v; 0.083% params) + bias-free linear value head on the final-token hidden state → scalar s per prompt "{query image} How far is this place from lat/lon, text, {candidate image}? Negative examples: {bottom-k text}" (Sec. 3.2, Eq. 1). Training on the new GeoRanking set (100k queries, 7 ranked candidates + 5 hard negatives, 2M pairs): first-order partial Plackett–Luce loss over candidates sorted by geodesic distance, K⁽¹⁾=1 (Eq. 2); second-order PL loss on the k₁(k₁−1)/2 pairwise score differences ordered by distance gaps (Eq. 3–4), weighted λ=0.7 (Eq. 5); 1 epoch, 16 h on 4×L40S. Inference: score 12–14 retrieved + 3–5 GPT-4V-generated candidates, argmax (Eq. 6). Results: IM2GPS3K 1 km 18.79 vs 16.65 (+12.9%), YFCC4K 32.94 vs 23.99 (+37.3%), SOTA at all five thresholds (Table 1). Ablations: second-order loss helps mostly at coarse thresholds (country 76.31 vs 75.61, continent 89.29 vs 88.28); removing hard negatives 18.79→17.35 @1 km; removing candidate images 18.79→15.58 (Table 2); K⁽¹⁾>1 hurts (train/test mismatch); beats G3 with 10% of data (Fig. 5); scales 0.5B→7B (Fig. 6); Recall@1 0.089→0.198, NDCG@10 0.674→0.842 over G3 retrieval (Table 5) with graded relevance by distance bucket; <half the latency of LLM prompting, parallelizable (Fig. 4).

**Transferable ideas.**

**Card 7.1 — Distance-aware listwise step ranker (first + second-order Plackett–Luce).**
- *Mechanism in paper:* candidates are ranked by a *continuous* distance to ground truth, not a binary label; L⁽¹⁾ is a partial PL loss over distance-sorted candidates (Eq. 2) and L⁽²⁾ supervises that larger distance gaps produce larger score gaps (Eq. 3–4): "learn both which candidate is closest and how much closer it is compared to others" (Sec. 1). Evaluation uses graded NDCG relevance (1 km → 1.0, 25 km → 0.8, …, >2500 km → 0; App. F).
- *Mapping:* query = failed trajectory τ; candidates = steps k (all, or the top-N from a screener); distance d_k = |k − t*| in steps (or better: a counterfactual distance, 1 − φ(τ,k,δ) from proposal 1, or min distance to any step in a set-valued label); scorer = LoRA'd LLM with a value head on the final token of a prompt "{task} {trajectory prefix window around k} How far is step k from the decisive error? Negatives: {steps certified correct}". Train with L⁽¹⁾ (K⁽¹⁾=1 or = |error set|) + L⁽²⁾. Output: a full ranked list → exact, ±k and nDCG natively; also the "who" via the top step's agent. Supervision L2 for index distance; L1+ for effect-based distance (continuous relevance is exactly what a listwise loss wants); text-only.
- *Datasets:* train on large injected sets (Who&When-Pro 12k, TracerTraj 4k, CORRECT-Error 2.2k) and on human sets with graded relevance from annotator votes (MP-Bench: 3 annotators → relevance 1.0/0.67/0.33; TrajErrBench κ 0.91/0.67); test on Who&When, LongRCA (median 145 steps — candidate pool must be screened), AgentRx, SearchAuditBench (tolerance spans give natural graded relevance). Baselines: prompted LLM all-at-once / step-by-step / binary-search (Who&When protocol), pointwise step classifier with BCE, pairwise RankNet.
- *Relation:* new formulation (attribution as graded ranking) and a direct consumer of proposal 1's effect profile as soft labels; complementary to proposal 2 (h_t gives a cheap screener, Card 7.2).
- *Main risk:* step-index distance is not semantic distance (step 3 and step 4 may belong to different agents, and being "off by 20 steps in the same agent's loop" can be more acceptable than off by 1 across agents) — define d_k with care (index + same-agent + same-subtask terms); injected sets have skewed error positions, so a ranker trained there may learn position priors; GeoRanker's K⁽¹⁾>1 degradation suggests set-valued labels need an explicit multi-target variant; context length for long trajectories.
- *Plausibility 5, Effort M.*

**Card 7.2 — Oracle-in-top-k diagnostic and two-stage screen-then-rerank attribution.**
- *Mechanism in paper:* Fig. 1 motivates the whole paper: "although the current SOTA model achieves 16.7% accuracy ..., better candidates often exist among the top-k retrieved results" (top-5 23.3%, top-10 28.0%, top-20 32.7%); Table 7 and Fig. 3 show accuracy rises with the candidate pool size then saturates; the limitation section proposes skipping reranking when the top-k is already geographically concentrated.
- *Mapping:* for any cheap screener (prompted LLM asked for 5–10 suspicious steps, proposal 2's h_t top-k, surprisal spikes), compute the oracle: fraction of trajectories where t* (or any set member) is within the top-k. This separates "candidate generation" errors from "selection" errors and tells where the 10–30% step accuracy ceiling comes from. Then rerank the top-k with Card 7.1 or with proposal 1's rollouts only on those k steps (cutting rollout cost by T/k). Also the GeoRanker skip rule: if screener candidates are already contiguous (one sub-task), skip the expensive stage. Output: when; supervision whatever the screener uses; text-only.
- *Datasets:* Who&When, MP-Bench, TrajErrBench, LongRCA (long: the oracle curve vs k is most informative here). Baseline: single-pass LLM step prediction.
- *Relation:* strengthens proposal 1 (restricts the perturbation screen to k candidates) and proposal 2 (h_t as the screener; oracle recall@k is a natural metric for it).
- *Main risk:* none technical; the danger is that oracle recall@k is high only for large k on 150-step traces, in which case reranking cost stays large.
- *Plausibility 4, Effort S.*

**Quotable facts.**
1. Fig. 1: G3 16.7% @1 km vs best-of-top-5/10/20 23.3/28.0/32.7% (+39.9/68.1/96.2%).
2. Table 1: IM2GPS3K 1 km 18.79 vs 16.65 (+12.9%); YFCC4K 1 km 32.94 vs 23.99 (+37.3%).
3. Table 2 ablation @1 km: w/o L⁽²⁾ 18.48; w/o negatives 17.35; w/o candidate images 15.58; full 18.79.
4. "GeoRanker surpasses G3 across all levels even when fine-tuned on just 10% samples" (Sec. 4.6, Fig. 5); trainable params 6.88M of 8.30B (Table 4).
5. Table 5 ranking metrics: Recall@1 0.0894→0.1982, NDCG@10 0.6735→0.8419; "K⁽¹⁾ shows a consistent downward trend ... train-test mismatch" (Sec. 4.4).

**Code/data released?** Yes — https://github.com/Applied-Machine-Learning-Lab/GeoRanker (code, checkpoint, GeoRanking dataset: 100k queries / 2M pairs).

---

## 8. GeoArena — "Evaluating Open-World Geographic Reasoning in Large Vision-Language Models" (Jia, Zhang, Zhao, Li, ACL 2026; arXiv 2509.04334v5)

**Paper.** Public arena: user uploads an in-the-wild image + prompt (LLM filter for relevance; 100% on a 200-prompt test, App. A.1), two anonymous LVLMs respond, user votes A / B / tie; identities revealed after voting (Sec. 4.1). Ranking by Bradley–Terry fitted via logistic regression (Eq. 3), rescaled to Elo (×400 + 1000), 95% CIs by 100 bootstrap rounds (Sec. 4.4). 17 models; Gemini 2.5 pro 1319.7 top, GPT-4o mini 871.6 bottom (Table 2); several models within 1040–1050 with overlapping CIs. Reliability: 100 battles re-judged by an expert with web/map access (3–5 min each): 78% agreement with crowd (83.3% left-win, 65.6% tie, 84.4% right-win; Table 3). LLM-as-judge alignment with human votes: Gemini 2.5 pro 65.8%, Qwen2.5-VL-72B 46.7% (Table 4). Style-controlled BT regression (Chatbot-Arena style): length β=0.526, list count 0.095, GPS-output ratio 0.06, headers −0.153, emphasis −0.117 (Sec. 5.6); style-adjusted leaderboard drops Gemma 3 12B from 4th to 9th (Table 6). Dataset: 94.2% outdoor, 45.2% with text, 15.8% with landmarks (App. A.2). Motivation explicitly includes contamination of static benchmarks and absence of ground truth for in-the-wild images.

**Transferable ideas.**

**Card 8.1 — Pairwise-preference arena for attributors, with style-controlled Bradley–Terry and an LLM-judge alignment check.**
- *Mechanism in paper:* "GeoArena reframes evaluation as a pairwise reasoning alignment task ... where human judges compare model-generated explanations based on reasoning quality, evidence synthesis, and plausibility" (Abstract); BT + bootstrap CIs (Sec. 4.4); style confounders regressed out (Sec. 5.6); expert-vs-crowd agreement (Table 3) and LLM-judge alignment (Table 4) as reliability checks.
- *Mapping:* "image" = a failed trajectory (optionally user-submitted fresh runs, which also defuses benchmark contamination); "model response" = an attributor's output (decisive step, agent, category, one-paragraph justification); judges vote which attribution is more convincing; BT over attributors (prompted LLMs, hazard model, perturbation-screen labels, humans) with CIs; regress out justification length/list/header counts. Add the two reliability checks: expert re-judging with replay access (the analogue of "search engines and map services"), and LLM-judge vs human agreement. Output: a ranking of attributors that does not require exact-step agreement; supervision: human preferences (new label type); text-only.
- *Datasets:* MP-Bench (3 annotators, set-valued votes) and Who&When (40–90% agreement) as the sets where exact-step metrics are least trustworthy; TrajErrBench (κ 0.91) as a sanity set where preferences should agree with exact-step accuracy. Baseline: exact-step / ±k accuracy rankings of the same attributors.
- *Relation:* new evaluation protocol; proposal 1's effect-based labels are the natural *validator* of preference votes (do humans prefer attributions that replay-fixes confirm? the paper's own warning is that votes reward verbosity, β_length = 0.526).
- *Main risk:* preference measures persuasiveness, not counterfactual truth; 78% expert–crowd agreement on a 3-way task is decent but ties are judged inconsistently (65.6%); needs a judge pool — in-house experts only, since crowd workers cannot read 100-step traces; sample inefficiency of BT with many attributors.
- *Plausibility 4, Effort M.*

**Card 8.2 — Pairwise *step* comparisons + Bradley–Terry to produce graded, uncertainty-aware step labels.**
- *Mechanism in paper:* BT turns noisy pairwise votes into latent strengths with bootstrap CIs and "distinguish[es] between meaningful performance differences and those that arise from sampling noise" (Sec. 4.4); GeoArena argues label-based evaluation "assumes a well-defined notion of correctness that does not hold when multiple hypotheses are plausible" (Sec. 1).
- *Mapping:* instead of asking annotators for the exact decisive step (40–90% agreement), ask "which of steps i or j is more responsible for the failure?" for sampled pairs (biased toward candidate steps from a screener); fit BT per trajectory → a strength γ_k per step with CIs. γ_k is a graded relevance label (feeds Card 7.1's listwise loss and nDCG), its CI width flags genuinely ambiguous trajectories, and the top-γ step is a consensus t*. Output: when (ranked, with uncertainty); supervision L2 but cheaper per judgement; text-only.
- *Datasets:* re-annotate a subset of Who&When and MP-Bench (where annotator disagreement is documented) to compare BT labels with majority/exact labels; SearchAuditBench tolerance spans as a check. Baseline: majority vote over three annotators (MP-Bench protocol).
- *Relation:* new labelling protocol; complements proposal 1 (compare BT strengths with effect profiles φ(τ,k,δ) — if they agree, cheap pairwise votes can replace rollouts for labelling).
- *Main risk:* pairwise judgements on long traces are still slow; BT assumes transitivity/one-dimensional "responsibility", which fails when two independent errors each suffice (set-valued ground truth); need O(T log T) pairs per trajectory unless screened.
- *Plausibility 3, Effort M.*

**Quotable facts.**
1. Expert–crowd agreement on 100 battles: 78.0% overall; 83.3% / 65.6% / 84.4% for left-win / tie / right-win (Table 3).
2. LLM-as-judge alignment with humans: Gemini 2.5 pro 65.79%, Qwen 2.5 VL 72B 46.67% (Table 4).
3. Style coefficients: β_length 0.526, β_list 0.095, β_GPS 0.06, β_header −0.153, β_emphasis −0.117 (Sec. 5.6); "Gemma 3 12B falls from 4th to 9th" after style adjustment (App. A.7).
4. "static benchmarks are increasingly vulnerable to data contamination from web-scale pretraining, outcome-level metrics collapse complex reasoning processes into a single label match, and authoritative ground truth is often unavailable" (Sec. 1).
5. Dataset composition: 94.2% outdoor, 45.2% with text, 15.8% with landmarks (App. A.2).

**Code/data released?** Yes — platform and code at https://github.com/Applied-Machine-Learning-Lab/ACL2026_GeoArena; anonymized images and votes released with user consent.

---

## Batch ranking (top ideas across the batch)

1. **Card 7.1 — Distance-aware listwise step ranker (GeoRanker's first+second-order PL loss, LoRA'd LLM + value head), trained on injected sets / vote-graded human sets, consuming proposal 1's effect profile as continuous relevance.** Plausibility 5, Effort M. The one idea in this batch I would start next week.
2. **Card 7.2 — Oracle-in-top-k diagnostic and screen-then-rerank pipeline** (is the 10–30% step-accuracy ceiling a candidate-generation or a selection problem?). Plausibility 4, Effort S.
3. **Card 4.1 — KDS contamination audit of Who&When / MAST / TRAIL etc. for every open-weight attributor model, with fresh trajectories as the λ=0 anchor** (optionally laundering-aware, Card 5.1). Plausibility 4, Effort S–M.
4. **Card 8.1 — Pairwise-preference arena for attributors with style-controlled Bradley–Terry, expert re-judging and LLM-judge alignment check**, validated against replay-based labels. Plausibility 4, Effort M.
5. **Card 6.1 — Unified attribution harness (adapter protocol, canonical set-valued/ordinal label schema, shared metric library)** — infrastructure that both proposals and ideas 1–4 need. Plausibility 4, Effort M–L.

Runners-up: Card 8.2 (BT over pairwise step comparisons → graded labels with CIs; 3), Card 5.2 (goal–detail repair search with accept-if-improves replay; 3), Card 3.1 (hierarchy-stratified repair footprint; 3). Zero-idea papers: gradient leading terms (pure LM-training theory); MxD contributes only low-plausibility grey-box cards.
