# Alternatives to the Neural CDE in OAT, and a label-free formulation beyond it

Context: *Tracing Agentic Failure from the Flow of Success* (Yeh, Zhu, Deep, Li; NeurIPS 2026; arXiv:2607.12747) proposes **OAT** (One-class Agent Tracing): embed each step with an LLM (Qwen3.5-27B hidden states, mean-pooled, PCA to 64 d), fit a Neural Controlled Differential Equation to the step sequences of *successful* trajectories only, and score each step of a failed trajectory by its reconstruction error against the learned "flow of success". Error steps are selected by top-k (k = 3) or a conformal threshold (alpha = 0.2). Evaluated on the authors' MCP-Atlas (103 successes for training, 88 author-annotated failures) and on Who&When as an out-of-distribution test.

## Why the Neural CDE is weakly motivated

- Neural CDEs pay off on irregularly sampled or partially observed series. Agent trajectories are discrete, uniformly indexed events; nothing happens between step k and k+1. The cubic-spline interpolation between step embeddings is semantically empty (there is no state halfway between a tool call and its observation).
- The smoothness bias cuts against the task: an error step often appears as an abrupt jump in embedding space, and heterogeneous step types (reasoning, tool arguments, raw tool output) alternate.
- OAT's own ablations (arXiv v1) contain **no per-step density baseline** (no Isolation Forest, OC-SVM or KDE; an earlier version of this note cited "F1 0.411 vs 0.435", which has no source in the paper). The ablations that exist are CDE vs Neural ODE (Fig. 3), gated vs ungated control path (Fig. 4) and CDE vs an RNN next-step predictor (Fig. 5, figure only, small gap). The large OOD gain (+0.172 AUROC, with −0.028 in-domain) comes entirely from the *gated control path*, an input-suppression trick that is independent of the CDE. Positional baselines the paper omits (computed on Who&When): first-3 hit 0.359 and random-3 hit 0.286 vs OAT top-3 0.451; position-only AUROC 0.602 ≈ ungated OAT, below gated OAT 0.758.
- A CDE would be justified if the time axis were token count or wall-clock latency (genuinely irregular spacing). The paper does not do this.

## Simpler alternatives for the "model of success dynamics" slot

Keep OAT's setting fixed: LLM embeddings per step, train on successful trajectories only, score each step of a failed trajectory by its departure from what successes do. Ordered from simplest up.

1. **Per-step density (no dynamics).** Gaussian / GMM / KDE / Isolation Forest on step embeddings of successful runs; score = negative log-density. OAT does not report this baseline; it is the floor our experiment has to add. Weakness: context-free, so a normal-looking action in the wrong place is invisible.
2. **Conditional density: next-step prediction + residual score.** Learn f(e_1..e_{t-1}) -> e_hat_t on successes; score step t by ||e_t - e_hat_t||. Predictor: ridge regression on the last k embeddings, a GRU, or a tiny causal Transformer. This is what the CDE computes with the spline and ODE solver removed. On ~100 trajectories a GRU or linear AR model is the right size. The honest ablation: same gate, same scoring rule, RNN vs CDE.
3. **Discrete state model: HMM / clustered transition matrix.** Cluster step embeddings into K types (plan, search, read, code, answer, ...); estimate transition probabilities from successes; score a step by the surprise of its transition P(type_t | type_{t-1}). Captures the structural failures the taxonomies name (step repetition, loops, premature termination, answer without retrieval; MAST FM-1.3, FM-1.5, FM-3.1). Interpretable, needs almost no data.
4. **Masked embedding reconstruction.** Small bidirectional encoder trained on successful trajectories to reconstruct a masked step from its neighbours; reconstruction error = anomaly score. Uses both sides of the context, which matters because an error often shows in the *following observation*, not in the action.
5. **Trajectory-level density with per-step attribution.** Sequence model giving log p(trajectory) for successes (normalizing flow or small LM over step embeddings); attribute by leave-one-step-out change in log-likelihood. More principled as a model, more expensive to attribute.
6. **Fine-tune a small LM on raw success text.** Skip embeddings; fine-tune a 1-3B model on successful trajectories as text and score each step by its token-level perplexity. Closest to the agent's own generative process. Caveat: the policy's own errors are fluent, so perplexity catches surface errors better than reasoning errors.

