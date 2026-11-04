# Cluster B: labels, annotators and abstention

*2026-11-01. Maps X1–X12 / H1–H13 (`findings/hypotheses.md`) onto six principles. Every arXiv id / DOI below was opened on
its abstract, JMLR/NeurIPS or Crossref page today unless marked **[unverified]**. Human-factors primaries on hindsight
(Fischhoff 1975, Caplan 1991, Rasmussen 1990) and the LLM position-bias papers are already verified in
`lit/known_phenomena.md` §1 and P3/P5 and are cited, not re-derived. Survival / change-point / MIL / PU / TPP material is in
`notes/lit_timeseries/README.md` and is not repeated.*

Notation: steps `t = 0..n−1`; a label source `j` (annotator, LLM draft, our judge, a rule) emits `S_j ⊆ {0..n−1} ∪ {⊥}`.
The six principles differ in the latent object: one true step (B1), a candidate set (B2), a vector of convention-specific
steps (B3), an outcome-dependent label (B4), a position-dependent *visibility* (B5), a label space with "no step" (B6).

---

## B1. Learning from multiple noisy annotators

**References.** Dawid & Skene 1979, *JRSS C* 28(1):20–28, DOI 10.2307/2346806. Whitehill et al. 2009, GLAD, NeurIPS 22.
Raykar et al. 2010, *JMLR* 11:1297–1322. Rodrigues & Pereira 2018, crowd layer, AAAI, arXiv:1709.01779. Tanno et al.
2019, CVPR, arXiv:1902.03680. LLM-judge variants: SkillAggregation (Sun et al., arXiv:2410.10215, CrowdLayer extended to
LLM judges); CARE (Zhao et al., arXiv:2603.00039, shared-confounder model, "up to 26.8%" lower aggregation error on 12
benchmarks); Kohli 2026, arXiv:2605.29800 (nine judges from seven families carry "about 2 independent votes' worth of
information"; aggregation closes "at most 11% of the gap" even with gold).

**Formal object.** Items `i`, sources `j`, observed labels `y_ij ∈ {1..K}`, latent truth `z_i`. Dawid–Skene: each source
has a confusion matrix `π^(j)_{k,l} = P(y_ij = l | z_i = k)`; EM alternates posteriors over `z_i` and MLEs of `π^(j)`
and the class prior. GLAD adds item difficulty `β_i` and source competence `α_j` with
`P(y = z) = σ(α_j β_i)`. Raykar et al. fit the classifier jointly with per-source sensitivity/specificity. Tanno and
Rodrigues put the confusion matrices as a layer on top of a network, with a trace penalty so the matrices do not absorb
the classifier's errors. Key assumptions: (a) sources are conditionally independent given `z_i`; (b) there is one `z_i`;
(c) `K` is a fixed label space shared by all items.

**Correspondence.** `z_i` = the decisive step; `y_ij` = annotator `j`'s step; `π^(j)` = that annotator's habit (always
later, always the orchestrator). Data that fit: MP-Bench (three Upwork annotators, every step binary; 16.2% of flagged
steps unanimous, 27.8% two votes, 56.1% one vote, arXiv:2603.25001; `loaders/mp_bench.py` exposes `votes` and
`extra.per_annotator`); SymFail (three annotators + adjudicator overriding all three in 20 cases); TraceElephant (three
experts, then reconciliation); the cross-team labels on shared logs (Who&When vs AgentRx 16/44 exact; Who&When step
unflagged by all three MP-Bench annotators in 26/57 HC logs). Our judge with / without GT and its `inventory` variant are
three more sources on the same items.

**Where it breaks.** (a) Independence: MP-Bench annotators 1 and 3 are verbatim identical on 19/169 manual logs and 26
logs lose their majority after de-duplication (`results/mp_bench/stats.txt`); FaP's second annotator is a jitter of the
first (§4 of hypotheses). Kohli's result is the general form: correlated sources make DS-EM *over*-confident in their
shared vote; CARE's shared-confounder term is the fix that exists. (b) Label space: `K = n_i` varies per item and a
confusion matrix over step identities is meaningless; the natural parameterisation is over *signed offset buckets*
relative to consensus (`≤−3, −2..−1, 0, +1..+2, ≥+3`) or over the chain positions of B3. (c) Single truth: the 1-vote
flags sit after the majority step in 948 cases and before it in 291 (manual), and 3-vote steps have median relative
position 0.82 vs 0.54 for 1-vote steps — the sources disagree systematically, not randomly, which is B3's territory.

**Prediction and pilot.** On MP-Bench manual logs an offset-bucket Dawid–Skene fit gives at least one annotator a
late-biased `π` (mass on `≥+3` above 0.3), and the DS mode moves *earlier* than `earliest_majority_step` in ≥10% of
logs; after de-duplicating annotators 1/3 it moves on the 26 lost-majority logs and nowhere else. Pilot (≤1 day): ~100
lines of EM on `extra.per_annotator`; re-score `results/mp_bench/all_at_once_std.jsonl` `pred_step` against the DS mode;
expect the 45% exact to move by <5 pp (the label, not the judge, is the bottleneck). Second: Who&When, AgentRx and
MP-Bench as three sources on the 57 shared HC logs; GLAD difficulty `β_i` predicted to track run length and exhaustion.

**Verdict: useful analogy.** The estimator is directly usable for de-duplication and for per-annotator offset
diagnostics, but the two assumptions that fail (independence, single truth) are exactly the ones our data violate.

**Prior applications.** None to agent attribution. The LLM-judge aggregation papers above (2024–2026) are the nearest;
MP-Bench aggregates by "consensus rate" and nDCG over the ranked steps, which is majority voting without a noise model.

---

## B2. Partial-label / candidate-set learning

**References.** Jin & Ghahramani 2002, "Learning with multiple labels", NeurIPS 15:921–928. Cour, Sapp & Taskar 2011,
*JMLR* 12:1501–1536. PRODEN: Lv et al. 2020, ICML, arXiv:2002.08053. PiCO: Wang et al. 2022, ICLR, arXiv:2201.08984.

**Formal object.** Each `x_i` comes with a candidate set `S_i ∋ y_i`; the learner minimises a risk over `S_i` — Jin &
Ghahramani's EM with a distribution over candidates, Cour's convex loss on `log Σ_{l∈S} p(l|x)`, PRODEN's progressive
re-weighting toward the candidate with the highest model score, PiCO's prototype-based disambiguation. Cour's
identifiability condition (ambiguity degree < 1): no wrong label may co-occur with the true one in *every* candidate
set; PRODEN's guarantee assumes the true label is the one the model will learn to prefer.

**Correspondence.** `S_i` = the set-valued golds we already have: TRAIL's error spans (841 errors on 144 traces, median
5 per trace; primary ≠ earliest in 58/144), AgentRx's annotated failure events (`extra.failures`; root is not the first in
19/73), MP-Bench's union of flags, SearchAuditBench's tolerance span, ±1/±3 windows, and the decision-triple collapse of
H10. Our judge's `step_in_set` *is* the partial-label coverage metric: MP-Bench 74, AgentRx 40, TRAIL 40, SAB 48,
Who&When 43 (no set, so = exact).

