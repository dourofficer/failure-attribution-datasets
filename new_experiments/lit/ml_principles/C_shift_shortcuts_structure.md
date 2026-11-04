# Cluster C: shift, shortcuts and structure

*Written 2026-11-01 against `findings/hypotheses.md`. Every arXiv id / DOI was checked on its abstract page or
Semantic Scholar record on 2026-11-01 unless marked **[unverified]** (publisher pages for the classical DOIs returned
403: title / authors / year / venue confirmed, abstract not). Process mining, spectrum localisation, CIRCA, HSMM
change-point mixtures and OAT are cited from `notes/lit_timeseries/` (README §4, `lit_E`, `lit_G` M18), not re-derived.
**Bold** numbers are quoted from sources; plain numbers are ours (`hypotheses.md`, `results/baseline_summary.md`).
Variables: trajectory `x = (s_0..s_T)`, labelled step `k*`, agent `a*`, outcome `S`, convention `c`, dataset `D`.*

---

## C1. Shortcut learning, Clever Hans predictors and partial-input baselines

**References.** Geirhos et al., "Shortcut learning in deep neural networks", Nat. Mach. Intell. 2020, arXiv:2004.07780.
Lapuschkin et al., "Unmasking Clever Hans predictors", Nat. Commun. 2019, DOI 10.1038/s41467-019-08987-4. Gururangan et
al., "Annotation artifacts in NLI data", NAACL 2018, arXiv:1803.02324. Poliak et al., "Hypothesis-only baselines in NLI",
*SEM 2018, arXiv:1805.01042.

**Formal object.** `P_train(x, y)` in which a cheap cue `z = g(x)` is correlated with `y` while the intended rule uses
`f(x)`. A risk minimiser picks `h(z)` whenever `P_train(y | z)` is peaked; Geirhos's test is an o.o.d. set with `z ⊥ y`,
where accuracy collapses to `P(y | z)`. The diagnostic estimator is the *partial-input baseline* (Gururangan, Poliak): a
classifier that sees only `z` (hypothesis-only NLI reaches **≈67% on SNLI, ≈53% on MultiNLI** vs 33% chance);
Lapuschkin's Spectral Relevance Analysis clusters relevance maps to find the cue actually used.

**Correspondence.** `x` = trajectory text; `y` = `k*`; `z` = position, framework template, agent name, length outlier,
seam, authorial voice. Our partial-input baselines are measured: last agent step = `k*` in 48% WWP (MathChat 79%), 50%
CORRECT-Error, 48% TracerTraj-diagnosed; CE seam rule 74.0%; SymFail 70% from (template, tool status); AgentHallu
category→landmark 55.8% > best LLM 41.1% (X7). The o.o.d. test is the last-step mask: judge exact 75 → 30 on WWP. The
model *rewarded* by the cue is the fine-tuned attributor trained on injected data (H7); a zero-shot judge can only
*follow* it.

**Where it breaks.** In NLI the premise still carries the true signal; in injected sets the cue is a property of the
*generator* (execution stops or is replayed at the injection, X8), so no artefact-free version of the same data exists
and removing the shortcut means changing the benchmark. Natural position priors (H5) are convention, not shortcut; a
partial-input baseline cannot tell the two apart, only a transfer test can.

**Prediction / pilot.** A trajectory-free predictor (per-framework position rule + agent name + length z-score) scores
≥50% exact on WWP text and ≤15% on Who&When HC; any attributor *fine-tuned* on WWP loses more than the zero-shot judge
under seam stripping (CE) and last-step masking (WWP). Pilot: extend `inspect/who_and_when_pro_stats.py` with a logistic
regression on text-masked features and add the row to `results/baseline_summary.md`; no LLM calls.

**Verdict: exact instance.** The label is predictable from partial input and the o.o.d. test (mask / strip) collapses
accuracy exactly as Geirhos's framework predicts.

