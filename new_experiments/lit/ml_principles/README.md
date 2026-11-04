# Which ML principles model the attribution problems: synthesis

2026-11-01. Three cluster notes (`A_causation_credit.md`, `B_labels_abstention.md`, `C_shift_shortcuts_structure.md`)
map the twelve phenomena and thirteen hypotheses of `findings/hypotheses.md` onto twenty existing principles, each with
verified references, an explicit variable correspondence, the point where the correspondence breaks, a falsifiable
prediction on a named dataset and a pilot that runs on the cached loaders and results. The earlier time-series survey
(`notes/lit_timeseries/README.md`) already covers hazard / survival, change-point, MIL / PU, RUDDER, point processes,
conformal monitors, process mining, spectrum localisation and CIRCA; this note does not repeat those.

Fit scale: **exact** = our object is literally theirs (same variables, same estimator applies); **analogy** = the
framing and one estimator transfer, a key assumption does not; **superficial** = shared vocabulary only.

## 1. The decomposition

The inspection found one problem that looks like "find the step" and is in fact seven problems with different homes:

| # | sub-problem | what the data showed | principle (fit) | file |
|---|---|---|---|---|
| 1 | **What "the decisive step" means** | every convention names a different point on the chain proposal → commitment → symptom → claim (X2); loops are overdetermined (X1); recovered errors (X6); omission/commission pairs (X3) | Halpern–Pearl actual causation + Halpern–Hitchcock normality (**exact** for the definition); Chockler–Halpern responsibility 1/(k+1) (**exact** for loops and ±1 tolerance); Tian–Pearl probabilities of causation (**exact**: a log *bounds* PN, only replay identifies it, and only under monotonicity and an SCM choice) | A1, A2, A7 |
| 2 | **What a label is** | labels are stop rules; three teams disagree on the same logs; annotators are outcome-informed; one "second annotator" is synthetic (X2, X5, §4) | human label variation / jury learning / labelling functions on a *monotone chain* latent (**exact** for evaluation, analogy for learning); hindsight-credit (HCA/CCA) as the label-generating process (**exact**); multi-annotator noise models over signed-offset buckets (analogy); examination-hypothesis click models for consensus-vs-position (analogy) | B3, A5, B1, B5 |
| 3 | **What the output space is** | 20–80% of runs per dataset have no decisive step: exhaustion, environment, artefact (X9, X12, H4) | selective prediction / reject option with named reject classes + open-set for exhaustion (**exact** for the output space and risk–coverage reporting; superficial as an LLM-confidence threshold) | B6 |
| 4 | **How to find a cause that is an omission** | the gap, not the step, is the error; the actor on the record is not the decider (X3, X4, H3, H2) | dynamic slicing / forward slice / where-provenance / taint through *control* dependence (**exact** on lineage logs such as MemTrace and string-carried items; analogy on free text, where dependence must be estimated) | C3 |
| 5 | **Which signal distinguishes failure** | successes carry the same error events; what differs is the response (X6, H8) | heterogeneous treatment effect conditional on the response (**exact**, with task confounding as the known failure mode); matched-anchor contrastive design over (obs, next action) (**exact** sampling design, loss immaterial) | A6, C6 |
| 6 | **Why injected data misleads** | last-step and seam priors; injected steps contradict their prefix; loyal continuations (X7, X8, H7) | shortcut learning + partial-input baselines (**exact**; Xu & Gao 2610.17747 already run the audit on WWP/Aegis); domain-adaptation bounds (analogy: the λ term says no joint hypothesis exists because the *label definition* changes — task shift, not distribution shift) | C1, C2 |
| 7 | **Where the oracle comes from for silent failures** | 65% of τ² failures have no transcript symptom; terminal artefacts are rule-shaped (X11, X12, H4b, H11) | specification mining + runtime verification / policy-as-automaton (**exact** for policy clauses and artefacts; *not monitorable* for hidden-goal and hindsight labels — H13 is a liveness property on a finite prefix) | C7 |

