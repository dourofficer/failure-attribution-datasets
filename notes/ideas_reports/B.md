# Batch B — reliability of vision-language / multimodal models

Reader angle: evidence (tool observation) vs prior (what the agent expected); abstention on unsolvable inputs; bootstrapping detectors from unlabeled data; self-adversarial training. Seven papers, 11 idea cards (strict: two papers get one card at plausibility ≤ 3, none padded).

Supervision levels: L2 step labels, L1+ several continuations of a prefix, L1 outcome only, L0 raw logs. "Grey-box" = needs hidden states / log-probs of an open model (self-collected runs, or teacher-forced re-encoding of released text logs by a proxy open model).

---

## 1. GLSim — Park & Li, NeurIPS 2025 (arXiv 2508.19972v3)

**Paper.** Training-free object-hallucination score for LVLMs, computed inside the generating model in the same forward pass. For every object mention o in a generated caption: *global* score = cos(h_{l'}(o), h_l(last token of the multimodal instruction prompt)); *local* score = mean over the top-K image patches of cos(h_l(v_i), h_{l'}(o)), where the K patches are chosen by a "visual logit lens" (softmax(h_l(v_i)·W_U)[o], i.e. which patch hidden states unembed to the object word). Final score 0.6·global + 0.4·local (Eq. 5); LLaVA-1.5-7B uses l=32, l'=31, K=32 ≈ 6% of 576 patches (Table 5, Fig. 5a). No training, hyperparameters from a validation split. Evaluated as object-level binary classification (real vs hallucinated via CHAIR string match) on 5k MSCOCO + 5k Objects365 images × LLaVA-1.5-7B/13B, MiniGPT-4, Shikra, plus five newer models (InstructBLIP, LLaVA-NeXT, Cambrian-1, Qwen2.5-VL, InternVL3). AUROC 83.7 on MSCOCO/LLaVA-7B vs Contextual Lens 75.4, SVAR (attention) 74.7, Internal Confidence (logit-lens prob) 72.9, NLL 63.7, entropy 64.0 (Table 1). Attention-based patch selection is the worst grounding method (66.3 vs 78.8 for logit lens, Table 3). Extends to attribute/relation hallucinations by averaging token scores over spans (Table 8, GPT-4o pseudo-labels).

### Idea 1a — Claim-grounding score for agent assertions (global+local hidden-state similarity)
- **Mechanism in paper.** §4.2–4.3, Eqs. 2–5: score an emitted content word by (i) similarity to the condensed context representation (last prompt token) and (ii) similarity to the top-K evidence tokens that "predict" it under the logit lens; the two are complementary ("does this object belong contextually?" vs "is there concrete visual evidence?", §1). Finding 1 (§5.3): embedding similarity > attention weights > token probability for detecting ungrounded mentions.
- **Mapping.** Sample = an agent message s_t; "object mention" = a factual claim span in s_t (number, file name, test verdict, page fact, extracted entity); "image" = the preceding tool observation(s) o_{<t} in the context. Compute, with an open model reading the trajectory (teacher-forced), (i) global: cos between the claim-span hidden state at a late-intermediate layer and the hidden state of the last token of the latest observation block; (ii) local: cos between the claim-span state and the top-K observation tokens selected by logit lens for the claim's first token (or, text-fallback, by max cosine as in Contextual Lens). A low-scoring claim = assertion with no support in the evidence → candidate error step ("when") and category "hallucinated/misread observation" ("what"). High global + low local is exactly the "contextually plausible but unsupported = answered from prior" signature (Fig. 2a). Output: per-step ungroundedness score; L0 (no labels needed to compute, L2 only to validate); grey-box.
- **Datasets / baseline.** AgentHallu (443 hallucinated + 250 clean, step + cause) is the natural validation set if the runs can be re-encoded by an open model; TraceElephant (full per-call inputs) for teacher-forced re-encoding; self-collected SWE/GAIA runs with open models for the native (same-model) setting. Baselines: NLL/entropy of the claim tokens, SelfCheck-style sampling consistency, prompted LLM judge on the same step, Lookback-Lens-style attention ratio.
- **Relation to proposals.** New signal; plugs into proposal 2 as a per-step covariate of the hazard h_t, and into proposal 1 as a cheap pre-screen to choose which steps to spend rollouts on.
- **Main risk.** The visual logit lens works because image-token states carry content, not next-token predictions; text observation tokens at late layers encode *their own next token*, so top-K selection may land on the token *before* the copied fact rather than on it. Need a text-specific grounding (max-cos / attention / induction-head reads) and the paper's own Table 3 says attention is the weakest option. Also claims that are *correctly copied but irrelevant* will score high.
- **Plausibility 3 / Effort M.**

