# Literature check: re-rolling a single LLM generation (2026-10-30)

Questions (single-generation setting only):
Q1. How to measure the effectiveness of a re-roll.
T1. Re-roll as f(query, trajectory): should fix wrong trajectories and leave correct ones alone.
T2. Which step to re-roll from: effectiveness vs efficiency (cached prefix, keep good reasoning).

Companion note: `lit_counterfactual_step_repair.md` (repair-effect profile, attribution side).

## Q1 — measurement

| Paper | Metric | Notes |
|---|---|---|
| Confidence v.s. Critique (arXiv 2412.19513) | CL = P(correct after | correct before), CS = P(correct after | wrong before); Acc2 = Acc1·CL + (1−Acc1)·CS; Relative Self-correction Score | probabilities estimated with M samples per question; most models "conservative" (high CL, low CS); prompts/ICL trade CL vs CS; SFT format change (CLT/CST) raises both |
| Probabilistic Inference Scaling Theory (arXiv 2508.16456) | same CL/CS, closed form Acc_t = Upp − α^t(Upp − Acc_0), Upp = CS/(1−CL+CS), α = CL−CS | ceiling of iterated re-rolling independent of Acc_0; oracle verifier (CL=1) → 100%; not tested on multi-step CoT |
| S²R (ACL 2025, arXiv 2502.12853) | ICR / CIR | RL raises ICR and lowers CIR |
| SCoRe (ICLR 2025, arXiv 2409.12917) | Δ(i→c), Δ(c→i) | multi-turn RL with reward shaping bonus |
| Risk-aware ISC (arXiv 2609.35832) | HarmRate, RecoveryRate, net = helpful − harmful flips | 29 models × 3 tasks; Llama-3.1-8B GSM8K +25.5 pts but 19.1% of correct answers overturned |
| REWIND (arXiv 2610.19561) | repairs vs regressions per run (46 vs 21 on MATH500) | answer-level only |
| Expanding LLM Reasoning (arXiv 2610.05584) | restart value Û_k = p̂_k − Y_base, n=4 continuations from step k | Y_base = original chain correct (0/1) |

Consensus: four-cell transition accounting (✓→✓, ✓→✗, ✗→✓, ✗→✗) with per-question probabilities, not a single gold-answer comparison. Single-sample comparison confounds the re-roll with sampling luck.

## T1 — f(query, trajectory): fix-if-wrong, keep-if-right

| Paper | Finding | Gap left |
|---|---|---|
| Confidence v.s. Critique | CL/CS trade-off is explicit; "liberal" (low CL, high CS) vs "conservative" models | no step-level version |
| Try Again, Don't Look Back (arXiv 2607.26117) | code, Qwen2.5-Coder 1.5–7B; blind resampling beats conditioned retry below 7B at 2.5–5.5× fewer tokens; conditioned retries reproduce near-identical programs 33–68% vs 2–14%; placebo (failed program + content-free notice) = feedback, so harm is self-conditioning | only retries after failure; never measures ✓→✗ |
| How Many Tries (arXiv 2604.10508) | HumanEval; self-repair with feedback uses 11–54% fewer tokens than resampling at comparable pass | not equal-compute accuracy |
| Refining Over Resampling (arXiv 2608.05643) | breadth × depth self-critique then majority vote; beats BoN/beam | no equal-compute resampling baseline (pith review); refines whole rollouts, no prefix |
| Risk-aware ISC (arXiv 2609.35832) | gate (features of initial response) beats always-revise in 4 settings, loses in others; "switch" prompts add harmful flips | exploratory selector results |
| Think Again or Think Longer (arXiv 2606.19808) | selective verification cuts harmful flips 2.2% → 1.0% on MATH500 but larger initial budget is the stronger lever (8,192-token solve matches at 28% fewer tokens) | Qwen3-4B only |
| REGAR / Know When to Reflect (Findings EMNLP 2026) | "toxic reflection" (✓→✗) at rates comparable to effective corrections; Reflecting Entropy + Belief Shift controller | abstract only |
| ReVISE (ICML 2025) | learned stop-or-refine policy via self-verification | training-based |
| Internal confidence signals (arXiv 2604.22271) | verbal confidence predicts error detection; an activation signal predicts which errors are correctable | diagnostic |
| Decoding the Critique Mechanism (arXiv 2603.16331) | injected arithmetic error persists in R1 traces yet final answer correct in 55–78% of GSM8K-Error cases, explicit corrections <6%; Qwen3-4B explicit backtracking recovers 42.7% / 81.9% | step-level "wrong" ≠ outcome wrong |
| Huang et al. ICLR 2024 (arXiv 2310.01798); Kamoi et al. TACL 2024 | ✓→✗ more common than ✗→✓ without oracle; prompted self-correction unproven on general tasks | — |

Verdict for T1: the desideratum is exactly CL≈1 on correct traces and high CS on wrong ones; the trade-off is documented and known to be prompt-robust, fine-tuning-movable. What is missing: (a) a step-level / prefix-keeping version of CL and CS (all of the above re-roll the whole answer or condition on the whole answer); (b) the comparison prefix-keep-from-k vs condition-on-whole-trajectory vs blind resample at matched tokens; (c) a harm curve harm(k) over restart positions.

## T2 — which step to re-roll from (effectiveness vs efficiency)