**Prior application (verified).** Xu & Gao, "Auditing Failure Attribution: Label Predictability and Judge Behavior",
arXiv:2610.17747 (Oct 2026) runs this audit on Who&When Pro, AFTraj and Aegis: "last step with reasoning" gets
**310/311** on ALFAgent vs **GPT-4.1 58.8%**; final-step **52.1%** on smolagents; per-system final-or-penultimate rule
**51.4%** over 6,257 text rows, **78.8%** on MathChat (our 48% / 79% agree); a reasoning-only step classifier **95.2%**;
judges fine-tuned on these labels beat GPT-4.1 by **41 points** and lose **31–99** when reasoning is added after the
faulty step (zero-shot **≤9**). Their four tests (input restriction, cue following, residual accuracy, aggregation) are
the protocol H7 should adopt; the natural-set transfer side is not run there.

---

## C2. Covariate shift, label shift and domain-adaptation bounds (H7)

**References.** Ben-David, Blitzer, Crammer, Kulesza, Pereira, Vaughan, "A theory of learning from different domains",
Machine Learning 79, 2010, DOI 10.1007/s10994-009-5152-4. Lipton, Wang, Smola, "Detecting and correcting for label
shift with black box predictors", ICML 2018, arXiv:1802.03916. Arjovsky et al., "Invariant risk minimization",
arXiv:1907.02893. Sagawa et al., "Distributionally robust neural networks for group shifts", ICLR 2020, arXiv:1911.08731.

**Formal object.** Source `S` (injected: WWP, CE, Aegis, TracerTraj) and target `T` (natural: Who&When, TraceElephant,
AgentRx). Ben-David: `ε_T(h) ≤ ε_S(h) + ½ d_HΔH(S, T) + λ`, where `d_HΔH` is the divergence a classifier from `H` can
detect between unlabelled samples, and `λ = min_h [ε_S(h) + ε_T(h)]`, the error of the best *joint* hypothesis. Label
shift (Lipton): `P_S(x|y) = P_T(x|y)`, only `P(y)` moves; BBSE estimates `P_T(y)` from a black-box predictor's confusion
matrix. IRM: find a representation under which one classifier is optimal in every training environment; group DRO:
minimise the worst group's loss (**10–40 pp** worst-group gains with strong regularisation).

**Correspondence.** Domain = dataset / generator; `y` = `k*`; `h` = attributor. The domain classifier estimating
`d_HΔH` is H7's style classifier: authorial voice (Aegis regex 91% vs prior 70%; WWP injected turn is its agent's length
outlier in 50–92%) makes injected and natural steps separable, so `d_HΔH` is large. The `λ` term decides: the best joint
hypothesis must label the prefix-contradicting step on `S` (100% locally detectable) *and* the acceptance / first-symptom
step on `T` (locally flagged 33–80%, earliest flag ≤42%); since the conventions differ (X2, X8) no single `h` fits both,
`λ` is large and the bound is vacuous whatever alignment is done. Label shift: the position prior moves (48–50% last
step on `S`), but `P(x | y)` moves too (an injected `k*` contradicts its prefix, a natural one does not), so BBSE's
assumption fails. IRM across injected frameworks would select "contradicts own prefix" as the invariant feature, which is
exactly the feature absent in `T`. Group DRO is the right vocabulary *within* natural data: groups = regimes (H4), and
the worst group (exhaustion, cross-team agreement ≈0–36%) is where every method is at chance.

**Where it breaks.** The theory holds `y` fixed across domains; here the *definition* of `y` changes. This is task
shift, not distribution shift; the remedy is H6 (matched conventions), not alignment. Only the local-consistency channel
(X8) is shared, as a sub-task.

**Prediction / pilot.** A TF-IDF domain classifier (injected vs natural step text, content words masked) reaches
AUROC > 0.9 (proxy-A-distance near maximum) while the same classifier used as a step scorer on Who&When is at chance
(≤ position prior 10%). Pilot: `loaders/who_and_when_pro.py` + `loaders/who_and_when.py` step texts, `inspect/aegis_cues.py`
regexes as features; no LLM calls.

**Verdict: useful analogy.** The bound names the right quantities and says why transfer fails (`λ`), but the cause is a
change in the target's definition, which domain adaptation does not model.

