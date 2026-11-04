# Failure attribution as a training signal for agents: literature synthesis

*Written 2026-10-28.* Direction: error localization / failure attribution (which step, which agent) used as a signal to **train the agent** (RL, DPO, SFT), as opposed to training an attributor (the subject of `failure_attribution_ideas.md`). Reference example given by the user: MiRL, arXiv:2610.35697.

Method: five parallel searches (Opus subagents) over 2024–2026 arXiv, each writing a structured file in `notes/lit_training_signal/`:

- `lit_A_error_targeted_rl.md` — error-targeted / restart-from-error RL (15 core + ~20 context)
- `lit_B_step_credit_rl.md` — step-level blame as RL credit (15 core + 18 lower-relevance + 16 unopened leads)
- `lit_C_attribution_sft.md` — attribution-driven SFT/DPO data construction (14 core + partials + controls)
- `lit_D_mas_blame_training.md` — multi-agent blame-based training (23 papers)
- `lit_E_critic_reward.md` — critics/attributors as reward; downstream experiments inside the attribution benchmarks

All 72 arXiv ids cited below were re-resolved through the arXiv API on 2026-10-28 and the titles match. Numbers were read by the subagents from arXiv HTML through a summarizer: re-check any figure against the PDF before quoting it in the report. Papers whose text and tables disagree are flagged in the per-file entries (PivoARL, ELPO, MAPPA, SHARP, AgentDebug).

---

## 1. Headline answers

- **The mechanism exists and works, but under other names.** The strongest 2026 agent-RL papers localize a decisive/pivotal/irrecoverable step and use it to (a) choose where rollouts restart, (b) edit the advantage at that step, or (c) truncate dense supervision after it. They call it "credit assignment", "pivotal turn", "error-localized", "critical step", not "failure attribution", and none of them cite Who&When, TraceElephant or AgenTracer as a source of signal.
- **No paper trains an agent with a benchmark-trained attributor** (AgenTracer-8B, Aegis-SFT/GRPO, a Who&When-Pro/TracerTraj/CORRECT-trained model) as reward, filter or restart selector. Every downstream experiment inside the attribution-benchmark papers (AgenTracer, AgentDebug, CORRECT, SearchAuditor, SymTrace, Conformal) is **inference-time**: attribution → prompt → re-roll/resume. Aegis, AgentRx, TraceElephant, Who&When Pro and MP-Bench have no downstream experiment.
- **No paper measures attribution accuracy against downstream training gain.** The one conceptual blueprint for MAS (2511.10687, "Who Gets the Reward & Who Gets the Blame?") has no experiments.
- **The recurring winning pattern is "propose, then verify, then credit":** an LLM (or the policy itself) proposes a blame step, Monte-Carlo continuations from the *current policy* confirm that the outcome actually flips there, and only then does the step shape credit or data (ELPO, ProVer, CSO, EEF, IPR/STeCa, AgentGrad). The cautionary paper 2610.17633 shows why: unverified LLM-judge "first mistake" labels on SWE-bench mostly sit *after* the step where success probability drops, and restarting from them does not help (−0.03 to −0.08), whereas restarting from the certified point of no return raises expected success 0.44 → 0.53 and from the measured restart point to 0.57.
- **Localization beats outcome-only in every clean ablation found** (Section 5), with gains of 3–15 points, but the dense/judge variants are fragile: fixed-weight judge rewards get hacked (VPPO "step inflation", AgentPRM, 2610.35497), so the working designs gate the step signal with the outcome (MiRL r = r_out ∧ r_judge; AgentEvolver α = 0.1–0.2; FAULT caps the penalty below the success–failure gap).

---

## 2. Taxonomy: how the signal is obtained × how it enters training

