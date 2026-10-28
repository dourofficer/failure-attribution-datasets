# Batch A — hallucination detection and uncertainty signals from model internals

Reader angle: an agent step = one LLM call whose prompt contains prior steps + tool observations (≈ retrieved context) and whose output may ignore, misread, or over-ride that context. All seven papers are from the same group (Sharon Li, UW-Madison) and share one toolkit: last-token hidden states across layers, contrast between "with context" and "without/with-random context", logit-lens trajectories, and label-light training. Notation below: L0 raw logs, L1 outcome only, L1+ outcomes of several continuations, L2 step labels.

---

## Paper 1 — TSV: "Steer LLM Latents for Hallucination Detection" (Park, Du, Yeh, Wang, Li; ICML 2025, arXiv 2503.01917)

**Mechanism.** A single trainable vector v ∈ R^d (4K params) is added to the residual stream at one early-middle layer l (LLaMA-3.1-8B: layer 9/4/8/9 per dataset; Qwen-2.5-7B: 4/6/11/6; Table 5) with strength λ=5: h^(l) ← h^(l) + λv, applied to all token positions of the (prompt ⊕ generation) sequence *after* generation is finished (detection-only; removing v restores the model). The final-layer last-token embedding is L2-normalised and modelled as a von Mises–Fisher mixture with two class prototypes µ_truthful, µ_hallucinated (κ=10, EMA-updated, Eq. 4–6); v is trained by cross-entropy to the prototype posterior. Stage 1 uses an exemplar set of N=32 (TruthfulQA) or 64 labelled pairs. Stage 2 pseudo-labels an unlabeled pool with entropic optimal transport (Sinkhorn, ε=0.05, 3 iters) whose column marginal w is the class ratio of the exemplar set (Eq. 7–9), keeps the K=128 lowest-cross-entropy samples (Eq. 10–11), and retrains. Score at test time: S(x) = softmax posterior of the truthful prototype (Eq. 13); one forward pass, O(m²). Evaluated on TruthfulQA/TriviaQA/SciQ/NQ-Open with BLEURT>0.5 (and GPT-4o) labels, AUROC. LLaMA-3.1-8B TruthfulQA: 84.2 (vs 85.5 fully-supervised TSV, 78.2 SAPLMA fully-supervised MLP probe, 70.6 HaloScope unsupervised, 71.4 perplexity). Cross-dataset transfer: trained on TruthfulQA → TriviaQA 79.8 vs 84.0 in-domain (Fig. 4).

**Transferable ideas.**