**Where it breaks.** (a) Our candidates are ordered on one causal chain; the "true" element is a convention choice, not a
hidden draw. (b) Cour's ambiguity condition is violated by construction: the claim / FINAL-ANSWER step co-occurs in the
set whenever the run ends with a claim (24% of MP-Bench unanimous flags; 46/117 TRAIL GAIA primaries are the manager's
final call), and ledger/verifier steps co-occur in every Magentic log. A PRODEN-style learner converges on the candidate
that is *easiest to score* — the loud late symptom — so PLL reproduces X1/X7 instead of removing it. (c) On
environment / exhaustion runs (X9) `S_i` contains nothing correct; the answer is `⊥` (B6).

**Prediction and pilot.** Train a text-free logistic step scorer (relative position, error string, role, tool status;
features from `inspect/trail_priors.py` / `agentrx_stats.py`) with the PRODEN objective, `S_i` = union of flags, on
TRAIL GAIA (117) and AgentRx (73). Prediction: the identified label's signed offset from `primary_idx` /
`root_cause_idx` has median > 0 and is the final-call span in ≥30% of TRAIL traces; control with `S_i = {primary}`.
Hours, no LLM calls. Free evaluation pilot: make `in_set` and ±1-after-collapse the primary columns in
`inspect/summarize_baselines.py` wherever a set exists.

