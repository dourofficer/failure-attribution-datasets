# Batch E — RL post-training objectives, reward shaping, evaluator-free selection

Papers: HERO (hybrid sparse+dense reward), LAD (advantage-distribution matching), GEB (optimistic exploration bonus in RLHF), CodeLutra (iterative DPO from correct/incorrect code), ModeX (evaluator-free Best-of-N by spectral mode extraction). All five come from Sharon Li's group (UW-Madison), two with Meta/Adobe.

Reading angle: (a) an attributor can itself be RL-trained (existing GRPO-tuned 8B attributors with step-distance rewards); (b) sparse outcome reward vs dense step scores = the L1 vs L2 supervision gap; (c) evaluator-free mode finding over N candidate attributions or N rollouts; (d) learning from correct AND incorrect attempts = success/failure trajectory pairs; (e) anything on advantage/variance normalisation useful for training a step-level hazard/value model from outcome labels.

---

## 1. HERO — "Hybrid Reinforcement: When Reward Is Sparse, It's Better to Be Dense"
arXiv 2510.07242v3 (Oct 2025), FAIR Meta + UW-Madison (Tao, Kulikov, Saha, Wang, Xu, Li, Weston, Yu).

**Mechanism.** GRPO for math reasoning where the per-rollout reward is built from two sources: a rule-based verifier r_rule ∈ {0,1} (math_verify) and a continuous reward-model score r_RM (AceMath-7B-RM). *Stratified normalisation* (Eq. 3, §3.2): within a group of N rollouts, partition by r_rule, then min–max normalise r_RM separately inside each stratum into [−α, α] for r_rule=0 and [1−β, 1+β] for r_rule=1 (α=β=0.05 on easy-to-verify data, 0.1 on hard/mixed). The verifier fixes the ordering between strata; the RM only orders *within* a stratum, so a group where all rollouts fail (all-zero → zero GRPO advantage) now has a gradient. *Variance-aware weighting* (Eq. 4–5): per prompt, w(σ_u) = w_min + (w_max−w_min)·sigmoid(k(σ_u − σ̄)) where σ_u = std of RM scores across the prompt's rollouts and σ̄ a running mean (w_min=0.4–0.5, w_max=2–3, k=5–6); r_final = w · r̂. Supervision: a verifier + an off-the-shelf RM, no step labels. Evaluated on Qwen3-4B-Base and OctoThinker-8B-Hybrid-Base after a 2k-sample SFT cold start, 2k RL prompts from OpenMathReasoning, 8–16 rollouts, 20 epochs. Key numbers (Table 2, Qwen3-4B, trained on easy-to-verify): easy-to-verify avg 62.0 vs 58.3 (verifier only) vs 56.4 (RM only); hard-to-verify avg 66.3 vs 57.1 vs 54.6. Ablations: dense *negatives* matter more than dense positives (Fig. 2a: none 59.4/62.2; pos-only 60.3/65.2; neg-only 61.4/68.4; both 62.0/73.2 on easy/hard); reweighting +1.2/+3.8 (Table 4); 72B RM gives no gain over 7B (Table 5); naive weighted sum of verifier and RM scores reaches only 55.9–58.7 / 60.2–61.4 (Table 9); RM-only training reward-hacks on non-verifiable data (App. A.3: MATH500 accuracy falls from ~0.75 at step 50 to <0.2 at step 100 and ~0 at step 150 while RM reward keeps climbing).

### Idea cards

