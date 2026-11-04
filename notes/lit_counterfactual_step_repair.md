# Literature check: "which step is most effective to correct?" (2026-10-30)

Question: for a failed multi-step trajectory (agent run or a single LLM chain of thought), which step's
correction most raises the success probability, and how to measure that. Checked against web search on
2026-10-30. Report cross-references: Proposal 1 (repair-effect profile), Proposal 2 (hazard model),
Proposal 3 (training value); EPV = Shen et al. 2026 in `8_proposals/training_signal.tex`.

## Closest prior work (ordered by closeness)

| Paper | Setting | What is measured | Intervention | Rule for "the" step | Gap left |
|---|---|---|---|---|---|
| Repairs for Whom? Evaluator–Executor Mismatch (arXiv 2610.38610) | ALFWorld, WebShop, gridworld; single-step repairs | net gain p_e(h_t,a') − p_e(h_t,a_t) under executor rollouts (5–20 per branch) | candidate actions from 3 LLMs + planner + random | compares earliest-single-success (AgenTracer), latest-significant (Causal Agent Replay), single-replay-flip (CausalFlow), 2-of-3 (DoVer), judges | agents only; no graded effect ladder; not CoT; shows labels are executor-specific (62% self-agreement, 29–32% across models) and best position differs by 0.51 across positions |
| Executable Prefix Values (arXiv 2610.17633, "EPV") | SWE-bench Verified, frozen agents | V-curve of success from each prefix, certified point of no return | restart (no edit) | restart point / PNR / decisive step | damage curve only, no repair; already in report |
| CausalFlow (arXiv 2605.25338) | typed-step agents on GSM8K, MBPP, SealQA, MedBrowseComp | CRS = 1 if any of K=3 proposals flips the verifier; minimality score | LLM-proposed minimal edit of the step | all steps with CRS=1, consensus-filtered | binary, K=3; says plain CoT "provides no identifiable intervention points" |
| HPFA (arXiv 2608.02026) | single-LLM math/code traces, Qwen3-8B | success after replacing step j and resampling downstream | replacement from a paired successful trace | earliest j with a successful replacement | earliest-fix rule, not max-effect; no profile |
| InT (ICLR 2026, Yang et al.) | single-LLM math CoT | none (no branched rollouts) | model proposes a single-step fix from the reference solution | first error | training method; effect never measured |
| ELPO (ACL 2026, arXiv 2602.09598) | tool-integrated reasoning | binary-search rollout tree for first irrecoverable step | none | first irrecoverable step | lock-in, not repair |
| REFLECT (arXiv 2606.09071) | agent traces, silent failures | outcome flip after a diagnosis-specific patch in controlled replay | patch | verified flip refines attribution | single replay; agents |
| Thought Anchors (arXiv 2506.19143) | long CoT, R1-distill | answer-distribution shift when a sentence is resampled to a different one (100 rollouts) | resample-different | "anchors" = high counterfactual importance | resample tier only; successful and failed traces not separated by repair |
| Thought Branches (arXiv 2510.27484) | long CoT | counterfactual++ importance; "resilience" = how often removed content is regenerated downstream | resample / remove | — | shows corrections can be undone by the model; no repair profile |
| Forking Paths (ICLR 2025) / Forking Fast (arXiv 2608.19611) | single generation, token level | outcome distribution per token, change points | resample alternates | forking tokens | damage side only; Forking Fast cuts cost |
| Pivotal Token Search (Phi-4) / Critical Tokens Matter (arXiv 2411.19943) | math CoT | success-probability change per token (64 rollouts per token in CTM) | resample | pivotal / critical tokens | damage side; used for DPO |
| OmegaPRM (arXiv 2406.06592) / MC Net Information Gain (arXiv 2603.17815) | math CoT | MC success rate per prefix | none | first step where success collapses | damage curve; PRM labels |
| Causal Sufficiency and Necessity for CoT (NeurIPS 2025, arXiv 2506.09853) | math/commonsense CoT | PS, PN, PNS per step under interventions | step swap | used to prune/add steps | not applied to failed-trace attribution |
| Martingale Foresight Sampling (arXiv 2601.15482) | decoding | reasoning quality as a (sub)martingale, Doob step value | — | — | framing exists for decoding, not attribution |
| BIG-Bench Mistake (ACL Findings 2024) / ProcessBench (arXiv 2412.06559) | CoT | human first-error labels | — | first error | labels never validated by rollouts; ProcessBench 3-way agreement ≈ 48–53% on hard sets |
| Stated steps causally load-bearing? (arXiv 2609.27038) | multi-hop lookup, Qwen3 | activation patching vs text editing | — | — | behavioural text edits overstate causal effect by ≈11 pts |
| Hidden Error Awareness (arXiv 2605.09502) | CoT incl. R1 | probe detects errors (AUROC 0.85) but interventions fail to fix | steering, patching, self-correction | — | signal diagnostic, not causal |
| Conformal Certification of Reasoning Trace Prefixes (EMNLP 2026, arXiv 2605.30085) | process-labelled CoT | certified error-free prefix length | — | — | certification, not repair |

## Verdict

Done already: rollout-measured value curves per step in CoT (OmegaPRM, forking/pivotal/critical tokens,
Thought Anchors); rollout-measured single-step repair gain in agents with a comparison of selection rules
(Repairs for Whom?); earliest-fixable-step labels in CoT (HPFA, InT); point of no return in agents (EPV, ELPO).

Still open:
1. Graded repair-effect profile in single-LLM CoT with an information-controlled intervention ladder
   (resample / flag / hint / oracle). CausalFlow explicitly skipped CoT; Thought Anchors is the resample tier
   only; HPFA and InT use reference-solution fixes with a binary, earliest-step rule.
2. Validity of human first-error labels (ProcessBench, PRM800K, BIG-Bench Mistake) against measured repair
   effect. EPV did this for judge labels on SWE-bench; Repairs for Whom? showed executor dependence; nobody
   did it for the CoT human-labelled sets.
3. Max-effect vs earliest-fix vs largest-drop as rules, in CoT, with the fix window between them.
   Repairs for Whom? reports that earliest-success rules lose up to 0.58 and that no position wins in general,
   but only on agents.
4. Correction resilience in failed traces: Thought Branches shows reasoning models regenerate removed
   content in successful traces; the failed-trace counterpart (does the model re-derive its error after a
   correction?) is unmeasured and bears on the fix window.
5. Necessity/sufficiency per step as an attribution target for failed traces (the NeurIPS 2025 paper uses
   them for pruning).
6. A calibrated predictor of repair effect (not value) from the text or hidden states (Hidden Error
   Awareness and "road not taken" hidden-state dynamics suggest the signal is there).

Methodological consequences: name the continuation policy in every effect (executor dependence); use the
same model as executor in the CoT setting, which is its cleanest advantage; use Thought Anchors' released
code and Forking Fast for cost; report behavioural flips, which is the quantity wanted here, but do not
call them faithfulness.