### Idea 1b — GLSim as-is on GUI/screenshot agents for perception-error steps
- **Mechanism in paper.** Same as above; object existence scoring per mention, including multi-token objects (first token, Table 11), on Qwen2.5-VL-7B / InternVL3-8B (Table 7: 76.1 / 73.2 AUROC).
- **Mapping.** Sample = a GUI/web-agent step whose message names UI elements ("the Submit button", "a date picker", "the price $42") while a screenshot is in context. Score each element mention with GLSim against the screenshot tokens; low score = the agent "saw" something not present → perception-error step. Output: when + what (perception vs planning). Grey-box, L0 to compute.
- **Datasets / baseline.** TraceElephant (220 runs, screenshots + full LLM-call inputs, replayable) and Who&When Pro image/GUI subset; needs either an open VLM agent or re-encoding of the stored (screenshot, prompt, response) by an open VLM. Baseline: VLM judge asked "is this element visible?", POPE-style yes/no probing (GLSim paper reports 2.8–1.0 pt precision gain and 5× lower latency vs POPE, Table 9).
- **Relation to proposals.** New; a modality-specific feature for both.
- **Main risk.** GUI screenshots are text-dense; GLSim was tuned on natural COCO/Objects365 scenes; element mentions are often multi-word and functional ("the login form"), not nouns with a single visual referent. Perception errors are one slice of GUI failures; the share in TraceElephant is unknown to me.
- **Plausibility 3 / Effort M.**

**Quotable facts.**
1. "GLSIM consistently outperforms existing state-of-the-art approaches ... achieving up to a +12.7% improvement in AUROC" (Shikra/MSCOCO vs SVAR, §1 & §5.2).
2. Token-probability detectors are near chance-ish: NLL 63.7 / entropy 64.0 AUROC vs 83.7 for GLSim on MSCOCO LLaVA-1.5-7B (Table 1, p.7).
3. Grounding patches by attention 66.3 vs cosine 76.2 vs logit lens 78.8 AUROC (local score, Table 3, p.8) — "high attention weights tend to be assigned to irrelevant regions".
4. Global score with last-instruction token 79.3 vs average image token 71.3 vs last image token 65.9 (Table 4).
5. One forward pass; 1.6 s/image vs 8.1 s for POPE prompting and 9.3 s for an external-model judge (Tables 9–10, Appendix D.4–D.5).

**Code/data.** Code released: github.com/deeplearning-wisc/glsim.

---

## 2. Unsolvable Problem Detection (UPD) — Miyai et al., arXiv 2403.20331v4 (Jun 2025)

**Paper.** A benchmark, not a method. From MMBench-dev (1,164 Qs) they remove 13% image-agnostic questions (text-only GPT-4 under CircularEval + manual check), then build three unsolvable variants of each solvable MCQA: AAD (delete the correct option; 820 Qs), IASD (swap in an unrelated option set; 919), IVQD (swap in an unrelated image; 356) — 2,095 questions, each paired with its solvable twin. Metric: *Dual accuracy* = correct on the standard twin AND withholds on the unsolvable one; three prompt regimes (Base, +"None of the above" option, +explicit instruction). 17 open + 5 closed LMMs, GPT-4o-mini extracts the choice (90–99% agreement with humans, Fig. F). Findings: open-source LMMs with >80% standard accuracy score <6% Dual in Base (LLaVA-OV-7B 4.5/5.5/2.5); correlation between standard and UPD accuracy only 6.5–39.1 (Table 2); a *bottleneck test* that puts the correct answer in the text ("The answer is three. Choose the option...") separates LLM-side refusal failures from vision-side failures (§5.4, Fig. 5); CoT/self-reflection help only LLM-bottlenecked models (Table 3); LoRA tuning with 6:2:2 Standard:AAD:IVQD on 10k A-OKVQA samples helps but hurts general tasks (App. D). Error analysis: GPT-4o "tends to select the option that is closest to the masked answer" and sometimes "the correct answer is reached within the reasoning process but the final answer is incorrect" (App. F.1).

### Idea 2a — Dual-accuracy (paired) evaluation for attribution judges
- **Mechanism in paper.** §4.2: a prediction counts only if the model is right on the solvable twin *and* abstains on the unsolvable twin; "Original Standard" is the upper bound. Table 2 shows single-condition accuracy is nearly uncorrelated with the paired metric.
- **Mapping.** Attribution judges are evaluated on failure-only sets (Who&When, MP-Bench, LongRCA ...), so a judge that always names *some* step is never penalised for flagging clean runs. Proposal: for every failed run, pair it with a matched successful run (same task/framework) and count a hit only if the judge localises t* (±k) in the failure AND reports "no decisive error" on the success; report Dual step accuracy next to the usual step accuracy. Output: metric for when/who/what; L2 on failures + outcome label on successes.
- **Datasets / baseline.** AgentHallu (443 failures + 250 clean runs), HORIZON (1,284 successes), Failure-as-a-Process (610 PASS, if trajectories are available), TRAIL successes; also injected sets (Who&When Pro) where the pre-injection run is the clean twin. Baseline: current single-condition step/agent accuracy of GPT-class judges (~55% agent / 10–30% step).
- **Relation to proposals.** New evaluation protocol; directly measures the false-alarm side of proposal 2's P(fail|prefix) and of any judge; cheap to add to the survey's metric table.
- **Main risk.** Successful runs may still contain recovered errors (set-valued labels in MP-Bench show humans disagree); "no decisive error" must be defined as "no unrecovered error", otherwise the pair is unfair.
- **Plausibility 4 / Effort S.**

