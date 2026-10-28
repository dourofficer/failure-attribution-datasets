# Review of `/dataDisk/home/thanhdo/fa_ideas` against `notes/failure_attribution_ideas.md`

*Written 2026-10-27.* `fa_ideas/` (9 files, 240 KB, compiled 2026-10-26) is an independent pass over the same 54 PDFs in `sharonish/papers`, with a different grouping (core / agents / reward-RL / halluc-UQ / OOD-shift / alignment-data / multimodal) and its own brief `FA_CONTEXT.md`. It is sharper and shorter than our collection (about 45 ideas against about 70), carries two factual corrections to the report, and computes a few numbers on `data/` that ours did not. Everything checked below was re-verified from `data/who_and_when` and from the extracted OAT text.

## 1. Corrections to the report (both verified, both should be applied)

- **The "one-class detectors reach F1 0.41" claim is not in OAT arXiv v1 (2607.12747v1).** A search of the full text finds no Isolation Forest, OC-SVM, KDE or per-step density baseline. The ablations that exist are Neural CDE vs Neural ODE (Fig. 3), gated vs ungated control path (+0.172 OOD AUROC, −0.028 in-domain; Fig. 4), CDE vs an RNN next-step predictor (Fig. 5, figure only, no numbers in text), layer / pooling / proxy-LLM ablations (App. G). Affected text:
  - `report/8_proposals/futureworks.tex:201` ("non-sequential one-class detectors on the same step embeddings reach F1 0.41");
  - `notes/alternatives.md:9` and `:16` ("Isolation Forest and OC-SVM ... F1 0.411 vs 0.435").
  - Suggested rewrite of the bullet at line 201: *The signal comes from selection, not from the dynamics: the paper's own RNN next-step predictor on the same step embeddings is only slightly behind the CDE (Fig. 5), the OOD gain (+0.172 AUROC) comes entirely from the gated control path that suppresses atypical inputs, and a model of all trajectories would recover the agent's own policy, under which its mistakes are ordinary on-policy actions (see the evidence in §2 below).* The Isolation-Forest / OC-SVM baselines at line 300 are fine as *our* planned baselines; they just cannot be attributed to OAT.
- **Positional baselines that OAT omits, recomputed on the 184 Who&When failures** (`history` index, `mistake_step` 0-based):

  | Baseline | Hit rate |
  |---|---|
  | OAT top-3 (paper) | 0.451 |
  | first-3 steps | 0.359 |
  | random-3 (k-matched) | 0.286 |
  | first step | 0.109 (paper: 0.115) |

  Position-only ranking ("earlier = more anomalous") gives per-trajectory AUROC **0.602**, above GPT-5 (0.584) and equal to ungated OAT (≈0.586); gated OAT's 0.758 is genuinely above it. By subset: Algorithm-Generated (median 10 steps) first-3 hit 0.516 vs random-3 0.360; Hand-Crafted (median 32.5 steps) first-3 hit 0.017 vs random-3 0.125. Median relative error position is 0.33 and 36% of errors fall at steps 0–2. These belong in the Proposal 2 baselines paragraph (`futureworks.tex:300`) and in Section 7's positional-prior discussion.

## 2. The purple note (`futureworks.tex:201`): fa_ideas' answer is richer than ours

Ours cites Cyclical Entropy Eruption Fig. 3/5 and Progress Advantage Fig. 3. fa_ideas adds:
- UQ-in-Agents Tab. 2: the agent's own NLL / entropy / verbalised confidence predict τ²-bench failure at AUROC 0.47–0.69, below chance for Kimi-K2.5 on Retail; uncertainty curves of successful and failed runs overlap within 1 sd.
- OAT App. H: it misses early latent reasoning errors "because such statements can appear in successful trajectories"; it fires on failure verbalisation and on reactions to empty tool returns (a t_obs detector, which matches our CORE-OAT reading).
- A formal framing from Debate-or-Vote: under the system's own policy V_t = P(success | prefix) is a Doob martingale, so an error is a step where V_t *drops*, not a low-probability action. The objection applies to density models of all trajectories; it does **not** apply to outcome-supervised hazard or value models, which only need the step to be outcome-predictive.
Recommended: replace the note with two sentences built from the martingale framing plus the two numeric citations.