**Verdict: exact instance for the evaluation object (set-valued gold, coverage metric); useful analogy for learning;
superficial for choosing a single primary.** The learning theory assumes the ambiguity is random; ours is structural.

**Prior applications.** None uses PLL on agent traces (searched "partial label" + "failure attribution"/"agent",
2024–2026). MP-Bench's nDCG over ranked steps and DRIFT's span-level F1 (arXiv:2606.02060) are set-valued evaluations
without the learning side.

---

## B3. Latent conventions: label variation, juries and labelling functions

**References.** Aroyo & Welty 2015, "Truth is a lie", *AI Magazine* 36(1):15–24, DOI 10.1609/aimag.v36i1.2564. Uma et
al. 2021, "Learning from disagreement: a survey", *JAIR* 72:1385–1470, DOI 10.1613/jair.1.12752. Plank 2022,
EMNLP, arXiv:2211.02570. Gordon et al. 2022, "Jury learning", CHI, arXiv:2202.02950. Ratner et al. 2016, "Data
programming", NeurIPS 29:3567–3575, arXiv:1605.07723. Rasmussen 1990 (stop rule; verified in `known_phenomena.md`).

**Formal object.** Three nested ideas. (i) *Human label variation* (Plank, Uma): disagreement is signal; keep
unaggregated labels, train on soft labels (Uma: soft labels beat gold on large datasets), evaluate against the
distribution. (ii) *Jury learning*: fit one model per annotator `f_j(x)`, let the evaluator compose a jury with chosen
weights, report the jury's verdict and its dissent. (iii) *Data programming*: labelling functions `λ_k(x) ∈ {1..K, ∅}`
(heuristic rules), a generative model `P(λ_1..λ_m, z)` with per-function accuracy and explicit pairwise dependencies,
fitted *without* gold; the marginal `P(z | λ)` trains the end model. Key assumption of (iii): a single latent `z`; the
functions are noisy views of it.

**Correspondence.** The conventions in X2 are labelling functions: `λ_lastStep`, `λ_firstPlannerPlanner` (CORRECT-Error
74%), `λ_firstDelegation` (LongRCA SWE-Pro 45%), `λ_firstWrite` (FaP 41%), `λ_categoryLandmark` (AgentHallu 55.8%),
`λ_earliestHIGH`, `λ_firstSymptom`, `λ_firstLedgerFlag`, `λ_acceptance` (H2). Each dataset's gold is one convention
applied with noise; FaP ships three (t_err, t_lock, t_obs) explicitly; HORIZON's judge is a 27/26/31% mixture. Jury
learning is literally H6 ("score under multiple conventions"): a jury of `{Who&When, AgentRx, MP-Bench}` models.
Rasmussen's stop rule is the convention's definition: the label is where the backward search stops.

**Where it breaks.** Ratner's generative model assumes the functions are noisy views of *one* `z`; our functions read
*different coordinates* of one chain, so their "accuracy" against a single `z` is undefined and the fitted dependencies
would absorb the chain structure. The fix is structural: latent `z = (t_prop, t_commit, t_sym, t_claim)` with each `λ_k`
attached to one coordinate and monotonicity constraints `t_prop ≤ t_commit ≤ t_sym ≤ t_claim`; this is a small
structured EM, not an off-the-shelf label model (it is the "structured prediction with latent alignment" item of
cluster C). Uma's soft-label training also fails when the variation is bimodal by 7–70 steps: a soft target spread over
two distant steps is not a smoothed version of either.