**Prior application.** None trains on injected and tests on natural with a shift analysis. Aegis evaluates o.o.d. on
Who&When; SOAP reports +8.5 pp on WW-AG vs +0.4 on CE (arXiv:2610.13105). One injected benchmark subsamples by
decisive-error position to mimic Who&When's early labels (id **[unverified]**), a label-shift correction in all but name.

---

## C3. Dynamic slicing, taint tracking, provenance and information-flow control (H3, X3, X4)

**References.** Korel & Laski, "Dynamic program slicing", Inf. Process. Lett. 1988, DOI 10.1016/0020-0190(88)90054-3.
Agrawal & Horgan, "Dynamic program slicing", PLDI 1990, DOI 10.1145/93542.93576. Clause, Li, Orso, "Dytan: a generic
dynamic taint analysis framework", ISSTA 2007, DOI 10.1145/1273463.1273490. Cheney, Chiticariu, Tan, "Provenance in
databases: why, how, and where", Found. Trends DB 2009, DOI 10.1561/1900000006. Agent IFC: Debenedetti et al., CaMeL,
arXiv:2503.18813 (control/data-flow separation + capabilities; **77%** of AgentDojo tasks solved with provable security vs
**84%** undefended); Costa et al., Fides, arXiv:2505.23643 (confidentiality / integrity labels on a variable-passing
planner).

**Formal object.** Execution trace `σ = (e_1..e_n)`; def-use chains `def(v, e_i) → use(v, e_j)`; control dependence
(`e_j` executed because of predicate `e_i`). Backward dynamic slice of `(v, e_n)` = executed statements that affected
`v`; forward slice of `(v, e_i)` = statements its value reaches. Taint: source labels propagate through data (optionally
control) flow; a sink check asks whether a labelled value arrived. Provenance: *why* (witness inputs), *where* (source
cell), *how* (semiring expression). Key assumption: dependence is syntactically recoverable from the trace.

