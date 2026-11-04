# Lit F: attribution over time — which step is responsible for a sequence-level outcome

*Slice F of the time-series survey (`notes/lit_timeseries/`). Written 2026-10-30. The notation (τ, s_t = (a_t, u_t, o_t), S, k*, E, k_lock, t_err/t_lock/t_obs, φ, e_τ(k), L0/L1/L1+/L2, P1/P2/P3) is from `00_context_brief.md`.*

**Verification legend.**
- **VERIFIED-pdf**: I downloaded the arXiv PDF and read the method section. Equations attributed to a VERIFIED-pdf paper are transcribed from its text. Equations marked "my derivation" or "standard form" are not.
- **VERIFIED-abs**: arXiv abstract page only.
- **VERIFIED-search**: bibliographic data (journal, DOI) confirmed only through search results.
- **unverified**: not confirmed. The venue is marked "unverified" whenever neither the PDF nor the abs page states it.

All 50 cited items are listed at the end with their status. Statements of the form "for agents, this becomes ..." are my mapping, not claims made by the cited paper.

**Section numbers used in cross-references:** §1 Scope and verdict, §2 Three notions, §3 Methods (3.1 time-series XAI, 3.2 RL credit assignment, 3.2b multi-agent, 3.3 sequential causal inference, 3.4 agent-side anchors), §4 RUDDER-style L1 attributor, §5 Ranked recommendations, §6 Open gaps, §7 Verification log.

---

## Scope and verdict

1. Three literatures answer "which time step caused a sequence-level outcome": time-series explainability (notion **A**), RL temporal credit assignment (**B**) and sequential causal inference (**C**). Fifty papers were verified.
2. They attribute different quantities. A: how much a *fitted predictor* relies on a step. B: the step's increment of expected return under the agent's *own* policy. C: the outcome change when an *intervention is executed*. Only C is the report's φ(τ,k,δ). B is φ for the single intervention "resample step k from the agent's policy". It is exactly the restart-measured prefix-value drop of Executable Prefix Values (arXiv:2610.17633).
3. Perturbation saliency (Dynamask, TimeSHAP, TSR) re-queries the model and holds the logged later steps fixed. Downstream symptoms then explain the cause away. It coincides with P1's surrogate T1 only when the predictor is prefix-truncated and calibrated and the replacement is a semantic δ (FIT's construction).
4. The most transferable object is RUDDER's "difference of consecutive return predictions" with a *causal* sequence model trained on the outcome S of self-collected runs (L1). It is an online, outcome-supervised replacement for OAT's non-causal one-class spline. It is also the unconstrained version of P2's hazard model, which forbids recovery.
5. Its documented bias is that credit lands where failure becomes *predictable*, i.e. near t_obs rather than t_err. RUDDER's analysis says this, and Synthetic Returns "spike for states that occur after critical actions". Only rollouts (L1+) or explicit dependency structure can move credit back to silent causes. The second option is TVT-style value transport over the SymFail/MemTrace/TRAIL graphs.
6. Sequential treatment-effect models (CRN, Causal Transformer, TE-CDE, G-Net) are the right architecture for P1's surrogate f(prefix,k,δ). TE-CDE is OAT's NCDE encoder plus a decoder driven by the treatment path. Agent logs violate positivity, though, so these models need *randomised* interventions as training data. The Aegis injector (temperature-0 MASLab) supplies corruption interventions. Repair rollouts on τ²-bench, ALFWorld/WebShop and SWE-bench supply the rest.
7. MARL credit (COMA, Shapley Q-value, Shapley counterfactual credits) answers "who". Difference rewards become exact under deterministic replay (Aegis, temperature 0) and are critic-approximated otherwise.
8. Synthetic control, interrupted time series and Granger causality fit instance-level k* poorly: the outcome is a terminal binary and there are no donor series. CAUSE (point process + integrated gradients) does give per-event Granger contributions usable for *mode-level* attribution on TRAIL/SymFail.
9. Recommendation:
   - First, a RUDDER-style L1 attributor with an action/observation split. Train it on τ²-bench and ALFWorld/WebShop runs. Test on TrajErrBench-τ², AgentRx and AgentErrorBench, plus AgentHallu, the only labelled set that ships clean runs.
   - Second, calibrate it against restart-measured prefix values on SWE-bench and τ²-bench.
   - Third, a TE-CDE/Causal-Transformer surrogate trained on randomised interventions.
10. Every method must beat two baselines: the dataset's position prior, and a "first observable symptom" heuristic, which is the baseline that exposes t_obs bias.

---

## Three notions of "the step that caused it"

**Common objects.** τ = (s_1..s_T); τ_{≤t} is the prefix through step t, and h_t is the corresponding environment-replayable history.
- `g(τ_{≤t}) := P(S=1 | τ_{≤t})`: a *fitted* prefix outcome model under the data-generating agent.
- `V(h_t) := P(S=1 | resume agent π from h_t)`: the *rollout-defined* prefix value. Definition 1 of Executable Prefix Values (EPV, 2610.17633), with V(h_0) = p(x) the task pass rate and V(h_T) = S.
- `p_δ(τ,k) := V(h_{k-1} ⊕ δ)`: replace step k by intervention δ and re-roll the rest.
- `p_0(τ,k) := V(h_k)`: keep the logged s_k and re-roll the rest. This is my reading of the brief's p_0.
- φ(τ,k,δ) = p_δ − p_0, and e_τ(k) = max_δ φ (brief §1).

### A. Model-prediction importance (time-series XAI)

`I_A(k) = D( f(τ), f(Π_k τ) )`. Here f is any fitted outcome model, and Π_k replaces step k (or a window around it) by a reference: zero/mean (TimeSHAP), temporal blur or moving average (Dynamask), a learned perturbation (ExtrMask, ContraLSP), a generator sample conditioned on the past (FIT), or a graft from the nearest unlike neighbour (Native Guide). D is a squared error, cross-entropy, KL or Shapley payoff.

FIT's prefix form is the closest to a temporal quantity:

```
I(x_S, t) = KL(p(y|X_{0:t}) || p(y|X_{0:t-1})) − KL(p(y|X_{0:t}) || p(y|X_{0:t-1}, x_{S,t}))
```

Its first term is the predicted-outcome shift between consecutive prefixes, the same quantity RUDDER differences (notion B).

**What differs from φ (the model is re-queried, not the environment).**
1. *Who writes the future.* φ regenerates s_{k+1..T} after δ. Masking keeps the logged s_{k+1..T}, which were caused by s_k. A whole-trajectory masked predictor therefore measures something like a controlled direct effect of s_k on f with all post-treatment variables frozen, not the total effect on S. Downstream symptoms (traceback, failing test, "I could not ...") carry the same information, so they **explain the cause away**. RUDDER names exactly this problem for return prediction.
2. *What is measured.* A predictor's output versus the verifier's S averaged over N re-executions. f inherits its training population (whose agent, which tasks), whereas φ refers to the agent under test.
3. *The replacement.* An "uninformative" baseline (zero, mean, blur) is off-manifold; TimeX++ and ContraLSP were built because of this. P1's δ is a semantic, task-valid step: on-manifold for the task but off-policy for the agent.
4. *Sign and scale.* Saliency is usually unsigned relevance or a KL. φ is a signed probability change, so it can mark recovery steps (φ < 0).
5. *Cost.* Forward passes versus N rollouts per (k, δ).
6. *When they coincide.* Suppose f is **prefix-truncated** (it sees only τ_{≤k}), **calibrated** to V under the test agent, and the replacement is the semantic δ. Then `f(τ_{<k} ⊕ δ) − f(τ_{≤k})` is an estimate of φ(τ,k,δ), and it is precisely P1's T1 surrogate. The remaining gap is (i) misspecification or miscalibration of f and (ii) positivity: f has never seen δ-like steps after τ_{<k}.

### B. Return contribution (RL temporal credit assignment)

The trajectory outcome is decomposed into per-step increments:
- RUDDER: `r_t = g(τ_{≤t}) − g(τ_{≤t-1})`, which telescopes to g(τ_{≤T}) − g(τ_{≤0}) ≈ S − P(S|x).
- Least-squares decomposition (Efroni; RRD; SPA-RL): min E[(S − Σ_t R̂(s_t))²].
- Return-conditional HCA: `c(a|x,Z) = 1 − π(a|x)/h_z(a|x,Z)`.

If g equals V (the model conditions on everything the environment state depends on and is fitted to the agent under test), then r_t = V(h_t) − V(h_{t−1}) = −Δ_t, EPV's value drop. EPV states that in expectation over the environment Δ_t = −A^π(h_{t−1}, a_t), and that Σ_t Δ_t = p(x) − Y.

**Nesting with C.** Take δ = "resample s_k from π(·|h_{k−1})". Then p_δ = V(h_{k−1}), so φ(τ,k,δ_π) = V(h_{k−1}) − V(h_k) = Δ_k: notion B is notion C restricted to the agent's own average action. Splitting each step into action and observation gives

```
V(h_t) − V(h_{t−1}) = [Q(h_{t−1},a_t) − V(h_{t−1})] + [V(h_t) − Q(h_{t−1},a_t)]
                     = advantage of the action ("skill") + observation surprise ("luck")
```

This is the skill/luck split that Counterfactual Credit Assignment formalises.

By Bayes' rule, the same identity HCA states for its state-conditional ratio gives `h_z(a|x,S)/π(a|x) = P(S|x,a)/P(S|x)`. HCA's credit for a failure is then 1 − P(S=0|τ_{<t})/P(S=0|τ_{<t}, a_t): RUDDER on a ratio scale, conditioned on the action only (my derivation).

### C. Interventional effect on the environment (sequential causal inference, P1)

`φ(τ,k,δ) = V(h_{k−1} ⊕ δ) − V(h_k)`. In potential-outcome notation (CRN), E[Y[ā(t, t+τ−1)] | H̄_t] for a planned treatment sequence ā. Identification from logs needs consistency, positivity and sequential ignorability. Executing the intervention by replay removes the need for the last two.

### How the dataset labels and the P2 hazard sit on these notions

| label / object | expressed through V, φ | notion | minimum supervision to estimate |
|---|---|---|---|
| k* (Who&When-style decisive step) | earliest k with p_{δ*}(τ,k) high, δ* = "the correct action"; e_τ(k) with oracle δ | C (oracle δ) | L1+ with an oracle-action δ; otherwise only L2 labels |
| decisive step t* of EPV | argmax_t Δ_t | B | L1+ (restarts); L1 approximation by a learned g |
| k_lock / t_lock / point of no return | EPV: t_pnr = min{t : U_α(h_s) ≤ ε ∀ s ≥ t}, with U_α the upper confidence bound on V | B | L1+; L1 approximation by a hazard or g |
| t_obs | first step whose observation carries an explicit failure signal | detectable by A, and where a learned g drops | L0/L1 |
| error set E | {k : Δ_k > θ} or {k : e_τ(k) > θ}; EPV's "erosion" failures have several drops | B/C | L1+ |
| responsible agent a* | difference / Shapley value of agent a's steps under replacement | C aggregated by agent | L1+ (replay); L1 via a critic |
| P2 hazard posterior P(t*=t \| S=0, τ) | B with two constraints: survival Π_{s≤t}(1−h_s) is non-increasing (no recovery), and the drops are normalised into one change point | B, constrained | L1 |

The hazard/RUDDER contrast matters empirically. Successful runs contain recovered errors (2.3 events per 22.8 steps on Terminal-Bench, per the brief). EPV finds that 30 of 47 resolved SWE-bench failures are "erosion" (no single drop holds ≥ 50% of the loss; median concentration C = 0.39), and only 17 are "cliffs". A single-change-point posterior is misspecified for most failures, while RUDDER-style increments can be negative (recovery) and spread.

### Estimability by supervision level