| Signal source → | Self-reflection by the policy | External LLM judge / PRM | Divergence from a reference run | MC / counterfactual rollouts | Verified-by-construction (injection, gold lineage) |
|---|---|---|---|---|---|
| **Restart / branch rollouts at the step** | PivoARL 2607.03702, R³L 2601.03715, SPROUT 2610.14405 | MiRL 2610.35697, RTI 2610.13438, SDPO 2501.01821, RoTS 2605.29447 | — | ELPO 2602.09598, PivotRL 2603.21383 (variance, no error), VSR 2610.15888 | CUA-Recovery 2610.27645 |
| **Advantage / reward edit at the step** | FAULT 2610.01161 | ETRO 2610.23048, AgentEvolver 2511.10395, CAPO 2508.02298, VPPO 2601.18984, MAPPA 2601.23228 (MAS) | — | ProVer 2609.36178, C3 2603.06859 (MAS), LVRL 2610.15840, HCAPO 2603.08754, SPA-RL 2505.20732, AgentPRM 2502.10325, GiGPO 2505.10978 | — |
| **Credit mask / truncation after the step** | PivoARL, R³L | ETRO, VPPO | — | ELPO (looser clip on suffix), EEF 2504.13145 (prefix masked) | AgentRefine 2501.01702 (error turns masked) |
| **SFT / DPO data at the step** | Agent-R 2501.11425 | GUI-Reflection 2506.08012, STeCa 2502.14276 (fix text) | EvoCUA 2601.15876, Skill-CDPO, dwDPO, ToolGraph 2606.23112 | CSO 2602.03412, IPR 2406.11176, STeCa, EEF | PALADIN 2509.25238, TermiGen 2602.07274 |
| **Task / environment selection** | — | SENTINEL 2606.12908 (12-category taxonomy), Agent-World 2604.18292, DataEnvGym 2410.06215, SwS 2506.08989 | — | — | — |
| **Prompt update of the blamed agent (MAS, no weights)** | — | HERA 2604.00901, LangMARL 2604.00722, MAPRO 2510.07475 | — | AgentGrad 2609.08572 (intervention-verified), HiveMind 2512.06432 (Shapley), Optimas 2507.03041 | — |
| **Inference-time feedback only** | — | AgentDebug 2509.25370, SearchAuditor 2608.05212, SymTrace 2608.25920, AgenTracer 2509.03312 (trained attributor), CORRECT 2509.24088, Conformal 2605.06788 | — | DoVer 2512.06749 | — |

---

## 3. Core papers by mechanism (verified; details in the per-file entries)

### 3.1 Restart or branch RL rollouts from the blamed prefix (MiRL's family)