**Correspondence.** Statement ↔ step; variable ↔ claim, entity, required item, task constraint; output ↔ final
answer. Backward slice of the final answer ↔ EMFA's backward producer–consumer walk (arXiv:2610.11600; without it HC/AG
step accuracy drops **32.76 → 1.72 / 50.00 → 13.49**) and MemTrace's shipped backward dependency slice (faulty op in the
slice 140/160, no path 20/160). The 20 no-path cases are X3 by construction: an *omission* is a use without a def, which
a slice over executed statements cannot contain ("relevant slicing" adds potential dependencies, DOI **[unverified]**).
H3's forward trace is the forward slice from a required item: the root is the last step on which the item is live.
*Where*-provenance of the final claim is AgentHallu's test (GT string absent from every step in 84% of hallucinated runs:
no source cell, hence fabrication; where present, the first containing step is the labelled fetch landmark). X4 is taint
with *implicit* flow: the specialist's step is the data owner but its control dependence is on the orchestrator's
instruction (TraceElephant 30/90 Magentic golds under the specialist's name; LongRCA 55 `Computer_terminal` labels);
taint through control dependence attributes to the prompt owner, data-only taint to the record owner. CaMeL's
control/data separation is the same distinction, used for security.

**Where it breaks.** LLM-step dependence is not syntactic: every step may depend on the whole context, so a syntactic
slice is the entire prefix. The slice is informative only if dependence is *semantic* (string carry, entity overlap, or
an estimated `P(depends)` as in BLADE). Taint over-approximates: a tainted observation reaches every later step, which
is X1's diffuse field; the useful quantity, the *first sanitiser that failed* (acceptance step, H2), is not defined by
taint analysis. Implicit flows are the classic blow-up of dynamic taint (Dytan makes them optional for that reason).

**Prediction / pilot.** On the 19 TraceElephant runs with the ground truth visible before the label, "last step
containing the GT string + 1" hits `k*` within ±1 in >50% (judge: 33% exact); on AgentHallu, the first step whose
observation contains the final claimed string is within ±1 of `k*` in ≥70% of Retrieval runs and ≈0% of Planning runs
(gold = step 0). Pilot: `inspect/g1_gt_visibility.py` and `inspect/memtrace_evidence_loss.py` already compute string
visibility; add the two rules, no LLM calls. Expensive: BLADE-style estimated `depends-on` edges and a semantic forward
slice on MemTrace's 50 Update / Extraction cases.

**Verdict: exact instance for lineage-structured logs (MemTrace) and string-carried items; useful analogy for free
text,** where dependence must be estimated and the attribution rule (first failed sanitiser) is not part of the
principle.

**Prior application (verified).** BLADE, Guo, Long, Zhang, arXiv:2610.18780 (Oct 2026): a probabilistic judge answers
*depends-on / repeats / contradicts / repairs* per event (edges kept at p ≥ 0.3, ≤2 handoffs audited per event) and
labels each handoff kept / breach (unverified adoption, inapplicable use, misinterpretation, correction with new error) /
inherited-or-repaired, findings attached to the *receiving* decision; step accuracy **HC 31.0, AG 54.0, M-One 80.9,
DyLAN 56.6, MetaGPT 65.4** vs All-at-once **24.1 / 50.0 / 78.7 / 52.6 / 54.3**, macro gain **+5.6 [2.8, 8.6]**. This is H2
plus an estimated def-use graph, the closest published form of H2+H3. FALAT, arXiv:2606.00765 (dependency-guided
search, **AG 46.0 / HC 29.1**). Survey arXiv:2606.04990 defines execution provenance as a typed graph and names
"semantic attribution of claims to evidence" as the open gap. PROV-AGENT, arXiv:2508.02866 (W3C-PROV for agent calls in
scientific workflows). No paper applies dynamic slicing by name; MemTrace's dependency slice is one in all but name.

---

## C4. Regime switching, mixture-of-experts gating and HSMM phase models (H4, H12)

**References.** Hamilton, "A new approach to the economic analysis of nonstationary time series and the business
cycle", Econometrica 1989, DOI 10.2307/1912559. Jacobs, Jordan, Nowlan, Hinton, "Adaptive mixtures of local experts",
Neural Computation 1991, DOI 10.1162/neco.1991.3.1.79. Yu, "Hidden semi-Markov models", Artif. Intell. 2010,
DOI 10.1016/j.artint.2009.11.011 (already used in `lit_G` M18).

**Formal object.** Hamilton: latent Markov regime `r_t` with regime-specific dynamics `x_t | r_t`; identified only if
the regimes differ in dynamics. MoE: `p(y|x) = Σ_k g_k(x) p_k(y|x)` with a gate trained jointly by EM; the gate
partitions the input space where one expert fits better than another. HSMM: states with explicit sojourn law `p(d|z)`,
hence a time-in-state hazard; Viterbi gives a segmentation into phases.

**Correspondence.** H4's regimes (single-commission / exhaustion / environment / artefact / silent) ↔ MoE experts with
per-regime attributors (H4b checker, H5 rule, "no attributable step"). The gate has no supervision (X9: no dataset has
that class), so it must be a hand-built classifier on text-free features, and the MoE is H5 with a prior stage. H12 ↔
HSMM states = phases (plan → fetch → write → verify → claim); "normal flow" = the PASS phase grammar plus sojourn laws;
deviation = phase skipping (claim without verify: FaP 16.3% PASS vs 28.7% FAIL) or sojourn overrun (exhaustion; 13/58
Who&When HC and 69 SymFail C2 runs end by budget). `lit_G` measured the emission version: outcome AUROC 0.498, `t_err` 29%.

**Where it breaks.** Hamilton's identification condition fails on content: PASS and FAIL share event dynamics (X6: FaP
error events at 0.28 vs 0.31; AgentHallu tool errors 33.6 vs 40.4%), so an emission-based regime model finds phases, not
failure. The regime that matters is visible only in phase *duration* and *order*, the HSMM's sojourn hazard. A gate
trained by EM on attribution loss is circular: it routes by convention, not by regime.

**Prediction / pilot.** An HSMM fitted on FaP PASS `action_segments` (states = segment types, explicit durations) gives
outcome AUROC ≥ 0.65 from the sojourn-survival statistic alone (vs 0.498 from emissions); for exhaustion runs the first
step whose sojourn exceeds the PASS 95th percentile lies after `t_err` and near `t_lock`; on HORIZON web a phase-skip
score does *not* beat length (AUROC 0.87–0.91). Pilot: `inspect/failure_as_process_stats.py` already parses
`action_segments`; fit duration quantiles on 610 PASS runs, score 1,184 FAIL runs, no LLM calls.