| notion | L0 | L1 (S only) | L1+ (several continuations of a prefix) | L2 (k*) |
|---|---|---|---|---|
| A: predictor reliance | only through a one-class predictor (OAT is A with a reconstruction "predictor") | any XAI method on an outcome classifier | – | evaluation; a supervised step classifier |
| B: return contribution | no | learned g: RUDDER, RRD, SPA-RL, HCA, implicit PRM. Approximates V under the behaviour policy; limited by what the step content reveals | exact V(h_t) by restarts (EPV) | evaluation |
| C: interventional effect | no | only for δ that vary *randomly* in the data (injection datasets are randomised "treatments"); otherwise unidentified | yes, for every δ in the vocabulary; trains the T1 surrogate | k* is a point estimate of C with oracle δ, never re-executed except in TraceElephant's dynamic setting |

---

## Methods

**Where the counterfactual outcomes come from.** "Fitted model" means the method only needs logs with outcomes plus forward passes. It corresponds to Proposal 1's surrogate T1 or Proposal 2's hazard. "Re-run" means it needs Proposal 1's rollouts.

Replayable sources that can supply counterfactual outcomes (brief §2):
- **τ²-bench**: simulated user and seeded database. Labelled failures come from TrajErrBench (400 τ² trajectories from gpt-5, deepseek-reasoner and qwen3-max) and AgentRx (29 public τ-retail runs).
- **ALFWorld/WebShop**: deterministic simulators. Labelled failures come from AgentErrorBench (100 ALFWorld + 50 WebShop failures from GPT-4o, Llama-3.3-70B and Qwen3-8B).
- **SWE-bench Verified**: containers. Labelled failures come from TraceElephant's SWE-agent subset (44 failures, GPT-4o, temperature 0.3). EPV's restart curves were measured on SWE-bench Verified with two open-weight agents.
- **MASLab via the Aegis injector**: temperature 0. Injections are made into *successful* runs, and the injector and wrappers are public.
- **SymFail**: SymTrace selective replay of a recorded prefix with the suffix run live.

| method family | notion | env re-run needed? | counterfactual outcomes to fit/evaluate it |
|---|---|---|---|
| Dynamask, FIT, WinIT, TSR, TimeSHAP/WindowSHAP, TimeX/TimeX++, ExtrMask/ContraLSP | A | no (fitted outcome model) | none to fit. Executed δ on τ²/ALFWorld/SWE are needed only to *validate* that I_A tracks φ |
| CoMTE, Native Guide | A (counterfactual examples) | no; *executed* variant = P1 oracle-action/swap-agent | the donor is a successful run of the same task: AgentHallu clean runs, Aegis clean baselines, or self-collected τ²/ALFWorld runs |
| RUDDER, RRD/LS-RD, IRCR, Synthetic Returns, Transformer/GRD decompositions, SPA-RL, implicit PRM, LaRe | B | no (fitted g on S) | L1 runs on τ², ALFWorld/WebShop, SWE-bench. EPV restarts (SWE-bench) as the ground-truth V |
| Align-RUDDER | B (success-only profile) | no | successful runs of the same task family (ALFWorld task types, WebShop, τ² procedures) |
| TVT | B + structure | no | dependency edges: SymFail event graphs, MemTrace execution graphs, TRAIL span trees |
| HCA, CCA | B | no (fitted hindsight models) | L1 runs; CCA also needs logged exogenous factors (τ² user-simulator seed and DB, test flakiness) |
| COMA, Shapley Q-value, Shapley counterfactual credits | C, by agent | critic version: no; difference-reward version: yes | Aegis temperature-0 replay (exact); SymFail replay; TraceElephant dynamic setting |
| MSM/R-MSN, g-computation/G-Net, CRN, Causal Transformer, TE-CDE | C | no at test time; needs **randomised δ** to train | Aegis injections (randomised corruption); repair-δ rollouts on τ²/ALFWorld/WebShop/SWE-bench |
| When-to-treat | C (timing policy) | no at test time; needs interventions at varied times | P1 screens with δ at several k; EPV restart curves |
| synthetic control, CausalImpact, ITS | C (single unit) | no | donor runs of the same task with a per-step progress series |
| Granger, Neural Granger, CAUSE | A/B (predictive precedence) | no | L1 event sequences (TRAIL timestamps, SymFail event graphs) |

Each entry below gives the citation, the mechanism and the mapping (a)–(f) from brief §7. In the mappings, (a) is x_t, (b) training/supervision, (c) output, (d) target/dataset/metric, (e) position baseline to beat and (f) what breaks.

Two notation points:
- **"Std. encoder"** = OAT's step representation: mean-pooled last-layer hidden states of a proxy LLM, PCA to 64 dimensions. It is concatenated with categorical marks (agent id, tool name, span kind) and observation flags (empty return, exception/traceback, non-zero exit, repeated call, return length, proxy-LM NLL of the action).
- **"Std. baselines"** = the per-dataset relative-position prior (Who&When first-3 hit 0.36, random-3 0.29, OAT top-3 0.45; median relative position AgentErrorBench 0.23, TrajErrBench 0.65, CORRECT-Error 0.95), plus a last-step baseline and a **first-symptom heuristic**: the first step whose observation carries an explicit failure signal.

### 3.1 Time-series explainability (notion A)

#### Dynamask (Crabbé & van der Schaar, ICML 2021)
- **Citation.** "Explaining Time Series Predictions with Dynamic Masks", arXiv:2106.05303. VERIFIED-pdf. Code: github.com/JonathanCrabbe/Dynamask.
- **Mechanism.** A mask M ∈ [0,1]^{T×d} drives a *dynamic* perturbation operator. The operator is a temporal Gaussian blur π_g with σ(m) = σ_max(1−m), a fade to the moving average µ_{t,i} over a window W (π_m), or a past-only moving average (π_p, for forecasting).
  ```
  M*_a = argmin_M  L_e(M) + λ_a ||vecsort(M) − r_a||² + λ_c Σ_t Σ_i |m_{t+1,i} − m_{t,i}|
  ```
  - L_e is the cross-entropy (or squared error) between f(X) and f(Π_M X).
  - r_a contains (1−a)·d·T zeros followed by a·d·T ones, so a is the "area": the fraction of inputs kept.
  - The extremal mask uses a* = min{a : L_e(M*_a) < ε}.
  - Mask information is I_M(A) = −Σ_{(t,i)∈A} ln(1 − m_{t,i}).
- **Mapping.**
  - (a) Std. encoder, one row per step.
  - (b) f is an outcome classifier P(S|τ) trained at L1. The mask is fitted per failed trajectory with no labels.
  - (c) A per-step saliency Σ_i m_{t,i}. The extremal area a* estimates *how many* steps are needed to explain the failure prediction.
  - (d) k* exact/±1 on TrajErrBench-τ² and AgentErrorBench; nDCG@5 against MP-Bench consensus (OOD); set-F1 against AgentRx failure events. Calibrate a against the dataset's error sparsity (4.5% Who&When, 10% AgentRx, 18% MP-Bench union).
  - (e) Std. baselines.
  - (f) Several things break.
    - With a whole-trajectory f, masking s_k leaves its consequences in place, so the explaining-away problem applies (§2.A).
    - Blurring towards neighbouring steps averages two unrelated tool calls, which is meaningless for discrete steps. Only π_p-like "replace by a prefix-conditioned sample" or a Native-Guide graft is sensible.
    - λ_c assumes the culprit is a contiguous window. That suits SearchAuditBench tolerance spans, not multi-cause errors.
- **Supervision.** L1 (to fit f). **Re-run:** no.

#### FIT — Feature Importance in Time (Tonekaboni et al., NeurIPS 2020)
- **Citation.** Tonekaboni, Joshi, Campbell, Duvenaud, Goldenberg, "What went wrong and when? Instance-wise feature importance for time-series black-box models", arXiv:2003.02821. VERIFIED-pdf, NeurIPS 2020 per the PDF header. Code: github.com/sanatonek/time_series_explainability.
- **Mechanism.** The score is the equation in §2.A. Term T1 is the temporal shift in the predictive distribution. Term T2 is the residual shift when only the subset S of the new observation is revealed. The unobserved complement is sampled from a recurrent latent-variable generator of p(x_t|X_{0:t−1}) and averaged by Monte Carlo. The black box must output p(y|X_{0:t}) at every t. Evaluated on MIMIC-III mortality and intervention prediction.
- **Mapping.**
  - (a) Step fields as feature groups: action text, arguments, observation, flags.
  - (b) A prefix predictor g at L1. The generator is trained on unlabelled logs (L0). For text steps the natural generator is an LLM sampling the next step from the prefix, which is π-resampling. FIT with an LLM generator is therefore a *model-imagined* version of notion B.
  - (c) A per-step, per-field score.
  - (d) k* on TrajErrBench-τ²/AgentErrorBench. The field-level scores can be checked against AgentErrorBench's critical-failure *module* (planning/reflection/memory/action/system) and TRAIL span categories.
  - (e) Std. baselines plus OAT.
  - (f) T1 is large where the prediction moves. With a causal g that is the step where failure becomes visible: a t_obs detector unless the error's content is itself predictive. The KL is unsigned.
- **Supervision.** L1. **Re-run:** no.

#### WinIT (Leung et al., ICLR 2023)
- **Citation.** Leung, Rooke, Smith, Zuberi, Volkovs, "Temporal Dependencies in Feature Importance for Time Series Prediction", arXiv:2107.14317. VERIFIED-pdf. Code: github.com/layer6ai-labs/WinIT.
- **Mechanism.** WinIT measures the importance of feature set S at time a on the prediction at a later time b:
  ```
  I(S,a,b) = i(S)^b_a − i(S)^b_{a+1}   (a < b < a+N),     I(S,a,a) = i(S)^a_a
  i(S)^b_a = D( p(y_b|X_{1:b}), p(y_b|X̃^S_{a:b}) )         D ∈ {L1, KL, JS}
  ```
  Here X̃ removes S on [a,b]. Scores are aggregated over a window of N future predictions. The difference over intervals isolates the contribution of time a when later observations of the same feature are correlated with it.
- **Mapping.** This is the only XAI method here that credits an observation for *delayed* changes in the prediction, which is the t_err → t_obs structure.
  - (a) Std. encoder.
  - (b) A causal g at L1.
  - (c) A per-step score aggregated over a window.
  - (d) k* on TrajErrBench/AgentErrorBench, and k_lock on AgentRx. Set N from the observed lag: Failure-as-a-Process medians are t_err 7, t_lock 12, t_obs 16, and 28% of failures are silent.
  - (e) Std. baselines plus the first-symptom heuristic.
  - (f) Removing a step from a dialogue is not a clean "unknown". The window must exceed the lag, and the cost is linear in N. It is still model-only, so it cannot recover silent errors that no later prediction reacts to.
- **Supervision.** L1. **Re-run:** no.

#### TSR and the Ismail et al. benchmark critique (NeurIPS 2020)
- **Citation.** Ismail, Gunady, Corrada Bravo, Feizi, "Benchmarking Deep Learning Interpretability in Time Series Predictions", arXiv:2010.13924. VERIFIED-pdf. Code: github.com/ayaabdelsalam91/TS-Interpretability-Benchmark.
- **Findings.** Saliency methods on RNNs, TCNs and Transformers generally fail to identify feature importance over time. If one feature at time t is salient, almost all features at t become salient ("conflation of time and feature domains"). Architecture strongly affects map quality. Evaluation used synthetic data with *planted* informative features, scored by precision/recall of saliency.
- **TSR.** First a time-relevance score Δ_t^time = Σ|R(X) − R(X with X_{:,t}=0)|. For steps with Δ_t^time > α, a feature-relevance score per feature. The final score is the product.
- **Mapping.**
  - The benchmark's design maps onto the injected-error datasets (Who&When Pro, CORRECT-Error, Aegis, TracerTraj), which are "planted saliency" benchmarks for agents. Their injection-position priors (0.83 and 0.95 relative position) let position baselines win, so a fair agent analogue needs uniformly randomised injection positions (§6).
  - TSR's two stages map to (1) which step and (2) which field or module inside it. Score stage 2 against AgentErrorBench modules and TRAIL categories.
  - (f) The conflation finding predicts that attribution on fused step embeddings will not separate a step's action from its observation. Index action and observation as separate time points, as TRAIL's span trees already do.