- **MiRL** (2610.35697, Oct 2026, Bansal group). Qwen3.8-27B localizer labels each step good/bad from the prefix; a teacher writes a corrected step so the rollout continues; Claude Opus 5 clusters 12,746 error steps into types, 8 "misbehaviors" cover 52.1%. 640 prefixes → 219 survive deterministic replay. Reward r = tests pass ∧ Gemini judge says misbehavior avoided in the next 5 steps; DPPO on Qwen3.5-4B. TB-Lite 51.8 vs TMax-4B 47.4 at 35% of the rollouts; ablation: prefix start +7.9, behavior reward +6.5. Only paper that **re-attributes after training** (misbehavior recurrence −43 to −57% on unseen prefixes). Its prefix check verifies replay, not the label. Does not cite R³L, ELPO, PivoARL, SPROUT, RTI, SENTINEL.
- **PivoARL** (2607.03702). The policy writes a reflection naming the earliest wrong turn k*; retry from k* with the correct prefix; prefix steps inherit the retry's return, suffix does not ("pivotal isolation"); reflection rewarded by retry success. GiGPO, Qwen3-4B: agent-task avg 83.9 vs GiGPO 73.9. Localization accuracy not measured; authors name it the main limitation. Natural drop-in slot for an external attributor.
- **R³L** (2601.03715). Same loop, earlier: self-diagnosis gives k_pivot; restart with guidance; train on prefix + corrected suffix with the guidance stripped; gradient mask before k_pivot; ×3 positive amplification. 1.5B ALFWorld 0.72 → 0.93 vs GRPO.
- **ELPO** (2602.09598). **Counterfactual** localizer: binary search over tool-call anchors, sample suffixes, first anchor from which no suffix succeeds = first *irrecoverable* step, O(log K) probes within a 16-rollout budget. Tree branches there; hierarchical advantage; looser lower clip on the suffix. Tool-integrated math/code, 7B avg 60.7 vs GRPO 51.2; ablation without localization −2.3 on AIME24. Fig. 1: editing the first irrecoverable step recovers failures far more often than editing the "first error". This is TraceElephant's decisive-step definition computed online.
- **SPROUT** (2610.14405). SWE/terminal: filesystem + context checkpointed after every turn; the actor as analyst/reviewer (with verifier diagnostics) picks the parent attempt and turn boundary to branch from; children's loss masks cover only post-branch turns. Qwen3.8-27B TB-2.1 64.0 vs GRPO 39.3. Solves MiRL's container-state problem with snapshots instead of replay (MiRL loses 66% of prefixes).
- **RTI** (2610.13438). Only in all-fail GRPO groups: a rubric-aware validator (privileged) flags the wrong step, a corrector rewrites it, rollout continues; a success replaces one failed group member. Qwen3.5-9B Claw-Eval-Hard20 85.0 vs GRPO 52.5.
- **PivotRL** (2603.21383, NVIDIA) and **VSR** (2610.15888): start-state selection by outcome *variance* at expert turns, no error localization. The "variance instead of attribution" baseline MiRL should be compared to. **R3** (2402.05808) is the reverse-curriculum ancestor.

### 3.2 Advantage or reward edits localized to the blamed step