| Paper | Cut/restart rule | Prefix kept? | Effect measured | Cost measured | Position analysis |
|---|---|---|---|---|---|
| Expanding LLM Reasoning (arXiv 2610.05584) | restart at step k, top-m steps by Û_k; learned router restricted to last third; "always-last" baseline | yes | Û_k with n=4 | aggregate generated output: always-last 0.830 acc at 0.774× of 4-sample SC output (one cell); H200 assay 0.912× tokens, 1.108× wall-clock | value concentrated (pooled Gini 0.896, within-chain 0.585); early-position labeling bias from earliest-index tie-break (GR@10 −0.175 → +0.095 with random ties); learned router = always-last (−0.006) |
| REWIND (arXiv 2610.19561) | entropy peak → largest adjacent entropy rise within w=5 → align to delimiter in previous 10 tokens; MH accept with α=4 | yes | accuracy, 3 seeds | 9.26× single-pass tokens (vs 8.84× MCMC) | cut-rule ablation on MATH500 (Qwen2.5-Math-7B): gradient-trace 77.6, random-in-window 75.2, peak 74.2, random delimiter 73.2, global random MCMC 72.6; no position-vs-cost analysis |
| Entropy-Cut MH (NeurIPS 2026) | entropy spikes = decision points | yes | accuracy | mixing time ∝ #decisions not #tokens (stylised proof) | uniform cuts "rewrite local details" |
| Power Sampling (ICLR 2026, arXiv 2510.14901) | random cut | yes | pass@k | — | — |
| Thinking Seeds (arXiv 2601.21476) | RL restart from truncated prefix; length-ratio (deterministic) beats random-among-high-entropy | yes | RL accuracy | 1.44× tokens at ratio 0.5 | "does not select the most useful restart states"; adaptive selection = future work |
| Re² (arXiv 2603.07197) | learn continue vs redo-from-scratch; reward = expected accuracy of fresh start | no | accuracy | not reported | restart is full |
| Self-Backtracking (arXiv 2502.04404) | model emits <backtrack>; inference always rewinds one step (pith) | yes | accuracy | — | b=0→b=1 only +2.9 pts |
| To Backtrack or Not (arXiv 2504.07052) | trained DFS traces | — | vs BoN at equal FLOPs | quadratic attention makes sequential search costlier per token | helps on deep trees (Sudoku), hurts on shallow (CountDown) |
| StepCo (arXiv 2410.12934) | first step with PSV score < threshold; keep prefix; revise that step and all later | yes | accuracy; ✓/✗ transition figure | −77.8% tokens vs Best-of-10 at +2.4 (GPT-4o) | threshold sweep changes iterations; no position sweep |
| HPFA (arXiv 2608.02026) | earliest step whose replacement + resampling succeeds | yes | success | — | earliest rule only |
| CUSUM re-decoding (arXiv 2607.20129) | CUSUM alarm → restore earlier token + KV state → constrained re-decode | yes | +1.67 MATH-500 (CI [+0.47,+2.80]); Omni-MATH −0.07 | +5.1% sampled tokens; ~317k discarded tokens / 1,500 units, so emitted length understates cost | "rollback alone insufficient", continuation policy must change |
| Retro-Search (arXiv 2504.04383) | at thought-switch points, continue current thought instead; keep if value higher with γ=0.9 length discount | yes | value with length penalty | −31.2% length, +7.7% acc after SFT | explicit correctness×length objective, but for data revision |
| RIR (arXiv 2609.18304, agents) | latest checkpoint that removes the failure condition while preserving progress | yes | SR | steps, rollbacks per task | no depth sweep |
| Stage-Replay Divergence (arXiv 2607.28495) | — | — | re-prefill vs live KV: 166/200 suffixes differ in BF16, accuracy ≈ same; FP32 no divergence | — | cached-prefix reuse is a cost claim, not a reproducibility claim |

Verdict for T2: the ingredients exist, the curve does not. 2610.05584 is the nearest (restart value per step, concentration, early-position bias, always-last baseline), but it restricts restarts to the last third, treats cost as an aggregate, and has no effect-vs-cost objective. REWIND has the only cut-rule ablation but no position-cost analysis. Thinking Seeds states adaptive restart selection as future work. No paper formulates "latest k within ε of max effect" or "net gain per regenerated token", and no paper reports harm(k) (✓→✗ as a function of restart position).

## Open gaps (both tensions)

1. Joint curve: effect(k), harm(k), cost(k) = expected regenerated tokens from k, for single-LLM CoT, with the tie rule randomised (early-position bias).
2. Three re-roll operators at matched tokens: blind resample, prefix-keep-from-k, condition-on-whole-trajectory. Anchoring (2607.26117) hits the third; whether prefix-keeping anchors the suffix is unmeasured.
3. Step-level CL/CS: CL(k) on correct traces (does restarting at k keep the answer?), CS(k) on wrong traces.
4. Outcome vs step error: hidden self-correction (2603.16331) means a trajectory with a wrong step is not a wrong trajectory; measure outcome probability, and use Thought Branches' resilience.
5. Continuation policy: CUSUM paper and Repairs-for-Whom both show the policy that continues matters; report it.
6. Cache fidelity: BF16 re-prefill ≠ live cache; report which is used.