**Prediction and pilot.** (1) On FaP (1,794 runs, three timestamps on disk) a label model over the cheap rules will
assign distinct dominant rules to t_err (first write / first symptom), t_lock (claim-without-verification) and t_obs
(first awareness phrase); one rule dominating all three means the chain is degenerate here. (2) On the 57 shared HC
logs, a two-convention mixture (earliest-symptom vs acceptance) puts Who&When and MP-Bench in *different* components on
the 13 exhaustion runs and the *same* one on short single-commission runs (116/120 AG agree). (3) Jury pilot: re-score
every cached `results/*/all_at_once_std.jsonl` under each available convention (TRAIL: earliest span / earliest HIGH /
last span; AgentRx: first / root; MP-Bench: earliest-majority / unanimous / any); the judge's best-convention exact is
predicted to exceed the single-convention number by 10–20 pp and to show which convention it natively follows (g2 R3:
"first plausible deviation"). Loaders only, no new calls.

**Verdict: exact instance for evaluation (Plank/Uma/jury), useful analogy for learning (data programming needs a
chain-structured latent).** The whole of X2/H6/H10 is "human label variation" with a known ordering on the variants.

**Prior applications.** MP-Bench (arXiv:2603.25001) is the only attribution benchmark that keeps per-annotator flags and
scores against a ranking rather than one step; FaP releases three timestamps; nobody has fitted a label model over
structural rules or reported jury-style per-convention scores. REFLECT (arXiv:2606.09071) and AgenTracer
(arXiv:2509.03312) replace annotators with intervention/replay-defined golds, which is a *different* convention (X8:
counterfactual-with-GT labels converge on the final answer in 42%), not a resolution of the mixture.

---

## B4. Hindsight / outcome bias and its correction

**References.** Fischhoff 1975 and Caplan, Posner & Cheney 1991 (verified in `known_phenomena.md`: "appropriate care"
ratings fall 31 pp when the outcome is made permanent). Matsuura et al. 2026, arXiv:2609.13454 (clinical temporal
reasoning; strict temporal masking lowers the hindsight-trap rate by 5.8–9.6 pp and the hindsight-bias rate by 3.3–5.5 pp
with no significant accuracy change; baseline HTR 14–15% for GPT). Learning to defer: Madras, Pitassi & Zemel 2018,
NeurIPS, arXiv:1711.06664; Mozannar & Sontag 2020, ICML, arXiv:2006.01862 (consistent surrogate for defer-to-expert).
Outcome-defined process labels: Math-Shepherd, arXiv:2312.08935 (step score = fraction of rollouts reaching the
reference answer) **[id from secondary sources; abstract page not opened]**.

**Formal object.** A label source reads `(x_{≤t}, x_{>t}, O)` and emits `y_t`; outcome bias is
`P(y_t = fail | x, O = fail) − P(y_t = fail | x, O = pass)` on matched `x`. Correction designs: (i) *paired outcome
masking* — same case, outcome hidden or varied (Caplan: 21 matched pairs; Matsuura: mask everything after `t`); (ii)
*learning to defer* — the model outputs `y` or `⊥` and a deferral cost; the consistent loss of Mozannar–Sontag treats
the expert as an extra class whose "correctness" is observed; (iii) *outcome-defined labels* accept the bias and define
the step label by rollouts.

**Correspondence.** The outcome-reading source is every annotator in X5 (LongRCA: 146 rationales quote the evaluator;
TRAIL: gold answer in step 2 of 117/117; TrajErrBench: diagnostics shown to pre-annotators; AgentErrorBench:
exploration-order labels "given where the object actually was") and the judge itself (H9: HC/30 step 8 vs 66 with/without
GT; TRAIL judge invents a failure in 9/40 correct-ending runs; TravelPlanner protocol blamed 7/14). The *prefix monitor*
is exactly Matsuura's strict masking applied to attribution; the judge-minus-monitor gap on the same record is the
hindsight share. Math-Shepherd-style labels are H13's "hindsight by construction": TracerTraj diagnosed labels and
AgenTracer's replay golds are rollout-defined.