Two further mappings are weaker: regime-switching / mixture-of-experts gating for H4 is **superficial** (no gate
supervision; it reduces to a classifier followed by per-class rules), and HSMM phase models for H12 are an **analogy**
that works through sojourn hazards, not emissions (the time-series note already showed emissions find phases, not failure).
Causal abstraction (Beckers–Halpern) gives the legitimacy test for collapsing decision triples (H10): interventions must
commute with the collapse map.

## 2. What follows for method design

- **Attribution is a selection among actual causes, so the convention must be an input.** HP says every point on the chain
  is an actual cause once the downstream chain is deterministic; the datasets differ in a selection rule, which
  Halpern–Hitchcock formalise as normality (blame the norm-violating step: H2's acceptance step). A method should output
  the chain (or its graded responsibility profile) and be scored per convention (H6), with jury-style reporting (B3).
- **"Late bias" has a formal reading.** The prefix monitor is Matsuura's strict temporal masking: it answers "is this step
  wrong given the past", which is π(a|x). The annotator and the holistic judge compute the hindsight distribution
  h_z(a|x, S=0). The unflaggable set of H13 is where π is high and h_z is high; no prefix method can recover it, and
  supplying the hidden statistic Φ changes *which* step is blamed more than *how often* (TrajErrBench goal probe: 16/50
  change, 22/50 correct either way). Deferral should be to an oracle, not to the annotator.
- **A log cannot certify necessity.** Tian–Pearl bounds on FaP will show the lower bound on PN near zero for early error
  events (prediction A7). Replay identifies PN only under monotonicity (violated: SymTrace 39/54 success re-runs fail) and
  under an SCM choice for the noise (Oberst–Sontag), which is exactly why counterfactual-with-ground-truth labels
  (TracerTraj) converge on the final answer.
- **The symptom field is a responsibility profile.** k repeated searches give each 1/(k+1): flat, not peaked, so there is
  no gradient to back-propagate from (X1). Taint over free text reproduces the same flatness (every later step is
  tainted); the useful object, the first failed sanitiser, is H2 again.
- **Forward provenance is the estimator for omissions.** A backward slice cannot contain a use without a def; the
  20/160 MemTrace roots with no path, the 84% of AgentHallu runs where the gold string never appears, and the 19
  TraceElephant runs where it appears and is dropped are all forward-slice / where-provenance cases (H3).
- **The output space needs ⊥ classes.** Closed-set reject classes for environment and artefact runs are regex-detectable
  (C7, H4b); the open class (exhaustion) is the *more* templated one, so detect it as the compact class, not as a tail.
- **Injected data trains the local-consistency channel only.** The shortcut audit is exact and already published for the
  injected side; the open claim is the natural-set transfer (fine-tuned attributors predicted to lose more than the
  zero-shot judge under masking / seam stripping).

## 3. Prioritised pilots (none needs new LLM calls; all run on `loaders/` and cached `results/`)

| # | pilot | tests | principle | file |
|---|---|---|---|---|
| 1 | Re-score every cached `all_at_once_std.jsonl` under each available convention (TRAIL earliest / HIGH / last fabrication; AgentRx first / root; MP-Bench majority / unanimous / any; TrajErrBench gold / +2 / +4; Who&When HC with triple collapse) | H6, H10 | jury learning, latent chain, causal abstraction | B3, C5, A3 |
| 2 | Normality vs position on AgentRx: is the root the earliest *norm-violating* flagged step (≥15/17 of the root ≠ first logs)? Same on MP-Bench 3-vote steps | H2 | HP + normality | A1 |
| 3 | Agreement vs repeat count on the 44 Who&When × AgentRx shared logs (Spearman ≥ 0.4 predicted) | X1, H4 | responsibility 1/(k+1) | A2 |
| 4 | Tian–Pearl PN bounds on FaP (1,794 runs; lower bound < 0.15 predicted), within the 58 matched tasks | X6, A7 | probabilities of causation | A7 |
| 5 | Response-conditional CATE (T-learner) on TRAIL `extra.errors` and AgentHallu: CATE ≈ 0 when the next action changes strategy, ≤ −0.3 when it repeats | H8 | HTE / uplift | A6 |
| 6 | (obs, next-action) classifier vs obs-only on AgentHallu tool-error steps (AUROC ≥ 0.65 vs ≈ 0.5) | H8 | matched-anchor contrast | C6 |
| 7 | GT-string forward rules: "last step containing GT + 1" on the 19 TraceElephant runs; "first observation containing the final claim" on AgentHallu Retrieval (≥70% within ±1) | H3 | forward slice / where-provenance | C3 |
| 8 | Offset-bucket Dawid–Skene on MP-Bench per-annotator flags; de-duplicate annotators 1/3; cascade check P(flag | earlier flag by same annotator) | §4, B5 | annotator models, click models | B1, B5 |
| 9 | Judge accuracy split by "prefix monitor called the gold reasonable" (≥15 pp gap predicted) | H13 | HCA / masking | A5, B4 |
| 10 | Failure-framed vs success-framed judge on AgentHallu clean runs and TRAIL correct-ending runs (invented step in >50% under failure framing) | H9, P4 | outcome bias | B4 |
| 11 | Risk–coverage curve from 3-seed agreement / inventory candidate count; regex pre-filter (HORIZON, AgentErrorBench) and exhaustion one-class score | H4, H4b | selective prediction / open-set | B6, C7 |
| 12 | Text-masked predictor on WWP (≥50%) vs Who&When HC (≤15%); TF-IDF domain classifier injected vs natural (AUROC > 0.9) that is at chance as a step scorer | H7 | shortcuts, λ term | C1, C2 |
| 13 | τ² policy clauses as a DFA: violation step within ±1 of gold in ≥70% of act.*/obs.*/WrongOrder, ≈0% of reason.* | H11, X11 | runtime verification | C7 |
| 14 | HSMM sojourn score on FaP PASS `action_segments` (outcome AUROC ≥ 0.65 vs 0.498 from emissions) | H12 | HSMM | C4 |

Pilots 1, 2, 3, 7, 12 are a few hours each; 4–6, 8–11, 13–14 one to two days each.

## 4. Novelty check

Taken (verified ids): counterfactual replay to define or find the step (AgenTracer 2509.03312, EPV 2610.17633, Causal
Agent Replay 2606.08275, CausalFlow 2605.25338, MRFR 2608.29228); Shapley over agents (2509.08682, 2511.10687,
2607.18255); AC2 inside one LLM pass (A2P 2509.10401); the shortcut audit on injected benchmarks (Xu & Gao 2610.17747:
boundary rule 310/311 on ALFAgent, fine-tuned judges lose 31–99 points when reasoning follows the fault); estimated
depends-on / contradicts / repairs edges with blame on the receiving decision (BLADE 2610.18780: HC 31.0 / AG 54.0 vs
all-at-once 24.1 / 50.0), which is the published form of H2 + H3; LTLf contracts over tool calls (ContrAgent 2609.18128);
per-annotator consensus ranking (MP-Bench 2603.25001).

Open (no 2024–2026 paper found): Halpern–Pearl / Chockler–Halpern by name, normality as the selection rule, responsibility
grading of loops; PN/PS bounds from logs; response-conditional treatment effects; a chain-structured label model or jury
scoring across conventions; an abstain / "no attributable step" class with risk–coverage reporting; dynamic slicing or
taint tracking applied by name to agent trajectories; matched-event PASS-vs-FAIL transition contrast; the natural-set
transfer side of the shortcut audit; scoring a runtime-verification violation step against attribution golds.

## 5. Caveats

Each cluster was written by one agent with abstract-level verification; publisher pages for several classical DOIs were
blocked, so those are confirmed bibliographically, not textually (items marked [unverified] in the cluster files: WLU
formula, Rubenstein 2017 id, Halpern 2016 book, Math-Shepherd id, Lafferty CRF id, "relevant slicing" DOI, Pro2Guard
abstract, two 2026 listings). Predictions in §3 are the agents' and mine; none has been run yet.