**Recommended first experiment:** (2) + (3) together with (1) as the floor. A GRU next-step predictor plus a transition-surprise term covers local deviation and structural failure, trains in seconds, and every component can be ablated. If it matches the CDE within noise on Who&When, the differential-equation machinery was decoration.

Shared limitation: all of these are *anomaly* scores, not causal attributions (OAT's Appendix A concedes the same).

## Why a fully unsupervised variant (model all trajectories, dominant mode = normal) loses the signal

- OAT's signal comes from *selection*, not from the CDE: training on successes shifts the reference distribution away from the agent's own policy. Modelling all trajectories recovers approximately the policy plus the environment, under which the agent's errors are high-probability draws. A hallucinated summary or a premature final answer is a typical action that happened to be wrong (cf. the Who&When example `Hand-Crafted/48.json`: "FINAL ANSWER: 20" after one search looks locally normal).
- Density-based anomaly on actions would catch only surface-visible errors (tool exceptions, loops, empty observations, format failures). Reasoning errors dominate the labels: 58% of TrajErrBench, 59% of Who&When Pro, 70% of TRAIL.
- Curating successes already requires outcome labels. OAT has them and discards the failures. Given the same information, use both classes.

### The step-level contamination argument, quantified from the survey data (failed trajectories only)

| Dataset | Error steps / trajectory | Steps / trajectory | Rate |
|---|---|---|---|
| LongRCA | 1 root | 156 | 0.6% |
| Failure as a Process | 1 decisive, 2.5 events | 41.7 | 2-6% |
| Who&When | 1 decisive | 22.2 | 4.5% |
| AgentRx | 4.6 events | 44.7 | 10% |
| TRAIL | 577 error spans | 4,626 spans | 12.5% |
| MP-Bench (>= 2 votes) | ~4.2 | 23.3 | 18% |

So 80-99% of steps in failed trajectories are correct. Two caveats: successful runs are not clean either (Failure-as-a-Process PASS runs average 2.3 recovered error events in 22.8 steps), and trajectory-level failure rates are high (often 40-60% on GAIA-style tasks), so "dominant mode" holds at the step level but fails at the trajectory level.

## A principled label-free formulation: outcome-supervised step hazard

Use trajectory outcomes (success/fail), which are nearly free (ground truth, unit tests, verifier), and no step labels. Treat failure as absorption at the first unrecovered error; let h_t = hazard that step t is that error given the prefix. Discrete-time survival likelihood:

```
P(success)        = prod_t (1 - h_t)
P(fail)           = sum_t h_t * prod_{s<t} (1 - h_s)
P(t* = t | fail)  = h_t * prod_{s<t} (1 - h_s) / P(fail)     <- attribution
```

Train h_t(prefix, step) by maximising the outcome likelihood over *all* trajectories. The posterior on the last line is the attribution and matches the "earliest decisive step" definition used by Who&When, TrajErrBench, LongRCA and Failure-as-a-Process. Relaxing to "any error step" with a noisy-OR link gives classic multiple-instance learning. Step encoder: OAT's LLM embedding or a small fine-tuned model; hazard head: small MLP or GRU over the prefix. OAT is the degenerate case that uses only the success term.

### Pitfalls and fixes

- **Last-step shortcut.** The final-answer step reveals the outcome, so the hazard piles mass on it (Who&When Pro and CORRECT-Error show how strong this prior is). Mask the last k steps from the hazard input, or evaluate with the final answer stripped.
- **Task-difficulty confound.** Hard tasks produce both failures and unusual steps. Use a matched design (same task, both outcomes): Failure-as-a-Process (89 tasks x 21 systems, PASS + FAIL, annotations only), AgentHallu (443 failed / 250 clean), HORIZON (judge outcomes for both). Most core MAS benchmarks release failures only, so successes must be generated (cheap).
- **Recovered errors in successes.** The survival likelihood only requires that no error was fatal, not that none occurred; a one-class model cannot express this.
- **Identifiability.** Without step labels the hazard can latch onto outcome-correlated, non-causal features. Use a small step-labelled set for model selection and calibration only, never training, and say so.

### Evaluation

Score first on set-labelled datasets (MP-Bench consensus ranking / nDCG, AgentRx failure events, TRAIL spans, Failure-as-a-Process t_err and t_lock), then report exact and windowed step accuracy on Who&When and TrajErrBench for comparability. The model also yields a prefix-only monitor (the online question of Failure-as-a-Process) and a proposal distribution for the counterfactual rollouts in the report's future-work section.
