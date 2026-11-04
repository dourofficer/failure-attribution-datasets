# Slice G: temporal point processes and discrete event-sequence models

*Written 2026-10-30 for the time-series survey (`notes/lit_timeseries/`). Builds on `00_context_brief.md`. Every paper cited was checked on arXiv, PMLR, a publisher page or a bibliographic index on 2026-10-30. Items marked "unverified" were not confirmed. The numbers in "Sanity checks on released data" were computed for this note from the local copies under `data/` (scripts described inline). They are single runs with no confidence intervals.*

## Scope and verdict

1. **Scope.** This slice covers six areas. (1) Neural temporal point processes (TPPs), and how the conditional intensity relates to the discrete hazard of Proposal 2. (2) Granger causality and influence estimation in multivariate Hawkes processes, as a formal answer to "who". (3) Goodness-of-fit, anomaly and change detection for event sequences. (4) Log and clickstream sequence anomaly detection over a learned event vocabulary. (5) HMMs, HSMMs and switching state-space models as the L0 change-point mixture. (6) 2024–2026 work that models agent traces as event sequences.
2. **Verdict on the formalism.** A trajectory is a *marked* event sequence. In 9 of the 11 datasets inspected the marks carry order but no meaningful time, so a TPP reduces to an autoregressive model over marks plus a length (termination) model. Only TRAIL (span timestamps and durations), MemTrace (`created_at`) and partly SymFail (per-call latency) have real inter-event times. The TPP view earns its keep through **likelihood structure** (exact likelihood, censoring, compensators, branching posteriors, omission scores), not through modelling time.
3. **Hazard and intensity are the same object.** Proposal 2's step hazard is the grouped-time version of the intensity of a latent "fatal error" mark F: `h_t = 1 − exp(−∫ λ_F)`. The outcome likelihood is a censored-survival likelihood: successes are right-censored at T, failures are interval-censored on [1,T] at L1 and exact at L2 (Section 2).
4. **Strongest finding: mark-structural priors beat the position prior by a wide margin, and nobody reports them.** These priors read the mark sequence alone. "First write/edit step" hits Failure-as-a-Process `t_err` exactly in 41.9% of 1,184 failures, against 10.1% for the relative-position prior. "First source edit" hits TraceElephant SWE-agent `k*` in 45.5% of 44, against 4.5%. "First WebSurfer step" scores 19.0% vs 3.4% on Who&When Hand-Crafted, and "step before the first code execution" scores 34.1% vs 19.8% on Who&When Algorithm-Generated. OAT and every attribution paper we know compare only to position priors. Caveat: the heuristics were chosen after inspecting these data.
5. **Weak finding: mark-only sequence models do not localise decisive errors.** On Failure-as-a-Process, two models fall below the position prior at ±1 and ±3 for `t_err`: a first-order transition-surprise model fitted on PASS runs, and a mark-only L1 hazard. Surprise does slightly better on `t_lock` and `t_obs`. Like OAT, sequence surprise is a symptom (`t_obs`) detector.
6. **"Who" via Granger/Hawkes** is well founded: impact functions, branching posteriors and attribution-based Granger statistics. But the theory is population-level and needs long sequences. The instance-level variants (Hawkes branching posterior, CAUSE event attributions, ISAHP) are the ones that map onto `a*` and `k*`. No paper has applied them to agent logs.
7. **Anomaly and GoF tests** (3S statistic, time-rescaling residuals, omission/commission outliers) give calibrated trajectory-level OOD scores. The omission-outlier idea, "an expected mark that did not occur", is the natural formalisation of FM-3.2 missing verification and FM-3.1 premature termination. The confound is that length alone separates FAIL from PASS (AUROC 0.653 on Failure-as-a-Process).
8. **HMM/HSMM/rSLDS** give the exact form of U2: a left-to-right HMM with an absorbing post-change state, whose HSMM duration hazard *is* a discrete hazard. On Failure-as-a-Process marks, the outcome-blind EM fit splits explore-heavy from edit-heavy regimes. It is useless for outcome (AUROC 0.498) but lands on `t_err` 29% of the time, because the phase boundary is where coding agents commit their decisive edit. This illustrates the identifiability warning in the report.
9. **Closest existing agent work** (2026) has three strands. The first is FSMs over tool names with success-model cross-entropy (Cho et al., arXiv:2608.23670). The second is one-class ESN plus CUSUM telemetry monitors (Dubey, arXiv:2608.02464). The third is absorbing Markov chains (TraceToChain, arXiv:2604.24579) and action-alphabet n-gram studies. None evaluates step localisation against an attribution benchmark.
10. **Recommendation.** First add mark-structural baselines to every evaluation (effort S). Then build a censored marked-TPP/hazard with mark × content covariates (effort M), and omission scores for verification and termination failures (effort S). Use Hawkes branching posteriors for "who" only on long logs (LongRCA, Who&When Hand-Crafted, TraceElephant Magentic-One).

## A trajectory as a marked event sequence

### What the released datasets support

The event `e_i = (t_i, k_i, c_i)` has a time `t_i`, a categorical mark `k_i`, and optional content `c_i`: the text, tool arguments, or an embedding. The table lists what is actually in the files. Fields were checked in `notes/*.md` and by opening the files for Who&When, TraceElephant, TRAIL, SymFail and Failure-as-a-Process.

| Dataset | Event unit | Mark vocabulary present in the release | Time | Sequence length (median) |
|---|---|---|---|---|
| Who&When | message | HC: role strings (`human`, `Orchestrator (thought)`, `Orchestrator (-> WebSurfer)`, `WebSurfer`, `FileSurfer`, `Assistant`, `ComputerTerminal`, `Orchestrator (termination condition)`). AG: expert `name` (82 distinct blamed names) + `Computer_terminal`. The Magentic-One ledger inside `Orchestrator (thought)` carries self-reported `is_in_loop` / `is_progress_being_made` flags (present in all 58 HC logs) | order only | 10 (HC 32.5) |
| TraceElephant | LLM API call | `agent_name` (Magentic-One: Orchestrator / WebSurfer / FileSurfer / Coder; Captain-Agent experts). SWE-Agent: tool name `str_replace_editor` / `bash` / `submit`, refinable by the `command` argument (view / create / str_replace / insert) | no timestamps. `usage` tokens per call (zero for SWE-Agent) → a "token clock" | 21 |
| LongRCA | history record | `name` = workflow role (e.g. Task_Planner, Action_Expert, Computer_terminal; TravelPlanner manager/stay/transport/food_attr/verifier) × `role` (assistant/user) | order only | 145 |
| Aegis | turn | `agent_name` × `phase` ∈ {initialization, reasoning, discussion, evaluation} (+ `agent_role` in DyLAN, `is_injected` in MacNet) | order only | 10 |
| SymFail | event-graph node | `kind` ∈ {sys_prompt, user_input, agent_action, tool_call, tool_result, final_result, error} × `agent_id`. Explicit dependency edges | `topological_timestamp` is an order index. Per-call `latency` in `api_records.jsonl` and in tool results (e.g. `browser_http_get` 7.29 s) | 7 |
| TRAIL | OpenTelemetry span | `openinference.span.kind` ∈ {AGENT, CHAIN, LLM, TOOL, none} × `tool.name` (SearchInformationTool, VisitTool, FinalAnswerTool, …) × `status_code`. Spans form a tree (`parent_span_id`) | **ISO timestamps and durations** (e.g. `PT28.9S`); DFS order = chronological | 20 spans |
| MemTrace | operation | `category` ∈ {initialization, boundary_detection, extraction, update, retrieval, evaluation} × `op_name` (9 names). Bipartite DAG | **`created_at` per operation (ms)** | 497 ops in slice |
| SearchAuditBench | message | `role` × `tool_name` ∈ {search, visit} × arguments (query list, URL list) → repeated-query keys | order only | 20 decisions / 43 msgs |
| AgentHallu | step | `role` (agent name in multi-agent frameworks) × `tool_calls[].name` / `arguments` | order only | 6 |
| TrajErrBench | message | `role` ∈ {system, user, assistant, tool}. Tool calls are rendered as text `[tool_calls]\n- fn({json})`, parseable to function name. `judgable` flag | order only | 29 / 117 msgs |
| Failure-as-a-Process | agent turn | `action_segments` → per-step code ∈ {E explore/read, P pure planning, W write/edit, X execute/run, V verify/test, C completion claim, R retry of a failed step, O other}, **for all 1,794 runs, FAIL and PASS**. No step text | order only | 27 (FAIL) / 16 (PASS) |

So only TRAIL and MemTrace support a genuine continuous-time TPP. SymFail and TraceElephant support a partial "cost clock" (latency, tokens). Everything else is a discrete-time marked sequence. Failure-as-a-Process is the only release with both outcome classes *and* a shared step-type vocabulary, so it is the natural L1 testbed for mark-only models. Its `action_segments` must be expanded to per-step codes and the segment boundaries discarded: `t_err` falls on a segment start in 87.8% of FAIL runs, against 55.5% expected by chance. The annotator evidently split segments at the error.

### The hazard–intensity correspondence

*Marked TPP.* With history `H_t`, the conditional intensity is `λ*(t,k) = lim_{dt→0} P(event of mark k in [t,t+dt) | H_t)/dt = λ*_g(t) p*(k | t)`. Here `λ*_g(t) = f*(t)/(1−F*(t))` is the hazard of the next event time. The log-likelihood on [0,T] is

```
ℓ = Σ_i log λ*(t_i, k_i) − Σ_k ∫_0^T λ*(u, k) du                 (compensator Λ*_k(T) = ∫ λ*(u,k) du)
```

*Failure as a latent terminal mark.* Add a mark F, "first unrecovered error", which occurs at most once and is never observed directly. Index time by steps, so step t covers the interval (t−1, t]. Then

```
h_t := P(t* = t | t* ≥ t, H_t) = 1 − exp(−∫_{t−1}^{t} λ*_F(u) du)        (exact for grouped time)
Π_{s≤t}(1 − h_s) = exp(−Λ*_F(t))                                        (survival = exp(−compensator))
h_t ≈ λ*_F(t)·Δ  for small hazards
```

