# Cluster A: causation and credit as the formal object behind "the decisive step"

2026-11-01. Maps X1–X12 / H1–H13 (`findings/hypotheses.md`) onto actual causation, degrees of responsibility, causal
abstraction, counterfactual multi-agent credit, hindsight credit, heterogeneous treatment effects and the identifiability of a
cause from logs. RUDDER, HCA, CCA, COMA, Shapley-Q, EPV and Causal Agent Replay are already written up in
`notes/lit_timeseries/lit_F_temporal_attribution_credit.md` (§3.2, §3.2b, §3.4) and are cross-referenced, not re-derived.
Tags: VERIFIED-abs = arXiv/DOI abstract page read this session; VERIFIED-search = bibliographic record only; UNVERIFIED =
from memory.

Notation: run `τ = (s_0, a_1, o_1, …, a_T, o_T)`, outcome `S ∈ {0,1}`, label step `k*` and agent `a*`,
`V(h_t) = P(S=1 | resume from prefix h_t)` (EPV's prefix value, lit_F §2).

---

## A1. Actual causation: Halpern–Pearl (2005, 2015), preemption, overdetermination, normality

**References.** Halpern & Pearl, "Causes and Explanations: A Structural-Model Approach, Part I: Causes", BJPS 56 (2005),
arXiv:cs/0011012 (VERIFIED-search; UAI 2001 version arXiv:1301.2275). Halpern, "A Modification of the Halpern–Pearl
Definition of Causality", IJCAI 2015, arXiv:1505.00162 (VERIFIED-abs). Halpern & Hitchcock, "Graded Causation and
Defaults", BJPS, arXiv:1309.1226 (VERIFIED-abs). Halpern, *Actual Causality*, MIT Press 2016 (UNVERIFIED).

**Formal object.** Causal model `M = (U, V, F)`, context `u`, candidate cause `X = x`, effect `φ`. HP-2015: `X = x` is an
actual cause of `φ` iff AC1 `(M,u) ⊨ X=x ∧ φ`; AC2 there is a set `W ⊆ V∖X` and a value `x'` such that, with `W` *frozen at
its actual values* `w*`, `(M,u) ⊨ [X←x', W←w*] ¬φ`; AC3 `X` is minimal. `W = ∅` is a but-for cause; a non-empty `W` is a
witness neutralising a back-up route. HP-2005 let `W` take non-actual values, which admitted spurious causes; 2015 forbids
that and lowers complexity. Test cases: *early preemption* (back-up never fires; freezing it makes the first cause but-for),
*late preemption* (both fire; the first to arrive is the cause, the second frozen at "arrived late"), *symmetric
overdetermination* (two sufficient causes; under HP-2015 neither is a cause alone, the pair is). Halpern–Hitchcock add a
normality ranking: witnesses must be at least as normal as the actual world, and a cause whose counterfactual replaces an
action by its default/norm is graded higher. HP causation is not transitive.

**Correspondence.** The chain proposal → commitment → symptom → claim → lock-in (X2) is a chain of endogenous variables; each
link is a but-for cause of `S=0` when the downstream chain is deterministic (EPV: `V` does not drop at 66% of judge labels,
so most judge labels are not but-for, lit_F §3.4). HP says every X2 convention names an actual cause; datasets differ in a
*selection* rule HP leaves open and Halpern–Hitchcock fill with normality. H2 (blame the acceptance step) is that rule: the
"request satisfied" ledger violates a norm, the failed page load is an exogenous abnormality, so the acceptance is graded
higher. X3 (omission → commission): the omission is a cause with `W = {later fabrication}` frozen; AgentRx's recovered/root
split (25/26 WebSurfer omissions "recovered", 22/73 roots = orchestrator acceptance) is a hand-applied normality ordering. X6
is early preemption's mirror: an event is not a cause while the recovery route fires, so the cause sits on the transition
(H8). Exhaustion runs (13/58 Who&When HC, 69 SymFail C2, 7–24 adherence repeats) are symmetric overdetermination: no repeat
is but-for, HP returns the set, and each team picks a member by convention.

**Where it breaks.** (i) HP needs `F`; a log is one draw of a stochastic policy, so `[X←x']` is a replay and replay is
non-deterministic (SymTrace: 39/54 successes fail on one of three re-runs, `lit/known_phenomena.md`). (ii) The contrast
`x'` (delete / no-op / oracle / resample) is the "default" HP leaves to the modeller, the same open gap as lit_F §6.9.
(iii) HP has no "no cause" class except "all exogenous", so X9 environment failures and H4's no-decisive-step runs are
outside it.

**Prediction and pilot.** Prediction: the convention gap is normality, not position. On the 44 AgentRx Magentic-One logs,
the root is the earliest *norm-violating* flagged step (acceptance / misinterpretation / invention / adherence) rather than
the earliest flagged step in ≥ 15 of the 17 logs with root ≠ first failure (`results/agentrx/stats.txt`: 17 logs, median gap
2, max 20). Pilot, no model calls: tag each entry of `labels.extra['failures']` (`loaders/agentrx.py`) as exogenous
(tool / page / guardrail) or norm-violating and count; repeat on MP-Bench `extra.per_annotator` to see whether the 3-vote
steps (median relative position 0.82, 24% FINAL ANSWER) are the earliest norm violation or the last chance. Refuted if the
root is simply the earliest flagged step.

**Verdict: exact instance for the *definition* of k\*, useful analogy for its computation.** The disagreement is about
selecting among several actual causes, which is what HP + normality formalise; the equations exist only through replay (A7).

**Prior applications.** No 2025–2026 LLM-agent paper in A8 invokes HP by name (abstract-level check). A2P (arXiv:2509.10401,
VERIFIED-abs) runs abduce → minimal intervention → counterfactual prediction in one LLM pass (Who&When AG 47.46% vs 16.67%,
HC 29.31% vs 12.07%): AC2 performed by the model's imagination instead of replay. Formal predecessors outside LLMs: Datta,
Garg, Kaynar, Sharma, Sinha, "Program Actions as Actual Causes: A Building Block for Accountability", CSF 2015,
arXiv:1505.01131 (VERIFIED-abs; actual cause of a safety violation on interacting-program logs, cause separated from blame)
and Gössler & Le Métayer, "A general framework for blaming in component-based systems", Sci. Comput. Program. 113:223–235,
2015 (VERIFIED-search; blame on component traces by counterfactual trace substitution). Both assume a per-component
specification of correct behaviour, i.e. the oracle X11 lacks.

---

## A2. Degrees of responsibility and blame (Chockler & Halpern 2004), Dec-POMDP extension

**References.** Chockler & Halpern, "Responsibility and Blame: A Structural-Model Approach", JAIR 22 (2004),
arXiv:cs/0312038 (VERIFIED-abs). Triantafyllou, Singla, Radanovic, "Actual Causality and Responsibility Attribution in
Decentralized Partially Observable MDPs", AIES 2022, arXiv:2204.00302 (VERIFIED-abs). Triantafyllou & Radanovic, AAMAS 2023,
arXiv:2302.12676 (VERIFIED-search; RA-MCTS).

**Formal object.** Responsibility of `X=x` for `φ` is `1/(k+1)`, `k` = minimal number of other variables that must change
before `X=x` is but-for (11–0 vote: each voter 1/6; 6–5: each 1). Blame = expected responsibility over the agent's epistemic
state. The Dec-POMDP papers embed agents' actions over time in an SCM, show HP-style definitions misfire when actions are
causally dependent across agents, define responsibility through the number of actual causes an agent participates in, and
approximate it by MCTS.

**Correspondence.** `k` repeated searches give each repeat `1/(k+1)`: X1's flat symptom field is the responsibility profile
of an overdetermined failure. X4 is the Dec-POMDP point: the specialist's recorded step is responsible only through the
orchestrator's instruction, and a definition blind to inter-agent dependence credits the recorder (TraceElephant 30/90 golds
under the specialist's name). Blame-as-expectation is X5/H13 inverted: the annotator's epistemic state contains the hidden
object location / user goal / failing test and assigns responsibility 1 to a step the attributor's state cannot distinguish
from a reasonable one (prefix monitor calls the gold "reasonable" in 12/20 AgentErrorBench, 8/20 TrajErrBench). H10's ±1
tolerance is a responsibility fact: ledger / instruction / next-speaker copies have `k = 0` jointly, `k = 2` singly.

**Where it breaks.** `k` counts variables, so it depends on step granularity (SymFail duplicates every call and labels one
copy in 357/536); blame needs an epistemic distribution no dataset records.

**Prediction and pilot.** Prediction: cross-team agreement falls with responsibility spread. On the 44 Who&When-HC × AgentRx
shared logs (`results/who_and_when/overlap_rows.json`: `ww_step`, `rx_root`, `rx_all`, `n`), |ww_step − rx_root| has
Spearman ≥ 0.4 with the near-duplicate-action count (`inspect/who_and_when_signals.py` `rep` detector,
`results/who_and_when/signals.txt`), and the 16/44 exact agreements concentrate in runs with ≤ 1 repeat. A 30-line script.
Refuted if agreement is independent of repeat count.

**Verdict: exact instance.** `1/(k+1)` is the right object for loops and for decision-unit tolerance; only `F` is missing.

**Prior applications.** None on LLM agents. EPV's share `ρ_t = Δ_t/p(x)` (lit_F §3.4) is a replay-defined analogue summing to
one.

---

## A3. Causal abstraction (Rubenstein et al. 2017; Beckers & Halpern 2019)

**References.** Beckers & Halpern, "Abstracting Causal Models", AAAI 2019, arXiv:1812.03789 (VERIFIED-abs). Rubenstein et
al., "Causal Consistency of Structural Equation Models", UAI 2017 (UNVERIFIED id).

**Formal object.** Low-level `M_L`, high-level `M_H`, map `τ: V_L → V_H`; `M_H` abstracts `M_L` if every allowed low-level
intervention `i` has a high-level `ω(i)` with `τ(M_L[do(i)]) = M_H[do(ω(i))]` (interventions commute with `τ`).
Beckers–Halpern order exact transformation < uniform transformation < abstraction < strong abstraction and show that merging
micro-variables into macro-variables is a strong abstraction.

**Correspondence.** H10 and X4 are abstraction questions: ledger → instruction → next-speaker are three low-level variables
with one macro-variable "orchestrator decision at round r", and the right `τ` assigns it to the prompt owner, not the thread
it was logged under. SWE-Agent "agents" that are tool names (225/1,551 mismatches) are a `τ` that is not an abstraction:
intervening on the tool does not commute with intervening on the caller. TraceElephant's gold following the recorded name in
218/219 runs is a low-level label under the instrumentation's `τ`.

**Where it breaks.** The theory tests whether a `τ` is consistent, not which is right, and a text log offers no interventions
to test commutation; the choice stays a convention, now explicit.

**Prediction and pilot.** Prediction: mapping predictions and golds through one `τ` (merge triples by round; assign Magentic
ledger calls to the Orchestrator) raises every Who&When-HC exact score by 5–10 pp and the judge's TraceElephant-Magentic agent
accuracy by ≥ 10 pp. Pilot: re-score `results/who_and_when/all_at_once_std.jsonl` and
`results/traceelephant/all_at_once_std.jsonl` with a `τ` built from `step.agent` and `step.meta['last_input']`. Refuted if
the gain is < 2 pp (misses are not within-triple).

**Verdict: useful analogy.** A legitimacy test for the collapse (interventions must commute), not an estimator.

**Prior applications.** CHIEF (arXiv:2602.23701, VERIFIED-abs) builds a hierarchical causal graph from flat logs before
attributing on Who&When, with no consistency check; Semantic Cooperative Games (arXiv:2607.18255, VERIFIED-abs) define a
semantic hypergraph as a macro-level of the message log.

---

## A4. Counterfactual credit in cooperative MARL: difference rewards, WLU, LOO, Shapley ("who")

**References.** Wolpert & Tumer, "An Introduction to Collective Intelligence", arXiv:cs/9908014 (VERIFIED-abs; formula below
UNVERIFIED, PDF unreadable) and "Optimal Payoff Functions for Members of Collectives", Adv. Complex Syst. 4(2/3):265–279,
2001 (VERIFIED-search). COMA, Shapley-Q, Shapley counterfactual credits: lit_F §3.2b.

**Formal object.** World utility `G(z)`; agent `η`'s Wonderful Life Utility `WLU_η(z) = G(z) − G(CL_η(z))`, `CL_η` clamping
`η`'s component to a null vector ("as if η never existed"); the 2001 paper derives the optimal clamp and the Aristocrat
Utility (clamp to the expected action). WLU is *factored* (improving it improves `G`) and more *learnable* (higher
signal-to-noise) than the team reward `G`. COMA replaces the clamp by a critic-marginalised baseline; Shapley averages the
marginal contribution over coalitions; leave-one-out is WLU with clamp = removal.

**Correspondence.** `G = S`; players = agents gives `a*`, players = steps gives `k*` / `E`. X4's instrumentation label clamps
the wrong variable (removing the specialist's logged turn leaves the orchestrator's decision). X10's verifier PASS has
`WLU ≈ 0`, which is H11 as a theorem. Learnability explains why agent-level scores (63–95%, §1) exceed step-level ones: the
agent difference signal aggregates steps. Exhaustion runs have `WLU ≈ 0` for every agent, H4's no-attributable-step class.

**Where it breaks.** (i) The clamp changes the protocol: deleting an orchestrator message breaks the next-speaker loop, so
`G(CL_η(z))` is undefined, not 0. (ii) Without replay the critic `Q(prefix, joint message)` inherits A5's hindsight bias.
(iii) Shapley efficiency forces blame to sum to the failure, redistributing environment failures (X9) onto agents, which is
what SymFail and LongRCA labels do by hand.

**Prediction and pilot.** Prediction: on Aegis (temperature-0 baselines; 2,359 rows with an injected step) LOO-replay names
an agent in `faulty_agents` in ≥ 90% of rows, while on Who&When-HC the judge's 63% agent accuracy does not beat "agent with
most steps after the first ledger no-progress flag". Cheapest pilot without replay, one call per (row, agent): a model-based
WLU on the 102 Magentic logs, `argmax_η [P̂(S=1 | redact η) − P̂(S=1)]` from the judge, scored against gold agent and against
last-speaker / most-messages baselines. If it does not beat them, the critic route is dead and only replay remains for "who".

**Verdict: exact instance for "who" under replay; useful analogy via a critic.** The object is right; the clamp is undefined
on message protocols without a harness.

**Prior applications.** Ma et al. (arXiv:2509.08682, VERIFIED-abs): Shapley over agents plus a "performance causal inversion
principle" on Who&When and TRAIL, ≤ 36.2% step accuracy, no position baseline in the abstract. SHARP (arXiv:2602.08335,
VERIFIED-search): Shapley credit for *training*. Yang et al., arXiv:2511.10687 (VERIFIED-abs, NeurIPS 2025 LAW workshop):
Shapley for success credit, "first-error localization" for blame, conceptual, no data. Causal Agent Replay
(arXiv:2606.08275, lit_F §3.4): MC-Shapley over steps with replay, synthetic SCMs only.