**A1.1 — Step-separator vector trained from 32 labelled steps + OT pseudo-labels**
- *Mechanism in paper:* Sec. 4.1–4.2, Eq. 2–12, Fig. 2; "with only 32 labeled examples, TSV outperforms SAPLMA with full supervision by 6.0% on TruthfulQA" (Sec. 5.2). Table 3: without the steering vector the prototype classifier on raw embeddings is at chance (52.2); with it 80.9 before and 84.2 after pseudo-label augmentation.
- *Mapping:* sample = one agent step (full prompt incl. prior steps and tool outputs ⊕ the step's output), read as the final-layer last-token embedding of the agent's own open model under the steered intermediate layer. Classes = {clean step, error step}. Exemplar set = 32–64 human-labelled decisive steps (L2) from AgentHallu / TraceElephant replays; unlabeled pool = all other steps of all logged trajectories (L0). Output: per-step score S_t → "when" = argmax or first step above threshold; also usable as the per-step feature of a hazard model. Supervision L2(tiny)+L0. Grey-box (own model; hidden states required).
- *Datasets:* self-collected replays of AgentHallu tasks, TraceElephant (full per-call requests, replayable), SymFail; synthetic Who&When-Pro for the exemplar set. Baselines: SAPLMA-style linear/MLP probe on unsteered embeddings, HaloScope, per-step perplexity/entropy, prompted LLM judge.
- *Relation:* new; complementary to proposal 2 (supplies the per-step emission feature for h_t); orthogonal to proposal 1.
- *Main risk:* class prior π of error steps is ~1–2% per trajectory, far below the 15–50% in the paper; OT pseudo-label accuracy already drops from 100% (K=32) to 81.8% (K=512) at the paper's priors (Table 2), and "decisive step" is a counterfactual trajectory-level label, not a per-sample truthfulness label — adjacent steps that look identical in latent space may have opposite labels.
- *Plausibility 4, Effort M.*

**A1.2 — Outcome-derived class marginals for OT pseudo-labelling (L1 instead of L2)**
- *Mechanism in paper:* Eq. 7 constrains Q^T 1 = w; App. E.3 shows the method is insensitive to w (uniform 83.2 / estimated 83.7 / oracle 84.3 / exemplar-ratio 84.2) and App. E.6 shows reversed w costs only ~2 points.
- *Mapping:* use the free outcome label to set bag-level marginals: successful trajectories contribute w=(1,0) (all steps clean — true under the counterfactual definition, modulo recovered errors); failed trajectories contribute w with at least one error step (e.g. k/T with k≈1–3). Run Sinkhorn per bag (learning-from-label-proportions / multiple-instance variant of Eq. 7). This removes the need for even the 32 exemplars, or lets the exemplars be synthetic (Who&When-Pro injected errors, labels exact by construction) while the marginals come from natural runs. Output: per-step scores; supervision L1 (+ optional synthetic L2). Grey-box.
- *Datasets:* any set with successes: AgentHallu (443 fail / 250 clean), HORIZON, Failure-as-a-Process (1,184/610), TRAIL; plus Who&When-Pro for exemplars. Baseline: A1.1 with human exemplars; proposal-2's L1 hazard model.
- *Relation:* strengthens proposal 2 — it is a representation-space instantiation of "fit on all trajectories using only the outcome"; the vMF-prototype/OT machinery is an alternative estimator to the survival likelihood.
- *Main risk:* per-bag marginals with k unknown; the "all steps of a success are clean" assumption is violated by recovered errors (Failure-as-a-Process shows errors that are repaired); the steering vector was never tested with >10k-token prompts.
- *Plausibility 3, Effort M.*

**A1.3 — Where to steer: early-middle residual stream, not the probe layer**
- *Mechanism in paper:* Fig. 3a: steering at layers 4–10 of 32 gives ≥80 AUROC, declining toward the top; MLP/attention/residual location "shows minimal impact"; Fig. 3b λ=5 best, λ=10 degrades. The paper's limitations (App. I) propose applying TSV "before and after each entity span" to localise.
- *Mapping:* for span-level attribution inside a long step (which token span of a code diff or tool argument is fabricated), compute S before/after each candidate span — a localisation recipe analogous to t_err inside a step. L2(tiny). Grey-box.
- *Relation:* new, small; a sub-step localiser for "what".
- *Main risk:* untested even in the paper.
- *Plausibility 2, Effort S.*

**Quotable facts.** (1) 84.2 AUROC with 32 labels vs 85.5 with full labels, TruthfulQA, LLaMA-3.1-8B (Table 1, p.6). (2) Prototype classifier on unsteered embeddings is at chance (52.2) → steering +28.7 points (Table 3, p.8). (3) OT pseudo-label accuracy 100/98.4/95.3/89.8/81.8% for K=32/64/128/256/512 (Table 2, p.7); 25% injected pseudo-label noise costs 2.9 AUROC (Table 11). (4) Best steering layers 4–10 of 32, residual/MLP/attn equivalent (Fig. 3a, p.7). (5) 4K trainable parameters, ~0.1 GPU-hour for 8B models (Table 4, App. H).

**Code/data:** code released, https://github.com/deeplearning-wisc/tsv.

---

## Paper 2 — HalluEntity: "Benchmarking and Understanding Entity-Level Hallucination Detection" (Yeh, Kamachee, Park, Li; TMLR 9/2025, arXiv 2502.11948)

**Mechanism.** A benchmark, not a method. 157 ChatGPT biographies from FActScore, atomic-fact labels mapped back onto 18,785 entity spans (avg 1.63 words; 15% hallucinated; 120 entities per bio) by a GPT-4o few-shot segmenter, then author-verified (Fleiss κ 0.984 across GPT-4o runs, Cohen κ 0.94 vs. verified). Five token-level uncertainty scores are averaged over an entity's tokens and evaluated by AUROC/AUPRC/F1opt across 17 open LLMs used as *proxy* scorers of ChatGPT text: Likelihood (−log p), Entropy, CCP (NLI-filtered alternative-token mass), SAR (NLL × sentence-embedding relevance weight), Focus (IDF-adjusted NLL+entropy restricted to keyword tokens, plus γ=0.9 × attention-weighted propagation of earlier tokens' scores, attention max-pooled over all layers/heads). Llama3-8B: Likelihood 0.57 AUROC / 0.17 AUPRC; Focus 0.78 / 0.40 (Table 1). Score choice dominates model family/size (Fig. 3a-b; 8B vs 70B differ <0.01). Hallucination rate rises with sentence position (first six words 9%, middle 25%, last six 36%) while model confidence rises with position (Likelihood FNR grows, Fig. 5 right). App. B: Pearson correlation of per-token NLL between generator and proxy models 0.83–0.98, entropy 0.80–0.98 (Tables 7–8).

**Transferable ideas.**

