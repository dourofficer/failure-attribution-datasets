# Lit search B: step-level blame signals used as RL training signals for LLM agents

- Search date: 2026-10-28.
- Scope: 2024–2026 papers where a per-step signal identifying *which* step caused failure (error step, critical/pivotal step, counterfactual effect, value/progress drop) shapes rewards, advantages, or rollout starts when training the *agent*. Papers that only train an attributor are out of scope.
- Method: WebSearch to find candidates, then WebFetch on arxiv.org/abs and, for key papers, arxiv.org/html.
- **VERIFIED** means I opened the arXiv abs page (and the HTML page where details are cited). Numbers from HTML pages came through an automatic page summarizer. Re-check any number before putting it in the report; where the summarizer flagged internal inconsistencies in a paper, I note them.
- **UNVERIFIED** means the id came from search results only.

---

## 0. Quick map (core papers, ranked by relevance to failure attribution as a training signal)

| # | Paper | arXiv | Date / venue | Step signal | How it enters RL | Status |
|---|---|---|---|---|---|---|
| 1 | ELPO: Error-Localized Policy Optimization | 2602.09598 | Feb 2026, preprint | First *irrecoverable* step via binary-search rollout tree (MC) | Hierarchical tree advantage + looser lower clip on critical-step suffix | VERIFIED |
| 2 | FAULT (My FAULT: Self-Diagnosis as Credit Assignment) | 2610.01161 | Oct 2026, preprint | Self-diagnoser cites error step + quote, evidence-checked, priced by regression on outcomes | Terminal reward redistributed as per-step penalty; episode + anchor-state step advantage | VERIFIED |
| 3 | PivoARL: Pivotal-Aware Self-Feedback Retry | 2607.03702 | Jul 2026, preprint | Policy's own reflection names earliest erroneous turn k* | Retry from k* with correct prefix; prefix gets retry credit, suffix isolated; GiGPO advantages | VERIFIED |
| 4 | ProVer: Targeting Pivotal Decisions | 2609.36178 | Sep 2026, preprint | Agentic LLM judge proposes decisive segment, verified by before/after MC continuations | +Δ̂ added to GRPO advantage on segment tokens (positive only) | VERIFIED |
| 5 | ETRO: Distill Until Divergence | 2610.23048 | Oct 2026, preprint | Writer LLM picks earliest unrecovered *decisive* error k | Positive OPD on prefix, negative OPD at k, GRPO only on suffix | VERIFIED |
| 6 | CSO: Verified Critical Step Optimization | 2602.03412 | Feb 2026, ACL 2026 Findings | PRM-flagged candidate step + expert alternative + policy branch rollout that must succeed | DPO pairs at verified critical step only | VERIFIED |
| 7 | MiRL (reference example) | 2610.35697 | Oct 2026, preprint | LLM error localizer; recurring misbehaviors | RL rollouts restarted from error prefixes; behavior-gated reward | VERIFIED |
| 8 | C3: The Trace Is the State (exact credit for agent teams) | 2603.06859 | Mar–Oct 2026, preprint | Per-message counterfactual continuation (MC) with leave-one-out baseline | Used directly as PPO advantage for a 2-agent team | VERIFIED |
| 9 | LVRL: LLM Value Functions for Credit Assignment | 2610.15840 | Oct 2026, preprint | Frozen LLM in-context state value; step credit = value difference | Step-level advantage (vs GRPO's uniform); LVOPD distills only on value-dropping actions | VERIFIED |
| 10 | HCAPO: Hindsight Credit Assignment | 2603.08754 | Mar 2026, preprint | Same LLM as hindsight critic (action likelihood given final success state) | GRPO z-score + hindsight Q z-score | VERIFIED |
| 11 | SPA-RL: Stepwise Progress Attribution | 2505.20732 | May 2025, preprint | Learned progress estimator; per-step contributions sum to outcome | Dense PPO reward = progress + grounding | VERIFIED |
| 12 | AgentPRM (Choudhury) | 2502.10325 | Feb 2025, preprint | PRM trained on MC Q-targets | Policy maximizes PRM with KL (Online DPO); Best-of-N | VERIFIED |
| 13 | GiGPO: Group-in-Group Policy Optimization | 2505.10978 | May 2025, NeurIPS 2025 | Anchor-state grouping across group rollouts gives step relative advantage | Episode advantage + step advantage | VERIFIED |
| 14 | Who Gets the Reward & Who Gets the Blame? | 2511.10687 | Nov 2025, NeurIPS 2025 LAW workshop | Shapley credit (success) / first-error localization (failure) in multi-LLM systems | Proposed signed, credit-conserving rewards / repair-aware preferences (no experiments) | VERIFIED |
| 15 | Executable Prefix Values for Locating Agent Failures (evidence/caveat) | 2610.17633 | Oct 2026, preprint | Restart-based success probability V(h_t), point of no return | Not RL; shows judge first-mistake labels are bad restart points | VERIFIED |

Supporting evidence papers (§3) and lower-relevance verified papers (§4) are listed further down.

---

## 1. Methods that explicitly localize the error / decisive step and use it in agent training

### 1.1 ELPO — Learning from the Irrecoverable: Error-Localized Policy Optimization for Tool-Integrated LLM Reasoning
- **arXiv:** 2602.09598 — **VERIFIED** (abs + HTML)
- **Authors:** Qiao Liang, Yuke Zhu, Chao Ge, et al.
- **Date / venue:** v1 10 Feb 2026; no venue listed.
- **Domain:** Tool-integrated reasoning: AIME24/25, MATH500, GSM8K, MATH, GPQA-Diamond, LiveCodeBench-v6.
- **Step signal:** The first *irrecoverable* step, found by binary-search exploration (BEL).
  - It runs on failed trajectories (one is chosen per cycle by an entropy-gap score) under a fixed budget of 16 rollouts.
  - At each midpoint tool-call anchor, it fixes the prefix and samples 1–3 suffixes.
  - If any suffix succeeds, the prefix is "recoverable" and the search moves right; otherwise it moves left.
  - This takes O(log K) probes.
- **Entry into RL:**
  - Hierarchical advantage A = 0.5·A_branch + 0.5·A_traj. A_branch normalizes over sibling tree nodes, each node's value is the mean of its children, and A_traj is the group-normalized terminal reward.
  - Error-localized adaptive clipping: for tokens from the critical step onward, the lower PPO clip is loosened from 1−0.2 to 1−0.315, so negative-advantage tokens in the error suffix are penalized more strongly.
- **Algorithm / base:** GRPO-family. Qwen2.5-7B-Instruct and Qwen3-4B-Instruct-2507, with cold-start SFT on Open-AgentRL-SFT-3K and RL on Open-AgentRL-30K.
- **Result vs outcome-only:**
  - 7B average 60.7 vs GRPO 51.2 (best baseline DemyAgent 59.4). AIME24 48.1 vs GRPO 23.3.
  - 4B average 72.6 vs DemyAgent-4B 71.9.
  - The paper's text claims +2.2 / +1.0 over DemyAgent, but the table averages imply about +1.3 / +0.7; re-check.
  - Motivating experiment: editing the *first irrecoverable* step recovers failed problems far more often than editing a random error.
- **Relevance:** ELPO's "first irrecoverable step" is essentially TraceElephant's "decisive step = point where failure became unavoidable" and AgenTracer's counterfactual-flip definition, computed online by MC. It is the clearest evidence that the *decisive* step, not just any error, is the right place to concentrate negative credit.

### 1.2 FAULT — My FAULT: Self-Diagnosis as Credit Assignment in Self-Evolving Agentic Reinforcement Learning
- **arXiv:** 2610.01161 — **VERIFIED** (abs + HTML)
- **Authors:** Yihua Zhu, Qianying Liu, Weixu Qiao, et al. (13 authors).
- **Date / venue:** v1 1 Oct 2026; preprint.
- **Domain:** ALFWorld, WebShop (long-horizon), Search-QA (short-horizon).
- **Step signal:** A self-diagnoser that shares weights with the actor and is cold-started by SFT on verified teacher diagnoses.
  - After each rollout it emits structured entries: error class from a fixed taxonomy, step index, and an exact quote from that step.
  - Entries whose step or quote do not match the trajectory are dropped (95.4% of teacher mentions passed).
  - Per-class relative error costs w_k are learned by regressing task success on error rates (conditional likelihood, refit periodically on recent rollouts).
- **Entry into RL:**
  - A trajectory penalty budget P = λ·clip(Σ_k w_k·x_k, 0, 1), capped below the success–failure reward gap.
  - P is split across steps in proportion to the priced errors cited at each step (δ_t), giving per-step returns E_t = R_out − δ_t.
  - Joint advantage = episode-level group advantage + ω·anchor-state step advantage (GiGPO-style).
  - Diagnosis tokens get no policy gradient, so the agent cannot game its own blame.
- **Algorithm / base:** GRPO/GiGPO-style. Qwen3-1.7B and Qwen3-4B-Instruct-2507.
- **Result vs outcome-only:**
  - ALFWorld (all unseen), 4B: 91.0 vs GRPO 49.3 / GiGPO 73.9. 1.7B: 68.7 vs 43.3 / 41.8.
  - WebShop score, 4B: 88.5 vs 67.8 / 68.5.
  - Search-QA, 4B: 43.8 vs 39.7 / 40.8.
  - SEED is close on several metrics.
  - The baselines are trained from the raw backbone, so check data/compute matching.
- **Localization quality:** Evaluated against an LLM judge's decisive-error step on 300 failed trajectories.
  - MRR 0.494 vs GiGPO 0.303 vs random 0.266.
  - The most-penalized step matches the judge in 82/300 trajectories vs 21/300 for GiGPO.
  - Signal coverage on same-outcome groups: 95.1% vs GiGPO 72.5% vs GRPO 41.4%.
- **Relevance:** This is the closest existing system to "a Who&When-style attributor as an in-loop reward model": a step-level blame emitter with evidence checks whose blame becomes per-step reward penalties. It also evaluates its blame with a decisive-error-step metric, like Who&When.

### 1.3 PivoARL — Agent Reinforcement Learning via Pivotal-Aware Self-Feedback Retry
- **arXiv:** 2607.03702 — **VERIFIED** (abs + HTML)
- **Authors:** Weiyang Guo, Zesheng Shi, Longhui Zhang, et al.
- **Date / venue:** v1 4 Jul 2026; no venue listed.
- **Domain:** ALFWorld, WebShop, Minesweeper, SciWorld (plus Sokoban), and 7 search-QA sets (NQ, TriviaQA, PopQA, HotpotQA, 2Wiki, MuSiQue, Bamboogle).
- **Step signal:** After a failed episode, the *same policy* writes a structured reflection with a pivotal turn index k* (the earliest erroneous turn) and a textual remark. This is self-judged, with no external verifier.
- **Entry into RL:**
  - The next episode reuses the prefix before k* and regenerates from k*, with the remark injected.
  - Pivotal-isolated cross-episode credit: prefix steps get their own return plus γ·(the retry's starting return); suffix steps (t ≥ k*) get only their own return, so the bad suffix never inherits the retry's success.
  - Advantages are GiGPO episode + step terms.
  - The reflection is rewarded by the success-gated return of its retry ("implicit reflection returns").
  - Pivotal turns also yield contrastive preference signals.
- **Algorithm / base:** GiGPO; Qwen3-4B; 3 episodes per trial.
- **Result vs outcome-only:**
  - Agent-task average 83.9 vs GiGPO 73.9, GRPO 67.9, MetaRL 75.9.
  - Minesweeper Suc@3 78.1 vs GiGPO 48.4.
  - Search Pass@3 average 56.9 vs GiGPO 47.2, GRPO 46.4.
  - The abstract and §4.2 state different margins over MetaRL (11.5% vs 10.5%).
  - No quantitative localization accuracy is reported; the authors list localization errors as the main limitation.
- **Relevance:** The same mechanism as MiRL (restart from the blamed prefix), but with the policy itself as the attributor, trained only through retry success. A drop-in place to substitute an external attributor (AgenTracer-8B or a Who&When-trained model) and measure whether better step accuracy turns into better RL.

### 1.4 ProVer — Targeting Pivotal Decisions for Credit Assignment in Agentic Reinforcement Learning
- **arXiv:** 2609.36178 — **VERIFIED** (abs + HTML)
- **Authors:** Dongwon Jung, Hemanth Neelgund Ramesh, Yifan Wang, et al.
- **Date / venue:** v1 28 Sep 2026; no venue listed.
- **Domain:** ALFWorld, WebShop, SearchQA.
- **Step signal:**
  - An *agentic* LLM judge (gpt-5.4-mini by default; a local Qwen3.5-9B was also tested) gets the task, the shortest successful trajectory in the group, and truncated previews of the failed ones, plus search and inspection tools.
  - It proposes one contiguous segment of at most 4 turns that explains the outcome difference.
  - The segment is **verified** by restoring the states before and after it and running K = 8 current-policy continuations from each: Δ̂ = success_after − success_before.
- **Entry into RL:**
  - A_u = A_GRPO + λ·Δ̂·1[u in segment] if Δ̂ > 0, applied to the successful source trajectory only (λ = 1).
  - Segments with Δ̂ ≤ 0 get nothing; there is no negative credit.
- **Algorithm / base:** GRPO; Qwen3.5-2B and Qwen3.5-4B.
- **Result vs outcome-only:**
  - Average 59.43 vs GRPO 54.07 / GiGPO 55.53 (2B); 64.40 vs GRPO 60.12 / GiGPO 59.90 (4B). That is +9.91% / +7.12% relative to GRPO.
  - Also beats CriticSearch and SPO at 38% lower judge cost.
  - Proposal acceptance (Δ̂ > 0) is 58.5–72.4% for the judge vs 19.5% for random segments.
- **Relevance:** A "propose with an LLM judge, then verify counterfactually" pipeline, the same split as Who&When-style LLM attribution followed by AgenTracer-style replay. It uses the *success-side* mirror of failure attribution. The natural extension, and an open gap, is applying negative Δ̂ to the decisive failure segment.

### 1.5 ETRO — Distill Until Divergence: Error-Truncated Hindsight Distillation for Agentic RL
- **arXiv:** 2610.23048 — **VERIFIED** (abs + HTML)
- **Authors:** Yibin Huang, Conghui Zhu.
- **Date / venue:** v1 16 Oct 2026; no venue listed.
- **Domain:** WebShop, ALFWorld, Search QA (7 datasets).
- **Step signal:**
  - A frozen Qwen3.5-27B "writer" reads the task, the full trajectory, and the outcome.
  - It picks the **earliest error that later actions do not recover from and that is decisive for the failure**; a format violation alone does not count.
  - If no error is confidently identified, k = ∞.
  - It also writes a positive skill and at most one negative skill.
- **Entry into RL:** Polarity-routed on-policy (self-)distillation added to the GRPO advantage, A = A_GRPO + 0.001·A_OPD.
  - Positive OPD on successful trajectories and on failed prefixes (t < k).
  - Negative OPD at the error turn (t = k).
  - No OPD after k (GRPO only), i.e. **truncation of dense supervision at the decisive error**.
- **Algorithm / base:** GRPO + OPD; Qwen2.5-Instruct 1.5B, 3B, 7B.
- **Result vs outcome-only:**
  - 7B: WebShop 85.8 vs GRPO 73.7; ALFWorld 97.0 vs 81.2; Search QA 51.8 vs 42.0.
  - 1.5B WebShop: 80.8 vs 62.0.
  - Non-ETRO baseline numbers are copied from prior reports.
- **Relevance:** Its error definition is essentially Who&When's "decisive error", and it is the most literal "stop learning at the mistake" design: credit to the prefix, blame at k, nothing dense after k.

### 1.6 CSO — Verified Critical Step Optimization for LLM Agents
- **arXiv:** 2602.03412 — **VERIFIED** (abs + HTML)
- **Authors:** Mukai Li, Qingcheng Zeng, Tianqing Fang, et al.
- **Date / venue:** v1 3 Feb 2026, v2 29 Apr 2026; **ACL 2026 Findings**.
- **Domain:** Deep research / web agents: GAIA-Text-103, XBench-DeepSearch.
- **Step signal:**
  - Claude-3.7-Sonnet acts as a rubric PRM, scoring each step's action in [0, 1].
  - A step is a candidate if the policy's action scores < 0.45 and the best of K = 5 expert alternatives (also from Claude) scores > 0.65.
  - The **policy** then rolls out from the alternative, and only branches that reach a correct outcome are kept. This is a verified counterfactual flip at the critical step.
- **Entry into training:** DPO pairs (verified alternative vs original failed action) at the critical step only; β = 0.5; 671 pairs; up to 2 iterative rounds. Preference optimization, not on-policy RL.
- **Base:** CK-Pro-8B (SFT on Qwen3-8B).
- **Result:**
  - GAIA-Text-103: 49.5 vs SFT 35.9, outcome-level ETO 38.9, Step-DPO 38.9, IPR 44.6.
  - XBench: 29 vs SFT 23.
  - Supervises only ~16% of steps.
  - No GRPO baseline.
- **Relevance:** Operationalizes AgenTracer's decisive-step definition ("the earliest action that, if corrected, flips failure to success") as a *training-data* filter. Shows that verified critical-step pairs beat both trajectory-level and dense step-level preferences.

### 1.7 MiRL — Error-Targeted Reinforcement Learning for Correcting Terminal Agent Misbehaviors (reference example)
- **arXiv:** 2610.35697 — **VERIFIED** (abs)
- **Authors:** Runchu Tian, Zaid Khan, Zun Wang, et al.
- **Date / venue:** v1 26 Oct 2026; preprint.
- **Domain:** Terminal agents (Terminal-Bench).
- **Step signal:** An LLM error localizer profiles wrong steps into recurring misbehaviors: on Qwen3.5-4B, 8 misbehaviors cover 52.1% of wrong steps.
- **Entry into RL:**
  - Rollouts start from prefixes just before the error steps; a prefix is kept only if replaying its commands reproduces the recorded outputs.
  - Reward = tests pass AND a behavior judge confirms the misbehavior was avoided.
- **Result:**
  - Terminal-Bench Lite 51.8 vs TMax-4B 47.4; TB 2.1: 21.3 vs 20.6, using 35% of the rollouts.
  - Misbehavior repetition drops 43–57% on unseen prefixes.

---

## 2. Counterfactual / Monte-Carlo / value-based step credit (implicit "which step mattered")

### 2.1 C3 — The Trace Is the State: Exact Credit Assignment for LLM Agent Teams
- **arXiv:** 2603.06859 — **VERIFIED** (abs + HTML)
- **Authors:** Yanjun Chen, Yirong Sun, Hanlin Wang, et al.
- **Date / venue:** v1 6 Mar 2026 … v4 7 Oct 2026. The title changed in v3 (earlier versions are cited as "C3, contextual counterfactual credit"). No venue listed.
- **Domain:** Multi-agent (2-agent) LLM workflows on math: MATH500, AIME25, CMATH, GSM8K; long-generation setting with Minerva-Math and AMC23.
- **Step signal:**
  - For each decision point (message), sample n alternative messages and run c_j continuations of each to the terminal reward, regenerating only downstream messages.
  - Â_j = Q̂(h, a_j) − b_{−j}, where b_{−j} is the leave-one-out mean of the other alternatives.
  - Rank correlation with a 16-continuation reference is 0.69 at 4 continuations (two references agree at ~0.73); a trained critic reaches only 0.29.
- **Entry into RL:** Used directly as the advantage in a PPO clipped surrogate.
- **Base:** Qwen3-4B-Instruct-2507.
- **Result:**
  - MATH500 82.8 vs MAGRPO 74.5 vs MAPPO 69.3; AIME25 8.0 vs 5.3 vs 3.3.
  - Uses 37% fewer training tokens than MAPPO.
- **Relevance:** Message-level counterfactual replay is exactly the AgenTracer labeling procedure, here used online as a multi-agent advantage. It is the most direct bridge from Who&When-style "which agent, which step" blame to MAS RL, though only on short math workflows.
- **Related, VERIFIED:** CCPO, "Counterfactual Credit Policy Optimization for Multi-Agent Collaboration", arXiv 2603.21563 (Mar–Jun 2026).
  - Agent-removal counterfactual marginal contribution gives role-specific rewards for GRPO/GSPO/REINFORCE++ in a Think–Solve dual-agent math setup.
  - The abstract reports mixed gains and no numbers.

### 2.2 LVRL — LLM Value Functions for Credit Assignment in Agentic RL
- **arXiv:** 2610.15840 — **VERIFIED** (abs)
- **Authors:** Kaijie Zhu, Weixiang Yan, Omar Attia, et al.
- **Date / venue:** v1 11 Oct 2026; no venue listed.
- **Domain:** AppWorld, BabyAI, SWE-bench Verified.
- **Step signal:**
  - A frozen LLM estimates policy-aware state values in context, without critic fine-tuning. It is conditioned on group rollouts and calibrated on known initial and terminal values.
  - Step credit = the change in value.
  - An MC analysis says the critic identifies semantic "pitfalls" and "recoveries". A search snippet gives 72% / 66%, which I did not see on the abs page.
- **Entry into RL:**
  - LVRL replaces GRPO's uniform trajectory advantage with value-difference advantages.
  - LVOPD applies teacher distillation only on actions whose estimated value *drops*, i.e. blamed steps.
- **Base:** Policies from 4B to 32B.
- **Result:**
  - Beats GRPO and PPO at all scales: up to +13.6 pp on AppWorld and +8.6 pp on SWE-bench Verified over GRPO.
  - BabyAI goes from 0 to 75.0%.
- **Relevance:** "Value drop = blame" computed by an off-the-shelf LLM. Directly comparable to using a prompted Who&When attributor, but with a value-function interface instead of an argmax step.

### 2.3 HCAPO — Hindsight Credit Assignment for Long-Horizon LLM Agents
- **arXiv:** 2603.08754 — **VERIFIED** (abs + HTML)
- **Authors:** Hui-Ze Tan, Xiao-Wen Yang, Hao Chen, et al.
- **Date / venue:** v1 7 Mar 2026; no venue listed.
- **Domain:** WebShop, ALFWorld, search-augmented QA.
- **Step signal:**
  - The policy LLM acts as a hindsight critic: π_hind(a_t) is the action's likelihood conditioned on s_t and the successful final state.
  - ρ_t = clip(π_hind / mean π_hind, 0.8, 1.2), and Q^H = ρ·γ^{T−t}·R.
- **Entry into RL:**
  - A = GRPO z-score + ω·z(Q^H).
  - A "do-no-harm" mask zeroes negative hindsight signals in successful trials.
- **Base:** Qwen2.5-Instruct 1.5B/3B/7B.
- **Result (7B):**
  - WebShop 73.8 vs GRPO 66.1.
  - ALFWorld 91.4 vs GRPO 77.6 (96.9 with temporal smoothing).
  - Roughly on par with GiGPO (90.8 / 72.8).
- **Relevance:** A cheap, rollout-free per-step reweighting with no explicit error localization. A useful "implicit attribution" baseline to compare against explicit decisive-step blame.

### 2.4 AgentPRM — Process Reward Models for LLM Agents: Practical Framework and Directions
- **arXiv:** 2502.10325 — **VERIFIED** (abs + HTML)
- **Author:** Sanjiban Choudhury.
- **Date / venue:** 14 Feb 2025; no venue listed.
- **Name clash:** Do not confuse with Xi et al., "AgentPRM … Step-Wise Promise and Progress", 2511.08325 (VERIFIED, Nov 2025). That paper uses TD+GAE labels, focuses mainly on test-time scaling, and uses RL only as analysis.
- **Domain:** ALFWorld (136 out-of-distribution games).
- **Step signal:**
  - A PRM trained with soft BCE on Monte-Carlo Q-targets: the mean discounted return over all visits to hashed (s, a) pairs in previous-policy rollouts.
  - InversePRM learns process rewards from demonstrations instead.
- **Entry into RL:** Each iteration maximizes the PRM with a KL penalty to the previous policy. The paper says PPO, Online DPO, or rejection sampling would work; experiments use Online DPO. Best-of-N is used at test time.
- **Base:** Llama-3.2-3B for both policy and PRM.
- **Result:**
  - π0 (SFT) 64.9 → π1 73.9 → π2 85.8 → π3 88.1; BoN-16 reaches 91.0.
  - GPT-4o ReAct 65.7; Claude-3.5-Sonnet ReAct 76.1.
  - InversePRM: 63.4 → 86.6.
- **Relevance:** The canonical "MC-labelled agent PRM drives policy improvement" recipe. A failure-attribution-trained model could be swapped in as the PRM, using argmin-step blame as a negative step reward.

### 2.5 SPA-RL — Reinforcing LLM Agents via Stepwise Progress Attribution
- **arXiv:** 2505.20732 — **VERIFIED** (abs + HTML)
- **Authors:** Hanlin Wang, Chak Tou Leong, Jiashuo Wang, Jian Wang, Wenjie Li (PolyU).
- **Date / venue:** 27 May 2025; no venue listed on the abs page.
- **Domain:** ALFWorld, WebShop, VirtualHome.
- **Step signal:**
  - A progress estimator (an MLP on the last hidden state of an LLM) outputs a per-step contribution c_t.
  - It is trained so that Σ_t c_t regresses (MSE) to the outcome reward over 10 exploration rollouts per task.
  - This is a learned reward decomposition, a form of attribution.
- **Entry into RL:** Dense reward r_t = c_t + 0.5·g_t, where g_t indicates the action is executable, optimized with PPO + GAE.
- **Base:** Llama-3.2-3B-Instruct for both agent and estimator.
- **Result:**
  - ALFWorld unseen 79.1 vs PPO 73.9, GRPO 70.9, RLOO 71.6, StepAgent 75.4, PRM4A 73.9.
  - WebShop 64.1 and VirtualHome 53.4, each about +1 point over RAGEN.
- **Relevance:** "Progress attribution" is a soft, additive version of failure attribution. The steps with the lowest c_t in a failed trajectory are its implicit blame, which makes SPA a natural baseline for any explicit decisive-step reward.

### 2.6 GiGPO — Group-in-Group Policy Optimization for LLM Agent Training
- **arXiv:** 2505.10978 — **VERIFIED** (abs)
- **Authors:** Lang Feng, Zhenghai Xue, Tingcong Liu, Bo An.
- **Date / venue:** v1 May 2025, v3 Oct 2025; **NeurIPS 2025**.
- **Domain:** ALFWorld, WebShop, search-augmented QA.
- **Step signal:** Anchor-state grouping. Identical environment states that recur across group rollouts form step-level groups, and actions from the same state get a relative advantage from their discounted returns. Critic-free and needs no extra rollouts.
- **Entry into RL:** Episode-level group advantage + step-level advantage.
- **Base:** Qwen2.5-1.5B/3B/7B-Instruct.
- **Result:**
  - Abstract: >12% over GRPO on ALFWorld and >9% on WebShop.
  - At 7B (as reproduced in HCAPO): ALFWorld 90.8 vs 77.6; WebShop 72.8 vs 66.1.
- **Relevance:** The de-facto baseline and backbone (PivoARL and FAULT build on it). Its step credit only exists where states repeat, which is exactly the coverage gap FAULT's explicit blame fills (95% vs 72% coverage).

---

## 3. Multi-agent blame framework and evidence on the reliability of step-blame signals

### 3.1 Who Gets the Reward & Who Gets the Blame? Evaluation-Aligned Training Signals for Multi-LLM Agents
- **arXiv:** 2511.10687 — **VERIFIED** (abs)
- **Authors:** Chih-Hsuan (Bella) Yang, Tanwi Mallick, Le Chen, et al.
- **Date / venue:** v1 Nov 2025; v2 withdrawn; v3 Jul 2026; NeurIPS 2025 LAW workshop.
- **Domain:** LLM multi-agent systems; conceptual.
- **Signal:**
  - On success: Shapley allocation across agents, refined into per-message rewards.
  - On failure: first-error localization of the earliest harmful step, which yields repair-aware preferences that penalize the harmful step and reward corrective attempts.
- **Entry into training:** Bounded, signed, credit-conserving signals described as compatible with RL or preference post-training. **No experiments.**
- **Relevance:** The only paper found that explicitly proposes Who&When-style failure attribution as the MAS training signal. It is a position/framework paper, so the empirical gap remains open.

### 3.2 Executable Prefix Values for Locating Agent Failures (caveat)
- **arXiv:** 2610.17633 — **VERIFIED** (abs)
- **Authors:** Bingyu Shen, Jiaqi Tang, Lan Wei, et al.
- **Date / venue:** 13 Oct 2026; preprint.
- **Method:** Restart the agent from reconstructed intermediate states of failed SWE-bench Verified runs (150 tasks, 2 open-weight agents) to estimate V(h_t) and a certified point of no return (PNR).
- **Findings on judge labels:** First-mistake labels from 4 frontier judges (Traverse rubric) often describe symptoms, not causes.
  - Cross-lineage judges agree on the exact step in only 21/57 cases.
  - The newest judges flag "mistakes" in 8/10 and 10/10 *successful* runs.
  - For 66% of labels, success probability does not drop at the labelled step.
  - Only 7/188 answers name the decisive step.
- **Restart experiment:** Restarting at the PNR raises expected success from 0.44 to 0.57; restarting at the judge's label changes it by −0.08 to −0.03.
- **Relevance:** Direct warning for MiRL/PivoARL-style "restart RL from the blamed step": unverified judge blame can be useless as a restart point. Argues for MC-verified decisive steps (as in ELPO, ProVer, CSO) and supports TraceElephant's PNR-style labels over judge labels.

### 3.3 Neglected Free Lunch from Post-training: Progress Advantage for LLM Agents
- **arXiv:** 2606.26080 — **VERIFIED** (abs + HTML)
- **Authors:** Changdae Oh, Wendi Li, Seongheon Park, et al. (the group includes Sharon Li).
- **Date / venue:** 24 Jun 2026; no venue listed.
- **Signal:** Step score = log π_RL(a|s) − log π_ref(a|s), argued to recover the optimal advantage. Needs no annotation and no trained PRM.
- **Use:** Failure attribution on **Who&When** by taking the argmin step. It is said to approach or rival AgenTracer on the Hand-Crafted split; exact numbers are only in Fig. 2. The paper also covers test-time scaling and uncertainty quantification.
- **Not used for RL training.**
- **Relevance:** Evidence that RL post-training already encodes step-level blame usable on Who&When. That blame could close the loop as a free dense credit signal in the next RL round; untested.

### 3.4 When Fine-Grained Credit Assignment Helps and Hurts: Multimodal Agentic RL through Video Editing
- **arXiv:** 2610.35497 — **VERIFIED** (abs)
- **Authors:** Lei Zhao, Zongheng Cao, Xinyu Hu, et al.
- **Date / venue:** 26 Oct 2026; preprint.
- **Setup:** LLM-judge process rewards added to outcome-only GRPO; four trailer-editing tasks of 30–60+ turns.
- **Findings:**
  - A *fixed* process-reward weight leads to reward hacking: the process reward rises while task outcomes fall.
  - A *decaying* weight gives +45.4% relative on the longest task (Fine Cut) and at most +10.4% on the shorter ones, where outcome-only GRPO stays competitive.
  - OPSD (on-policy self-distillation with privileged information) gives little gain or degrades.
- **Relevance:** Practical guidance: judge-based step blame should be annealed or anchored to outcomes, which FAULT does by capping the penalty below the success–failure gap.

### 3.5 Agent Error Dataset: Scaling 50,000 Error–Diagnosis Pairs for Failure Analysis and Error-Aware Post-Training
- **arXiv:** 2609.40111 — **VERIFIED** (abs)
- **Authors:** Kunlun Zhu, Xuyan Ye, Yibo Li, … Heng Ji.
- **Date / venue:** 30 Sep 2026; preprint.
- **Method:** The AET pipeline collects natural failures from 23 policies, then diagnoses, corrects, and checks them against evidence, with replay-verified corrections where possible.
- **Findings:**
  - Qwen3-8B exact-step agreement rises from 47.2% to 63.6% after diagnosis fine-tuning.
  - First-proposal corrections raise verifier pass rate from 18.4% to 51.1%.
  - Action-only repair training beats success-only training by +6.67 on WebShop-lite (single seed).
- **Relevance:** A failure-attribution dataset used for *actor* post-training (SFT-style, not RL). The closest dataset-to-agent pipeline found.

### 3.6 Credit Without Ground Truth: Claim-Matched Evaluation of Step-Level Credit with Finite Executed Replay
- **arXiv:** 2608.19760 — **VERIFIED** (abs)
- **Author:** Haiyue Zhang (single author).
- **Date / venue:** Aug–Oct 2026, v3; no venue listed.
- **Setup:** An ALFWorld audit of step-credit signals against two independent executed-replay banks.
- **Findings:**
  - Cross-bank association Pearson 0.736 but pooled Spearman 0.330.
  - Judge alignment is modestly positive.
  - Training utility is "unestablished".
- **Relevance:** A low-weight caution that step-credit signals need replay-based validation.

---

## 4. Also checked (VERIFIED arXiv pages; lower relevance or no explicit blame step)
- **Tree-GRPO**, "Tree Search for LLM Agent Reinforcement Learning", 2509.21240, ICLR 2026. Tree rollouts with shared prefixes give within- and across-tree step advantages from outcome reward alone.
- **ARPO**, "Agentic Reinforced Policy Optimization", 2507.19849, Jul 2025. Entropy-triggered branching after tool calls plus step-level advantage attribution; uses half the tool budget.
- **Thinking vs. Doing (TTI)**, 2506.07976, Jun 2025. *Not* step credit: curriculum RL that scales the interaction horizon (Gemma-3-12B; WebVoyager, WebArena).
- **AgentPRM (Xi et al.)**, 2511.08325, Nov 2025. Promise/progress PRM with TD+GAE labels; mainly test-time scaling, with RL only as analysis.
- **Turn-PPO**, 2512.17008, EACL 2026. Turn-level MDP for PPO (WebShop, Sokoban); argues PPO is more robust than GRPO for multi-turn.
- **MT-GRPO**, "Reinforcing Multi-Turn Reasoning in LLM Agents via Turn-Level Credit Assignment" (v1 title; v3 retitled "...Fine-Grained Reward Structure and Credit Assignment"), 2505.11821, 2025–2026. Verifiable per-turn rewards; v1 reports 100% tool execution and 50% EM vs 20–30% for baselines.
- **iStar**, "Agentic Reinforcement Learning with Implicit Step Rewards", 2509.19199, Sep 2025. Implicit PRM via trajectory DPO; step + episode advantages (WebShop, VisualSokoban, SOTOPIA).
- **CARL**, "Criticality-Aware Agentic RL", 2512.04949, Dec 2025–May 2026. Entropy as a criticality proxy; updates only on high-criticality actions.
- **SCPO**, "Semantic Consistency Policy Optimization", 2606.25852, Jun 2026, under review at EMNLP 2026. Failed steps get positive credit for progress shared with a successful sibling; 1.5B: ALFWorld 93.7, WebShop 74.8.
- **TRACE**, "Turn-level Reward Assignment via Credit Estimation", 2607.13988, Jul 2026. TD of frozen-reference gold-answer log-ratio values; BrowseComp-Plus 7.2→35.6 (Qwen3-4B).
- **CrEST**, "Teach the Magnitude, Not the Direction", 2608.13179, Aug–Oct 2026. Verifier-anchored sign, self-teacher magnitude; BFCL V3.
- **VPR**, "Verifiable Process Rewards for Agentic Reasoning", 2605.10325, May–Oct 2026. Oracle action-level verifiers (Sokoban, Sudoku, Minesweeper, τ²-bench); beats GRPO and VinePPO on Qwen3-4B.
- **RTMC**, "Step-Level Credit Assignment via Rollout Trees", 2604.11037, Apr 2026. Pools returns over shared states; +3.2 pass@1 over GRPO on SWE-bench Verified.
- **CAPO**, "Towards Enhancing LLM Reasoning through Generative Credit Assignment", 2508.02298, 2025. An off-the-shelf LLM GenPRM flags erroneous steps in one pass, with voting, giving token-level credit in RLVR (math, not agents).
- **Agent-R**, 2501.11425, Jan 2025. The actor identifies the first error step in an MCTS-built failed trajectory and splices in the correct sibling path; iterative self-training (+5.59%).
- **CRAFT**, 2606.29476, Jun 2026. Counterfactual per-token credit from GRPO siblings for self-distilled RL; no numbers in the abstract.
- **OAT**, "Tracing Agentic Failure from the Flow of Success", 2607.12747, NeurIPS 2026. A failure *attributor* trained only on successes (neural CDE, one-class); not used for RL. Relevant to the attribution side.
- **Survey**, "From Reasoning to Agentic: Credit Assignment in RL for LLMs", 2604.09459, v3 Aug 2026. Covers 69 papers through Jul 2026; useful for the taxonomy, but the abstract does not frame things as failure attribution.

## 5. UNVERIFIED leads (ids from search snippets only, pages not opened)
- SWE-MILE, milestone credit for SWE agents (2609.32631).
- SWE-TRACE, rubric PRMs for SWE agents (2604.14820).
- "When Agents go Astray: Course-Correcting SWE Agents with PRMs" (2509.02360).
- Who&When Pro (2607.09996).
- SHARP, Shapley credit for MAS (2602.08335).
- Conformal Agent Error Attribution, inference-time rollback to the first step in a conformal set (2605.06788).
- AgentLocate (2607.07989).
- Fail-Fast, Restart-Smart (2608.03222).
- Learning What to Skip, counterfactual credit for MAS workflows (2609.30734).
- COSAC (2604.17693).
- TreeHCA (2610.12828).
- "Drowning in Routine" (2606.22164).
- Semantic Cooperative Games (2607.18255).
- ReCast (2610.11334).
- StepFinder (2606.03467).
- GraphTracer (2510.10581).
- Named in the brief but not searched or verified here: EDGE-GRPO, Agent-R1, AgentQ. No ids given, to avoid inventing them.

---

## 6. Synthesis: how step-level blame enters agent RL (for the survey's "use as a training signal" section)

**Entry points observed:**
- **Restart or branch from the blamed prefix** (reshapes the rollout distribution): MiRL, PivoARL, ELPO's tree, CSO's branches, ProVer's boundary continuations.
- **Advantage edits localized to the blamed step or segment:**
  - Additive bonus (ProVer, positive only).
  - Redistributing the terminal reward as step penalties (FAULT).
  - Polarity-routed distillation (ETRO).
  - Stronger clipping-side penalty on the error suffix (ELPO).
  - Value-drop advantages (LVRL).
- **Suffix isolation / truncation after the decisive error:**
  - PivoARL: the suffix never inherits the retry's success.
  - ETRO: no dense supervision after k.
  - ELPO: suffix tokens get the larger negative update.
- **Preference pairs at the critical step:** CSO (verified DPO pairs); the conceptual repair-aware preferences in 2511.10687.
- **Dense learned decompositions (soft attribution):** SPA-RL, AgentPRM, iStar, HCAPO, GiGPO.

**Common design pattern:**
- An LLM proposes a blame step; MC continuations from the current policy verify it; only then does it shape credit (ProVer, CSO, ELPO; MiRL's replay check; FAULT's evidence check).
- Executable Prefix Values (2610.17633) shows why verification matters: unverified judge first-mistake labels often fall where success probability does not drop, and restarting from them does not help.

**Definitions align with our datasets:**
- ELPO's "first irrecoverable step" and the PNR in 2610.17633 ≈ TraceElephant's decisive step ("failure became unavoidable").
- CSO's "alternative flips outcome" ≈ AgenTracer's counterfactual decisive error.
- ETRO's "earliest unrecovered, decisive" ≈ Who&When's decisive error.
- FAULT evaluates its blame with a Who&When-style decisive-step match (top-1 82/300).

**Gaps (as of 2026-10-28, from these searches):**
- No paper was found that trains an agent using a **Who&When / AgenTracer / TraceElephant-trained attributor as the reward or credit model**. AgenTracer's own downstream gains (+4.8–14.2%) come from feedback at inference time.
- Progress Advantage (2606.26080) shows RL log-ratios score Who&When near AgenTracer, but it does not close the loop.
- Multi-agent RL with step-level blame is either conceptual (2511.10687) or limited to short 2-agent math workflows (C3 2603.06859, CCPO 2603.21563). No MAS RL paper uses Who&When-style agent+step blame on GAIA- or AssistantBench-style tasks.
- Negative credit on the decisive failure step, verified by MC, is underexplored: ProVer only rewards success segments, and CSO uses expert alternatives.
- Attributor accuracy (Who&When step-level accuracy is low for prompted LLMs; AgentDebug reports 50% step accuracy) means raw attributor output is too noisy to use without verification or annealing (see 2610.35497 on reward hacking with fixed process weights).