**E1.1 — Verifier-gated dense reward for RL-trained attributors**
- *Mechanism in paper:* Eq. 3 stratified normalisation + Eq. 4 variance weighting; "HERO introduces reward differences within regions where the rule-based rewards are all 0 or all 1, thereby enabling meaningful gradient flow even when the rule-based verifier assigns the same outcome to all rollouts" (§3.2). Dense negatives are the component that matters (Fig. 2a).
- *Mapping:* the policy is the attributor; a "rollout" is one sampled attribution (t̂, agent, category, rationale) for a log; the "verifier" is the sparse exact match (t̂ = t*, or agent match, or t̂ within the annotators' tolerance span / vote set); the "RM" is any continuous proxy: (i) step distance |t̂ − t*| (what existing GRPO attributors already use, but as the *whole* reward), (ii) an LLM-judge score of the rationale, or (iii) — the interesting one — the replay effect φ(τ, t̂, δ) from proposal 1 (does fixing the predicted step actually rescue the run?). Stratify: among rollouts that hit the verifier (correct agent / within-span), rank by distance or φ; among misses, rank by distance or φ into [−α, α]. With natural step accuracy at 10–30%, most GRPO groups are all-miss, i.e. precisely HERO's zero-gradient regime, and HERO's finding that the *negative* stratum carries the learning signal says the dense-negative design is where the gain will be. Variance weighting: logs whose N sampled attributions are widely spread (high σ of φ or of t̂) get up to 2–3× weight; logs where all N rollouts agree are down-weighted. Output: when/who/what. Supervision: L2 for the gate (labelled logs) or L1+ if the gate is the replay outcome (φ > 0 ⇒ "verified"); text-only.
- *Datasets / baseline:* train on Who&When Pro / TracerTraj / CORRECT-Error (exact labels, large), fine-tune/eval on Who&When, TraceElephant, MP-Bench (use the 3-annotator vote set as the gate, distance to the modal vote as the dense signal), TrajErrBench, LongRCA. Baseline: the same 8B GRPO recipe with (a) binary exact-match reward, (b) pure step-distance reward, (c) naive weighted sum of the two (HERO Table 9 predicts (c) underperforms).
- *Relation to proposals:* new (training-objective level); becomes a direct consumer of proposal 1 if φ is used as the dense signal, and gives proposal 1 a concrete downstream use for the surrogate f(prefix, step, δ).
- *Main risk:* the dense proxy may be badly aligned with the human label on natural failures (HERO's own App. B.1 shows 13.7% of RM groups rank at chance; step distance is a poor proxy when the cause is 40 steps before the symptom). Also HERO's gains were on math with a 7B RM trained on the same domain; no equivalent off-the-shelf "attribution RM" exists.
- *Plausibility 4, Effort M.*

**E1.2 — Outcome-variance weighting and graded-failure targets for an L1+/L1 hazard model**
- *Mechanism in paper:* Eq. 4 up-weights prompts with high intra-group score variance ("ambiguous, high-variance prompts are emphasized because they reveal more about model weaknesses"); Fig. 2a shows gradations among *failed* rollouts carry more signal than gradations among successes.
- *Mapping:* in proposal 2's L1+ setting (N continuations of each prefix), the per-prefix success rate p_k has variance p_k(1−p_k); prefixes with p_k ≈ 0 (already locked in) or ≈ 1 (nothing has gone wrong yet) are uninformative about *where* the error is, whereas prefixes in the transition region are where t* and t_lock live. Weight the hazard-model likelihood terms at prefix k by a HERO-style bounded sigmoid of the rollout-outcome variance so model capacity concentrates on the transition region instead of on the long flat tails of 150-step runs. Second, where the environment returns a *graded* outcome (WebShop reward ∈ [0,1], fraction of SWE-Bench tests passed, τ²-bench partial credit), use HERO's stratification: binary PASS/FAIL fixes the stratum, the graded score orders trajectories *within the FAIL stratum* — i.e. "how far did this failed run get" becomes a dense target for the hazard model while never letting a high partial score outrank a pass. Output: P(fail | prefix), t*, t_lock. Supervision L1 / L1+; text-only.
- *Datasets / baseline:* self-collected rollouts in replayable envs (ALFWorld/WebShop → AgentErrorBench; τ²-bench/SWE-Bench Pro → TrajErrBench; SymFail, TraceElephant replays). Baseline: unweighted MLE hazard fit (proposal 2 as drafted) and OAT.
- *Relation:* strengthens proposal 2 (a weighting/target refinement, not a new estimator).
- *Main risk:* with small N (8–16 rollouts per prefix) the variance estimate is itself noisy; the effect was +1.2/+3.8 points in HERO, so expect a modest gain.
- *Plausibility 3, Effort S.*

### Quotable facts
- Table 1 (750 responses on HardVerify_Math): math_reward (verl) recall 10.1% / precision 97.5% / FPR 0.3%; math_verify (verl) recall 68.4% / precision 100%; AceMath-7B-RM at threshold 1 recall 91.7% / precision 67.7% / FPR 46.4% — the precision–recall trade-off between rule and model verifiers.
- Fig. 2a (Qwen3-4B, easy-to-verify training): dense negatives alone lift hard-to-verify accuracy 62.2 → 68.4; dense positives alone 62.2 → 65.2; both 73.2. "Dense negative ranges are more important than positive samples."
- Table 9: a naive weighted sum of verifier and RM reward (α ∈ {0.1, 0.5, 0.9}) gives 55.9–58.7 easy / 60.2–61.4 hard vs HERO 62.0 / 73.2.
- Table 5: replacing the 7B RM with a 72B RM changes 62.0/73.2 to 62.8/71.4 — "the gains of HERO primarily come from its hybrid reward formulation ... rather than from reward model scaling."
- App. B.1: RM scores vs verifier labels, AUROC per rollout group: mean 0.79, median 0.92, ~80% of groups > 0.7, 13.7% in 0.4–0.6.

### Code/data released?
No code link in the paper text; relies on verl, math_verify, AceMath-RM-7B (all public). Training data drawn from OpenMathReasoning; TextBookReasoning filter described in App. A.2.3.

---

## 2. LAD — "Learning Advantage Distribution for Reasoning"
arXiv 2602.20132v1 (Feb 2026), UW-Madison (Wendi Li, Sharon Li).

**Mechanism.** Replaces GRPO's expected-advantage maximisation with distribution matching. Lemma 3.1: the trust-region (KL-constrained) optimum satisfies π*/π_old ∝ exp(A/η). LAD defines the policy-induced distribution P_π ∝ π_θ/π_old and the advantage-induced target P_A ∝ exp(A/η) and minimises an f-divergence between them (Eq. 7). Because the normalisers are intractable, Lemma 3.2 gives a surrogate with the same optimum: L_LAD = E_{y∼π_old} exp(A/η) · f( (π_θ/π_old) · exp(−A/η) ) (Eq. 8). Its gradient weight f'( ratio · e^{−A/η} ) depends jointly on the advantage and the likelihood ratio, so growth of log π_θ for a high-advantage response is suppressed once the ratio is already large — an implicit, advantage-aware trust region without entropy bonus or clipping (§3.3, App. B.4). Advantage A is still GRPO's group-normalised outcome reward; cost equals GRPO (Fig. 5). Strict divergences (JS, Hellinger, TV) beat KL/rKL/Jeffreys (Fig. 4); JS used in main runs; robust to η ∈ [1/32, 4] (Table 6). Bandit (50 arms, 3-mode advantage): LAD recovers all three modes, GRPO collapses to one, FlowRL partially (Fig. 1). LLM results (Table 1, Qwen2.5-7B on DAPO-MATH, Avg@32 over six math sets): GRPO 37.28 → LAD 40.08; Pass@32 65.76 (+2.63 over FlowRL); code (Table 2, DeepSeek-R1-Distill-7B on DeepCoder): LiveCodeBench Avg@16 32.46 → 33.51, CodeForces percentile 70.3 → 82.5; diversity dist-4 0.290 → 0.444, GPT-4 logical-diversity 2.04 → 2.58 (Table 4). FlowRL shown to be the η→∞, small-step special case (App. B.5).

### Idea cards

**E2.1 — Distribution-matching attributor: learn P(step) ∝ exp(φ/η) instead of argmax**
- *Mechanism in paper:* Eq. 5 target P_A(y|x) ∝ exp(A(x,y)/η) and Eq. 8 surrogate; "preserve multiple promising reasoning modes instead of collapsing onto a single high-reward trajectory" (§1); bandit result Fig. 1.
- *Mapping:* attribution labels are intrinsically multimodal: humans agree on the exact step only 40–90% of the time, MP-Bench stores set-valued votes from three annotators, Failure-as-a-Process distinguishes t_err/t_lock/t_obs, and proposal 1's repair-effect profile φ(τ,k,δ) is a whole curve over k, not a point. A GRPO-trained attributor with a distance reward is pushed to collapse onto one mode — in practice the salient symptom step t_obs. Train the attributor (or proposal 1's surrogate f(prefix, step)) with LAD so that its distribution over candidate steps matches softmax(φ(τ,·)/η) (or softmax of −distance to the annotator vote set). The output is then a calibrated ranked list over steps, which is what nDCG, set-F1 and the P(fail|prefix) calibration metrics in the brief actually score; argmax of the matched distribution still yields the exact-step prediction. Supervision: L2 (votes) or L1+ (φ from rollouts); text-only.
- *Datasets / baseline:* MP-Bench (vote sets), SearchAuditBench (tolerance spans), Failure-as-a-Process (three timestamps), Who&When Pro for scale. Baseline: GRPO attributor with identical advantage; FlowRL; GRPO + entropy bonus. Compare on exact-step, set-F1, nDCG and on calibration of the step distribution against the empirical vote histogram.
- *Relation:* strengthens proposal 1 (gives the surrogate-learning task a principled objective: match the φ-profile rather than regress its argmax) and is complementary to E1.1 (reward design) — the two compose.
- *Main risk:* LAD's benefit was measured as diversity + Avg@k on math/code; on single-label datasets a flatter step distribution may lower exact-step accuracy while helping set metrics — the trade-off has to be shown. η sets the sharpness and interacts with the scale of φ.
- *Plausibility 3, Effort M.*

(No second card: LAD's other contributions — surrogate bound Thm B.1, divergence choice, FlowRL reduction — are internal to the RL objective and do not change the mapping.)

### Quotable facts
- Table 1: Avg@32 GRPO 37.28 vs LAD 40.08 (AIME 2024 14.03 → 19.60); Pass@32 average 65.76, +2.63 over FlowRL (App. C.3).
- Table 2: CodeForces rating 1355 → 1534, percentile 70.3% → 82.5%; HumanEval+ Pass@16 93.25 → 95.71.
- Table 4 (AIME 24/25 rollouts): dist-4 GRPO 0.2902 → LAD 0.4442; GPT-4 logical-diversity score 2.04 → 2.58.
- §4.3 / Fig. 4: strict divergences (TV, Hellinger, JS) outperform KL, reverse-KL and Jeffreys "because they penalize discrepancies symmetrically."
- App. B.3, Fig. 6: during training, GRPO-normalised advantages stay within roughly ±0.4 and |log π_θ/π_old| < 0.2 — the small-advantage / small-step assumptions the surrogate bound relies on.

### Code/data released?
"Code is available here" (link stripped in extraction); trained on DAPO-MATH and DeepCoder (public).

---

## 3. GEB — "General Exploratory Bonus for Optimistic Exploration in RLHF"
ICLR 2026 (arXiv 2510.03269v4), UW-Madison (Wendi Li, Changdae Oh, Sharon Li).

**Mechanism.** Iterative online DPO (3 rounds; URM-LLaMa-3.1-8B as preference oracle; Llama-3-8B-SFT and Mistral-Instruct-v0.3). Defines an "optimism condition" for an exploratory bonus: ∂/∂π_s(∂L_bonus/∂π) < 0, i.e. responses rare under the sampling/reference policy must receive a larger upward push (Def. 3.1). Proves that the prior bonus L_bonus = max_π J_{β,f}(π, r) (SELM, XPO, VPO) violates it under KL and the whole α-divergence family (Lemma 3.1–3.2, Thm 3.3: the bonus pulls π toward π_ref and amplifies reward where π_ref is already high; under reverse KL the realised bonus is a constant — Table 1). GEB instead adds a π_ref-dependent regulation and, after reward reparameterisation, the bonus becomes L_bonus = β E_{y∼π_ref}[u f'(u) − f(u)] with u any decreasing function of π(y|x) with u > α (Eq. 11, Table 2: u = 1+α−π, 1/π, arctanh(1−π)+α); computed on rejected responses only, no extra sampling. Results: UltraFeedback win-rate vs base, Mistral/KL 78.42 (f-DPO) → 81.00 (GEB-π); Hellinger 72.69 → 75.69; LLaMA/KL 73.11 → 74.98 (Table 3); on 12K DAPO-MATH prompts where Qwen2.5-7B fails within 2 samples, Pass@16 avg 56.94 → 62.75 (Table 6). Bonus/loss ratio must sit in ~1e-2–1e-6 (Fig. 3).

### Idea cards

**E3.1 — Optimism bonus against the "symptom-step prior" of a preference-trained attributor** (speculative)
- *Mechanism in paper:* Eq. 11 with u decreasing in π, applied to rejected responses, provably raises probability of low-π_ref outputs; Table 6 shows the gain concentrates on prompts whose correct answer lies where the reference model rarely samples.
- *Mapping:* a base LLM attributor's prior puts mass on the observable crash step t_obs; the true decisive step (dozens of steps earlier, subtle) is a low-π_ref output — the exact regime of GEB's Table 6. When fine-tuning an attributor by iterative DPO on (correct, incorrect) attribution pairs (cf. E4.2), add a GEB bonus on the rejected attributions so that early/rare candidate steps gain probability instead of the policy collapsing back to the reference's symptom-step habit. Output: when. Supervision L2 (or L1+ with φ as the preference oracle); text-only.
- *Datasets / baseline:* Who&When Pro (position skew makes it a poor test — natural sets needed), LongRCA (median 145 steps, long cause-to-symptom gaps), Failure-as-a-Process (t_err vs t_obs gap is explicit). Baseline: iterative DPO without bonus; DPO + SELM/XPO-style bonus (GEB predicts no gain).
- *Relation:* new, but only as an add-on to a DPO-trained attributor (E4.2).
- *Main risk:* the attributor's answer space is a finite list of T steps — exploration can be done by enumeration or stratified sampling of candidate steps at rollout time, which makes an in-loss bonus a roundabout remedy; GEB's gains in RLHF are 1–3 win-rate points and sensitive to κ over four orders of magnitude.
- *Plausibility 2, Effort M.*

### Quotable facts
- Lemma 3.1: with KL regularisation, "r1 and r2 yield the same set of policies" — the SELM/XPO/VPO-style exploratory bonus provably does not change the induced policy.
- Table 1: under reverse KL the realised bonus is a constant; under forward KL it is E_{π_ref} log(π/π_ref), rewarding what π_ref already samples.
- Table 6 (prompts where Qwen2.5-7B fails in 2 samples, KL): Pass@16 OlympiadBench 57.78 → 65.78, AIME 2025 23.23 → 29.48 (GEB-1/π) vs DPO.
- Table 10: restricting the bonus to rejected responses beats applying it to all (e.g. Hellinger 73.40 → 75.48).
- Fig. 3: performance stable only when |κ L_bonus|/|L_DPO| ∈ [1e-6, 1e-2].

### Code/data released?
"Code is available here" (link stripped); RLHFlow-UltraFeedback prompts, URM-LLaMa-3.1-8B oracle, DAPO-MATH-17K (all public).

---

## 4. CodeLutra — "Boosting LLM Code Generation via Preference-Guided Refinement"
TMLR 06/2025 (arXiv 2411.05199v3), UW-Madison + Adobe Research (Tao, Chen, Yu, Mai, Rossi, Li, Mitra).

**Mechanism.** Iterative self-generated preference learning (Alg. 1). Each iteration: sample M=10 responses per training question at T=1.0, execute, split into correct Y^(c) (execution result matches reference) and rejected Y^(r); form K=10 (correct, rejected) pairs per question (sampling with replacement if a set is small); update with a dual loss L = DPO(π_θ; π_t as reference) + λ·SFT on the correct responses (Eq. 3; β=0.1 SQL / 0.5 DS-1000, λ=1.0 / 0.5, LoRA r=8, lr 5e-5, 1 epoch per iteration, 4 iterations). The SFT term exists because plain DPO lowers the log-likelihood of *both* chosen and rejected code (Fig. 2); without it Spider EX collapses to 17.2 (Table 2). Supervision: executable ground truth (or merely executability). Results (Table 1, Llama-3-8B): Spider EX 59.3 → 76.6 (GPT-4 74.4), BIRD 22.3 → 43.1 (GPT-4 46.3), DS-1000 Pass@1 28.2 → 48.6 with only 500 training problems (GPT-4 49.4). Ablations: without negatives the model plateaus at SFT level (Fig. 3a); executability-only labels (no ground truth) still give 22.3 → 30.9 on BIRD and executable fraction 59.8% → 89.7% (Fig. 3c); the preference-trained generator classifies correct vs incorrect Codestral code at 79.6% vs 56.3% for SFT (App. B.1, Table 6); GPT-4-judged preference pairs give 27.8 vs 48.2 with execution pairs (Table 8). Limitation (App. C): "treats all failed code attempts uniformly, without distinguishing between different types or severities of errors."

### Idea cards

**E4.1 — Per-step DPO implicit reward from success/failure trajectory pairs as an L1 step scorer (grey-box)**
- *Mechanism in paper:* Eq. 3 DPO on self-generated (success, failure) pairs with execution as the only label; App. B.1 shows the resulting *generator* becomes a 79.6%-accurate *discriminator* of code quality without any discriminator training.
- *Mapping:* for an open-weight agent policy on a replayable task, collect N runs per task, split by outcome (L1), pair each failed trajectory with a successful one on the same task, and run CodeLutra's DPO+SFT (the SFT term on successes prevents the collapse of success-prefix likelihood). The DPO implicit reward β log π_θ(y|x)/π_ref(y|x) factorises over tokens, hence over agent steps: scanning a failed trajectory step by step, r_t = β Σ_{tokens in s_t} log π_θ/π_ref gives a per-step credit profile from outcome labels alone; the first step with a large negative r_t (or the arg-min) is the attribution candidate, and cumulative r_{≤t} is a monotone proxy for P(fail | prefix). Requires the agent's own log-probs (grey-box, self-collected runs); observations/tool outputs are masked out of the sum so only agent-emitted tokens are scored. Output: when, P(fail|prefix); multi-agent "who" follows from which role emitted the step. Supervision L1.
- *Datasets / baseline:* self-collected runs on ALFWorld/WebShop (evaluate against AgentErrorBench's 200 labelled single-agent logs by running the same open model), τ²-bench / SWE-Bench Pro (TrajErrBench), SymFail and TraceElephant replays; AgentHallu's 443 hallucinated + 250 clean runs if their policy is open. Baseline: OAT (one-class model of successes), proposal 2's MLE hazard fit, prompted LLM judge, and the plain per-token log-prob / entropy of the *untrained* policy (to show the preference training is what makes the signal attributive).
- *Relation:* strengthens proposal 2 — it is an alternative L1 estimator of the step hazard (a learned implicit reward instead of a survival-likelihood fit) and provides the "which hidden signal" answer the brief asks for: the log-ratio between the preference-tuned and the original policy on agent-emitted tokens, aggregated per step. New relative to both proposals in using the agent policy itself as the attributor.
- *Main risk:* DPO's implicit reward is known to be poorly calibrated at the token level and dominated by length/format; success and failure runs on the same task may diverge for benign reasons (different valid plans), so the min-r_t step may mark divergence, not error. Needs a policy that both fails and succeeds on the same task often enough to form pairs.
- *Plausibility 4, Effort M.*

**E4.2 — Iterative DPO+SFT attributor from a few hundred labelled logs**
- *Mechanism in paper:* Alg. 1 loop with K pairs per question from the model's own samples; 500 DS-1000 problems suffice for 28.2 → 48.6; dual loss (Table 2) and negatives (Fig. 3a) are both necessary; execution-based pairs beat GPT-4-judged pairs 48.2 vs 27.8 (Table 8).
- *Mapping:* the attributor samples M attributions per labelled log; those matching the label (exact step / within span / in the vote set) are chosen, the rest rejected; K pairs per log; DPO + λ·SFT on the chosen attributions; 3–4 iterations. This is the DPO counterpart of the existing GRPO attributors, and CodeLutra's data-efficiency result (500 samples) matches the scale of Who&When (184), TraceElephant (220), MP-Bench (289), TrajErrBench (486). Table 8 is a warning against using an LLM judge to label the pairs: use the human label or the replay outcome φ (L1+) as the preference source. Output: when/who/what. Supervision L2 (or L1+ with φ); text-only.
- *Datasets / baseline:* train on any one natural set, evaluate cross-dataset; baseline: SFT on the gold (step, rationale) only, GRPO attributor with distance reward, prompted frontier model.
- *Relation:* new training recipe, independent of both proposals; composes with E3.1 and with E2.1's objective.
- *Main risk:* attribution "correctness" is far noisier than code execution (κ 0.67–0.91, human agreement 40–90%), so a hard chosen/rejected split will inject label noise into every pair; the gain may be bounded by inter-annotator agreement.
- *Plausibility 3, Effort S.*

### Quotable facts
- Table 1: Llama-3-8B Spider EX 59.3 → 76.6 after 3 iterations (GPT-4 74.4, SFT 67.9); DS-1000 Pass@1 28.2 → 48.6 from 500 training problems (GPT-4 49.4, SFT 30.0).
- Table 2: DPO without the SFT term on chosen code: Spider 17.2, DS-1000 12.4 vs 76.6 / 48.6 with it.
- Fig. 3c / §6: with executability as the only label (no ground truth), BIRD EX 22.3 → 30.9 and executable-code fraction 59.8% → 89.7%.
- App. B.1, Table 6: a model trained with the preference loss classifies correct vs incorrect code at 79.6%; the SFT model at 56.3% ("close to random guessing").
- Table 8: pairs labelled by GPT-4 preference → 27.8% on DS-1000; pairs labelled by execution → 48.2%.

### Code/data released?
No code/model link in the text (OpenReview page only); data are public (Spider, BIRD, DS-1000) and exact checkpoints are listed in Table 5.

---

## 5. ModeX — "Evaluator-Free Best-of-N Selection for Open-Ended Generation"
arXiv 2601.02535v2 (Apr 2026), UW-Madison (Hyeong Kyu Choi, Sharon Li).

**Mechanism.** Sample N outputs; build a weighted graph with A_ij = Jaccard(unigrams) + Jaccard(bigrams) + Jaccard(trigrams) (Eq. 1); recursively bipartition with the Fiedler vector of L = D − A (Eq. 2–3), keep the larger side (tie → larger total edge weight), stop when the cut's conductance φ ≥ τ = 0.8 (Eq. 4); return the max-weighted-degree node of the final cluster (Eq. 5). Theory (§5.3): the spectral cut separates modal components (Thm 1, via Cheeger), and weighted degree is a kernel density estimate so the centroid is the within-cluster mode (Thm 2). ModeX-Lite applies one (non-recursive) cut-and-prune every T = 100 generated tokens on the partial outputs, because "non-representative paths tend to diverge early" (Fig. 4: high-quality candidates identifiable from <50% of the generation). No evaluator, no extra inference; O(NL + N²). Results (Table 1, N=16): Qwen2.5-7B HumanEval Pass@1 69.89 → 75.61 (Lite 78.66), Math-500 70.98 → 78.00 (= perplexity-BoN, gold PRM-BoN 82.0), CNN/DM ROUGE-L 20.17 → 21.06 (Lite 21.89); Llama-3.1-8B Math 38.75 → 49.33; LLM-Judge over 16 candidates is *worse* than single-path on code (65.24 vs 69.89 Qwen; 7.32 vs 18.29 CodeLlama); Self-Certainty BoN is worse than single path on code (55.49). n-gram similarity beats SentenceBERT and last-token embedding similarity (Table 3: Math 78.00 vs 70.67 / 71.33). GPT-4 on AIME 2025: 20.42 → 30.00 at N=16 (App. G). Limitation: consensus-on-error when the model's mode is itself wrong.

### Idea cards

**E5.1 — Judge-free consensus over N sampled attributions**
- *Mechanism in paper:* Eq. 1–5, Alg. 1; Table 1 shows evaluator-free mode extraction beats an LLM judge selecting among the same 16 candidates, with the judge sometimes below single-path.
- *Mapping:* sample N = 8–16 attributions (step, agent, category, rationale) per log from any attributor (prompted or trained); build the n-gram similarity graph over the full outputs (rationale included, so it generalises majority vote on the step index to the free-text explanation and category), take the modal cluster's centroid. Also usable to merge outputs of *different* attributors (ensemble without a meta-judge). Output: when/who/what; cluster size and conductance give a confidence score for calibration. Supervision: none at inference; text-only.
- *Datasets / baseline:* every human-labelled set; baselines: single sample, majority vote on step index only, LLM-judge selection over the N candidates, perplexity/self-certainty BoN. Metric: exact step, ±k, agent, category accuracy; plus whether cluster size predicts correctness.
- *Relation:* new, orthogonal to both proposals (inference-time aggregation).
- *Main risk:* ModeX's own limitation applies with force: attributors are *systematically* biased toward the crash step, so the mode will often be the wrong-but-popular t_obs; the method helps only when errors are idiosyncratic. Expect gains on category/agent, smaller on exact step.
- *Plausibility 4, Effort S.*

**E5.2 — Departure-from-consensus curve over N sibling rollouts as a label-free t_err detector**
- *Mechanism in paper:* ModeX-Lite's observation and Fig. 4 — on partial generations, non-representative paths separate from the modal cluster early and can be pruned; Thm 2 — weighted degree ≈ KDE density of a sample among its siblings.
- *Mapping:* for a task with N trajectories from the same policy (replayable envs or datasets with many runs per task), compute for the failed run τ_f and each step t its weighted degree d_t = Σ_j Sim(prefix_t(τ_f), prefix_t(τ_j)) over the siblings' step-aligned prefixes, using Jaccard on *agent-emitted* n-grams only (mask observations). The curve d_t / normalised by the cluster's average degree falls when τ_f leaves the modal behaviour; the first sustained drop is a candidate t_err; the step at which τ_f's nearest sibling cluster contains no successful run is a candidate t_lock. Entirely L0 when siblings' outcomes are unknown (pure density), L1 when they are known (restrict the reference cluster to successes, which makes it a nonparametric cousin of OAT). Output: when, t_lock, P(fail|prefix)-like score.
- *Datasets / baseline:* needs several runs per task: SymFail / TraceElephant (replayable), Failure-as-a-Process (1,184 FAIL + 610 PASS CLI-coding runs with t_err/t_lock/t_obs — the natural test if runs share tasks), AgentHallu (hallucinated vs clean runs), HORIZON (3,782 incl. 1,284 successes), Who&When Pro (same injected task across 15 frameworks). Baseline: OAT (neural-CDE one-class model), proposal 2's L0 change-point mixture, LLM judge.
- *Relation:* strengthens proposal 2 (a cheap, training-free L0/L1 feature for the change-point / hazard model) and reuses the same N rollouts proposal 1 already pays for.
- *Main risk:* agent trajectories legitimately diverge (different valid plans, different tool orderings), so low similarity is not error; lexical Jaccard was tuned on short outputs (≤2k tokens), not 7k–260k-token logs — step-aligned, agent-only windows are essential and alignment across runs of different length is itself a problem.
- *Plausibility 3, Effort M.*

**E5.3 — Consensus step as the counterfactual fix δ for proposal 1**
- *Mechanism in paper:* centroid = within-cluster mode (Eq. 5, Thm 2).
- *Mapping:* proposal 1 needs a repair δ to apply at step k. Among the sibling rollouts that share the prefix up to k−1, take the ModeX centroid of their step-k outputs as δ_k ("replace step k with the consensus action") — a judge-free, model-free δ that is always available in replayable environments, and the natural δ for the fragility curves on successful runs. Output: repair-effect profile φ(τ,k,δ_consensus); supervision L1+.
- *Datasets / baseline:* replayable sets (TraceElephant, SymFail, MemTrace execution graphs; ALFWorld/WebShop/τ²-bench rollouts). Baseline δ's: oracle human-written fix (SearchAuditBench repair rubric), LLM-proposed fix, random sibling's step k.
- *Relation:* strengthens proposal 1 (defines one of its free parameters).
- *Main risk:* if the policy's mode at step k is itself the error (systematic failure), consensus δ reproduces the mistake and φ reads zero — but that is informative: it separates idiosyncratic from systematic failures.
- *Plausibility 3, Effort S.*

### Quotable facts
- Table 1 (Qwen2.5-7B, N=16): HumanEval Pass@1 single 69.89 ± 3.59 → ModeX 75.61 / ModeX-Lite 78.66; Math-500 70.98 → 78.00 (PRM Best-of-16 gold 82.00); LLM Judge (N=16) 65.24 on code — below single path.
- Table 1 (Llama): LLM Judge N=16 on HumanEval 7.32 vs single path 18.29; ModeX 32.32.
- Table 3: n-gram Jaccard similarity 78.00 on Math-500 vs SentenceBERT 70.67 and last-token embedding 71.33.
- Fig. 4 / §3: "high-quality candidates are identifiable based on partial generations, even when less than 50% of the full trajectory has been produced."
- Table 2: latency per sample (CNN/DM, Qwen-7B) single 5.5 s, ModeX-Lite N=16 9.1 s, LLM Judge 10.7 s, Self-Refine 31.7 s.

### Code/data released?
Yes: https://github.com/deeplearning-wisc/ModeX ; benchmarks public (CNN/DM, HumanEval, Math-500).

---

## Cross-cutting note: advantage / variance normalisation for a step-level hazard or value model trained from outcome labels

- **Stratify, don't blend.** HERO's central empirical point (Table 9 vs Table 2) is that a linear mix of a binary outcome and a continuous proxy destabilises training, whereas min–max normalising the proxy *within* each outcome stratum keeps the outcome's ordering intact. For a hazard/value model: let PASS/FAIL define the strata and any graded signal (partial score, test fraction, step-distance, φ) only re-order *inside* a stratum (E1.2).
- **The negative stratum is where the information is** (HERO Fig. 2a). Gradations among failed runs/attributions help more than gradations among successes; natural-failure datasets that release failures only (most of them) are therefore not as crippling for this style of training as for OAT-style one-class modelling of successes.
- **Weight by intra-group variance** (HERO Eq. 4): bounded sigmoid weights in [0.4, 3] keyed to the std of the proxy across a prompt's rollouts. For L1+ hazard fitting, use the rollout-outcome variance p_k(1−p_k) at prefix k.
- **Keep advantages bounded and steps small** (LAD App. B.3, Fig. 6): GRPO group-normalisation keeps |A| ≲ 0.4 and the surrogate bound needs |π_θ/π_old − 1| < δ; LAD's gradient weight f'(ratio·e^{−A/η}) is an advantage-aware trust region that needs no entropy term — relevant if the attributor or surrogate is trained with policy-gradient and collapses onto the symptom step.
- **Guard against likelihood collapse of positives** (CodeLutra Fig. 2 / Table 2): any Bradley–Terry / DPO-style contrast between success and failure prefixes lowers the likelihood of *both*; add an SFT/likelihood term on the success side (λ ≈ 0.5–1.0), otherwise the learned score is a ranking signal with no absolute calibration — fatal for P(fail | prefix).
- **Do not label preference pairs with an LLM judge when a verifier exists** (CodeLutra Table 8: 27.8 vs 48.2; ModeX Table 1: judge-over-16 below single path). Use the outcome or the replay effect.

---

## Batch ranking (top 5 across the batch)

1. **E4.1 Per-step DPO implicit reward from success/failure trajectory pairs (grey-box L1 step scorer)** — turns the agent policy itself into a hazard estimator from outcome labels; direct alternative/complement to proposal 2's survival fit. Plausibility 4, Effort M.
2. **E1.1 Verifier-gated dense reward (HERO) for GRPO-trained attributors** — fixes the all-miss zero-gradient regime that natural failures put RL attributors in; can consume proposal 1's φ as the dense signal. Plausibility 4, Effort M.
3. **E5.1 Judge-free consensus over N sampled attributions (ModeX)** — cheapest win; extends majority vote to (step, agent, category, rationale) and yields a confidence score. Plausibility 4, Effort S.
4. **E5.2 Departure-from-consensus curve over sibling rollouts as L0/L1 t_err detector** — training-free nonparametric cousin of OAT; reuses proposal 1's rollouts. Plausibility 3, Effort M.
5. **E2.1 Distribution-matching attributor (LAD) targeting softmax(φ/η) or annotator vote histograms** — principled objective for proposal 1's surrogate and for set-F1/nDCG-style evaluation. Plausibility 3, Effort M.

(E1.2, E4.2, E5.3 are small, S/M-effort refinements worth bundling with the above; E3.1 (GEB) is the only idea in the batch I would not start.)