**Verdict: useful analogy for H12 (phase = HSMM state, deviation = sojourn / order); superficial resemblance for MoE
gating** (no gate supervision; reduces to a classifier followed by per-class rules).

**Prior application.** None for LLM-agent traces (searched 2026-11-01); the nearest is agent-declared "semantic phases"
in coding trajectories (NeurIPS 2026 listing, id **[unverified]**), supervised by design.

---

## C5. Structured prediction with latent alignment and multi-target evaluation (H6, X2, H10)

**References.** Lafferty, McCallum, Pereira, "Conditional random fields", ICML 2001 **[id not fetched this session]**.
Quattoni et al., "Hidden conditional random fields", IEEE TPAMI 2007, DOI 10.1109/TPAMI.2007.1124. Yu & Joachims,
"Learning structural SVMs with latent variables", ICML 2009, DOI 10.1145/1553374.1553523.

**Formal object.** Output `y` is a structure (here a monotone chain `k_prop ≤ k_commit ≤ k_sym ≤ k_claim`), latent `h`
is an alignment or convention, and the model scores `(x, y, h)` jointly: HCRF marginalises `h`, latent SSVM does CCCP
on `max_h`. Training loss: `−log Σ_h P(y, h | x)`; the observed label of dataset `D` is `y_{c(D)}`, one coordinate of
the chain chosen by the convention `c`. Multi-target evaluation scores each coordinate against the dataset that labels it.

**Correspondence.** The chain is real: TrajErrBench labels the proposal (318/400) and the DB write follows at +2 / +4,
where the judge's modal miss sits; AgentHallu labels the observation one hop before the assertion; AgentRx root vs first
failure differ in 19/73; HORIZON's judge is a within-dataset mixture (27% / 26% / 31%). FaP alone ships three
coordinates (`t_err`, `t_lock`, `t_obs`), with a synthetic second annotator (hypotheses §4). ±1 tolerance (H10) is
segmentation boundary noise; decision triples are one segment labelled at three coordinates.

**Where it breaks.** Across datasets the convention is a constant, so the "latent" variable is observed (a dataset
indicator) and the model is a chain predictor plus a lookup. Within a dataset (HORIZON) it is truly latent and EM is
degenerate: the latent variable explains any label by picking the coordinate that fits. Monotonicity fails when the
claim precedes the symptom (X10: PASS verdicts after the root in 97% of LongRCA SWE-Pro runs).

**Prediction / pilot.** Scoring the cached judge predictions against the whole chain raises TrajErrBench τ² exact from
44% to ≥55% (absorbing the +2 / +4 execution misses) and flips the sign of "misses later / all" on TRAIL under the
last-fabrication coordinate; LongRCA stays ≈20% because its divergence is convention-free exhaustion. Pilot: re-score
`results/trajerrbench/all_at_once_std.jsonl` against {gold, gold+2, gold+4}, `results/trail/all_at_once_std.jsonl`
against {earliest span, earliest HIGH, last fabrication} from `extra.errors`, Who&When HC with the triple collapse (H10);
no LLM calls.

**Verdict: useful analogy.** The monotone chain and multi-target scoring are the right objects; the convention is
identifiable only across datasets, so only the evaluation protocol transfers, not the learning machinery.

**Prior application.** None; datasets shipping several coordinates (FaP, AgentRx first-vs-root, TRAIL spans) are scored
on one.

---

## C6. Contrastive and pairwise models over transitions with PASS recoveries as negatives (H8, X6)

**References.** van den Oord, Li, Vinyals, "Representation learning with contrastive predictive coding",
arXiv:1807.03748 (InfoNCE). Pairwise logistic / Siamese scoring is standard and needs no single citation.