---

## A5. Hindsight and counterfactual credit assignment ("when"): the annotator as a hindsight model

**References.** HCA, arXiv:1912.02503; CCA, arXiv:2011.09464 (both VERIFIED in lit_F §3.2 with estimators). Only the
correspondence is new.

**Formal object (recalled).** HCA credit `c(a|x,Z) = 1 − π(a|x)/h_z(a|x,Z)`, `h_z` the hindsight distribution of the action
given the return. CCA baseline `V(x, Φ)` with a hindsight statistic `Φ` constrained to be independent of the action given the
state, separating skill from luck.

**Correspondence.** X5 says the annotator *is* `h_z`: given `S = 0` and the evaluator's verdict, which action is most
likely under failure, a different object from `π(a|x)` (what a prefix reader judges reasonable). H13's unflaggable set is
`{t : π(a_t|x_t) high, h_z(a_t|x_t,S=0) high}`, where HCA credit is small because failure does not change the action's
likelihood: exploration-order labels in AgentErrorBench depend on the object location, a `U` variable. CCA's `Φ ⊥ A_t | X_t`
names the X9/X11 problem: the hidden user goal, flaky test and `__SHOPPING__` placeholder are `Φ`, and the step should be
credited only for the residual. H9's invented failure is `h_z` evaluated at a guessed `Z`.