### Idea 2b — Unsolvable-observation injection on successful runs (AAD/IASD/IVQD for tools)
- **Mechanism in paper.** §4.1 / App. B: three systematic, cheap corruptions that make a solvable instance unsolvable while keeping it superficially well-formed; manual filtering of ambiguous cases; measure whether the model abstains or fabricates.
- **Mapping.** Take a successful replayable trajectory, pick step k, and corrupt the *observation* so the task is no longer solvable from it: (AAD) delete the needed fact from the tool output / search result; (IASD) return a well-formed but irrelevant result (wrong file, wrong page section); (IVQD) return the output of a different tool/page. Replay from k. Label by construction: t_err = k (evidence removed), and the agent's reaction is categorised as abstain/retry (correct), fabricate (hallucination), or ignore (prior-driven continuation). This produces an injected failure set whose error *position* is uniform in k (unlike Who&When Pro/Aegis, which skew to start/end) and whose failure mode is "evidence missing" — the mode that proposal 1's δ-fix cannot repair at k (the fix must be a retry). Output: when + what; L1 outcome via replay; text-only.
- **Datasets / baseline.** Replayable environments: τ²-bench / SWE-Bench Pro (TrajErrBench), ALFWorld/WebShop (AgentErrorBench), SymFail event graphs, TraceElephant replay. Compare detectors trained on this set vs on Who&When Pro for transfer to natural failures (Who&When, LongRCA).
- **Relation to proposals.** Strengthens proposal 1: it is the fragility-curve experiment with a principled perturbation family and a paired metric; also supplies hard negatives for proposal 2 (steps where the evidence is fine but the agent abstains anyway).
- **Main risk.** Corruptions must be "manually removed if ambiguous" (the paper filtered many); automating that needs a verifier; agents with retry loops will trivially recover, so the measurement is about the *first reaction*, not the outcome.
- **Plausibility 4 / Effort M.**

### Idea 2c — Bottleneck test as a repair family: "give the reading" vs "give the decision"
- **Mechanism in paper.** §5.4 / Fig. 5: prompt the LMM with the correct answer stated in text; if it now refuses correctly, the failure was perception; if not, the failure is on the language/refusal side. CoT/self-reflection then help exactly the language-bottlenecked models (Table 3).
- **Mapping.** For a candidate error step t, define two minimal interventions δ_read = "append the correct extraction of o_{t-1} to the prompt" and δ_decide = "append the correct action". If δ_read alone repairs the continuation (P(success) ↑), category = observation misreading/perception; if only δ_decide does, category = reasoning/planning; if neither, the error is earlier (t* < t). Output: what (two-way), and a consistency check on when. L1+ via rollouts; text-only.
- **Datasets / baseline.** Replayable sets as in 2b; compare the induced category against human "what" labels in TrajErrBench (κ 0.91/0.67), AgentErrorBench (module+type), AgentRx (9 categories).
- **Relation to proposals.** Strengthens proposal 1: a concrete, two-element δ family whose contrast yields the taxonomy label instead of a free-text LLM category.
- **Main risk.** Requires a ground-truth "correct reading" per step, which only exists where the task has a verifier or a human label; for long GAIA-style runs the correct reading is itself ambiguous.
- **Plausibility 3 / Effort M.**

**Quotable facts.**
1. 2,095 unsolvable questions (820 AAD / 919 IASD / 356 IVQD) paired with solvable twins; 13% of MMBench removed as image-agnostic (§4.1, App. B.1).
2. LLaVA-OV-7B: Original Standard 86.0/82.5/84.8 but Base Dual accuracy 4.5/5.5/2.5; GPT-4o 45.6/56.1/65.2 (Table 1).
3. Correlation between Original Standard and UPD accuracy: max 39.1, min 6.5 (Table 2) — "the community's efforts to improve performance on existing benchmarks do not directly contribute to enhancing model reliability" (§1).
4. Self-reflection raises GPT-4o AAD Dual from 45.6 to 55.2 while dropping Standard from 80.2 to 69.8 (Table 3) — abstention gains are paid for in recall.
5. "there are cases where the correct answer is reached within the reasoning process but the final answer is incorrect" (App. F.1, Fig. I) — commitment error, not reasoning error.

**Code/data.** Benchmark + eval code: github.com/AtsuMiyai/UPD.

---

## 3. Miscalibration in prompt tuning / DOR — Wang, Li & Wei, ICML 2025 (arXiv 2410.02681v4)

**Paper.** Analyses CLIP prompt tuning (ViT-B/16, 16-shot, base-to-new split on 11 datasets). CE-based tuning (CoOp) raises the *feature divergence* (mean kNN cosine distance) among class text embeddings, widening the max-vs-rest logit gap for all classes, so confidence rises on new classes whose accuracy did not → over-confidence (new-class ECE 14.58 vs 4.61 zero-shot). Regularising toward the hand-crafted prompt (KgCoOp) anchors divergence and confidence → under-confidence on base classes whose accuracy rose (base ECE 5.82). Proposition C.1: E[max softmax] is monotone in logit std. DOR: build a pool of ~5k WordNet nouns that are *near* the base classes in CLIP text space but disjoint from them (Eq. 6–7), resample a batch each iteration and penalise 1 − cos(ψ_tuned(outlier), ψ_zero-shot(outlier)) (Eq. 8) — i.e. regularise where you have no labels, leave the labelled classes free. CoOp+DOR: new ECE 6.49, base 2.67, HM accuracy 72.4→77.6 (Tables 1, 6); near-OOD outliers 7.09 vs random 7.33 vs far 7.72 vs oracle new classes 4.34 (Table 8); gradient conflict with CE concentrated in (−0.1, 0.1] vs [−1, 0] for KgCoOp/PromptSRC (Fig. 7).