Suppose λ*_F is proportional, `λ*_F(u) = λ_0(u) exp(η_t)` on step t. Then `h_t = 1 − exp(−exp(η_t + log Λ_{0,t}))`, a complementary log-log link (Prentice & Gloeckler 1978, *Biometrics* 34:57–67; DOI not confirmed). That is the principled link for Proposal 2's hazard head; the logistic link is its small-hazard approximation.

*The three supervision levels are three censoring schemes for the F mark.*

```
success (S=1):         log P = −Λ_F(T)                 = Σ_t log(1−h_t)                    right-censored at T
failure, L1 (S=0):     log P = log(1 − exp(−Λ_F(T)))   = log(1 − Π_t(1−h_t))               interval-censored on [1,T]
failure, L2 (k* known):log P = log λ_F(k*) − Λ_F(k*)   = log h_{k*} + Σ_{s<k*} log(1−h_s)  exact event time
L1+ (prefix rollouts): each continuation from τ_{<k} is a censored observation of the same Λ_F after k
```

The posterior `P(t* = t | S=0, τ) = h_t Π_{s<t}(1−h_s) / (1 − Π_s(1−h_s))` in the brief is the conditional density of the latent F event given that it happened before T.

*The observed marks.* In Proposal 2 they are only covariates in `H_t`. A full joint model also gives them intensities: `λ*(t, k) = λ^{(0)}(t,k)` before t* and `λ^{(1)}(t,k)` after. That is a regime-switching (Markov-modulated) point process, and the regime switch is the only signal left at L0. The discrete-time version is a two-state left-to-right HMM with an absorbing post-change state. Failure-as-a-Process's three timestamps then become a three-state process {healthy → erroneous-recoverable → locked}. `t_err` is the entry into the erroneous state (on the path that ends locked), `t_lock` is absorption, and `t_obs` is the first *observed* symptom mark whose intensity is raised by the latent F (a Hawkes-style excitation from a hidden event).

*"Who" in this language.* For an additive (Hawkes) intensity `λ_F(t) = μ_F + Σ_{t_j<t} φ_{F,k_j}(t − t_j)`, the branching posterior `P(parent of F = event j) = φ_{F,k_j}(t* − t_j)/λ_F(t*)` attributes the failure to an earlier step. Summed over the steps of agent a, it attributes the failure to an agent. Section 3, M8 covers this.

### Sanity checks on released data (computed for this note)

All "exact / ±1 / ±3" figures are step-hit rates against the stated label.

**Failure-as-a-Process** (1,184 FAIL, 610 PASS, per-step codes):

- **Code share.** PASS vs FAIL: V 20.1% vs 13.1%, R 8.4% vs 12.7%, C 3.9% vs 2.2%, W 16.4% vs 18.4%. Mean R steps per run: 1.90 vs 5.30.
- **Code at the labelled step** (share, lift over the FAIL base rate):

  | Label | Codes |
  |---|---|
  | `t_err` | W 58.0% (×3.15), X 20.4% (×0.85), E 9.0% (×0.38), P 6.1% (×4.0), V 2.6% (×0.20) |
  | `t_lock` | W 54.6% (×2.96), X 26.4%, C 4.6% (×2.07) |
  | `t_obs` (852 non-null) | X 41.2% (×1.72), V 40.7% (×3.11) |

  Decisive errors sit on write/edit actions; first symptoms sit on verify/execute actions.
- **Localisation of `t_err`:**

  | Method | exact | ±1 | ±3 |
  |---|---|---|---|
  | Position prior (0.31·m) | 10.1 | 25.2 | 45.3 |
  | Random step | 6.3 | 17.4 | 33.4 |
  | First W step | 41.9 | 52.1 | 65.7 |
  | First P or W | 42.7 | 51.3 | 64.9 |
  | First-order PASS-chain, argmax surprisal | 10.9 | 19.6 | 35.0 |
  | Mark-only L1 hazard posterior mode (logistic hazard on (previous, current) code, 5-fold by task) | 7.9 | 16.6 | 32.8 |
  | L0 change-point EM, posterior mode (two first-order chains q0/q1, uniform change prior + "no change", best of 6 seeds) | 29.3 | 37.2 | 47.1 |

- **Localisation of `t_lock`.** Position prior 7.6 / 19.4 / 38.8, PASS-chain surprisal 9.5 / 22.6 / 40.1, first W 28.7 / 39.3 / 51.3.
- **Localisation of `t_obs`.** Position prior 5.2 / 15.1 / 31.2, PASS-chain surprisal 5.0 / 17.7 / 33.6, **first V 23.8 / 37.8 / 48.4**.
- **Trajectory-level FAIL vs PASS AUROC.** Length m alone 0.653, two-chain log-likelihood ratio 0.617 (5-fold by task), mark-only L1 hazard 0.663 (0.675 with position bins), L0 EM P(change) 0.498. The EM fit gives an average posterior probability of 5.4% for "no change": q0 is explore/retry/other-heavy, q1 is edit/verify/claim-heavy.
- **First C with no V in the 3 preceding steps.** PASS 16.3% (n=435), FAIL 28.7% (n=839).

**Who&When** (184):

- **Hand-Crafted (58).** `k*` is a `WebSurfer` message in 55% of logs (lift 2.91) and an `Orchestrator (thought)` in 22% (lift 0.43).
  - Position prior (0.33): exact 3.4%, ±3 24.1%.
  - First WebSurfer step: exact 19.0%, ±1 24.1%, ±3 25.9%.
  - First non-orchestrator, non-human step: 20.7 / 25.9 / 27.6.
  - Role prior for "who": 53.4%.
  - Stall flags: 36 of 58 logs contain a ledger flag (`is_in_loop` true or `is_progress_being_made` false). The first flag comes *after* `k*` in 61%, a median 4.5 steps later, and never exactly at `k*`. It is a `t_obs`-type symptom mark.
- **Algorithm-Generated (126).**
  - Position prior (0.29): 19.8 / 46.0 / 84.1.
  - Step 1: 27.0 / 51.6 / 70.6.
  - Step before the first `Computer_terminal` message (the first code-writing turn): 34.1 / 46.8 / 69.0.

**TraceElephant** (219 with a numeric `k*`):

- **SWE-Agent (44).** `k*` is a source-file `str_replace`/`insert` in 64% (lift 4.1). The first such edit hits 45.5 / 65.9 / 72.7, against position 4.5 / 18.2 / 45.5.
- **Captain-Agent and Magentic-One.** The first step of the most-blamed agent is *worse* than position (9.4 vs 14.1; 3.3 vs 5.6). A token-clock position prior does not help (11.8 vs 14.1; 6.7 vs 5.6).

**Reading.** The marks carry a "first committing action" prior that is 3–10× the position prior on coding and web-browsing systems, but not on the GAIA multi-agent systems of TraceElephant. Mark-only *learned* models do not recover it at L1: the outcome likelihood rewards whatever predicts failure overall (retries, length), not where the error sits. These heuristics were chosen after looking at the lifts on the same data. They must be re-validated on held-out sets (TrajErrBench SWE-Pro, AgentErrorBench, LongRCA, CodeTraceBench) before being reported as baselines.

## Methods

Every mapping follows brief section 7: (a) `x_t`, (b) training data and supervision level, (c) output, (d) target, dataset and metric, (e) the baseline to beat, (f) what breaks. "Mark-structural prior" means the first-committing-action heuristics above.

### A. Neural temporal point processes

#### M1. RMTPP and Neural Hawkes

- **Citations.**
  - Du, Dai, Trivedi, Upadhyay, Gomez-Rodriguez, Song, "Recurrent Marked Temporal Point Processes: Embedding Event History to Vector", KDD 2016, DOI 10.1145/2939672.2939875.
  - Mei & Eisner, "The Neural Hawkes Process: A Neurally Self-Modulating Multivariate Point Process", NeurIPS 2017, arXiv:1612.09328.
- **Mechanism.**
  - RMTPP embeds the history with an RNN, `h_j = RNN(h_{j−1}, [emb(k_j), t_j − t_{j−1}])`. The ground intensity between events is `λ*(t) = exp(v·h_j + w(t − t_j) + b)` and the next mark is `softmax(V h_j)`, so the likelihood is closed-form.
  - Neural Hawkes replaces the RNN with a continuous-time LSTM. Its cell decays between events, `c(t) = c̄_{i} + (c_{i} − c̄_{i}) e^{−δ_i (t − t_i)}` and `h(t) = o_i ⊙ tanh(c(t))`, with `λ_k(t) = f_k(w_kᵀ h(t))` and `f_k` a scaled softplus. Events can therefore excite *or inhibit* each mark, and the compensator is estimated by Monte Carlo.
  - Both are the generic backbone for any "intensity of mark k given the trajectory so far".
- **Mapping.**
  - (a) Event = step. Mark = agent × step type: Failure-as-a-Process code, SymFail `kind`, TRAIL span kind × tool name, or tool name in SearchAuditBench, AgentHallu and TrajErrBench. Time = unit clock, or wall clock (TRAIL, MemTrace), or token clock (TraceElephant non-SWE). Add two terminal marks, SUCCESS_END and FAIL_END.
  - (b) Either L1, likelihood of all runs including the terminal mark, with F as a censored latent mark as in Section 2. Or OAT-style selection: fit on successes, then score failures.
  - (c) Per-step `h_t` / posterior over `t*`, or per-step surprisal `−log λ*(t_i,k_i) + ΔΛ*_i`, and the cumulative compensator `Λ*_F(t)` as a monitor.
  - (d) `t_err` / `t_lock` / `t_obs` on Failure-as-a-Process (exact, ±k), `k*` on Who&When / TraceElephant / TrajErrBench, FAIL vs PASS AUROC on Failure-as-a-Process and AgentHallu (443/250).
  - (e) Position *and* mark-structural priors, and length-only AUROC (0.653 on Failure-as-a-Process).
  - (f) Sequences hold 5–150 events, one per task, so parameters must be pooled across tasks. Under a unit clock the timing part degenerates and the model is a mark language model plus a stopping model. With 8 marks, first-order context does not localise `t_err` (sanity checks), so content covariates are needed. The final step reveals the outcome (last-step shortcut), so mask the terminal mark from the inputs.