**Where it breaks.** Temperature-0 agents give `π(a|x) ≈ 1` and the ratio degenerates (lit_F §3.2 (f)); `Φ` is not
independent of the action when the user simulator reacts to the agent.

**Prediction and pilot.** Prediction: judge exact accuracy on records where the prefix monitor judged the gold "reasonable"
(`results/<slug>/prefix_probe.jsonl`, `scores[gold].mistake == false`) is ≥ 15 pp below its accuracy on the remaining
records of the same dataset (AgentErrorBench, TrajErrBench, HORIZON), and supplying `Φ` changes *which* step more than
accuracy (TrajErrBench zh goal: 16/50 predictions change, 22/50 correct either way). Pilot: join `prefix_probe.jsonl` with
`all_at_once_std.jsonl` per slug.

**Verdict: exact instance of the label-generating process, useful analogy as an estimator.** HCA/CCA describe what annotators
compute; they do not supply `Φ`.

**Prior applications.** None beyond lit_F's return decomposers (SPA-RL, implicit PRM, LaRe), which are not hindsight-ratio
estimators.

---

## A6. Heterogeneous treatment effects / uplift for X6 ("same event, different fate")

**References.** Künzel, Sekhon, Bickel, Yu, "Meta-learners for estimating heterogeneous treatment effects using machine
learning", PNAS 2019, arXiv:1706.03461 (VERIFIED-abs). Wager & Athey, "Estimation and inference of heterogeneous treatment
effects using random forests", JASA 2018, arXiv:1510.04342 (VERIFIED-abs). Gutierrez & Gérardy, "Causal inference and uplift
modelling: a review of the literature", PMLR 67:1–13, 2017 (VERIFIED-search).