### Idea 3 — Outlier-anchored calibration of fine-tuned attribution / hazard models
- **Mechanism in paper.** §4, Eqs. 6–9: calibration on unseen classes is preserved by keeping the fine-tuned model's outputs on *unlabelled near-distribution inputs* close to the base model, instead of regularising on the labelled classes (which fights the task loss).
- **Mapping.** Any step-scorer or hazard model trained on labelled failures (L2 from Who&When/TrajErrBench, or exact-by-construction labels from Who&When Pro/Aegis) sees only a few failure modes and frameworks; on new frameworks / natural failures it will be over-confident in the same way CoOp is on new classes. DOR analogue: during fine-tuning, draw batches of unlabelled trajectories/steps from *other* frameworks and tasks (HORIZON 3.8k, MAST-Data 1.6k, TracerTraj 4k, or own L0 logs), and add a term keeping the fine-tuned model's step-score distribution (or P(fail|prefix)) on them close to the pre-fine-tuning model's. Diagnostic from §3.2: track the spread of per-step logits (softmax over positions) before/after tuning — a growing top-vs-rest gap on unlabelled runs predicts over-confident step picks. Output: better-calibrated P(fail|prefix) and step posteriors; needs L2 or synthetic labels for the task loss, L0 for the regulariser; text-only.
- **Datasets / baseline.** Train on Who&When Pro (skewed positions), evaluate ECE/step accuracy on Who&When, LongRCA, TrajErrBench; baselines: plain fine-tune, KL-to-reference on the labelled set (KgCoOp analogue), temperature scaling.
- **Relation to proposals.** Complements both: proposal 1's surrogate f(prefix, step, δ) and proposal 2's hazard model are both fine-tuned predictors whose calibration on natural failures is a stated metric.
- **Main risk.** DOR works because zero-shot CLIP is already well calibrated (ECE ~4) so anchoring to it is a good target; a prompted-LLM base attribution model is *not* well calibrated, so anchoring may preserve a bad prior. The effect may be swamped by the synthetic→natural position shift, which is a covariate shift DOR did not address (its covariate-shift gains were modest, Table 5).
- **Plausibility 2 / Effort M.**

**Quotable facts.**
1. CoOp: new-class ECE 14.58 (zero-shot 4.61); KgCoOp: base-class ECE 5.82 (CoOp 3.07) — "a trade-off of calibration between base and new classes" (Table 1, 3; Abstract).
2. DOR cuts CoOp new-class ECE 14.58→6.49 and raises new-class accuracy 61.74→72.01 (Tables 1, 6).
3. Near-OOD outliers 7.09 vs random 7.33 vs far-OOD 7.72 vs oracle 4.34 new-class ECE (Table 8) — random outliers are already a strong regulariser.
4. Proposition C.1: for logits ~N(μ, σ²), E[max softmax] increases with σ (Appendix C) — logit spread, not accuracy, drives confidence.
5. Gradient-conflict distribution: DOR mostly in (−0.1, 0.1], base-class regularisers mostly in [−1, 0] (Fig. 7, App. B.2).

**Code/data.** Code: github.com/ml-stat-Sustech/Outlier-Calibration.

---

## 4. Why multimodal ICL lags behind — Wang & Li, arXiv 2604.13403 (Apr 2026)

**Paper.** Controlled outlier-detection ICL task (identify the single minority item by shape or colour; the rule must be inferred from demonstrations) rendered identically as text and as images. Zero-shot parity, but 4-shot multimodal drops 24.8 pts for Qwen2.5-VL-7B (88.4→63.6) and 18.5 for Gemma-3-12B (Table 1). Error split: Case 1 false task recognition vs Case 2 right rule, wrong answer; both inflate in the image version (Fig. 3). Mechanism via attention: demonstration *label* tokens attend to the correct evidence region in mid layers even when the final answer is wrong (Finding 1, Fig. 4–5); the query's last token attends to demonstration labels/evidence only in late layers, where the mapping is no longer represented (Finding 2, Fig. 6) — "task mapping construction and task application are decoupled across different layers". Causal check: replacing attention over image tokens by a uniform distribution (UAS) collapses 4-shot accuracy to ≈ zero-shot (Qwen-7B 69.1→45.4; Table 2). Correct vs error samples differ mainly in *late-layer* attention to evidence (Fig. 6 difference plots). Fix (MGI): pick the peak grounding layer ℓ* = argmin attention entropy of label→image attention (Eq. 1), amplify the query's attention to the salient image tokens (> 1.5× mean) in layers > L_start by λ (Eq. 5); gains ≤ ~1.1 pts (Table 3), 876 ms setup per query. App. C.1 replicates the mid-construct/late-consume pattern on 50 hand-annotated MM-Vet items (mid-layer attention to correct regions 3–9× other regions). App. C.2: Qwen attends text-dominantly at every layer; Gemma alternates modalities; only a few heads attend to demonstrations at all.