- **Supervision.** L1 (any saliency on g). **Re-run:** no.

#### TimeSHAP (Bento et al., KDD 2021) and WindowSHAP
- **Citation.** Bento, Saleiro, Cruz, Figueiredo, Bizarro, "TimeSHAP: Explaining Recurrent Models through Sequence Perturbations", arXiv:2012.00073. VERIFIED-pdf. Code: github.com/feedzai/timeshap (VERIFIED-search).
- **Mechanism.** KernelSHAP over the event axis, with the perturbation h^e_X(z) = X·D_z + B(I − D_z). B is the matrix of training-set mean features and z ∈ {0,1}^l toggles events. Efficiency gives Σ_k φ_k = f(X) − f(h_X(0)).
  - *Temporal coalition pruning* lumps the oldest events whose joint Shapley value is below η, reducing cost from O(2^l) to O(2^{l−i}).
  - Reported on a fraud RNN: positive sequences can be pruned to 10% of their length, and the most recent event contributes on average 41% of the score.
- **WindowSHAP.** Nayebi, Tipirneni, Reddy, Foreman, Subbian, arXiv:2211.06507, VERIFIED-pdf (abstract). Shapley values over time *windows* (stationary, sliding, dynamic). On 120-step clinical series, merging 10 adjacent points cut CPU time by 80% compared with KernelSHAP.
- **Mapping.**
  - (a) Steps as events.
  - (b) An outcome classifier at L1.
  - (c) Signed per-step Shapley values summing to the predicted failure logit minus a baseline. This is notion A with B's efficiency property. Summing over an agent's steps gives an agent score for a*.
  - (d) Who&When/TraceElephant agent- and step-level accuracy (OOD); TrajErrBench; MP-Bench nDCG@5.
  - (e) Std. baselines.
  - (f) The mean-embedding "baseline step" is off-manifold. Recurrent predictors concentrate credit on recent events, which produces a last-step shortcut. Coalition pruning assumes old events are unimportant, the opposite of Who&When, where 36% of decisive errors fall in steps 0–2.
- **Supervision.** L1. **Re-run:** no (an executed Shapley version is Causal Agent Replay, §3.4).

#### TimeX (NeurIPS 2023) and TimeX++ (ICML 2024)
- **Citations.**
  - Queen, Hartvigsen, Koker, He, Tsiligkaridis, Zitnik, "Encoding Time-Series Explanations through Self-Supervised Model Behavior Consistency", arXiv:2306.02109. VERIFIED-pdf. Code: github.com/mims-harvard/TimeX.
  - Liu, Wang, Shi, Zheng, Chen, Song, Dong, Obeysekera, Shirani, Luo, "TimeX++: Learning Time-Series Explanations with Information Bottleneck", arXiv:2405.09308. VERIFIED-pdf. Code: github.com/zichuan-liu/TimeXplusplus.
- **Mechanism.**
  - TimeX trains an interpretable surrogate (mask generator plus explanation encoder) to mimic a pretrained model. Model-behaviour consistency is L_MBC = (1/N²) Σ_{i,j} (D_Z(z_i,z_j) − D_{Z_E}(z^E_i,z^E_j))², with cosine distances. Label consistency is a Jensen–Shannon divergence between logits. "Landmarks" in the explanation latent space summarise recurring explanation patterns.
  - TimeX++ shows that information-bottleneck explanation objectives admit trivial and out-of-distribution solutions. It replaces the terms with label consistency and a modified compactness term, and generates explanation-embedded instances that are in-distribution and label-preserving.
- **Mapping.** These are *amortised* explainers: train once, then explain every failed run in one pass, with OAT-like speed.
  - (a) Std. encoder.
  - (b) An outcome classifier at L1.
  - (c) A per-step mask plus an explanation embedding. Landmarks are candidate *failure modes*, so the method attributes step and mode jointly.
  - (d) Step against k*. Cluster landmarks against MAST, AgentRx or TRAIL categories (adjusted mutual information).
  - (e) Std. baselines.
  - (f) Quality is bounded by f. It needs thousands of trajectories, and only the replayable environments can produce that many with outcomes.
- **Supervision.** L1. **Re-run:** no.

#### Learned perturbations: ExtrMask (ICML 2023) and ContraLSP (ICLR 2024)
- **Citations.**
  - Enguehard, "Learning Perturbations to Explain Time Series Predictions", arXiv:2305.18840. VERIFIED-pdf. Code: github.com/josephenguehard/time_interpret.
  - Liu, Zhang, Wang et al., "Explaining Time Series via Contrastive and Locally Sparse Perturbations", arXiv:2401.08552. VERIFIED-pdf (abstract). Code: github.com/zichuan-liu/ContraLSP.
- **Mechanism.**
  - ExtrMask learns the perturbation together with the mask: Φ(x,m) = m·x + (1−m)·NN(x), with NN a bidirectional GRU. The loss is λ1||m||_1 + λ2||NN(x)||_1 + L(f(x), f(Φ(x,m))).
  - ContraLSP builds "uninformative" perturbations from counterfactual samples kept in-distribution by contrastive learning. Sample-specific sparse gates give binary, smooth masks.
- **Mapping.** The learned replacement NN(x) is the model-space analogue of P1's δ vocabulary.
  - For agent steps, replace NN(x) by an LLM proposing an in-distribution alternative step, and ContraLSP's counterfactual sample by the aligned step of a successful run.
  - (b) L1. (c) Per-step mask. (d)/(e) As for Dynamask.
  - (f) "Uninformative" is ill-defined for a tool call. ExtrMask's bidirectional GRU reads the future, so it is non-causal, the same objection as OAT's spline.
- **Supervision.** L1. **Re-run:** no.

#### CoMTE (Ates et al., ICAPAI 2021)
- **Citation.** Ates, Aksar, Leung, Coskun, "Counterfactual Explanations for Machine Learning on Multivariate Time Series Data", arXiv:2008.10781, DOI 10.1109/ICAPAI49758.2021.9462056. VERIFIED-pdf and abs.
- **Mechanism.** Pick a *distractor*: a training sample of the target class. Substitute entire channels (whole metric series) from the distractor into the query, minimising the number of substitutions needed to flip the prediction. Greedy and optimisation-based search.
- **Mapping.** Channels are agents, not times.
  - The question becomes: "which agent's message stream, swapped for the corresponding stream from a successful run of the same task, flips predicted success?" This is the model-space version of P1's *swap-agent* δ and a who-attribution.
  - (a) Per-agent sub-sequences. (b) L1 outcome classifier. (c) A minimal set of agents. (d) a* on Aegis (agent, mode) labels and Who&When agent-level (OOD). (e) A "most-active agent" baseline.
  - (f) Needs aligned runs with the same roster on the same task. Aegis ships clean, successful temperature-0 baselines, the ideal distractors. Swapping one agent's stream breaks conversational coherence. Executed on MASLab, it becomes an exact difference reward.
- **Supervision.** L1. **Re-run:** no (an executed variant is possible on Aegis/MASLab).

#### Native Guide (Delaney, Greene, Keane, ICCBR 2021)
- **Citation.** "Instance-based Counterfactual Explanations for Time Series Classification", arXiv:2009.13211 (VERIFIED-pdf), DOI 10.1007/978-3-030-86957-1_3 (VERIFIED-search). Code: github.com/e-delaney/Instance-Based_CFE_TSC.
- **Mechanism.**
  1. Retrieve the query's *nearest unlike neighbour* (NUN) from the case base.
  2. Use class-activation-map weights to locate the most discriminative contiguous subsequence.
  3. Copy that subsequence from the NUN into the query, enlarging it until the predicted class flips.