- **Supervision.** L1 (or OAT's L1-selected one-class).
- **Code.** Both are implemented in EasyTPP (M4).

#### M2. Transformer Hawkes Process and Self-Attentive Hawkes Process

- **Citations.**
  - Zuo, Jiang, Li, Zhao, Zha, "Transformer Hawkes Process", ICML 2020 (PMLR 119:11692–11702), arXiv:2002.09291.
  - Zhang, Lipani, Kirnap, Yilmaz, "Self-Attentive Hawkes Process", ICML 2020 (PMLR 119:11183–11193), arXiv:1907.07561.
- **Mechanism.**
  - THP self-attends over event embeddings plus a sinusoidal temporal encoding of `t_j`. For t in [t_j, t_{j+1}), `λ_k(t) = softplus_k(α_k (t − t_j)/t_j + w_kᵀ h(t_j) + b_k)`.
  - SAHP encodes time gaps as phase shifts of the sinusoidal positional encoding. Attention summarises the influence of past events into a decaying intensity, and the attention weights "show contributions of each historical event" (abstract).
- **Mapping.**
  - (a) As in M1.
  - (b) L1, with a terminal FAIL/SUCCESS mark.
  - (c) Attention from the FAIL_END position, or from the first symptom mark, to earlier events gives a per-step attribution, and its aggregation by agent gives "who".
  - (d) `k*` / `a*` on Who&When, TraceElephant, LongRCA (Agent Acc and Step Acc / ±5), and `t_err` on Failure-as-a-Process.
  - (e) Role prior (LongRCA 40.3%, Who&When Hand-Crafted 53.4%) plus position and mark-structural priors.
  - (f) Attention is not attribution. A few hundred sequences cannot fit a Transformer. Under a unit clock the temporal encoding is just a positional encoding, so the model is a small LM over marks. It is long-range dependency that LongRCA (median 145 steps) actually needs.
- **Supervision.** L1.
- **Code.** In EasyTPP.

#### M3. Intensity-free TPPs (LogNormMix)

- **Citation.** Shchur, Biloš, Günnemann, "Intensity-Free Learning of Temporal Point Processes", ICLR 2020, arXiv:1909.12127.
- **Mechanism.** Model the inter-event time density directly, `p*(τ) = Σ_c w_c LogNormal(τ; μ_c, s_c)` with `(w, μ, s) = affine(h_j)`, softmax on w and exp on s. Marks are categorical given `h_j` and conditionally independent of τ. The likelihood is exact, and sampling and moments are closed-form, with mean `Σ w_c exp(μ_c + s_c²/2)`. This answers OAT's App. A wish for "exact likelihood via normalising flows" at much lower cost.
- **Mapping.**
  - (a) Only where τ means something: TRAIL span gaps and durations, MemTrace operation gaps, SymFail call latencies, TraceElephant tokens per call as a "duration".
  - (b) L0 on TRAIL (not outcome-selected), or fit on clean spans only.
  - (c) Per-event `−log p*(τ_i) − log p*(k_i)`.
  - (d) TRAIL error spans in the time-sensitive leaves (Resource Abuse 57, Timeout 2, Resource Exhaustion 3, Service Errors 2): span-level set-F1 and per-category recall.
  - (e) A per-span-kind duration quantile rule.
  - (f) Wall-clock time mostly measures provider latency, not agent behaviour. TRAIL has only 148 traces. Its span tree must be flattened in DFS order, which is chronological per the dataset notes.
- **Supervision.** L0.
- **Code.** github.com/shchur/ifl-tpp.

#### M4. EasyTPP (benchmark and library)

- **Citation.** Xue et al., "EasyTPP: Towards Open Benchmarking Temporal Point Processes", ICLR 2024, arXiv:2307.08097.
- **Mechanism.** A unified implementation and evaluation harness. Its GitHub README lists 10 models (RMTPP, NHP, FullyNN, SAHP, THP, IntensityFree, ODETPP, AttNHP, WSMTHP, S2P2) and 8 datasets (synthetic Hawkes, Retweet, Taxi, StackOverflow, Taobao, Amazon, Earthquake, Volcano), under Apache-2.0.
- **Mapping.** This is infrastructure, not a method. Export each attribution dataset as (time_since_start, time_since_last_event, type_event) with a unit or token clock, then run all ten backbones for M1–M3 in one harness. The censored-F loss of Section 2 would have to be added as a custom loss; we did not check whether the library supports censoring.
- **What breaks.** The benchmark datasets have many long sequences per user. Agent data has one short sequence per task.
- **Code.** github.com/ant-research/EasyTemporalPointProcess.

#### M5. LLM-based TPPs with text marks (Language-TPP, TPP-LLM)

- **Citations.**
  - Kong, Zhang, Liu, Tong, Liu, Zhou, "Byte-token Enhanced Language Models for Temporal Point Processes Analysis" (Language-TPP), WWW 2026, arXiv:2502.07139.
  - Liu & Quan, "TPP-LLM: Modeling Temporal Point Processes by Efficiently Fine-Tuning Large Language Models", arXiv:2410.02062 (preprint).
- **Mechanism.**
  - Language-TPP maps inter-event gaps to special byte tokens, so an unmodified LM models (time, event text) jointly.
  - TPP-LLM uses textual event descriptions as marks, with temporal embeddings and PEFT.
- **Mapping.** This is how a TPP can see *content*, which the sanity checks show is needed. The mark is the step text (or a tool call), and the time token is the step gap or a token count.
  - (b) L1, via fine-tuning on runs with a terminal outcome event.
  - (c) Per-step NLL or hazard.
  - (d) As in M1.
  - (f) Fine-tuning cost. Neither paper evaluates anomaly detection or attribution. The approach collapses into "an LM scoring the trajectory", which other slices cover.
- **Supervision.** L1.
- **Code.** Not checked.

### B. Granger causality and influence ("who")

#### M6. Granger causality for Hawkes processes via impact functions

- **Citation.** Xu, Farajtabar, Zha, "Learning Granger Causality for Hawkes Processes", ICML 2016, arXiv:1602.04511.
- **Mechanism.** A multivariate Hawkes intensity `λ_c(t) = μ_c + Σ_{c'} Σ_{t_j<t, c_j=c'} φ_{cc'}(t − t_j)` with `φ_{cc'}(s) = Σ_m a_{cc'm} κ_m(s)` over basis functions κ_m. Type c' does not Granger-cause c iff `φ_{cc'} ≡ 0` iff the group `a_{cc'·} = 0`. The coefficients are learned by maximum likelihood plus a sparse-group-lasso, with optional clustering of event types and adaptive basis selection.
- **Mapping.**
  - (a) Marks = agent roles plus a small set of *symptom* marks derived from observations: tool error or exception, empty return, failed verify, a ledger stall flag, a FAIL_END terminal.
  - (b) L0 for symptom marks, L1 with FAIL_END. Pool all runs of one system.
  - (c) The influence matrix A (roles × marks). Its column for FAIL_END or symptoms ranks roles by their excitation of failure.
  - (d) "Who" (Agent Acc) on Who&When Hand-Crafted (8 fixed role strings), TraceElephant Magentic-One, LongRCA (roles per source; the only long sequences), and Aegis Agent μF1/MF1 (injected agent sets).
  - (e) Role prior: LongRCA 40.3%, Who&When Hand-Crafted 53.4%, Who&When Algorithm-Generated 14.3%.
  - (f) The result is population-level, not instance-level. Algorithm-Generated agent names are task-specific (82 distinct), so map them to role types first. Symptoms are often emitted by the *observer* (ComputerTerminal reports the error), so the Granger parent of a symptom is the last actor, which is right for a local error and wrong for an upstream reasoning error. Episodes of about 10 events give almost no information per pair of types. Episodes are also non-stationary: one-shot and goal-directed.
- **Supervision.** L0/L1.
- **Code.** Not checked. The tick library (Bacry et al., arXiv:1707.03003) provides point-process learners. Its Hawkes-specific learners are known to us but were not re-verified.

#### M7. Integrated-cumulant (kernel-free) causality (NPHC)

- **Citation.** Achab, Bacry, Gaïffas, Mastromatteo, Muzy, "Uncovering Causality from Multivariate Hawkes Integrated Cumulants", JMLR 18(192), 2018; ICML 2017 short version; arXiv:1607.06333.
- **Mechanism.** Estimate the integrated kernel matrix `G = ∫ φ(s) ds` without parametrising kernels, by matching the second- and third-order integrated cumulants. `G_{cc'}` is the expected number of type-c events directly triggered by one type-c' event, which makes it a population "blame matrix".
- **Mapping.** `G_{FAIL, a}` is the expected number of failure or symptom events triggered per event of agent a. Datasets and metrics are as in M6.
- **What breaks.** Cumulant estimation assumes long, stationary realisations, which a 10-event episode is not. It is only plausible on LongRCA (1,140 runs, median 145 steps) or MemTrace operation streams. Low priority.
- **Supervision.** L0.

#### M8. Hawkes branching posterior (latent parent) as per-step and per-agent attribution

- **Citation.** Veen & Schoenberg, "Estimation of space–time branching process models in seismology using an EM-type algorithm", JASA 103(482):614–624, 2008, DOI 10.1198/016214508000000148.
- **Mechanism.** A Hawkes process is a branching (immigrant–offspring) process. The EM algorithm treats each event's parent as latent:
  ```
  P(parent(i) = j) = φ_{k_i k_j}(t_i − t_j) / λ_{k_i}(t_i)
  P(i immigrant)   = μ_{k_i} / λ_{k_i}(t_i)
  ```
- **Mapping.** Evaluate the parent distribution at the FAIL_END event, or at the first symptom mark.
  - Its mass on step j is a per-step attribution score.
  - Its mass summed over agent a's events is a "who" score.
  - Following parents back to the immigrant ancestor gives a root-cause chain. The ancestor is the candidate `k*`, which matches "earliest decisive step".
  - (b) L1 (FAIL_END) or L0 (symptoms).
  - (d) `k*` / `a*` on Who&When, TraceElephant, LongRCA. On SymFail, compare the learned parents with the *recorded* dependency edges and the labelled failure node.
  - (e) Position, mark-structural and role priors.
  - (f) Additive excitation, one F event per sequence, and a kernel on a unit clock. Excitation is not a counterfactual effect, so it must be confirmed by Proposal 1 rollouts.
- **Supervision.** L0/L1.
- **Code.** Not checked; the EM is a few lines of code.

#### M9. CAUSE: Granger causality from neural TPPs via attribution

- **Citation.** Zhang, Panum, Jha, Chalasani, Page, "CAUSE: Learning Granger Causality from Event Sequences using Attribution Methods", ICML 2020 (PMLR 119:11235–11245), arXiv:2002.07906.
- **Mechanism.**
  - Fit a neural point process: a GRU history encoder with a semi-parametric decoder whose intensity is a positive-weighted sum of Gaussian basis functions.
  - Compute *Integrated Gradients* attributions of each past event to the **cumulative intensity** of type k over each inter-event interval.
  - The Granger statistic for k' → k sums those attributions over all type-k' events and divides by the type-k' count. A negative value means inhibition.
- **Mapping.** The *pre-aggregation* event-level attributions are exactly per-step attributions to the FAIL_END or symptom intensity.
  - (a) Mark = agent × step type; content can be added as event features.
  - (b) L1.
  - (c) Per-step IG score, plus a per-agent sum.
  - (d) `k*` (exact, ±k) and `a*` on Who&When, TraceElephant, LongRCA, and Aegis Agent F1.
  - (e) As in M8.
  - (f) IG with a few hundred training sequences is noisy, and the attribution baseline (the "empty history") is arbitrary. Attribution to an intensity is not attribution to the outcome.
- **Supervision.** L1.
- **Code.** github.com/razhangwei/CAUSE.

#### M10. Instance-wise Granger causality (ISAHP)

- **Citation.** Wu, Idé, Kollias, Navratil, Lozano, Abe, Ma, Yu, "Learning Granger Causality from Instance-wise Self-attentive Hawkes Processes", AISTATS 2024 (PMLR 238:415–423), arXiv:2402.03726.
- **Mechanism.** A self-attentive Hawkes model built to satisfy Granger principles at the level of *individual events*, presented as the first neural point process that infers instance-level causality.
- **Mapping.** Identical to M9, but the instance-level design matches the attribution task (one culprit per trajectory) better than type-level Granger. It is the most direct "which step's event raised the failure intensity" model.
- **Supervision.** L1.
- **What breaks.** As in M9.
- **Code.** Not checked.

#### M11. Topological Hawkes Processes

- **Citation.** Cai, Wu, Qiao, Hao, Zhang, Zhang, "THP: Topological Hawkes Processes for Learning Causal Structure on Event Sequences", IEEE TNNLS (accepted), arXiv:2105.10884.
- **Mechanism.** Events occur on the nodes of a known topology. The intensity combines graph convolution over neighbours with temporal convolution, and the causal structure among event types is learned by sparse likelihood optimisation with EM.
- **Mapping.**
  - Topology = the MAS communication graph: Aegis MacNet chain/star/tree/fully-connected topologies and DyLAN graphs, the SymFail dependency graph, the MemTrace bipartite DAG.
  - Marks = component type × status.
  - (d) Aegis (agent, mode) pair F1, and MemTrace operation-category accuracy (the "faulty component").
  - (f) Designed for telecom alarm networks with thousands of events. Aegis injections are synthetic.
- **Supervision.** L0/L1.
- **Code.** Not checked.

### C. Goodness-of-fit, anomaly and change detection for event sequences

#### M12. OoD detection for TPPs with the sum-of-squared-spacings (3S) statistic

- **Citation.** Shchur, Türkmen, Januschowski, Gasthaus, Günnemann, "Detecting Anomalous Event Sequences with Temporal Point Processes", NeurIPS 2021, arXiv:2106.04465.
- **Mechanism.**
  - Apply the compensator, `z_i = Λ*(t_i)`. Under the model, z is a unit-rate Poisson process on [0, V] with `V = Λ*(T)`.
  - The 3S statistic is `ψ = (1/V) Σ_{i=1}^{N+1} (z_i − z_{i−1})²`. Unlike the KS statistics it is sensitive to the event count N.
  - Fit a neural TPP on in-distribution sequences. The OoD p-value comes from the empirical distribution of ψ on held-out in-distribution data, not from the model.
  - Marked TPPs are handled by concatenating the per-mark transformed sequences.
  - On marked data, 3S beat log-likelihood scoring in 9 of 9 cases, including Sock Shop microservice logs with injected faults.
- **Mapping.**
  - (a) Marked sequence; unit clock unless the dataset has times.
  - (b) Fit on successes, the same selection as OAT. This is "L1-selected one-class".
  - (c) A trajectory-level p-value. As a step score, use the largest spacing contribution `w_i²` or the per-mark rescaled gap. A large gap is a stall; a run of tiny gaps is thrash.
  - (d) FAIL vs PASS AUROC on Failure-as-a-Process (1,184/610), AgentHallu (443/250), HORIZON (judge-labelled). TRAIL error-trace vs clean-trace.
  - (e) **Length-only AUROC** (0.653 on Failure-as-a-Process), because 3S responds to N by design. Also the two-chain likelihood ratio (0.617).
  - (f) Task-difficulty confound: failures are longer (median 27 vs 16 steps). The test is trajectory-level only. Under a unit clock most of the power comes from N and mark frequencies.
- **Supervision.** L1-selected.
- **Code.** github.com/shchur/tpp-anomaly-detection.

#### M13. Event outliers: commission and omission

- **Citation.** Liu & Hauskrecht, "Event Outlier Detection in Continuous Time", ICML 2021 (PMLR 139), arXiv:1912.09522.
- **Mechanism.** Two outlier types are defined under a learned TPP, a continuous-time LSTM with contextual event types:
  - *Commission*: an event occurred where it should not. Its score is the negative conditional intensity at the event.
  - *Omission*: an expected event is absent. Its score comes from the intensity mass of the missing type over a window with no such event.
  - The paper gives FDR and FPR bounds.
- **Mapping.** This is the cleanest formalisation of two MAST modes.
  - FM-3.2 missing verification is an *omission* of the V (verify) mark before the C (claim) or final-answer mark: score `Σ_{s∈window} p*(V | H_s)`, or `∫ λ*_V`, over the window before C.
  - FM-3.1 premature termination is a *commission* of C or final-answer at low `λ*_C`.
  - AgentHallu "Missing Required Call" (32 cases) is an omission of a tool-call mark.
  - (b) Fit on PASS runs (L1-selected) or on all runs (L0).
  - (d) Failure-as-a-Process `verification_before_claim` (PASS), `verification_ever` / `first_relevant_verification_step` (FAIL), `tail_dominant_behavior = immediate_claim`. Also MAST-Data FM-3.1 / FM-3.2 (trace-level, LLM judge), TrajErrBench VERIFY.NoVerification / PrematureTermination (step labels), Aegis FM-3.1 / FM-3.2 injections.
  - (e) The rule "first C with no V in the previous 3 steps", which flags 16.3% of PASS and 28.7% of FAIL runs.
  - (f) What "should" happen depends on the task. Omission is only identifiable when the success population is homogeneous. Detecting *verification theatre*, a V that tests the wrong thing, needs content.
- **Supervision.** L1-selected / L0.
- **Code.** Not checked.

#### M14. Time-rescaling residuals

- **Citations.**
  - Brown, Barbieri, Ventura, Kass, Frank, "The Time-Rescaling Theorem and Its Application to Neural Spike Train Data Analysis", Neural Computation 14(2):325–346, 2002, DOI 10.1162/08997660252741149.
  - Rasmussen, "Lecture Notes: Temporal Point Processes and the Conditional Intensity Function", arXiv:1806.00221 (2018), which covers likelihood, simulation and residual analysis.
- **Mechanism.** If the model is right, `u_i = 1 − exp(−(Λ*(t_i) − Λ*(t_{i−1})))` are i.i.d. Uniform(0,1). A KS test on the u's is a goodness-of-fit test, and each `u_i` is a calibrated per-event residual.
- **Mapping.** Per-step residual p-values are a *model-based* replacement for OAT's conformal threshold. A step is flagged when `u_i` is extreme under a TPP fitted on successes. Targets are as in M12 at step level: TRAIL error spans (set-F1), Who&When `k*`. The false-positive guarantee holds per event under the model, not marginally as with conformal prediction.
- **What breaks.** Needs a meaningful clock. Under a unit clock it reduces to a mark-probability residual.
- **Supervision.** L1-selected.

#### M15. Sequential change detection for Hawkes networks (CUSUM)

- **Citation.** Wang, Xie, Xie, Cuozzo, Mak, "Sequential change-point detection for mutually exciting point processes over networks", Technometrics 65(1):44–56, 2023, DOI 10.1080/00401706.2022.2054862, arXiv:2102.05724.
- **Mechanism.** A recursive, memory-efficient CUSUM of the log-likelihood ratio between a post-change Hawkes model (changed influence matrix) and the pre-change model. In our notation it has the form `W_t = max(0, W_{t−1} + log(λ^{(1)}(t_i,k_i)/λ^{(0)}(t_i,k_i)) − ∫(λ^{(1)} − λ^{(0)}))`, with an alarm when `W_t > b`. The paper compares it with Shewhart, GLR and score statistics.
- **Mapping.** This is U3, the prefix monitor.
  - Pre-change = success-regime model, post-change = failure regime (from the L0 EM of M18, or fitted on failed suffixes).
  - (d) Alarm time vs `t_lock` (lead time, recall at a fixed false-alarm rate) on Failure-as-a-Process. FAIL gives detections; PASS gives false alarms. Compare with the paper's prompted monitor (82% precision, 18% recall, median lead 0) and with Dubey 2026 (M22).
  - (f) With median `t_lock` = 12 in runs of 27 steps, the detection delay is a large fraction of the remaining trajectory. The post-change model is unknown, so use GLR or a mixture.
- **Supervision.** L0/L1.
- **Code.** Not checked.

### D. Discrete sequences, logs and clickstreams

#### M16. Classical discrete-sequence anomaly detection

- **Citations.**
  - Chandola, Banerjee, Kumar, "Anomaly Detection for Discrete Sequences: A Survey", IEEE TKDE 24(5):823–839, 2012, DOI 10.1109/TKDE.2010.235.
  - Sun, Chawla, Arunasalam, "Mining for Outliers in Sequential Databases", SDM 2006:94–105, DOI 10.1137/1.9781611972764.9.
  - Forrest, Hofmeyr, Somayaji, Longstaff, "A Sense of Self for Unix Processes", IEEE S&P 1996. Venue confirmed via a course citation; DOI unverified.
- **Mechanism.**
  - The survey distinguishes three problems. (i) Is a whole sequence anomalous with respect to a database of normal sequences? (ii) Which subsequence inside a long sequence is anomalous? (iii) Which pattern has an anomalous frequency?
  - Technique families: kernel/similarity, window-based, Markovian (fixed-order, variable-order, sparse) and HMM.
  - Forrest's window method (later called "stide") scores the fraction of length-k windows absent from the normal database.
  - The probabilistic suffix tree (PST) scores sequences by their normalised probability under a variable-order Markov model trained on normal data. Outliers are separable using only the nodes near the root, keeping under 5% of the tree.
- **Mapping.**
  - (i) is trajectory-level failure detection, (ii) is step localisation (the window with the lowest likelihood), and (iii) is repetition frequency (FM-1.3, `thrash_repeat`).
  - (a) Mark = tool name + hash of the normalised arguments. With FaaP's 8 codes, windows saturate.
  - (b) Successes only (L1-selected).
  - (c) Per-window score; the first or max window is the predicted `k*`.
  - (d) `k*` on TraceElephant, Who&When, TrajErrBench; `t_err` / `t_obs` on Failure-as-a-Process.
  - (e) Position and mark-structural priors.
  - (f) Our first-order chain is the order-1 PST, and it does not beat position for `t_err`. Higher orders need far more than 610 PASS runs.
- **Supervision.** L1-selected.
- **Code.** Standard.

#### M17. Log-key models (DeepLog, LogBERT) with a parsed or clustered event vocabulary

- **Citations.**
  - Du, Li, Zheng, Srikumar, "DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning", CCS 2017:1285–1298, DOI 10.1145/3133956.3134015.
  - Guo, Yuan, Wu, "LogBERT: Log Anomaly Detection via BERT", arXiv:2103.04475.
  - He, Zhu, Zheng, Lyu, "Drain: An Online Log Parsing Approach with Fixed Depth Tree", ICWS 2017 (DOI unverified).
  - Xu, Huang, Fox, Patterson, Jordan, "Detecting Large-Scale System Problems by Mining Console Logs", SOSP 2009 (PCA on per-session message-count vectors; DOI unverified).
  - Le & Zhang, "Log-based Anomaly Detection with Deep Learning: How Far Are We?", ICSE 2022, arXiv:2202.04301, DOI 10.1145/3510003.3510155.
- **Mechanism.**
  - Drain groups raw messages into templates (log keys) with a fixed-depth parse tree, so the event vocabulary is *learned* from text.
  - DeepLog's LSTM predicts the next key and flags the actual key if it is not in the top-g predictions. It also has a parameter-value model and a workflow model for diagnosis.
  - LogBERT is a self-supervised BERT trained on normal key sequences.
  - Xu et al. use count vectors and PCA residuals, which work at session level only.
  - Le & Zhang show that results depend heavily on training-data selection, data grouping, class balance, label noise and early-detection settings, and that no model "always works well".
- **Mapping.**
  - (a) Key = Drain template of the step's action string (tool name + command head), or k-means cluster of OAT's 64-d step embeddings. This is the "event vocabulary learned by clustering".
  - (b) Successes only (L1-selected; DeepLog trains on normal sessions).
  - (c) A per-step top-g miss flag; the first miss is the predicted `k*`.
  - (d) TraceElephant, Who&When, TrajErrBench, SearchAuditBench `k*` (exact, ±k, tolerance-span hit).
  - (e) Mark-structural priors.
  - (f) Log benchmarks have up to millions of sessions; here there are hundreds. A top-g miss fires on rare but legal keys (Le & Zhang's critique carries over).
- **Supervision.** L1-selected.
- **Code.** LogADEmpirical (github.com/LogIntelligence/LogADEmpirical) re-implements DeepLog and others.

### E. Hidden Markov, semi-Markov and switching-state models

#### M18. HMM, HSMM and recurrent HSMM as the L0 change-point mixture

- **Citations.**
  - Rabiner, "A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition", Proc. IEEE 77(2):257–286, 1989 (IEEE Xplore doc. 18626, i.e. DOI 10.1109/5.18626).
  - Yu, "Hidden Semi-Markov Models", Artificial Intelligence 174(2):215–243, 2010, DOI 10.1016/j.artint.2009.11.011.
  - Dai, Dai, Zhang, Li, Song, "Recurrent Hidden Semi-Markov Model", ICLR 2017.
- **Mechanism.**
  - An HMM has `p(x) = Σ_z π_{z_1} Π A_{z_{t−1} z_t} Π b_{z_t}(x_t)`, fitted by forward–backward and Baum–Welch EM.
  - The change-point mixture of U2 is a **left-to-right two-state HMM with an absorbing post-change state**, with `A = [[1−ρ, ρ],[0, 1]]` and autoregressive emissions `q_s(x_t | x_{t−1})`. The forward–backward pair posterior `P(z_{t−1}=0, z_t=1 | x)` is exactly `P(t* = t | x)`.
  - A constant ρ gives a geometric prior on t*, i.e. a constant hazard.
  - An HSMM replaces the geometric sojourn with an explicit duration law `p(d | z)`. The switching hazard `p(d)/P(D ≥ d)` then depends on time in state, which is a discrete hazard.
  - The R-HSMM puts an RNN emission inside each segment; exact EM becomes too costly, so it uses variational inference.
  - A three-state left-to-right HSMM {healthy, erroneous, locked} encodes (`t_err`, `t_lock`).
- **Mapping.**
  - (a) Per-step mark plus observation flags (error, empty, repeated command), or embeddings for R-HSMM.
  - (b) L0: EM with outcomes hidden. Or **L1 by constraint**: successful runs are forbidden from entering the post-change state. This partially supervised HMM is the bridge between U1 and U2.
  - (c) Posterior over change points and state marginals.
  - (d) `t_err` / `t_lock` / `t_obs` on Failure-as-a-Process, `k*` on Who&When and TraceElephant, MP-Bench consensus ranking (nDCG@5).
  - (e) Position and mark-structural priors.
  - (f) Identifiability. Our L0 fit on Failure-as-a-Process found the explore→edit phase split: average posterior P(no change) 5.4%, outcome AUROC 0.498. It still hits `t_err` in 29.3% (vs position 10.1%), but only because the decisive error is often the first edit, which the plain "first W" rule gets 41.9% of the time. The report's warning ("planning versus execution phase") is confirmed on real data. Use marks that separate symptoms from phases (error flags, repeats).
- **Supervision.** L0 / L1 by constraint.
- **Code.** hmmlearn and ssm (github.com/lindermanlab/ssm); both are standard, but availability was not re-checked.

#### M19. Switching linear dynamical systems and recurrent SLDS

- **Citations.**
  - Fox, Sudderth, Jordan, Willsky, "Bayesian Nonparametric Inference of Switching Dynamic Linear Models", IEEE TSP, DOI 10.1109/TSP.2010.2102756, arXiv:1003.3829.
  - Linderman, Johnson, Miller, Adams, Blei, Paninski, "Bayesian Learning and Inference in Recurrent Switching Linear Dynamical Systems", AISTATS 2017 (PMLR 54:914–922), arXiv:1610.08466.
- **Mechanism.**
  - An SLDS has continuous dynamics `x_t = A_{z_t} x_{t−1} + b_{z_t} + ε` and a Markov regime `z_t`. Fox et al. put an HDP prior on the number of regimes, with ARD.
  - The rSLDS makes switching depend on the continuous state, `p(z_{t+1} | z_t, x_t) = softmax(R x_t + r_{z_t})`, with Pólya-gamma augmentation for fast Bayesian inference.
- **Mapping.** This is OAT's continuous-embedding view made regime-switching and causal.
  - (a) OAT's `h_t`, PCA to 64 d, from a proxy LLM.
  - (b) L0 on all runs, or L1 with the success constraint of M18.
  - (c) `P(z_t = failure regime)`. In the rSLDS, `p(z_{t+1} = fail | x_t)` is a hazard that is logistic in the embedding, i.e. Proposal 2's `h_θ` with linear dynamics.
  - (d) `k*` on Who&When (OOD, as in OAT), TraceElephant, TrajErrBench, AgentHallu (with its 250 clean runs), and SearchAuditBench tolerance spans.
  - (e) OAT top-3 0.45 and AUROC 0.76 on Who&When, plus position and mark-structural priors.
  - (f) Linear dynamics over 64-d jumps between heterogeneous steps (tool call → observation) are a poor fit. Regimes may track agent identity (who speaks) rather than error, so condition on the mark (agent id) as an input.
- **Supervision.** L0/L1.
- **Code.** ssm library (Linderman lab), not re-verified.

#### M20. Bayesian online change-point detection (BOCPD)

- **Citation.** Adams & MacKay, "Bayesian Online Changepoint Detection", arXiv:0710.3742 (2007). It is already cited by the report for U2.
- **Mechanism.** Track the run length `r_t` online. The joint `P(r_t, x_{1:t}) = Σ_{r_{t−1}} P(r_t | r_{t−1}) P(x_t | r_{t−1}, x^{(r)}) P(r_{t−1}, x_{1:t−1})`, with growth probability `1 − H(r_{t−1})` and change probability `H(r_{t−1})`. H is a *hazard function*; a constant `1/λ` gives a geometric prior. Exact message passing assumes that parameters before and after a change are independent.
- **Mapping.** BOCPD with a learned, covariate-dependent `H = h_θ(τ_{<t}, s_t)` *is* Proposal 2's hazard used online (U3).
  - (a) Mark + observation flags, or embeddings.
  - (c) `P(r_t = 0)` per step, and a MAP change point.
  - (d) Lead time vs `t_lock` on Failure-as-a-Process; `k*` on Who&When.
  - (f) "Post-change parameters independent" means the failure regime is modelled as generic novelty, so it is again a `t_obs` detector. Several changes (recovered errors in PASS runs: 2.3 per run) cause false alarms.
- **Supervision.** L0.
- **Code.** Many implementations.

### F. 2024–2026 work on agent traces as event sequences

#### M21. Automata from agent traces (FSM + success-model surprisal)

- **Citation.** Cho, Cardenoso Fernandez, Mohammed, Wu, Da Costa, Wicaksono, Koshiyama, "Automata from Agent Traces: Failure and Next-Step Prediction", arXiv:2608.23670 (Aug 2026, preprint).
- **Mechanism.**
  - Steps are symbolised by deterministic rules in priority order: tool-call function name, then `[ACTION]` tag, then the first command token's category, then a `role:content-type` fallback.
  - A directly-follows automaton is built from a trie by merging states with the same last activity, then pruning singleton transitions. This gives 7–43 states on 12 datasets, including Who&When, tau2-bench (airline, retail, telecom), SWE-agent and WebArena.
  - Per-step surprise is `−log₂ P̂(a_t | q_t)`. Trace cross-entropy under a success-only model is `CE⁺`, and `CE⁻ − CE⁺` separates the outcomes.
  - The cumulative log-likelihood ratio `L_t` declares failure online.
  - Failure AUROC reaches 0.941 (tau2 telecom), and is 0.903 on WebArena and 0.799 on SWE-agent. On SWE-agent, 50% of the trace gives 92% of full-trace AUROC.
  - Who&When is included only structurally: 9 states, 8 activity types, and "only failure traces … failure prediction undefined".
  - Appendix H.10 reports per-state error-rate differentials (e.g. SWE-agent `edit:text` 0.368 vs 0.486) and a first success/failure divergence at the edit-vs-search branch, but **no step localisation against any attribution label**.
- **Mapping.** This is exactly the "transition-matrix surprise under a success model" baseline the brief asks for.
  - (a) Tool name or role:content-type.
  - (b) Successes only (L1-selected).
  - (c) Per-step surprise.
  - (d) Argmax surprise vs `k*` on TrajErrBench tau2 (the same environment as their tau2 FSMs), TraceElephant SWE-Agent, Who&When. Note that the authors' own observation that edit-state transitions separate outcomes matches the "first source edit" prior (45.5% on TraceElephant SWE).
  - (e) Mark-structural priors.
  - (f) Our first-order analogue on Failure-as-a-Process is below position for `t_err` and above it for `t_lock` / `t_obs`, so expect a symptom detector.
- **Supervision.** L1-selected.
- **Code.** No link found.

#### M22. One-class telemetry monitor with echo-state networks and CUSUM

- **Citation.** Dubey, "Real-Time Detection and Repair of LLM Agent Failures", arXiv:2608.02464 (Aug 2026, preprint).
- **Mechanism.**
  - Per-step telemetry `x_t = [e_t; u_t; m_t]`: a 32-d char-3-gram hash embedding, 4 token-surprisal aggregates, and an action one-hot with log latency, output length and an error flag. Later versions add behavioural and grounding features.
  - Per channel, a frozen random reservoir `h_t = (1−α)h_{t−1} + α tanh(W h_{t−1} + W_in x_t)` with a ridge readout predicting the next step, trained on healthy runs only.
  - Surprise `q_t` is the normalised one-step MSE. A one-sided CUSUM `S_t = max(0, S_{t−1} + z(q_t) − κ)` is maxed over channels, with the threshold at the (1−β) healthy quantile.
  - Results: 0.71 detection at 5% false alarms and AUROC 0.872 on 2,823 own episodes; 0.745 on AFTraj-2K and 0.779 on ATBench without retraining; cold transfer 0.527.
  - The alarm typically fires one step after a verified onset. Rollback-and-rerun recovers 45% of failures, against 16% for resampling.
- **Mapping.** This is the closest existing system to U3 with a TPP-style input: marks (action one-hot) plus timing (latency) plus an error flag.
  - (b) L1-selected.
  - (c) Alarm time.
  - (d) Lead time vs `t_lock` / `t_obs` on Failure-as-a-Process (needs step text, so it requires re-collected Terminal-Bench runs), or on replayable tau2 and SWE runs.
  - (e) A memoryless Mahalanobis score (the paper's own baseline), plus position.
  - (f) It fires at onset, i.e. `t_obs`, not `t_err`. A per-deployment healthy null is needed.
- **Supervision.** L1-selected.
- **Code.** github.com/sunnydubey1111/agent-trajectory-sentinel.

#### M23. Absorbing Markov chains of agent traces (TraceToChain)

- **Citation.** Tran-Truong & Le, "Measuring the Unmeasurable: Markov Chain Reliability for LLM Agents", arXiv:2604.24579 (Apr 2026, preprint).
- **Mechanism.** Cluster steps into an automatic taxonomy. Fit an absorbing DTMC `(Q̂, R̂⊕, R̂⊖)` (transient block plus success and failure absorption) by Laplace-smoothed maximum likelihood, and derive the first-passage success-time distribution. Pass@k, pass^k and reliability-decay curves are projections of it. Validation uses AIC, a KS test on the first-passage CDF (p > 0.05 on 7 of 7 frameworks), and Dirichlet and bootstrap intervals.
- **Mapping.** The absorbing chain is a discrete-time hazard model whose hazard depends only on the current mark: `h_t = R̂⊖[s_t]`. Hence `P(absorbed via ⊖ at t | fail)` is a ready-made attribution posterior that the paper does not compute.
  - (d) `t_lock` on Failure-as-a-Process (absorption = lock-in), `k*` on Who&When.
  - (f) A first-order Markov, mark-only hazard. Our analogous mark-only hazard was below position.
- **Supervision.** L1.
- **Code.** Not stated.

#### M24. Action-alphabet n-gram and transition studies

- **Citations.**
  - Deng, "Your Agent Has a Genome: Sequence-Level Behavioral Analysis and Runtime Governance of LLM-Powered Autonomous Agents", arXiv:2606.15579 (preprint).
  - Bouzenia & Pradel, "Understanding Software Engineering Agents: A Study of Thought-Action-Result Trajectories", ASE 2025, arXiv:2506.18824.
- **Mechanism.**
  - Deng encodes steps with a 4-letter alphabet: X explore, E execute, P plan, V verify. Note the letters clash with Failure-as-a-Process's codes.
  - Findings: Markov transition matrix and n-gram mining; E→V transitions 2.1% ("verification deficit"); trigram P-X-P lowers success by 10.4%; P-ratio r = −0.256 with success.
  - A three-layer runtime governor (rules, a statistical accumulator, a χ²-based threshold) raised success by 6.2 pp in a before/after deployment, not a controlled trial. The patterns reportedly replicate on 2,000 SWE-agent trajectories.
  - Bouzenia & Pradel unify 120 trajectories (2,822 LLM interactions) of RepairAgent, AutoCodeRover and OpenHands, and report action motifs that distinguish success from failure. The specific repetition findings appear in a search summary but were not verified in the full text.
- **Mapping.** n-gram motif counts and transition frequencies are covariates for the hazard (M1) and statistics for Section 4.
  - (d) Failure-as-a-Process `tail_dominant_behavior` (`thrash_repeat`, `verification_theater`, `immediate_claim`) and MAST-Data FM-1.3 / FM-3.2.
  - (f) Correlational. These are trajectory-level, not step-level, results.
- **Supervision.** L1.
- **Code.** Deng releases a toolkit; Bouzenia & Pradel release data.

#### M25. Prefix monitors with key-step labels and the limits of early signals

- **Citations.**
  - Pan, Shen, Lu, Ding, Cheng, Wang, "Monitoring Web Agents Without Internal Signals: Observable Trajectories and Key-Step Supervision", arXiv:2609.02057 (Sep 2026, preprint).
  - Li, Yu, Zang, Zhuang, Mo, Gan, "Last Step Matters: Early Uncertainty Cannot Predict Failure in Long-Horizon Agents", EMNLP 2026, arXiv:2608.29685.
  - Li, Li, Zhang, Tang, Huang, "TRACES: Proactive Safety Auditing for Multi-Turn LLM Agents via Trajectory-State Modeling", EMNLP 2026, arXiv:2605.27690.
- **Mechanism.**
  - Pan et al. label each prefix "on track" until a *key-step boundary*, the first uncorrected critical error linked to failure. This is a `t_lock`-style event time used as an L2 hazard label. They use macro (cross-step behaviour and feedback) and micro (consistency across repeated black-box queries) features on WebArena-Lite and Online-Mind2Web.
  - Li et al. find verbal confidence reaches AUROC 0.85 at completion, but no signal exceeds 0.60 at 50% progress on deep-research agents. They attribute this to "path switching", i.e. regime changes.
  - TRACES learns prefix-level risk states from observer-LLM hidden states with trajectory-level labels only (an L1 hazard analogue, for safety).
- **Mapping.** These calibrate what U3 can expect. Hazard monitors trained with `t_lock`-type labels (Pan) are the L2 upper reference for the L0/L1 monitors of M15, M20 and M22. Li et al.'s path switching is an HMM regime phenomenon, and it predicts small lead times.
  - (d) Lead time on Failure-as-a-Process and HORIZON's 294 web runs with step labels.
- **Supervision.** L1/L2.
- **Code.** Not checked.

#### M26. Hawkes and HMM models of LLM conversations and reliability (adjacent)

- **Citations.**
  - Ross & Deutsch, "The Ancestor Hawkes Process with an Application to Group Chat Data", arXiv:2605.02613. A multivariate Hawkes in which an event's impact depends on whether it initiated a cluster; marks are sender identity only; 9-person group chat.
  - Deng, Ye, Xie, "HawkesLLM: Semantic Uncertainty Propagation in Agentic Text Simulation", arXiv:2605.23043 (ICML 2026 workshop). A multivariate Hawkes over text-generating agent nodes selects which earlier outputs condition later prompts.
  - Chakherlou, Khastgir, Popov, Zhao, "Modeling Memory-Dependent Reliability of LLMs: A Hidden Markov Model", arXiv:2607.22951. A latent interaction state generates correct/incorrect outcomes in sequential sessions.
- **Mapping.**
  - Ross & Deutsch is the closest published Hawkes model to multi-agent message logs. Its "initiator vs follow-up" distinction is the immigrant/offspring split of M8, applied to who-starts-a-cascade.
  - HawkesLLM uses Hawkes excitation for *simulation*, not diagnosis.
  - Chakherlou et al. is an HMM over outcome sequences, not steps.
  - None targets attribution.

#### M27. Supervised trajectory anomaly and onset localisers (for contrast)

- **Citations.**
  - Liu et al., "TrajAD: Trajectory Anomaly Detection for Trustworthy LLM Agents", arXiv:2602.06443. Step-level localisation trained with process supervision on the perturb-and-complete TrajBench.
  - Li et al., "CodeTracer: Towards Traceable Agent States", arXiv:2604.11641. Reconstructs state transitions as a hierarchical trace tree and localises failure onset on CodeTraceBench. It is the source of 71% of Failure-as-a-Process trajectories.
  - Zheng et al., "Leveraging Trajectory Graphs for Pre-Execution Error Diagnosis in Agentic LLM Systems", arXiv:2607.27443. A probabilistic graph of historical trajectories plus a GNN flags failure-prone action patterns before execution; +14.69% average pass ratio.
- **Mapping.** These are L2 or supervised comparators. Trajectory Graph Copilot is the only one that learns sequential action patterns that "lead to failure", a mark-transition hazard. CodeTraceBench is a held-out set for the mark-structural priors.

## Structural failure modes as event-pattern statistics

This is the identifiability map for U2: which failure modes leave a footprint in the mark or observation stream, the statistic that detects each, and the dataset that can score it. "Identifiable at L0" means a change-point or OOD model with no outcome labels can in principle flag it, because the mode changes the *event pattern*, not just content.

| Mode | Event-sequence statistic | TPP / sequence reading | Datasets and labels that score it | Identifiable at L0? |
|---|---|---|---|---|
| **MAST FM-1.3 step repetition** | `rep_t = 1[∃ s<t: key(s) = key(t)]` with `key = (agent, tool, normalised args)`. Longest run of identical consecutive marks. Count of R (retry) codes. SearchAuditBench: repeated query or URL in `tool_arguments` | Self-excitation `α_kk` (branching ratio of a mark on itself) above the success-population value. 3S with many tiny rescaled gaps | MAST-Data FM-1.3 (trace-level, LLM judge); Aegis FM-1.3 injections ("add redundant steps"; agent label); Failure-as-a-Process `forewarning_types ∋ repeated_command`, tail `thrash_repeat`, R code (R steps per run 1.90 PASS vs 5.30 FAIL); TrajErrBench VERIFY.InfiniteRetry; TRAIL Resource Abuse | **Yes.** Pure action-stream pattern; usually a symptom after `k*` (`t_obs`-type) |
| **MAST FM-1.5 unaware of termination conditions** | Activity after success evidence: steps after the first passing V, or events after a C mark. Hitting the step cap. Who&When Hand-Crafted `Orchestrator (termination condition)` mark position | Omission of C when `λ*_C` (under the success model) is high. Length above the success quantile | MAST-Data FM-1.5; Aegis FM-1.5; AgentErrorBench (30-step cap); Who&When Hand-Crafted | **Partly.** Length is confounded with task difficulty (length-only AUROC 0.653 on Failure-as-a-Process) |
| **MAST FM-3.1 premature termination** | C / final-answer mark with fewer than q evidence events (E/X/V, search/visit) before it, against the success-population quantile per task type. Final answer directly after a failed or empty observation | Commission outlier: `−log λ*_C(t_C)` (M13) | Failure-as-a-Process tail `immediate_claim`; TrajErrBench VERIFY.PrematureTermination; SearchAuditBench (the final answer is the critical step in 16.9%); Who&When ("didn't find enough information … but directly gave the answer"); MAST-Data and Aegis FM-3.1 | **Yes** for the structural part; "was the evidence sufficient?" needs content |
| **MAST FM-3.2 no / incomplete verification** | `1[no V mark in (t_C − w, t_C)]`; first C with no V in the previous 3 steps: PASS 16.3% vs FAIL 28.7% on Failure-as-a-Process. Who&When Algorithm-Generated: no `Verification_Expert` turn before the final answer | Omission outlier: `Σ_{s∈window} p*(V | H_s)` with V absent (M13) | Failure-as-a-Process `verification_before_claim` (PASS), `verification_ever`, `first_relevant_verification_step` (FAIL), tail `verification_theater`; MAST-Data and Aegis FM-3.2; TrajErrBench VERIFY.NoVerification | **Yes** for absence. **No** for verification theatre or FM-3.3 incorrect verification (content) |
| **AgentRx "Invalid Invocation"** | First tool-call event whose observation has error status: exception text, HTTP or schema error, "invalid"/"not found" returns. TRAIL `status_code`; SymFail `error` node kind / `tool_failure_count` | Commission outlier on the joint mark (tool, status = error). Intensity of error marks excited by the preceding call | AgentRx (rare: 0–2.2% of critical labels per domain in the paper; 1 root cause and 5 failure events in the 73 public records); TrajErrBench ACT.ToolSchemaMismatch (8, 1.6%); AgentHallu "Incorrect Tool Arguments" (36); TRAIL Tool-related / Tool Selection errors; SymFail | **Yes.** The observation stream changes (the report's U2 prediction). The *invalid call* is the step before the error observation, so localisation is "error mark − 1" |
| **TRAIL Resource Abuse** (excessive tool calls; annotators mark the **last** instance) | Count of TOOL spans per CHAIN step, or TOOL-mark intensity over a sliding window, above the success quantile. Per-span duration | Excess ground intensity of the TOOL mark (M3, M15). The labelled span is the *end* of the burst, so detect the change *back* to normal and take the last burst event | TRAIL (57 annotated Resource Abuse spans: 39 GAIA, 18 SWE), set-F1 at span level. Also Resource Exhaustion (3) and Timeout (2) | **Yes** (timing and counts). TRAIL is the only dataset with real durations |
| **Stalled progress** | Magentic-One ledger flags `is_in_loop = true` or `is_progress_being_made = false`, present in all 58 Who&When Hand-Crafted logs and 74 TraceElephant Magentic-One GAIA runs; flagged in 36 of 58 Hand-Crafted logs. The first flag comes after `k*` in 61%, a median 4.5 steps later | A self-reported symptom mark. Its Hawkes parent (M8) or the last WebSurfer action before it is a `k*` candidate | Who&When Hand-Crafted, TraceElephant Magentic-One (`k*`); Failure-as-a-Process `cosmetic_progress` / `new_wrong_direction` tails | **Yes** (as a symptom). It gives `t_obs`, not `t_err` |
| **Decisive wrong edit / first committing action** (not a MAST mode, but the dominant footprint) | First W step; first source edit; first web action; turn before the first code execution | A phase change in the mark process (the L0 EM finds it) | Failure-as-a-Process `t_err` (first W 41.9% exact); TraceElephant SWE `k*` (45.5%); Who&When Hand-Crafted (19.0%) and Algorithm-Generated (34.1%) | **Locatable but not detectable.** The phase change happens in successes too, so it gives *where*, not *whether* (EM outcome AUROC 0.498) |

**Summary.** Repetition, invalid invocation, resource abuse, stalls and absent verification are event-pattern modes, so they are identifiable at L0. They mostly mark `t_obs`; the decisive step is their parent. Premature and unaware termination are identifiable only relative to a success-population norm, which requires L1 selection. Errors that live in content (wrong inference, misread output, incorrect verification, hallucinated summaries) are not identifiable from marks. In Failure-as-a-Process, `misread_output` is a `trigger_mechanism` whose `t_err` typically falls on the *following* W step, so marks localise it only via the first-committing-action prior.

## Ranked recommendations

Gains are measured where we computed them (marked "measured") and are otherwise our expectation. Baselines: position = relative-position prior; mark = mark-structural prior.

| # | Method | Benchmark(s) | Target label | Supervision | Expected gain over OAT / position prior | Effort | Risk |
|---|---|---|---|---|---|---|---|
| 1 | **Mark-structural priors as mandatory baselines** (first W / first source edit / first web action / turn before first code execution; per-dataset mark lift table) | Failure-as-a-Process, TraceElephant-SWE, Who&When; validate on TrajErrBench SWE-Pro, AgentErrorBench, LongRCA, CodeTraceBench | `t_err`, `k*` | none (rule) | Measured exact-hit gain over position: +31.8 pp (Failure-as-a-Process), +41.0 pp (TraceElephant SWE), +15.6 pp (Who&When Hand-Crafted), +14.3 pp (Who&When Algorithm-Generated). OAT reports no such baseline | S | Chosen post hoc on test data. May partly reflect an annotation convention ("decisive = first wrong commit"). No gain on GAIA multi-agent systems in TraceElephant |
| 2 | **Censored marked-TPP hazard** (cloglog head; neural TPP backbone from EasyTPP; marks × content covariates such as observation error flags and step-embedding PCA; FAIL as a latent censored mark) | Failure-as-a-Process (marks only, L1), AgentHallu (443/250), freshly generated tau2 / SWE / Terminal-Bench runs; evaluate on Who&When, TraceElephant, TrajErrBench | `k*`, `t_err`, `t_lock`; FAIL vs PASS AUROC | L1 (+L1+ via prefix rollouts) | Mark-only version measured *below* position (7.9% vs 10.1% exact). With content covariates, expected to beat position; it must beat the mark prior to matter. Unlike OAT it is causal and calibrated | M | Last-step and length shortcuts (length-only AUROC 0.653). The hazard learns "failure-prone context", not location |
| 3 | **Omission / commission scores for verification and termination** (Liu & Hauskrecht scores under a PASS-fitted mark model) | Failure-as-a-Process (`verification_before_claim`, `immediate_claim`), MAST-Data FM-3.1/3.2, TrajErrBench VERIFY.*, Aegis FM-3.x, AgentHallu "Missing Required Call" | Mode presence (trace-level F1), the C step | L1-selected | A rule baseline already separates (C without V: 16.3% PASS vs 28.7% FAIL). Expect higher precision with intensity-weighted windows. OAT cannot express omissions | S | Task-dependent norms. Verification theatre is invisible |
| 4 | **Hawkes branching posterior / CAUSE / ISAHP for "who"** (symptom marks and FAIL_END; parent chain to the immigrant root) | LongRCA (long sequences, role labels), Who&When Hand-Crafted, TraceElephant Magentic-One; SymFail (compare parents with recorded dependency edges) | `a*` (Agent Acc), `k*` | L0/L1 | Must beat the role prior (LongRCA 40.3%, Who&When Hand-Crafted 53.4%). Plausible on LongRCA; unclear on 10-step logs | M | Symptoms are emitted by observers; population vs instance mismatch; Algorithm-Generated names are task-specific |
| 5 | **Constrained HMM / HSMM change-point mixture** (U2 and its L1-constrained version) with symptom-aware marks (error, empty, repeat, stall flags) | Failure-as-a-Process; Who&When Hand-Crafted (ledger flags); TRAIL | `t_err`, `t_lock`, `t_obs`; per-mode recall | L0, and L1 by constraint | Measured L0 on marks: 29.3% exact on `t_err` (vs 10.1% position, below the 41.9% first-W rule), outcome AUROC 0.498. Worth running as the identifiability experiment, not as a detector | M | Converges to phase splits (confirmed). Needs symptom marks to align with failure |
| 6 | **CUSUM / BOCPD prefix monitor** (TPP or chain log-likelihood ratio; compare with Dubey's ESN+CUSUM) | Failure-as-a-Process (`t_lock` lead time; PASS for false alarms); replayable tau2 / Terminal-Bench | `t_lock`, `t_obs` | L1-selected / L0 | Measured surprise is near position for `t_lock` (22.6 vs 19.4 ±1). Expect detection near `t_obs` with small lead (cf. Li et al.: no early signal above 0.60 AUROC at 50% progress) | S | Short remaining horizon; recovered errors in PASS runs (2.3 per run) cause false alarms |
| 7 | **3S / time-rescaling GoF on real-time traces** (intensity-free TPP on spans) | TRAIL (timestamps, durations, status), MemTrace (`created_at`) | TRAIL error spans (Resource Abuse, Timeout), MemTrace operation | L0 | Unknown. The only place where the "time" in TPP carries information | S–M | 148 TRAIL traces, not outcome-selected; latency reflects providers, not agents |
| 8 | **FSM / PST / DeepLog success-model surprisal** (Cho et al. symbolisation; Drain or k-means vocabulary) | TrajErrBench tau2, TraceElephant SWE, Who&When | `k*`, `t_obs` | L1-selected | Measured first-order version below position for `t_err` (19.6 vs 25.2 ±1); slightly above for `t_obs` (17.7 vs 15.1). Expect the same `t_obs` bias as OAT App. H | S | Small success sets; rare-but-legal keys |

## Open gaps

1. **No paper applies TPPs, Hawkes processes or Granger influence to agent trajectories for attribution.** Searches on 2026-10-30 found Hawkes only in agent *simulation* (HawkesLLM; Hawkes-driven email-network agents, arXiv:2605.12507, not further verified) and human group chat (Ancestor Hawkes). Agent-trace sequence work (Cho et al., Dubey, TraceToChain, Deng) reports trajectory-level prediction, not step localisation against Who&When / TraceElephant / TrajErrBench labels.
2. **No dataset combines outcomes, step content and real time.** Failure-as-a-Process has both outcome classes and step-type marks but no text and no timestamps. TRAIL has timestamps and durations but is not outcome-selected (148 traces). TraceElephant and Who&When release failures only. A re-collected Terminal-Bench / tau2 corpus with OpenTelemetry spans, both outcomes and Failure-as-a-Process-style codes would serve M1–M3, M12–M15 and U1–U3 at once.
3. **The mark vocabulary is not standardised.** Datasets expose agent names, span kinds, node kinds, tool names or action codes, each in a different scheme. Failure-as-a-Process's 8-code codebook and Cho et al.'s deterministic symbolisation rules are two candidates for a cross-dataset step-type tagger. The mark-structural priors (Section 2) depend on such a tagger (W = write/edit, "source edit", "first web action").
4. **Mark-structural priors are unreported and unvalidated.** Every attribution method, OAT included, should be compared against "first committing action" priors. These priors may also reveal an annotation convention, i.e. that `t_err` / `k*` is defined as the first wrong commit. Test them on held-out sets and in a counterfactual check (Proposal 1): is the first edit decisive when replaced?
5. **Annotation leakage in Failure-as-a-Process segments.** `t_err` falls on an `action_segments` boundary in 87.8% of runs vs 55.5% by chance. Any model fed segment structure, rather than per-step codes, leaks the label.
6. **Population vs instance.** Granger and Hawkes theory estimates type-level influence from long stationary streams. Agent logs are short, one per task, and goal-directed. Instance-level variants (branching posterior, CAUSE event attributions, ISAHP) exist, but their accuracy at 5–30 events per sequence is unknown.
7. **Symptom vs cause.** Every L0/L1-selected detector in this slice (surprise, 3S, CUSUM, BOCPD, omission) fires on observable symptoms: verify/execute marks, stall flags, error returns. They give `t_obs` in Failure-as-a-Process terms. The decisive step is the *parent* of the first symptom. The Hawkes branching posterior is the only formal mechanism here for walking back from symptom to cause, and it is untested.
8. **What is "time" for an agent?** Wall-clock time mixes provider latency with agent behaviour. A token clock (cumulative tokens) did not improve the position prior on TraceElephant. A progress clock (fraction of subgoals done) would be the meaningful time axis, but no dataset records it.

## Verified references (arXiv id / DOI)

Neural TPPs:
- Du et al. 2016, RMTPP, KDD, DOI 10.1145/2939672.2939875
- Mei & Eisner 2017, Neural Hawkes, NeurIPS, arXiv:1612.09328
- Zuo et al. 2020, THP, ICML, arXiv:2002.09291
- Zhang et al. 2020, SAHP, ICML, arXiv:1907.07561
- Shchur, Biloš, Günnemann 2020, Intensity-free TPPs, ICLR, arXiv:1909.12127
- Shchur, Türkmen, Januschowski, Günnemann 2021, Neural TPPs review, IJCAI, arXiv:2104.03528
- Xue et al. 2024, EasyTPP, ICLR, arXiv:2307.08097
- Rasmussen 2018, lecture notes, arXiv:1806.00221
- Kirchner 2017, "An estimation procedure for the Hawkes process" (binned Hawkes ↔ INAR(p) / VAR(p)), Quantitative Finance 17:571–595, arXiv:1509.02017
- Kong et al. 2026, Language-TPP, WWW, arXiv:2502.07139
- Liu & Quan 2024, TPP-LLM, arXiv:2410.02062

Granger causality and influence:
- Xu, Farajtabar, Zha 2016, ICML, arXiv:1602.04511
- Achab et al. 2018, NPHC, JMLR 18(192), arXiv:1607.06333
- Zhang et al. 2020, CAUSE, ICML, arXiv:2002.07906
- Wu et al. 2024, ISAHP, AISTATS, arXiv:2402.03726
- Cai et al., Topological Hawkes, IEEE TNNLS, arXiv:2105.10884
- Veen & Schoenberg 2008, Hawkes EM / branching, JASA, DOI 10.1198/016214508000000148
- Bacry et al., tick, arXiv:1707.03003

Goodness-of-fit, anomaly and change detection:
- Shchur et al. 2021, NeurIPS, arXiv:2106.04465
- Liu & Hauskrecht 2021, ICML, arXiv:1912.09522
- Brown et al. 2002, Neural Computation, DOI 10.1162/08997660252741149
- Wang, Xie, Xie, Cuozzo, Mak 2023, Technometrics, DOI 10.1080/00401706.2022.2054862, arXiv:2102.05724
- Prentice & Gloeckler 1978, Biometrics 34:57–67 (DOI not confirmed)

Discrete sequences and logs:
- Chandola, Banerjee, Kumar 2012, TKDE, DOI 10.1109/TKDE.2010.235
- Sun, Chawla, Arunasalam 2006, SDM, DOI 10.1137/1.9781611972764.9
- Forrest et al. 1996, IEEE S&P (DOI unverified)
- Du et al. 2017, DeepLog, CCS, DOI 10.1145/3133956.3134015
- Guo, Yuan, Wu 2021, LogBERT, arXiv:2103.04475
- He et al. 2017, Drain, ICWS (DOI unverified)
- Xu et al. 2009, SOSP (DOI unverified)
- Le & Zhang 2022, ICSE, arXiv:2202.04301

HMM and switching models:
- Rabiner 1989, Proc. IEEE 77(2) (IEEE doc 18626)
- Yu 2010, HSMM, AIJ, DOI 10.1016/j.artint.2009.11.011
- Dai et al. 2017, R-HSMM, ICLR (arXiv id not checked)
- Fox et al. 2011, IEEE TSP, DOI 10.1109/TSP.2010.2102756, arXiv:1003.3829
- Linderman et al. 2017, rSLDS, AISTATS, arXiv:1610.08466
- Adams & MacKay 2007, BOCPD, arXiv:0710.3742

Agent traces (2025–2026; mostly preprints):
- Cho et al., arXiv:2608.23670
- Dubey, arXiv:2608.02464
- Tran-Truong & Le, arXiv:2604.24579
- Deng, arXiv:2606.15579
- Bouzenia & Pradel, ASE 2025, arXiv:2506.18824
- Pan et al., arXiv:2609.02057
- Li et al., EMNLP 2026, arXiv:2608.29685
- TRACES, EMNLP 2026, arXiv:2605.27690
- Ross & Deutsch, arXiv:2605.02613
- HawkesLLM, arXiv:2605.23043
- Chakherlou et al., arXiv:2607.22951
- TrajAD, arXiv:2602.06443
- CodeTracer, arXiv:2604.11641
- Trajectory Graph Copilot, arXiv:2607.27443