**Where it breaks.** Matsuura's question ("diagnosis at time t?") is well-posed without the future; "which step caused
the failure?" presupposes the failure, and 65.5% of τ² failures have no transcript symptom (X11). Masking the outcome
therefore changes the question into anomaly detection, and the judge *invents* an outcome (P4, H9). Learning-to-defer
assumes the expert is less biased than the model; our expert (the annotator) is the more outcome-informed party. The
usable version is defer-to-*oracle* (object location, user goal, failing tests), H13's expensive test.

**Prediction and pilot.** Caplan design on data with matched prefixes: AgentHallu (250 clean vs 443 hallucinated runs,
equal tool-error rates) and TRAIL's 34 correct-ending GAIA runs. Run `baseline/all_at_once.py --no-gt` on clean runs
under a failure framing and under a success framing: the judge names a step in >50% of clean runs under the failure
framing (9/40 already on TRAIL), mostly the first tool error — the invented failure follows the symptom prior. Second:
emulate a deferral head as "attribute only if the prefix monitor also flags the gold"; H13 says this defers 12/20
AgentErrorBench and 8/20 τ² golds; predicted exact >55% on retained vs <15% on deferred.

**Verdict: exact instance for the bias (the judge and the annotators are conditional readers of the outcome; the prefix
monitor is the masking instrument); useful analogy for the correction.** The correction is weaker than in clinical
reasoning because masking removes the question for silent failures.

**Prior applications.** Known_phenomena P3/P4; trajectory-judge (arXiv:2609.00038: outcome-only judge 45% recall on
silent faults, 33% false alarms on correct trajectories). No one has run a paired outcome-masked re-annotation on an
attribution benchmark; hypothesis 3 in `known_phenomena.md` §3 proposes it.

---

## B5. Position / exposure bias: examination hypothesis and click models

**References.** Craswell, Zoeter, Taylor & Ramsey 2008, WSDM, DOI 10.1145/1341531.1341545 (cascade model). Wang,
Bendersky, Metzler & Najork 2016, SIGIR, DOI 10.1145/2911451.2911537. Joachims, Swaminathan & Schnabel 2017, WSDM,
arXiv:1608.04468 (propensity-weighted ranking SVM; propensities from randomisation). LLM-judge position bias: Zheng et
al. 2023, arXiv:2306.05685 (consistency numbers in `known_phenomena.md` P5).

**Formal object.** Examination hypothesis: `P(click | d, k) = P(E = 1 | k) · P(R = 1 | d)` — a document is clicked only if
examined (position `k`) *and* relevant. Cascade model: the user scans top-down and stops at the first satisfying click.
Unbiased LTR: with propensities `θ_k = P(E | k)` estimated by swap/randomisation interventions, the IPS estimator
`Σ_i c_i · r_i / θ_{k_i}` is unbiased for the full-information risk. Key assumptions: relevance is independent of
position; examination is identifiable by intervention.

**Correspondence.** Click ↔ a source (annotator, judge, per-step monitor) flags step `t`; examined ↔ it attended to
`t`; relevant ↔ `t` is genuinely erroneous. Exposure is non-uniform because late steps are loud (X1; the prefix monitor
flags post-gold steps at 2–7× the pre-gold rate), and MP-Bench consensus is a click curve (3-vote steps: median relative
position 0.82, error-string rate 0.27; 1-vote steps: 0.54 / 0.09; 1-vote flags after the majority 948 vs before 291).
The cascade stop rule is Rasmussen's stop rule for a forward reader. LongRCA's judge late bias (30/48 misses later on
142-step traces) is examination decay with context (P5); the WWP last-step masking (75→30) is a swap intervention that
measured a propensity.

**Where it breaks.** The examination hypothesis needs relevance independent of position; in trajectories the early
error *causes* later loud steps, so later "relevance" is induced by the thing we want to find. IPS re-weighting of
flags by `1/θ_t` therefore corrects annotator *attention* but not symptom *propagation* — it would up-weight early
flags that exist and cannot create flags on silent early steps. Also, randomising step order (the LTR estimation
intervention) destroys the dependency structure, so only partial interventions are available: reversed numbering,
last-k masking, step-window presentation.