**Formal object.** Units with covariates `x`, binary treatment `w`, outcome `y`; CATE `τ(x) = E[Y(1) − Y(0) | X = x]`.
T-/S-/X-learners (X-learner efficient when one arm is much larger), causal forests (pointwise consistent, asymptotically
Gaussian under unconfoundedness, honest splitting). Uplift modelling targets the same quantity via two-model, class
transformation or direct methods. Assumptions: unconfoundedness `(Y(0),Y(1)) ⊥ W | X` and overlap.

**Correspondence.** Unit = (run, event); `w` = "error event of type c at step t"; `y = S`; `x` = (task, position, *response
at t+1*). X6's numbers are marginal ATEs by type: TRAIL formatting / instruction / orchestration errors have `P(correct)
0.28–0.29` vs base 0.29 (ATE ≈ 0), retrieval 0.13 and tool-hallucination 0.17 (ATE ≈ −0.15); FaP PASS runs carry 2.3 events
at the same relative position as FAIL `t_err` (0.28 vs 0.31). H8 is the HTE claim: `τ(x)` is large when the response repeats
or paraphrases and ≈ 0 when it changes strategy. The step to blame is the one with the largest individual effect, not the one
with an event.

**Where it breaks.** Unconfoundedness fails: hard tasks produce both errors and failures (HORIZON pass/fail separation is
length and early stop, AUROC 0.87–0.91 on `n_steps`), so ATEs are biased unless task identity is in `x`; FaP's 58 matched
tasks (`results/failure_as_process/g3_stats.md`, "matched design") are the within-task fix. Overlap fails for categories that
occur only in failures.

**Prediction and pilot.** Prediction: within task, the CATE of an error event is ≈ 0 given "next action changes strategy"
and ≤ −0.3 given "next action repeats / paraphrases", on TRAIL (`extra.errors`, 117 GAIA traces, 34 correct) and AgentHallu
(693 runs; tool errors 33.6% clean vs 40.4% hallucinated). Pilot: a T-learner (two logistic models) over (category, position,
task, response-type regex) with bootstrap CIs, loaders only. Refuted if the CATE is flat in response type.

**Verdict: exact instance** of X6/H8, with the known failure mode (task confounding) already visible in HORIZON.

**Prior applications.** None found on LLM-agent failure data.

---

## A7. Identifiability of the decisive step: observational logs vs interventional replays

**References.** Tian & Pearl, "Probabilities of Causation: Bounds and Identification", UAI 2000 / Ann. Math. AI 28:287–313,
DOI 10.1023/A:1018912507879, arXiv:1301.3898 (VERIFIED-search; journal volume UNVERIFIED, Springer page gated). Oberst &
Sontag, "Counterfactual Off-Policy Evaluation with Gumbel-Max Structural Causal Models", ICML 2019, arXiv:1905.05824
(VERIFIED-abs). EPV, arXiv:2610.17633 (lit_F).

**Formal object.** Probability of necessity `PN = P(Y_{x'} = y' | X = x, Y = y)` ("had the step been different, would the
failure have been avoided, given it was taken and the run failed"), sufficiency `PS`, `PNS`. From observational data alone,
under exogeneity, `max{0, (P(y|x) − P(y|x'))/P(y|x)} ≤ PN ≤ min{1, P(y'|x')/P(y|x)}`; experimental `P(y_x), P(y_{x'})`
tighten the bounds; under *monotonicity* (the step never helps) `PN = (P(y) − P(y_{x'}))/P(x,y)` is point-identified.
Oberst–Sontag: in a finite POMDP the counterfactual *trajectory* is not identified by the transition kernel; it needs an SCM
for the noise (Gumbel-max is one choice satisfying counterfactual stability), so replayed counterfactuals carry an
unverifiable modelling assumption even with a simulator.

**Correspondence.** "Was step k decisive?" is `PN` for `X = a_k`. Logs are observational; replays (AgenTracer, EPV, Causal
Agent Replay, TraceElephant dynamic) are the experimental arm. Monotonicity says correcting a step cannot make the run fail,
contradicted by SymTrace's 39/54 re-run flips. Oberst–Sontag's point is X8's "loyal continuations": an injected-then-replayed
run fixes the noise differently from a natural run, so counterfactual-with-ground-truth labels (TracerTraj) converge on the
final answer (42%) because the implicit SCM resamples everything downstream.

**Where it breaks.** PN is a population quantity over runs sharing `(x, y)`; one trajectory has `n = 1`, so instance-level PN
needs replays of *that* prefix (EPV's `K = 8/32` restarts), still under an SCM choice.

**Prediction and pilot.** Prediction: on FaP's 1,794 runs with `x` = "an error event before relative position 0.4" (PASS
events in `labels.extra`, FAIL `t_err`), `P(y|x)` and `P(y|x')` differ by < 0.1, so the Tian–Pearl lower bound on PN is
< 0.15 and the upper bound > 0.9: the logs do not identify whether early events are necessary causes, X6 stated as a bound.
Pilot: ten lines over `loaders/failure_as_process.py`; recompute within the 58 matched tasks to see whether stratification
tightens it. Refuted if the lower bound exceeds 0.5 (then logs identify causes and replays are a luxury).

**Verdict: exact instance.** PN/PS is the quantity every "decisive step" label asserts; the bounds state what a log can
and cannot support.

**Prior applications.** EPV is the interventional estimator (`Δ_t`, PNR). MRFR / Graph-Constrained Joint Replay
(arXiv:2608.29228, VERIFIED-abs) recovers all inclusion-minimal event sets whose replay restores success (Family Exact Match
1.000 on 120 synthetic DAGs and 24 LLM cases, 52–55% fewer replays than exhaustive search): PNS over sets, the only paper
treating overdetermination explicitly. CausalFlow (arXiv:2605.25338, VERIFIED-abs): step-level Causal Responsibility Score by
counterfactual intervention on single-agent traces, no numbers in the abstract. None states its SCM assumption or reports PN
bounds.

---

## A8. Prior LLM-agent work using these principles (novelty check)

| paper | id | principle | data / numbers | tag |
|---|---|---|---|---|
| Who&When (ICML 2025) | 2505.00212 | LLM judge formats | 184 logs | lit_F |
| AgenTracer | 2509.03312 | oracle-action replay to generate labels | +18.18 pp Who&When | lit_F |
| A2P | 2509.10401 | AC2 test inside one LLM pass | WW-AG 47.46 / HC 29.31 | abs |
| Ma et al. | 2509.08682 | Shapley over agents + causal discovery | Who&When, TRAIL, ≤ 36.2% | abs |
| EPV | 2610.17633 | replay prefix value, shares, PNR | SWE-bench Verified, 47 + 60 failures | lit_F |
| Yang et al. | 2511.10687 | Shapley credit + first-error blame, conceptual | none | abs |
| CHIEF | 2602.23701 | hierarchical causal graph + counterfactual screening | Who&When, "beats 8 baselines" | abs |
| CausalFlow | 2605.25338 | step counterfactual responsibility score | 4 single-agent benchmarks | abs |
| Causal Agent Replay | 2606.08275 | SCM do(), point-of-commitment, MC-Shapley over steps | synthetic SCMs | lit_F |
| Semantic Cooperative Games | 2607.18255 | Shapley on semantic hypergraph (contribution) | medical benchmark, −93.3% cost | abs |
| AgentLocate (COLM 2026) | 2607.07989 | LLM judge + multi-evaluator verification | two unnamed benchmarks | abs |
| MRFR / GCJR | 2608.29228 | minimal repair families by joint replay | 120 DAGs + 24 LLM cases, FEM 1.000 | abs |

Absent from all abstracts: Halpern–Pearl or Chockler–Halpern by name; normality as the selection rule among multiple causes;
PN/PS bounds from logs; HTE on event–response pairs; any comparison of a counterfactual method against a position prior
(H5/H7). "Counterfactual replay finds the step" and "Shapley over agents" are taken.

---

## Summary (principle → fit)

1. A1 Actual causation (HP-2015 + normality): **exact instance** of the k\* definition and the convention problem
   (X2/X3/H2/H6); computable only by replay.
2. A2 Responsibility `1/(k+1)` and blame: **exact instance** for loops / overdetermination (X1, H4, H10) and for hindsight
   labels as blame ≠ responsibility (X5/H13).
3. A3 Causal abstraction: **useful analogy** for decision-unit collapse and record-owner vs decision-owner (H10, X4).
4. A4 Difference rewards / WLU / LOO / Shapley: **exact instance for "who" under replay, useful analogy via a critic**;
   clamp undefined on message protocols; verifier steps have zero credit (H11).
5. A5 HCA / CCA: **exact instance of the label-generating process** (annotator = hindsight distribution, X5/H9/H13); as an
   estimator needs the hidden `Φ`.
6. A6 HTE / uplift: **exact instance** of X6/H8 (CATE conditional on the response); task confounding is the known failure
   mode, FaP matched tasks the fix.
7. A7 Probabilities of causation + SCM choice: **exact instance**; a log bounds PN, a replay identifies it only under
   monotonicity and an SCM assumption.
8. Pilots on cached files: normality vs position on AgentRx roots (A1); agreement vs repeat count on 44 shared logs (A2);
   τ-collapsed re-scoring (A3); model-based WLU vs last-speaker on 102 Magentic logs (A4); accuracy split by "gold judged
   reasonable" (A5); response-conditional CATE on TRAIL/AgentHallu (A6); PN bounds on FaP (A7).
9. Novelty: replay and Shapley-over-agents are taken; normality selection, responsibility grading, PN bounds and
   response-conditional HTE on agent logs are open.