**Formal object.** Anchor `o_t` (an observation of a given event type), candidates `a_{t+1}` drawn from runs that
received the same event type; InfoNCE `−log [exp f(o_t, a^+) / Σ_j exp f(o_t, a_j)]` learns a score of the *response
given the event*. The key assumption is that positives and negatives share the anchor distribution; otherwise the
contrast learns the anchor, not the response.

**Correspondence.** X6 is this sampling design: FaP PASS runs carry error events at the same rate and position as FAIL
(71% with ≥1; 0.28 vs 0.31); AgentHallu clean runs have tool errors at 33.6% vs 40.4%; TRAIL formatting / orchestration
errors are outcome-neutral (P(correct) 0.28–0.29 vs base 0.29). The anchor is matched by construction, so any learned
difference lies in `a_{t+1}` (strategy change vs identical retry: AgentErrorBench action-repeat 0.10 → 0.38 across the
label). H8's transition classifier is the pairwise version; CIRCA's parent-conditional score (`lit_E` 3.1.4) the
one-class version.

**Where it breaks.** FaP has no step text; same-task PASS runs exist only in AgentHallu, HORIZON and SymTrace reruns.
PASS recoveries are silent (AgentRx recovered WebSurfer failures: 0/24 error strings, 6/24 ledger flags), so positives
must be found by event matching. With unmatched anchors the model learns task difficulty (HORIZON's length separation).

**Prediction / pilot.** On AgentHallu an observation-only classifier on tool-error steps is at chance (AUROC ≈ 0.5,
equal error rates across outcomes) while a transition classifier on `(o_t, a_{t+1})` pairs reaches AUROC ≥ 0.65
hallucinated vs clean, beating the judge's 69% ±1 only in the Retrieval / Tool categories. Pilot:
`inspect/agenthallu_detect.py` + `loaders/agenthallu.py` (443 / 250), TF-IDF logistic on pairs vs observations, no LLM calls.

**Verdict: exact instance of the sampling design (matched-anchor contrast); the InfoNCE loss itself is optional.**

**Prior application.** OAT, arXiv:2607.12747 (NeurIPS 2026): one-class on **100** successes, **+20% F1** in-domain /
**+7%** o.o.d.; conditions on the prefix, not the event type, no FAIL negatives. Repair work (ELPO, "Repairs for Whom?",
EPV arXiv:2610.17633) uses rollouts, not PASS recoveries. No paper trains the matched-event transition contrast.

---

## C7. Specification mining, runtime verification and policy-as-automaton (X11, X12, H4b, H9, H11, H13)

**References.** Ernst et al., "The Daikon system for dynamic detection of likely invariants", Sci. Comput. Program.
2007, DOI 10.1016/j.scico.2007.01.015. Leucker & Schallhart, "A brief account of runtime verification", J. Log. Algebr.
Program. 2009, DOI 10.1016/j.jlap.2008.08.004. Agent-specific: Xiao & Nuzzo, ContrAgent, arXiv:2609.18128 (assume-
guarantee contracts in LTLf over tool-call predicates, compiled to DFAs, online gating and offline trace evaluation,
"matches LLM-judge and rule-based guardrails" with deterministic verdicts); Wu & Gong, "Policy-invisible violations",
arXiv:2604.12177 (PhantomPolicy, **600** traces, **5.3%** of case labels changed by trace review; Sentinel checks graph
invariants on a simulated world state). Pro2Guard, arXiv:2508.00500 (DTMC abstraction + monitor automaton) **[abstract
not fetched]**.

**Formal object.** Trace `σ` over atomic predicates; specification `φ` (LTLf, or Daikon's invariant templates at
program points); monitor `M_φ: Σ* → {⊤, ⊥, ?}` with three-valued finite-prefix semantics; Daikon keeps an invariant
never falsified on the corpus whose support exceeds a confidence threshold. Monitorability: safety properties are
refutable on a finite prefix, liveness properties are not.

**Correspondence.** Predicates = tool-call signatures, arguments, DB / file-system state; the τ² step-0 policy clause =
a contract; the silent failure (65.5% of τ² failures have no transcript symptom) = the DFA entering its violating state
at the step that executes the forbidden call, which is also the acceptance step (H2) and is H9's "simulate the rule" for
the policy half of X11. Daikon on PASS runs yields the invariants behind X12 / H4b: `final action ∈ {answer}` (HORIZON
Claude OS 38% `finish`), `action matches syntax` (AgentErrorBench 33–46% quoted actions), `verify precedes claim` (FaP
omission rule), `no example-question drift` (75.5% of HORIZON GPT OS failures). The `?` verdict is H4's "no attributable
step" class. Monitorability explains H13: a hindsight label (wasteful exploration order given the hidden object
location) is a liveness-type property, unflaggable on any prefix.