**Prediction and pilot.** (1) Cascade check on MP-Bench manual logs: `P(flag_t | same annotator flagged earlier)` vs
`P(flag_t | none earlier)`; a "stopping" annotator has the first far *below* the second, a "symptom collector" far
*above*. Prediction: one of each among the three, which explains the 60% pairwise disagreement without any error of
judgement. (2) `all_at_once.py --mask-last 1` on Who&When HC and TraceElephant: exact moves by <5 pp (no last-step
propensity on natural logs) against 75→30 on WWP. (3) Reversed rendering: mean signed offset shifts ≤2 steps on
≤60-step sets, >10 on LongRCA.

**Verdict: useful analogy.** The factorisation examined × relevant explains annotator consensus and judge decay, and
the intervention logic (masking) is already in use; it breaks on the causal confounding of exposure and relevance.

**Prior applications.** Pairwise-judge position bias (Zheng 2023) and lost-in-the-middle are measured on LLM judges;
no work applies click models or IPS to step flags or to step-attribution annotators.

---

## B6. Reject option, selective prediction, open-set recognition

**References.** Chow 1970, *IEEE Trans. Inf. Theory* 16(1):41–46, DOI 10.1109/TIT.1970.1054406. El-Yaniv & Wiener
2010, *JMLR* 11 (noise-free selective classification; risk–coverage). Geifman & El-Yaniv 2017, NeurIPS,
arXiv:1705.08500 (SR-based selection with a guaranteed risk; e.g. 2% top-5 ImageNet error at ~60% coverage). Mozannar &
Sontag 2020 (above). Scheirer, de Rezende Rocha, Sapkota & Boult 2013, *TPAMI* 35(7):1757–1772, DOI
10.1109/TPAMI.2012.256 (open-space risk). Bendale & Boult 2016, OpenMax, CVPR, arXiv:1511.06233. Hendrycks & Gimpel
2017, ICLR, arXiv:1610.02136 (max-softmax baseline).

**Formal object.** Selective classifier `(f, g)`: predict `f(x)` when `g(x) = 1`, else abstain; coverage
`E[g]`, selective risk `E[ℓ(f,y) g] / E[g]`; Chow's rule abstains when the max posterior is below `1 − c` for abstention
cost `c`, optimal when posteriors are calibrated. Open-set recognition adds classes unseen at training and bounds
*open-space risk* (the volume of the input space labelled as a known class far from any training sample); OpenMax
re-distributes logit mass to an "unknown" class by extreme-value fits on activation distances.

**Correspondence.** Output space `y ∈ {0..n−1} ∪ {⊥_env, ⊥_budget, ⊥_artefact, ⊥_none}`. Environment/harness failures
(X9: SymFail 450/536 never reached a page; LongRCA ≥60% TravelPlanner simulator conditions; AgentRx guardrail 9/44)
and terminal artefacts (X12: HORIZON 75.5% of GPT-OS failures answer the in-context example; 89% of web failures are
early stops) are *known* extra classes — closed-set with regex-detectable signatures (H4b). Exhaustion runs with no
decisive step (22% of Who&When HC, 84% of SymFail, 8+ AgentErrorBench budget runs; H4) are the *open* class: nothing in
the step label space is correct. Our judge currently has coverage 1.0 by construction and a measured cost of that:
it invents a step in 9/40 correct TRAIL runs (B4) and attributes an agent in 98% of SearchAuditBench records.

**Where it breaks.** (a) Chow/Geifman need an informative confidence; an LLM judge's verbalised confidence on a step
pick is not calibrated against *convention* noise, and the right risk is measured against agreement with any
convention, not one gold. (b) The reject region is not a tail: 20–80% of runs per dataset, so this is a mixture/regime
problem (H4's regime classifier is a gating network, B-cluster's `g`) rather than a low-coverage guarantee. (c)
Open-set methods assume known classes are compact in feature space; "runs with a decisive step" are not — they are the
heterogeneous class, and the open class (exhaustion) is the *more* templated one (SymFail 70% template), so the usual
geometry is inverted: detect the "no-step" class as the compact one.

