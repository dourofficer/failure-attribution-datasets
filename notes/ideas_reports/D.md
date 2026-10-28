# Batch D — Preference alignment: theory and data-centric alignment (7 papers)

Angle kept in mind throughout: step labels are NOISY (40–90% exact-step agreement, MP-Bench keeps three
annotators' votes, LLM drafts anchor humans), SCARCE (hundreds of trajectories), and often come as CANDIDATE
SETS. A (prefix, good continuation, bad continuation) triple is a natural preference pair, so DPO/Bradley–Terry
training of a step-level scorer is a legitimate mapping. All seven papers come from the same UW–Madison group
(Sharon Li) except CanDist (Zhejiang + Li), and they cross-cite, so the ideas compose.

---

## 1. Im & Li — "Can DPO Learn Diverse Human Values? A Theoretical Scaling Law" (NeurIPS 2025)

**Paper.** Pure theory + verification. Signal: the DPO reward margin r_j = β[log π_θ(y_w|x)/π_θ(y_l|x) − same
under π_ref] of every training pair, followed through gradient flow of the *unembedding matrix W only* (backbone
g(x) → last hidden state frozen). Lemma 4.1: τ ṙ_j = (1/N) Σ_i β² σ(−r_i) (y_w,j − y_l,j)ᵀ(y_w,i − y_l,i) Σ_ij with
Σ_ij = g(x_i)ᵀg(x_j), i.e. pair j's margin grows only through pairs that share preference tokens AND have
correlated last-layer embeddings. Data model: K "value" clusters, each a pair of Gaussians N(±c_i + b, v²I) with
orthogonal concept directions c_i and a shared component b; Q samples per cluster. Thm 4.2: all training margins
positive by τ_1 = Kτ log3 / 5β²; Thm 4.3: population 0-1 risk ≤ 2KQ²e^{−Q/45}, hence Q = Θ(log K) samples per
value (e.g. K=10 needs >875 per value for error <0.05, Fig. 4). Verified on Anthropic Persona with Llama-3.1-8B,
Llama-2-7B, Mistral-7B, Qwen3-8B: shared-component + near-orthogonal residual geometry (Fig. 3), margin growth
slows with K (Fig. 5), test error vs K linear fits R² 0.97/0.95/0.99. Supervision: standard pairwise labels.

**Transferable ideas.**

*Card 1.1 — On-policy "bad step" has a huge negative initial margin: DPO on natural failures may never flip it.*
- Mechanism (Sec. 7 Discussions): the margin change is bounded by log 3 at the end of finite-step training, so
  "any preference pair where the reference model is more than 3^{1/β} times more likely to generate the rejected
  response than the preferred one would not flip." Also the per-response dynamics τ ṙ_{w/l,j} = (1/N)Σ β²σ(−r_i)
  y_{w/l,j}ᵀ(y_w,i − y_l,i)Σ_ij: heavily overlapping chosen/rejected responses move together (gradient
  entanglement / likelihood displacement, refs [100,101]).
- Mapping: in failure attribution the "bad" step was *produced by the agent itself* under the same prefix, so if the
  reference model is the agent's own policy (or a close relative), log π_ref(bad|prefix) ≫ log π_ref(good|prefix)
  and the pair starts deep in the non-flippable regime; additionally good/bad steps for the same prefix share most
  tokens (same tool, one argument differs). Prediction: sequence-level DPO on (prefix, good step, bad step) will
  show the two likelihoods co-moving and poor margin flips. Remedy implied by the theory: (a) use a Bradley–Terry
  head on frozen embeddings (paper 5's setup) or a classifier rather than policy-space DPO; (b) if DPO, restrict
  the loss to the differing span (token-level DPO) and use a reference model that did NOT generate the trajectory.
- Datasets: self-collected replayable runs with an open agent model (needed to compute π_ref); TraceElephant /
  SymFail per-call requests make re-scoring with the original open model possible. Baseline: vanilla DPO vs
  embedding-BT head on the same pairs; metric = fraction of pairs whose margin becomes positive + exact-step acc.
- Relation: new (a design constraint for any DPO-style attributor); orthogonal to both proposals.
- Risk: the log 3 bound is for last-layer training; full fine-tuning can flip harder pairs. Cheap to check first.
- Plausibility 3, Effort S (a diagnostic: histogram of β·log-ratios of (good, bad) pairs under the agent model).

*Card 1.2 — Per-failure-mode sample budget Q ∝ log K, and a geometry pre-check for the "what" task.*
- Mechanism: Thm 4.3 bound 2KQ²e^{−Q/45}; Fig. 3 verification recipe (mean-subtract last-token embeddings,
  cosine-similarity matrix between concept clusters should be ≈0 off-diagonal).
- Mapping: cluster = failure category (9–20 modes), sample = (trajectory or (prefix, step)) embedding; the paper's
  recipe tells us, before training a category classifier, whether modes are represented along near-orthogonal
  directions in a frozen LLM (if they are, few hundred per mode suffice; if a shared direction dominates, the
  log K law does not apply and more data per mode is needed). Output: "what" head; supervision L2 (mode labels).
- Datasets: Who&When Pro (12k, 15 frameworks, mode label), Aegis (9.5k, MAST mode sets), MAST-Data (1,642),
  HORIZON (3,782); natural: AgentRx (9 categories), AgentErrorBench (module+type). Baseline: learning curve per mode
  with uniform vs balanced sampling.
- Relation: new but minor; informs data collection for the taxonomy head only.
- Risk: the paper's clusters are single short statements; a 100-step trajectory embedding is dominated by task
  content, not failure mode, so orthogonality likely fails — which is itself the useful finding.
- Plausibility 2, Effort S.

**Quotable facts.** (i) "the number of samples required per human value must grow logarithmically with the number
of distinct values" (abstract; Thm 4.3 R(P) ≤ 2KQ²e^{−Q/45}). (ii) K=10 requires >875 samples per value for
near-zero generalization error (Sec. 4.2, Fig. 4). (iii) Linear fit of test error vs K: R² 0.97 (Llama-3.1-8B),
0.95 (Mistral-7B-v0.3), 0.99 (Qwen3-8B-Base) (Sec. 5). (iv) Margin change bounded by log 3 ⇒ pairs where π_ref
prefers the rejected by >3^{1/β} do not flip (Sec. 7). (v) Qwen3-8B test error rises 0.000→0.183 from K=1 to 8
(Table 2, App. E).

**Code/data.** Appendix F says "Code is provided here" (link stripped in extraction); trains with TRL on Anthropic
Persona; no new data.

---

## 2. Im & Li — "How Well Can Preference Optimization Generalize Under Noisy Feedback?" (TMLR, Feb 2026)

**Paper.** Finite-step generalization theory for the GPO family (DPO f=−log σ, IPO squared, SLiC hinge) with two
noise models: ε-mislabeled (i.i.d. flips) and ω-uncertain (label sampled with prob σ((r*(y_w)−r*(y_l))/ω), i.e.
Bradley–Terry ambiguity). Data model: post-RMSNorm last-token embeddings are near-unit-norm (Table 1: norm 139.6,
std <1% of mean; cosine to class mean 0.956), so positives/negatives are vMF(μ±, κ) with angle 2φ between means
and normalized concentration γ = 2κ/d. Core mechanism: the learned boundary direction equals the difference of
noisy class means, whose cosine with μ+−μ− is ≥ 1 − 5/√N − 5√(log N/N)/((1−2ε)γ/(2+γ) + 2√(log N/N)) (Lemma B.2),
and the boundary rotates by at most arcsin δ while t ≤ δτ/(4β²D) (Lemma B.3). Thm 3.3: population risk ≤
c·exp(−dγ²/(5(2+γ))) as long as ε ≤ 1/2 − O((2+γ)/γ · √(log N/N)); robustness to noise ε needs N ≳
Õ(1/(γ²(1−2ε)²)); E[R] is 1/2 at ε=1/2 with zero second derivative (inflection, linear approach). ω-uncertain
noise gives the same bound up to O(1/d) and is *benign*: flipped samples concentrate near the boundary (App. C).
Verified: synthetic vMF (d=512, N∈{200,600,2000}); Llama-3.1-8B/-Instruct/3.2-3B on two Persona behaviors with
ε∈[0,0.5]; better-separated behavior (mean-embedding separation 19.5 vs 7.2) degrades later; instruct model most
robust. Practical advice: measure separation of positive/negative mean embeddings *under the chosen model* before
choosing a noise-robust loss (Dr. DPO, rDPO, cDPO, ROPO).

**Transferable ideas.**

*Card 2.1 — Noise-tolerance budget from embedding separation: predict how many noisy step labels we need.*
- Mechanism: Thm 3.3 + Table 2 recipe (separation = ‖mean emb(positives) − mean emb(negatives)‖ of final-prompt-
  token last-layer embeddings) + the sample-complexity statement N ≳ 1/(γ²(1−2ε)²).
- Mapping: positives = embeddings of (prefix, labelled decisive step), negatives = (prefix, non-error step) from
  the same trajectories (or from successful runs); ε ≈ per-dataset flip rate estimated from inter-annotator
  agreement (TrajErrBench κ 0.91 vs 0.67 gives two regimes; MP-Bench three votes give per-sample ε_i, and the
  paper's remark says the theorem holds with ε = average ε_i). Output: a predicted accuracy-vs-N curve per dataset
  and per backbone, and a go/no-go for plain BT/DPO vs noise-robust loss. Supervision L2; grey-box (needs an open
  encoder, text-only datasets are fine since we re-encode).
- Datasets: Who&When, MP-Bench, TrajErrBench (two subsets), LongRCA; validate by injecting extra flips (as the
  paper does) and checking the predicted inflection/linear regime. Baseline: just train and observe.
- Relation: new; it is a *planning tool* for both proposals (how much L2 data is worth collecting vs L1/L1+).
- Risk: separation in a frozen LLM between "error step" and "fine step" may be tiny (errors are subtle by
  construction), landing us in the low-γ regime where the bound is vacuous — but that also tells us L2-only is hopeless
  and pushes toward rollouts (proposal 1).
- Plausibility 3, Effort S.

*Card 2.2 — Treat human step disagreement as ω-uncertain (ambiguity) noise, not random flips; drop 50/50 items.*
- Mechanism: Def. 3.2 and App. C — under ω-noise the flipped labels are those near the boundary, so training is
  robust; Thm 3.3 Eq. (7): at ε = 1/2 the expected risk is exactly 1/2 (such samples carry zero information).
  Lemma B.3: early training follows the noisy-mean direction (robust); later steps rotate the boundary (memorize).
- Mapping: MP-Bench votes → per-step soft target p_t = votes_t/3; steps with 1-1-1 or 2-1 splits between
  *adjacent* steps are the ω-type ambiguity (benign for a ±k metric), whereas 2-1 splits between distant steps are
  ε-type. Train the step scorer with vote-weighted targets, remove trajectories with maximal disagreement, and use
  early stopping (few epochs) as the noise-robust regime. Output: when (exact/±k).
- Datasets: MP-Bench (289, three annotators); Failure-as-a-Process (t_err/t_lock/t_obs give three "legitimate"
  positions). Baseline: majority-vote hard labels, full training.
- Relation: strengthens proposal 2 (soft targets plug into the hazard likelihood as a mixture over candidate steps,
  see Card 7.1); complementary to PrefCleanBench's "remove, don't flip" (Card 4.1).
- Risk: with 289 logs, dropping disagreements may remove the hardest, most informative cases.
- Plausibility 3, Effort S.

**Quotable facts.** (i) HH-RLHF contains "more than 25% of noise" (Sec. 3.1, citing Yeh et al. 2025; Wang et al.
2024). (ii) Risk ≤ c·exp(−dγ²/(5(2+γ))) for ε ≤ 1/2 − O((2+γ)/γ·√(log N/N)) (Thm 3.3). (iii) Sample complexity
for robustness to noise rate ε grows at least as Õ(1/(γ²(1−2ε)²)) (Key takeaway 2). (iv) Post-RMSNorm Llama-3.1-8B
embeddings: average norm 139.6, norm variance 0.96; average cosine to class mean 0.956 (Table 1). (v) Mean-embedding
separation Llama-3.2-3B / 3.1-8B / 3.1-8B-Instruct = 3.33 / 5.09 / 7.21 (Behavior 1) and 10.3 / 18.3 / 19.5
(Behavior 2); more separated ⇒ more noise-robust (Table 2, Fig. 6).

**Code/data.** No code link in the text; experiments on Anthropic Persona with TRL; no new data.

---

## 3. Yeh, Wang, Du, Park, Tao, Im, Li — "Position: Challenges and Future Directions of Data-Centric AI Alignment" (ICML 2025 Position track)

**Paper.** Position paper with one small empirical study (App. A): 160 Anthropic-HH pairs (80 harmless + 80
helpful) re-labelled by three in-lab annotators with four options (chosen better / rejected better / both good /
both bad) and free-text notes; Fleiss κ 0.46; 25% "rejected is better" (contradicting the original label), 25%
"both are bad", <5% three-way disagreement. Thematic coding gives six sources of unreliability: (1) mislabeling,
(2) subjectivity / lack of context, (3) different preference criteria (concise vs detailed, direct vs clarifying
question), (4) different thresholds for the same criterion, (5) harmful content in both responses, (6)
misinformation/off-topic in both. Among low-IAA items: 2% / 28% / 29% / 37% / 0% / 4%; among "both bad" items:
0 / 0 / 25% / 0 / 39% / 36% (Table 3). Also: GPT-4 as judge is ~50/50 across repeated trials when two responses are
subtly different; prompt quality drives response quality; recommends "both good/both bad" options, committee-of-
reward-models disagreement to flag human mistakes (their earlier work), quality over quantity, verification.

**Transferable ideas.**

*Card 3.1 — Disagreement-source audit of step labels: how much "noise" is criterion mismatch that a definition fixes?*
- Mechanism: App. A.2 coding protocol (notes → codes → six themes) and the finding that 66% of low-agreement items
  come from *different criteria or thresholds*, not mistakes (Table 3, col. 2).
- Mapping to failure attribution: (1) mislabel; (2) missing context (truncated observation, screenshot not shown);
  (3) different criteria = earliest cause vs most proximate cause vs "who should have caught it" vs lock-in point;
  (4) different thresholds = how wrong a step must be before it counts; (5) "both bad" = several independent errors
  (set-valued label, nothing single is decisive); (6) "irrelevant" = failure not attributable to any step (ill-posed
  task, wrong gold answer, environment flake). Experiment: take MP-Bench items with split votes and Who&When items
  where LLM and human disagree; have 2–3 annotators code the disagreement with this taxonomy. Hypothesis: a large
  share falls under (3)/(4)/(5)/(6), which means the exact-step agreement ceiling is a *definition* problem; the
  interventional definition of proposal 1 (repair-effect profile; decisive step, error set, lock-in as summary
  statistics) resolves (3) and (4) by construction and makes (5) a first-class output. Also add a "no decisive
  step / multiple" option to any new labelling protocol (the paper's "both bad" lesson). Output: a measured
  decomposition of label noise; supervision L2 (human time only).
- Datasets: MP-Bench (289 logs, 3 votes), Who&When (184), TrajErrBench (κ 0.67 subset), AgentHallu.
- Relation: strengthens proposal 1 (gives the empirical motivation for a counterfactual definition and a way to
  show the human-vs-effect label disagreement is mostly criterion mismatch); new as an experiment.
- Risk: in-lab annotators; small N; coding is itself subjective (the paper's own κ was only 0.46).
- Plausibility 4, Effort S–M (≈100 items × 3 annotators).

No further cards: Directions 1, 2, 6, 7 (diverse/longitudinal collection, oversight, standardisation) are generic
and do not change what we would compute.

**Quotable facts.** (i) Re-annotation of 160 HH samples: 25% "rejected is better", 25% "both are bad", <5%
uncertain; Fleiss κ = 0.46 (App. A.1). (ii) Among low inter-annotator-agreement items only 2% are outright
mislabels; 28% subjectivity, 29% different criteria, 37% different thresholds (Table 3). (iii) Among "both are bad"
items: 39% harmful in both, 36% misinformation/irrelevant in both (Table 3). (iv) "GPT-4's selections can be evenly
split among multiple trials, choosing each option about half the time" on subtly different pairs (Sec. 4.2).
(v) Weak LLM feedback "rivals or even exceeds that of fully human-annotated data" (Sec. 3, citing Tao & Li 2025).

**Code/data.** None released (the 160 re-annotations are not stated to be public).

---

## 4. Yeh & Li — "Clean First, Align Later: Benchmarking Preference Data Cleaning for Reliable LLM Alignment" (PrefCleanBench, NeurIPS 2025)

**Paper.** Benchmark of 13 cleaning methods in three families, each with *remove* (-R) or *flip* (-F) treatment:
LLM-as-judge (GPT-4o scores both responses, random order); reward-gap (train 8 DPO models with different seeds on
the target data, average r(x,y_c)−r(x,y_r), flag bottom p∈{10..40}%); RM voting (committee of 6 public
RewardBench RMs — INF-ORM-70B, LDL-Gemma-27B, QRM-Gemma-27B, Skywork-Gemma-27B, GRM-3B, ArmoRM-8B — a member
"votes incorrect" if it ranks the rejected higher; VoteAll vs VoteMaj); heuristics (InsTag complexity/diversity of
the prompt, IFD = ppl(y|x)/ppl(y), IFD-gap between chosen and rejected). Protocol: SFT on chosen, then DPO
(Llama3-8B, LoRA r=16) on cleaned vs original; metrics = win-tie rate of cleaned-model outputs vs original-model
outputs (GPT-4o, 200 prompts, both orders) and average gold reward (URM-LLaMa-3.1-8B, also QRM and OffsetBias);
four datasets (Anthropic-HH 160k, UltraFeedback 55k, PKU-SafeRLHF 73k, HelpSteer2 8.7k); generalization across 8
optimizers (DPO, CPO, SLiC, KTO, AOT, IPO, rDPO, ORPO) and 5 base models. Findings: removing beats flipping
everywhere; VoteMaj-R is best and most transferable (HH: win-tie 0.705, avg reward 7.29 vs 6.00 vanilla;
PKU 0.770/8.48 vs 6.32); LLM-Judge-F and most -F variants fall below vanilla; optimum removal 20–30% ≈ known noise
in HH; VoteMaj flags low-quality *prompts* (greetings, vague asks) which flipping cannot fix; LLM-judge vs VoteMaj
disagree mainly when both responses are of similar (often both-bad) quality. Limitation: no ground truth for
cleaning precision/recall.

**Transferable ideas.**

*Card 4.1 — Committee-vote cleaning of human step labels; remove the trajectory, do not relabel it.*
- Mechanism: Sec. 3.3 RM voting (member votes "incorrect" when its own ranking contradicts the label; majority
  rule), Sec. 5.1 "Should we remove the data or flip the label?" (removal wins because many flagged items are
  unreliable for reasons other than a swapped label), Table 1/3/4 (VoteMaj-R best across datasets, optimizers,
  models), and the 20–30% sweet spot (Table 2).
- Mapping: a "committee member" is any step scorer that produces a ranking over steps of a failed trajectory:
  (a) 3–6 prompted LLM attributors of different families/prompts; (b) step-reward MLPs trained with different
  seeds on the noisy human labels (= the reward-gap member); (c) if replayable, proposal 1's rollout effect
  φ(τ,k,δ) as a model-free member; (d) proposal 2's label-free hazard model. A human label (trajectory, t*) is
  flagged when a majority of members rank some other step above t* by a margin; flagged trajectories are REMOVED
  from the training set (they are usually the "no single decisive step / ill-posed task" cases, the analogue of
  low-quality prompts), not relabelled to the committee's step. Train the final attributor on the cleaned set.
  Output: when/who; supervision L2 (+L1+ if rollouts used); text-only works.
- Datasets: train/clean on Who&When (184), LongRCA (1,140), MP-Bench (289 — here the three human votes let us check
  whether committee flags coincide with human disagreement), AgentErrorBench; test on high-agreement subsets
  (TrajErrBench τ²-bench, κ 0.91) and on injected sets with exact labels (Who&When Pro, CORRECT-Error, TracerTraj)
  where we can *inject* label noise (shift label to a neighbouring or random step) and measure cleaning precision/
  recall — the ground-truth evaluation the paper says it lacks. Baselines: train on raw labels; single-judge
  removal; flip-to-committee-step.
- Relation: new as a pipeline; strengthens proposal 1 (effect-based labels become a committee member and the
  "compare effect labels to human labels" task gets a decision rule) and proposal 2 (cleaned L2 set for the
  supervised comparison).
- Risk: with N≈200, removing 20–30% hurts; committee members built from the same LLM family share biases (the paper
  notes judge diversity is what makes VoteMaj work); prompted attributors are only 10–30% exact-step accurate, so
  majority disagreement with the human is the common case — need to flag on *margin* or ±k, not exact step.
- Plausibility 4, Effort M.

*Card 4.2 — Seed-ensemble reward-gap as a label-noise detector on scarce step labels.*
- Mechanism: Sec. 3.3 "Reward gap" — 8 models with different seeds trained on the *target* data, gap averaged,
  smallest-gap p% flagged (Wang et al. 2024 found a sizeable fraction of negative gaps in HH).
- Mapping: train 8 lightweight step-scorers (MLP on frozen (prefix, step) embeddings; see Card 5.1) on the human
  labels; for each trajectory compute gap = score(t*) − max_{t≠t*} score(t) averaged over seeds; a strongly
  negative gap that persists across seeds flags a label the data cannot support. Cheap at our scale (8 MLPs,
  minutes). Output: ranked list of suspicious labels for human re-check (ties to Card 3.1).
- Datasets: all L2 sets; validate on injected-noise versions of Who&When Pro.
- Relation: new; a member of Card 4.1's committee.
- Risk: with few hundred labels the ensemble can underfit and flag hard-but-correct labels; p must be tuned on
  injected data. Plausibility 3, Effort S.

**Quotable facts.** (i) "removing unreliable data generally performs a better alignment than flipping labels"
(Sec. 5.1). (ii) VoteMaj-R on Anthropic-HH: win-tie 0.705, avg reward 7.287 vs 6.001 uncleaned; on PKU-SafeRLHF
0.770 / 8.478 vs 6.318 (Table 1). (iii) LLM-Judge-F win-tie 0.570/0.585/0.625/0.515 with avg reward below vanilla
on all four datasets (Table 1). (iv) "The optimal filtering rate is achieved somewhere between 20% to 30%, which
aligns with the amount of noise known in datasets such as Anthropic-HH" (Sec. 5.1, Table 2). (v) LLM-judge vs
VoteMaj disagreement "usually happens when the two response candidates have a similar quality" — forced choice
gives ~1/2 chance of keeping a both-bad pair (Sec. 5.1). (vi) Cost: GPT-4o judging of 160k pairs ≈ $350; RM
voting < 6 h on 4×H200 (App. E).

**Code/data.** https://github.com/deeplearning-wisc/PrefCleanBench (modular implementations of all 13 methods).

---

## 5. Tao, Du, Li — "Limited Preference Data? Learning Better Reward Model with Latent Space Synthesis" (LENS, NeurIPS 2025)

**Paper.** Reward modelling with ~1,000 seed pairs. Signal: e = last-layer final-hidden-state embedding of
(prompt, response) from a frozen LLM (Llama-3.1-8B-Instruct, d=4096). Model: a VAE (2-layer MLP encoder/decoder,
hidden 64, latent d_VAE=16, β_KL=1; shared encoder/decoder with *separate* posterior heads for preferred vs
rejected — Table 5 shows this choice matters: 1.96 vs 1.35/1.47) plus a divergence term −W₂(q(z|e⁺), q(z|e⁻))
with weight γ=0.1 (γ too large over-separates and hurts, Fig. 2a/3). Synthesis: add N(0, 0.01·I) noise in latent,
keep top-k by likelihood under the posterior, decode; pairs = all (orig ∪ synth)⁺ × (orig ∪ synth)⁻. Reward model
= 2-layer MLP (hidden 256) on embeddings with Bradley–Terry loss. Theory: Thm 1 margin of synthetic pair ≥ original
margin − 2L_r(L_g t_δ + ε_rec)^α; Thm 2 augmentation strictly reduces estimation error once N > N₀, estimated
empirically N₀ ≈ 66 pairs (App. B.5, with ε_rec ∝ N^{−0.26}). Results (Best-of-16 gold reward, Skywork): HH-RLHF
1.43 → 1.86/1.94/2.20 at 2×/4×/8× vs best textual synthesis (full fine-tune) 1.93 at 8×; TL;DR 0.78 → 1.48 vs 1.23;
even 100 seed pairs: 0.68 → 0.93 (Fig. 2c); naive Gaussian sampling in LLM space collapses (0.94 at 8×). 0.5M
parameters vs 8B generator, 0.2h vs 3.6h synthesis; synthetic pairs keep 93.9% of original orderings under a
100k-trained oracle RM. Rejection-sampling SFT with the LENS RM wins 61% vs 39% (GPT-4 judge).

**Transferable ideas.**

*Card 5.1 — Step-level reward model from few hundred labelled trajectories via latent-space pair synthesis.*
- Mechanism: Secs. 3.1–3.3 as above; the key empirical facts are (a) a frozen-embedding MLP ≈ full fine-tuning at
  1k pairs (Table 1, 1.43 vs 1.49), (b) synthesis in a *learned* 16-d latent with a mild contrastive term beats both
  text-space LLM augmentation and naive embedding noise, (c) benefit persists down to 100 seed pairs.
- Mapping: sample = embedding of (prefix up to t, step s_t) from a frozen open model (last token hidden state;
  for long prefixes use the agent's own context window or a summary + last k steps). Positives = steps labelled
  non-error (all other steps of a failed run, or any step of a successful run — AgentHallu's 250 clean runs,
  HORIZON/TRAIL/Failure-as-a-Process successes); negatives = the labelled decisive step (and, as a variant, all
  steps after lock-in). Pairs are formed *within a trajectory* (same prefix family) so the MLP learns "which step
  in this run is the error". Train contrastive VAE on these embeddings, synthesize 4–8× pairs, train the BT MLP;
  at inference score every step of a failed run and output argmax / ranked list (nDCG) / P(error|prefix,step).
  Supervision L2 (also works with L1+: positives/negatives from rollout outcomes of the same prefix, which is the
  on-policy pair proposal 1 generates anyway). Grey-box only in the sense of needing an open encoder; all released
  text logs can be re-encoded.
- Datasets: Who&When (184), MP-Bench (289), LongRCA (1,140), TrajErrBench (486), AgentErrorBench (200),
  SearchAuditBench (1,243); cross-dataset transfer test. Baselines: MLP on original pairs only; prompted-LLM
  attributor; textual augmentation (LLM-paraphrased steps); the PRM/step-reward baselines already in the survey.
  Evaluate on both exact-step and ±k, and calibration of the sigmoid score.
- Relation: new; strengthens proposal 1 (the surrogate f(prefix, step, δ) ≈ effect is exactly an embedding-head
  regressor; Thm 1 holds for any Hölder-continuous scorer, so LENS-style augmentation of (embedding, effect) pairs
  is admissible) and gives proposal 2 a supervised comparator at the same cost.
- Risk: the negative class is heterogeneous (many failure modes) and subtle, so a single W₂ push may not create a
  usable latent separation (paper's γ ablation shows over/under-separation both hurt); synthetic embeddings are not
  decodable, so no human inspection of what was synthesized; long-context embeddings of 100-step prefixes may wash
  out the step. Mitigation: use the "difference" embedding (step with vs without the prefix) or per-step pooled
  states.
- Plausibility 4, Effort M.

*Card 5.2 — Order-preservation check as QA for any synthetic/pseudo-labelled attribution data.*
- Mechanism: App. B.5.4 — a strong oracle RM scores original and synthetic pairs; report retained ordering (93.9%)
  and gap shrinkage (2.86 → 2.64).
- Mapping: whenever we manufacture training pairs (latent synthesis, weak-LLM labels of Card 6.1, candidate-set
  distillation of Card 7.1, injected failures), score them with the most trustworthy oracle we have — rollout effect
  on replayable data, or human-majority on MP-Bench — and report the retained-ordering rate before training.
- Relation: methodological glue; strengthens proposal 1 (effect as oracle). Plausibility 4, Effort S.

**Quotable facts.** (i) HH-RLHF with 1,000 seed pairs: gold reward 1.43 → 2.20 at 8× latent augmentation vs 1.93
for text-space synthesis with full fine-tuning (Table 1). (ii) "18× faster in generation and using a 16,000×
smaller model" (abstract; 0.5M vs 8B, 0.2h vs 3.6h, Table 2). (iii) Embedding MLP without augmentation ≈ full
fine-tuning (1.43 vs 1.49 HH; 0.78 vs 0.69 TL;DR) (Table 1). (iv) With only 0.1k seeds, 4× augmentation lifts
0.68 → 0.93 (Fig. 2c); theoretical threshold N₀ ≈ 66 pairs (App. B.5.1). (v) Synthetic pairs retain 93.9% of
original preference orderings under an oracle RM (App. B.5.4). (vi) Naive Gaussian sampling in LLM embedding space
degrades monotonically (1.43 → 0.94 at 8×) (Table 1).

**Code/data.** https://github.com/deeplearning-wisc/lens.

---

## 6. Tao & Li — "Your Weak LLM is Secretly a Strong Teacher for Alignment" (ICLR 2025)

**Paper.** Semi-supervised alignment. Labelled D_l (human pairs) and unlabelled D_u (triplets (x,y₁,y₂) without
preference). Weak LLM π_w (OPT-125M): SFT on (x,y_w) of D_l, then DPO on D_l; its implicit reward r_w(x,y) =
β log π_w(y|x)/π_w^SFT(y|x) labels D_u (ŷ_w = argmax r_w). Student (OPT-1.3B…13B, Llama-2-7B, Mistral-7B,
Gemma-7B): SFT on weak-chosen then DPO on D_weak. Evaluation: gold reward (Mistral-7B Unified-Feedback RM; also
DeBERTa and RM-Mistral) and GPT-4 win rate vs the same student trained on human labels of D_u. Results: weak
feedback ≥ human feedback (OPT-1.3B 4.84 vs 4.63; Mistral-7B 7.90 vs 7.19; TL;DR 3.29 vs 2.71), GPT-4 win rate
≈50%; supervisor size barely matters (125M 4.84, 1.3B 4.78, Llama-3-8B 4.91) and *prompted GPT-4 is worse*
(4.52); labelled fraction 1/16 still 4.31 vs 4.37. Analysis: weak labels agree with humans on 60.6%; on the
mismatched 39.4%, 44.3% of weak choices have higher gold reward; gold-reward gap is 2.27 on matched vs −0.36 on
mismatched (weak LLM errs on subtly different pairs); GPT-4 ten-trial consistency 0.84 (match) vs 0.66 (mismatch);
training on the mismatched set alone still gives +1.79, whereas random-flip noise of the same rate gives −0.69 —
weak-LLM "noise" is systematic and benign, not random.

**Transferable ideas.**

*Card 6.1 — Small task-specific attributor trained on ~200 human labels as the pseudo-labeler for unlabelled failures.*
- Mechanism: Sec. 3.1 three-stage pipeline (train weak model on D_l → implicit reward labels D_u → train student);
  Fig. 2b (task-specific 125M beats prompted GPT-4); Fig. 4a (1/16 labelled suffices); Table 11 (weak-LLM errors ≠
  random flips).
- Mapping: D_l = human (prefix, error step, non-error step) pairs from Who&When/MP-Bench/LongRCA; weak model = a
  0.1–1B LM (or the embedding-MLP of Card 5.1) trained with BT/DPO on them; D_u = every failed trajectory we have
  without step labels (self-collected runs, HORIZON/MAST-Data failures (trace-level only), the unlabelled halves of
  any benchmark run, and — with care about position skew — injected sets); the weak scorer ranks steps in each
  unlabelled run and emits (prefix, top step, other steps) pairs; the final attributor (bigger model) is trained on
  the union. The paper's central claim to test in our domain: a *task-specific* weak scorer labels better than a
  *prompted* frontier LLM — plausible given prompted LLMs' 10–30% exact-step accuracy.
  Output: when (+who in MAS by reading the step's emitter). Supervision: small L2 + large L0.
- Datasets: label with a model trained on LongRCA (largest), evaluate on Who&When and MP-Bench (held out);
  reverse direction too. Baselines: prompted-LLM pseudo-labels; training on human labels only; self-training with
  the final model itself.
- Relation: new; complementary to proposal 2 (the hazard model fitted on outcome labels is itself a candidate weak
  teacher: L1-trained teacher → pseudo step labels → supervised student), and to Card 7.1 (teacher can emit
  candidate sets instead of single steps).
- Risk: the paper's success rests on human labels being as noisy as weak-LLM labels in a *generation* task scored
  by a gold RM; attribution is a localization task with a hard metric, and weak-model errors concentrate on
  "subtle" pairs — which for us are adjacent steps, i.e. most of the mass. Position skew of injected sets may be
  learned as a shortcut.
- Plausibility 4, Effort M.

*Card 6.2 — Attributor self-consistency as an ambiguity detector for step labels.*
- Mechanism: Sec. 4 / Table 5: ten GPT-4 trials; majority fraction 0.84 on clear pairs vs 0.66 (down to 0.5) on
  subtly different pairs; low consistency ⇔ responses indistinguishable.
- Mapping: run the LLM attributor k=10 times (temperature >0) on each trajectory; consistency c = fraction of
  trials agreeing with the modal step (or entropy over steps). Use c to (a) predict which trajectories humans will
  disagree on (validate against MP-Bench vote splits and TrajErrBench κ subsets), (b) route low-c trajectories to
  candidate-set labelling / removal (Cards 7.1, 4.1), (c) report accuracy stratified by c so benchmark numbers
  separate "hard because ambiguous" from "hard because subtle". Output: calibration-like signal; supervision none
  (L0 + LLM calls).
- Datasets: MP-Bench first (direct check), then Who&When, LongRCA.
- Relation: new, cheap; feeds both proposals' evaluation sections. Risk: temperature sampling measures model
  randomness, not label ambiguity, if the model is simply bad; the paper's own Table 4 (CanDist) shows sampled
  diversity is a weak proxy for inherent uncertainty.
- Plausibility 4, Effort S.

*Card 6.3 — Audit human-vs-model mismatches with an objective oracle (rollout effect).*
- Mechanism: Sec. 4 Table 2/3: on mismatched items, the gold RM sided with the weak LLM 44.3% of the time, i.e.
  "human feedback is similarly imperfect".
- Mapping: on replayable data (TraceElephant, SymFail, AgentRx, self-collected), when the model's step and the
  human's step differ, replay with a fix at each and compare P(success); the fraction of mismatches where the
  model's step has the larger repair effect is a direct, label-free estimate of human mislabel rate.
- Relation: this is essentially proposal 1's "compare effect-based labels to human labels" task — mark as
  *strengthens proposal 1* (adds the mismatch-conditioned framing and the 44.3% reference point), not new.
- Plausibility 4, Effort M (rollouts). 

**Quotable facts.** (i) OPT-125M feedback beats human feedback for OPT-1.3B student: gold reward 4.84 vs 4.63; and
beats prompted GPT-4 feedback (4.52) (Fig. 2). (ii) With only 1/16 of the data labelled, weak feedback gives 4.31
vs 4.37 for human (Fig. 4a). (iii) Weak labels match human labels on 60.6%; of the mismatches, 44.3% of weak
choices have higher gold reward (Sec. 4). (iv) Gold-reward gap chosen−rejected: 1.52 human, 2.27 matched, −0.36
mismatched (Table 2). (v) GPT-4 ten-trial preference consistency 0.84 (match) vs 0.66 (mismatch) (Table 5).
(vi) Training on the fully mismatched set still improves the student by +1.79 while equally frequent random flips
give −0.69 (Tables 1 and 11).

**Code/data.** https://github.com/deeplearning-wisc/weak_llm_teacher.

---

## 7. Xia, Wang, Li, Yu, Wang, Zhao, Wu — "Prompt Candidates, then Distill: A Teacher-Student Framework for LLM-driven Data Annotation" (CanDist, arXiv 2506.03857, ACL-style 2025)

**Paper.** LLM annotation for text classification without human labels. Instead of a single label, prompt the LLM
(GPT-3.5; also Llama-3.1-8B, GPT-4o) for a *candidate set* s ⊆ Y: CA_add ("if unsure, include other potential
choices") or CA_all ("all possible choices"). Coverage 1−α (true label ∈ s) rises from 71.1 → 74.7 / 89.1 on TREC
with only 1.07 / 1.70 labels on average; across six datasets CA_all adds 14–27 points of coverage with ≤2 labels
(Table 8). Prompting candidates beats self-consistency sampling: 40 sampled paths reach 1−α 84.3 at 1.39 labels
vs CA_all 89.1 at 1.70 from one call (Table 4). Then distil a RoBERTa-base student with *Distribution Refinery*:
target q_i = student's softmax renormalized over the candidate set (uniform at t=0, Eq. 1); filter samples whose
argmax falls outside the candidate set (Eq. 2); class-wise small-loss selection + temperature sharpening of
reliable targets (Eq. 3); out-of-candidate samples with max prob > τ get their argmax as label (Eq. 4); plus
back-translation consistency and mixup. Theory (Thm 1, linearized softmax, class-structured feature similarity a>b):
the student distilled from the teacher's top-2 reaches 100% train accuracy under R_cc' + Σ R_ci < 1 (true label
merely most frequent), while top-1 needs the stricter < 1 − θ/(φ−θ). Results: TREC test 87.80 vs FreeAL 82.33 vs
few-shot 77.20; MA/DBpedia on par with supervised fine-tuning; "let the LLM select from the candidates" is 3.7–3.9
points *worse* than SLM distillation (Table 3); with GPT-4o: 96.40 vs 87.60 few-shot; CanDist + 20% human labels ≈
active learning with 50% (Fig. 6, App. B.5).

**Transferable ideas.**

*Card 7.1 — Candidate-step annotation + partial-label distillation of a step attributor (set-valued labels are the
native format of this problem).*
- Mechanism: Sec. 3.2 (prompt for all plausible labels; coverage/F1 metrics 1−α, β-coverage), Sec. 3.3 Eqs. 1–5
  (Distribution Refinery), Thm 1 (top-2 distillation needs only that the true label be the most frequent candidate),
  Table 3 (distilling beats asking the LLM to pick from its own candidates).
- Mapping: label space for a given trajectory = its steps {1..T}; the "LLM annotator" is a prompted attributor asked
  for *all steps that could be the decisive error* (CA_all) or "best guess + alternatives if unsure" (CA_add);
  humans can be asked the same way, and MP-Bench's three votes, SearchAuditBench's tolerance spans, and
  Failure-as-a-Process's (t_err, t_lock, t_obs) are already candidate sets. Student = a per-trajectory step scorer
  (embedding-MLP of Card 5.1, or a small LM with a softmax over steps) trained with q_i = its own prediction
  renormalized over the candidate set, out-of-candidate filtering, small-loss selection per trajectory length
  bucket (the class-wise selection analogue). The correct step "emerges" from the candidates as the model learns
  what error steps look like across trajectories. Metrics: exact-step, ±k, nDCG of the ranked candidates, and
  coverage 1−α of the LLM's candidate sets (a new, cheap benchmark statistic: how often is the human step inside
  the LLM's candidate set?). Supervision: L0 + LLM candidates, or L2-set. Text-only.
  Synthesis with proposal 2: the survival likelihood with a candidate set S is the partial-label likelihood
  Σ_{t∈S} h_t ∏_{s<t}(1−h_s) — so the hazard model is a natural student and MP-Bench votes / tolerance spans become
  usable supervision for it without choosing one step.
- Datasets: MP-Bench (union of votes = candidate set; majority = check), SearchAuditBench (1,243 with tolerance
  spans — the largest natural set with interval labels), Who&When / LongRCA (LLM-drafted candidate sets, humans as
  test), AgentHallu. Baselines: single-label LLM annotation + distillation (FreeAL-style), majority vote over
  sampled attributions (self-consistency), LLM-select-from-candidates, human-label-only training.
- Relation: new, and the strongest strengthening of proposal 2 in this batch (gives it a principled way to use
  set-valued human labels and LLM drafts).
- Risk: Thm 1 assumes a fixed label space with class-structured similarity; steps are trajectory-specific, so the
  memorization-effect argument (easy patterns first) may not transfer to localization among 100 steps; candidate
  sets for long trajectories could be large (the paper keeps ≤2 labels), diluting the signal — enforce a cap or use
  intervals.
- Plausibility 5, Effort M.

*Card 7.2 — "Ask for all plausible steps once" instead of sampling the attributor many times.*
- Mechanism: Table 4 — one CA_all call: coverage 89.1 at 1.70 labels; 40 self-consistency samples: 84.3 at 1.39;
  SC on top of candidates helps further (Fig. 4/5).
- Mapping: a one-line change to every prompted-LLM attributor baseline: request the candidate set of decisive
  steps (and optionally rank them). Report recall@|S| and nDCG alongside exact-step; use the candidate set as the
  input to Card 7.1 / Card 4.1 and as the human anchor set (reduces LLM anchoring to a *single* wrong step, which is
  the documented bias in human labelling). Output: ranked candidate list; supervision none.
- Datasets: Who&When, MP-Bench, LongRCA (nDCG is already a metric in the survey).
- Relation: new, trivial to run; strengthens both proposals' evaluation. Risk: LLMs may over-include (coverage up,
  F1 down — the paper's AGNews case). Plausibility 4, Effort S.

*Card 7.3 — Annotation budget: 20% human + candidate distillation ≈ 50% human with active learning.*
- Mechanism: App. B.5 / Fig. 6 (CanDist-hybrid).
- Mapping: for a new attribution dataset, label 20% of trajectories by humans (used for small-loss calibration and
  as test), LLM-candidate the rest, distil. Relation: planning guidance for data collection; Plausibility 3,
  Effort S (it is a protocol, not an experiment).

**Quotable facts.** (i) Candidate prompting raises coverage of the true label from 71.07% (single) to 89.09% on
TREC with 1.70 labels on average (Table 8). (ii) One candidate-prompt call (89.1 coverage) beats 40 self-consistency
samples (84.3) (Table 4). (iii) Letting the LLM pick from its own candidates loses 3.74–3.90 points on average vs
distilling a small student (Table 3). (iv) Top-2 distillation needs only R_cc' + Σ_{i≠c} R_ci < 1 vs top-1's
< 1 − θ/(φ−θ) (Thm 1). (v) TREC test accuracy: few-shot 77.20, FreeAL 82.33, CanDist_all 87.80; with GPT-4o 87.60 →
96.40 (Tables 2, 10). (vi) CanDist + 20% human labels matches active learning with 50% human labels (App. B.5).

**Code/data.** https://github.com/MingxuanXia/CanDist.

---

## Batch ranking (top 5 across the batch)

1. **Card 7.1 — Candidate-step annotation + partial-label distillation; hazard model as the student (plausibility 5,
   M).** Set-valued labels are what we already have (MP-Bench votes, tolerance spans, t_err/t_lock/t_obs); Thm 1
   says distilling from candidates tolerates far more noise than single labels; gives proposal 2 a way to use L2-set.
2. **Card 4.1 — Committee-vote cleaning of human step labels, remove-don't-flip, with precision/recall measured on
   injected-noise exact-label sets (4, M).** Directly attacks the 40–90% agreement problem; rollout effect (proposal 1)
   is a model-free committee member.
3. **Card 5.1 — Latent-space synthesis of (prefix, step) pairs for an embedding-MLP step reward model (4, M).**
   Works from ~100 seed pairs (N₀≈66), 0.5M-parameter generator, beats text augmentation; same head serves as
   proposal 1's effect surrogate.
4. **Card 6.1 — Small task-specific attributor as pseudo-labeler for unlabelled failures (4, M).** Task-specific
   125M beat prompted GPT-4 as a labeler; our prompted attributors are at 10–30% step accuracy, so a trained small
   scorer plausibly labels better; proposal 2's L1 model can be the teacher.
5. **Card 3.1 + Card 6.2 — Disagreement-source audit and attributor self-consistency as ambiguity detector (4, S).**
   Cheap; likely shows most "label noise" is criterion mismatch (66% in the HH study), which is exactly what proposal
   1's interventional definition removes; consistency stratifies benchmark accuracy into ambiguous vs subtle.

Honourable mentions: Card 7.2 (ask for all plausible steps once; 4, S — run next week as a baseline change);
Card 1.1 (on-policy bad step cannot be flipped by finite-step DPO — a design constraint, 3, S); Card 2.1 (embedding
separation → noise-tolerance/sample budget, 3, S). Paper 3's collection/oversight directions and Paper 1's log K
law for taxonomies (Card 1.2, 2) are low-value for us.
