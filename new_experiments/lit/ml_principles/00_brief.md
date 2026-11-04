# Brief: which ML principles model the attribution problems found in the data

Context for the literature agents (2026-11-01). The dataset inspection (`new_experiments/findings/hypotheses.md`,
read it first) found twelve recurring phenomena X1–X12 and thirteen hypotheses H1–H13. The question now is whether each
problem is an instance of an existing, well-studied ML principle, so that its theory, estimators and known failure
modes can be borrowed instead of re-invented.

Already mapped by the earlier time-series survey (`notes/lit_timeseries/README.md`, do NOT re-survey these):
survival / discrete-time hazard models, change-point and Shiryaev filters, multiple-instance and PU learning on steps,
RUDDER-style return decomposition, temporal point processes, conformal monitors, process mining / conformance
checking, spectrum-based fault localisation, CIRCA / Shapley outlier attribution on graphs, neural CDEs / anomaly
detection on step embeddings. Cite them where relevant, do not re-derive them.

## The problems to map (short form; numbers and record ids are in hypotheses.md)

- **X1 diffuse symptom field.** After the error, steps fill with retries, loops, verifier chatter; density is flat,
  not peaked. Per-step monitors flag post-error steps 2–7× more than pre-error steps; a whole-trajectory judge does not.
- **X2 label = convention on a chain** (proposal → commitment → first symptom → claim → lock-in). Different datasets,
  and different annotators of the *same* log, pick different points; divergence 7–70 steps on long / exhausted runs.
- **X3 omission → commission pairs.** The evidence gap and the later fabrication are both "the" error; annotators split.
- **X4 record owner ≠ decision owner.** Agent labels follow instrumentation (thread name, reacting role), not the
  prompt owner who decided.
- **X5 outcome-informed / hindsight labels.** Rationales quote the evaluator; labels mark choices wrong only given
  hidden state; the LLM judge is itself a conditional reader of the outcome and invents a failure when none is given.
- **X6 same signal, different fate.** Successful runs contain the same error events at the same rate and position;
  what differs is the response to the event.
- **X7 structural / positional priors** explain much published accuracy (last step 48–50% in injected sets; first
  write, first delegation, category-conditioned landmarks).
- **X8 injected ≠ natural.** Injected steps contradict their prefix and are 100% locally detectable; continuations are
  loyal; corruptions have an authorial voice; counterfactual-with-GT labels converge on the final answer.
- **X9 environment / harness failures labelled on agents**; no dataset has a "no attributable step" class.
- **X10 verification theatre and final-claim labels**; the end of the run looks the same in PASS and FAIL.
- **X11 silent failures** need an oracle (policy clause, DB diff, hidden tests, file-system state) absent from the log.
- **X12 terminal artefacts** (answering the in-context example, `finish` vs `answer`, quoted actions) decide a large
  share of "natural" failures and are regex-detectable.

Hypotheses in one line each: H1 late bias is an instrument property (per-step vs holistic); H2 blame the acceptance
step (first decision that proceeds despite a condition); H3 forward-trace required items instead of back-tracing
symptoms; H4 classify the failure regime first, allow "no decisive step"; H4b artefact checkers first; H5 category →
positional rule; H6 score under multiple conventions; H7 injected data trains a different skill and last-step priors;
H8 score transitions (obs→response) not observations; H9 make the failure description an explicit input; H10 collapse
decision triples, ±1 primary metric; H11 verifier/claim steps are zero evidence; H12 "normal flow" is phase structure;
H13 hindsight labels are unflaggable by prefix methods.

## Candidate principle clusters to verify and deepen (one agent each)

A. **Causation and credit.** Actual causation (Halpern–Pearl, but-for, preemption, overdetermination, early vs late
   preemption) as the formal object behind "earliest decisive step", "first unrecovered failure", MP-Bench's multiple
   causes and recovered errors; degrees of responsibility and blame (Chockler–Halpern); causal abstraction; counterfactual
   credit assignment in cooperative multi-agent RL (COMA, difference rewards, Shapley/value-based credit, LOO baselines)
   for "who"; hindsight credit assignment (HCA, counterfactual credit) for "when"; heterogeneous treatment effects /
   uplift for X6 ("same event, different fate"); interventional vs observational identifiability of the decisive step.
B. **Labels, annotators and abstention.** Learning from multiple noisy annotators (Dawid–Skene and successors, annotator
   confusion models, "learning from crowds" with per-annotator bias); partial-label / candidate-set / ambiguous-label
   learning for set-valued golds (MP-Bench, AgentRx, TRAIL, tolerance spans); latent-target / convention-mixture models
   (EM over labelling conventions, multiple-ground-truth evaluation); hindsight and outcome bias and their correction
   (outcome-blind re-annotation designs, debiasing with masked outcomes, "learning to defer"); position / exposure bias
   models from unbiased learning-to-rank and click models (annotators "examine" late symptoms more); reject option,
   selective prediction and open-set recognition for "no decisive step" / environment-caused classes.
C. **Shift, shortcuts and structure.** Shortcut learning / Clever Hans / spurious correlation and the last-step prior;
   covariate and label shift between injected and natural failures and what domain-adaptation theory says about
   transfer (H7); dynamic program slicing, taint tracking and provenance / information-flow models as the formal version
   of forward-tracing required items (H3) and of record-owner vs decision-owner (X4); regime-switching / mixture-of-
   experts gating for failure regimes (H4) and HSMM phase models for "normal flow as phase structure" (H12); structured
   prediction with latent alignment for predicting the whole chain proposal→commitment→symptom→claim (H6) and
   multi-target evaluation; contrastive / pairwise models over transitions (obs_t, act_{t+1}) with PASS recoveries as
   negatives (H8); specification / invariant mining and runtime verification as the oracle for silent failures (H11).

## Required output per cluster file `new_experiments/lit/ml_principles/<A|B|C>_<name>.md`

1. For each principle: the canonical reference(s) with verified arXiv id / DOI, the formal object (what is x, y, the
   loss or estimator, the key assumption), and a 3–6 sentence statement of what it says.
2. The mapping: which X/H it models, written as an explicit correspondence (our step ↔ their variable, our label ↔ their
   target, our dataset quirk ↔ their known failure mode). State where the correspondence breaks.
3. What the principle *predicts* on our data (a falsifiable statement with the dataset named) and the cheapest pilot
   that uses the existing loaders / cached baselines (`new_experiments/results/`).
4. A fit verdict: exact instance / useful analogy / superficial resemblance, with one sentence why.
5. Prior work that already applied the principle to LLM-agent failure attribution, if any (verified), so we do not
   claim novelty we do not have.
Keep each file under ~3,500 words; prefer precision over coverage; quote numbers from the sources.