**Where it breaks.** Policy-invisible violations need world state absent from the log (the other half of X11:
`reason.WrongChoice` needs the hidden goal; BFCL gold responses visibly error in only 19–56%). Predicates must be
grounded from free text (ContrAgent assumes a fixed predicate set). Daikon over-fits templates: on SymFail (70% of
labels from template + tool status) it would mine the harness, not the task. The violation step is not always the
decisive step: the check fires at execution (+2 / +4) while TrajErrBench labels the proposal (C5).

**Prediction / pilot.** On TrajErrBench τ² the categories decidable from policy + tool outputs (act.*, obs.*,
WrongOrder) get a DFA violation step within ±1 of `k*` in ≥70% of runs, reason.* in ≈0%; on HORIZON OS the mined
terminal-action invariant reaches precision >0.95 against the environment verdict (H4b). Pilot:
`inspect/horizon_os_terminal.py` exists for the second; for the first, hand-write five τ² clauses as predicates over
`results/trajerrbench/g3_tau2_struct.json` tool calls and score by category, no LLM calls.

**Verdict: exact instance for policy and artefact failures (X12, the policy half of X11); inapplicable for hidden-goal
and hindsight failures,** whose property is not monitorable from the log.

**Prior application (verified).** ContrAgent (offline DFA trace evaluation), Sentinel (graph invariants), `lit_timeseries`
README §4 item 5 (Declare rules from the written policy, BFCL pilot 0.28–0.36 vs 0.18). None scores the violation step
against a step-attribution gold; that comparison is open.

---

## Summary (principle → fit)

1. Shortcut learning / partial-input baselines (Geirhos; Gururangan): **exact instance** of X7/X8/H7; Xu & Gao 2610.17747 already audit WWP/Aegis (boundary rule 310/311), the natural-set transfer is ours.
2. Domain adaptation bounds / label shift / IRM / group DRO: **useful analogy**; the `λ` term (no good joint hypothesis) is the right diagnosis, but the shift is in the label's definition, which the theory does not model.
3. Dynamic slicing / taint / provenance / IFC: **exact instance** for lineage logs (MemTrace) and string-carried items, **useful analogy** for free text; BLADE 2610.18780 is the published estimated-def-use version of H2+H3.
4. Regime switching / MoE gating: **superficial** (no gate supervision; reduces to H5); HSMM phases for H12: **useful analogy** via sojourn hazards, not emissions (`lit_G` already shows emissions find phases, not failure).
5. Latent-alignment structured prediction / multi-target scoring: **useful analogy**; the chain is real, the convention is a dataset constant, so only the evaluation protocol transfers.
6. Contrastive transitions with matched PASS events: **exact instance** of the sampling design behind X6/H8; loss choice immaterial; feasible now only on AgentHallu.
7. Specification mining / runtime verification / policy-as-automaton: **exact instance** for X12 and the policy half of X11 (ContrAgent, Sentinel exist, none scored against step golds); not monitorable for hidden-goal and hindsight labels (H13).
8. No 2024–2026 paper applies dynamic slicing or taint tracking by name to agent trajectories; the nearest are BLADE, EMFA, FALAT (estimated dependency graphs) and the security-side IFC systems CaMeL / Fides, which enforce rather than attribute.
9. Cheapest pilots, all without LLM calls: text-masked predictor on WWP; domain classifier WWP vs Who&When; GT-string +1 rule on TraceElephant / claim-source on AgentHallu; HSMM sojourn score on FaP segments; chain re-scoring of cached TrajErrBench / TRAIL predictions; (obs, act) vs obs-only classifier on AgentHallu; τ² policy DFA by category.
