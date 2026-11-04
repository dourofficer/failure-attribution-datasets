# Context brief: failure attribution in LLM agent systems, read as a time-series problem

*Written 2026-10-30 as the shared brief for the time-series literature survey (`notes/lit_timeseries/`). Condensed from `report/` (the 21-dataset survey) and from the OAT paper. Everything here is established; the survey agents should build on it, not re-derive it.*

## 1. The objects

An agent system (single- or multi-agent, stochastic) runs on a task `x` and produces a trajectory
`tau = (s_1, ..., s_T)`, one step per policy decision. A step `s_t = (a_t, u_t, o_t)` records the acting agent `a_t`, its output `u_t` (message, tool call, code) and the resulting observation `o_t` (tool return, page, test log). A verifier gives a trajectory-level outcome `S in {0,1}` (success/failure). `tau_{<k}` is the prefix.

What the datasets label on a *failed* trajectory:

| Label | Definition | Datasets that use it |
|---|---|---|
| decisive step `k*` ("when") | earliest step such that, had it been correct, the run would have succeeded (counterfactual, never tested by re-execution except in TraceElephant) | Who&When, TraceElephant, TrajErrBench, LongRCA, CORRECT-Error, injected sets |
| responsible agent `a*` ("who") | the agent that emitted `k*` (= sender of the labelled step in 99-100% of records) | same |
| error set `E` | several steps with per-annotator votes (3 annotators) | MP-Bench (consensus rate per step), AgentRx (all failure events + one root cause), TRAIL (every error span) |
| lock-in `k_lock` | first step from which the run never recovers (first *unrecovered* failure) | AgentRx, Failure-as-a-Process (`t_lock`) |
| three timestamps | `t_err` (decisive) <= `t_lock` (lock-in) <= `t_obs` (first externally observable symptom; null for silent failures) | Failure-as-a-Process |
| failure mode | a category from a taxonomy (MAST 14 modes; Who&When Pro 17; AgentRx 9; TRAIL 21 leaves; TrajErrBench 20) | MAST-Data, Aegis, Who&When Pro, AgentRx, TRAIL, AgentHallu, TrajErrBench |
| tolerance span | `[k_s, k_e]` of equally defensible adjacent steps | SearchAuditBench |

Human agreement on `k*` is low: exact-step agreement 40% (LongRCA), 78% (AgentHallu), 91%/67% (TrajErrBench tau2/SWE-Pro), Krippendorff alpha 0.64 (TraceElephant); only 16% of MP-Bench flagged steps are flagged by all three annotators. The report therefore defines attribution as estimating a *repair-effect profile* `e_tau(k) = max_delta [p_delta(tau,k) - p_0(tau,k)]` (success-rate change when step k is replaced by an intervention delta and the run is re-rolled N times), with `k*`, `E`, `k_lock`, `a*` as summary statistics of the profile.

**Step-level sparsity.** Errors are sparse in both outcome classes: labelled error steps are 0.6% (LongRCA), 4.5% (Who&When), 10% (AgentRx), 12.5% (TRAIL), 18% (MP-Bench union) of the steps of failed runs; successful Terminal-Bench runs still contain 2.3 recovered error events per 22.8 steps. "Success" is a trajectory property, not a step property.

**Error position priors are strong and dataset-specific.** Relative position of `k*`: Who&When 0.46 (36% of errors at steps 0-2; first-3 hit rate 0.36 on the whole set), TraceElephant 0.47, MP-Bench 0.40, AgentErrorBench 0.23 (median), Failure-as-a-Process `t_err` 0.31, TrajErrBench 0.65, SearchAuditBench 0.58 (final answer is the critical step in 17%), Who&When Pro 0.83 (injected), CORRECT-Error 0.95 (injected: 52% in the last fifth). Any step-scoring method must be compared against position-only baselines.

**Step units differ.** Who&When: every message incl. orchestrator thoughts; TraceElephant: one LLM API call (inputs, outputs, screenshots); TRAIL: OpenTelemetry spans in DFS order (LLM/TOOL/CHAIN/AGENT kinds); MemTrace: operations in a bipartite execution graph; SymFail: nodes of an event-dependency graph; AgentRx: 1-based from the system message; TracerTraj: mixed 0/1-based. Pooling datasets requires explicit normalisation.

## 2. The 21 datasets (what a method could be run on)