### Idea 4a — Observation-ablation sensitivity: a one-pass counterfactual for "ignored evidence"
- **Mechanism in paper.** Table 2 / §4.1 causal intervention: remove the model's access to the evidence (uniform attention over image tokens) and measure how much the prediction depended on it; the drop to zero-shot level proves the prediction *was* evidence-driven. Fig. 6: error samples are those whose final-layer attention to evidence is low.
- **Mapping.** For agent step t with observation o_{t-1} and emitted action a_t, compute Δ_t = log p(a_t | prefix with o_{t-1}) − log p(a_t | prefix with o_{t-1} ablated) (ablation = blank/placeholder, or a shuffled observation from another step = UPD's IVQD; grey-box variant = zero the attention to the observation span). Δ_t ≈ 0 means the agent would have emitted the same action without reading the evidence — a prior-driven step. In a failed run, the earliest step with Δ_t ≈ 0 *and* an observation that contradicts the prior (detected by a cheap textual contradiction check) is a candidate t*; category "ignored observation / confirmation bias". Output: when + what, plus a per-step covariate for P(fail|prefix). Needs log-probs of the emitting model (open model or API logprobs); L0 to compute. Two forward passes per step, no environment rollout.
- **Datasets / baseline.** Self-collected runs with open models (needed anyway for proposal 1); AgentHallu for validating against human "hallucinated step" labels after teacher-forced re-encoding; SearchAuditBench (deep-search, 1,243 runs with root cause) where "ignored retrieved evidence" is a labelled root cause. Baselines: prompted judge, NLL/entropy of a_t, attention-ratio (Lookback Lens) feature.
- **Relation to proposals.** Strengthens proposal 1: it is an *execution-free* surrogate of the repair-effect profile restricted to input-side perturbations (how much does the agent's own action depend on its evidence), usable as the prior for which k to roll out; gives proposal 2 a mechanistic covariate.
- **Main risk.** Many correct steps legitimately do not depend on the latest observation (planning, formatting), so Δ_t ≈ 0 alone is not an error; it must be conjoined with "the observation mattered" (e.g. a verifier says the observation contained the needed fact). Teacher-forced re-encoding with a different model than the one that acted changes the semantics of Δ_t.
- **Plausibility 4 / Effort S–M.**

### Idea 4b — Late-layer evidence-attention as an observation-neglect feature
- **Mechanism in paper.** Fig. 6 and App. C.1: correct predictions keep "significantly higher attention to evidence regions in late layers compared to error samples"; the diagnostic quantity is attention from the answer token to annotated evidence tokens, by layer; peak layer found by entropy (Eq. 1).
- **Mapping.** Per agent step, the mass of late-layer attention from the first action tokens to (a) the latest observation span vs (b) the agent's own earlier messages/system prompt. Low (a)/(b) ratio = the step was written from the agent's prior. Combine with Idea 1a (GLSim warns attention grounding is the weakest signal, so use it as one covariate, not the detector). Output: per-step feature; grey-box; L0.
- **Datasets / baseline.** As 4a. Baseline: Lookback Lens (context-vs-generated attention ratio for RAG hallucination), which is the text analogue.
- **Relation to proposals.** Covariate for proposal 2; cheap pre-screen for proposal 1.
- **Main risk.** The paper itself shows attention allocation is architecture-specific (Qwen text-dominant everywhere, Gemma alternating) and concentrated in a few heads, so a single aggregate ratio will need per-model calibration; GLSim's Table 3 shows attention grounding loses 12 AUROC to similarity grounding.
- **Plausibility 3 / Effort M.**

**Quotable facts.**
1. Qwen2.5-VL-7B 4-shot: text-only 88.40 vs multimodal 63.60 (−24.8); Gemma-3-12B 91.40 vs 72.93 (Table 1); zero-shot is at parity.
2. Uniform Attention Suppression over image tokens: 69.09→45.44 (Qwen-7B, zero-shot 45.20), Gemma-3-27B 78.62→0.0 (Table 2).
3. Finding 1: label→evidence grounding in mid layers "emerges regardless of whether the final prediction on the query is correct or not" (§4.1).
4. MM-Vet replication: mid-layer attention to correct regions 3–9× other regions; Gemma-3-12B L11–L23 ≈0.02–0.05 vs 0.003–0.006, late L30+ 0.0015 vs 0.0032; query attention to evidence ~1e-4 in L10–20 rising to ~1e-3 at L29+ (App. C.1).
5. MGI improves 4-shot accuracy by ≤1.1 pts (Table 3) at 876 ms per-query setup cost (App. C.4) — the mechanism is real but the fix is small.

**Code/data.** "Our code is available here" (link not present in the text extraction); models are public checkpoints.

---

## 5. VLMGuard — Fang et al., TMLR 07/2026 (arXiv 2410.00296v2)

**Paper.** Malicious-prompt detection from an *unlabelled* deployment mixture P = (1−π)P_benign + πP_malicious with small π (Huber contamination). Stage 1: take the last-token hidden state f_i of each prompt at an intermediate layer (Qwen2.5-VL-7B; best layer mid-stack, Fig. 4b; Fig. 7 uses layer 8), centre by the mixture mean, SVD, and score κ_i = (1/k) Σ_{j≤k} λ_j ⟨f_i − μ, v_j⟩² — variance-weighted projection energy on the top-k singular directions (Eq. 6). Rationale: with rare contamination the mean is benign, so the leading variance directions are pulled toward the malicious offset; Lemma K.1 Σ = Σ_within + π(1−π)δδᵀ, Theorem K.3 gap ≥ (1−2π)α_kΔ² − 2kσ². Threshold at a quantile → noisy pseudo-partition (precision 25%, recall 83%, 0.08% leakage at π=0.005, Table 12). Stage 2: 3-layer MLP trained on the pseudo-labels; it denoises and is robust to paraphrase, where the raw κ is not (§3.3, Fig. 2b–c). AUROC (π=0.005) 94.79 avg on Qwen-7B vs HiddenDetect 76.57, ASTRA 82.70, GPT-5.4 judge 89.40 (Table 1); 88.16 with a single malicious example (π=0.001, Fig. 3b); 99.05/96.82/97.48 on Qwen-72B (Table 2); works text-only (79.65 vs 62.84 self-judge, Table 11). Layer-wise summation hurts (81.48 vs 91.95, Table 3); last token > mean pooling > earlier positions (Table 7). Hyperparameters (layer, k, threshold) chosen on 100 labelled validation prompts.

### Idea 5a — Unlabelled-mixture subspace bootstrapping of a step-anomaly scorer (L0/L1)
- **Mechanism in paper.** §3.1–3.2: no labels; exploit that the rare class shifts the leading covariance directions; score by projection energy; pseudo-label; train a small classifier that generalises better than the raw score.
- **Mapping.** Units = agent steps (or whole trajectories). Representation = hidden state of the last token of the agent's action at a mid layer (grey-box) or, text-only, a sentence embedding of (observation, action). Error steps are rare contamination (1–3 per 10–150 steps ⇒ π ≈ 0.01–0.03, exactly the regime of Fig. 3b/Table 6). Centre over the corpus, SVD, κ-score, pseudo-label the top quantile, train an MLP → per-step anomaly score → ranked candidate steps (nDCG), with the earliest high-scoring step as t*. **Outcome-conditioned variant (L1):** replace the unsupervised top singular direction by the mean-difference direction between steps of FAIL runs and steps of PASS runs (that is exactly the δ of Lemma K.1, estimated with the outcome as a weak label); project steps of a failed run onto it and rank. Output: when (ranked list), P(fail|prefix) proxy via cumulative max; L0 or L1; grey-box preferred, text-only possible.
- **Datasets / baseline.** Needs successes for the L1 variant: AgentHallu (443/250), HORIZON (1,284 successes), TRAIL, Failure-as-a-Process (610 PASS). Grey-box on self-collected runs. Baselines: OAT (one-class model of successful trajectories), proposal 2's L0 change-point mixture, random/last-step ranking, prompted judge.
- **Relation to proposals.** New method at L0/L1; complementary to proposal 2 (κ can be the emission feature of the hazard/change-point model; the pseudo-partition can initialise it); offers the first real competitor baseline for L0 beyond OAT.
- **Main risk.** The paper's own §3.3 concedes the top singular directions capture "phrasing patterns, instruction style, prompt length"; in trajectories the dominant variance is tool type, position, task — not erroneousness — so the unsupervised variant may need within-tool-type centring or the L1 direction. Representation choice matters a lot (last token > pooling by 4.4 AUROC, Table 7; layer-wise sum −10).
- **Plausibility 3 (L0) / 4 (L1 variant) / Effort M.**

### Idea 5b — Pseudo-label-then-classify to denoise cheap step labels
- **Mechanism in paper.** §3.3, Fig. 2b–c, Fig. 4a: a classifier trained on a 25%-precision pseudo-partition beats thresholding the score that produced the partition, and is robust to surface perturbations.
- **Mapping.** Use noisy, cheap step labels — LLM-judge labels (MAST-Data, HORIZON trace-level flags), injected positions (Who&When Pro, skewed), or κ-scores — as pseudo-labels to train a lightweight classifier on representation features, then evaluate on human step labels. Output: when/what; weak-L2 → L2 evaluation; grey-box or text embeddings.
- **Datasets / baseline.** Train on Who&When Pro + MAST-Data pseudo-labels; test on Who&When, TrajErrBench, MP-Bench. Baseline: the pseudo-labeller itself; direct fine-tune on the small human set.
- **Relation to proposals.** Minor; a training recipe usable by both proposals' learned components.
- **Main risk.** Generic; the denoising works in VLMGuard because the pseudo-negatives are almost clean (0.08% leakage) — LLM-judge negatives in agent traces are far noisier.
- **Plausibility 3 / Effort S.**

**Quotable facts.**
1. Avg AUROC 94.79 (Qwen2.5-VL-7B, π=0.005) vs HiddenDetect 76.57, ASTRA 82.70, GPT-5.4 as judge 89.40 (Table 1).
2. "even in the extreme case of π = 0.001, where only one malicious example in the unlabeled dataset is available, VLMGuard still achieves a strong AUROC of 88.16%" (§4.3, Fig. 3b).
3. Pseudo-partition at π=0.005: precision 25.00%, recall 83.33%, contamination of the benign pool 0.08% (Table 12) — the downstream classifier tolerates 75% false pseudo-positives.
4. Last-token representation 91.95 vs mean pooling 87.53 vs 1/3-position 82.93 AUROC (Table 7); summing layer-wise scores drops to 81.48 vs 91.95 for the best single layer (Table 3).
5. Theorem K.3: E[κ_k|m] − E[κ_k|b] ≥ (1−2π)α_kΔ² − 2kσ²; empirically the top-10 subspace captures ≥80% of the mean-shift energy even at π=0.005 (Table 17).

**Code/data.** Code: github.com/radiolab-ntu/vlmguard; datasets are public safety benchmarks (JailBreakV-28K, GPT4V-Caption, VLGuard, MLLMGuard, MSSBench).

---

## 6. UniGame — Su et al., arXiv 2511.19413v3 (Mar 2026)

**Paper.** Self-adversarial post-training for unified multimodal models (Janus-Pro-7B; also BLIP-3o, Chameleon, two toy UMMs). A 3-layer MLP perturber C (2.1M params) adds a bounded perturbation (ε_max=0.02, learnable scalar gate) to the post-LM fused visual tokens; the generation branch G decodes the perturbed tokens into a *realistic* image; candidates pass a CLIP text–image consistency filter (≥0.6) and a hardness score H = CE of the understanding branch on the decoded image (60th percentile per batch); hard ones go into a 50-item replay buffer. Minimax: C maximises U's loss − λ‖δ‖² (Eq. 7); U (LoRA) minimises clean CE + β·buffer CE (β=0.5, Eq. 6). gen_lr/und_lr ≈ 250 needed for a stable "tug-of-war". VQAv2 79.5 (SFT) → 83.4; NaturalBench 73.8→78.6; AdVQA 34.2→40.4; consistency score +4.66 (Tables 1–4, 9). Key ablation (Table 4): embedding-space adversarial perturbation gives +0.7 at best; forcing the perturbation through the decoder ("on-manifold") gives +2.0 before any filtering, +3.9 with CLIP + buffer. Theory: first-order equivalent to a Jacobian-norm penalty λε_max E‖∇_z ℓ_U‖ (Prop. 2); decoder-constrained perturbations "inflate" the data manifold toward high-gradient regions (Lemma 1). Hard-sample loss stays above clean/adversarial loss for 5k steps (Fig. 4b).

### Idea 6 — Learned on-manifold observation adversary for fragility curves and realistic injection
- **Mechanism in paper.** §3.3–3.4, Eqs. 4–7, Table 4: a small learned perturber searches for the *most confusing yet realistic and semantically valid* input, realism enforced by decoding through the model's own generator and a consistency check; hard cases are mined into a buffer; realism (decoder constraint) matters more than adversarial strength.
- **Mapping.** For successful replayable runs, replace the hand-written injection of Who&When Pro/Aegis by a learned adversary over *observations*: an LLM rewriter (the "decoder") proposes paraphrases/truncations/reorderings of o_{k} that must pass a semantic-preservation check (the needed fact is still present, verified by a checker — the CLIP-filter analogue), scored by hardness = drop in log p(correct a_{k+1}) or by rollout failure rate; keep the hardest in a buffer, iterate. Output: (i) fragility curve per position k with *worst-case realistic* perturbations rather than random ones (proposal 1), (ii) an injected dataset whose failures are "evidence present but misread" with t_err = k by construction, position-uniform, more natural than appended errors. Supervision: L1 via replay; text-only.
- **Datasets / baseline.** Replayable: τ²-bench, SWE-Bench Pro, ALFWorld/WebShop, SymFail. Baseline: Who&When Pro-style LLM-authored injection; random observation noise (UniGame's Table 4 "random noise" row is the analogue and *hurt*, 78.5 vs 79.5).
- **Relation to proposals.** Strengthens proposal 1 (fragility curves with an adversarial instead of random inject); otherwise a data-generation idea, not an attribution method.
- **Main risk.** No differentiable decoder in text: the minimax becomes black-box search over LLM rewrites, expensive per step and prone to producing perturbations that a verifier accepts but a human would call unfair; the paper's gain is a few points of VQA accuracy, and the agent analogue has no evidence yet. Red-teaming flavour; attribution value is indirect.
- **Plausibility 2 / Effort L.**

**Quotable facts.**
1. Table 4 (VQAv2): SFT 79.5; random token noise 78.5; adversarial embedding 78.9; +cosine+buffer 80.2; decoding only 81.5; +CLIP 82.7; full 83.4 — "on-manifold constraints are inherently superior to token-space constraints".
2. OOD/adversarial robustness: NaturalBench 73.8→78.6, AdVQA 34.2→40.4 (Table 9).
3. Perturber 2.1M params (<1% trainable), ε_max=0.02, buffer 50, CLIP ≥0.6, τ = 60th percentile of hardness, β=0.5, learning-rate ratio ≈250 (§4.1, App. B.2, F.2).
4. Hard-sample loss dominates clean and fresh-adversarial loss for 5k training steps (Fig. 4b) — the buffer keeps finding failures.
5. Prop. 2: adversarial self-play ≈ adding λ·ε_max·E‖∇_z ℓ_U(z)‖ (Eq. 14).

**Code/data.** Code: github.com/AIFrontierLab/TorchUMM.

---

## 7. Visionary-R1 — Xia et al., arXiv 2505.14677v3 (Oct 2025)

**Paper.** GRPO on Qwen2.5-VL-3B with 272.6K CoT-free VQA pairs (11 datasets). Plain GRPO (reason→answer, accuracy + format reward) learns a *shortcut*: short, uninformative <think>, answer from question text, ignoring the image; good on easy train items, fails on test (Fig. 1); MathVista 61.5→61.8, MMBench 82.1→78.6. Fix: caption–reason–answer format (<info><think><answer>) plus a *caption reward* r_c ∈ {0,1}: the policy's own LLM part is given only the caption and asked to answer; reward 1 if it answers correctly, with a filter prompt that marks captions containing reasoning/answers as "Hacking Sample" (App. A.3, Fig. 7). R = r_a + r_f + 0.1·r_c; cosine-annealed KL (static 0.04 collapses at ~700 steps, 0.008 → empty <think> reward hacking, Fig. 5). Results: MathVista 69.4, MathVision 24.7, MMBench 84.1 (Table 1); ablation trained on ChartQA: GRPO 59.0 → +caption 62.6 → +caption reward 64.6, while a length reward *hurts* (62.0) (Table 2). Longer reasoning correlates with accuracy across benchmarks (Fig. 2).

### Idea 7 — Restatement-sufficiency test for observation-misreading steps
- **Mechanism in paper.** §3.2 caption reward: an intermediate restatement of the evidence is judged *functionally* — can the decision be made from the restatement alone? — rather than by a faithfulness rating; a filter rejects restatements that smuggle in the conclusion.
- **Mapping.** Many agents emit a restatement of the tool output before acting (SWE agents summarise test logs; Who&When web-surfers report page content to the orchestrator; deep-search agents summarise retrieved pages). For each such step compute (i) decision-from-restatement: a frozen LM given only the agent's restatement + task chooses the next action/answer; (ii) decision-from-observation: the same LM given the raw observation. Disagreement, or (i) matching the agent's (wrong) action while (ii) does not, flags the restatement as lossy/misread → t* candidate with category "observation misinterpretation / information loss in hand-off" ("what"), and "who" = the summarising agent in a MAS. Output: when + who + what; L0 to compute, L2 to validate; text-only.
- **Datasets / baseline.** Who&When (184 MAS runs where the web-surfer→orchestrator summary is a frequent error locus), SearchAuditBench (1,243 deep-search runs with root causes incl. evidence misreading), TrajErrBench SWE runs (test-log misreading), AgentHallu. Baseline: prompted judge asked "is the summary faithful?", and all-steps GPT judge.
- **Relation to proposals.** New per-step signal; cheap enough to run over every step and feed proposal 2; it localises the hand-off errors proposal 1 can only find by rollouts.
- **Main risk.** Only applies where the agent actually restates evidence (coder agents often act directly on raw output); the frozen LM's own misreading adds noise; disagreement between (i) and (ii) is also high on steps where the restatement is correct but the decision is under-determined.
- **Plausibility 4 / Effort S–M.**

(No second card: the shortcut phenomenon itself — outcome-only RL teaches agents to skip reading observations on easy items — is a cause of the failures we attribute, not a way to attribute them; worth citing as motivation.)

**Quotable facts.**
1. "GRPO often leads to degenerate behaviors where the model ignores the visual input and relies primarily on textual patterns from the question to generate an answer" (§3.1).
2. Base 61.5/19.1/82.1 → SFT 54.6/7.0/80.7 → GRPO 61.8/20.3/78.6 → Visionary-R1 69.4/24.7/84.1 on MathVista/MathVision/MMBench (Table 1, 3B model).
3. Ablation trained on ChartQA, tested on MathVista: GRPO 59.0, +caption format 62.6, +length reward 62.0, +caption reward 64.6 (Table 2) — rewarding length "merely increases redundancy".
4. Static KL 0.04: output length explodes at ~700 steps then collapses to ~100 tokens with format and caption reward crashing; KL 0.008: "zero token in between <think></think>" (Fig. 5, §4.3).
5. Reward weight α=0.1 vs 0.5 makes no significant difference (Table 7).

**Code/data.** github.com/maifoundations/Visionary-R1; "Code and models will be publicly released" (Abstract).

---

## Batch ranking (top 5)

1. **Observation-ablation sensitivity Δ_t (Idea 4a, from the ICL paper's UAS intervention + UPD's IVQD).** Two forward passes per step, no rollouts, directly operationalises "answered from prior vs from evidence"; feeds proposal 1 as an execution-free screen and proposal 2 as a covariate. Plausibility 4, Effort S–M.
2. **Dual-accuracy paired evaluation for attribution judges (Idea 2a, UPD).** Fixes a blind spot of failure-only benchmarks using the successes we already have (AgentHallu, HORIZON, Failure-as-a-Process). Plausibility 4, Effort S.
3. **Restatement-sufficiency test (Idea 7, Visionary-R1 caption reward).** Functional check of evidence hand-offs; natural fit for Who&When web-surfer summaries and SearchAuditBench. Plausibility 4, Effort S–M.
4. **Unsolvable-observation injection on successful runs (Idea 2b, UPD).** A principled, position-uniform injection family (evidence deleted / irrelevant / swapped) for proposal 1's fragility curves. Plausibility 4, Effort M.
5. **Outcome-conditioned subspace scoring of steps (Idea 5a L1 variant, VLMGuard).** Mean-difference direction FAIL vs PASS steps + projection energy + MLP denoising gives an L1 step ranker and the first non-OAT baseline for L0/L1 attribution. Plausibility 4 (L1) / 3 (L0), Effort M.

Lower: GLSim claim-grounding (1a, 3), GLSim on GUI screenshots (1b, 3), bottleneck-test δ family (2c, 3), late-layer evidence attention (4b, 3), pseudo-label denoising (5b, 3), DOR calibration anchoring (3, 2), UniGame learned observation adversary (6, 2).