## 3. Ideas in fa_ideas that are new or materially sharper than ours (adopt)

| fa_ideas code | Idea | Our nearest code | What is new |
|---|---|---|---|
| B2 + A-group §4.1 | **Value model with martingale / TD(0) consistency loss, trained from outcomes only; decisive = largest drop, lock-in = ε-crossing, recovery = rise** | CORE-PQM, F1.2 | Unifies PQM ranking, the martingale and Proposal 2 into one "hazard with recovery" model; removes the absorbing assumption that FaP PASS runs (2.3 recovered errors each) contradict. Testable claim: the largest drop sits at t_lock, not t_err. |
| B3 | **Contrastive OAT**: fit the step-dynamics predictor separately on successes and failures of the same tasks, score r_t = e_t^succ − e_t^fail | — | Direct, cheap test of whether outcome information is step-local; OAT is the one-class degenerate case. Data: FaP, AgentHallu. |
| B4 (1a–1c) | **Wild-step filtering** with residualisation (regress out role, step type, position, length before the SVD), bag constraint, first-passage decoding, and **outcome-only hyperparameter selection** | B5a | The 1-day **subspace-alignment diagnostic** (does the error-mean-difference vector lie in the top-k wild subspace at all?) is a cheap go/no-go for the whole SAL/HaloScope family. |
| C2 + E-8b | **FA-CleanBench** with rule validity filters and a **register-leak probe** (injector-vs-agent likelihood ratio finds the injected step without reading the outcome ⇒ style shortcut) | #11 (D4.1) | Concrete filters tied to dirty rows already in our notes (CORRECT-Error: 8.4% agent/role mismatch, 43 rows point at the user message; AgentErrorBench: 27 empty types; TracerTraj: 21 tasks in both splits). Replay at k = t_inj makes cleaning precision/recall measurable, which PrefCleanBench cannot do. |
| C3 | **Conformal risk control on a small labelled set** → smallest set S with P(t* ∈ S) ≥ 1−α, on top of OAT's success-calibrated FPR control | CORE-H&S functional CP | A coverage guarantee for the *decisive step*, not just a false-alarm guarantee; report set size vs coverage on MP-Bench / AgentRx / TRAIL. |
| E2 (C7.1) | **Knowledge-edit injection**: AlphaEdit one wrong leaf fact into an open agent's weights; errors arise fluently at natural positions; editing one agent's weights gives an exact *who* | — (we only took G3.1/G3.2 from KnowledgeSmith) | Counters the late-position skew of prompt injection. Limited to factual errors; 35% over-spreading. |
| E3 (3a–3c) | **Missing-cell correction** for injected→natural: tabulate (error × position bucket × role); PU learning with the prior pinned by "one decisive step per failure" where injected data has no cell; label-shift reweighting elsewhere | #9 (C8.1) | Makes the PU idea operational against Fig. `errpos`; generating the source on the *same* systems (TraceElephant replay) makes the invariance assumption true by construction. |
| E1 (F7.1) | **Self-adversarial, on-manifold, causally verified injection** (adversary picks step + fault type, agent's own model realises it, roll forward, realism filter, rollout causality check, hard buffer; adversary also chooses k) | B6 (rated 2) | Our version was a weak "observation adversary"; this version yields Proposal 1 repair-effect labels for free and attacks the position shortcut. Deserves plausibility 3–4. |
| F1 | **Identity-bias test for judges**: rerun with anonymised and permuted agent names; Attribution-IBC | F2.2 (anonymisation as a replay δ) | Prompting-only, days of work, quantifies how much "who" accuracy is a role-name prior (problem 6). |
| F5 | **Streaming attributor with LRU-rotated "suspect memory" heads** for long traces | F5.1 (capture/retention) | No training; targets LongRCA / TRAIL where early causes are lost by rolling summaries. |
| C6.2 | **Relevance-conditioned who-rule** (observation relevant + next step wrong → blame consumer; distracting → blame the retriever) | — | Black-box, works on closed logs; a cheap debiasing of the WebSurfer/Orchestrator prior. |
| F4.1 | **"Failure to withhold" as an error class** with AAD / IVQD / IASD subtypes and a solvability probe; decisive step = the commit | B2a/B2c | B2c (δ_read vs δ_decide) already covers F4.3; the error class and probe are new. |
| D2 (2a) | **Three-way active labelling** {correct-unusual, symptom, decisive} with the annotator simulated from AgentRx / FaP labels, budgets 25–200 | C2.1/C2.2 | The only label set that teaches cause-vs-symptom directly; also chooses rollout sites. |
| C7 (3b) | **Symptom-shift noise curves** (move t* to the symptom step) in addition to random flips | D2.1/D2.2 | FA's realistic noise model. |

## 4. Numeric checks fa_ideas made on our data (useful caveats)

- **Capture/retention reality check.** Under exact normalised string match, the gold answer appears anywhere in the failed Who&When history for only 13 of 145 usable trajectories (fa_ideas) / 7 of 96 (our stricter replication). Either way, under 10% of Who&When failures are retention failures; our idea #7 (capture/retention scan, rated 5) applies to MemTrace / SearchAuditBench / LongRCA, not to Who&When.
- **OAT in-domain AUROC (0.629) is below OOD (0.758)**, consistent with Who&When's early-error prior interacting with OAT's u = t/T time axis and query-initialised state.
- **Proxy-LLM ablation**: Llama-4-Scout / Gemma-4-31B / GPT-oss-120B embeddings lose little, so OAT's signal is content, not privileged internal state (supports our idea #2, proxy re-encoding).
- Dedup counts used by fa_ideas (MP-Bench reuses 177 of 289 Who&When logs; AgentRx's 44 Magentic-One traces are Who&When samples) match `report/3_core/mp_bench/mp_bench.tex` and `notes/agentrx.md`.

## 5. Overlap (same idea in both; which version to keep)

- Progress advantage baseline (A1) = our #1; ours adds the φ-equivalence validation against rollouts and TIES-merged references; fa_ideas adds cumulative-sum lock-in readout and advantage mass per agent for *who*. Merge.
- Observation-ablation / OIS / LUMINA (A2, C5.1, F2.1, F3.1) = our #8, B4a, A6.1, A7.1; fa_ideas adds the design rule "mask the evidence span, never random" and the dependency matrix D[t, j] as provenance for *who*. Merge.
- Hide-and-Seek port (B1) = our #6; fa_ideas quotes the peak lag (+0.07 to +0.11) vs onset (±0.016). Keep ours, add numbers.
- CanDist-FA (C1) = our #4; fa_ideas spells out the candidate set per dataset (Aegis → all steps of the agent; injected → [t_inj, symptom]; FaP → [t_err, t_lock]; ±k windows). Add that table to ours.
- HERO (D1/B2) = our #12; ModeX (C4) = our #15; DACA (C6) = our A3.1; LENS, CONDA, DaWin, TSV (B5), SpikeScore (A3), Focus (C2.1), GeoRanker/GeoArena (F9/F10), KDS = same ideas, same ratings.
- Weak/irrelevant lists agree: Gradient-Leading-Terms, MxD, TorchUMM, MetaMind, Vittle, Feature Resonance.

## 6. What ours has that fa_ideas lacks (keep)

- Proxy re-encoding as explicit infrastructure (#2) with the 0.83–0.98 proxy–generator NLL correlation.
- MAD-oracle freeze as a near-free exact repair testbed (F1.1); eruption-phase checkpoints as a natural-failure generator (CORE-SEAL); pressure-event injection with displaced errors (F4.1); anchored injection on label-free candidates (C3.2).
- Evaluation protocol items: leave-one-dataset-out, surface-perturbation invariance, AUPRC with position/sparsity stratification, three-timestamp evaluation, unified harness.
- Conformity/obstinacy/subversion cells and the Pólya-urn propagation model (F2.1, F2.3).

## 7. Suggested actions

1. Fix `futureworks.tex:201` and `notes/alternatives.md` (§1); add the positional baselines to `futureworks.tex:300` and Section 7.
2. Replace the purple note with the martingale-plus-evidence sentences (§2).
3. Fold the §3 table into `notes/failure_attribution_ideas.md` as new cards (suggested codes X1–X13) and raise B6 to plausibility 3–4.
4. Add fa_ideas' "contrastive OAT" and "position-only AUROC" to the next-week experiment list; both run on data already downloaded.