Columns: failures natural (N) or injected (I); labels; #failed trajectories; median steps; are *successful* trajectories released (needed for one-class / outcome-supervised training); replayable (state can be restored and re-executed); observation level (A: full LLM I/O + state, B: message stream with tool I/O, C: agent outputs only, D: no step text).

| Dataset | N/I | Labels | #failed | med. steps | successes released? | replay | obs |
|---|---|---|---|---|---|---|---|
| Who&When (ICML'25) | N | agent, step, reason | 184 | 10 (HC subset 32.5) | no | live web, no | C |
| TraceElephant (ACL'26) | N | agent, step (LLM call), reason; full traces, screenshots | 220 | 21 | no (160 withheld) | SWE-Agent subset yes | A |
| MP-Bench (ICML'26) | N | step sets, 3 annotators, consensus rate, 9 categories, ideal action | 289 | 10 (manual 31.5) | no | no | C |
| Who&When Pro (ICML'26) | I | agent, step, mode (17); 26 benchmarks, text/image/video | 12,326 | 4 | no | no (pipeline unreleased) | B |
| LongRCA (arXiv'26) | N | role, earliest root step; 5 domains | 1,140 | 145 (max 728) | no | sandboxes yes, agents no | B |
| AgentRx (EMNLP'26) | N | all failure events + root cause, 9 categories | 73 public of 170 | 33 | no | tau-bench rows yes | B |
| SymFail / SymTrace (arXiv'26) | N | failure node, C1-C4 symptom set; event graphs with per-call LLM I/O; selective-replay framework | 536 | 7 | no | yes (recorded prefix) | A |
| TracerTraj (ICLR'26) | I+N | agent, step; train/test | 3,998 | 10 | no | no | B |
| Aegis (ICLR'26) | I | (agent, mode) pairs, no step; train/val/test; injector + MAS wrappers public | 9,533 | 10 | no | re-run at temp 0 | B |
| CORRECT-Error (ICML'26) | I | agent, step | 2,226 | 10 | no | no | C |
| AgentErrata (arXiv'26) | I | step, 10 modes | 303 | – | not released | – | D |
| MAST-Data (NeurIPS'25) | N | 14 modes per trace (LLM judge; 19 human) | 1,642 traces | 6 | no outcome label | no | C |
| TRAIL (Patronus'25) | N | every error span: category (21), impact, evidence; OpenTelemetry span trees | 148 (not selected by outcome) | 20 spans | mixed | SWE subset | A |
| AgentErrorBench (ICML'26) | N | critical step, module, 17 types; ALFWorld/WebShop/GAIA | 200 | 30 (cap) | no | ALFWorld/WebShop deterministic | B |
| SearchAuditBench (arXiv'26) | N | critical step + tolerance span, 6 root causes, repair directive + rubrics | 1,243 | 20 decisions (43 msgs) | no | no | B |
| Failure as a Process (arXiv'26) | N | `t_err`/`t_lock`/`t_obs`, 9 triggers, tail behaviour; PASS runs annotated too | 1,184 FAIL + 610 PASS | 27 / 16 | yes (annotations only, no step text) | Terminal-Bench yes | D |
| TrajErrBench (EMNLP'26) | N | critical step, 20 types; tau2-bench + SWE-Bench Pro | 486 | 29 / 117 msgs | no | yes | B |
| AgentHallu (arXiv'26) | N | hallucination step, 5/14 categories, reason; 250 clean runs | 443 (+250 clean) | 6 | yes | BFCL subset | B |
| MemTrace (arXiv'26) | N | faulty memory operation, 7 types; execution graphs | 160 | 497 ops in slice | no | yes (MIT code) | A |
| HORIZON (arXiv'26) | N | 7 modes (LLM judge); step on 294 web runs | 2,498 (+1,284 judged success) | 11 | yes (judge) | docker | B |
| MegaRCA-Mix (arXiv'26) | N | (edge, fault side, mode) sets | 50 | 286k tokens | not released | – | D |

Replayable systems where unlabelled runs can be *collected* with outcomes for free (the "data engine"): tau2-Bench (simulated user, seeded DB), ALFWorld/WebShop (deterministic text simulators), SWE-bench/SWE-Bench Pro/Terminal-Bench (containers), MASLab systems with the Aegis injector (no environment state; temperature 0), WebArena/AgentBench-OS/BIRD (docker). Live-web GAIA/AssistantBench/BrowseComp are log-only.

## 3. Supervision levels (from Proposal 2 of the report)

- **L2**: step label `k*` available (every dataset above, test only).
- **L1+**: outcomes of several *continuations of the same prefix* (rollouts, or the failed and absorbed branches of an injection); no human label.
- **L1**: trajectory outcome `S` only (free wherever the task has a verifier).
- **L0**: raw logs, neither `S` nor `k*`.

OAT sits between L1 and L0: it uses `S` to select successes, then ignores it.

## 4. The anchor: OAT (Yeh, Zhu, Deep, Li; NeurIPS 2026; arXiv:2607.12747)

**Setting.** "Unsupervised failure attribution": train only on successful trajectories `D_succ` (103 Qwen3.5-27B runs on MCP-Atlas, a tool-calling benchmark, 7 steps on average), then on a failed trajectory predict the *set* of failure-contributing steps `y(tau') ⊆ {1..T}` ("each step meaningfully degrades the trajectory toward failure, regardless of whether intervening at t alone is sufficient for recovery"; 1.56 labelled steps per failure on average). Test: 88 author-annotated MCP-Atlas failures (in-domain) and Who&When's 184 (OOD).

**Step representation.** `h_t = M^(l)(a_t | Q, a_1, s_1, ..., s_{t-1})`: last-layer hidden states of the generating LLM (or a proxy LLM) while producing action `a_t`, mean-pooled over tokens, PCA to 64 d. `h_Q` = representation of the query. Later layers work better; proxy models (Llama-4-Scout, Gemma-4-31B, GPT-oss-120B) lose little.

**Time axis.** `u(t) = t / T`, i.e. every trajectory is normalised to [0,1] and treated as an *irregularly sampled* observation of a continuous latent path from `h_Q` to `h_T`.

**Model (this is the borrowed part).** Neural CDE of Kidger et al. 2020 (arXiv:2005.08926):
```
X(u)   = natural cubic spline through (h_t, u_t)          control path, not learnable, dim d_h+1 (time channel)
z(0)   = g2(h_Q)                                           initial state from the query
z(u)   = z(0) + ∫_0^u f(v, z(v); θ_f) dX(v)                 Riemann-Stieltjes, = ∫ f(v,z) (dX/dv) dv
h_hat(u) = g1(z(u))                                        linear readout to representation space
loss   = E_{tau ~ D_succ} Σ_t || h_t - h_hat(u_t) ||²      reconstruction of every step of successful runs
```
`f` is a 3-layer MLP (hidden 64), Euler solver. Ablated against a Neural ODE (no control path; worse on all metrics) and an RNN next-step predictor on the same embeddings (CDE slightly better; figure only).

**OAT's additions to the NCDE recipe.** (i) One-class *reconstruction* objective instead of classification. (ii) A **gated control path**: `d X~/du = q(dX/du; θ_q) ⊙ dX/du` with `q: R^{d_h+1} → [0,1]^{d_h+1}` a network that suppresses atypically large or unfamiliar spline derivatives; this is the source of the entire OOD gain (+0.172 AUROC on Who&When, −0.028 in-domain). (iii) **Per-step anomaly score** `e_t = || h'_t − h_hat(u_t) ||²`, decoded by top-k (k = 3) or by a **conformal threshold**: `δ` = (1−α)-quantile of step scores on held-out successful trajectories (α = 0.2), guaranteeing a false-positive rate ≤ α on in-distribution steps.

**Numbers.** In-domain F1 0.42 (top-k) / 0.44 (CP), AUROC 0.63, vs GPT-5 prompting 0.18; Who&When OOD F1 0.23 / 0.21, AUROC 0.76, vs GPT-5 0.15; 200-5000× faster, 0 tokens. OAT reports Random-Step and First-Step baselines, but each picks a single step, so they are not matched to its top-3 decoder. k-matched positional baselines (recomputed on Who&When in `notes/fa_ideas_review.md` and `lit_B_tsad.md`): first-3 hit 0.36, random-3 hit 0.29 vs OAT top-3 0.45; with one gold step and k = 3, F1 = hit/2 with a ceiling of 0.5; position-only AUROC 0.60 ≈ ungated OAT, below gated OAT 0.76.

**Stated limitations / future work (App. A).** Exact likelihood via continuous normalising flows (score = NLL instead of reconstruction error); attention-based control paths; Neural SDEs for stochasticity. App. H: misses early latent reasoning errors ("such statements can appear in successful trajectories"); fires on failure verbalisation and on reactions to empty tool returns (i.e. it is closer to a `t_obs` detector than a `t_err` detector); hard conformal threshold under-detects when several steps are flagged.

**Critique already in the repo (`notes/alternatives.md`, Proposal 2).** Agent steps are discrete, uniformly indexed events: the spline interpolates between a tool call and its observation, which is semantically empty; the cubic spline is non-causal (future steps affect `X(u_t)`), so OAT cannot run as an online monitor; the signal comes from *selection* (training only on successes shifts the reference away from the agent's own policy, under which its mistakes are typical actions) rather than from the differential-equation model; selecting successes already needs outcome labels, after which OAT throws away the failures. The report's Proposal 2 replaces the one-class model with an outcome-supervised **discrete-time hazard model**: `h_t = h_θ(tau_{<t}, s_t)` = probability step t is the first unrecovered error; `P(S=1|tau) = Π_t (1−h_t)`; `P(t*=t | S=0, tau) = h_t Π_{s<t}(1−h_s) / (1 − Π_s(1−h_s))`; fitted by maximum likelihood on all trajectories with outcomes (L1), sharpened by prefix rollouts (L1+); at L0 the same posterior becomes a change point between a shared pre-change dynamics `q_0` and a post-change regime `q_1`.

## 5. The NCDE source (Kidger, Morrill, Foster, Lyons, NeurIPS 2020, arXiv:2005.08926)

`z_t = z_{t0} + ∫_{t0}^t f_θ(z_s) dX_s`, `z_{t0} = ζ_θ(x_0, t_0)`, with `X` the natural cubic spline through `(x_i, t_i)` (time as a channel), solved as the ODE `dz/ds = f_θ(z_s) dX/ds` with any ODE solver; linear readout of `z_{t_n}` (or the whole path); trained by cross-entropy with adjoint backprop; universal approximation via the signature transform; strictly subsumes `dz/ds = h(z, X_s)` models (ODE-RNN, GRU-ODE); benchmarks CharacterTrajectories (30/50/70% observations dropped), PhysioNet sepsis, Speech Commands; stated limitation: natural cubic splines are non-causal, so online/real-time use needs a different interpolation (follow-up: Morrill et al. 2021, "Neural CDEs for online prediction tasks"; Neural Rough DEs for long series; Neural SDEs).

So OAT's lineage is: NCDE (classification of irregular series) → one-class reconstruction of the control path itself, scored per observation, with a gate on `dX/du` and a conformal decoder. The question of this survey is which *other* time-series formulations transfer the same way, and to which benchmark.

## 6. The three research proposals in the report (for mapping)

- **P1 Counterfactual perturbation screens.** Replace step k by an intervention δ (oracle-action, hint, fix-observation, reassign; corrupt-output, corrupt-observation, delete, swap-agent), re-roll N times, measure `φ = p_δ − p_0`. Tasks: T1 a surrogate `f(tau_{<k}, s_k, δ) ≈ p_δ` without executing; T2 attribution = argmax effect; T3 fragility curves `r(k/T)` and the point of no return.
- **P2 Label-free attribution.** The hazard model above at L1/L1+/L0; U1 outcome-supervised hazard, U2 change-point mixture at L0 (which error classes are identifiable from the dominant mode alone?), U3 prefix monitor (cumulative hazard as online lock-in estimate; lead time vs `t_lock`; Failure-as-a-Process's prompted monitor has 82% precision, 18% recall, median lead time 0).
- **P3 Attribution-guided policy improvement.** Use an attribution weight vector `w_tau` to restart rollouts (R), reweight step advantages (C), build preference pairs (D), or update only the culprit agent (M); measure the accuracy-to-value curve.

## 7. What a useful "mapping" looks like

For a time-series method to count as a mapping, the survey file must say: (a) what plays the role of `x_t` (step embedding, step-type token, agent id as a mark, observation features such as tool-return length / exception flag / repeated query, token NLL from a proxy LM), (b) what the method is trained on and at which supervision level (L0/L1/L1+/L2), (c) what it outputs (per-step score, change point, hazard, intensity, effect size, span), (d) which labelled target it is scored against (k*, E, k_lock, t_err/t_lock/t_obs, mode, who) and on which dataset(s) with which metric (exact / ±k step accuracy, nDCG@5 for MP-Bench, set-F1 for AgentRx/TRAIL, lead time for monitors, AUROC/AUPRC per trajectory), (e) which position-prior baseline it must beat, and (f) what breaks (non-causal interpolation, last-step shortcut, task-difficulty confound, recovered errors in successes, multiple causes).