**Prediction and pilot.** (1) Risk–coverage curve for the judge on Who&When (184) and TRAIL (40), confidence proxy =
agreement across 3 seeds (120 extra calls) or candidate count from the cached `inventory` variant. If informative, exact
at 50% coverage is ≥60% (from 43%); if flat, the judge's uncertainty says nothing about convention noise and `g` must
come from text-free regime features. (2) Closed-set pre-filter with the regexes of `inspect/horizon_os_terminal.py` /
`agenterrorbench_heuristics.py`: removed runs are judge misses above the base rate, so exact on the remainder rises ≥5
pp on HORIZON and AgentErrorBench. (3) Open class: one-class score on (distinct-action fraction, null observations, env
error at first tool call); cross-team exact agreement inside the flagged set ≈0–36% vs >60% outside (H4's test).

**Verdict: exact instance for the output space and the evaluation (abstain class + risk–coverage reporting); useful
analogy for the gating mechanism; superficial if implemented as a threshold on LLM self-reported confidence.**

**Prior applications.** No attribution benchmark or method offers an abstain / "no attributable step" output (searched
"failure attribution" + abstain/no error/unattributable, 2026). The closest are detection-first designs: AgentHallu's
250 clean runs (detection AUROC before localisation), TRAIL's correct-ending traces with error spans, and REFLECT's
silent-failure focus (arXiv:2606.09071); trajectory-judge's 33% false-alarm rate on correct trajectories is the measured
cost of coverage 1.0.

---

## Annotation problems of hypotheses.md §4, by principle

Non-independent annotators → B1(a); outcome-informed labels → B4; environment failures and "no step" runs → B6;
baked-in position priors → B5 (exposure) and B3 (rule as labelling function); conventions and duplicated decision units
→ B2 and B3. "Agent labels follow instrumentation" (X4) has no home here; it is cluster C's provenance problem.

## Summary

- B1 Multi-annotator noise models (Dawid–Skene, GLAD, crowd layer; CARE/Kohli for LLM judges): **useful analogy** — estimator usable for de-duplication and offset diagnostics; independence and single-truth assumptions fail on exactly our data.
- B2 Partial-label / candidate-set learning (Jin–Ghahramani, Cour, PRODEN, PiCO): **exact instance for evaluation** (in-set coverage), **useful analogy for learning**, **superficial** for picking one primary; PRODEN-style learners are predicted to converge on the late loud candidate.
- B3 Latent conventions: label variation, jury learning, data programming: **exact instance for evaluation** (score per convention, keep per-annotator labels), **useful analogy for learning** — needs a chain-structured latent, not Snorkel's single z.
- B4 Hindsight / outcome bias and masking / deferral: **exact instance for the bias** (prefix monitor = Matsuura's strict masking; judge is a conditional reader), **useful analogy for the correction** — masking changes the question for silent failures; defer-to-oracle, not to annotator.
- B5 Examination hypothesis / click models / IPS: **useful analogy** — explains MP-Bench vote-vs-position curve and LongRCA decay; breaks because later relevance is causally induced by the earlier error.
- B6 Reject option / selective prediction / open-set: **exact instance for the output space and risk–coverage reporting**, **useful analogy** for gating, **superficial** as a confidence threshold on LLM self-reports; no prior attribution work has an abstain class.
- Cheapest pilots, all on cached inputs: offset-bucket DS on MP-Bench per-annotator flags; per-convention re-scoring of every cached judge run; failure-framed judge on AgentHallu clean runs; `--mask-last 1` on natural sets; 3-seed agreement as a risk–coverage proxy; regex pre-filter before the judge on HORIZON/AgentErrorBench.
- Prior work applying any of B1–B6 to LLM-agent step attribution: none found; MP-Bench (per-annotator consensus ranking), FaP (three timestamps), AgentHallu/TRAIL (clean runs) and REFLECT/AgenTracer (intervention-defined golds) are the closest and are cited to avoid over-claiming.