- **FAULT** (2610.01161, Oct 2026). A self-diagnoser sharing weights with the actor emits (error class, step index, verbatim quote); entries whose quote does not match are dropped; per-class error costs learned by regressing outcome on error rates; the terminal reward is redistributed as per-step penalties δ_t capped below the success–failure gap; GiGPO-style anchor advantages on top; diagnosis tokens get no gradient. ALFWorld 4B 91.0 vs GRPO 49.3 / GiGPO 73.9; signal coverage 95% vs 72% (GiGPO) / 41% (GRPO). Evaluates its blame against an LLM judge's decisive step: top-1 match 82/300 vs 21/300 for GiGPO's argmin, MRR 0.49 vs 0.30. **Closest existing thing to "a Who&When-style attributor as in-loop reward model".**
- **ETRO** (2610.23048). A frozen 27B writer picks the earliest decisive, unrecovered error k (Who&When's definition verbatim); on-policy distillation is positive on t<k, negative at t=k, absent after k (GRPO only). 7B WebShop 85.8 vs GRPO 73.7, ALFWorld 97.0 vs 81.2.
- **ProVer** (2609.36178). Agentic judge proposes a ≤4-turn pivotal segment explaining the success/failure difference; **verified** by K=8 current-policy continuations before/after the segment (Δ̂); bonus λ·Δ̂ on segment tokens, positive only. +9.9% / +7.1% relative to GRPO (Qwen3.5-2B/4B). Judge proposals accepted 58–72% vs 19.5% random. Open mirror: negative Δ̂ on the decisive *failure* segment.
- **AgentEvolver** (2511.10395, Alibaba). Qwen-Max labels every step GOOD/BAD in one pass; standardized attribution reward fused with outcome reward at α = 0.1–0.2. AppWorld+BFCL avg 41.3 → 47.6 (7B); attribution-only (35.7) is *worse* than outcome-only, so the gate matters.
- **LVRL** (2610.15840). A frozen LLM estimates state values in context; credit = value difference; LVOPD distils a teacher only on value-dropping steps. Up to +13.6 pp AppWorld, +8.6 pp SWE-bench Verified over GRPO. "Value drop = blame" with no explicit argmax step — the training-side analogue of the survey's hazard model (Proposal 2).
- **HCAPO** (2603.08754), **SPA-RL** (2505.20732), **AgentPRM** (2502.10325), **GiGPO** (2505.10978): implicit/soft attribution baselines (hindsight likelihood, learned progress decomposition, MC-labelled PRM, anchor-state grouping). GiGPO's credit exists only where states repeat, which is the coverage gap FAULT fills.
- **VPPO** (2601.18984, math) and **CAPO** (2508.02298, math): PRM/judge used *only* to find the first error; VPPO rewards a shortened good prefix and zeros the suffix. Rewarding the full prefix caused "step inflation". Gains small (+1.5–2 Avg@16; CAPO +1–3). VPPO is the clearest written argument that "first-error localization" is the right interface between a PRM and a reward.

### 3.3 Attribution-driven SFT / DPO data construction

- **CSO** (2602.03412, ACL 2026 Findings). On the policy's own failures, Claude-3.7 PRM scores each step and 5 expert alternatives; a candidate step needs policy < 0.45 and best alternative > 0.65; the **policy** continues from the alternative and the pair is kept only if the outcome flips. DPO at verified steps only (~16% of steps, 671 pairs). GAIA-Text 49.5 vs IPR 44.6, Step-DPO 38.9, ETO 38.9, SFT 35.9. Same definition as AgenTracer's counterfactual label, used as a data filter.
- **Agent-R** (2501.11425). Actor flags its first wrong step in an MCTS failed branch; splice bad prefix + revision phrase + good sibling suffix; iterative SFT. 70.7 vs ETO 65.1 vs splice-at-end 62.4 — the +8.4 over splice-at-end is the cleanest ablation of *where* you splice.
- **IPR** (2406.11176) / **STeCa** (2502.14276): MC step reward (N=5) along an expert prefix; first deviated step → step-DPO pair (IPR) or GPT-4o reflection + corrected action (STeCa). 69.4 / 70.9 vs ETO 66.4 / 66.9. Need expert trajectories.
- **EEF** (2504.13145): rollouts from evenly spaced states of *failed expert* trajectories; first state s_i where the policy succeeds from s_{i−l} but fails from s_i marks a harmful segment; train only from that state on. WebShop 62.0 vs RFT×6 53.6.
- **SDPO** (2501.01821, ACL 2025): GPT-4o marks the erroneous turn, resample from before it, segment-level DPO. Beats session-level ETO/DMPO.
- **CUA-Recovery / ReRail** (2610.27645): root-cause step from a gold per-step lineage (human-verified on test); replay the erroneous state with unrelated earlier errors repaired; verified recoveries → SFT with hints stripped. Error-awareness 35.2% vs 23.6% for a **token-matched success-only control**.
- **EvoCUA** (2601.15876), **GUI-Reflection** (2506.08012), **RoTS** (2605.29447, ICML 2026 spotlight): GUI agents; first divergence from a reference / GPT-4o first-error / reflector-proposed error node; correction pair at t* plus reflection pair at t*+1; +3 pts OSWorld (EvoCUA DPO stage), 14.6 → 34.7 (GUI-Reflection vs filtered BC).
- **AgentRefine** (2501.01702, ICLR 2025): errors synthesized, kept in context but masked from the loss; removing the mask drops SciWorld 7.7 → 3.3.
- **Agent Error Dataset** (2609.40111): 50k natural error–diagnosis pairs; "error-aware post-training" of the actor (action-only repair training +6.7 over success-only on WebShop-lite, single seed). Closest dataset-to-actor pipeline.
- **dwDPO** (EMNLP 2026 main, no arXiv): the implicit DPO reward finds the divergence step and an asymmetric kernel concentrates the loss there — turns ETO-style pairs into error-step-focused training without new data.
- Controls that are outcome-only or inference-only: ETO 2403.02502, NAT 2402.11651, SCoRe 2409.12917, Re-ReST 2406.01495, **ReTerm** 2610.18484 (recovery RL forked from the *end* of a failed run, no localization: TB-2.0 34.8 vs GRPO 28.0 — the "recovery without localization" contrast), AgentDebug, AgentRewind 2608.14380, TrajDebug 2608.06346, Traverse/Scout 2609.17930.

### 3.4 Multi-agent: blame as per-agent credit

- **Weight training with per-agent/per-message credit:** MALT 2412.01928 (MC tree value → per-role SFT/DPO), ACC-Collab 2411.00053, CollabUIAgents 2502.14496 (GPT-4o scores agent × round → DPO; w/o credit 29.3 → 25.0 AndroidWorld), MAPoRL 2502.18439, SiriuS 2502.04780 (repairs *every* agent, no blame), CoMAS 2510.08529 (zero-sum solver/critic reward; hacked without the scorer), MarsRL 2511.11373 (verifier rewarded on its verdict, not team outcome), **MAPPA** 2601.23228 (LLM coach scores every action and shifts blame upstream, e.g. a downstream FileNotFound is charged to the producer; REINFORCE++; AIME 49.2 → 66.7 on Qwen3-4B; **no shared-reward ablation**), **SHARP** 2602.08335 (leave-one-out agent masking; MuSiQue 47.0 → 50.8 vs broadcast reward), **C3 / "The Trace Is the State"** 2603.06859 (per-message counterfactual continuation with leave-one-out baseline as the PPO advantage; MATH500 82.8 vs MAGRPO 74.5; credit reliability collapses at 10 agents), CCPO/SEPO 2603.21563 (agent-removal counterfactual; explicit λ_blame term; gains non-uniform, some AMC/AIME cells drop), COSAC 2604.17693 (difference-reward theory; 10 questions).
- **Prompt/workflow updates of the blamed agent (no weights):** **AgentGrad** 2609.08572 (NeurIPS 2026: sequential intervention in reverse order, target = first agent whose corrected output makes the run succeed = Who&When's decisive error operationalized; +11.76 vs GEPA +9.24), HiveMind 2512.06432 (DAG-Shapley, AAAI 2026), LangMARL 2604.00722, MAPRO 2510.07475, TRUCE (ICML 2026), 2605.30227 (structural = which agent, temporal = which round), HERA 2604.00901, Optimas 2507.03041 (learned local reward ranks at 78% vs LLM judge 49.5%).
- **Blueprint only:** 2511.10687 (Shapley for successes; binary-search prefix judge finds the first harmful message in failures → repair-aware DPO pairs; "our contribution is conceptual").
- Shared-reward baselines/stabilisers: MAGRPO 2508.04652, Dr. MAS 2602.08847, M-GRPO 2511.13288.
- Observation: the prompt-level work (AgentGrad, HiveMind, TRUCE) already updates *only the culprit*; the RL side still uses dense per-agent credit. No MAS RL paper uses (agent, step) blame on GAIA/AssistantBench-style tasks.

### 3.5 Downstream experiments inside the attribution benchmarks (all inference-time)

| Paper | Feedback mechanism | Result |
|---|---|---|
| AgenTracer 2509.03312 | AgenTracer-8B `<think>` injected into the next round, ×3 | +4.8% OWL/GAIA, +14.2% MaAS/MATH-500; CRITIC baseline degrades |
| AgentDebug 2509.25370 | GPT-4.1 critical step + guidance, re-roll ≤5× | ALFWorld 21→55, 48→74 (units unstated); "training a debugger too expensive" |
| CORRECT 2509.24088 | restart from detected step vs random step | 10% → 20% on Who&When HC |
| SearchAuditor 2608.05212 | resume at critical step + repair directive | fix rate 17.4% vs 9.4% unguided retry, **5.6% generic hint at the same step**, 6.1% AgentRx repair |
| SymTrace 2608.25920 | one replay from the suspicious node, category-conditioned instruction | 20.15% vs 6.90% for three full reruns, 3.7% random node, 1.3% last node |
| Conformal 2605.06788 | roll back to the start of a conformal step set | ≈ top-1, within noise |
| TraceElephant, Aegis, AgentRx, Who&When Pro, MP-Bench | none | — |

SearchAuditor's generic-hint ablation shows localization alone is not enough: wrong guidance at the right step is *worse* than an unguided retry. SymTrace's Last-Node / Random-Node / Full-Rerun protocol is the right baseline set for any attribution-to-repair or attribution-to-training claim.

### 3.6 Critics and judges as reward (adjacent)

Agent-RLVR 2506.11425 (teacher guidance → guided success → DPO; SWE-bench V 9.4 → 22.4), Critique-GRPO 2506.03106 (ICML 2026; Prop. 4.1 formalizes why a first-error-localizing critique collapses search complexity), NLAC 2512.04601, CGI 2503.16024 (8B trained critic beats GPT-4o as critic, 61.4 vs 32.3), SRR-Judge 2602.07773, Text2Grad 2505.22338 (span-level ±1 token rewards → PPO), **CTRL** 2502.03492 (critic trained by GRPO with reward = "revision passes tests": the recipe for training an *attributor* on repair success instead of label agreement; PivoARL does this implicitly).

---

## 4. Cautionary evidence

- **Executable Prefix Values** (2610.17633, Oct 2026). mini-swe-agent on 150 SWE-bench Verified tasks, V(h_t) by adaptive bisection (~331 continuations per curve). Four frontier judges with a first-mistake rubric agree on the exact step in 21/57 cases; flag "mistakes" in 8/10 and 10/10 *successful* runs; for 66% of labels success probability does not drop at the labelled step; only 7/188 answers (abstract; 7/162 labels in §6.3) name the decisive step. Restart at the certified point of no return: 0.44 → 0.53; at the measured restart point: 0.57; at the judge label: −0.03 to −0.08. Re-checked on arXiv HTML 2026-10-28. Direct warning for MiRL/PivoARL/R³L-style restart from unverified blame, and support for PNR-style (TraceElephant) labels over judge labels.
- **Reward hacking of localizer-based rewards:** VPPO step inflation; AgentPRM validation process reward rises while success falls 82 → 70%; 2610.35497 (fixed-weight judge process reward hacked, decaying weight gives +45% relative on the longest task). Working guards: outcome gate (MiRL), small α (AgentEvolver), penalty cap (FAULT), no gradient to diagnosis tokens (FAULT).
- **Whether error-targeting itself helps is not isolated:** SENTINEL and Agent-World have no ablation removing the diagnosis; 2609.04128 ("Environment Evolution for Terminal Agents") finds weakness-targeted co-evolution *underperforms* off-policy environment evolution on TB-2.1 (62.9 vs 71.5).
- **Credit Without Ground Truth** (2608.19760): judge step-credit correlates with executed replay (Pearson 0.74) but orders steps poorly (Spearman 0.33); training utility "unestablished".
- **DoVer** (2512.06749): single (agent, step) blame is often ill-defined; 30–60% of attribution hypotheses validated or refuted by intervention.
- **Infrastructure dominates in terminal/SWE domains:** MiRL keeps 34% of prefixes by deterministic replay, 2610.17633 ~74%, SPROUT 100% by per-turn snapshots. The same Assumption (Replayability) as the survey's Proposal 1.

---

## 5. Does localization beat outcome-only? Clean ablations found

| Paper | Localized variant | Outcome-only control | Gain |
|---|---|---|---|
| Agent-R | splice at self-identified first error | splice at end | 70.7 vs 62.4 |
| CSO | DPO at verified critical steps | ETO / RFT / Step-DPO | 49.5 vs 38.9 / 34.9 / 38.9 |
| CUA-Recovery | recovery SFT from root-cause state | token-matched success-only SFT | 35.2 vs 23.6 EAR |
| CollabUIAgents | per-(agent, round) judge credit | trajectory-level DPO | 29.3 vs 25.0 |
| SHARP | leave-one-out agent credit | broadcast reward | 50.8 vs 47.0 |
| C3 | per-message counterfactual advantage | MAGRPO | 82.8 vs 74.5 |
| AgentEvolver | step attribution ⊕ outcome | outcome only | 47.6 vs 41.3 |
| MiRL | prefix start + behavior reward | TMax-189 | 51.8 vs 43.4 |
| ELPO | with binary-search localization | without | +2.3 / +2.0 AIME |
| AgentRefine | error turns masked | not masked | 7.7 vs 3.3 |
| ReTerm (contrast) | recovery from *end* state, no localization | GRPO | 34.8 vs 28.0 |

Gains are consistent but mostly 3–10 points; the biggest numbers (FAULT, PivoARL, ETRO vs GRPO) come from papers whose baselines may not be compute-matched.

---

## 6. Gaps and opportunities for the survey / proposals

1. **Close the loop with a benchmark-trained attributor.** Drop AgenTracer-8B (or a Who&When-Pro/CORRECT-trained model, or the survey's hazard model) into PivoARL's or MiRL's localizer slot and measure RL gain as a function of attribution accuracy. Nobody has done this; FAULT is the only paper that even scores its blame against a decisive-step judge. This is "attribution accuracy → training value", the missing evaluation axis.
2. **Verified negative credit at the decisive failure step.** ProVer verifies positive segments only; CSO uses expert alternatives; ELPO is tool-math. An MC-verified negative Δ̂ on natural agent failures is open, and it is exactly the repair-effect profile e_τ(k) of the survey's Definition (Proposal 1): the rollout screen *is* the credit signal (C3 computes it per message for 2-agent math).
3. **MAS RL with (agent, step) blame on realistic tasks.** Everything is 2-agent math (C3, CCPO) or conceptual (2511.10687). AgentGrad's intervention-verified target selection works for prompts; the RL analogue, "update only the culprit's weights / mask the others' advantages", is untested. SiriuS's brute-force loop over all agents is the obvious baseline.
4. **Attributor trained on repair success, not label match** (CTRL recipe; PivoARL implicitly): reward = resume-from-my-step succeeds. Fits the survey's observation that human labels disagree (40% exact-step agreement in LongRCA) and SearchAuditor's finding that directive content matters.
5. **Position-prior and last-step leakage** apply here as in the survey: judge labels drift toward symptoms (2610.17633), injected datasets skew late; any trained localizer used for restart selection inherits that skew.
6. **Baselines to require of any "attribution improves training" claim:** PivotRL/VSR (variance-selected start states, no attribution), ReTerm (recovery without localization), GiGPO/HCAPO (implicit credit), SymTrace's last/random node, and a generic-hint control at the predicted step (SearchAuditor).
7. **Relation to the survey's proposals:** ELPO / ProVer / CSO / EEF / 2610.17633 are existing instances of Proposal 1's counterfactual screen with N = 1–8 rollouts, used as a *training* signal rather than a label; LVRL / SPA-RL / HCAPO are value-function surrogates of Proposal 2's hazard, fitted online. The data-engine table (Section 8 of the report) already lists the replayable systems these methods run on (ALFWorld, WebShop, τ²-bench, SWE-bench, Terminal-Bench).

---

## 7. Unverified leads not opened (ids from search snippets only)

SWE-MILE 2609.32631, SWE-TRACE 2604.14820, SWE-Shepherd 2604.10493, "When Agents go Astray" 2509.02360, Fail-Fast Restart-Smart 2608.03222, "Learning What to Skip" 2609.30734, TreeHCA 2610.12828, ReCast 2610.11334, StepFinder 2606.03467, GraphTracer 2510.10581, LLM-MCA 2502.16863, EnvGen 2403.12014, AgentGen 2408.00764, COvolve 2603.28386, MASPRM 2510.24803, "Prefix Sampling (Zhu et al. 2026)" cited by 2610.17633 but not found. Named in the brief but not searched: EDGE-GRPO, Agent-R1, AgentQ. "BacktrackAgent" not found by name.