- **Mapping.** This is the closest model-space analogue of the **oracle-action** δ.
  - Let NUN = the nearest successful run of the same task (or task family). Graft its aligned step(s) into the failed run at position k. The *earliest* k whose graft flips g estimates k* in the brief's sense: "had it been correct, the run would have succeeded".
  - Executed on τ²/ALFWorld/WebShop, the graft becomes a real oracle-action δ drawn from successes rather than from a human. That is a cheap way to obtain P1's oracle intervention.
  - (a) Std. encoder. (b) L1 (needs successes of the same task). (c) Earliest flipping position.
  - (d) k* exact/±1 on AgentErrorBench (ALFWorld has six task types and many runs per type) and TrajErrBench-τ².
  - (e) Std. baselines.
  - (f) Steps must be aligned across runs (use Align-RUDDER's alignment). Grafted steps can be inconsistent with the failed prefix: they reference objects or IDs that do not exist.
- **Supervision.** L1 (model) or L1+ (executed). **Re-run:** optional.

### 3.2 Temporal credit assignment in RL (notion B)

Background survey: Pignatelli, Ferret, van Hasselt, Geist, Mesnard, Pietquin, Toni, "A Survey of Temporal Credit Assignment in Deep Reinforcement Learning", TMLR 04/2024, arXiv:2312.01072 (VERIFIED-pdf, header only).

None of the RL methods below was ever evaluated against a *human* step label. They are judged by policy-learning speed. Their attribution quality on agent traces is therefore untested.

#### RUDDER (Arjona-Medina et al., NeurIPS 2019)
- **Citation.** Arjona-Medina, Gillhofer, Widrich, Unterthiner, Brandstetter, Hochreiter, "RUDDER: Return Decomposition for Delayed Rewards", arXiv:1806.07857. VERIFIED-pdf; NeurIPS 2019 proceedings VERIFIED-search. Code: github.com/ml-jku/rudder.
- **Mechanism.** An LSTM g predicts the *sequence-wide* return at every time step. The redistributed reward is the "difference of return predictions" (contribution-analysis method A):
  ```
  h_0 = g(Δ_{0:0}),   h_t = g(Δ_{0:t}) − g(Δ_{0:t−1})
  ```
  - Integrated gradients and LRP are alternatives (methods B and C). The authors prefer A because B and C "rely on information later in the sequence" and give non-Markov, high-variance rewards.
  - The inputs Δ(s_{t−1},a_{t−1},s_t,a_t) are state-action *differences*. They avoid the "explaining away" problem, in which later states that store reward-relevant information take the credit from the causing action.
  - Late predictions are up-weighted because the "future is less random".
  - A lessons buffer prioritises episodes with large prediction error.
  - An optimal redistribution makes the expected future reward zero. The authors argue the LSTM gives fewer spurious contributions than a feed-forward Q-network because it "will only learn to store information if a state-action pair has a strong evidence for a change in the expected return".
- **Mapping.** See §4. (a) Std. encoder plus Δ features. (b) L1. (c) A signed per-step increment. (d) k*, k_lock, E. (e) Std. baselines, first-symptom heuristic, OAT. (f) The t_obs bias (§4.6).
- **Re-run:** no.

#### Align-RUDDER (Patil et al., ICML 2022)
- **Citation.** Patil, Hofmarcher, Dinu, Dorfer, Blies, Brandstetter, Arjona-Medina, Hochreiter, "Align-RUDDER: Learning From Few Demonstrations by Reward Redistribution", arXiv:2009.14108. VERIFIED-pdf. Code: github.com/ml-jku/align-rudder.
- **Mechanism.**
  1. Events are clusters of *state differences* (affinity propagation).
  2. Define an alignment scoring scheme.
  3. Run a multiple sequence alignment (MSA) of a few high-return demonstrations.
  4. Build a profile model / position-specific scoring matrix (PSSM).
  5. Align each prefix of a new episode to the profile: R_{t+1} ∝ S(τ_t) − S(τ_{t−1}). High-scoring alignment columns are sub-tasks.
- **Mapping.** Success-only supervision, OAT's regime, but discrete and causal.
  - (a) Events = clustered (tool, argument pattern, observation flag) tuples.
  - (b) Successful runs of one task family.
  - (c) Per-step alignment-score increments. The first step after which the failed run stops gaining score, or is aligned to a gap, is the *deviation point*.
  - (d) AgentErrorBench ALFWorld (six task types, small action vocabulary), WebShop, and τ² (procedures fixed by the domain policy). Metric: k* exact/±1.
  - (e) OAT (same supervision); AgentErrorBench's early prior (median relative position 0.23).
  - (f) Multiple valid plans or reorderings break the MSA. Recoverable detours are flagged as deviations.
- **Re-run:** no.

#### Least-squares return decomposition and RRD (Efroni et al., AAAI 2021; Ren et al., ICLR 2022)
- **Citations.**
  - Efroni, Merlis, Mannor, "Reinforcement Learning with Trajectory Feedback", arXiv:2008.06036. VERIFIED-pdf (header; AAAI 2021 per the copyright line).
  - Ren, Guo, Zhou, Peng, "Learning Long-Term Reward Redistribution via Randomized Return Decomposition", arXiv:2111.13485. VERIFIED-pdf.
- **Mechanism.**
  ```
  L_RD(θ) = E_τ[(R_ep(τ) − Σ_t R̂_θ(s_t,a_t))²]
  L_Rand-RD(θ) = E_τ E_{I∼ρ_T}[(R_ep(τ) − (T/|I|) Σ_{t∈I} R̂_θ(s_t,a_t))²]
  ```
  Theorem 1: L_Rand-RD = L_RD + a variance term. RRD therefore interpolates between return decomposition and uniform redistribution, controlled by the subsequence size.
- **Mapping.**
  - (a) Std. encoder with a contextual R̂ (SPA-RL uses the LLM's prefix-conditioned hidden state).
  - (b) L1. For binary S use a logit link: S ~ Bernoulli(σ(b_x + Σ_t c_t)), with a per-task offset b_x.
  - (c) Additive per-step contributions; the most negative is the blame.
  - (d) As RUDDER. Random subsequences make it tractable on LongRCA (median 145 steps, maximum 728).
  - (e) Std. baselines.
  - (f) A Markovian R̂(s_t,a_t) cannot express "harmful only given earlier context". Subsequence sampling adds variance on short traces (Who&When median 10 steps).
- **Re-run:** no.

#### IRCR (Gangwani et al., NeurIPS 2020)
- **Citation.** Gangwani, Zhou, Peng, "Learning Guidance Rewards with Trajectory-space Smoothing", arXiv:2010.12718. VERIFIED-pdf. The method is named "Iterative Relative Credit Refinement".
- **Mechanism.** The guidance reward r_g(s,a) = E_{τ∼p_β(τ;s,a)}[R(τ)] is the expected (normalised) return of stored trajectories that contain (s,a). It is a uniform, "non-committal" redistribution estimated by Monte Carlo over a buffer.
- **Mapping.** A zero-training L1 **frequency baseline**: score each step by the failure rate of trajectories (same task family) that contain an equivalent step, hashed or clustered by tool, arguments and observation flag. This is the spectrum idea from software fault localisation.
  - (d) k*, E. (e) Every learned decomposer must beat it.
  - (f) It needs exact or clustered state matches (the same coverage problem as GiGPO's anchor states) and is confounded with task difficulty.
- **Re-run:** no.

#### Transformer decomposition (Liu et al. 2019) and Generative Return Decomposition (Zhang et al., NeurIPS 2023)
- **Citations.**
  - Liu, Luo, Zhong, Chen, Liu, Peng, "Sequence Modeling of Temporal Credit Assignment for Episodic Reinforcement Learning", arXiv:1905.13420 (preprint, "under review" in the PDF). VERIFIED-pdf.
  - Zhang, Du, Huang, Wang, Wang, Fang, Pechenizkiy, "Interpretable Reward Redistribution in Reinforcement Learning: A Causal Approach", arXiv:2305.18427. VERIFIED-pdf (abstract and header). Project page: reedzyd.github.io/GenerativeReturnDecomposition.
- **Mechanism.**
  - Liu et al.: h_t = Transformer(v_0..v_t) (causal); importance z = sigmoid(w_{s2} tanh(W_{s1} H^⊤)); r̂ = w_r^⊤(z_t h_t) + b_r. Interval rewards are summed to match the episodic return.
  - GRD: a causal generative model with categorical masks over state and action dimensions generates Markovian rewards, which sum to the return. The paper proves the rewards and causal structure identifiable.
- **Mapping.** z_t is an outcome-supervised per-step importance, OAT's score with labels. GRD's masks say *which fields* of a step drive the reward, which maps to module- or field-level attribution (AgentErrorBench modules).
  - (b) L1. (d)/(e) As RUDDER.
  - (f) Attention weights are not attributions (the Dynamask paper discusses RETAIN and Jain & Wallace). GRD's identifiability assumes Markov rewards and causal sufficiency.
- **Re-run:** no.

#### Synthetic Returns (Raposo et al. 2021)
- **Citation.** Raposo, Ritter, Santoro, Wayne, Weber, Botvinick, van Hasselt, Song, "Synthetic Returns for Long-Term Credit Assignment", arXiv:2102.12425 (preprint). VERIFIED-pdf.
- **Mechanism.** State-associative learning:
  ```
  L = (r_t − g(s_t) Σ_{k<t} c(s_k) − b(s_t))²,     r̃_t = α c(s_t) + β r_t
  ```
  c(s_k) is the reward that being in s_k contributes to *any* future reward. It does not take the future state as input, so it can be queried online. The authors report that synthetic returns "spike for states that occur after critical actions are taken", and that the agent solves Atari Skiing 25× faster than the previous state of the art.
- **Mapping.**
  - (a) Std. encoder per half-step (action, observation).
  - (b) L1, with r_T = S and all other r_t = 0.
  - (c) c(s_k), an online per-step contribution.
  - (d) k* at ±1 tolerance.
  - (f) The reported "spike after the critical action" is a one-step instance of the t_obs bias. In agent traces, o_k after a wrong a_k carries the evidence, so credit must be shifted from o_k back to a_k. Treating (a_k, o_k) as one step hides the problem; splitting them exposes it.
- **Re-run:** no.

#### Temporal Value Transport (Hung et al., Nature Communications 2019)
- **Citation.** Hung, Lillicrap, Abramson, Wu, Mirza, Carnevale, Ahuja, Wayne, "Optimizing agent behavior over long time scales by transporting value", Nat. Commun. 10:5223 (2019), DOI 10.1038/s41467-019-13073-w (VERIFIED-search); arXiv:1810.06721 (VERIFIED-pdf).
- **Mechanism.** In a memory-augmented agent, when a read at time t' has read strength β above a threshold, a "splice" occurs. The value prediction after the read is transported as a fictitious reward to the time t whose memory was read:
  ```
  r_t ← r_t + α · w_{t'}[t] · V̂_{t'+1}
  ```
  The distractor interval between them is effectively spliced out of credit assignment.
- **Mapping.** In agent traces, "memory reads" are explicit data dependencies: a later step consumes an earlier tool result, file, variable or message.
  - SymFail event-dependency graphs, MemTrace execution graphs and TRAIL parent/child spans provide these edges.
  - **Blame transport** (my construction): take the drop in predicted success at the symptom step and propagate it backwards along dependency edges, weighted by the dependency, to the producing step.
  - (b) L1 (the drop) plus L0 (the graph). (c) Per-step transported blame.
  - (d) MemTrace's faulty memory operation, SymFail's failure node, k* versus t_obs.
  - (e) The first-symptom heuristic and "parent of the first symptom".
  - (f) Only explicit data flow is covered. Reasoning errors (a wrong plan) propagate through the context window, not through edges. Attention weights of the acting LLM could serve as soft reads but are not faithful.
- **Re-run:** no.

#### Hindsight Credit Assignment (Harutyunyan et al., NeurIPS 2019)
- **Citation.** Harutyunyan, Dabney, Mesnard, Heess, Azar, Piot, van Hasselt, Singh, Wayne, Precup, Munos, "Hindsight Credit Assignment", arXiv:1912.02503. VERIFIED-pdf.
- **Mechanism.**
  ```
  Q^π(x,a) = r(x,a) + E[Σ_{k≥1} γ^k (h_k(a|x,X_k)/π(a|x)) R_k],   h_k(a|x,y)/π(a|x) = P(X_k=y|x,a)/P(X_k=y|x)
  A^π(x,a) = E[(1 − π(a|x)/h_z(a|x,Z(τ))) Z(τ)]
  ```
  The factor c(a|x,Z) = 1 − π(a|x)/h_z "expresses how much a single action a contributed to obtaining a return Z". It is 0 if other actions would have given the same return.
- **Mapping.** For failure attribution, Z = S = 0. Two estimators:
  1. *Discriminative*: with a prefix predictor, c_t = 1 − P(S=0|τ_{<t})/P(S=0|τ_{<t},a_t) (§2.B). This is RUDDER on a ratio scale that isolates the action from the subsequent observation.
  2. *Generative*: the hindsight distribution h_z(a_t|ctx, S=0) is approximated by a proxy LLM's log-likelihood of a_t under a prompt stating that the run failed, contrasted with the plain likelihood π(a_t|ctx).
  - (a) Action text plus proxy-LM log-probs.
  - (b) L1. The generative variant needs no training, so it is effectively L0 plus the knowledge that the run failed.
  - (c) Per-step c_t.
  - (d) k* on AgentHallu (hallucinated step), AgentErrorBench and Who&When.
  - (e) Std. baselines.
  - (f) Sequence log-likelihoods are dominated by length and format tokens, so per-token normalisation is needed. For temperature-0 agents π(a_t|ctx) ≈ 1, so ratio credit degenerates. Calibration of P(S=0|·) near 1 on hard tasks is poor.
- **Re-run:** no.

#### Counterfactual Credit Assignment (Mesnard et al., ICML 2021)
- **Citation.** Mesnard, Weber, Viola, Thakoor, Saade, Harutyunyan, Dabney, Stepleton, Heess, Guez, Moulines, Hutter, Buesing, Munos, "Counterfactual Credit Assignment in Model-Free Reinforcement Learning", arXiv:2011.09464. VERIFIED-pdf.
- **Mechanism.** Future-conditional baselines V(X_t, Φ_t) use a hindsight statistic Φ_t *constrained to be independent of A_t given X_t*:
  ```
  ∇_θ E[G] = E[Σ_t γ^t S_t (G_t − V(X_t, Φ_t))]
  ```
  This is unbiased with no higher variance than the forward baseline. It separates "skill" from "luck". Φ can include exogenous factors, other agents' simultaneous actions, or simulator state.
- **Mapping.** In agent tasks, exogenous randomness includes the simulated user's choices (τ²-bench), web-page variability, flaky tests and other agents' messages. Condition the baseline on these, and the residual credited to the agent's step is its skill component.
  - This targets the task-difficulty and environment confound directly. AgentRx's τ-retail root causes name the *User* as the failed agent in 8 of 29 runs (repo notes), which is a natural test of agent-versus-environment blame.
  - (b) L1 runs with logged exogenous variables (τ² user-simulator seed and transcript).
  - (c) Per-step skill credit.
  - (d) AgentRx failed_agent, TrajErrBench k*.
  - (f) Independence of Φ from the action is hard to guarantee: the simulated user *reacts* to the agent.
- **Re-run:** no.

#### LLM-era return decomposition: SPA-RL, implicit PRM, LaRe, attention-based credit, GraphGPO
- **SPA-RL.** Wang, Leong, Wang, Wang, Li, "SPA-RL: Reinforcing LLM Agents via Stepwise Progress Attribution", arXiv:2505.20732. VERIFIED-pdf. Code: github.com/WangHanLinHenry/SPA-RL-Agent.
  - A progress estimator E_γ (LLM backbone) outputs per-step contributions c_t, trained by MSE so that Σ_t c_t matches the task outcome. The dense reward is c_t plus an action-grounding term. Evaluated on ALFWorld, WebShop and VirtualHome.
  - **Mapping.** An *existing* L1 return decomposer on AgentErrorBench's own environments. Its most negative c_t on failed runs is an attribution that can be scored on AgentErrorBench k* today. It is the first learned baseline to report.
- **Implicit PRM.** Yuan, Li, Chen, Cui, Ding, Zhang, Zhou, Liu, Peng, "Free Process Rewards without Process Labels", arXiv:2412.01981. VERIFIED-pdf (venue unverified). Code: github.com/lifan-yuan/ImplicitPRM.
  - Train an outcome reward model parameterised as r_θ(y) = β log π_θ(y)/π_ref(y). The per-step process reward is β log π_θ(y_t|y_{<t})/π_ref(y_t|y_{<t}), learned from response-level labels only.
  - **Mapping.** A return decomposition built into an LM's own likelihood. Train on agent runs with S (L1); each step's log-ratio is its contribution. It ties attribution (P2) to policy improvement (P3) through the same object.
  - (f) It requires fine-tuning an agent-sized LM, and token-level log-ratios are noisy.
- **LaRe.** Qu, Jiang, Wang, Mao, Wang, Liu, Ji, "Latent Reward: LLM-Empowered Credit Assignment in Episodic Reinforcement Learning", arXiv:2412.11120. VERIFIED-pdf (AAAI 2025 per the copyright line). Code: github.com/thu-rllab/LaRe.
  - An LLM writes code that maps states to a multi-dimensional "latent reward", decoded into return-decomposition rewards, with self-verification. The paper claims it also allocates contributions among multiple agents.
  - **Mapping.** An LLM-proposed feature map for the decomposer, e.g. "DB write matches policy", "tests run before submit".
- **ABC (attention-based credit).** Chan, Sun, Holt, van der Schaar, "Dense Reward for Free in Reinforcement Learning from Human Feedback", arXiv:2402.00782. VERIFIED-pdf (venue unverified). Code: github.com/XanderJC/attention-based-credit.
  - Redistributes a reward model's scalar along the completion using the reward model's own attention map. The paper proves this equivalent to potential-based shaping.
  - **Mapping.** If an outcome judge or classifier reads the whole trajectory, its attention over steps is a free per-step score. It inherits the attention ≠ attribution caveat.
- **GraphGPO.** Cheng, He, Feng, Xu, Yan, Feng, An, "Beyond Trajectory-Level Attribution: Graph-Based Credit Assignment for Agentic Reinforcement Learning", arXiv:2605.26684. VERIFIED-pdf (abstract). Code: github.com/langfengQ/verl-agent (recipe/GraphGPO).
  - Merges all rollouts into a state-transition graph, estimates each state's distance to the goal, and credits each edge by the distance reduction.
  - **Mapping.** An L1+ notion-B estimator, since grouped rollouts of the same task share states. It is feasible on ALFWorld/WebShop, where states recur.

### 3.2b Multi-agent credit: the "who" question

#### COMA (Foerster et al., AAAI 2018)
- **Citation.** Foerster, Farquhar, Afouras, Nardelli, Whiteson, "Counterfactual Multi-Agent Policy Gradients", arXiv:1705.08926. VERIFIED-pdf.
- **Mechanism.**
  - Difference rewards D^a = r(s,u) − r(s,(u^{−a}, c^a)) replace agent a's action with a default c^a. They "typically require access to a simulator", one counterfactual simulation per agent, plus a user-chosen default action.
  - COMA replaces both with a centralised critic and a counterfactual baseline that marginalises a's action:
    ```
    A^a(s,τ,u) = Q(s,τ,u) − Σ_{u'^a} π^a(u'^a|τ^a) Q(s,τ,(u^{−a},u'^a))
    ```
- **Mapping.** This is exactly the re-run versus fitted-model split.
  - *Difference-reward version*: replace agent a's message at step k with a default ("no-op/pass", deleted, or re-sampled) and **re-run** at temperature 0 with the Aegis MASLab wrappers. The result is an exact a*.
  - *COMA version*: a critic Q(prefix, joint message) trained on L1 runs, marginalising a's message over samples from a's own LLM. This is model-only.
  - (d) Aegis (agent, mode) pairs (set-F1 over agents), Who&When agent-level accuracy (OOD), TraceElephant MAS subsets.
  - (e) "Agent with most messages" and "agent emitting the last message" baselines.
  - (f) The choice of default action changes the answer; deleting a message can break the protocol (the orchestrator waits forever).
- **Re-run:** the difference version yes; COMA no.

#### Shapley Q-value (Wang et al., AAAI 2020) and Shapley Counterfactual Credits (Li et al., KDD 2021)
- **Citations.**
  - Wang, Zhang, Kim, Gu, "Shapley Q-value: A Local Reward Approach to Solve Global Reward Games", arXiv:1907.05707. VERIFIED-pdf.
  - Li, Kuang, Wang, Liu, Chen, Wu, Xiao, "Shapley Counterfactual Credits for Multi-Agent Reinforcement Learning", arXiv:2106.00285. VERIFIED-pdf.
- **Mechanism.** The Shapley value Sh_i = Σ_{C⊆N\{i}} |C|!(|N|−|C|−1)!/|N|! · [v(C∪{i}) − v(C)], which satisfies efficiency, dummy and symmetry. Li et al. estimate v(C) as the change of a *central critic* when the actions of agents outside C are set to a baseline. Monte-Carlo sampling of coalitions makes the cost polynomial.
- **Mapping.**
  - Players = agents gives a*. Players = steps gives a Shapley version of k*/E, which is what Causal Agent Replay (§3.4) does with re-execution.
  - Efficiency means the shares sum to the failure, giving a graded responsibility like EPV's ρ_t = Δ_t/p(x).
  - (b) Critic at L1, or exact values with temperature-0 replay (L1+). (d) Aegis, Who&When agent-level, MP-Bench sets (nDCG over steps).
  - (f) Coalitions of *steps* are not well defined: removing step j changes what later steps would have been. Only executed coalitions (re-run with the steps outside C replaced) are causal.
- **Re-run:** critic version no; exact version yes.

### 3.3 Sequential treatment effects and causal inference on time series (notion C)

**The common mapping for this family.**
- **Treatment A_k**: the intervention applied at step k, A_k ∈ {none, oracle-action, hint, fix-observation, reassign, corrupt-output, corrupt-observation, delete, swap-agent}, i.e. P1's δ vocabulary.
- **Time-varying covariates X_t**: the std. encoder of steps and observations.
- **Outcome Y**: the terminal S, or intermediate progress where one exists (tests passing after an edit, WebShop attribute-match score, τ² database distance to the goal state).

Observational agent logs contain only "A_k = none". The identifying assumptions are consistency, positivity and sequential ignorability (CRN §3). Positivity fails for every δ the agent never produced. These models therefore need training data in which δ was **randomised**:
- Corruption δ: Aegis' injector on MASLab, injected into successful temperature-0 runs, or TracerTraj-style injection.
- Repair δ: rollouts on τ²/ALFWorld/WebShop/SWE-bench.

Once δ is randomised, the confounding-adjustment machinery (IPTW, adversarial balancing) is unnecessary *except* when the screen itself is adaptive. EPV's bisection schedule concentrates rollouts near drops, and that selection must be re-weighted.

One property is unusual compared with medicine: an LLM agent's **propensity** P(a_t | h_t) is computable from token log-probabilities. IPTW is therefore feasible from logs. The catch is that low-temperature agents give near-degenerate propensities.

#### Marginal structural models (Robins, Hernán, Brumback 2000) and R-MSN (Lim et al., NeurIPS 2018)
- **Citations.**
  - Robins, Hernán, Brumback, "Marginal Structural Models and Causal Inference in Epidemiology", Epidemiology 11(5):550–560, DOI 10.1097/00001648-200009000-00011. VERIFIED-search.
  - Lim, Alaa, van der Schaar, "Forecasting Treatment Responses Over Time Using Recurrent Marginal Structural Networks", NeurIPS 2018. VERIFIED-search; no arXiv version found.
- **Mechanism.** Inverse-probability-of-treatment weighting with stabilised weights Π_t P(A_t|Ā_{t−1})/P(A_t|H̄_t) (the standard textbook form, not transcribed from the paper) creates a pseudo-population in which treatment does not depend on time-varying confounders. R-MSN learns the propensity and outcome networks as RNNs and puts the IPTW weights into a seq2seq training objective.
- **Mapping.**
  - (a) Std. encoder. (b) L1 logs plus propensities from agent log-probs, or L1+ screens with known randomisation probabilities.
  - (c) The effect of an action class at step k on S. (d) T1 calibration against held-out rollout success rates; T2 argmax against k*.
  - (e) A δ-agnostic predictor.
  - (f) Extreme weights at low temperature.
- **Re-run:** no (weights replace re-runs, if positivity holds).

#### g-computation (Robins 1986) and G-Net (Li et al.)
- **Citations.**
  - Robins, "A new approach to causal inference in mortality studies with a sustained exposure period", Mathematical Modelling 7(9–12):1393–1512 (1986), DOI 10.1016/0270-0255(86)90088-6. VERIFIED-search.
  - Li, Shahn, Li, Lu, Chakraborty, Sow, Ghalwash, Lehman, "G-Net: A Deep Learning Approach to G-computation for Counterfactual Outcome Prediction Under Dynamic Treatment Regimes", arXiv:2003.10551. VERIFIED-pdf (abstract); venue unverified.
- **Mechanism.** The g-formula integrates the outcome model over the *simulated* distribution of future covariates under the intervened regime. G-Net learns these conditional distributions with sequential deep models and estimates counterfactual outcomes by Monte Carlo simulation of covariate trajectories under static or dynamic regimes. Evaluated on CVSim, a mechanistic cardiovascular simulator.
- **Mapping.** g-computation = "simulate the future after δ with a learned model", i.e. **model-based P1**.
  - The learned model is a world-plus-agent simulator: an LLM that proposes the agent's next step and also predicts the tool return or simulated-user reply. Roll it forward from τ_{<k} ⊕ δ and read S off a learned or rule-based verifier.
  - Feasible where the environment is textual and predictable: τ²-bench, where the user is itself an LLM simulator and the DB transitions are rule-like, and ALFWorld, where the true text simulator can serve as part of the model. Not feasible on SWE-bench (test outcomes).
  - (d) T1 error against real rollouts.
  - (f) Simulator bias compounds over the horizon, and errors in the simulated environment become false attributions.
- **Re-run:** no (simulated); real rollouts are needed only for validation.

#### Counterfactual Recurrent Network (Bica et al., ICLR 2020)
- **Citation.** Bica, Alaa, Jordon, van der Schaar, "Estimating Counterfactual Treatment Outcomes over Time through Adversarially Balanced Representations", arXiv:2002.04083. VERIFIED-pdf. Code: github.com/ioanabica/Counterfactual-Recurrent-Network.
- **Mechanism.** Estimate E(Y_{t+τ}[ā(t,t+τ−1)] | H̄_t) under consistency, positivity and sequential strong ignorability. An LSTM encoder builds a representation Φ(H̄_t) that is predictive of outcomes but **not** of the current treatment (domain-adversarial training with gradient reversal), so that P(Φ|A_t=A_1) = … = P(Φ|A_t=A_K). A decoder rolls out a planned treatment sequence.
- **Mapping.**
  - (a) Std. encoder over τ_{<k}. (b) L1+ screen data with δ at random k.
  - (c) p̂_δ(τ,k) and φ̂ = p̂_δ − p̂_none.
  - (d) T1: Brier score and AUROC of p̂_δ against rollout success on held-out (τ,k,δ) triples. T2: argmax_k max_δ φ̂ against k* (TrajErrBench-τ², AgentErrorBench). T3: fragility curves r(k/T).
  - (e) Position-only φ̂(k/T) and a δ-agnostic g.
  - (f) Balancing is pointless under randomised δ but essential for adaptive screens and for learning from Aegis' *selected* failures (only successful injections are released).
- **Re-run:** no at test time; the training data are rollouts.

#### Causal Transformer (Melnychuk, Frauen, Feuerriegel, ICML 2022)
- **Citation.** "Causal Transformer for Estimating Counterfactual Outcomes", arXiv:2204.07258. VERIFIED-pdf. Code: github.com/Valentyn1997/CausalTransformer.
- **Mechanism.** Three transformer subnetworks, for time-varying covariates, previous treatments and previous outcomes, are joined by cross-attention. A *counterfactual domain confusion* loss learns representations that predict the next outcome but not the current treatment assignment.
- **Mapping.** The three streams map onto agent traces as observations o_t, actions or interventions (a_t, δ), and intermediate outcomes (progress signals).
  - It exploits partial progress where available: SWE-bench test counts, WebShop scores, τ² DB-goal distance.
  - (b) L1+. (c)/(d)/(e) As CRN. (f) Long traces (LongRCA) exceed comfortable context lengths.
- **Re-run:** no at test time.

#### TE-CDE (Seedat et al., ICML 2022): the NCDE bridge to OAT
- **Citation.** Seedat, Imrie, Bellot, Qian, van der Schaar, "Continuous-Time Modeling of Counterfactual Outcomes Using Neural Controlled Differential Equations", arXiv:2206.08311. VERIFIED-pdf. Code: github.com/seedatnabeel/TE-CDE.
- **Mechanism.**
  ```
  encoder:  Z_{t0} = g_η(X_{t0}, A_{t0}, Y_{t0}),   Z_t = Z_{t0} + ∫_{t0}^{t} f_θ(Z_s) d[X_s, A_s, Y_s]
  decoder:  Z_{t'} = Z_t + ∫_t^{t'} f_φ(Z_s) (dA_s/ds) ds        (driven by the hypothetical treatment schedule)
  ```
  Domain-adversarial training removes time-dependent confounding. The evaluation is a tumour-growth simulator with irregular sampling.
- **Mapping.** OAT is the *encoder half* of this model: an NCDE over (h_t, u_t), trained one-class to reconstruct the control path. TE-CDE adds what OAT lacks, **a decoder controlled by an intervention path**. The concrete T1 surrogate:
  1. Run the NCDE encoder over τ_{<k}, with OAT's gate optional.
  2. Run a decoder CDE driven by a path whose increment at k encodes δ.
  3. Read out P(S).
  - (b) L1+. (d) T1 calibration and T2 against k*.
  - (e) OAT's anomaly score at k as a δ-agnostic baseline.
  - (f) Everything the brief says about OAT's time axis applies. The natural cubic spline is non-causal; use rectilinear or causal interpolation. u = t/T is undefined for a counterfactual future of unknown length; use the absolute step index. The decoder assumes the agent's post-k behaviour is summarised by the latent state, i.e. an implicit g-computation.
- **Re-run:** no at test time.

#### When-to-treat policies (Nie, Brunskill, Wager)
- **Citation.** "Learning When-to-Treat Policies", arXiv:1905.09751. VERIFIED-pdf (2020 draft); JASA venue unverified.
- **Mechanism.** An "advantage doubly robust" estimator for learning *when* to start which treatment from observational data under sequential ignorability. It has welfare regret bounds and needs no Markov assumption.
- **Mapping.** This is the *timing* question of P2-U3 and P3-R: when to restart, hint or escalate.
  - The value of intervening at t trades off success gained against cost. EPV's restart point t_r = min{t : R(x,B−t) − V(h_t) ≥ µ} and its certified t_pnr are the oracle solutions.
  - (b) L1+ (screens with δ at several k; EPV curves). (c) A stopping/intervention rule.
  - (d) Lead time against t_lock (Failure-as-a-Process; brief: the prompted monitor has median lead time 0 and 18% recall), and expected success after the intervention (EPV: 0.44 → 0.57 offline when restarting at the measured point).
  - (e) "Intervene at the first symptom", and "intervene at a fixed fraction of T".
  - (f) It needs interventions observed at varied times. Doubly robust estimation needs both a propensity model and an outcome model.
- **Re-run:** no at test time.

#### Synthetic control, CausalImpact, interrupted time series
- **Citations.**
  - Abadie, Diamond, Hainmueller, "Synthetic Control Methods for Comparative Case Studies", JASA 105(490):493–505 (2010), DOI 10.1198/jasa.2009.ap08746. VERIFIED-search.
  - Brodersen, Gallusser, Koehler, Remy, Scott, "Inferring causal impact using Bayesian structural time-series models", Ann. Appl. Stat. 9(1):247–274 (2015), DOI 10.1214/14-AOAS788, arXiv:1506.00356. VERIFIED-pdf.
  - Bernal, Cummins, Gasparrini, "Interrupted time series regression for the evaluation of public health interventions: a tutorial", IJE 46(1):348–355 (2017), DOI 10.1093/ije/dyw098. VERIFIED-search; corrigendum DOI 10.1093/ije/dyaa118.
- **Mechanism.**
  - Synthetic control: a convex combination of donor units matching the pre-period gives the counterfactual post-period.
  - CausalImpact: a diffusion-regression state-space model on control series predicts the counterfactual response and the temporal evolution of the effect.
  - Interrupted time series: segmented regression for level and slope change at a *known* interruption time.
- **Mapping.**
  - These need a per-step continuous outcome series and donors. Candidate series: g(τ_{≤t}) from §4, tests passing after each edit (SWE-bench), WebShop match score, τ² DB distance. Candidate donors: successful runs of the same task, aligned by step or by progress.
  - Their natural use is **testing a candidate k** from another attributor ("did progress diverge from its synthetic control after k?"), not searching over k. Searching over k turns ITS into change-point detection, which is P2-U2 and another slice.
  - (b) L1. (d) Agreement of the test with k*. (e) Std. baselines.
  - (f) The terminal binary outcome, the lack of a meaningful pre-period for early errors (Who&When: 36% at steps 0–2), and donor scarcity.
- **Re-run:** no.

#### Granger causality: classical, neural, and CAUSE
- **Citations.**
  - Granger, "Investigating Causal Relations by Econometric Models and Cross-spectral Methods", Econometrica 37(3):424–438 (1969), JSTOR 1912791, DOI 10.2307/1912791. VERIFIED-search.
  - Tank, Covert, Foti, Shojaie, Fox, "Neural Granger Causality", IEEE TPAMI, DOI 10.1109/TPAMI.2021.3065601, arXiv:1802.05842. VERIFIED-pdf and abs.
  - Zhang, Panum, Jha, Chalasani, Page, "CAUSE: Learning Granger Causality from Event Sequences using Attribution Methods", ICML 2020 (PMLR 119), arXiv:2002.07906. VERIFIED-pdf and search. Code: github.com/razhangwei/CAUSE.
- **Mechanism.**
  - Neural Granger: component-wise MLPs/LSTMs with group-lasso penalties on input weights; zeroed groups mean non-causality.
  - CAUSE fits a neural point process, then applies integrated gradients to the cumulative intensity, against a baseline in which the observed event types are zeroed. Completeness gives f_k(x_i) − f_k(x̄_i) = Σ_{j≤i} A_j(f_k, x_i, x̄_i): per-event contributions to the intensity of type k. These aggregate into a population statistic Y_{k,k'}.
- **Mapping.**
  - Event types are (agent, span kind / step type, observation flag), with a terminal "failure" type and a "success" type.
  - Per-event A_j toward the failure intensity gives *instance-level* step scores (notion A on a point-process predictor). The population Y_{fail,k'} says which step types Granger-cause failure, a *mode-level* prior (MAST, AgentRx, TRAIL categories).
  - TRAIL spans carry real timestamps, so the irregular-time setting is native.
  - (b) L1 (needs non-failing sequences). (d) Mode frequency correlation; per-instance k*.
  - (f) Granger causality is predictive precedence. Symptoms precede the failure label too, so Granger ranks symptoms highly. It cannot separate t_err from t_obs.
- **Re-run:** no.

### 3.4 Agent-side anchors (papers already applying these ideas to LLM agents)

- **Executable Prefix Values for Locating Agent Failures.** Shen, Tang, Wei, Sheng, Li, Li, arXiv:2610.17633. VERIFIED-pdf.
  - Assumes replayability. Defines V(h_t), the drop Δ_t = V(h_{t−1}) − V(h_t) (in expectation over the environment, the negative advantage of a_t), responsibility shares ρ_t = Δ_t/p(x), decisive t* = argmax Δ_t, onset t_on (Fisher test), a certified point of no return t_pnr, and concentration C (cliff if C ≥ 0.5, otherwise erosion).
  - Schedule: screen at K=8 continuations per anchor; bisect adjacent anchors that differ by ≥ 0.25; confirm at K=32; certify PNR at K=24 with a Wilson upper bound below ε = 0.15.
  - Data: 150 SWE-bench Verified tasks and two frozen open-weight agents; curves for 47 and 60 failures.
  - Findings: judges agree on the exact step in 21/57 cases; for 66% of judge labels V does not drop at the label; only 7/188 judge answers name the decisive step; 17 cliffs and 30 erosions among the 47 resolved; restarting at the measured point raises expected success from 0.44 to 0.57, while restarting at a judge label does not.
  - Code: anonymous.4open.science/r/laf27.
  - **Role here:** the notion-B ground truth and the calibration target for every L1 method in §4.
- **Causal Agent Replay.** Shah, arXiv:2606.08275. VERIFIED-abs.
  - SCM view of an agent run: do() on a step, then re-execution under the same stochastic policy. A single-step contrastive estimator with a "point-of-commitment" rule, plus a budget-bounded Monte-Carlo **Shapley** estimator across interacting steps, both with confidence intervals.
  - Validated only on synthetic SCMs with planted ground truth.
  - Code: github.com/jaineet17/causal-agent-replay.
  - **Role:** an executed Shapley-over-steps implementation (notion C).
- **AgenTracer.** Zhang, Wang, Chen, Zhou, Wang, Yan, arXiv:2509.03312. VERIFIED-abs.
  - Counterfactual replay (oracle guidance replacing agent actions) plus programmed fault injection produce TracerTraj. An RL-trained 8B tracer is reported up to 18.18% above Gemini-2.5-Pro and Claude-4-Sonnet on Who&When.
  - **Role:** the oracle-action δ executed at scale to produce *labels* (L1+ → L2).
- **Ma et al.** "Automatic Failure Attribution and Critical Step Prediction Method for Multi-Agent Systems Based on Causal Inference", arXiv:2509.08682. VERIFIED-abs.
  - Shapley values with a "performance causal inversion principle" for agent responsibility, and a causal-discovery algorithm (CDC-MAS) for non-stationary interaction data to find critical steps.
  - Evaluated on Who&When and TRAIL; up to 36.2% step-level accuracy.
  - **Role:** the only Granger/causal-discovery-style attributor already run on Who&When. The abstract does not say whether it reports position baselines.

---

## RUDDER-style return decomposition as an L1 attributor

**Goal.** From trajectories with outcomes only (L1), produce per-step blame on failed runs. It must be causal (usable online as a P2-U3 monitor), able to express recovery, and scored against k*, k_lock, E and MP-Bench consensus. Conceptually it is a learned approximation of EPV's prefix-value curve V(h_t).

### 4.1 Data (all L1, collected for free)

| environment | training runs (self-collected, S from the verifier) | labelled test set | note |
|---|---|---|---|
| τ²-bench airline/retail | several thousand runs; ≥ 8 seeds per task so that runs share prefixes and give per-task pass rates; same models as the test set where affordable (gpt-5, deepseek-reasoner, qwen3-max) | TrajErrBench-τ² (400 failures, k* + 20 error types); AgentRx τ-retail (29, all failure events + root cause + failed agent) | user-simulator seed logged (exogenous Φ for the CCA split) |
| ALFWorld / WebShop | runs of Qwen3-8B, Llama-3.3-70B and GPT-4o (AgentErrorBench's models) | AgentErrorBench (100 + 50; critical step + module) | deterministic simulators, so prefixes recur and GraphGPO/IRCR-style matching is possible |
| SWE-bench Verified | SWE-agent with GPT-4o at temperature 0.3 (TraceElephant's configuration) | TraceElephant SWE-agent subset (44 failures; step = LLM call) | EPV-style restart curves can be built here (§4.7) |
| (in-domain, released) | AgentHallu: 250 clean + 443 failed runs | AgentHallu hallucination step | the only labelled set that ships clean runs *with* step text |
| MAS (OOD only) | MASLab runs through the Aegis wrappers (GPT-4o-mini, temperature 0) | Who&When (184), MP-Bench (289) as OOD, like OAT | no in-domain successes for these two |

Failure-as-a-Process (t_err/t_lock/t_obs) has no step text. The repo notes say it can be re-joined with the public Terminal-Bench trajectories. If that works, it is the one place to measure the t_obs bias directly (§4.6).

### 4.2 Encoder

- **Half-steps.** Index the action a_t and the observation o_t as separate time points. Ismail et al.'s conflation result and Synthetic Returns' "spike after the critical action" both argue for this. It is also required for the action/observation (skill/luck) split.
- **Features.** The std. encoder: proxy-LLM hidden states of the step text conditioned on the prefix (OAT reports that proxy models lose little), PCA to 64–128 dimensions. Add categorical marks (agent id, tool name, span kind) and scalars (return length, empty return, exception/traceback, non-zero exit, repeated-call n-gram match, proxy-LM NLL of the action). Add RUDDER's **difference features** h_t − h_{t−1} and a tool-argument diff, which address explaining away.
- **Sequence model.** A causal LSTM. RUDDER's argument for LSTMs over feed-forward critics is that they change prediction only on evidence, giving fewer spurious contributions. A causal transformer is the alternative. Either way the model outputs a logit ℓ_t = logit g(τ_{≤t}) at every half-step, plus a per-task offset b_x estimated from that task's runs, so that task difficulty is not credited to step 1.

### 4.3 Decomposition losses (four variants, same encoder)

| variant | loss | step credit |
|---|---|---|
| V1 RUDDER | Σ_t w_t · BCE(S, σ(b_x + ℓ_t)), with w_t increasing in t (RUDDER up-weights late predictions), + λ Σ_t \|ℓ_t − ℓ_{t−1}\| (changes only on evidence; Dynamask's λ_c analogue) | r_t = σ(b_x+ℓ_t) − σ(b_x+ℓ_{t−1}) |
| V2 LS/RRD | S ~ Bernoulli(σ(b_x + (T/\|I\|) Σ_{t∈I} c_t)) on random subsequences I (RRD), with a contextual c_t (SPA-RL) | c_t |
| V3 hazard (P2-U1) | P(S=1\|τ) = Π_t (1 − h_t) | posterior P(t*=t \| S=0, τ); monotone, single change point |
| V4 natural-fork targets | V1 plus an auxiliary BCE at every prefix shared by several runs (τ² seeds, ALFWorld/WebShop determinism), with target the empirical success rate of all runs sharing τ_{≤t}. A causal model already gives identical outputs on identical prefixes; the gain is the Monte-Carlo target, not a consistency penalty | as V1. These "natural forks" are a free, weak L1+ signal |

### 4.4 Scoring and decoding

- **Action/observation split.** This is the CCA skill/luck split applied to RUDDER.
  - Action credit: r^a_t = g(τ_{<t} ⊕ a_t) − g(τ_{<t}).
  - Observation credit: r^o_t = g(τ_{≤t}) − g(τ_{<t} ⊕ a_t).
  - Agent blame is b_t = −r^a_t on agent half-steps. Environment or user blame is −r^o_t. Score the latter against AgentRx failed_agent ∈ {Assistant, User}.
- **Decisive step.** k̂* = argmax_t b_t (EPV's decisive step). Alternatively, the *earliest* t with b_t ≥ θ (the brief's "earliest" definition of k*). θ is the conformal (1−α)-quantile of the maximum b_t on held-out *successful* runs, which gives OAT-style FPR control.
- **Sets and rankings.** {t : b_t ≥ θ} is scored by set-F1 against AgentRx failure events and TRAIL spans. The ranking by b_t is scored by nDCG@5 against MP-Bench consensus rates (OOD).
- **Lock-in.** k̂_lock = first t after which σ(b_x + ℓ_s) < ε for all s ≥ t, i.e. the model's point of no return. Score it against AgentRx k_lock, and against Failure-as-a-Process t_lock if the re-join works.
- **Agent.** â* = argmax_a Σ_{t: agent(t)=a} b_t, scored on Who&When agent level and Aegis agent sets.

### 4.5 Metrics and baselines it must beat

- **Metrics.** Exact, ±1 and ±3 step accuracy; mean |k̂* − k*|/T; nDCG@5 (MP-Bench); set-F1 (AgentRx, TRAIL); lead time of k̂_lock relative to t_lock. Also report trajectory-level AUROC of g at T and of g at k* as sanity checks: is g an outcome predictor at all, and is the failure already predictable at k*?
- **Baselines.**
  1. Position prior per dataset (first-3 / relative-position mean), random-k, last step.
  2. The **first-symptom heuristic** and its **dependency parent** (the TVT-style transport baseline).
  3. OAT (top-3 and conformal) on the same embeddings.
  4. The IRCR frequency baseline.
  5. SPA-RL's progress estimator (an existing learned decomposer, on ALFWorld/WebShop).
  6. FIT/Dynamask applied to the same g. Does model-side occlusion beat simple differences?
  7. An all-at-once LLM judge.

### 4.6 Known failure modes, with the diagnostic for each

1. **Predictability ≠ causation (the t_obs bias).**
   - g drops where failure becomes *predictable from the logged content*. RUDDER notes that late predictions are more accurate because the future is less random. Synthetic Returns spike after the critical action.
   - In coding agents, Failure-as-a-Process medians are t_err 7, t_lock 12, t_obs 16, with 28% of failures silent. EPV reports that judge labels mostly do not coincide with drops.
   - Prediction: k̂* mass concentrates at t_obs, or at the step after k*.
   - Diagnostic: histograms of k̂* − k* and k̂* − t_obs (t_obs from the first-symptom heuristic or Failure-as-a-Process).
   - Mitigations: the half-step split; TVT transport along dependency edges; a WinIT window; L1+ calibration at a few anchors (§4.7).
2. **An identifiability limit at L1.** A cause at step k can be found only if its *content* shifts P(S | τ_{≤k}) across the training distribution. Plausible-but-wrong plans and silent hallucinations do not, until their consequences appear. No L1 method recovers these; rollouts (L1+) do. This is the precise sense in which L1+ is necessary.
3. **Recovered errors in successes.** These are frequent (brief: 2.3 recovered events per 22.8 steps on Terminal-Bench). g learns that many error types are recoverable and assigns them small drops. That is correct for k_lock but lowers recall against "all errors" labels (AgentRx events, TRAIL). Report the two targets separately.
4. **Task-difficulty confound.** Hard tasks fail regardless. Without b_x the credit sits on the query or the first observation. Use ≥ 8 runs per task; also report blame on observation half-steps (environment) separately.
5. **Policy mismatch.** The labelled TrajErrBench/TraceElephant trajectories come from specific agents. A g trained on other agents' runs estimates V under *their* policy. Match models where possible, and report the shift.
6. **Last-step shortcut.** Final answers, "TERMINATE" and failure verbalisations produce the largest drops. OAT's App. H reports the same behaviour, and CORRECT-Error has 52% of its errors in the last fifth. Report with and without the final step.
7. **Multiple causes / erosion.** EPV: 30/47 failures are erosion. Use set decoding and report the concentration C of the predicted drops. The single-change-point V3 is misspecified for erosion.
8. **Variance on long traces.** LongRCA has a median of 145 steps. Use RRD subsequences and the λ-smoothing.
9. **Step units.** Dataset step units differ (brief §1). Fix the half-step convention per dataset before pooling.

### 4.7 L1+ upgrade and the calibration experiment

On 30–50 failed runs per environment (TraceElephant SWE-agent, TrajErrBench-τ²), measure V(h_t) by restarts with EPV's schedule: K=8 screening, bisection on gaps ≥ 0.25, K=32 confirmation. Then:
- **(i)** measure how far g's curve is from V̂: drop location, concentration, cliff/erosion agreement.
- **(ii)** fit isotonic calibration of g to V̂.
- **(iii)** fine-tune g with V̂ as a soft target at the anchors.

The difference in step accuracy before and after (iii) is the measured value of L1+ over L1 for this attributor. The same anchors also give training data for the §3.3 surrogates.

---

## Ranked recommendations

"Expected gain" is a reasoned expectation, not a measurement. No method below has been run on these benchmarks unless stated. The OAT reference points on Who&When are top-3 0.45 against first-3 0.36 and random-3 0.29, and AUROC 0.76 against position-only 0.60.

| # | method | benchmark(s) | target label | supervision | expected gain over OAT / position prior | effort | risk |
|---|---|---|---|---|---|---|---|
| 1 | RUDDER-style causal prefix-success model, half-step action/observation split, per-task offset (§4, V1/V4) | τ²-bench → TrajErrBench-τ², AgentRx; ALFWorld/WebShop → AgentErrorBench; AgentHallu (in-domain) | k*, k_lock, Assistant-vs-User | L1 | Largest where errors are visible in the step's content (wrong tool arguments, DB writes, invalid actions). It uses failures, which OAT discards, and is causal and online. Must clear the late prior on TrajErrBench (0.65) and the early prior on AgentErrorBench (0.23). Weakest on silent reasoning errors | M | t_obs bias (§4.6.1); policy mismatch |
| 2 | Restart-measured prefix values (EPV protocol) as ground truth + L1+ calibration of #1 | SWE-bench Verified (TraceElephant SWE-agent), τ²-bench | t*, t_pnr vs k*, k_lock | L1+ | Not a competitor but the reference. It tells whether k* labels mark causes (EPV: 66% of judge labels show no drop) and bounds #1 | L (K·T rollouts per run) | replay fidelity; compute |
| 3 | TVT-style blame transport along dependency edges, on top of #1's drops | SymFail event graphs, MemTrace, TRAIL span trees | t_err (from t_obs), faulty node / memory op | L1 + L0 graph | Directly targets #1's main failure mode; gains expected where the error and the symptom are linked by explicit data flow (memory and tool-result misuse) | S–M | reasoning errors have no explicit edge |
| 4 | Sequential treatment-effect surrogate f(prefix,k,δ): TE-CDE (OAT's NCDE plus a treatment decoder) or Causal Transformer | train: Aegis injector on MASLab (randomised corruption) + repair-δ rollouts on τ²/ALFWorld/WebShop; test: rollout φ, TrajErrBench, AgentErrorBench | φ̂ → T2 (argmax vs k*), T3 fragility | L1+ (training) | Replaces rollouts at test time. Unlike OAT it is supervised by interventions. The competitor is the rollout φ, not the position prior | L | positivity outside the screened δ; δ encoding; adaptive-design selection bias |
| 5 | Native-Guide graft (aligned step from the nearest successful run of the same task) + FIT-style prefix re-query; executed graft = oracle-action δ | ALFWorld/WebShop/τ² (many runs per task) | k* (earliest flip) | L1 (model) / L1+ (executed) | Operationalises the "had it been correct" definition of k* without a human oracle. The executed variant gives P1's oracle intervention cheaply | S (model) / M (executed) | step alignment; grafts inconsistent with the prefix |
| 6 | Difference rewards / Shapley over agents with temperature-0 replay (COMA, Shapley counterfactual credits) | Aegis (agent, mode); Who&When agent-level (OOD); TraceElephant MAS | a* | L1+ (replay) or L1 (critic) | Exact per-agent effects on Aegis-style systems; who-accuracy against "most messages" and "last speaker" baselines | M | the default action changes the answer; deleting messages breaks protocols |
| 7 | Align-RUDDER profile alignment of the failed run to an MSA of successes | AgentErrorBench ALFWorld/WebShop; τ² procedures | k* (first deviation) | L1 (success selection, OAT's regime) | The head-to-head competitor to OAT under identical supervision, discrete and causal | M | many valid plans; recoverable detours flagged |
| 8 | HCA ratio credit with proxy-LM log-probs (prompt with vs without "this run failed") | AgentHallu, AgentErrorBench, Who&When | k* | L1 (discriminative) / L0+S (generative) | Cheap, model-only. Plausible on single-step hallucinations | S | likelihood dominated by surface tokens; degenerate at temperature 0 |
| 9 | IRCR frequency baseline (failure rate of runs containing an equivalent step) | any environment with many runs per task | k*, E | L1 | A baseline to report, not to win | S | confounded by task |
| 10 | Amortised explainers (TimeX/TimeX++) on the #1 predictor | as #1 | k* + mode (landmarks) | L1 | Joint step and mode attribution at OAT-like speed | M | bounded by predictor quality |
| 11 | CAUSE (neural point process + IG) | TRAIL (timestamps), SymFail, LongRCA | mode-level priors, E | L1 | Population-level mode attribution; little instance-level gain expected | M | Granger ranks symptoms |
| 12 | Implicit-PRM log-ratio decomposition | ALFWorld/WebShop with open agents (Qwen3-8B) | k*; directly reusable in P3 | L1 | Couples attribution and policy improvement through one object | L | requires training an agent-sized LM |
| 13 | Synthetic control / ITS on a progress series to *test* a candidate k | SWE-bench (tests passing), WebShop (score), τ² (DB distance) | verification of k̂ from #1 | L1 | Low as an attributor; useful as a falsification test | S–M | binary terminal outcome; donor scarcity |

---

## Open gaps

1. **No benchmark pairs step labels with measured V-curves at scale.** EPV covers SWE-bench Verified only, with two agents and about 107 resolved failures. Building V-curves (or φ for an oracle δ) for TrajErrBench-τ² and AgentErrorBench-ALFWorld would let all three notions be scored against both human k* and the decisive drop. It would also settle how often k* is a symptom.
2. **No "planted saliency" benchmark of the Ismail et al. kind.** Injection datasets exist, but their positions are skewed (Who&When Pro 0.83, CORRECT-Error 0.95), they release only *successful* injections (Aegis), and Aegis has no step labels. An injection set with uniformly randomised step positions, released clean counterparts, and both failed and absorbed injections would serve as a calibrated synthetic benchmark. It would also be free L1+ data for §3.3.
3. **Positivity.** Logs contain one action per prefix. Only injections randomise the "treatment", and repair δ exist nowhere outside rollouts. No released dataset contains executed repair interventions with outcomes, apart from what replay frameworks (SymTrace, TraceElephant dynamic) can generate.
4. **Cause versus symptom.** No time-series XAI method separates a cause from a later symptom. Granger causality by construction credits symptoms. WinIT's window, TVT's transport and RUDDER's difference features are the only temporal mechanisms that move credit backwards, and none has been tested on agent traces.
5. **Recovery and negative credit.** Hazard models forbid recovery. RUDDER, Shapley and EPV's ρ_t allow it. Whether recovered errors belong in the label is a definition question (AgentRx all events vs k_lock), and benchmarks mix the two.
6. **Known propensities are unexploited.** Unlike clinical data, an agent's P(a_t | h_t) is computable. IPTW and doubly robust estimators of step effects from logs are therefore possible in principle. Nobody has tried, and low-temperature degeneracy is the obstacle.
7. **The OAT ↔ TE-CDE combination is open.** No work combines an outcome- or one-class-trained NCDE encoder with a treatment-driven decoder for agent traces.
8. **RL credit methods are never scored on attribution.** RUDDER, RRD, IRCR, SPA-RL and GiGPO are evaluated by learning speed or success rate, never by agreement with step labels. Running SPA-RL's estimator on AgentErrorBench is a one-day experiment that nobody has reported.
9. **The default action for "who".** COMA was motivated by the arbitrariness of difference rewards' default action. For agents the candidates (delete, no-op message, resample, oracle) give different a*, and no study compares them.
10. **Time-axis conventions.** Dynamask's smoothness, WinIT's window and TSR's threshold all depend on the step unit (message, LLM call, span). Results will not transfer across Who&When, TraceElephant and TRAIL without the normalisation the brief demands.

---

## Verification log (50 items)

| # | item | id / DOI | status |
|---|---|---|---|
| 1 | Dynamask (Crabbé & van der Schaar, ICML 2021) | arXiv:2106.05303 | VERIFIED-pdf |
| 2 | FIT (Tonekaboni et al., NeurIPS 2020) | arXiv:2003.02821 | VERIFIED-pdf |
| 3 | WinIT (Leung et al., ICLR 2023) | arXiv:2107.14317 | VERIFIED-pdf |
| 4 | Ismail et al., TS interpretability benchmark + TSR (NeurIPS 2020) | arXiv:2010.13924 | VERIFIED-pdf |
| 5 | TimeSHAP (Bento et al., KDD 2021) | arXiv:2012.00073 | VERIFIED-pdf; code VERIFIED-search |
| 6 | WindowSHAP (Nayebi et al.) | arXiv:2211.06507 | VERIFIED-pdf (abstract); venue unverified |
| 7 | TimeX (Queen et al., NeurIPS 2023) | arXiv:2306.02109 | VERIFIED-pdf |
| 8 | TimeX++ (Liu et al., ICML 2024) | arXiv:2405.09308 | VERIFIED-pdf |
| 9 | ExtrMask, learned perturbations (Enguehard, ICML 2023) | arXiv:2305.18840 | VERIFIED-pdf |
| 10 | ContraLSP (Liu et al., ICLR 2024) | arXiv:2401.08552 | VERIFIED-pdf (abstract) |
| 11 | CoMTE (Ates et al., ICAPAI 2021) | arXiv:2008.10781; DOI 10.1109/ICAPAI49758.2021.9462056 | VERIFIED-pdf + abs |
| 12 | Native Guide (Delaney et al., ICCBR 2021) | arXiv:2009.13211; DOI 10.1007/978-3-030-86957-1_3 | VERIFIED-pdf + search |
| 13 | RUDDER (Arjona-Medina et al., NeurIPS 2019) | arXiv:1806.07857 | VERIFIED-pdf + search |
| 14 | Align-RUDDER (Patil et al., ICML 2022) | arXiv:2009.14108 | VERIFIED-pdf |
| 15 | RL with trajectory feedback (Efroni et al., AAAI 2021) | arXiv:2008.06036 | VERIFIED-pdf (header) |
| 16 | RRD (Ren et al., ICLR 2022) | arXiv:2111.13485 | VERIFIED-pdf |
| 17 | IRCR (Gangwani et al., NeurIPS 2020) | arXiv:2010.12718 | VERIFIED-pdf |
| 18 | Sequence modelling of temporal credit assignment (Liu et al. 2019) | arXiv:1905.13420 | VERIFIED-pdf (preprint) |
| 19 | GRD (Zhang et al., NeurIPS 2023) | arXiv:2305.18427 | VERIFIED-pdf (abstract) |
| 20 | Synthetic Returns (Raposo et al. 2021) | arXiv:2102.12425 | VERIFIED-pdf (preprint) |
| 21 | TVT (Hung et al., Nat. Commun. 2019) | arXiv:1810.06721; DOI 10.1038/s41467-019-13073-w | VERIFIED-pdf + search |
| 22 | HCA (Harutyunyan et al., NeurIPS 2019) | arXiv:1912.02503 | VERIFIED-pdf |
| 23 | CCA (Mesnard et al., ICML 2021) | arXiv:2011.09464 | VERIFIED-pdf |
| 24 | Survey of temporal credit assignment (Pignatelli et al., TMLR 2024) | arXiv:2312.01072 | VERIFIED-pdf (header) |
| 25 | COMA (Foerster et al., AAAI 2018) | arXiv:1705.08926 | VERIFIED-pdf |
| 26 | Shapley Q-value (Wang et al., AAAI 2020) | arXiv:1907.05707 | VERIFIED-pdf |
| 27 | Shapley counterfactual credits (Li et al., KDD 2021) | arXiv:2106.00285 | VERIFIED-pdf |
| 28 | SPA-RL (Wang et al. 2025) | arXiv:2505.20732 | VERIFIED-pdf |
| 29 | Implicit PRM (Yuan et al.) | arXiv:2412.01981 | VERIFIED-pdf; venue unverified |
| 30 | LaRe (Qu et al., AAAI 2025) | arXiv:2412.11120 | VERIFIED-pdf |
| 31 | ABC, dense reward for free (Chan et al.) | arXiv:2402.00782 | VERIFIED-pdf; venue unverified |
| 32 | GraphGPO (Cheng et al. 2026) | arXiv:2605.26684 | VERIFIED-pdf (abstract) |
| 33 | CRN (Bica et al., ICLR 2020) | arXiv:2002.04083 | VERIFIED-pdf |
| 34 | G-Net (Li et al.) | arXiv:2003.10551 | VERIFIED-pdf (abstract); venue unverified |
| 35 | Causal Transformer (Melnychuk et al., ICML 2022) | arXiv:2204.07258 | VERIFIED-pdf |
| 36 | TE-CDE (Seedat et al., ICML 2022) | arXiv:2206.08311 | VERIFIED-pdf |
| 37 | R-MSN (Lim et al., NeurIPS 2018) | NeurIPS 2018 proceedings | VERIFIED-search |
| 38 | Marginal structural models (Robins et al. 2000) | DOI 10.1097/00001648-200009000-00011 | VERIFIED-search |
| 39 | g-formula (Robins 1986) | DOI 10.1016/0270-0255(86)90088-6 | VERIFIED-search |
| 40 | When-to-treat (Nie, Brunskill, Wager) | arXiv:1905.09751 | VERIFIED-pdf; JASA venue unverified |
| 41 | Synthetic control (Abadie et al. 2010) | DOI 10.1198/jasa.2009.ap08746 | VERIFIED-search |
| 42 | CausalImpact (Brodersen et al. 2015) | arXiv:1506.00356; DOI 10.1214/14-AOAS788 | VERIFIED-pdf |
| 43 | ITS tutorial (Bernal et al. 2017) | DOI 10.1093/ije/dyw098 | VERIFIED-search |
| 44 | Granger (1969) | JSTOR 1912791 / DOI 10.2307/1912791 | VERIFIED-search |
| 45 | Neural Granger causality (Tank et al., TPAMI) | arXiv:1802.05842; DOI 10.1109/TPAMI.2021.3065601 | VERIFIED-pdf + abs |
| 46 | CAUSE (Zhang et al., ICML 2020) | arXiv:2002.07906 | VERIFIED-pdf + search |
| 47 | Executable Prefix Values (Shen et al. 2026) | arXiv:2610.17633 | VERIFIED-pdf |
| 48 | Causal Agent Replay (Shah 2026) | arXiv:2606.08275 | VERIFIED-abs |
| 49 | AgenTracer (Zhang et al. 2025) | arXiv:2509.03312 | VERIFIED-abs |
| 50 | Ma et al., causal-inference failure attribution (2025) | arXiv:2509.08682 | VERIFIED-abs |

Checked and not used:
- arXiv:2505.11821 (turn-level credit assignment for multi-turn LLM agents). It assumes the turn-level rewards are *given*, so it does not decompose them.
- DARS, arXiv:2610.01207. Downloaded but not read beyond the title.

The task's "TS-Shapley / sequential Shapley" is covered by TimeSHAP and WindowSHAP. I found no separately verifiable paper under that exact name.