**A2.1 — Proxy-model rescoring turns released text logs into grey-box data**
- *Mechanism in paper:* App. B "Proxy LLM setting": generator Llama3-8B scored by Llama3.1-8B/InternLM2/Qwen2.5/phi-2/Mistral/Gemma2; correlations 0.83–0.98 (Tables 7, 8); all 17-model results in the paper are proxy results for ChatGPT text. (LUMINA Fig. 3 independently shows Llama2-7B detecting GPT-4's RAG hallucinations at parity with same-model detection.)
- *Mapping:* every released dataset with full per-call inputs (TraceElephant, SymFail, MemTrace; Who&When and LongRCA to the extent the prompt is reconstructible) is teacher-forced through an open 7–14B model to obtain per-token NLL/entropy/attention and hidden states for each agent step, conditioned on the same context the closed model saw. Output: a feature vector per step usable by any downstream attributor (hazard model, probe, Focus-style propagation). Supervision L0; converts text-only to grey-box.
- *Datasets:* TraceElephant (220), SymFail (536), MemTrace (160), AgentHallu, LongRCA (median 145 steps, 1,140 runs). Baseline: text-only LLM judge; black-box features (step length, tool error flags).
- *Relation:* enabling infrastructure for both proposals (proposal 2 needs per-step features at scale; proposal 1's surrogate f(prefix, step, δ) needs inputs). New as a stated step.
- *Main risk:* correlations were measured on biography prose with same-era 7–9B models; agent outputs are code/JSON/tool calls from GPT-4-class generators, and contexts run to 100k+ tokens — correlation could be much weaker and long-context proxy inference is the cost driver.
- *Plausibility 4, Effort S–M.*

**A2.2 — Attention-propagated step scores (Focus over steps) as a propagation estimate**
- *Mechanism in paper:* Sec. 4, Focus: y_i = 1[x_i ∈ K]·(h_i + γ p_i), p_i = Σ_j att_{i,j}/Σ_k att_{i,k} · y_j with attention max-pooled over layers and heads; Sec. 5.3: "Focus detects hallucinations at sentence ends by linking them to prior hallucinated content (e.g., 'Ukrainian club')" (Table 5 case 3) and propagation "leads to a decrease in FNR over positions" but raises FPR.
- *Mapping:* token → step. Step t's score = own uncertainty on its key tokens (tool names, arguments, numbers, identifiers ≈ "keywords") + γ·Σ_j A_{t,j} y_j where A_{t,j} is pooled attention from step t's output tokens to step j's content. Reading the propagation matrix backwards gives, for the observable symptom step t_obs, the earliest upstream step with high own-score that t_obs's tokens attend to — a mechanistic estimate of the t_err → t_obs chain. Output: when (root), t_err/t_obs pair, ranked candidate list (nDCG). Supervision L0. Grey-box (attention needed; proxy ok per A2.1).
- *Datasets:* Failure-as-a-Process (has t_err/t_lock/t_obs), SearchAuditBench (root + tolerance span), AgentHallu. Baseline: per-step NLL/entropy without propagation; LLM judge; textual dependency heuristics.
- *Relation:* new; a cheap non-interventional surrogate for proposal 1's propagation profile φ(τ,k,δ); could be validated against rollout-estimated effects.
- *Main risk:* attention is not causal influence, and max-pooling over all layers/heads on 50k-token contexts is dominated by attention sinks; Focus's own FPR rose with propagation.
- *Plausibility 3, Effort M.*

**A2.3 — Evaluate step detectors stratified by sparsity and position; prefer AUPRC**
- *Mechanism in paper:* Fig. 3c: all five scores have F1opt ≈ 0.2 when hallucination rate <10%; Likelihood/Entropy/CCP have PrecisionOpt ≈ base rate with RecallOpt up to 1.0 ("over-predict"); Sec. 5.1 argues AUPRC because true negatives are uninformative tokens.
- *Mapping:* error steps are ~1% of steps, so any uncertainty-style step score will sit in the paper's "sparse" regime; report AUPRC/set-F1 and stratify by error position (early/middle/late) and by trajectory length. Also note the position effect: model confidence increases with position while error rate does not → late-trajectory errors are the blind spot of likelihood-based monitors. Supervision: evaluation only.
- *Relation:* strengthens evaluation protocol of both proposals.
- *Main risk:* none beyond being a protocol note.
- *Plausibility 5, Effort S.*

**Quotable facts.** (1) 18,785 entities, 15% hallucinated; proper nouns 30.9%, numbers 36.2%, adpositions 11.7% hallucination rate (Sec. 3.2, Fig. 2). (2) Llama3-8B: Likelihood AUROC 0.57/AUPRC 0.17 vs Focus 0.78/0.40; CCP RecallOpt 1.00 at PrecisionOpt 0.15 (Table 1, p.6). (3) Hallucination rate by sentence position: 9% / 25% / 36% (first six / middle / last six words) while likelihood FNR increases with position (Sec. 3.2, Fig. 5). (4) Model scale changes AUPRC by <0.01 within families except Gemma-2 (+0.12) (Sec. 5.2). (5) Proxy-vs-generator per-token NLL correlation 0.83–0.98 (Table 7, App. B).

**Code/data:** dataset released (MIT), https://huggingface.co/datasets/samuelyeh/HalluEntity; no method code needed (standard scores).

---

## Paper 3 — DACA: "Your Pre-trained LLM is Secretly an Unsupervised Confidence Calibrator" (Luo, Wang, Li, Wei; NeurIPS 2025, arXiv 2505.16690)

**Mechanism.** Observation: pre-trained LMs are calibrated on MCQ (Llama-3-8B base ECE 3.52%) while post-trained versions are over-confident (instruct 19.00%; Fig. 1). Calibrate the post-trained model g by temperature scaling without labels: minimise KL(softmax(f(x)) ‖ softmax(g(x)/τ)) on an unlabeled set, but only over *agreement* examples where argmax f = argmax g (Eq. 7). Theory: on disagreement examples where the base model gives g's answer less than 1/k mass, the KL-optimal τ is ∞ (Prop. 3.3), so naive alignment drives τ up and makes g under-confident (Fig. 2). Extends to vector/matrix scaling (Eq. 8). f need not share architecture with g: GPT-4o on MedMCQA calibrated with Gemma-3-12B base ECE 21.23 → 6.99 (Table 2); Gemma-3-12B-Instruct on MMLU 23.68 → 8.60 vs 9.75 for *labelled* TS (Table 1); Tulu-3 SFT+DPO+RLVR 25.19 → 5.99 (Table 3). Open-ended QA via P(True) (Yes/No) on TruthfulQA: Qwen2.5-32B-Instruct ECE 30.96 → 5.24 (Table 12). Verbalised confidence baselines are worse than no calibration.

**Transferable ideas.**

**A3.1 — Label-free calibration of P(fail | prefix) and of LLM-judge step probabilities via base-model agreement**
- *Mechanism in paper:* Eq. 7, L(τ;x) = 1[ŷ=ŷ′]·KL(p_f ‖ σ(g/τ)); Sec. 5 "Can DACA be applied to open-ended QA" uses p(Yes|x) of f and g with disagreement defined on the Yes/No argmax.
- *Mapping:* the monitor/judge is g: either an instruct model prompted "Will this run fail? / Is step t the decisive error? (Yes/No)" or a fine-tuned classifier head; f is an open *base* model given the same prompt and read at the Yes/No logits. Fit τ on unlabeled trajectories restricted to prefixes where both say the same thing. Output: calibrated P(fail|prefix) (the brief's calibration metric) and calibrated per-step probabilities for set-valued decisions; ranking (nDCG) is unchanged since TS is monotone. Supervision L0 (+ outcome labels only for evaluation). Text-only prompts + one open base model.
- *Datasets:* Failure-as-a-Process (PASS/FAIL), HORIZON (1,284 successes), AgentHallu (250 clean) for ECE of P(fail|prefix); Who&When / MP-Bench for step-judge calibration. Baseline: labelled TS (upper bound), vanilla, verbalised confidence, CAPE-style prompt ensembles.
- *Relation:* strengthens proposal 2 — its hazard h_t is a probability whose calibration is a claimed deliverable; DACA gives a label-free post-hoc check/fix and also calibrates the prompted baselines proposal 2 compares against. New element.
- *Main risk:* the assumption ECE_f ≈ 0 was verified on short MCQ/TruthfulQA prompts; a base model reading a 50k-token trajectory and emitting Yes/No may be near-uniform, making the agreement set small and f's "calibration" meaningless; DACA fits a single global τ, so it cannot fix prefix-length-dependent miscalibration.
- *Plausibility 3, Effort S.*

**A3.2 — (not a card) Base-vs-instruct disagreement as an error signal.** Considered and rejected: the paper shows disagreement examples are mostly where post-training *improved* accuracy, so disagreement is not evidence of error. Zero-idea note.

**Quotable facts.** (1) Base vs instruct ECE on MMLU: Llama-3-8B 3.52% vs 19.00%; Qwen2.5-7B 5.41% vs 20.84%; DeepSeek-V2-Lite 3.39% vs 20.81% (Fig. 1, p.3). (2) Gemma-3-12B-Instruct MMLU ECE 23.68 → 8.60 (DACA, no labels) vs 9.75 (TS with labels) (Table 1, p.7). (3) GPT-4o on MedMCQA ECE 21.23 → 6.99 using Gemma-3-12B base as the reference; better-calibrated reference → lower final ECE (Table 2, p.7). (4) Prop. 3.3: on disagreement samples with σ_c(f(x)) < 1/k the KL-optimal temperature is τ* = ∞ (p.5). (5) Open-ended P(True) on TruthfulQA: Qwen2.5-32B-Instruct ECE 30.96 → 5.24; Llama-3-70B-Instruct 42.50 → 17.00 (Table 12, p.30).

**Code/data:** code released, https://github.com/ml-stat-Sustech/Disagreement-Aware-Calibration.

---

## Paper 4 — LUMINA: "Detecting Hallucinations in RAG System with Context–Knowledge Signals" (Yeh, Li, Mallick; ICLR 2026, arXiv 2509.21875)

**Mechanism.** Two per-token signals, no training, two forward passes. (i) External-context utilisation E_t = MMD² (cosine kernel over output-token embeddings, approximated on the top-100 tokens) between the next-token distribution p(·|q, d, a_<t) with the retrieved documents and p(·|q, d′, a_<t) with d′ = the retrieved documents of another random data point (Eq. 3–7). (ii) Internal-knowledge utilisation I_t = "information processing rate" R: logit-lens each layer l, take 1 − min([f(h_l)]_{top}/p_final(top), 1), weight by layer index l, divide by Σ_l l·H(f(h_l)) (Eq. 8); high R = the final top token only emerges late = much parametric composition; calibrated by p(a_t)/p(a_t,1) (Eq. 11). Hallucination score H_t = λ I_t − (1−λ) E_t, λ=0.5, averaged over response tokens. Validated by four one-tailed hypothesis tests on >65k tokens (e.g. E with docs > E without docs, t=79.85; R without docs > R with docs, t=101.2; Table 1). RAGTruth AUROC 0.76/0.86/0.74/0.77 (Llama2-7B/13B, Llama3-8B, Mistral-7B); HalluRAG 0.92/0.92/0.99 vs ReDeEP 0.68/0.76/0.79 (Table 2); competitive with supervised SAPLMA (Table 4). Robust to 30% noise in d and d′ (Fig. 2), and to a detector ≠ generator (Llama2-7B/Qwen3-4B/Llama4-17B scoring GPT-3.5/GPT-4 responses, Fig. 3). Error analysis: false positives come from low-quality retrieved documents that force internal-knowledge use (24%) and label errors (32%); false negatives from summarisation (64%).

**Transferable ideas.**

**A4.1 — Observation-utilisation score per agent step (MMD vs. a swapped observation) + parametric-composition rate**
- *Mechanism in paper:* Measurement 1 (Eq. 3–6): replace d by random d′, keep the prefix a_<t fixed, compute MMD of the two next-token distributions; Measurement 2 (Eq. 8); Fig. 5 left: hallucinations sit at low-E / high-I; Conjecture 1 "a is more likely hallucination if I ≫ E".
- *Mapping:* step t = the LLM call after tool observation o_{t−1}. d = o_{t−1} (or all observations in context), d′ = an observation of the same tool type from a different trajectory (keeps format, breaks content). Teacher-force the step's actual output a and compute per-token E_t, I_t and H_t; aggregate over the step (mean, or max over "key" tokens: tool arguments, numbers, paths). Low E on a step that follows a tool call = the agent's output did not depend on what the tool returned (ignoring tool output, hallucinated tool result, unverified assumption); high I on argument tokens = fabricated arguments. Output: per-step score for "when", and a 2-D (E,I) signature usable as a "what" feature (context-ignoring vs. parametric fabrication vs. grounded-but-wrong). Supervision L0. Grey-box; proxy model allowed (Fig. 3), so applicable to released logs with full inputs after A2.1.
- *Datasets:* AgentHallu (hallucination-specific, 443 + 250 clean, step + cause), SearchAuditBench (deep search ≈ RAG, 1,243 runs with root cause), TraceElephant, SymFail, self-collected τ²-bench/SWE runs. Baselines: per-step perplexity/LN-entropy, P(True), LLM judge, ReDeEP-style attention-head scores.
- *Relation:* new; it is an *input-side* counterfactual that needs no environment execution — a one-call surrogate for proposal 1's δ = "give the agent a different observation at step k", and a feature for proposal 2's h_t.
- *Main risk:* in agents many steps legitimately ignore the latest observation (planning, summarising, retries), so low E is only diagnostic conditional on step type; the swapped observation sits in the middle of the context, so the second forward pass recomputes everything after it (cost ≈ 2× per step over 10k–260k tokens); the paper's FP analysis shows that when the context is genuinely useless (bad tool output) the score flags the model rather than the tool — which, for attribution, may actually be the right step but the wrong "what".
- *Plausibility 4, Effort M.*

**A4.2 — Validate step-level internal signals by testable implications before using them as labels**
- *Mechanism in paper:* Sec. 3.3, H1–H4 and Table 1: derive implications that must hold if the score measures what it claims (E higher with docs than without; summarisation E > QA E; R without docs > with docs; data-to-text R > summarisation R) and test them with t-tests on tens of thousands of tokens.
- *Mapping:* for any step-level internal signal s (A1.1, A2.2, A4.1, A5.1, A6.1, A7.1) state implications on *unlabeled* trajectories: E should be higher on the step right after a tool call than on planning steps; I should be higher on steps with no observation in context; a context-ignoring score should rise when the observation is replaced by an error message that the agent then does not mention; fragility-style implications from proposal 1 (the score at k should correlate with rollout-estimated effect) etc. Supervision L0/L1+. Any access.
- *Relation:* strengthens both proposals' methodology; new as a checklist.
- *Main risk:* implications are necessary, not sufficient (the paper admits prior work "verified causal relationship with hallucination but not with utilization").
- *Plausibility 4, Effort S.*

**Quotable facts.** (1) HalluRAG AUROC: LUMINA 0.9153 / 0.9166 / 0.9899 vs ReDeEP 0.6771 / 0.7645 / 0.7870 (Llama2-7B / 13B / Mistral-7B) (Table 2, p.7). (2) RAGTruth AUROC 0.7646 / 0.8569 / 0.7446 / 0.7685; supervised SAPLMA 0.6508 / 0.8337 / – / 0.8073 (Tables 2, 4). (3) Hypothesis tests on >65k tokens: H1 t=79.85–94.15, H3 t=91.0–109.3, all p<0.001 (Table 1, p.6). (4) Detector ≠ generator works: "Llama2-7B achieves a comparable or higher AUROC than Llama3-8B on Llama3-8B responses" and Qwen3-4B/Llama4-17B score GPT-3.5/GPT-4 responses (Sec. 4.3, Fig. 3). (5) Two forward passes, <1 s per 150-token response on one H100; std over five choices of random d′ <0.0025 (App. E.4, G). (6) Error analysis: 24% of FPs from low-quality retrieved docs, 32% label errors; 64% of FNs from summarisation (Table 6).

**Code/data:** code released, https://github.com/deeplearning-wisc/LUMINA.

---

## Paper 5 — "How Retrieved Context Shapes Internal Representations in RAG" (Yeh, Li; arXiv 2602.20091, 2026, ACL-style)

**Mechanism.** Analysis paper. For 200 queries per dataset (TriviaQA, NQ, PopQA, StrategyQA) and Gemma3-27B / Llama4-Scout-17B / Qwen3-Next-80B (instruct, plus base for the first two), retrieve 20 MassiveDS documents, label each relevant/distracting/random with GPT-5 (100% human agreement on relevant), split queries into easy/hard by whether the model answers correctly without documents, then compare the *last prompt token* hidden state h ∈ R^{L×D} across contexts (single-doc: relevant/distracting/random/none; multi-doc: 1 relevant + 3 distracting or + 3 random) via PCA, cosine similarity to the no-doc state, and linear probes (acc + mean distance to boundary, Tables 6–10). Findings: random docs move the representation most and the move predicts abstention (instruct abstains 97.6% on random docs even for easy TriviaQA where base answers 89.4% correctly; Table 1); relevant docs barely move it (probe acc ≈1.0 but margin 0.25–0.53 vs 0.54–0.78 for random); one relevant doc anchors the state against added noise (relevant vs relevant+distracting probe acc 0.46–0.74), and 20 unfiltered docs ≈ relevant-only accuracy (Table 3); layer-wise, random docs separate by L23/46 while relevant vs distracting stay entangled until L35 and are never fully separable; later layers pull relevant-doc states back toward the no-doc state (parametric dominance; also in base models). Hard queries: base models remain wrong 35.6% of the time even with relevant docs.

**Transferable ideas.**

**A5.1 — Last-prompt-token drift as an online symptom/abstention monitor and loop detector**
- *Mechanism in paper:* Obs. 1, Fig. 3/7: abstention probability increases monotonically as cos(h_with_ctx, h_query_only) decreases; Obs. 2: relevant docs leave the state nearly unchanged ("confirmation signal"); App. E.1: relevant docs raise response log-likelihood (t=3.1–14.4 on TriviaQA/StrategyQA).
- *Mapping:* at each step compute d_t = 1 − cos(h_L(prefix_t), h_L(prefix_t with the newest observation removed)) at the final (or ~L·0.5) layer. Spikes of d_t predict the model entering a refusal/retry mode (an observable symptom t_obs, giving lead time for online monitoring); runs of d_t ≈ 0 across repeated tool calls indicate the agent is not updating on observations (stuck loops, confirmation of a wrong plan). Output: P(fail|prefix) feature, t_obs, lead time. Supervision L0 (L1 to calibrate). Grey-box own model.
- *Datasets:* self-collected replays; AgentHallu; Failure-as-a-Process (t_obs labels) if re-run with an open model. Baselines: textual loop/repeat detectors, step entropy, LLM judge.
- *Relation:* new; a change-point feature for proposal 2's L0 mixture; overlaps with A4.1/A6.1 (output- vs. representation-level versions of the same contrast — Paper 6 Table 4 argues the latent version is more informative than logit-lens projections).
- *Main risk:* measured on single short docs and simple QA; in agent contexts every observation is semantically "related", so drift may track observation length/format rather than informativeness, and the abstention link is an instruction-tuning artefact (base models show no drift; Fig. 4).
- *Plausibility 3, Effort M.*

**A5.2 — Separability-by-layer as a feasibility map for which failure categories internals can catch**
- *Mechanism in paper:* Obs. 4–5 and Fig. 6/10–12, Tables 6–10: coarse mismatch (random) is linearly separable from layer ~L/2; plausible-but-wrong (distracting) vs relevant is "not fully separable even at the final layer"; later layers close the no-doc/relevant gap.
- *Mapping:* before investing in a latent step detector, run the same probe sweep on (clean step vs error step) stratified by failure category: errors caused by garbage/irrelevant tool output should separate early; errors caused by plausible-but-wrong observations (the "distracting" analogue: stale search results, near-miss API responses) are predicted to be hard for any internal-state detector and should be routed to interventional methods. Output: a category-level prior on detector reliability; also suggests reading mid-layers rather than the final layer for context-related errors (final layers over-write with parametric knowledge). Supervision L2 for the sweep only.
- *Datasets:* AgentHallu (cause labels), AgentErrorBench (module+type), AgentRx (9 categories), re-run with an open model. Baseline: single-layer probe.
- *Relation:* strengthens both proposals (tells where proposal 1's execution-based labels are indispensable; tells proposal 2 which layer to read).
- *Main risk:* 200 queries per setting in the paper; category-stratified error steps will be far fewer.
- *Plausibility 3, Effort S.*

**Quotable facts.** (1) Gemma3-27B on TriviaQA easy queries with a random doc: base 89.4% correct / 3.8% abstain; instruction-tuned 1.7% correct / 97.6% abstain (Table 1, p.5). (2) Hard queries with a relevant doc: base 35.6% incorrect; "instruction-tuned LLMs exhibit an even higher error rate with relevant documents than with distracting documents" in some cases (Sec. 5.1). (3) Probe margin no-doc vs relevant 0.25–0.53 vs no-doc vs random 0.54–0.78 (Tables 6–7, App. E.2). (4) Llama4-17B: random-doc states separate at L23/46, relevant vs distracting entangled until L35 and never fully separable (Obs. 4, Fig. 6). (5) 20 unfiltered docs ≈ relevant-only accuracy (e.g. Gemma TriviaQA easy 90.3 vs 90.4) (Table 3, p.9).

**Code/data:** no code link in the paper; prompts for the LLM judges are in App. C; data are public QA sets + MassiveDS.

---

## Paper 6 — "Understanding Language Prior of LVLMs by Contrasting Chain-of-Embedding" (Long, Oh, Park, Li; ICLR 2026, arXiv 2509.23050)

**Mechanism.** For an LVLM with L decoder layers, take the last-token embedding at each layer with the image, z^l_vis = f_l(x_v, x_t), and without it, z^l_blind = f_l(∅, x_t); d_l = cosine distance. Split the data *without labels* into vision-dependent D_VT = {x : F(x_v,x_t) ≠ F(∅,x_t)} and vision-independent D_T (prediction unchanged). The Visual Integration Point l* is the layer where E_{D_VT}[d_l] − E_{D_T}[d_l] jumps above a threshold and stays (Hyp. 3.1, Eq. 3; automatic variance-normalised rule in App. B.2, Eq. 9). Total Visual Integration TVI(x) = mean_{l ≥ l*} d_l (Def. 3.2). VIP exists in all 60 model×dataset settings, at ≈60% depth (Qwen2.5-VL-7B 18/28; Gemma-3-4B 20/34; stable across LLaVA training checkpoints). Post-VIP TVI correlates with correctness (Spearman 0.72 on VLind-Bench, Qwen2.5-VL-7B) vs 0.15 pre-VIP (Table 1); beats mean visual attention (0.09) and final-layer output divergence (0.30) (Table 3); logit-lens KL/JS versions fail (−0.17/0.29; Table 4). Datasets with strong language prior (ViLP) have lower TVI; an attention-reallocation intervention (PAI) raises TVI 0.038→0.144 and accuracy 50→52.3; TVI as an SFT regulariser improves LLaVA-1.5 on MME.

**Transferable ideas.**

**A6.1 — Context Integration Point and Total Context Integration for agent steps**
- *Mechanism in paper:* Sec. 3.1–3.3, Eq. 2–4; label-free grouping by prediction agreement (Sec. 3.2); Table 4 (latent cosine ≫ logit-lens); App. B.2 automatic l* rule.
- *Mapping:* image → the observation block(s) in the step's prompt (or everything except the task instruction). For each step compute the chain d_l between the prompt with and without the observation; group steps by whether the greedy output changes when the observation is removed (label-free; "context-dependent" vs "context-independent" steps); locate the layer l* where the two groups' d_l diverge for the agent model; TCI_t = mean_{l≥l*} d_l. A step that *should* be context-dependent (immediately after a tool result, or a step whose output cites the observation) but has low TCI is language-prior-dominated → candidate error step; the per-sample TCI is a continuous score. Output: when (ranking), what (context-ignoring vs. grounded), online feature. Supervision L0. Grey-box own model.
- *Datasets:* self-collected replays of AgentHallu / τ²-bench (TrajErrBench tasks) / WebShop (AgentErrorBench). Baselines: A4.1 (output-level MMD), entropy, LLM judge; final-layer-only drift (A5.1) as the ablation the paper itself ran (Table 3 "Output Divergence").
- *Relation:* new; the same contrast as A4.1/A5.1 but aggregated over post-l* layers, which the paper shows is the part that carries the correctness signal (0.72 vs 0.15). Supports proposal 2 as a feature; supports proposal 1 as a cheap surrogate for "remove the observation".
- *Main risk:* VIP is tied to modality fusion (vision tokens are "seen but not used" early); a text-only analogue may not have a clean l*. Removing a block from the middle of a long prompt changes positions and lengths, which itself moves last-token embeddings; needs a length-matched placeholder (as LUMINA's random d′ does) rather than deletion. Spearman 0.72 was on yes/no and MCQ outputs where the last token is the answer; agent outputs are long.
- *Plausibility 3, Effort M.*

**A6.2 — Label-free "context-dependent step" grouping as a cheap one-call counterfactual**
- *Mechanism in paper:* D_VT := {F(x_v,x_t) ≠ F(∅,x_t)} (Sec. 3.2); App. C validates it against a synthetic CommonsenseQA+random-image control (Fig. 10).
- *Mapping:* for every step, one extra greedy decode with the newest observation blanked: if the output is unchanged, the step did not use the observation at all. Intersected with "the observation contained a signal the agent needed" (e.g. an error string, a changed test status) this yields a hard flag for the "ignored tool output" category with no training. Supervision L0; grey-box or even black-box API (only outputs are compared).
- *Datasets:* any replayable set (TraceElephant, SymFail) or live runs; evaluate against AgentHallu causes / AgentRx categories. Baseline: LLM-judge asked "did the agent use the tool output?".
- *Relation:* new; a degenerate (single-call, non-rollout) member of proposal 1's perturbation screen with δ = "blank the observation".
- *Main risk:* output equality is too strict for long free-form steps (needs semantic equivalence), and unchanged output after blanking is correct behaviour for many steps.
- *Plausibility 4, Effort S.*

**Quotable facts.** (1) Spearman(TVI, correctness) 0.724 post-VIP vs 0.149 pre-VIP, Qwen2.5-VL-7B on VLind-Bench (Table 1, p.5). (2) TVI 0.72/0.63 vs mean visual attention 0.09/−0.04 vs output divergence 0.30/0.51 (VLind/ViLP, Qwen2.5-VL-7B) (Table 3, p.7). (3) Logit-lens distances fail: KL −0.17/0.29, JS −0.23/0.29 vs latent cosine 0.72/0.63 (Table 4, p.8). (4) VIP at ≈60% of depth for Gemma-3 4B/12B/27B and stable across LLaVA checkpoints (Fig. 5, Fig. 15). (5) PAI intervention: TVI 0.038 → 0.144, accuracy 50.0 → 52.3 (Table 2, p.7).

**Code/data:** the text says "Code:" and "repository at:" with the link left blank in this version; models/datasets public. Treat as not released.

---

## Paper 7 — VAUQ: "Vision-Aware Uncertainty Quantification for LVLM Self-Evaluation" (Park, Oh, Choi, Du, Li; arXiv 2602.21054, 2026, ACL-style)

**Mechanism.** Training-free response-level score s = H(y|v,t) − α·IS_core, where H is length-normalised predictive entropy of the generated response (teacher-forced) and IS_core = H(y|v_masked,t) − H(y|v,t) is the entropy increase when the "core" visual evidence is removed (Eq. 5–6). Core region = top-K% image patches by attention from generated tokens, summed over heads and over layers 10–25 (LLaVA-1.5-7B) / 12–26 (Qwen2.5-VL-7B) (Eq. 3–4); masking is implemented as attention knockout of those visual tokens (App. A). Three forward passes total; no sampling. Motivation (Fig. 1, Table 4): on ViLP counterfactual images, entropy AUROC is 48.4 (below chance) vs 83.2 on factual images — confidence tracks the language prior; IS_core is 75.2 on counterfactual; the combination 70.4/83.6. Results: ViLP LLaVA-1.5-7B 77.0 vs Semantic Entropy 63.7 / VL-Uncertainty 55.6; gains across MMVet, VisualCoT, CVBench, HallusionBench on LLaVA-1.5-7B/13B, Qwen2.5-VL-7B, InternVL3.5-8B (Tables 1–2, 6). Core masking ≈ oracle GT-box masking (77.8 vs 78.6; random masking 73.3; blank image 75.2; Table 3). α∈[0.5,1.5], K∈[30,60] transfer across datasets (Fig. 5c). 0.73 s/sample vs 13.6 s for VL-Uncertainty.

**Transferable ideas.**

**A7.1 — Core-evidence knockout: entropy gain when the most-attended context spans are masked**
- *Mechanism in paper:* Eq. 3–6; Table 3 (targeted masking > blank > random); Fig. 3 (early layers' attention does not localise evidence, layers ≥10 do); App. A (attention knockout instead of input edit).
- *Mapping:* for step t, aggregate mid-layer attention from the step's output tokens to tokens of the observations in context, take the top-K% observation tokens as "core evidence", knock them out in a second teacher-forced pass, and compute ΔH_t. s_t = H_t − α ΔH_t: confident outputs whose confidence does not depend on any evidence are flagged. Side product: the identity of the core spans and the step that produced them gives an evidence chain (step t relied on observation from step j) — a cheap "who/when" link for multi-agent logs. Output: per-step P(error) proxy, evidence links. Supervision L0. Grey-box own model (or proxy via A2.1).
- *Datasets:* SearchAuditBench (has tolerance spans — natural evidence-span labels to validate the localisation, as VisualCoT boxes do here), AgentHallu, TraceElephant. Baselines: step entropy alone; A4.1 whole-observation swap; A6.2 blanking.
- *Relation:* new; finer-grained than A4.1 (removes the used evidence rather than the whole observation) and a one-pass surrogate for proposal 1's δ = "delete evidence". Feature for proposal 2.
- *Main risk:* attention sinks and long contexts make top-K% selection noisy (Paper 6 App. E shows pathological attention concentration under strong language prior); α and K are dataset-tuned (Tables 11–14) even if they transfer reasonably; teacher-forced entropy over long code/JSON outputs is dominated by boilerplate tokens — needs the keyword restriction of Focus (Paper 2).
- *Plausibility 3, Effort M.*

**A7.2 — Evaluate step monitors on prior-consistent vs prior-contradicting observations**
- *Mechanism in paper:* Fig. 1 and Table 4: all LLM self-evaluation scores (entropy, verbalised, semantic entropy, EigenScore) collapse on the counterfactual split (entropy −40.9%, EigenScore −26.0%).
- *Mapping:* partition error steps by whether the triggering observation agrees with what the model would have predicted without it (cheap to compute with A6.2's blanked decode). Expect uncertainty-based step detectors and LLM judges to fail precisely on prior-contradicting observations (unexpected API results, failing tests the model "expects" to pass) — the most dangerous natural failures. Report the two numbers separately. Supervision: evaluation only.
- *Relation:* strengthens evaluation of both proposals; motivates A4.1/A6.1/A7.1 over plain uncertainty.
- *Plausibility 4, Effort S.*

**Quotable facts.** (1) Entropy AUROC 83.2 (factual) vs 48.4 (counterfactual) on ViLP, LLaVA-1.5-7B; IS_core 60.9 vs 75.2; combined 83.6 vs 70.4 (Table 4, p.7). (2) ViLP AUROC: VAUQ 77.0 vs Semantic Entropy 63.7, EigenScore 63.2, VL-Uncertainty 55.6 (Table 1, p.6); AUPRC 68.2 vs 60.2 (Table 10). (3) Masking variants on VisualCoT: blank 75.2, random 73.3, oracle GT box 78.6, attention-core 77.8 (Table 3, p.6). (4) Attention in layers 0–10 does not localise the evidence region; layers 10–25 do (Fig. 3, p.7). (5) 0.73 s vs 13.6 s per sample (VL-Uncertainty), a 94.6% reduction (Table 5, Sec. 5.3).

**Code/data:** code released, https://github.com/deeplearning-wisc/vauq.

---

## Batch ranking (top 5 across the batch)

1. **A4.1 Observation-utilisation score per step (LUMINA's MMD-vs-swapped-observation + information-processing rate)** — label-free, two forward passes, proxy-model-compatible, directly targets "agent ignored / over-rode the tool output"; cheap non-executing surrogate for proposal 1. Plausibility 4, M.
2. **A2.1 Proxy-model rescoring of released text logs** (HalluEntity App. B correlations 0.83–0.98; LUMINA Fig. 3) — unlocks per-token NLL/entropy/attention/hidden-state features on TraceElephant/SymFail/MemTrace/AgentHallu without re-running agents; prerequisite for every other card on released data. Plausibility 4, S–M.
3. **A1.1/A1.2 Step-separator steering vector with 32 labelled steps and OT pseudo-labels whose class marginals come from outcome labels** — the most label-efficient supervised step scorer in the batch, +28 AUROC over raw-embedding probes in the source paper; a representation-space sibling of proposal 2's L1 fitting. Plausibility 4/3, M.
4. **A6.2 Label-free "did this step use the observation?" flag** (one blanked re-decode; Paper 6's agreement grouping) combined with **A7.2/A2.3 stratified evaluation** (prior-contradicting observations; sparse-error AUPRC) — trivially cheap, and the stratified evaluation will likely show where prompted judges and entropy monitors fail. Plausibility 4, S.
5. **A3.1 DACA label-free calibration of P(fail|prefix) and judge probabilities using an open base model on the agreement set** — the only idea in the batch that addresses the brief's calibration metric without labels; works for API judges. Plausibility 3, S.

Runner-up worth noting: A5.2 layer-wise separability sweep as a feasibility map (which failure categories any internal-state detector can catch; read mid-layers, not final) — small effort, informs where proposal 1's executed labels are irreplaceable.
